# WA Gemini 3.6 + 3.5 Flash Lite Settings Dropdown — Selectable-Option Evidence

Session: 2026-07-21
Repo: `$GITHUB_REPOSITORY`
Branch: `feat/gemini-3-5-flash-lite-3-6-flash` (worktree at `~/projects/worktree_gemini_3_6`)
Goal: Add `gemini-3.6-flash` and `gemini-3.5-flash-lite` to the user-facing
"AI Provider & Model" settings dropdown on the v1 frontend (port 8081),
plus every backend registration point, with end-to-end proof that the
new options are present, selectable, and the DOM correctly reflects the
chosen value.

## Why this evidence shape

`your-project.com`'s `AGENTS.md` requires `/es` evidence (real server,
real LLM, real browser/video) for any change under `$PROJECT_ROOT/`. The
shape used here is the new "selectable-option proof" added to
`web-page-screenshots` v1.3.0 — three pre-check layers (served HTML
curl, model-constants endpoint, backend constants module) before the
browser step, plus per-option PNGs and a single .webm of the selection
flow.

## Files changed (the 5+ registration points)

| Path | Change |
|---|---|
| `$PROJECT_ROOT/constants.py` | `ALLOWED_GEMINI_MODELS` +2; `GEMINI_MODEL_MAPPING` +2 entries (with full source citation comments); `MODELS_WITH_CODE_EXECUTION` +2; `MODEL_CONTEXT_WINDOW_TOKENS` +2 (1M each); `MODEL_MAX_OUTPUT_TOKENS` +2 (65K each) |
| `$PROJECT_ROOT/frontend_v1/js/settings.js` | `GEMINI_MODEL_MAPPING` +2 entries (JS-side normalize, mirrors Python) |
| `$PROJECT_ROOT/templates/settings.html` | 2 new `<option value="gemini-3.6-flash">...` and `<option value="gemini-3.5-flash-lite">...` rows in `<select id="geminiModel">` |
| `$PROJECT_ROOT/tests/test_centralized_model_selection.py` | New `TestGemini36And35FlashLiteRegistration` class — 5 tests asserting each new id is wired into allowed/mapping/code-exec/limits/provider |

Net diff (from origin/main `664cf2fa0f`):

```
$PROJECT_ROOT/constants.py                                 |  18 ++++++++++++++++
$PROJECT_ROOT/frontend_v1/js/settings.js                   |   2 +
$PROJECT_ROOT/templates/settings.html                      |   2 +
$PROJECT_ROOT/tests/test_centralized_model_selection.py   |  60 ++++++++++++ (5 tests + import)
```

## Verification

### Layer A — curl `/settings` shows the new options at the template level

```bash
$ curl -fsS "http://127.0.0.1:8081/settings" | grep -E 'option value="(gemini-3\.6-flash|gemini-3\.5-flash-lite)"'
                        <option value="gemini-3.6-flash">Gemini 3.6 Flash (better coding + token efficiency)</option>
                        <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash Lite (fastest, most cost-effective)</option>
```

Confirms the backend→template→HTML pipe is intact. If this fails, the
JS hydration is irrelevant — the option was never rendered at all.

### Layer B — `/api/constants/models` exposes DEFAULT_GEMINI_MODEL

```bash
$ curl -fsS "http://127.0.0.1:8081/api/constants/models" | jq .
{
  "SPICY_MODEL": "x-ai/grok-4.3",
  "DEFAULT_GEMINI_MODEL": "gemini-3-flash-preview",
  "DEFAULT_OPENROUTER_MODEL": "meta-llama/llama-3.1-70b-instruct",
  "DEFAULT_CEREBRAS_MODEL": "qwen-3-235b-a22b-instruct-2507"
}
```

The endpoint doesn't need to enumerate allowed models (those come from
the HTML template), it just exposes the default. Confirms the route is
live and JSON-shape contract preserved.

### Layer C — backend constants module exposes both new ids end-to-end

```bash
$ ./vpython -c "
from mvp_site import constants
for m in ['gemini-3.6-flash','gemini-3.5-flash-lite']:
    print(m, 'allowed=', m in constants.ALLOWED_GEMINI_MODELS,
          'mapping=', constants.GEMINI_MODEL_MAPPING.get(m),
          'code_exec=', m in constants.MODELS_WITH_CODE_EXECUTION,
          'ctx=', constants.MODEL_CONTEXT_WINDOW_TOKENS.get(m),
          'max_out=', constants.MODEL_MAX_OUTPUT_TOKENS.get(m))"
gemini-3.6-flash allowed= True mapping= gemini-3.6-flash code_exec= True ctx= 1000000 max_out= 65536
gemini-3.5-flash-lite allowed= True mapping= gemini-3.5-flash-lite code_exec= True ctx= 1000000 max_out= 65536
```

