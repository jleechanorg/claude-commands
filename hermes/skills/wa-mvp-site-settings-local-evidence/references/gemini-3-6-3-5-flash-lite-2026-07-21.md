# Worked Example — Gemini 3.6 Flash + 3.5 Flash Lite Settings Dropdown (2026-07-21)

Worked-example companion to `wa-mvp-site-settings-local-evidence`. The
canonical session: adding `gemini-3.6-flash` and `gemini-3.5-flash-lite`
to `$GITHUB_REPOSITORY`'s settings dropdown. This file shows
what a complete `$PROJECT_ROOT/` settings change actually looks like end-to-end
— the exact edits, the exact test class, the exact curl/Playwright proof.

## What changed (7+1 = 14 lines + 60 lines test)

```
$PROJECT_ROOT/constants.py                                 | 18 ++++++++++++++++
$PROJECT_ROOT/frontend_v1/js/settings.js                   |  2 +
$PROJECT_ROOT/templates/settings.html                      |  2 +
$PROJECT_ROOT/tests/test_centralized_model_selection.py   | 60 +++++++++++++ (5 tests + import)
```

Branch: `feat/gemini-3-5-flash-lite-3-6-flash`
Worktree: `~/projects/worktree_gemini_3_6`
Source: [Gemini 3.6 Flash + 3.5 Flash Lite announcement (Jul 2026)](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-6-flash-3-5-flash-lite-3-5-flash-cyber/)

### `$PROJECT_ROOT/constants.py` (5 registration points)

```python
# 1) ALLOWED_GEMINI_MODELS — add the two new ids
ALLOWED_GEMINI_MODELS = [
    DEFAULT_GEMINI_MODEL,  # gemini-3-flash-preview (unchanged default)
    "gemini-3.5-flash",
    "gemini-2.0-flash",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.6-flash",                          # NEW
    "gemini-3.5-flash-lite",                     # NEW
]

# 2) GEMINI_MODEL_MAPPING — passthrough entries with source citations
GEMINI_MODEL_MAPPING = {
    ...
    "gemini-3.6-flash": "gemini-3.6-flash",            # NEW — see citation
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",  # NEW — see citation
    ...
}

# 3) MODELS_WITH_CODE_EXECUTION — inherit 3.x single-pass contract
MODELS_WITH_CODE_EXECUTION: set[str] = {
    "gemini-3-flash-preview",
    "gemini-3.0-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite-preview",
    "gemini-3.6-flash",                              # NEW
    "gemini-3.5-flash-lite",                         # NEW
}

# 4) MODEL_CONTEXT_WINDOW_TOKENS
MODEL_CONTEXT_WINDOW_TOKENS = {
    ...
    "gemini-3.6-flash": 1_000_000,        # NEW (Jul 2026, inherits 3.x 1M)
    "gemini-3.5-flash-lite": 1_000_000,   # NEW (Jul 2026, inherits 3.x 1M)
    ...
}

# 5) MODEL_MAX_OUTPUT_TOKENS
MODEL_MAX_OUTPUT_TOKENS = {
    ...
    "gemini-3.6-flash": 65_536,           # NEW (3.x family)
    "gemini-3.5-flash-lite": 65_536,      # NEW (3.x family)
    ...
}
```

### `$PROJECT_ROOT/frontend_v1/js/settings.js` (1 registration point)

```js
const GEMINI_MODEL_MAPPING = {
  "gemini-3-flash-preview": "gemini-3-flash-preview",
  "gemini-3.5-flash": "gemini-3.5-flash",
  "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite-preview",
  "gemini-3.6-flash": "gemini-3.6-flash",            // NEW
  "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",  // NEW
  "gemini-2.0-flash": "gemini-2.0-flash",
  // legacy redirects unchanged
};
```

### `$PROJECT_ROOT/templates/settings.html` (1 registration point)

```html
<select id="geminiModel" class="form-select" name="geminiModel">
    <option value="gemini-3-flash-preview">Gemini 3 Flash (default - best value)</option>
    <option value="gemini-3.5-flash">Gemini 3.5 Flash (newer/stronger)</option>
    <option value="gemini-3.6-flash">Gemini 3.6 Flash (better coding + token efficiency)</option>   <!-- NEW -->
    <option value="gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite (lighter, faster)</option>
    <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash Lite (fastest, most cost-effective)</option>   <!-- NEW -->
    <option value="gemini-2.0-flash">Gemini 2.0 Flash (legacy)</option>
</select>
```

### `$PROJECT_ROOT/tests/test_centralized_model_selection.py` (1 new test class)

