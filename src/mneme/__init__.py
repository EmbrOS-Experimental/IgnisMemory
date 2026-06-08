"""Mneme — Agent Memory Framework.

Local-first, belief-aware, self-curing memory for any AI agent.
Cross-platform. Zero cloud dependency. MIT licensed.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import numpy as np

__version__ = "0.1.0"


# ─── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class Scope:
    """Isolation boundaries for memories."""
    agent: str = "default"
    project: str = "default"
    user: str = "default"
    session: str = "default"

    def to_dict(self) -> dict[str, str]:
        return {"agent": self.agent, "project": self.project, "user": self.user, "session": self.session}

    def matches(self, other: Scope, match_project: bool = True) -> bool:
        if match_project and self.project != other.project:
            return False
        return True


@dataclass
class Fact:
    """A single ingested memory — fast, cheap, zero-LLM."""
    content: str
    embedding: list[float]
    scope: Scope
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_confirmed: str = ""
    times_seen: int = 1
    confidence: float = 0.5
    pinned: bool = False
    superseded_by: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.last_confirmed:
            self.last_confirmed = self.created

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "scope": self.scope.to_dict(),
            "created": self.created,
            "last_confirmed": self.last_confirmed,
            "times_seen": self.times_seen,
            "confidence": self.confidence,
            "pinned": self.pinned,
            "superseded_by": self.superseded_by,
            "metadata": self.metadata,
        }


@dataclass
class Belief:
    """A causal lesson extracted from facts — reasoned, confidence-scaled."""
    content: str
    evidence: list[str]  # fact IDs
    causal: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 0.5
    confirmed_count: int = 1
    contradicted_by: Optional[str] = None
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    scope: Scope = field(default_factory=Scope)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "causal": self.causal,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "confirmed_count": self.confirmed_count,
            "contradicted_by": self.contradicted_by,
            "extracted_at": self.extracted_at,
            "scope": self.scope.to_dict(),
        }


@dataclass
class RecallResult:
    """A single result from recall()."""
    id: str
    content: str
    confidence: float
    score: float
    scope: dict[str, str]
    created: str
    is_belief: bool = False
    causal: str = ""
    evidence: list[str] = field(default_factory=list)


# ─── Embedding (zero-LLM, CPU-only) ───────────────────────────────────────────

class Embedder:
    """Lightweight embedding using sentence-transformers or fallback hash.

    Priority:
    1. sentence-transformers (best quality, still CPU)
    2. Character n-gram hash embedding (zero deps, works everywhere)
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dim: int = 384):
        self.dim = dim
        self._model = None
        self._model_name = model_name

    def _load_model(self):
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
        except ImportError:
            self._model = "fallback"

    def embed(self, text: str) -> list[float]:
        self._load_model()
        if self._model == "fallback":
            return self._hash_embed(text)
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def _hash_embed(self, text: str) -> list[float]:
        """Deterministic hash-based embedding. Zero dependencies."""
        vec = np.zeros(self.dim, dtype=np.float32)
        text_lower = text.lower().strip()
        for i in range(len(text_lower) - 2):
            trigram = text_lower[i:i+3]
            h = int(hashlib.md5(trigram.encode()).hexdigest(), 16)
            idx = h % self.dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()


# ─── Storage Backend ───────────────────────────────────────────────────────────

