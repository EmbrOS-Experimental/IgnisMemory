"""Example: Multi-agent shared memory."""

from mneme import Memory

# Setup: two agents working on the same project
builder = Memory(agent="builder", project="api-service")
deployer = Memory(agent="deployer", project="api-service")
tester = Memory(agent="tester", project="api-service")

# Builder agent writes what it learns
builder.write("API endpoint /users requires authentication via JWT")
builder.write("Rate limit: 100 requests per minute per API key")
builder.write("Database: Railway PostgreSQL, connection pool max 20")

# Deployer agent reads builder's knowledge
print("=== Deployer reading builder's memories ===")
for r in deployer.recall("API authentication"):
    print(f"  📖 {r.content} (by builder)")

for r in deployer.recall("rate limits"):
    print(f"  📖 {r.content} (by builder)")

# Deployer adds its own observations
deployer.write("Health check endpoint at /health, returns 200 OK")
deployer.write("Railway auto-deploys on git push to main")

# Tester reads from both
print("\n=== Tester reading all project memories ===")
for r in tester.recall("API limits and auth"):
    print(f"  📖 {r.content}")

# Builder reads deployer's additions
print("\n=== Builder reading deployer's memories ===")
for r in builder.recall("health check"):
    print(f"  📖 {r.content} (by deployer)")

# Stats
print(f"\nProject stats: {builder.stats()}")

builder.close()
deployer.close()
tester.close()