All five registration points wired. If any printed `False` or `None`,
the diff was incomplete.

### Layer D — pytest regression guard

```
$ ./vpython -m pytest $PROJECT_ROOT/tests/test_centralized_model_selection.py \
             $PROJECT_ROOT/tests/test_settings_validation.py -q
91 passed, 4 warnings in 0.93s
```

The 5 new tests in `TestGemini36And35FlashLiteRegistration` pass:
- `test_new_models_allowed_in_dropdown` — `assertIn` against `ALLOWED_GEMINI_MODELS`
- `test_new_models_passthrough_in_mapping` — `assertEqual` against `GEMINI_MODEL_MAPPING[k] == k`
- `test_new_models_support_code_execution_plus_json` — `assertIn` against `MODELS_WITH_CODE_EXECUTION`
- `test_new_models_have_context_and_output_limits` — 1_000_000 / 65_536
- `test_new_models_route_to_gemini_provider` — `infer_provider_from_model(...)` returns `LLM_PROVIDER_GEMINI`

Full suite went 86 → 91 passing (5 new added, 0 regressions).

### Layer E — headless browser selectable-option proof

Script `/tmp/gemini_3_6_evidence/capture_settings_video.py` (canonical
recipe in `SKILL.md` "Selectable-option proof" section). Output:

```
[settings] dropdown options: [
  'Gemini 3 Flash (default - best value)',
  'Gemini 3.5 Flash (newer/stronger)',
  'Gemini 3.6 Flash (better coding + token efficiency)',     ← NEW
  'Gemini 3.1 Flash Lite (lighter, faster)',
  'Gemini 3.5 Flash Lite (fastest, most cost-effective)',   ← NEW
  'Gemini 2.0 Flash (legacy)'
]
[settings] dropdown values: [
  'gemini-3-flash-preview', 'gemini-3.5-flash', 'gemini-3.6-flash',
  'gemini-3.1-flash-lite-preview', 'gemini-3.5-flash-lite', 'gemini-2.0-flash'
]
[select] geminiModel.value='gemini-3.6-flash'         text='Gemini 3.6 Flash (better coding + token efficiency)'
[select] geminiModel.value='gemini-3.5-flash-lite'   text='Gemini 3.5 Flash Lite (fastest, most cost-effective)'
[video] saved: /tmp/gemini_3_6_evidence/settings_gemini_3_6_and_3_5_flash_lite.webm (414429 bytes)
✅ ALL DROPDOWN CHECKS PASSED
```

Three assertions pass that pure BEFORE/AFTER would miss:
1. **6 options present** in JS-hydrated `<select>` (was 4).
2. **Each new option selectable** via `page.select_option(...)` without
   throwing.
3. **`el.value === "<new-value>"` AND `el.options[el.selectedIndex].textContent.trim()`
   matches the human-readable label** — not just that the select fired.

Captured artifacts (all in `/tmp/gemini_3_6_evidence/`):

| File | Bytes | Description |
|---|---|---|
| `settings_with_3_6_flash_selected.png`         | 259096 | Full-page settings after selecting `gemini-3.6-flash` |
| `settings_with_3_5_flash_lite_selected.png`   | 259025 | Full-page settings after selecting `gemini-3.5-flash-lite` |
| `settings_dropdown_closeup.png`               | 150170 | Dropdown scrolled into center for closing shot |
| `settings_gemini_3_6_and_3_5_flash_lite.webm` | 414429 | Playwright record_video: open page → select each new option → closeup |

## What the local server was

`./local.sh --force-default-port --no-log-stream` from the worktree —
Flask on `:8081`, MCP on `:8001`. The MCP server stayed un-healthy on
this session (port 8001 already held by a non-MCP process), but the
settings flow doesn't touch MCP — Flask served `/settings` and
`/api/constants/models` cleanly on `:8081`.

## What this PR is NOT (anti-scope)

- Did not change `DEFAULT_GEMINI_MODEL` — stays `gemini-3-flash-preview`.
  Per the Gemini blog post, 3.6 Flash is described as Google's new
  "workhorse" but is priced the same tier as 3.5 Flash. Default-stability
  for live campaigns is more important than chasing the newest default
  until the 3.6 series has been on the API for ≥2 weeks and a separate
  PR moves the default.
- Did not remove or replace any existing model. All 4 prior options
  (`gemini-3-flash-preview`, `gemini-3.5-flash`, `gemini-3.1-flash-lite-preview`,
  `gemini-2.0-flash`) remain in the dropdown.
- Did not introduce Gemini 3.5 Flash Cyber (the third model in the
  July 2026 release wave — `gemini-3.5-cyber-flash`) — that's a
  specialist cyber model and belongs in a separate PR if at all.
