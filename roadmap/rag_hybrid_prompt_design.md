# Hybrid Core+RAG Prompt Delivery (Design)

## Context (what this repo/app is)
- **WorldArchitect.AI**: A browser-based narrative + mechanics runner for D&D‑style RPG campaigns. It uses large prompts to instruct an LLM (Story/DM/God modes) to manage state, narrate, roll dice, and enforce safety rules (e.g., MBTI/alignment internal-only). Prompts live in `mvp_site/prompts/` and are versioned snapshots in `prompt_archive/`.
- Current pain: prompts are long; truncation drops safety/format rules. We need a hybrid approach that pins critical rules and retrieves the rest via RAG.

## Goals
- Keep non-negotiable schema/safety instructions **always present** (no truncation risk).
- Shrink per-turn prompt tokens by retrieving only relevant sections from archived prompts.
- Support versioned prompt sets (starting with `prompt_archive/dec_2025`) and easy rollbacks.
- Improve faithfulness vs. truncation while keeping latency manageable.

## High-level approach
- **Pinned Core Header**: Small, static text injected every turn with essential rules.
- **RAG Layer**: Retrieve top, relevant chunks from archived prompts (hybrid BM25 + dense) and append below the core header.
- **Fallback**: If retrieval fails/low-score, respond with core header only (flag for logs).

## What must be in the Core Header (always present)
- Mode declaration and requirements: Story, DM, God; mode header line required; God uses `god_mode_response`, `god:` prefixed choices, default `god:return_story`.
- JSON response schema and **FORBIDDEN** list (no extra fields, no debug/state in narrative, no markdown code fences, no text outside JSON except mode line).
- Planning blocks required in Story; snake_case; Deep Think rule (no narrative advance; pros/cons/confidence).
- Dice protocol: real code execution for rolls; show DC/AC; advantage shows both dice.
- Session header/resources format; Level 1 half‑casters show “No Spells Yet (Level 2+).”
- `state_updates` mandatory every turn; narrow-path updates; entity ID format; deletes via "__DELETE__".
- Time-forward-only; rest/travel costs; +1 microsecond for think blocks; backward time only via explicit God.
- Safety: MBTI/alignment/Big Five INTERNAL ONLY—never in narrative.

## What lives in RAG
- Mechanics detail: XP by CR table, class resources, leveling tables.
- Narrative protocols: complication system, NPC autonomy, living world, world-gen hooks.
- Examples and extended guidance (e.g., companion generation rules, opening scene tips).
- Less-frequent schemas (location/NPC details), long-form explanations.

## Corpus & chunking
- Source: `prompt_archive/dec_2025/*.md` (later versions via env `PROMPT_VERSION`).
- Chunking: 350–600 tokens, 10–15% overlap; keep headings with chunks; store preview (first ~200 chars) for logging.
- Metadata tags per chunk: filename, version, domain (schema|safety|mechanics|narrative|worldgen|examples), mode (story|dm|god|general), section (heading path), date, length.

## Retrieval strategy
- Hybrid: BM25 (or SPLADE) + dense embeddings; weighted fusion; take top 12, re-rank to top 6 with bonuses for domain/mode match and same version; enforce score floor (e.g., 0.25 fused).
- Budget: cap retrieved context to ~1–1.5k tokens; drop lowest-scoring chunks if over budget.
- Normalization: prepend each chunk with its heading and wrap in a standard delimiter to keep formatting consistent.
- Cache: LRU on (mode, query hash) for top chunks.

## Assembly flow
1) Core header (static file `prompt_archive/core_header.txt`).
2) Retrieved context (normalized, ordered by re-rank).
3) User/system turn content.
4) If retrieval empty/low-score → core only, set `retrieval_sparse` flag in logs.

## Storage & refresh
- Index artifacts under `data/prompt_index/<version>/` (FAISS or similar + bm25 + meta JSONL).
- Rebuild index when `PROMPT_VERSION` changes or prompts update.

## Telemetry & safety
- Log chunk IDs, version, scores, lengths, retrieval_sparse flag; optional DM-only source list for debugging.
- Core header enforces MBTI/alignment ban even if retrieval misses.
- If we later add private data, ensure ACL-aware retrieval + redaction before assembly.

## Evaluation (acceptance gates)
- Needle tests: CR XP queries pull correct chunk; time-forward rule retrieved; forbidden list intact.
- Policy tests: no MBTI/alignment leakage in narrative.
- Schema tests: responses validate against JSON contract with core header only.
- Latency: benchmark vs. current prompt; target similar or better with caching.
- Retrieval quality: >90% recall on curated queries (RAGAS or similar), manual spot-checks.

## Risks & mitigations
- Retrieval miss → core header + score floor + logging to detect.
- Latency → cache, fused retrieval, trimmed context budget.
- Stale index → re-index on prompt change; store versioned indices.
- Formatting drift → normalization wrapper; tests on assembled prompt.

## Artifacts to produce (separate plan file covers implementation)
- `prompt_archive/core_header.txt`
- Index build script; runtime retriever/assembler; tests; docs/README for ops.
