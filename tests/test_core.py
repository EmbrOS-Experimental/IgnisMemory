"""Tests for Mneme core memory engine."""

import os
import tempfile

import pytest

from mneme import Memory, Fact, Belief, Scope, Embedder, SqliteVecBackend, Curator


@pytest.fixture
def tmp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


@pytest.fixture
def mem(tmp_db):
    m = Memory(agent="test-agent", project="test-project", db_path=tmp_db)
    yield m
    m.close()


class TestEmbedder:
    def test_hash_embed(self):
        e = Embedder()
        v = e._hash_embed("hello world")
        assert len(v) == 384
        # Normalized
        import math
        norm = math.sqrt(sum(x**2 for x in v))
        assert abs(norm - 1.0) < 0.01

    def test_deterministic(self):
        e = Embedder()
        v1 = e._hash_embed("test")
        v2 = e._hash_embed("test")
        assert v1 == v2

    def test_different_inputs(self):
        e = Embedder()
        v1 = e._hash_embed("hello")
        v2 = e._hash_embed("goodbye")
        assert v1 != v2


class TestMemory:
    def test_write(self, mem):
        fact = mem.write("User prefers dark mode")
        assert fact.id is not None
        assert fact.content == "User prefers dark mode"
        assert fact.confidence == 0.5

    def test_write_dedup(self, mem):
        f1 = mem.write("User prefers dark mode")
        f2 = mem.write("User prefers dark mode")
        assert f1.id == f2.id
        assert f2.times_seen == 2

    def test_recall(self, mem):
        mem.write("User prefers dark mode")
        mem.write("API rate limit is 100 req/min")
        mem.write("Deployment uses Railway")

        results = mem.recall("user interface preferences")
        assert len(results) > 0
        assert any("dark mode" in r.content for r in results)

    def test_recall_empty(self, mem):
        results = mem.recall("nonexistent topic")
        assert len(results) == 0

    def test_stats(self, mem):
        mem.write("Fact 1")
        mem.write("Fact 2")
        stats = mem.stats()
        assert stats["facts"] >= 2

    def test_scope_isolation(self, tmp_db):
        m1 = Memory(agent="a1", project="shared", db_path=tmp_db)
        m2 = Memory(agent="a2", project="shared", db_path=tmp_db)

        m1.write("Agent 1 fact")
        m2.write("Agent 2 fact")

        # Both should see both facts (same project scope)
        r1 = m1.recall("fact")
        r2 = m2.recall("fact")
        assert len(r1) == 2
        assert len(r2) == 2

        m1.close()
        m2.close()


class TestCurator:
    def test_deduplicate(self, mem):
        for _ in range(3):
            mem.write("User likes dark mode")

        stats = mem.stats()
        # Should be deduplicated to 1 fact
        assert stats["facts"] == 1

    def test_promote(self, mem):
        for _ in range(20):
            mem.write("Very important fact")

        mem.curate()
        results = mem.recall("very important fact")
        if results:
            assert results[0].confidence > 0.5


class TestBeliefs:
    def test_simple_extraction(self, mem):
        mem.write("Connection pool at 20 caused CPU spike")
        mem.write("Increasing pool to 30 caused another CPU spike")
        mem.write("Reducing pool to 10 fixed the CPU issue")

        beliefs = mem.extract_beliefs()
        assert isinstance(beliefs, list)


class TestFactModel:
    def test_to_dict(self):
        f = Fact(content="test", embedding=[0.1, 0.2], scope=Scope())
        d = f.to_dict()
        assert d["content"] == "test"
        assert "id" in d

    def test_belief_to_dict(self):
        b = Belief(content="test belief", evidence=["fact-1"])
        d = b.to_dict()
        assert d["content"] == "test belief"
        assert d["evidence"] == ["fact-1"]
