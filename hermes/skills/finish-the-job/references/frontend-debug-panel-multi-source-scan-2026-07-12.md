# Frontend Debug Mode panel reads multiple debug_info sources — multi-surface scan recipe

**Verified:** 2026-07-12, $GITHUB_REPOSITORY PR [#8337](https://github.com/$GITHUB_REPOSITORY/pull/8337) (hide state-update schema-gate warnings from the System Warnings panel). User pushback that surfaced this lesson: *"What are these screenshots I need real gameplay screenshots"*.

## The trap

When a /es evidence task says "hide warnings from the Debug Mode panel", the obvious fix is to filter the ONE obvious `debug_info` field (e.g. `_server_system_warnings`). It feels complete. You ship the PR, capture the screenshot, push.

But the user's screenshot still shows the warnings — because the frontend renderer reads **MULTIPLE** `debug_info` fields into the panel, not just the one obvious one.

Verified bug case (PR #8337 round 1):
- `$PROJECT_ROOT/narrative_response_schema.py` mirrored ALL schema-gate corrections into `_state_update_schema_gate_errors` AND prefixed copies into `_server_system_warnings`. Round 1 fix filtered `_server_system_warnings` → no more "State update schema gate: …" prefix entries.
- BUT `frontend_v1/app.js:1417-1437` ALSO reads `_state_update_schema_gate_errors` into the panel as bare strings (without the prefix).
- Result: the screenshot showed 3 prefixed bullets GONE, but 3 NEW bare `Kept state_updates.custom_campaign_state.{divin|crus|reso}` bullets appeared in the panel from the second surface.
- Jeffrey: *"What are these screenshots I need real gameplay screenshots"* — the round-1 "real" screenshots still showed warnings.

Round 2 added a new `_state_update_schema_gate_benign` key and routed benign entries there (kept for observability / GCP logs), so the frontend's surfaced lists contained only real `SCHEMA_WARNING` items.

## The 4-line recipe — multi-source scan BEFORE writing the fix

1. **Grep the renderer(s) for every `debug_info` field the panel reads.** The renderer is the source of truth for what the user sees — not the producer.
   ```bash
   grep -nE 'debug_info\._|debug_info\?._' frontend_v1/app.js frontend_v1/index.html \
     css/*.css $PROJECT_ROOT/templates/*.html
   ```
   List every field (e.g. `_server_system_warnings`, `_state_update_schema_gate_errors`, `_state_update_schema_gate_kinds`, `_system_warnings`).

2. **Filter ALL of them at the producer, not just the obvious one.** For each surfaced field, decide: benign → separate observability key (e.g. `_state_update_schema_gate_benign`); real warning → keep in the surfaced list. Don't try to mix kinds in one list — the frontend can't sort them.

3. **Capture BEFORE/AFTER screenshots AFTER all surface filters are applied, not after the first.** A round-1 fix that captures one screenshot is misleading; the user sees the cumulative state of all surfaces.

4. **Take BOTH producer-level AND real-UI screenshots.** Producer-level (a Python harness that constructs the same `NarrativeResponse` and reads `debug_info`) proves the producer is correct; real-UI (a headless Chromium run against the actual `frontend_v1/index.html` with the production renderer) proves the panel is correct. The panel renderer is the source of truth for what the user sees — producer tests alone don't catch the multi-surface case.

## Verification recipe (run before claiming "warnings hidden from panel" is done)

```bash
# 1. Enumerate all debug_info fields the renderer surfaces
grep -nE 'debug_info\._' frontend_v1/app.js | grep -vE 'get\(.*_\|kinds' | head -20
# Expected: each surfaced field listed (server warnings, gate errors, system warnings, etc.)

# 2. For each surfaced field, confirm benign entries don't appear
PYTHONPATH=. TESTING_AUTH_BYPASS=true python3 -c "
from mvp_site.narrative_response_schema import NarrativeResponse
r = NarrativeResponse(narrative='ok', state_updates={'custom_campaign_state': {'divin': 1}})
for field in ['_server_system_warnings', '_state_update_schema_gate_errors',
              '_state_update_schema_gate_benign']:
    print(field, '=>', len(r.debug_info.get(field, [])))
# Expected: surfaced fields == 0; benign-only fields > 0
"

# 3. Take real-UI screenshot (headless Chromium against frontend_v1/index.html)
# Recipe: load index.html, inject a fabricated narrative-response payload that
# triggers the warnings renderer, capture .system-warnings panel section.
# See $PROJECT_ROOT/frontend_v1/style.css .system-warnings class for the visual.
```

## Companion references

- `references/non-ui-es-evidence-harness-html-png-2026-07-12.md` — the harness → JSON → HTML → PNG → gist → PR embed pipeline for non-UI /es evidence.
- `evidence-attach-to-slack` skill — for the 3-stage `files.completeUploadExternal` upload to the Slack thread.
- `ui-change-requires-before-after-visual-proof` skill (cursor rule) — broader rule that requires real before/after screenshots for user-visible changes.

## Why this matters

Per `finish-the-job` pitfall "PR open with green CI awaiting user merge" — a green CI + producer tests + round-1 screenshot is NOT enough evidence for a panel-rendering fix. The user sees the panel; the panel is what gets reviewed. Capture it AFTER every debug_info filter is applied, against the real frontend.