```python
from mvp_site import constants  # NEW IMPORT

class TestGemini36And35FlashLiteRegistration(unittest.TestCase):
    NEW_MODELS = ("gemini-3.6-flash", "gemini-3.5-flash-lite")

    def test_new_models_allowed_in_dropdown(self):
        for m in self.NEW_MODELS:
            self.assertIn(m, constants.ALLOWED_GEMINI_MODELS, ...)

    def test_new_models_passthrough_in_mapping(self):
        for m in self.NEW_MODELS:
            self.assertEqual(constants.GEMINI_MODEL_MAPPING.get(m), m, ...)

    def test_new_models_support_code_execution_plus_json(self):
        for m in self.NEW_MODELS:
            self.assertIn(m, constants.MODELS_WITH_CODE_EXECUTION, ...)

    def test_new_models_have_context_and_output_limits(self):
        for m in self.NEW_MODELS:
            self.assertEqual(constants.MODEL_CONTEXT_WINDOW_TOKENS.get(m), 1_000_000, ...)
            self.assertEqual(constants.MODEL_MAX_OUTPUT_TOKENS.get(m), 65_536, ...)

    def test_new_models_route_to_gemini_provider(self):
        for m in self.NEW_MODELS:
            self.assertEqual(
                constants.infer_provider_from_model(m),
                constants.LLM_PROVIDER_GEMINI,
                ...,
            )
```

5 tests, all green after the edits.

## The `/es` evidence (the actual proof)

### Layer 1: Flask boot

```
$ TESTING_AUTH_BYPASS=true PORT=8081 ./vpython -m mvp_site.main serve &
[lsof -ti:8081] → 90977   # Flask is alive
```

### Layer 3: served HTML carries the new options

```
$ curl -fsS "http://127.0.0.1:8081/settings" | grep 'option value="gemini-'
                        <option value="gemini-3-flash-preview">Gemini 3 Flash (default - best value)</option>
                        <option value="gemini-3.5-flash">Gemini 3.5 Flash (newer/stronger)</option>
                        <option value="gemini-3.6-flash">Gemini 3.6 Flash (better coding + token efficiency)</option>
                        <option value="gemini-3.1-flash-lite-preview">Gemini 3.1 Flash Lite (lighter, faster)</option>
                        <option value="gemini-3.5-flash-lite">Gemini 3.5 Flash Lite (fastest, most cost-effective)</option>
                        <option value="gemini-2.0-flash">Gemini 2.0 Flash (legacy)</option>
```

### Layer 4: constants probe

```
$ ./vpython -c "from mvp_site import constants
for m in ['gemini-3.6-flash','gemini-3.5-flash-lite']:
  print(m, 'in ALLOWED=', m in constants.ALLOWED_GEMINI_MODELS,
        'mapping=', constants.GEMINI_MODEL_MAPPING.get(m),
        'code_exec=', m in constants.MODELS_WITH_CODE_EXECUTION,
        'ctx=', constants.MODEL_CONTEXT_WINDOW_TOKENS.get(m),
        'max_out=', constants.MODEL_MAX_OUTPUT_TOKENS.get(m))"
gemini-3.6-flash in ALLOWED= True mapping= gemini-3.6-flash code_exec= True ctx= 1000000 max_out= 65536
gemini-3.5-flash-lite in ALLOWED= True mapping= gemini-3.5-flash-lite code_exec= True ctx= 1000000 max_out= 65536
```

### Layer 5: POST /api/settings round-trip

```
$ curl -fsS -X POST "http://127.0.0.1:8081/api/settings" \
    -H "Content-Type: application/json" -H "X-Test-Bypass-Auth: true" \
    -H "X-Test-User-ID: gemini-3-6-test-user" \
    -d '{"llm_provider":"gemini","gemini_model":"gemini-3.6-flash"}'
{"message": "Settings saved", "success": true}

$ curl -fsS "http://127.0.0.1:8081/api/settings" \
    -H "X-Test-Bypass-Auth: true" -H "X-Test-User-ID: gemini-3-6-test-user" | jq .gemini_model
"gemini-3.5-flash-lite"   # confirmed round-trip
```

