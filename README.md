<div align="center">

# 🔥 Ignis Memory

**Agent memory that learns, forgets, believes, and compounds.**

Not a diary. A brain.

[![Tests](https://github.com/EmbrOS-Experimental/IgnisMemory/actions/workflows/test.yml/badge.svg)](https://github.com/EmbrOS-Experimental/IgnisMemory/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/MCP-compatible-purple.svg)](https://modelcontextprotocol.io)

**Built by the team at [EmbrOS](https://embros.xyz)** — the AI Builder Operating System.

[Why](#-why) · [How](#-how) · [Install](#-install) · [Quick Start](#-quick-start) · [MCP](#-mcp-server) · [Contribute](#-contribute)

</div>

---

## 🤔 Why

Every agent memory system stores **what happened**. None store **what it means**.

Your agent remembers "connection pool set to 20" and "CPU spiked 15%" as two separate facts. A human engineer would say: *"Increasing the connection pool causes CPU regression — don't do that."*

That's the gap. **Ignis Memory** is the first framework that maintains a **belief store** — causal, confidence-scaled, self-evolving knowledge that compounds over time.

```
Traditional memory:  [fact] [fact] [fact] [fact] [fact]
Ignis Memory:        [fact] [fact] → [belief] → [better next time]
```

### The Problem with Existing Solutions

| | Mem0 | Letta | Zep | Cognee | **Ignis** |
|---|---|---|---|---|---|
| Local-first, instant start | △ | △ | ❌ | △ | **✅** |
| Zero-LLM writes (CPU only) | ❌ | ❌ | ❌ | ❌ | **✅** |
| Belief store (causal lessons) | ❌ | ❌ | ❌ | ❌ | **✅** |
| Auto-curation (decay/dedup/promote) | ❌ | △ | △ | △ | **✅** |
| Git-like memory versioning | ❌ | △ | ❌ | ❌ | **✅** |
| Multi-agent shared memory | ❌ | ❌ | ❌ | ❌ | **✅** |
| MCP server (any agent) | ✅ | △ | ❌ | △ | **✅** |
| Cross-platform (Win/Mac/Linux) | ✅ | ✅ | ✅ | ✅ | **✅** |
| Free, MIT, no strings | ✅ | ✅ | ❌ | ✅ | **✅** |

> 💡 **Research-backed:** Based on analysis of 21 frameworks, 20+ academic papers (SleepGate, ZenBrain, A-MEM, MemoryOS), and 6 survey articles from 2025-2026. [Read the full research](RESEARCH.md).

---

## 🧠 How

### Two Layers. Facts First. Beliefs on Top.

**Facts** are cheap. Write them fast, zero LLM calls, CPU-only embedding.

```python
mem.write("User prefers dark mode")
mem.write("Railway deploy failed: missing DATABASE_URL")
mem.write("Connection pool at 20 → CPU spike +15%, timeouts unchanged")
```

**Beliefs** are extracted during idle time. Dual-agent: one extracts, one challenges.

```python
mem.extract_beliefs()
# → "Connection pool size↑ causes CPU regression without fixing timeouts"
#    confidence: 87% | evidence: 3 facts | causal: pool↑ → cpu↑, timeouts unchanged
```

### Multi-Strategy Retrieval

Vector search alone misses things. Ignis searches **three ways simultaneously**:

1. **Semantic** — embedding cosine similarity
2. **Keyword** — BM25-inspired term matching
3. **Beliefs** — causal lessons ranked by confidence

Results are merged, deduplicated, and ranked by `score × confidence`.

### Automatic Curation (During Idle Time)

```
Every write:
  └── embed → check for near-dups → merge or insert

Idle-time passes:
  ├── Deduplicate (merge dups, increment times_seen)
  ├── Decay (Ebbinghaus forgetting curve for unconfirmed memories)
  ├── Promote (confidence > 90% → pinned)
  ├── Deprecate (contradicted → superseded, not deleted)
  └── Extract beliefs (dual-agent: extractor + challenger)
```

### Multi-Agent Shared Memory

Multiple agents on the same project share a memory space:

```python
builder = Memory(agent="builder", project="api-service")
builder.write("Rate limit is 100 req/min")

deployer = Memory(agent="deployer", project="api-service")
deployer.recall("API limits")
# → "Rate limit is 100 req/min" (written by builder)
```

---

## 📦 Install

```bash
pip install mneme-memory
```

Optional extras:

```bash
pip install mneme-memory[embed]    # sentence-transformers (better embeddings)
pip install mneme-memory[mcp]      # MCP server support
pip install mneme-memory[qdrant]   # Qdrant backend
pip install mneme-memory[all]      # everything
```

**Requirements:** Python 3.10+. Works on Windows, macOS, Linux. No GPU needed. No cloud needed.

---

## ⚡ Quick Start

### Python SDK

```python
from mneme import Memory

mem = Memory(agent="my-agent", my-project")

# Write — zero LLM calls, CPU only
mem.write("User prefers dark mode")
mem.write("API rate limit is 100 req/min")
mem.write("Connection pool at 20 caused CPU spike +15%")

# Read — multi-strategy retrieval
results = mem.recall("how does the user want the UI?")
for r in results:
    print(f"[{r.confidence:.0%}] {r.content}")

# Extract beliefs (async, dual-agent, during idle)
mem.extract_beliefs()

# Curate — deduplicate, decay stale, promote high-confidence
mem.curate()

# Stats
print(mem.stats())  # {"facts": 3, "beliefs": 1}
```

### CLI

```bash
# Write
mneme write "User prefers dark mode" --agent my-agent --project my-project

# Recall
mneme recall "UI preferences" --limit 5

# Curate
mneme curate

# Stats
mneme stats
```

### MCP Server

```bash
# For Claude Code, Cursor, Codex, etc.
mneme serve --stdio

# Or HTTP for remote agents
mneme serve --port 8192
```

Configure in your agent:

```jsonc
// .cursor/mcp.json, .codex/mcp.json, Claude Desktop, etc.
{
  "ignis-memory": {
    "command": "mneme",
    "args": ["serve", "--stdio"]
  }
}
```

---

## 🏗️ Architecture

```
Any Agent (Claude Code, Cursor, Ollama, custom)
        │
        ▼
┌────────────┐  ┌─────────┐  ┌──────────┐
│ MCP Server │  │ REST API│  │Py/TS SDK │
└─────┬──────┘  └────┬────┘  └────┬─────┘
      └──────┬───────┘            │
             ▼                    │
      ┌───────────────────────────┤
      │      CORE ENGINE          │
      │                           │
      │  write()    recall()      │
      │  (zero-LLM) (multi-strat) │
      │                           │
      │  extract_beliefs()        │
      │  (async / idle-time)      │
      │                           │
      │  curate()                 │
      │  (async / idle-time)      │
      └────────────┬──────────────┘
                   │
      ┌────────────┴──────────────┐
      │   STORAGE (pluggable)     │
      │                           │
      │  SQLite    (default)     │  ← zero config, instant
      │  Qdrant    (Docker)      │  ← multi-agent, large scale
      │  pgvector  (Postgres)    │  ← existing infra
      └───────────────────────────┘
```

### Memory Model

**Fact** (ingested immediately, zero LLM):
```python
{
  "id": "uuid",
  "content": "User prefers dark mode",
  "embedding": [0.01, -0.03, ...],
  "scope": {"agent": "my-agent", "project": "my-project"},
  "confidence": 0.95,           # decays if unconfirmed
  "times_seen": 5,              # increments on dedup
  "pinned": False,              # auto-promoted at >90%
  "superseded_by": None,        # soft delete
}
```

**Belief** (extracted async, dual-agent):
```python
{
  "content": "Connection pool↑ causes CPU regression without fixing timeouts",
  "causal": "pool↑ → cpu↑, timeouts unchanged",
  "evidence": ["fact-uuid-1", "fact-uuid-2"],
  "confidence": 0.87,
  "confirmed_count": 3,
}
```

---

## 🤖 Agent Integration

### Recommended Agent Loop

```
1. BEFORE task:   context = mem.recall(task_description)
2. DURING task:   mem.write(observation)  # as things happen
3. AFTER task:    mem.write(outcome)
                  mem.extract_beliefs()    # if idle
                  mem.curate()             # if idle
```

### With Ollama (Local LLM)

```python
from mneme import Memory
from openai import OpenAI

llm = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
mem = Memory(agent="local-agent", project="my-app", llm_client=llm)

mem.write("User asked for Romanian language support")
mem.write("User's browser language is ro-RO")

beliefs = mem.extract_beliefs()  # Uses Ollama for dual-agent extraction
```

### With OpenAI

```python
from openai import OpenAI
from mneme import Memory

llm = OpenAI()
mem = Memory(agent="coding-agent", project="backend", llm_client=llm)
```

---

## 🗺️ Roadmap

- [x] Core architecture design
- [x] Zero-LLM ingest + SQLite backend
- [x] Multi-strategy retrieval (semantic + keyword + beliefs)
- [x] Belief extraction (rule-based + dual-agent LLM)
- [x] Auto-curation (dedup, decay, promote)
- [x] MCP server (stdio + HTTP)
- [x] CLI
- [x] Multi-agent shared memory
- [x] Cross-platform CI (Win/Mac/Linux)
- [ ] TypeScript SDK
- [ ] Qdrant backend
- [ ] Memory versioning (git-like)
- [ ] Web dashboard for browsing memories
- [ ] Embodied memory (images/audio)

---

## 🤝 Contribute

This is open source. MIT. Free forever. Built by the community.

**Ways to help:**
- 🐛 Report bugs via [GitHub Issues](https://github.com/EmbrOS-Experimental/IgnisMemory/issues)
- 💡 Suggest features — open a discussion
- 🔧 Submit PRs — check the roadmap above for what's next
- ⭐ Star the repo — helps others find it
- 🐦 Share it — tweet it, blog it, tell your agent friends

**Development setup:**

```bash
git clone https://github.com/EmbrOS-Experimental/IgnisMemory.git
cd IgnisMemory
pip install -e ".[dev]"
pytest tests/ -v
```

---

## 🔗 Built By

**Ignis Memory** is built by the team behind **[EmbrOS](https://embros.xyz)** — the AI Builder Operating System.

EmbrOS is building the full stack for AI-powered development: agents, memory, sandboxes, deployment. Ignis Memory is the memory layer, open-sourced for everyone.

- 🌐 [embros.xyz](https://embros.xyz)
- 💬 [Discord](https://discord.gg/FZsWkYpM9b)
- 🐙 [GitHub](https://github.com/EmbrOS-Experimental)

---

## 📄 License

MIT. Do whatever you want with it. No attribution required, but we appreciate it.

---

<div align="center">

**If your agent remembers everything but learns nothing, it's not memory. It's a log.**

**Ignis Memory. Remember. Learn. Compound.**

⭐ Star this repo if it's useful. It helps.

</div>

---

🐦 Follow on X: [@probert_mihai](https://x.com/probert_mihai)
