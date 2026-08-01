---
title: Non-UI /es evidence — harness + JSON transcripts + HTML render + headless PNG + gist + Slack upload
date: 2026-07-12
verified-on: $GITHUB_REPOSITORY PR #8337 (fix/state-update-warnings)
---

## When to use

The `ui-change-requires-before-after-visual-proof` skill covers **UI deltas** — a button moves, a color changes, a modal appears. That recipe assumes you can open the app in a real browser and screenshot two states.

This recipe is the equivalent for **data-shape deltas** — server-side filtering, log surface changes, JSON shape changes, anything where the bug is "the wrong entries are present in the wrong field." The proof is the JSON shape itself, not pixels. Verified on PR #8337 (hide state-update schema-gate warnings): the screenshot's evidence is a list of strings inside `_server_system_warnings`, not a DOM delta.

## The 8-step recipe

### Step 1 — write the harness

Build a Python script that constructs real server objects with the exact payload shapes from the screenshot / user complaint. Use the actual class the production server constructs, not a re-implementation.

```python
# harness_before_after.py
from mvp_site.narrative_response_schema import NarrativeResponse
from mvp_site.schemas.validation import (
    CORRECTION_KIND_BENIGN_NORMALIZE,
    sanitize_state_updates_overlay,
)

CASES = [
    ("screenshot_shape_3_unknown_custom_campaign_state_keys",
     {"custom_campaign_state": {"divin": True, "crus": True, "reso": True}}),
    # ... 4 more shapes covering the full family
]

results = []
for name, payload in CASES:
    resp = NarrativeResponse(narrative="ok", state_updates=payload)
    results.append({
        "name": name,
        "warnings": resp.debug_info.get("_server_system_warnings", []) or [],
        "gate_errors": resp.debug_info.get("_state_update_schema_gate_errors", []) or [],
        "kinds": resp.debug_info.get("_state_update_schema_gate_kinds", []) or [],
    })
```

### Step 2 — precise verifier (do NOT use `warnings_count == 0`)

Assert against the **specific class** you're hiding, not the whole warnings list. Other unrelated warnings may exist (e.g. `Missing action_resolution field (required for player actions)` is a separate validation that fires on every NarrativeResponse without that field). Filter with a prefix check:

```python
def schema_gate_warnings(warnings):
    return [w for w in warnings if w.startswith("State update schema gate:")]

all_pass = all(
    len(schema_gate_warnings(r["warnings"])) == 0 for r in results
)
```

Coarse `warnings_count == 0` was the False-PASS bug on PR #8337 — the unrelated `Missing action_resolution field` warning added 1 to the count, masking the real PASS.

### Step 3 — run BEFORE (on `origin/main`)

Create a side-worktree pinned to `origin/main` to capture the buggy state without disturbing the fix worktree:

```bash
git worktree add -B fix-state-update-warnings-before ~/.worktrees/<topic>-before origin/main
```

Run the harness there, capture the JSON transcript.

### Step 4 — run AFTER (on the branch)

Run the harness in the fix worktree, capture the JSON transcript.

### Step 5 — render the JSON as styled HTML

Build a single page with side-by-side BEFORE / AFTER panels. Use a clean table with columns:
- Case name (monospace)
- Number (e.g. warnings-count or schema-gate-count)
- Kind tags as colored badges (`BENIGN_NORMALIZE` green / `SCHEMA_WARNING` red)
- Verdict (`PASS` / `FAIL`)

Tip: use `display: grid` with `grid-template-columns: 1fr 1fr` for the side-by-side layout. Colored section headers (red BEFORE, green AFTER) help visual scanning.

### Step 6 — capture screenshots with headless Chromium

Use Playwright sync API at `device_scale_factor=2` for retina-quality PNGs:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1280, "height": 1024},
        device_scale_factor=2,
    )
    page = context.new_page()
    page.goto(f"file://{html_path}", wait_until="networkidle")
    page.wait_for_load_state("domcontentloaded")
    page.screenshot(path=png_path, full_page=True)
    browser.close()
```

Capture THREE screenshots for full coverage:
- `before-only.png` — the BEFORE panel alone
- `after-only.png` — the AFTER panel alone
- `before-after-comparison.png` — both panels side-by-side

### Step 7 — upload PNGs to a public GitHub gist

**`gh gist create <binary>` rejects binaries.** The workaround (verified PR #8337 gist `d3b849f066247fb6e2dbda895402f804`):

1. Create an empty public gist with a placeholder text file via REST `POST https://api.github.com/gists` with `Bearer $(gh auth token)`:
   ```python
   payload = {"description": "PR #8337 evidence", "public": True, "files": {"README.md": {"content": "..."}}}
   req = urllib.request.Request("https://api.github.com/gists",
       data=json.dumps(payload).encode(),
       headers={"Authorization": f"Bearer {gh_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"},
       method="POST")
   gist_id = json.loads(urllib.request.urlopen(req, timeout=30).read())["id"]
   ```
