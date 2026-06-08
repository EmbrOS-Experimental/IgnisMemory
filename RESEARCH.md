# 🧠 AI Agent Memory Landscape — Complete Research Report
**Date:** June 2026  
**Compiled by:** OWL for Ignis Framework

---

## 1. THE MEMORY PROBLEM, FRAMED CORRECTY

There are **two distinct memory problems** most people conflate:

| Problem | Description | Hardness |
|---|---|---|
| **Personalization** | Remember user preferences, conversation history, who they are | Easier — mostly solved |
| **Institutional Knowledge** | Agent learns from experience, compounds domain expertise, extracts causal lessons | Harder — barely solved |

> "Current memory tools are **diaries**. What agents need is a **notebook** — something that records lessons, not just events." — Moses Njau, Data Unlocked

Most frameworks solve personalization. Few solve institutional knowledge.

---

## 2. TAXONOMY OF MEMORY TYPES

| Memory Type | What it is | Covered? |
|---|---|---|
| **Episodic** | Specific events and experiences | ✅ Most tools |
| **Semantic** | Facts, knowledge, concepts | ✅ Vector stores |
| **Procedural** | Learned skills/behavioral patterns from experience | ❌ Largely missing |
| **Working** | Short-term context within a session | ✅ Everyone |
| **Causal/Belief** | "Why X happens" — not just "what happened" | ❌ Almost nobody |

---

## 3. EXISTING SOLUTIONS — COMPLETE LANDSCAPE

### 3.1 Production / OSS Frameworks

| Solution | Memory Class | Architecture | OSS | Cloud | Self-Host | Stars | Pricing |
|---|---|---|---|---|---|---|---|
| **Mem0** | Personalization + some institutional | Vector + Graph (entity linking) | Apache 2.0 | ✅ | ✅ (OSS) | ~48K | Free→$249/mo (platform) |
| **Letta (ex-MemGPT)** | Both (tiered OS-inspired) | Fast/Slow tiers, sleep-time compute | Apache 2.0 | ✅ | ✅ (OSS) | ~23K | Free (OSS) |
| **Zep / Graphiti** | Both (strongest on temporal) | Temporal Knowledge Graph | Graphiti: OSS | ✅ | Graphiti only | ~24K | Free→$312+/mo |
| **Cognee** | Institutional | KG + Vector | Open Core | ✅ | ✅ | ~12K | Free (OSS) |
| **Hindsight** | Both (built for institutional) | Multi-strategy hybrid | MIT | ✅ | ✅ | ~4K | Free (OSS) |
| **LangMem** | Personalization | Flat key-value + vector | MIT | ❌ | ✅ | ~1.3K | Free |
| **LlamaIndex Memory** | Personalization | Composable buffers | MIT | LlamaCloud | ✅ | Part of ~48K | Free (OSS) |
| **Microsoft GraphRAG** | Knowledge graph RAG | Graph + RAG | MIT | Azure | ✅ | ~18K | Free (OSS) |
| **SuperMemory** | Personalization | Memory + RAG | ❌ | ✅ | Enterprise only | — | Paid only |
| **MemOS (MemTensor)** | Full memory OS | Plaintext + Activation + Parametric | Apache 2.0 | ❌ | ✅ | New | Free (OSS) |
| **A-MEM** | Both | Zettelkasten dynamic notes | MIT (paper code) | ❌ | ✅ | New | Free (research) |
| **OpenMemory (Mem0)** | Project-scoped | MCP server, local | OSS | ❌ | ✅ | New | Free |

### 3.2 Academic / Research-Stage

| Solution | Key Innovation | Status |
|---|---|---|
| **MemoryOS** | Three-tier hierarchy (short/mid/long), +49% F1 on LoCoMo | EMNLP 2025 Oral, OSS |
| **SleepGate** | Sleep cycles over KV cache, O(n)→O(log n) interference | arXiv 2026, 99.5% vs <18% |
| **ZenBrain** | 15 neuroscience mechanisms, near-oracle at 1/1M token cost | arXiv 2026, OSS |
| **MemForest** | Hierarchical temporal index (MemTree), 6x throughput | VLDB 2027 submission |
| **SuperLocalMemory V3** | Zero-LLM memory, CPU-only, 7-channel cognitive retrieval | arXiv 2026 |
| **HiMem** | Episode + Note dual memory, conflict-aware reconsolidation | arXiv 2026 |
| **FSFM** | Formal taxonomy of forgetting mechanisms | arXiv 2026 |
| **G-Memory** | Multi-agent shared memory, organizational theory | NeurIPS 2026 |
| **RMM** | Prospective + backward-looking reflection for dialogue | ACL 2025 |
| **Titans / MIRAS** | Test-time learning with persistent memory params | Google Research |
| **ReadAgent** | Gist memory, 3.5-20x context extension | Google DeepMind 2024 |
| **MemoryBank** | Ebbinghaus Forgetting Curve in LLM memory | 2023 |
| **MemWalker** | Tree-of-summaries for interactive reading | 2023 |

