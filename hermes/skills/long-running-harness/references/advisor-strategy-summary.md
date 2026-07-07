# Advisor Strategy — Key Points

Source: https://claude.com/blog/the-advisor-strategy (April 9, 2026)

## Core Idea

Pair **Opus as an advisor** with **Sonnet/Haiku as an executor**. The executor drives the task end-to-end; the advisor provides guidance only when the executor asks. This gets near-Opus intelligence at near-Sonnet cost.

## How It Works

- Sonnet/Haiku runs the full task — calling tools, reading results, iterating
- When the executor hits a decision it can't solve, it invokes the `advisor_20260301` tool
- Opus sees the curated context and returns a plan, correction, or stop signal
- The executor resumes — the advisor never calls tools or produces user-facing output

## Key Insight: Inverts Sub-Agent Pattern

Common pattern: large orchestrator decomposes work → delegates to workers.
Advisor strategy: **small model drives** → **escalates selectively** → no decomposition, no worker pool.

## API Usage

```python
tools=[{
    "type": "advisor_20260301",
    "name": "advisor",
    "model": "claude-opus-4-6",
    "max_uses": 3,  # Cap advisor calls per request
}]
```

## Cost Profile

- Advisor generates short plans (400-700 text tokens)
- Executor handles full output at its lower rate
- Overall cost well below running advisor end-to-end
- `max_uses` prevents runaway advisor calls

## Benchmark Results

- Sonnet + Opus advisor: **+2.7pp** on SWE-bench Multilingual vs Sonnet alone
- **-11.9% cost per agentic task** vs Sonnet alone
- Haiku + Opus advisor: **41.2% on BrowseComp** (vs 19.7% solo Haiku)
- Haiku + Opus: 85% less per task than Sonnet

## Implications for Harness Design

1. The executor doesn't need to be Opus — it just needs Opus on speed-dial
2. The advisor works best when called sparingly (max 3x per request)
3. Handoff is within a single API request — no extra round-trips
4. The executor decides WHEN to consult — no orchestration logic needed
