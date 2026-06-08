"""CLI for Mneme."""

from __future__ import annotations

import json

import click
from rich.console import Console
from rich.table import Table

from mneme import Memory

console = Console()


@click.group()
@click.option("--db", default="~/.mneme/memory.db", help="Database path")
@click.pass_context
def cli(ctx, db):
    """Mneme — Agent Memory Framework"""
    ctx.ensure_object(dict)
    ctx.obj["db"] = db


@cli.command()
@click.argument("content")
@click.option("--agent", default="default", help="Agent ID")
@click.option("--project", default="default", help="Project ID")
@click.pass_context
def write(ctx, content, agent, project):
    """Store a memory."""
    mem = Memory(agent=agent, project=project, db_path=ctx.obj["db"])
    fact = mem.write(content)
    console.print(f"[green]✓[/green] Stored [dim]{fact.id[:8]}[/dim]  "
                  f"confidence={fact.confidence:.0%}  times_seen={fact.times_seen}")
    mem.close()


@cli.command()
@click.argument("query")
@click.option("--agent", default="default", help="Agent ID")
@click.option("--project", default="default", help="Project ID")
@click.option("--limit", default=5, help="Max results")
@click.pass_context
def recall(ctx, query, agent, project, limit):
    """Search memories."""
    mem = Memory(agent=agent, project=project, db_path=ctx.obj["db"])
    results = mem.recall(query, limit=limit)

    if not results:
        console.print("[dim]No results found.[/dim]")
        mem.close()
        return

    table = Table(title=f"Results for: {query}")
    table.add_column("Score", style="cyan", width=8)
    table.add_column("Conf", style="green", width=6)
    table.add_column("Type", style="yellow", width=7)
    table.add_column("Content")

    for r in results:
        table.add_row(
            f"{r.score:.3f}",
            f"{r.confidence:.0%}",
            "belief" if r.is_belief else "fact",
            r.content[:120],
        )

    console.print(table)
    mem.close()


@cli.command()
@click.option("--agent", default="default", help="Agent ID")
@click.option("--project", default="default", help="Project ID")
@click.pass_context
def curate(ctx, agent, project):
    """Run curation pass."""
    mem = Memory(agent=agent, project=project, db_path=ctx.obj["db"])
    stats_before = mem.stats()
    mem.curate()
    stats_after = mem.stats()
    console.print(f"[green]✓[/green] Curated: {stats_before} → {stats_after}")
    mem.close()


@cli.command()
@click.option("--agent", default="default", help="Agent ID")
@click.option("--project", default="default", help="Project ID")
@click.pass_context
def stats(ctx, agent, project):
    """Show memory statistics."""
    mem = Memory(agent=agent, project=project, db_path=ctx.obj["db"])
    s = mem.stats()
    console.print(f"Facts: [bold]{s['facts']}[/bold]  Beliefs: [bold]{s['beliefs']}[/bold]")
    mem.close()


@cli.command()
@click.option("--port", default=8192, help="HTTP port")
@click.option("--host", default="127.0.0.1", help="Host")
@click.option("--stdio", is_flag=True, help="Use stdio transport (for MCP clients)")
@click.pass_context
def serve(ctx, port, host, stdio):
    """Start MCP server."""
    if stdio:
        from mneme.mcp import serve_stdio
        console.print("[dim]Starting MCP server on stdio...[/dim]")
        import asyncio
        asyncio.run(serve_stdio(ctx.obj["db"]))
    else:
        from mneme.mcp import serve_http
        console.print(f"[dim]Starting MCP server on {host}:{port}...[/dim]")
        serve_http(host, port, ctx.obj["db"])


def main():
    cli()


if __name__ == "__main__":
    main()