---

## 4. ARCHITECTURAL PATTERNS

### 4.1 What Works (Consensus 2026)

1. **Multi-signal retrieval** — semantic + keyword (BM25) + entity + temporal in parallel. Vector-only fails on temporal queries and rare entities.
2. **Write-heavy, read-fast** — Do extraction, entity resolution, embedding at INGESTION time so retrieval is cheap.
3. **Multi-scope tagging** — Every memory tagged with user_id, agent_id, run_id for proper isolation.
4. **Async consolidation** — Background/sleep-time processing for memory refinement (Letta pioneered this).
5. **Temporal awareness** — Facts have validity windows. "Customer X preference" should know WHEN it was true.

### 4.2 The Pipeline All Systems Share

```
INGEST → extract facts/entities → resolve entities → assign timestamps → embed → store
RETRIEVE → multi-strategy search → rerank → synthesize with LLM → return context
```

---

## 5. BENCHMARK LANDSCAPE

| Benchmark | What it tests | Top Scores (2026) |
|---|---|---|
| **LoCoMo** | Multi-session conversation recall | Mem0: 92.5, MemoryOS: +49% F1 |
| **LongMemEval** | Knowledge update, preference tracking | Mem0: 94.4 |
| **BEAM** | Production-scale (1M-10M tokens), contradiction, abstention | Mem0: 64.1 (1M), 48.6 (10M) |
| **LongMemEval-V2** | Up to 500 trajectories / 115M tokens | Emerging |

---

## 6. LOCAL / SELF-HOSTED OPTIONS (No Cloud Required)

| Solution | Offline? | Vector Store | Model Dep | Install |
|---|---|---|---|---|
| **Letta (MemGPT)** | ✅ With Ollama | Qdrant/Chroma | Ollama local | pip + Docker |
| **Cognee** | ✅ | Qdrant/Chroma/PGVector | Any embedding model | pip + Docker |
| **Mem0 OSS** | ✅ | Qdrant/Chroma/FAISS/20 others | Any LLM | pip |
| **Hindsight** | ✅ | Any (pluggable) | Any LLM | pip |
| **Graphiti (Zep OSS)** | ✅ | Neo4j/PostgreSQL | Any LLM | Docker |
| **MemOS** | ✅ | Local | Local LLM | pip |
| **A-MEM** | ✅ | Local | Any LLM | pip (research) |
| **LangMem** | ✅ | Any (pluggable) | Any LLM | pip |
| **EchoVault** | ✅ | SQLite + FTS | None (Markdown) | MCP server |
| **LangGraph Checkpoint** | ✅ | SQLite/Redis | Any LLM | pip |

---

## 7. KEY GAPS — WHAT DOESN'T EXIST YET

### 🔴 Critical Gaps

1. **Procedural Belief Extraction** — No production system extracts **causal beliefs** from experience. Mem0 stores facts. Letta manages context. Nobody says "I tried X, it failed, here's WHY." The Medium article "Half Solved" nails this: we have diaries, not notebooks.

2. **Learned Forgetting** — Only available in research (FSFM, SuperLocalMemory). No production system has first-class forgetting. Memories accumulate forever → stale, contradictory, noisy.

3. **Cross-Session Identity** — When an agent works across days/weeks WITH THE SAME ENTITIES (same repo, same customer, same project), no system properly maintains identity continuity. Memories are isolated per-session.

4. **Conflict Resolution** — When new info contradicts old info, systems either accumulate duplicates or blindly overwrite. No nuanced confidence+evidence model.

5. **Temporal Reasoning at Scale** — Zep does temporal KGs but it's expensive. Nobody has cheap temporal reasoning for millions of memories.

### 🟡 Important Gaps

6. **Zero-LLM Memory Operations** — SuperLocalMemory is the only one. Every other system uses LLMs for extraction, which is slow and costs money. For local agents, a CPU-only memory layer is a massive unlock.

7. **Multi-Agent Shared Memory** — G-Memory is research-only. Hints in Hindsight. No production MCP/server for agents to share a memory space.

8. **Memory Compression with Loyalty** — ReadAgent's gist approach is promising but not productized. Nobody has "compress 1000 memories into 10 summaries on a schedule."

9. **Embodied/Multimodal Memory** — Almost no memory systems handle images, audio, or sensory data as first-class memory objects. Cognee claims this but it's early.

10. **Evaluation Beyond Benchmarks** — LoCoMo tests conversation recall. Nobody benchmarks "did the agent GET BETTER at its job over 100 sessions?"

### 🟢 Niche Gaps (for Ignis specifically)

11. **Local-First, Fast Startup** — EchoVault (SQLite + Markdown) is closest but primitive. No solution starts instantly, uses zero GPU, and scales to millions of memories.