class SqliteVecBackend:
    """Default storage: SQLite. Zero config. Works everywhere."""

    def __init__(self, db_path: str = "~/.mneme/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._init_tables()
        return self._conn

    def _init_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS facts (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                embedding BLOB,
                scope_agent TEXT DEFAULT 'default',
                scope_project TEXT DEFAULT 'default',
                scope_user TEXT DEFAULT 'default',
                scope_session TEXT DEFAULT 'default',
                created TEXT NOT NULL,
                last_confirmed TEXT NOT NULL,
                times_seen INTEGER DEFAULT 1,
                confidence REAL DEFAULT 0.5,
                pinned INTEGER DEFAULT 0,
                superseded_by TEXT,
                metadata TEXT DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS beliefs (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                causal TEXT DEFAULT '',
                evidence TEXT DEFAULT '[]',
                confidence REAL DEFAULT 0.5,
                confirmed_count INTEGER DEFAULT 1,
                contradicted_by TEXT,
                extracted_at TEXT NOT NULL,
                scope_agent TEXT DEFAULT 'default',
                scope_project TEXT DEFAULT 'default',
                scope_user TEXT DEFAULT 'default'
            );

            CREATE INDEX IF NOT EXISTS idx_facts_project ON facts(scope_project);
            CREATE INDEX IF NOT EXISTS idx_facts_agent ON facts(scope_agent);
            CREATE INDEX IF NOT EXISTS idx_facts_superseded ON facts(superseded_by);
            CREATE INDEX IF NOT EXISTS idx_beliefs_project ON beliefs(scope_project);
        """)
        self._conn.commit()

    def store_fact(self, fact: Fact):
        emb_bytes = np.array(fact.embedding, dtype=np.float32).tobytes()
        self.conn.execute("""
            INSERT INTO facts (id, content, embedding, scope_agent, scope_project,
                scope_user, scope_session, created, last_confirmed, times_seen,
                confidence, pinned, superseded_by, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            fact.id, fact.content, emb_bytes,
            fact.scope.agent, fact.scope.project, fact.scope.user, fact.scope.session,
            fact.created, fact.last_confirmed, fact.times_seen,
            fact.confidence, int(fact.pinned), fact.superseded_by,
            json.dumps(fact.metadata),
        ))
        self.conn.commit()

    def find_similar_fact(self, embedding: list[float], scope: Scope, threshold: float = 0.92) -> Optional[Fact]:
        """Find a near-duplicate fact within the same project scope."""
        rows = self.conn.execute(
            "SELECT * FROM facts WHERE scope_project = ? AND superseded_by IS NULL",
            (scope.project,)
        ).fetchall()
        if not rows:
            return None

        query_vec = np.array(embedding, dtype=np.float32)
        best = None
        best_score = 0.0

        for row in rows:
            if row["embedding"] is None:
                continue
            vec = np.frombuffer(row["embedding"], dtype=np.float32)
            score = float(np.dot(query_vec, vec))
            if score > best_score:
                best_score = score
                best = row

        if best and best_score >= threshold:
            return self._row_to_fact(best)
        return None

    def search_facts(self, query_embedding: list[float], scope: Scope,
                     limit: int = 10, since: Optional[str] = None) -> list[tuple[Fact, float]]:
        """Semantic search within scope."""
        rows = self.conn.execute(
            "SELECT * FROM facts WHERE scope_project = ? AND superseded_by IS NULL",
            (scope.project,)
        ).fetchall()

        query_vec = np.array(query_embedding, dtype=np.float32)
        scored: list[tuple[Fact, float]] = []

        for row in rows:
            if row["embedding"] is None:
                continue
            if since and row["created"] < since:
                continue
            vec = np.frombuffer(row["embedding"], dtype=np.float32)
            score = float(np.dot(query_vec, vec))
            fact = self._row_to_fact(row)
            scored.append((fact, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def search_keyword(self, query: str, scope: Scope, limit: int = 10) -> list[tuple[Fact, float]]:
        """Keyword search within scope."""
        terms = query.lower().split()
        if not terms:
            return []

        conditions = " OR ".join(["content LIKE ?"] * len(terms))
        params = [f"%{t}%" for t in terms] + [scope.project]

        rows = self.conn.execute(
            f"SELECT * FROM facts WHERE ({conditions}) AND scope_project = ? AND superseded_by IS NULL",
            params
        ).fetchall()

        results: list[tuple[Fact, float]] = []
        for row in rows:
            fact = self._row_to_fact(row)
            content_lower = fact.content.lower()
            matches = sum(1 for t in terms if t in content_lower)
            score = matches / len(terms)
            results.append((fact, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_all_facts(self, scope: Scope) -> list[Fact]:
        rows = self.conn.execute(
            "SELECT * FROM facts WHERE scope_project = ? AND superseded_by IS NULL ORDER BY created DESC",
            (scope.project,)
        ).fetchall()
        return [self._row_to_fact(r) for r in rows]

    def update_fact(self, fact: Fact):
        emb_bytes = np.array(fact.embedding, dtype=np.float32).tobytes()
        self.conn.execute("""
            UPDATE facts SET content=?, embedding=?, last_confirmed=?, times_seen=?,
                confidence=?, pinned=?, superseded_by=?, metadata=?
            WHERE id=?
        """, (
            fact.content, emb_bytes, fact.last_confirmed, fact.times_seen,
            fact.confidence, int(fact.pinned), fact.superseded_by,
            json.dumps(fact.metadata), fact.id,
        ))
        self.conn.commit()

    def store_belief(self, belief: Belief):
        self.conn.execute("""
            INSERT INTO beliefs (id, content, causal, evidence, confidence,
                confirmed_count, contradicted_by, extracted_at,
                scope_agent, scope_project, scope_user)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            belief.id, belief.content, belief.causal,
            json.dumps(belief.evidence), belief.confidence,
            belief.confirmed_count, belief.contradicted_by, belief.extracted_at,
            belief.scope.agent, belief.scope.project, belief.scope.user,
        ))
        self.conn.commit()

    def search_beliefs(self, query: str, scope: Scope, limit: int = 5) -> list[tuple[Belief, float]]:
        terms = query.lower().split()
        if not terms:
            return []

        conditions = " OR ".join(["content LIKE ?"] * len(terms))
        params = [f"%{t}%" for t in terms] + [scope.project]

        rows = self.conn.execute(
            f"SELECT * FROM beliefs WHERE ({conditions}) AND scope_project = ?",
            params
        ).fetchall()

        results: list[tuple[Belief, float]] = []
        for row in rows:
            belief = self._row_to_belief(row)
            content_lower = belief.content.lower()
            matches = sum(1 for t in terms if t in content_lower)
            score = matches / len(terms) * belief.confidence
            results.append((belief, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def get_stats(self, scope: Scope) -> dict:
        facts_count = self.conn.execute(
            "SELECT COUNT(*) FROM facts WHERE scope_project = ? AND superseded_by IS NULL",
            (scope.project,)
        ).fetchone()[0]
        beliefs_count = self.conn.execute(
            "SELECT COUNT(*) FROM beliefs WHERE scope_project = ?",
            (scope.project,)
        ).fetchone()[0]
        return {"facts": facts_count, "beliefs": beliefs_count}

    def _row_to_fact(self, row) -> Fact:
        emb = list(np.frombuffer(row["embedding"], dtype=np.float32)) if row["embedding"] else []
        return Fact(
            id=row["id"],
            content=row["content"],
            embedding=emb,
            scope=Scope(
                agent=row["scope_agent"],
                project=row["scope_project"],
                user=row["scope_user"],
                session=row["scope_session"],
            ),
            created=row["created"],
            last_confirmed=row["last_confirmed"],
            times_seen=row["times_seen"],
            confidence=row["confidence"],
            pinned=bool(row["pinned"]),
            superseded_by=row["superseded_by"],
            metadata=json.loads(row["metadata"] or "{}"),
        )

    def _row_to_belief(self, row) -> Belief:
        return Belief(
            id=row["id"],
            content=row["content"],
            causal=row["causal"],
            evidence=json.loads(row["evidence"] or "[]"),
            confidence=row["confidence"],
            confirmed_count=row["confirmed_count"],
            contradicted_by=row["contradicted_by"],
            extracted_at=row["extracted_at"],
            scope=Scope(
                agent=row["scope_agent"],
                project=row["scope_project"],
                user=row["scope_user"],
            ),
        )

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ─── Curation Engine ───────────────────────────────────────────────────────────

class Curator:
    """Automatic memory maintenance: dedup, decay, promote."""

    def __init__(self, backend: SqliteVecBackend, embedder: Embedder):
        self.backend = backend
        self.embedder = embedder

    def curate(self, scope: Scope):
        """Run full curation pass. Call during idle time."""
        self.deduplicate(scope)
        self.decay(scope)
        self.promote(scope)

    def deduplicate(self, scope: Scope, threshold: float = 0.92):
        """Merge near-duplicate facts."""
        facts = self.backend.get_all_facts(scope)
        merged = set()

        for i, fact_a in enumerate(facts):
            if fact_a.id in merged:
                continue
            for fact_b in facts[i+1:]:
                if fact_b.id in merged:
                    continue
                if not fact_a.embedding or not fact_b.embedding:
                    continue
                score = float(np.dot(
                    np.array(fact_a.embedding),
                    np.array(fact_b.embedding)
                ))
                if score >= threshold:
                    fact_a.times_seen += fact_b.times_seen
                    fact_a.confidence = min(1.0, fact_a.confidence + 0.05)
                    fact_a.last_confirmed = max(fact_a.last_confirmed, fact_b.last_confirmed)
                    fact_b.superseded_by = fact_a.id
                    self.backend.update_fact(fact_a)
                    self.backend.update_fact(fact_b)
                    merged.add(fact_b.id)

    def decay(self, scope: Scope, rate: float = 0.01):
        """Ebbinghaus-inspired decay for unconfirmed memories."""
        facts = self.backend.get_all_facts(scope)
        now = datetime.now(timezone.utc)

        for fact in facts:
            if fact.pinned:
                continue
            created = datetime.fromisoformat(fact.created)
            days_old = (now - created).total_seconds() / 86400
            decay_factor = math.exp(-rate * days_old)
            new_confidence = fact.confidence * decay_factor
            if abs(new_confidence - fact.confidence) > 0.01:
                fact.confidence = max(0.05, new_confidence)
                self.backend.update_fact(fact)

    def promote(self, scope: Scope, threshold: float = 0.9):
        """Pin high-confidence memories."""
        facts = self.backend.get_all_facts(scope)
        for fact in facts:
            if fact.confidence >= threshold and not fact.pinned:
                fact.pinned = True
                self.backend.update_fact(fact)


# ─── Belief Extraction ─────────────────────────────────────────────────────────

class BeliefExtractor:
    """Extract causal beliefs from clusters of facts. Uses LLM only during idle."""

    def __init__(self, backend: SqliteVecBackend, llm_client=None):
        self.backend = backend
        self.llm = llm_client

    def extract(self, scope: Scope) -> list[Belief]:
        if self.llm is None:
            return self._extract_simple(scope)
        return self._extract_with_llm(scope)

    def _extract_simple(self, scope: Scope) -> list[Belief]:
        """Rule-based extraction (no LLM needed)."""
        facts = self.backend.get_all_facts(scope)
        beliefs = []

        for fact in facts:
            if fact.confidence < 0.7:
                continue
            content = fact.content.lower()
            causal_markers = [
                "causes", "leads to", "results in", "because", "due to",
                "after", "then", "→", "->", "failed", "error", "fixed",
                "caused", "made", "increased", "decreased", "broke",
            ]
            if any(m in content for m in causal_markers):
                belief = Belief(
                    content=fact.content,
                    evidence=[fact.id],
                    confidence=fact.confidence * 0.8,
                    scope=fact.scope,
                )
                self.backend.store_belief(belief)
                beliefs.append(belief)

        return beliefs

    def _extract_with_llm(self, scope: Scope) -> list[Belief]:
        """Dual-agent extraction: extractor + challenger."""
        facts = self.backend.get_all_facts(scope)
        if len(facts) < 3:
            return []

        candidates = [f for f in facts if f.confidence > 0.5]
        if not candidates:
            return []

        beliefs = []
        for i in range(0, len(candidates) - 2, 3):
            cluster = candidates[i:i+3]
            texts = [f.content for f in cluster]

            extract_prompt = f"""Given these observations, extract one causal belief (a lesson about WHY something happens):

Observations:
{chr(10).join(f"- {t}" for t in texts)}

Respond with JSON: {{"belief": "...", "causal": "X causes Y", "confidence": 0.0-1.0}}
If no causal pattern exists, respond: {{"belief": null}}"""

            try:
                response = self.llm.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": extract_prompt}],
                    response_format={"type": "json_object"},
                )
                result = json.loads(response.choices[0].message.content)

                if result.get("belief"):
                    challenge_prompt = f"""Is this belief actually supported by the observations?

Observations:
{chr(10).join(f"- {t}" for t in texts)}

Proposed belief: {result['belief']}

Respond with JSON: {{"valid": true/false, "reason": "..."}}"""

                    challenge = self.llm.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": challenge_prompt}],
                        response_format={"type": "json_object"},
                    )
                    challenge_result = json.loads(challenge.choices[0].message.content)

                    if challenge_result.get("valid", False):
                        belief = Belief(
                            content=result["belief"],
                            causal=result.get("causal", ""),
                            evidence=[f.id for f in cluster],
                            confidence=result.get("confidence", 0.5),
                            scope=scope,
                        )
                        self.backend.store_belief(belief)
                        beliefs.append(belief)
            except Exception:
                continue

        return beliefs


# ─── Main Memory Interface ─────────────────────────────────────────────────────

class Memory:
    """Primary interface. One instance per agent+project pair."""

    def __init__(
        self,
        agent: str = "default",
        project: str = "default",
        user: str = "default",
        db_path: str = "~/.mneme/memory.db",
        llm_client=None,
    ):
        self.scope = Scope(agent=agent, project=project, user=user)
        self.embedder = Embedder()
        self.backend = SqliteVecBackend(db_path)
        self.curator = Curator(self.backend, self.embedder)
        self.extractor = BeliefExtractor(self.backend, llm_client)

    def write(self, content: str, metadata: dict | None = None) -> Fact:
        """Ingest a memory. Zero LLM calls. CPU only."""
        embedding = self.embedder.embed(content)

        existing = self.backend.find_similar_fact(embedding, self.scope)
        if existing:
            existing.times_seen += 1
            existing.last_confirmed = datetime.now(timezone.utc).isoformat()
            existing.confidence = min(1.0, existing.confidence + 0.02)
            if metadata:
                existing.metadata.update(metadata)
            self.backend.update_fact(existing)
            return existing

        fact = Fact(
            content=content,
            embedding=embedding,
            scope=self.scope,
            metadata=metadata or {},
        )
        self.backend.store_fact(fact)
        return fact

    def recall(self, query: str, limit: int = 5) -> list[RecallResult]:
        """Multi-strategy retrieval: semantic + keyword + beliefs."""
        query_emb = self.embedder.embed(query)

        semantic_results = self.backend.search_facts(query_emb, self.scope, limit=limit)
        keyword_results = self.backend.search_keyword(query, self.scope, limit=limit)
        belief_results = self.backend.search_beliefs(query, self.scope, limit=limit // 2 + 1)

        seen: dict[str, RecallResult] = {}

        for fact, score in semantic_results:
            if fact.id not in seen:
                seen[fact.id] = RecallResult(
                    id=fact.id, content=fact.content,
                    confidence=fact.confidence, score=score,
                    scope=fact.scope.to_dict(), created=fact.created,
                )

        for fact, score in keyword_results:
            if fact.id in seen:
                seen[fact.id].score = max(seen[fact.id].score, score * 0.8)
            else:
                seen[fact.id] = RecallResult(
                    id=fact.id, content=fact.content,
                    confidence=fact.confidence, score=score * 0.8,
                    scope=fact.scope.to_dict(), created=fact.created,
                )

        for belief, score in belief_results:
            if belief.id not in seen:
                seen[belief.id] = RecallResult(
                    id=belief.id, content=belief.content,
                    confidence=belief.confidence, score=score,
                    scope=belief.scope.to_dict(), created=belief.extracted_at,
                    is_belief=True, causal=belief.causal,
                    evidence=belief.evidence,
                )

        results = sorted(seen.values(), key=lambda r: r.score * r.confidence, reverse=True)
        return results[:limit]

    def extract_beliefs(self) -> list[Belief]:
        """Extract causal beliefs. Uses LLM if available."""
        return self.extractor.extract(self.scope)

    def curate(self):
        """Run curation pass. Call during idle time."""
        self.curator.curate(self.scope)

    def stats(self) -> dict:
        return self.backend.get_stats(self.scope)

    def close(self):
        self.backend.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