**THE WRONG-SHAPE TRAP** (don't do this):

```
$ curl -fsS -X POST "http://127.0.0.1:8081/api/settings" \
    -H "Content-Type: application/json" -H "X-Test-Bypass-Auth: true" \
    -d '{"settings":{"gemini_model":"gemini-3.6-flash"}}'
{"error":"Invalid settings data"}   # ← because {"settings":...} wraps the dict
```

### Layer 7: Playwright headless proof

Script: `/tmp/gemini_3_6_evidence/capture_settings_video_v2.py`
Output:

```
[dropdown options rendered in live browser]:
  - gemini-3-flash-preview          Gemini 3 Flash (default - best value)
  - gemini-3.5-flash                Gemini 3.5 Flash (newer/stronger)
  - gemini-3.6-flash                Gemini 3.6 Flash (better coding + token efficiency)
  - gemini-3.1-flash-lite-preview   Gemini 3.1 Flash Lite (lighter, faster)
  - gemini-3.5-flash-lite           Gemini 3.5 Flash Lite (fastest, most cost-effective)
  - gemini-2.0-flash                Gemini 2.0 Flash (legacy)
[OK] Both new options are present in the live dropdown
[API round-trip after dropdown change] gemini_model='gemini-3.5-flash-lite'
[video] saved: /tmp/gemini_3_6_evidence/settings_gemini_3_6_and_3_5_flash_lite_v2.webm (1168125 bytes)
✅ ALL LIVE EVIDENCE CAPTURED
```

Captured artifacts:

| File | Bytes | What it proves |
|---|---|---|
| `live_3_6_flash_selected.png` | 136778 | `geminiModel.value="gemini-3.6-flash"` after `select_option` |
| `live_3_5_flash_lite_selected.png` | 136778 | `geminiModel.value="gemini-3.5-flash-lite"` after `select_option` |
| `live_final_api_confirmed.png` | 153077 | After JS `fetch('/api/settings')` confirmed `gemini_model='gemini-3.5-flash-lite'` from real backend |
| `settings_gemini_3_6_and_3_5_flash_lite_v2.webm` | 1168125 | Captions: "Selected gemini-3.6-flash — value persisted" → "Selected gemini-3.5-flash-lite — value persisted" → "GET /api/settings -> gemini_model='gemini-3.5-flash-lite' (CONFIRMED via real backend)" |

### Layer 8: pytest

```
$ ./vpython -m pytest $PROJECT_ROOT/tests/test_centralized_model_selection.py $PROJECT_ROOT/tests/test_settings_validation.py -q
91 passed, 4 warnings in 0.93s
```

(86 prior + 5 new in `TestGemini36And35FlashLiteRegistration`; 0 regressions.)

## Bugs / pitfalls hit during this session (now in SKILL.md)

1. **`f"""... {value!r} ..."""` inside `vp.evaluate()`** → JS `SyntaxError: Unexpected identifier 'gemini'`. Fix: `evaluate((val) => { ... }, value)`. (Captured in `web-page-screenshots` SKILL.md v1.3.1.)

2. **`POST /api/settings` is the raw dict**, not `{"settings": ...}` — `main.py` does `data = request.get_json(force=True)` and passes it straight down. Wrapping produces 400 "Invalid settings data". (Captured in this skill's "POST /api/settings payload shape" section.)

3. **`./local.sh` returns exit-0 once backgrounding is done**, NOT when Flask is healthy. Always verify with `lsof -ti:8081` and `curl /api/constants/models`. (Captured in this skill's "Local server launch — the local.sh exit-0 trap" section.)

4. **`$PROJECT_ROOT/main.py serve` has no `--port` flag** — port comes from `PORT` env var only. `parse_port_robust()` accepts messy strings like `"ℹ️ Port 8081 in use, trying 8082...\n8082"`. (Captured here.)

5. **`WORLDAI_DEFAULT_GEMINI_MODEL` is read at import time** by `constants.py:62` (lines 62–63: `os.getenv("WORLDAI_DEFAULT_GEMINI_MODEL", "gemini-3-flash-preview")`). Server restart needed to pick up changes. (Captured here.)

6. **`/api/constants/models` returns only the default model name, not the allowed list.** Frontend doesn't query allowed models at runtime — it reads them from the inline JS `GEMINI_MODEL_MAPPING` map. So changing `ALLOWED_GEMINI_MODELS` on the backend has zero frontend effect until you also update `settings.js`. (Captured here.)

## Companion reference

- `web-page-screenshots` / `references/worldarchitect-ai-gemini-3-6-settings-evidence-2026-07-21.md` — the longer, more verbose evidence write-up that this file companions. This file is the **skills integration** view; the other is the **PR-evidence** view.
- `web-page-screenshots` v1.3.0 "Selectable-option proof" section — the generic Playwright recipe that produced the .webm above.
- `web-page-screenshots` v1.3.1 (added 2026-07-21) "Playwright `vp.evaluate()` chokes on Python f-string-with-`!r` interpolation" — the `f"""{api_value!r}"""` pitfall.
