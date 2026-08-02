# PR #8418 driven to green — module-global-flag-race v1.1.0 corrections (2026-07-17)

Follow-up to `references/2026-07-16-bq-is-test-null-pr-8418.md`. That
reference captured the design + tests; this one captures the **three
corrections CodeRabbit review caught** AND the **8-section PR description
gate choreography** used to drive the PR to green.

## Headline result

PR [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418) landed
GREEN on SHA `3bd900ffb1`:

- GATE-1 (CI), GATE-2 (mergeable), GATE-3 (CodeRabbit APPROVED),
  GATE-4 (Bugbot clean), GATE-5 (comments resolved),
  GATE-6 (PR description gate + gist evidence),
  GATE-8 (mcp-smoke-tests #137615 real-mode).
- 65/65 tests pass with `GOOGLE_APPLICATION_CREDENTIALS=/dev/null`
  reproducing the CI failure mode.

## Correction 1: Cooldown re-check inside the lock (the third gate)

The Step-4 helper in SKILL.md has TWO double-checks under `_migration_lock`
(TTL re-check + populate). It was missing the THIRD: a cooldown re-check.
Without it, a thread that races past the first cooldown gate, queues on
`_migration_lock`, then enters the try-block and re-hammers BQ even
though a sibling already stamped `_payloads_schema_refresh_attempted_at`
during the wait. CodeRabbit Issue 1 (2026-07-17) flagged this gap
verbatim. Fix:

```python
with _migration_lock:
    cached_set = _payloads_schema_set
    if cached_set is not None and (time.monotonic() - _payloads_schema_cached_at) < _payloads_schema_ttl_seconds:
        return True
    # NEW: third gate — re-check the cooldown stamp a sibling may have just set.
    if (time.monotonic() - _payloads_schema_refresh_attempted_at) < _payloads_schema_refresh_cooldown:
        return False
    try:
        token, project = _get_token_and_project()
        new_set = _refresh_payloads_schema_set(token, project)
        _payloads_schema_set = new_set
        _payloads_schema_cached_at = time.monotonic()
        return True
    except (RequestException, GoogleAuthError, RuntimeError) as exc:
        _payloads_schema_refresh_attempted_at = time.monotonic()
        logging.warning(f"BQ logging: payloads schema refresh failed: {exc}")
        return False
```

Pin it with `test_schema_refresh_cooldown_holds_under_lock_acquire`:
pre-arm `_payloads_schema_refresh_attempted_at` to a recent value, two
threads barrier-sync, the second thread to acquire the lock observes the
freshly-stamped cooldown and aborts WITHOUT calling the mock refresh.

## Correction 2: `_GATED_COLUMNS` is the authoritative declaration

The Step-3 code block in SKILL.md showed an inline `gated = {...}` dict
at the call site. This was CodeRabbit Issue 2 — the inline dict drifts
from the `_GATED_COLUMNS` tuple that downstream consumers (audit logs,
migration tests, type stubs) iterate. Fix: hoist `_GATED_COLUMNS` to the
authoritative declaration and split the values into a sibling mapping.

```python
gated_values: dict[str, object] = {
    "user_id": uid, "is_test": test_flag, "cached_tokens": cached_tokens,
    "thoughts_tokens": thoughts_tokens, "tool_use_tokens": tool_use_tokens,
    "rag_mode": rag_mode,
}
for column_name in _GATED_COLUMNS:
    if column_name in live_columns:
        row[column_name] = gated_values[column_name]
```

Adding a future gated column is now a single-line tuple change; it
cannot drift from the iteration.

## Correction 3: `_get_token_and_project` must be mocked in CI tests

This is the most expensive lesson from the session. CI runners use
`GOOGLE_APPLICATION_CREDENTIALS=/dev/null` as a deliberate safety stub.
`_get_token_and_project()` reads this env var via `google.auth.default()`
and raises `DefaultCredentialsError` BEFORE
`_refresh_payloads_schema_set(token, project)` is called. The exception
is caught at the `(GoogleAuthError, ...)` except block, which sets
`_payloads_schema_refresh_attempted_at` and logs the warning — making
the test look like "refresh failed" when in reality the mock was
bypassed entirely.

Symptom: `_payloads_schema_refresh_attempted_at` is non-zero AFTER the
test, mock call count is 0, and the warning log mentions
`File /dev/null is not a valid json file` (google-auth's stub-load
failure message).

Fix: every cache-refresh test must patch BOTH `_refresh_payloads_schema_set`
AND `_get_token_and_project`:

```python
monkeypatch.setattr(bq_logging, "_refresh_payloads_schema_set", mock_refresh)
monkeypatch.setattr(bq_logging, "_get_token_and_project", lambda: ("mock-token", "mock-project"))
```

Local repro recipe (always run before pushing):

```bash
GOOGLE_APPLICATION_CREDENTIALS=/dev/null /tmp/wa-py-8418/bin/python -m pytest \
  $PROJECT_ROOT/tests/test_bq_logging.py -x -n auto --dist=loadfile
```

If the test passes locally WITHOUT this env var and FAILS with it, the
test is missing the `_get_token_and_project` mock. This is the most
common cause of "tests pass locally but fail on CI" for any module that
wraps `_refresh_payloads_schema_set` patterns.

## Bonus: `tables.get` response-shape validation (defensive)

Pre-8418 code was `fields = resp.json().get("schema", {}).get("fields", [])`
— silently returns `[]` on a malformed response. Post-8418 validates
the shape (dict body, dict schema, list fields) before caching, raising
`RuntimeError` that lands in the same except block. This prevents a
malformed `tables.get` response from looking identical to "table has
zero columns" and dropping ALL gated columns for the TTL window.

## The 8-section PR description gate choreography

Driving the PR to green required populating ALL 8 sections of
`.github/scripts/pr_description_gate.py` `SECTION_HEADERS`. The
choreography (in order):

1. `## Summary` — 1-3 line headline of the fix
2. `## Tenets` — 3-5 numbered design tenets (Fail-loud, Lock-held invariants, etc.)
3. `## Design Decision` — paragraph-form explanation + linked bead ID
   **inside this section** (the gate validates bead references inside
   the Design Decision section specifically, not at the bottom of the body)
4. `## Production Code Changes` — bullet list of files + functions + line ranges
5. `## Test Changes` — bullet list of new/modified tests
6. `## Known Limitations` — at least one bullet (steady-state cost, latency, bypass cases)
7. `## Unit Test Evidence` — exact pytest command + counts (anchor: a
   code block ≥80 chars OR a URL)
8. `## Non-Unit Test Evidence` — at least one `/end2end-testing` payload
   marker OR a real LLM response (the gate validates the END2END_MARKERS
   tuple against this section's content). Backend-only changes still
   need this because `is_backend=true` triggers the conditional rule
9. `## Real LLM Evidence` — for prompt-touching changes; for this PR
   (no prompt change), an explicit "Not applicable" is acceptable
10. `## Evidence` — must contain an evidence-link anchor (`.mp4|.gif|.png|.jpg|
    webp|loom.com|asciinema.org|youtube.com|gist.github.com|/gist|
    user-attachments`)

Two failure modes observed in this session:

- The `gh api` GraphQL rate limit hit twice, causing the validator
  to fall back to local git diff + REST API. When the API is degraded,
  the gate SKIPS certain checks (it does NOT fail-open); expect the
  precheck to run but report "gh api degraded" warnings in the logs.
- The GATE-6 evidence-link heuristic looks at PR body + PR comments,
  not just the body. If your PR body has a GitHub PR URL but no gist,
  the gate fails with `GATE-6 FAIL: evidence required but no evidence
  link found`. Add the gist URL inside the `## Evidence` section.

## Cross-references

- `references/2026-07-16-bq-is-test-null-pr-8418.md` — original v1.0.0 design + tests
- `~/.hermes/skills/software-development/wa-green-gate-pr-shape/SKILL.md` — the broader PR-shape discipline
- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` — the green-driving recipe
- Skill: `~/.hermes/skills/software-development/module-global-flag-race/SKILL.md`
- Fix PR: [#8418](https://github.com/$GITHUB_REPOSITORY/pull/8418)
- Beads: `rev-2l2x6` (this PR) → `rev-uh0ek` (root alert)
- Slack thread: `C0BCVG4F560/1784219487.851579`
