# Implementation Plan: Hybrid Core+RAG Prompt Delivery

## Scope
Implement runtime prompt assembly with pinned core header plus RAG retrieval over `prompt_archive/dec_2025` prompts. No model changes.

## Milestones
1) Core header extraction
2) Index build (hybrid search)
3) Runtime assembler
4) Telemetry + tests
5) Docs/handoff

## Tasks
### 1) Core header
- Create `prompt_archive/core_header.txt` with the always-present rules (see design). Derive from current `dec_2025` prompts.
- Add small generator script to re-build core header from source snippets if needed.

### 2) Index build
- Script `tools/build_prompt_index.py`:
  - Read `prompt_archive/${PROMPT_VERSION:-dec_2025}/*.md`
  - Chunk (350–600 tokens, 10–15% overlap)
  - Compute embeddings (use existing embedding service or local model); store vectors + metadata (filename, version, domain, mode, section, heading, preview, length).
  - Build BM25 index (e.g., `rank-bm25` or SPLADE if available).
  - Persist to `data/prompt_index/<version>/` (vectors.npy/FAISS, meta.jsonl, bm25.pkl).

### 3) Retrieval + assembly
- New module `prompting/rag_prompt_loader.py`:
  - `retrieve(query, mode, version, k=12)` hybrid BM25+dense, fuse scores, re-rank to top 6 with domain/mode/recency bonuses and score floor.
  - `normalize_chunks(chunks)` adds heading + delimiter, trims to budget.
  - `assemble_prompt(user_input, mode, version)` => core_header + normalized retrieved + user input; if retrieval empty/low-score, use core only and flag `retrieval_sparse=True`.
- Config: env vars `PROMPT_VERSION`, `PROMPT_MAX_TOKENS_RETRIEVED` (default 1500), `PROMPT_RETRIEVER_SCORE_FLOOR`.
- Cache: LRU on (mode, normalized query hash) for top chunks.

### 4) Telemetry & tests
- Log chunk IDs, scores, lengths, version, `retrieval_sparse` flag (structured log).
- Unit tests:
  - Retrieval returns CR XP chunk when queried with “CR 1/4 XP”.
  - Core header always present; schema forbiddens intact.
  - God mode assembly includes mode header + `god_mode_response` slot + `god:return_story` in planning block template.
  - Time-forward rule chunk retrieved for “backward time”.
- Integration test: simulate prompt assembly for Story/DM/God; assert total token budget respected.

### 5) Docs/Handoff
- Update `roadmap/rag_hybrid_prompt_design.md` (done) and add quickstart README under `prompt_archive/README.md` with: how to rebuild index, env vars, and expected artifacts.
- Copy design + impl plan to `~/Downloads/` for the next agent.

## Deliverables
- `prompt_archive/core_header.txt`
- `tools/build_prompt_index.py`
- `prompting/rag_prompt_loader.py` (or equivalent location per codebase norms)
- Tests under `tests/prompting/test_rag_prompt_loader.py`
- Docs: `prompt_archive/README.md` + updated roadmap.

## Open decisions (for follow-up agent)
- Which embedding backend to use (local vs API) and model choice.
- Exact scoring weights for BM25 vs dense; start with 0.5/0.5 and tune.
- Whether to expose retrieved chunk IDs to the model (probably no—logging only).