12. **Agent-Written Memory** — No system has the agent actively curate its own memory during execution (not just reflection after). Letta's sleep-time is the closest.

13. **Memory Versioning / Git for Memory** — Letta has "context repositories" concept. Nothing mature. Memory should be diffable, branchable, revertible.

14. **Cost-Aware Memory** — No system tracks how much each memory costs (in tokens, storage, retrieval time) and optimizes accordingly.

15. **Privacy-Preserving Memory Architecture** — No one has a clean architecture for "these memories stay on-device, these can go to cloud" with enforcement.

---

## 8. SOLUTION COMPARISON MATRIX

```
Feature              Mem0  Letta  Zep    Cognee  Hindsight  MemOS  LangMem  GraphRAG
─────────────────────────────────────────────────────────────────────────────────────
Fact extraction       ✅    ✅     ✅      ✅       ✅          ✅      ✅       ✅
Graph relationships   ✅    ✅     ✅✅     ✅       ✅          ✅      ❌       ✅✅
Temporal awareness    △     ✅     ✅✅     △        △           ✅      ❌       ❌
Causal beliefs        ❌    △      ❌      ❌       ✅          ❌      ❌       ❌
Sleep/background      ❌    ✅✅    ❌      ❌       △           ✅      ❌       ❌
Self-evolving notes   ❌    ✅     △       ✅       ✅          ✅      ❌       ❌
Multi-agent           ❌    △      ❌      ❌       △           ✅      ❌       ❌
Fully offline         ✅    ✅     △       ✅       ✅          ✅      ✅       ✅
Zero-LLM ops          ❌    ❌     ❌      ❌       ❌          ❌      ❌       ❌
Forgetting/curation   ❌    ✅     ✅      ✅       ✅          ✅      ❌       ❌
Memory versioning     ❌    △      ❌      ❌       ❌          ❌      ❌       ❌
Multi-strategy search ✅    ✅     ✅      ✅       ✅✅         ✅      ✅       ✅
Production stability  ✅✅   ✅     ✅✅     ✅       ✅          △       ✅       ✅

✅✅ = Best in class  ✅ = Good  △ = Partial  ❌ = Missing
```

---

## 9. WHAT IGNIS SHOULD BUILD

Based on the gap analysis, the things that **don't exist** and would be genuinely differentiated:

### Killer Feature Set for a Local-First Agent Memory:

1. **Belief Store over Fact Store** — Store "lessons with confidence" not just "facts with timestamps." Causal, confidence-scaled, evidence-trailed.

2. **Zero-LLM ingestion path** — Use embedding-only (no LLM call) for initial memory writes. LLM only for consolidation/reflection during idle time.

3. **Automatic memory curation** — Background process that: deduplicates, resolves contradictions, decays stale memories, promotes high-confidence ones. Like a sleep cycle for your memory DB.

4. **Temporal awareness built-in** — Every memory has a validity window. "User prefers X" should have first_seen, last_confirmed, times_seen metadata.

5. **Git-like memory versioning** — Memories can be branched, diffed, and reverted. If a consolidation pass goes wrong, roll back.

6. **Multi-scope by design** — project, user, agent, session — with clear isolation and optional cross-pollination.

7. **Pluggable vector backend** — SQLite+vec0 for local, Qdrant for bigger, optional cloud.

8. **MCP server interface** — Any compatible agent (Claude Code, Cursor, Codex, etc.) should plug in trivially.

None of the existing solutions combine all of these. The closest is Letta + some research patches.

---

## 10. KEY PAPERS TO READ

| Paper | Why |
|---|---|
| **Mem0** (ECAI 2025, arXiv:2504.19413) | Best head-to-head comparison of 10 memory approaches |
| **Memory in the Age of AI Agents** (2025, arXiv:2512.13564) | 102-page survey, 47 authors — the bible |
| **Memory for Autonomous LLM Agents** (2026, arXiv:2603.07670) | Five mechanism families taxonomy |
| **SleepGate** (2026, arXiv:2603.14517) | Sleep-inspired KV cache consolidation |
| **ZenBrain** (2026, arXiv:2604.23878) | 15 neuroscience mechanisms, near-oracle |
| **A-MEM** (NeurIPS 2025, arXiv:2502.12110) | Zettelkasten-inspired dynamic memory |
| **MemoryOS** (EMNLP 2025, arXiv:2506.06326) | Three-tier hierarchy, +49% F1 |
| **Hindsight** (2025, arXiv:2512.12818) | Institutional knowledge focus |
| **FSFM** (2026, arXiv:2604.20300) | Forgetting taxonomy |
| **The Memory Problem Is Half Solved** (Medium 2026) | Belief store concept, very practical |

---

*Research compiled June 2026. All pricing and features current as of retrieval date.*
