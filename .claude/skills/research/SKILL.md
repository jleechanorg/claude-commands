---
name: research
description: Systematic multi-source research combining ultra-depth thinking (/thinku) with multi-engine search (/perp) — academic rigor, source verification, and structured findings. Use when the user asks to research a topic, evaluate libraries/frameworks, investigate best practices, or wants a cited, cross-validated research report. Slash command: /research.
---

# /research — Academic and Technical Research

**Purpose**: Systematic research using multiple information sources with academic rigor.

**Usage**: `/research <topic>` — conduct comprehensive research on a specific topic.

## Execution workflow

### Phase 0 — Memory search context (parallel)

Run a full memory search in the background while research proceeds, so known
facts aren't re-discovered:
```
/e /memory_search "$ARGUMENTS"
```
Display results as "Prior Knowledge Found" before continuing to Phase 1.

### Phase 1 — Execution standards

- Use WebFetch to confirm content before citing it.
- Document which sources were successfully read vs failed.
- Never present search-result URLs as evidence without reading them.
- Never claim source content based on search snippet descriptions alone.

### Phase 2 — Research planning (`/thinku`)

Ultra-depth thinking: define research scope/objectives, key questions,
search strategy, anticipated gaps, and integration approach.

### Phase 3 — Multi-source gathering (`/perp`)

Search across Claude WebSearch, Perplexity (citations + recency), DuckDuckGo
(alternative perspectives), Grok (real-time trends), and Gemini (technical
consultation). Cross-validate and organize findings by source and credibility.

### Phase 4 — Deep analysis integration (`/thinku` + findings)

Synthesize across sources: identify patterns/contradictions, evaluate
credibility and recency, generate insights beyond any single source.

### Phase 5 — Structured documentation

Report: Research Planning → Information Sources (by engine) → Analysis
Integration → Evidence-based Conclusions with source attribution.

## Current date awareness

Capture today's date before framing queries or judging source freshness:
```sh
CURRENT_DATE=$(date "+%Y-%m-%d")
```
Fallback if `date` fails: `python3 -c "from datetime import datetime; print(datetime.now().strftime('%Y-%m-%d'))"`.

## Research integrity protocol

1. **Search ≠ Sources** — web search results are leads, not verified evidence.
2. **WebFetch before cite** — only cite URLs after successfully reading content.
3. **Transparent failures** — report clearly when a source couldn't be accessed.
4. **Evidence-based claims** — every assertion must trace to content actually read.

## When to use vs. related commands

- `/perp` — multi-engine search alone, no deep-thinking integration.
- `/thinku` — deep thinking alone, no comprehensive search.
- `/arch` — architecture-specific design research.
- `/research` = `/thinku` + `/perp` + integration — full academic research methodology.

Good for: technical architecture decisions, library/framework evaluation, best
practice research, academic/scientific topics, market/trend research,
troubleshooting complex issues.

**Memory enhancement**: automatically searches memory context (Memory MCP /
`/memory_search`) for relevant past research methodologies and patterns to
inform strategy and result quality.
