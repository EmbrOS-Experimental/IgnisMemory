# Agent Deployment Plan — Mneme Memory

## What Gets Deployed

Mneme is a library + MCP server. It doesn't run as a service. Agents embed it or connect to it.

### Deployment Models

#### 1. Embedded (pip install)
```
pip install mneme-memory
```
Agent imports `Memory` class directly. SQLite DB lives on disk. Zero config.

#### 2. MCP Server (stdio)
```
mneme serve --stdio
```
Agent (Claude Code, Cursor, Codex) spawns Mneme as a subprocess. Communicates over stdio. Agent calls `mneme_write`, `mneme_recall`, `mneme_curate` as tools.

#### 3. MCP Server (HTTP)
```
mneme serve --port 8192
```
Remote agents connect over HTTP/SSE. Useful for multi-agent setups or when the agent runs on a different machine.

#### 4. Docker
```dockerfile
FROM python:3.12-slim
RUN pip install mneme-memory
VOLUME /data
CMD ["mneme", "serve", "--port", "8192", "--db", "/data/memory.db"]
```

## Agent Integration Guide

### Claude Code / Cursor
```jsonc
// .cursor/mcp.json
{
  "mneme": {
    "command": "mneme",
    "args": ["serve", "--stdio"]
  }
}
```

### Custom Python Agent
```python
from mneme import Memory

mem = Memory(agent="my-agent", project="my-project")
mem.write("observation")
results = mem.recall("query")
```

### Ollama-based Agent
```python
from mneme import Memory
from openai import OpenAI

llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
mem = Memory(agent="ollama-agent", project="local", llm_client=llm)
```

## Recommended Agent Architecture

```
┌─────────────────────────────────────────┐
│              YOUR AGENT                  │
│  (Claude Code, Ollama, custom, etc.)    │
│                                         │
│  1. Before task:                        │
│     context = mem.recall(task_desc)     │
│                                         │
│  2. During task:                        │
│     mem.write(observation)              │
│                                         │
│  3. After task:                         │
│     mem.write(outcome)                  │
│     mem.extract_beliefs()  (if idle)    │
│     mem.curate()           (if idle)    │
└─────────────────────────────────────────┘
```

## Multi-Agent Setup

For teams of agents working on the same project:

1. **Shared project scope**: All agents use `project="same-project-id"`
2. **MCP server mode**: One Mneme instance serves all agents over HTTP
3. **Per-agent private memories**: Each agent uses its own `agent="agent-id"` for private observations
4. **Cross-agent learning**: Agent B can read Agent A's project-scoped memories

## Storage Backends

| Backend | When to use | Config |
|---|---|---|
| sqlite-vec (default) | Single agent, local, <1M memories | `db_path="~/.mneme/memory.db"` |
| Qdrant | Multi-agent, >1M memories, Docker | `pip install mneme-memory[qdrant]` |
| pgvector | Existing PostgreSQL | `pip install mneme-memory[qdrant]` |

## Idle-Time Curation Schedule

For long-running agents, schedule curation:

```python
import asyncio
from mneme import Memory

mem = Memory(agent="my-agent", project="my-project")

async def curation_loop():
    while True:
        await asyncio.sleep(3600)  # Every hour
        mem.curate()
        mem.extract_beliefs()

asyncio.run(curation_loop())
```

Or use a cron job:
```bash
# Curate every hour
0 * * * * mneme curate --agent my-agent --project my-project
```

## Security Notes

- SQLite DB is a single file — back it up
- No encryption at rest (add filesystem encryption if needed)
- MCP stdio mode is local-only (no network exposure)
- HTTP mode binds to 127.0.0.1 by default
- No telemetry, no phone-home, no tracking
