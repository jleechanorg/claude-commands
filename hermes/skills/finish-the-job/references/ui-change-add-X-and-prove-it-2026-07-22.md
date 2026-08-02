# UI change with "add X to settings and prove it works" — visual evidence is the deliverable

**Verified 2026-07-22, $GITHUB_REPOSITORY `add-gemini-flash-models-to-settings` (Slack thread `C0AH3RY3DK6/p1784653940`).**

## The failure mode

User message contained all three triggers:

1. *"Add Gemini 3.5 flash lite and 3.6 flash to settings"* — UI-layer change.
2. *"iterate and test it to confirm it works"* — verification step required.
3. *"make sure you change all the right places and run local.sh and use /browser or testing_ui test to get captioned video proof the setting works"* — visual evidence required.

Agent completed the code changes but did **not** attach the captioned screenshots/video before claiming the change was done. Jeffrey's verbatim reply:

> *"Is this finally wokring? show me captioned screeshots/video here. why didnt you alreayd?"*

Two distinct anti-patterns fired in one session:

1. **Audit-without-proof** — agent did `rg` and verified the new entries existed in `$PROJECT_ROOT/constants.py` and `$PROJECT_ROOT/templates/settings.html`, then said *"End state: blocked/in progress — not proven working. No PR URL or visual evidence exists yet."* The right move at this point was to **continue** to evidence, not stop.
2. **Local-path citation** — early reply referenced `MEDIA:$HOME/.../foo.png` style evidence paths. `mcp__slack__conversations_add_message` does NOT render those as attachments; the path is sent as literal text and no file is attached. See `evidence-attach-to-slack` + `evidence-attach-presend-gate`.

## The 6-gate contract (run all before posting "done")

### Gate 1 — Audit every layer

The right places to edit for a settings/model/option addition in `$GITHUB_REPOSITORY`:

```bash
rg -n '<canonical-key>|<model-name>|<setting-key>' -g '*.{py,js,ts,tsx,html,json}' \
  $PROJECT_ROOT/constants.py \
  $PROJECT_ROOT/templates/settings.html \
  $PROJECT_ROOT/frontend_v1/js/settings.js \
  $PROJECT_ROOT/frontend_v1/app.js \
  $PROJECT_ROOT/llm_providers/*.py \
  $PROJECT_ROOT/tests/test_*.py
```

Concrete locations to verify for a Gemini model add:

| Layer | File | What to add |
|---|---|---|
| Backend model registry | `$PROJECT_ROOT/constants.py` | `GEMINI_3_5_FLASH = "gemini-3.5-flash"`, `GEMINI_3_6_FLASH = "gemini-3.6-flash"`; add to `VALID_GEMINI_MODELS`, `GEMINI_INPUT_TOKEN_LIMITS`, `GEMINI_OUTPUT_TOKEN_LIMITS`, `DEFAULT_GEMINI_MODEL` candidates |
| Backend default alias | `$PROJECT_ROOT/constants.py` | If a new default, update `DEFAULT_GEMINI_MODEL`; if an alias, add to `GEMINI_MODEL_ALIASES` |
| Settings template | `$PROJECT_ROOT/templates/settings.html` | `<option value="gemini-3.5-flash-lite">Gemini 3.5 Flash Lite (faster, lower cost)</option>` etc. |
| Frontend settings map | `$PROJECT_ROOT/frontend_v1/js/settings.js` | Add `"gemini-3.5-flash-lite": "gemini-3.5-flash-lite"` to `GEMINI_MODEL_ALIASES` and to `DEFAULT_GEMINI_MODEL` candidates |
| Backend allowlist | `$PROJECT_ROOT/llm_providers/*.py` | Verify the provider's `__init__` accepts the new model name (no hardcoded blocklist) |
| Tests | `$PROJECT_ROOT/tests/test_centralized_model_selection.py`, `$PROJECT_ROOT/tests/test_byok_coverage.py`, etc. | Add the new model to expected-known sets |
| Frontend runtime | `$PROJECT_ROOT/frontend_v1/app.js` (around line 4425/4651) | `APP_MODELS.DEFAULT_GEMINI_MODEL` mirror |
| Cypress / UI tests | `$PROJECT_ROOT/frontend_v1/tests/settings_listeners.test.js` | Add to `elements.geminiModel.value = 'gemini-3.5-flash-lite'` test cases |

**Single-commit rule:** fix ALL occurrences in one commit (per `grep-before-constant-change`). Skip a layer → the setting silently fails or is hidden.

### Gate 2 — Run the app

```bash
bash local.sh   # or: bash scripts/run_smoke_local.sh
```

