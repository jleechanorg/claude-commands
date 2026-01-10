# Merge Decisions: main -> claude/test-and-fix-system-prompt-RiZyM

Date: 2026-01-09
Merge commit: 7f89d7df7

## Conflicts Resolved

1) `.beads/issues.jsonl`
- Decision: Keep all entries from both sides.
- Reason: JSONL is append-only; dropping entries would lose issue history.

2) `mvp_site/entity_validator.py`
- Decision: Use `Optional[...]` type annotations.
- Reason: File already imports `Optional`; keeps typing style consistent with module.

3) `mvp_site/game_state.py`
- Decision: Keep `_coerce_int` overloads for precise typing; use `datetime.timezone.utc` for timestamps.
- Reason: Overloads provide better type hints; timezone usage matches existing file patterns.

4) `mvp_site/llm_service.py`
- Decision: Keep `BaseAgent` import with `# noqa: F401`.
- Reason: Aligns with main branch expectations; no runtime behavior change.

5) `mvp_site/narrative_response_schema.py`
- Decision: Include **both** `items_used` and `social_hp_challenge` in `to_dict`.
- Reason: Preserve audit trail plus new Social HP schema field.

6) `mvp_site/narrative_sync_validator.py`
- Decision: Use `Optional[...]` annotations for consistency with module imports.

7) `testing_mcp/lib/evidence_utils.py`
- Decision: Merge metadata to include run/iteration/bundle_version **and** evidence standards fields (`git_provenance`, `server`, `timestamp`).
- Reason: Preserve new versioned evidence format while satisfying evidence standards.

## Did we drop anything from main?
No. All main-branch changes were preserved. Where conflicts existed, the resolution either kept the main behavior intact or merged in additional fields without removing main content.