2. Clone it as a writable git repo: `gh gist clone <gist_id> /tmp/gist-repo` (the `--force` flag does NOT exist; clone overwrites if dir exists)
3. `cp /path/to/real/<png>.png /tmp/gist-repo/`
4. Commit + push: `git add . && git commit -m "..." && git push origin HEAD`
5. Get the SHA: `git rev-parse HEAD` (NOT `/HEAD/` — the CDN 404s on `HEAD`)
6. Raw URL format: `https://gist.githubusercontent.com/<user>/<gist_id>/raw/<sha>/`
7. Verify with `curl -sSI <raw_url> | grep -i content-type` — must show `image/png`, NOT `text/plain`

### Step 8 — embed in PR + upload to Slack thread

**PR description:** use markdown image syntax with the gist raw URL:
```
![BEFORE — origin/main](https://gist.githubusercontent.com/<user>/<gist_id>/raw/<sha>/before-only.png)
```

`gh pr edit <N> --body-file /tmp/pr-body.md` rewrites the PR description in one call. (For new PRs, write the body to a file first because shell-quoting parens or special characters in titles is the single most common 422 cause — see `references/rate-limit-rest-pr-create-fallback-2026-07-12.md`.)

**Slack thread:** load `evidence-attach-to-slack` skill and use the 3-stage `files.completeUploadExternal` API. Verified recipe on PR #8337:

```python
import urllib.request, urllib.parse, json

bot_token = subprocess.run(["bash", "-c",
    "source ~/.bashrc 2>/dev/null; echo -n \"$HERMES_SLACK_BOT_TOKEN\""],
    capture_output=True, text=True).stdout.strip()

for fname in files:
    file_size = os.path.getsize(full_path)
    # Stage 1: form-encoded (NOT JSON!)
    stage1_data = urllib.parse.urlencode({"filename": fname, "length": str(file_size)}).encode()
    r1 = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.getUploadURLExternal",
        data=stage1_data,
        headers={"Authorization": f"Bearer {bot_token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST"), timeout=30).read())
    # Stage 2: raw binary to upload_url
    with open(full_path, "rb") as f:
        urllib.request.urlopen(urllib.request.Request(r1["upload_url"],
            data=f.read(), headers={"Content-Type": "image/png"}, method="POST"),
            timeout=60)
    # Stage 3: completeUploadExternal — files array only contains {id, title}, NO extra keys
    stage3_data = urllib.parse.urlencode({
        "channel_id": channel_id,
        "thread_ts": thread_ts,
        "files": json.dumps([{"id": r1["file_id"], "title": f"PR #8337 — {fname}"}]),
    }).encode()
    urllib.request.urlopen(urllib.request.Request(
        "https://slack.com/api/files.completeUploadExternal",
        data=stage3_data,
        headers={"Authorization": f"Bearer {bot_token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST"), timeout=30)
```

**Gotchas** (verified 2026-07-12, all of these bite):
- Stage 1 wants `application/x-www-form-urlencoded`, NOT JSON. JSON silently drops the fields and returns `invalid_arguments: missing required field: length, filename`.
- Stage 3's `files[i]` object cannot include `initial_comment` (that's a top-level parameter, not a per-file property). Putting it inside returns `invalid additional property: initial_comment`.
- Stage 3 accepts JSON OR form-encoded, but the JSON parser is strict about per-file extra properties while the form-encoded parser is permissive. Default to form-encoded.

## Cost + verification

| Step | Cost | Verification |
|---|---|---|
| 1. Harness | 5-10 min | `python3 harness_before_after.py` exits 0 |
| 2. Verifier | 0 | Coarse `== 0` fails on unrelated warnings; class-prefix filter passes |
| 3-4. Run BEFORE+AFTER | 2 min | JSON transcripts saved to disk |
| 5. HTML | 5 min | `file://<html>` renders correctly in any browser |
| 6. Screenshots | 30s | `ls -la *.png` shows 3 PNGs with realistic sizes (100-500 KB) |
| 7. Gist upload | 2 min | `curl -sSI <raw_url> | grep content-type` shows `image/png` |
| 8. PR embed + Slack | 3 min | PR page renders images inline; thread has 3 bot messages with `FileCount: 1` each |

Total: ~20 minutes for a complete non-UI `/es` evidence bundle that survives both PR review and Slack-thread visibility.

## Why this is better than the alternatives

- **Plain text logs in fenced code blocks** — works for terminal-style output but the user explicitly asked for "before/after and screenshots" on PR #8337. Text alone doesn't satisfy that.
- **Single PNG with a wall of JSON text inside** — dense and unreadable. The split PNGs (BEFORE / AFTER / side-by-side) are scannable in 5 seconds.
- **Embedded PNGs in the PR branch** — bloats the PR diff (Jeffrey's 2026-07-08 preference: "evidence should be in gist urls not attached to the PR files"). The gist path keeps PR diffs reviewable.
- **Skipping the Slack upload** — leaves the user unable to see the proof in their inbox. The Slack thread is the user's actual view of the work; the PR is for reviewers.
