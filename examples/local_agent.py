"""Example: Local agent with Mneme memory + Ollama."""

from mneme import Memory

# Initialize memory for a local coding agent
mem = Memory(
    agent="coding-agent",
    project="my-web-app",
    db_path="~/.mneme/my-web-app.db",
)


# Simulate an agent session
def agent_session():
    # Agent writes observations during work
    mem.write("User wants a Next.js app with dark mode toggle")
    mem.write("Railway deployment configured with PostgreSQL addon")
    mem.write("API routes use /api prefix, max 100 req/min rate limit")
    mem.write("Tailwind CSS configured with custom color tokens")
    mem.write("Database schema: users, projects, sessions tables")

    # Later, agent recalls context
    print("=== Recalling deployment info ===")
    for r in mem.recall("how is deployment configured?"):
        print(f"  [{r.confidence:.0%}] {r.content}")

    print("\n=== Recalling rate limits ===")
    for r in mem.recall("API rate limits"):
        print(f"  [{r.confidence:.0%}] {r.content}")

    # After several sessions, extract beliefs
    print("\n=== Extracting beliefs ===")
    mem.write("Build failed: missing DATABASE_URL env var")
    mem.write("Build failed again: DATABASE_URL still not set in Railway env")
    mem.write("Fixed: added DATABASE_URL to Railway environment variables")

    beliefs = mem.extract_beliefs()
    for b in beliefs:
        print(f"  💡 {b.content} (confidence: {b.confidence:.0%})")

    # Run curation
    mem.curate()
    print(f"\n=== Stats: {mem.stats()} ===")


if __name__ == "__main__":
    agent_session()
    mem.close()
