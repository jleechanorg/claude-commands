---
name: pre-push-ci-lint-preflight
description: Pre-flight checklist for opening a PR against a strict-CI repo
  (jleechanorg/*) — pre-pass the repo's known-class lint requirements before
  pushing so the first CI cycle doesn't fail on `Beads:`, `beads-jsonl-validation`,
  `import-validation`, prompt-contract-hash, schema-coverage-guard, or other
  project-specific body/workflow lints. Companion to finish-the-job
  "Phase 0 docs-only PR fast path" and the Phase 4 "PR open with green CI awaiting
  user merge" end-state. v1.0.0 verified 2026-07-08 with PR #8241; v1.1.0
  addendum (2026-07-14, PR #8399) adds the GATE-6b `## Evidence`
  substring-match gotcha and the `pytest.skip(allow_module_level=True)`
  false-green-guard pitfall for behavioral Playwright tests.
---

# Pre-push CI lint pre-flight — checklist for `gh pr create`

## v1.1.0 addendum (2026-07-14, your-project.com PR [#8399](https://github.com/$GITHUB_REPOSITORY/pull/8399))

Two more known-class lint pitfalls surfaced on a CSS-only fix PR. Both are
deterministic — pre-pass them before pushing.

### GATE-6b substring match: rename `## Evidence Gist` → `## Evidence`

The PR-description-gate (`pr_description_gate.py` in
`.github/scripts/`) does a substring match against expected section
headings, but the failure report says "missing section" even when the
section is present under a *synonymous* heading. `## Evidence Gist`
contains `## Evidence` as a prefix, but the validator still reports:
```
GATE-6b FAIL: PR description gate rejected PR body
  missing_sections: ["## Evidence"]
  section_checks: [{ "header": "## Evidence Gist", "present": true, "has_content": true, ... }]
```

The section IS present, but the heading text doesn't match the canonical
name the gate expects. The gate lists `## Evidence` in its required
sections — it doesn't tell you that `## Evidence Gist` is the wrong
text on failure; it just says "missing".

**Fix:** use the exact required heading text. Canonical headings for a
your-project.com PR that touches `$PROJECT_ROOT/`:
- `## Summary`
- `## Production Code Changes`
- `## Test Changes`
- `## Unit Test Evidence`
- `## Non-Unit Test Evidence`
- `## Real LLM Evidence`
- `## Evidence`        ← exactly this, not "Evidence Gist", "Evidence bundle", "Visual proof", etc.
- `## Known Limitations`
- `## Risk`
- `## Out of scope`
- `## Branch / Commits`
- `## Beads`

Lesson: when pre-passing the body, copy the heading text from a recent
passing PR's `gh pr view <N> --body` rather than improvising synonyms.
Embed the URL of that passing PR as a one-line reference in your session
notes so future sessions have a known-good template.

### `pytest.skip(allow_module_level=True)` returns exit code 5 → false-green guard fires

For behavioral Playwright tests in
`$PROJECT_ROOT/tests/test_*_behavioral.py`, the temptation is to gate the
whole module on whether Chromium / a network call / an env var is
available:

```python
# at top of module
if not chromium_available():
    pytest.skip("no chromium", allow_module_level=True)
```

**This is a CI failure, not a CI skip.** `run_tests.sh` (your-project.com's
test launcher) has a false-green guard that interprets pytest exit code 5
("no tests collected") as a CI failure:

```
FAIL DEBUG: pytest collected 0 tests — false-green guard (exit 5)
```

It happens because `pytest.skip(allow_module_level=True)` makes pytest
report zero collected-and-run tests and return exit code 5 (distinct
from exit code 0 with skips). The false-green guard catches this on
purpose — a test file that "passes" while running zero tests is worse
than no test file at all (it gives false confidence in CI green).

**Right pattern (verified on PR #8399 — matches the existing
`test_navbar_mobile_layout_behavioral.py` shape):**

```python
playwright = pytest.importorskip("playwright.sync_api")  # module-level OK — register skip at collection

def test_no_overflow_at_1280(self, viewport):
    chromium = self._require_chromium()  # function-level skip, NOT module-level
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=chromium)
        ...

def _require_chromium(self):
    chromium = "$HOME/Library/Caches/ms-playwright/chromium-1217/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing"
    if not os.path.exists(chromium):
        pytest.skip(f"Chromium not available at {chromium}")
    return chromium
```

`pytest.importorskip` at module-level is fine — pytest reports `N skipped
in 0.08s` and exits 0. What triggers exit 5 is `pytest.skip(allow_module_level=True)`.

If you can't even import the module without the dep (eg the test file
imports `playwright.sync_api` at top), the safer shape is:

```python
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    sync_playwright = None

def test_xxx(self):
    if sync_playwright is None:
        pytest.skip("playwright not installed")
```

The module imports cleanly; each test self-skips if its dep is missing;
pytest exits 0 with skips counted.

Lesson: pre-pass any new behavioral test against the false-green guard
*BEFORE* committing — run `run_tests.sh` locally OR check `pytest -q
tests/test_xxx_behavioral.py` exit code: if exit != 0 AND exit != 1
(the normal `tests failed` code), your skip pattern is wrong and CI
will fail even though the test "passes" when run.

### Reusable body template addition (v1.1.0)

The v1.0.0 body template (above) used `## Evidence` correctly. Two
additions needed by GATE-6b for any PR that touches `$PROJECT_ROOT/`:

```bash
BODY=$(cat <<EOF
## Summary
<one paragraph>
## Production Code Changes
<file:line summary>
## Test Changes
<file:line summary>
## Unit Test Evidence
<count of new/passing unit tests, with the pytest command run>
## Non-Unit Test Evidence
<captioned gif, cast, loom, asciinema, or user-attachments link to a non-unit-test artifact>
MD screenshot / GIF / loom link here
## Real LLM Evidence
N/A — <why this PR doesn't produce LLM-visible behavior change>
## Evidence
<public gist URL with binary PNGs/GIFs, sizes, captions>
## Known Limitations
<bullet list — anything not fixed, async work, follow-up beads>
## Risk
<risk level + any blast radius concerns>
## Out of scope
<explicit non-goals, related issues that aren't addressed here>
## Branch / Commits
<git log output of the PR branch's commits>
## Source
<where the task originated — Slack thread ts, GH issue link>
Beads: <REV-xxx or none>
EOF
)
```

GATE-6b will fail `## Non-Unit Test Evidence` for an $PROJECT_ROOT/-touching
PR that doesn't include a captioned visual/link. Verified on PR #8399's
first push — the standalone `## Evidence` section was present (with
image links) but `## Non-Unit Test Evidence` was missing its
caption-prefaced visual link until I added the 2-frame GIF.

---

## Original v1.0.0 content starts here

## Verified bug case (2026-07-08, your-project.com PR [#8241](https://github.com/$GITHUB_REPOSITORY/pull/8241))

**Setup:** Opening a 1-file, 1-line docs-only PR (`$PROJECT_ROOT/prompts/narrative_system_instruction.md` L1318) — dead-pointer fix. Local commit was clean and the diff was exactly the intended one-liner.

**Failure mode:** First `gh pr create` push triggered the CI lint job **"PR body has Beads line"** with verdict `fail` in 4 seconds:

```
PR body has Beads line  Validate Beads line in PR body
...
2026-07-08T01:45:26.5783242Z ##[error]PR body is missing the required Beads: line.
2026-07-08T01:45:26.6085246Z ##[error]Add one of:
2026-07-08T01:45:26.6087636Z ##[error]  - Beads: REV-xxxx (or comma-separated list) when this PR closes/fixes/refs a bead
2026-07-08T01:45:26.6090408Z ##[error]  - Beads: none if no bead applies (explicit opt-out)
```

**Cost of the post-push fix cycle:**
1. CI confirmed-fail; `gh pr edit --body` to add `Beads: none`
2. Required BEADS line check re-triggered on the next tick (~60s) and passed
3. The cycle cost ~5 min + 1 push + 1 API edit + 60s wait

The principle: **known-class CI body-lint failures are deterministic and should be pre-passed**, not learned-from-failure.

## The pre-push lint checklist (jleechanorg/* repos)

Before `gh pr create` for the first time against any `jleechanorg/*` repo, run:

```bash
REPO=jleechanorg/<repo>     # your-project.com, ez-gh-actions, etc.

# 1. Read the repo's custom GHA lint workflows — these define the body-shape rules.
gh workflow list --repo "$REPO" --json name --jq '.[] | .name' \
  | grep -iE "(lint|body|beads|prompt|schema|import|contract)" | head -20

# 2. Faster than parsing the workflow YAML: hit the .github/workflows/ dir directly.
gh api "repos/$REPO/contents/.github/workflows?ref=main" \
  --jq '.[] | select(.name | test("(body|beads|prompt|schema|import|contract|lint).*\.yml$"; "i")) | .name'

# 3. Cross-check against the same lint job names that fired on your last N PRs:
gh pr list --repo "$REPO" --state all --limit 10 \
  --json number,title \
  --jq '.[] | {n: .number, t: .title}'

# 4. Confirm the local body template passes the linter by DRY-RUNNING gh pr create
#    into a local file first. The simplest version: keep a known-good body
#    template in your session notes that the WA-repo linters accept.
```

### Known-class body / workflow lints ($GITHUB_REPOSITORY, 2026-07-08)

| Lint job | Failure pattern | Pre-pass fix |
|---|---|---|
| `PR body has Beads line` | Missing `^Beads: <id-or-none>` line (standalone) | Append `Beads: REV-xxxx` if a bead applies OR `Beads: none` for opt-out — never omit the line |
| `.beads/issues.jsonl sorted by id` | `.beads/issues.jsonl` was modified but not re-sorted | `br sync` then re-commit before pushing |
| `beads-jsonl-validation` | Malformed beads record (missing field, wrong type) | Run `br validate` locally before commit |
| `import-validation` | Local import redirects that conflict with the live repo | Read the project's `.claude/import-allowlist.json` before introducing a new import path |
| `Prompt / Tool Contract Hash Validation` | Prompt/tool contract text changed without the matching hash field | Update the hash in the contract file AND re-run the contract hash generator |
| `Schema Coverage Guard` | New emitted field has no matching schema entry | Add the schema field BEFORE running the prompt in the diff |
| `detect-changes` | Diff too large for the workflow's `paths:` filter | Confirm you actually triggered the workflow you expected (silently no-ops when `paths:` doesn't match) |

### Known-class test/lint checks that hold the PR back but won't appear as `fail` immediately

These aren't body lints but are common first-push surprises on your-project.com. They sit in the queue and may take 2-6 minutes to surface, blocking the first reconciliation cycle:

- `Prompt / Tool Contract Hash Validation` (Python prompt-hash mismatches in `$PROJECT_ROOT/prompts/`)
- `Schema Coverage Guard` (`schemas/*.json` drift vs LLM-emitted fields)
- `Function LOC Ratchet (world_logic.py / llm_service.py)` — fails when LOC crosses a ratchet threshold even on accidental whitespace changes
- `Python Linting (Ruff)` / `Python Type Checking (mypy)` — when the PR touches any `.py` file

For docs-only PRs (only `*.md` files under `$PROJECT_ROOT/`), the only body-lint that fires is `PR body has Beads line`. The other checks all `pending` indefinitely waiting for paths they don't match.

### Two cheap preflight commands before `gh pr create`

```bash
# 1. Confirm the body passes WA's beads-pr-lint standalone line check:
grep -qE "^Beads: (REV-[a-z0-9]+|none)$" /tmp/pr-body.md \
  && echo "PASS: Beads line present" \
  || echo "FAIL: add 'Beads: REV-xxx' (or 'Beads: none') as standalone line"

# 2. Confirm the diff is exactly the intended scope (no surprise files):
git diff origin/main...HEAD --name-only
```

## The reusable body template (your-project.com docs PRs)

Use this shell-heredoc template for any `gh pr create` on $GITHUB_REPOSITORY docs-only PR:

```bash
BODY=$(cat <<EOF
## Summary

<one-paragraph what changed>

## Root cause

<why the bug is the bug — file:line, commit, prior state>

## Impact

- **Runtime behavior:** <zero | change with description>
- **Documentation:** <now correct|unchanged>

## Changes

\`\`\`diff
<the actual diff>
\`\`\`

## User Stories

N/A — <why no user-visible change>

## Evidence

N/A — documentation-only fix, no LLM-visible behavior change. <cite which file paths are unchanged but were the canonical source of truth>

## Verification

\`\`\`bash
# <commands proving the change is scoped correctly>
\`\`\`

## Source

<where the task originated — Slack thread ts, GH issue link, etc.>

Beads: none
EOF
)
gh pr create --base main --head <branch> --title "<prefix>(<scope>): <title>" --body "$BODY"
```

The terminal `Beads: none` line is the **only** line that consistently fails when omitted; everything else above is documentation discipline that the user has come to expect on WA PRs.

## When this pre-flight is NOT enough

The following still require live-state verification (not just pre-push):

1. **Existing PR repair** — `drive-pr-to-green` Step 2's 5-check preflight is the right tool.
2. **Multi-PR sweep / batched merge** — candidate-list tier classification (see `references/nonprod-sweep-candidate-filtering-2026-07-07.md`) is a separate pre-push gate.
3. **PRs that touch `$PROJECT_ROOT/` production code** — `AGENTS.md` evidence requirement (Layer 2 end-to-end) is mandatory, NOT just a lint pre-pass.
4. **PRs with new env vars, secrets, or deploy config** — `doctor.sh` approval flow applies (NOT a `gh pr create` concern).

## Why this belongs in `finish-the-job`, not `drive-pr-to-green`

`drive-pr-to-green` assumes an **existing** PR with a known `headRefOid` and walks the diagnostic→fix→push→wait→merge sequence. The body-lint pre-pass fires at **PR creation**, before `headRefOid` exists and before any of `drive-pr-to-green`'s steps apply.

The right home is `finish-the-job`'s Phase 0 docs-only PR fast path, because that path also creates a PR fresh (no prior state, no prior lint check). The reference lives in `finish-the-job/references/` and the umbrella gets a one-line cross-reference pointer; the contract row "PR open with green CI awaiting user merge" gets a qualifier "and free of known-class lint failures on first push."

## Citations

- `~/.claude/CLAUDE.md` — `WA Checkout 488-550s → fetch-depth:1+submodules:false+lfs:false` + bead-pr-lint standalone `^Beads:` line rule
- Verified incident: 2026-07-08, $GITHUB_REPOSITORY PR [#8241](https://github.com/$GITHUB_REPOSITORY/pull/8241), commit `550cad6bea` — `[antig] fix(prompts): restore dead-pointer from narrative ripples Quick Reference`
- Companion umbrella: `finish-the-job` v1.5.0+ "Docs-only PR fast path" Phase 0 entry
- Companion umbrella: `drive-pr-to-green` Step 2 5-check preflight (for existing-PR repair, separate gate)
