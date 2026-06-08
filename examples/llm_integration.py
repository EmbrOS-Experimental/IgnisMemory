"""Example: Integrating Mneme with an LLM client for belief extraction."""

from mneme import Memory


def example_with_openai():
    """Use OpenAI for dual-agent belief extraction."""
    from openai import OpenAI

    llm = OpenAI()  # Uses OPENAI_API_KEY env var

    mem = Memory(
        agent="coding-agent",
        project="backend-api",
        llm_client=llm,
    )

    # Accumulate facts over multiple sessions
    mem.write("Increasing connection pool to 20 → CPU +15%, timeouts unchanged")
    mem.write("Increasing connection pool to 30 → CPU +35%, OOM kill")
    mem.write("Reducing pool to 5 → CPU normal, timeouts fixed")
    mem.write("Pool size doesn't affect timeouts, only CPU/memory")

    # Extract beliefs with dual-agent (extractor + challenger)
    beliefs = mem.extract_beliefs()
    for b in beliefs:
        print(f"💡 Belief: {b.content}")
        print(f"   Causal: {b.causal}")
        print(f"   Confidence: {b.confidence:.0%}")
        print(f"   Evidence: {len(b.evidence)} facts")

    mem.close()


def example_with_ollama():
    """Use Ollama (local) for belief extraction."""
    from openai import OpenAI

    # Ollama exposes an OpenAI-compatible API
    llm = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # Any non-empty string
    )

    mem = Memory(
        agent="local-agent",
        project="my-app",
        llm_client=llm,
    )

    mem.write("User asked for Romanian language support")
    mem.write("User switched interface to Romanian twice this week")
    mem.write("User's browser language is ro-RO")

    beliefs = mem.extract_beliefs()
    for b in beliefs:
        print(f"💡 {b.content}")

    mem.close()


if __name__ == "__main__":
    # Run with OpenAI
    # example_with_openai()

    # Or with Ollama (local)
    # example_with_ollama()
    pass