Verify no boot errors. If `local.sh` requires backend services (Firestore emulator, etc.), boot them first or use the headless boot variant.

### Gate 3 — Capture BEFORE/AFTER PNGs

Use `browser_navigate` + `browser_snapshot` (or headless Chromium / Playwright if you need pixels):

```python
# BEFORE: settings page without new options
browser_navigate(url=settings_url)
browser_snapshot()  → /tmp/before_settings.png

# AFTER: edit local, reload, verify options present, selected, persisted
browser_navigate(url=settings_url)
browser_snapshot()  → /tmp/after_settings.png
```

For the AFTER PNG, do the full click-through: open settings → click Gemini model dropdown → select new option → click Save → reload page → verify the dropdown still shows the new option (proves persistence).

### Gate 4 — Capture captioned MP4

Use `mp4-caption-burn` skill OR a Playwright `record_video` + ffmpeg caption burn:

```bash
# Generate PNG sequence from the click-through
for i in 1..N; do capture_settings_$i.png; done

# Caption + combine into MP4
ffmpeg -framerate 2 -i capture_settings_%d.png \
  -vf "drawtext=text='Step %{n}: open settings and select Gemini 3.5 Flash Lite':fontcolor=white:fontsize=24:x=20:y=H-th-20" \
  -c:v libx264 -pix_fmt yuv420p /tmp/settings_proof.mp4
```

OR use `web-page-screenshots` skill (for OG thumbnails / before-after pairs).

### Gate 5 — Upload via 3-stage Slack API (NOT `MEDIA:/path`)

Bare `MEDIA:$HOME/.../foo.png` tokens render as literal text through `mcp__slack__conversations_add_message` — Slack shows the path string, no attachment. Use the 3-stage `files.completeUploadExternal` API:

1. `POST files.getUploadURLExternal` with `filename` + `length` → returns `upload_url` + `file_id`.
2. `POST <upload_url>` with the file body (binary).
3. `POST files.completeUploadExternal` with `files=[{file_id, title}]` + `channel_id` + `thread_ts` + `initial_comment`.

Token: `HERMES_SLACK_BOT_TOKEN`. See `evidence-attach-to-slack` + `evidence-attach-presend-gate` for the full recipe.

### Gate 6 — Vision-verify the captions and UI

After upload, use `vision_analyze` on each captured PNG and the MP4 still:

```text
vision_analyze(image_url=/tmp/after_settings.png, question="Does this settings page show a 'Gemini 3.5 Flash Lite' option selected?")
```

If the vision model returns *"No, only the legacy options are visible"* → the PNG does NOT prove the change → re-run Gate 3. Vision-verify is a HARD GATE; do not skip.

## Forbidden reply shapes

| Shape | Why forbidden |
|---|---|
| *"Settings now include X"* | No proof attached — Jeffrey will reply "why didn't you already" |
| *"Evidence saved to `/tmp/foo.png`"* | Path is not viewable to the user in Slack |
| *"Running local.sh now"* | No follow-up; agent goes silent |
| *"The change is on branch `<branch>` ready for review"* | When no visual proof has been produced yet |
| *"I added X to `constants.py` and `settings.html`"* | Doesn't say anything about UI rendering or persistence |

## What to say when you cannot complete the chain in one session

Be explicit about what's missing:

```text
End state: blocked/in progress — not proven working.

Audit: ✅ all 8 layers touched (constants.py, settings.html, settings.js, app.js,
       providers, tests, frontend tests, byok).
Code: ✅ committed on branch fix/gemini-35-lite-36-flash-settings (sha XXX).
Run: ✅ local.sh booted clean.
Evidence: ❌ no BEFORE/AFTER PNGs and no captioned MP4 attached yet.
PR: ❌ no PR created yet (blocked on evidence gate for prompt-only PRs).

To finish: dispatch `ao spawn` worker to capture UI screenshots + MP4,
upload via 3-stage `files.completeUploadExternal`, vision-verify, then PR.
```

## Companion skills

- `grep-before-constant-change` — every layer touched, same commit (SOUL.md `## COMMIT:`).
- `evidence-attach-to-slack` — 3-stage upload recipe.
- `evidence-attach-presend-gate` — 5-step pre-send sequence.
- `ui-change-requires-before-after-visual-proof` — already enforced in SOUL.md `## COMMIT:` for public URLs.
- `web-page-screenshots` — Playwright/Chromium capture recipe.
- `mp4-caption-burn` — ffmpeg caption burn recipe.
- `mp4-caption-burn`, `evidence-attach-to-slack` are themselves canonical; this reference is the class-level *"add X to settings"* workflow that ties them together.