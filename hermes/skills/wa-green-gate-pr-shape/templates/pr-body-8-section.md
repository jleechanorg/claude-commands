# Your Project PR Body — 8-Section Gate-6b Scaffold + Gate-0 Tenets anchor

Copy-paste this into the PR body for any your-project.com PR that touches
`$PROJECT_ROOT/**`, `testing_mcp/**`, `testing_ui/**`, or `deploy.sh`. Run the
local validator before pushing.

The 8 sections are checked by `python3 .github/scripts/pr_description_gate.py`
in the your-project.com repo. ALL 8 headers must appear in this exact order
with `## ` (two-hash, line-start) prefix. The 4 evidence sections
(`## Unit Test Evidence`, `## Non-Unit Test Evidence`, `## Real LLM Evidence`,
`## Evidence`) must each contain a `https?://` URL or a fenced code block.

For production-code PRs that touch `$PROJECT_ROOT/**/*.py` AND need Gate-0
(Design Doc Grep) to pass, also include `## Tenets (or ## Design Decision)`
with a linked `world_reference/<file>.md` artifact + bead ID. Verified
PR #8485 (2026-07-20, disable sovereign/multiverse tier).

Filling the template blanks below produces a body that passes GATE-0 + GATE-6b
on the first push.

```markdown
## Summary
- <one-line scope statement>
- <2-4 bullets listing concrete changes>

## Production Code Changes
- `path/to/file.py` (<+N>/<-M>): <description of real diff content>

## Test Changes
- `path/to/test_X.py`: <new/updated tests>
  (or "no test changes — `<scope reason>`" if the change is documentation/
   config-only or, for prompts, see `## Real LLM Evidence`)

## Known Limitations
- <honest scope statement>
- (or "none beyond what the summary states")

## Unit Test Evidence
\`\`\`bash
./run_tests.sh --full
# output: <paste a few PASS lines + summary, or link to gist if output is huge>
\`\`\`

or for large outputs, link the gist:
<https://gist.github.com/<user>/<id>/raw/<sha>/test_output.txt>

## Non-Unit Test Evidence
- For prompt-only / config-only changes, a JSON contract diff:
\`\`\`json
{"state_updates": {"custom_campaign_state": {"<key>": "<value>"}}}
\`\`\`
with `role: model` candidate marker.

- For UI / visible changes, a media URL:
<https://<user>.github.io/screenshots/pr-<N>/screen-cast.webm>

- For backend-only changes touching `$PROJECT_ROOT/**/*.py`, a real import-call
  probe against the PR head SHA + a gist URL of the captured output:
\`\`\`python
# /end2end-testing — import-call probe:
from mvp_site.campaign_divine import is_multiverse_upgrade_available
assert is_multiverse_upgrade_available({...}) is False
\`\`\`
Gist: <https://gist.github.com/<user>/<id>/raw/<sha>/probe.log>

## Real LLM Evidence
- /es bundle (gist, JSON): <https://gist.github.com/<user>/<id>/raw/<sha>/bundle.json>
- Capture command line:
\`\`\`bash
agy --dangerously-skip-permissions --print --model "<model>" \\
    --prompt "$(cat <<'EOF'
<full prompt + scene request>
EOF
)"
\`\`\`
- Sample response excerpt:

\`\`\`json
{"role": "model", "content": "<echo of narrative>"}
\`\`\`

## Evidence
- /es bundle URL: <https://gist.github.com/<user>/<id>/raw/<sha>/bundle.json>
- Capture script: `~/.hermes/scripts/worldai/<your-test>.py`
- GitHub PR HEAD SHA: `<ec74ca...>`
- Contract check exit code: `0` (PASS)
- Bead ID (if any): `<rev-XXXX>` or "no bead — straightforward change"

## Tenets (or ## Design Decision)
<REQUIRED for production-code PRs to satisfy Gate-0 (Design Doc Grep Gate).>
- Linked artifact: `world_reference/<file>.md` (must exist on disk at this path)
- Bead reference: `<rev-XXXX>` or `.beads/issues.jsonl`
- Why this change: <one-line rationale tying the diff to the design doc>
```

## Why this exists

Discovered while debugging **PR #8467** ($GITHUB_REPOSITORY, 2026-07-20):
- First body had `## Summary`, `## Real LLM Evidence`, `## Known Limitations`,
  `## Verification` — beautifully written, completely wrong shape.
- Gate-6b validator reported:
  `missing_sections: [Production Code Changes, Test Changes, Unit Test Evidence, Non-Unit Test Evidence, Evidence]`
  — 5 missing, 0 anchor violations.
- Estimated cost: 2-3 more CI cycles to discover the right shape on worldai's
  self-hosted runner pool (~3 minutes per cycle = 6-9 minutes wasted).

## Why it pays off

Pre-flight local validation:

```bash
python3 .github/scripts/pr_description_gate.py --body-file /tmp/body.md \
  --changed-files $PROJECT_ROOT/foo.py \
  --changed-files $PROJECT_ROOT/foo_test.py
# Expect: "overall": "PASS"
```

Returns JSON. Local iteration = zero API cost. Push once green.

## When N/A is allowed

Per the v1.2.0 GATE-6b logic in the parent skill:
- `$PROJECT_ROOT/prompts/**` files → `## Real LLM Evidence` requires LLM response
  markers (`role: model`, `Request:`/`Response:` lines, `LLM_RESPONSE_MARKERS`).
- `$PROJECT_ROOT/frontend_v*/**` or `$PROJECT_ROOT/static/**` or `$PROJECT_ROOT/templates/**`
  → `## Non-Unit Test Evidence` requires media URL (`.mp4|.gif|.cast|.webp`
  or `loom.com`/`asciinema.org`/`user-attachments`).
- `$PROJECT_ROOT/**/*.py` (outside tests) → `## Non-Unit Test Evidence` requires
  LLM response OR `/end2end-testing` response/payload marker.
- Docs-only (`docs/`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `.claude/`,
  `.codex/`, `.cursor/`) → all evidence gates bypass with
  `GATE-6 PASS: docs-only change set`.

For docs-only changes, drop the evidence sections in the body but keep the
8-section headers (with N/A bodies is OK; the validator only fails on
entirely-absent headers for the production/limited-section path).
