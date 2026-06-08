"""MCP server for Mneme. Exposes memory tools to any MCP-compatible agent."""

from __future__ import annotations

import json
import sys
from typing import Any

from mneme import Memory


def create_mcp_server(db_path: str = "~/.mneme/memory.db"):
    """Create and return an MCP server instance."""
    try:
        from mcp.server import Server
        from mcp.types import Tool, TextContent
    except ImportError:
        print("mcp package not installed. Run: pip install mcp", file=sys.stderr)
        sys.exit(1)

    server = Server("mneme-memory")
    memories: dict[str, Memory] = {}

    def get_memory(agent: str = "default", project: str = "default") -> Memory:
        key = f"{agent}:{project}"
        if key not in memories:
            memories[key] = Memory(agent=agent, project=project, db_path=db_path)
        return memories[key]

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="mneme_write",
                description="Store a memory. Zero LLM calls, CPU only.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "What to remember"},
                        "agent": {"type": "string", "description": "Agent ID", "default": "default"},
                        "project": {"type": "string", "description": "Project ID", "default": "default"},
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="mneme_recall",
                description="Retrieve memories using multi-strategy search (semantic + keyword + beliefs).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What to search for"},
                        "agent": {"type": "string", "description": "Agent ID", "default": "default"},
                        "project": {"type": "string", "description": "Project ID", "default": "default"},
                        "limit": {"type": "integer", "description": "Max results", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="mneme_beliefs",
                description="Extract causal beliefs from accumulated facts. Uses LLM if configured.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string", "description": "Agent ID", "default": "default"},
                        "project": {"type": "string", "description": "Project ID", "default": "default"},
                    },
                },
            ),
            Tool(
                name="mneme_curate",
                description="Run curation: deduplicate, decay stale memories, promote high-confidence ones.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string", "description": "Agent ID", "default": "default"},
                        "project": {"type": "string", "description": "Project ID", "default": "default"},
                    },
                },
            ),
            Tool(
                name="mneme_stats",
                description="Get memory statistics for a project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "agent": {"type": "string", "description": "Agent ID", "default": "default"},
                        "project": {"type": "string", "description": "Project ID", "default": "default"},
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]):
        agent = arguments.get("agent", "default")
        project = arguments.get("project", "default")

        if name == "mneme_write":
            mem = get_memory(agent, project)
            fact = mem.write(arguments["content"])
            return [TextContent(type="text", text=json.dumps({
                "status": "stored",
                "id": fact.id,
                "times_seen": fact.times_seen,
                "confidence": fact.confidence,
            }))]

        elif name == "mneme_recall":
            mem = get_memory(agent, project)
            results = mem.recall(arguments["query"], limit=arguments.get("limit", 5))
            return [TextContent(type="text", text=json.dumps([
                {
                    "id": r.id,
                    "content": r.content,
                    "confidence": r.confidence,
                    "score": round(r.score, 3),
                    "is_belief": r.is_belief,
                    "causal": r.causal,
                }
                for r in results
            ], indent=2))]

        elif name == "mneme_beliefs":
            mem = get_memory(agent, project)
            beliefs = mem.extract_beliefs()
            return [TextContent(type="text", text=json.dumps([
                {"content": b.content, "causal": b.causal, "confidence": b.confidence}
                for b in beliefs
            ], indent=2))]

        elif name == "mneme_curate":
            mem = get_memory(agent, project)
            mem.curate()
            stats = mem.stats()
            return [TextContent(type="text", text=json.dumps({
                "status": "curated",
                "stats": stats,
            }))]

        elif name == "mneme_stats":
            mem = get_memory(agent, project)
            return [TextContent(type="text", text=json.dumps(mem.stats()))]

        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    return server


async def serve_stdio(db_path: str = "~/.mneme/memory.db"):
    """Run MCP server over stdio (for Claude Code, Cursor, etc.)."""
    from mcp.server.stdio import stdio_server

    server = create_mcp_server(db_path)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def serve_http(host: str = "127.0.0.1", port: int = 8192, db_path: str = "~/.mneme/memory.db"):
    """Run MCP server over HTTP (for remote agents)."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount, Route

    server = create_mcp_server(db_path)
    sse = SseServerTransport("/messages")

    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())

    app = Starlette(
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages", app=sse.handle_post_message),
        ],
    )

    import uvicorn
    uvicorn.run(app, host=host, port=port)
