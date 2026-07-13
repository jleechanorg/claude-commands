---
name: fixpr
description: Analyze and fix PR blockers (CI failures, merge conflicts, bot/review feedback) to get a PR into a mergeable state — never merges it. GitHub status is the sole source of truth over local assumptions. Slash command /fixpr. Also embodied as the copilot-fixpr subagent type for parallel/automated PR-fixing dispatch. Use when a PR has failing CI, merge conflicts, or unresolved bot comments and needs to be driven to green.
---

# /fixpr — PR Fix Analysis (local-first, GitHub-authoritative)

**Purpose**: get a PR to a mergeable state (all checks passing, no conflicts, no blocking reviews) — never merge it. The user retains control over when/if to merge.

## The three commandments

1. **Local-first**: never push a fix until you've reproduced the failure locally, fixed it, and verified the full local test suite passes.
2. **GitHub is the sole source of truth**: never assume local conditions match GitHub reality. Fetch fresh GitHub status before any analysis, display it inline, and re-verify after every fix. `mergeable: "MERGEABLE"` only means no merge conflicts — it does **not** mean CI passed. Use `mergeStateStatus` and the individual `statusCheckRollup` conclusions, never `mergeable` alone.
3. **Never merge**: success means the merge button would be green, not that you clicked it.

## 2026-07 fleet-drive lessons (read before touching a multi-PR backlog)

These came out of driving a real 40+ PR backlog and matter as much as the mechanics below:

- **CodeRabbit staleness is the single biggest lever, not code defects.** A large fraction of "blocked" PRs are otherwise fully CI-green and blocked purely on a stale-or-missing CR approval at head. Check CR review state before assuming a code fix is needed — re-triggering review often unblocks more than any fix would.
- **Check for active external automation before touching a PR.** A meaningful share of any backlog is already under active bot iteration (this exact `/fixpr` methodology running as the `copilot-fixpr` subagent, or codex automation) at any given moment — that work is partly self-resolving. Touching a PR that's mid-automation just races it; check recent commit/comment cadence first.
- **Evidence/review staleness compounds fast — re-derive, don't trust cached citations.** The dominant risk in a PR-fixing pass is stale artifacts, not incorrect code. Every real bug found in recent sessions came from re-deriving evidence at the PR's actual current head SHA rather than trusting an existing citation or a previous run's output.
- **"70+ open PRs" overstates actionability.** Typically only a minority are genuinely ready for a human merge call at any moment; most are either bot-blocked (CR staleness) or automation-in-progress. Triage before batch-driving.

## Workflow

### Step 0: Verify GitHub CLI auth (mandatory pre-flight)

```bash
if ! gh auth status; then
  echo "GitHub CLI not authenticated - run 'gh auth login' first"
  exit 1
fi
```

### Step 1: Gather repository context

Extract repo owner/name from git remote (handle both HTTPS and SSH URL forms), determine the default branch without assuming `main` (could be `master`/`develop`). Quote all bash variables.

### Step 2: Fetch fresh GitHub PR status (authoritative — never trust cache or local state)

```bash
status=$(gh pr view "$PR" --json mergeStateStatus,statusCheckRollup,mergeable,reviews,comments)
merge_state=$(echo "$status" | jq -r '.mergeStateStatus // "UNKNOWN"')

# statusCheckRollup.contexts.nodes is the LIST of individual checks — never
# call .get()/jq-index the rollup wrapper itself, only iterate the list.
failed_checks=$(echo "$status" | jq '[(.statusCheckRollup.contexts.nodes // [])[]
  | select((.conclusion // .state // "")
      | test("^(FAILURE|ERROR|TIMED_OUT|ACTION_REQUIRED|CANCELLED)$"))]')
failed_count=$(echo "$failed_checks" | jq 'length')

if [[ "$merge_state" == "CLEAN" ]] && [[ "$failed_count" -eq 0 ]]; then
  echo "Actually ready to merge"
else
  echo "Blocked: $merge_state, $failed_count failing checks"
fi

# Human-readable failing-check summary
gh pr view "$PR" --json statusCheckRollup --jq \
  '(.statusCheckRollup.contexts.nodes // [])
   | map(select((.conclusion // .state // "") | test("^(FAILURE|ERROR|TIMED_OUT|ACTION_REQUIRED|CANCELLED)$")))
   | map("\((.name // .context) // "unknown"): \((.description // "no description provided"))")
   | .[]'
```

Fetch and display inline, all from GitHub (never assume local state matches):
- **CI/checks**: `statusCheckRollup` per above.
- **Merge conflicts**: `mergeable`, `mergeStateStatus`; `gh pr diff <PR>` for actual conflict content.
- **Bot/review feedback**: `reviews`, `comments` — both are LISTS; iterate, never `.get()` the array itself. A blocking review looks like `CHANGES_REQUESTED by @reviewer`.

**Defensive parsing pattern** (GitHub API responses vary between dict/list shapes; never assume):
```python
nodes = []
if isinstance(status_data, dict):
    nodes = ((status_data.get('statusCheckRollup') or {}).get('contexts') or {}).get('nodes') or []
for check in nodes:
    if isinstance(check, dict):
        outcome = check.get('conclusion') or check.get('state') or ''
        name = check.get('name') or check.get('context') or 'unknown'
        if outcome in ('FAILURE', 'ERROR', 'TIMED_OUT', 'CANCELLED', 'ACTION_REQUIRED'):
            print(f"Failed: {name}")
```

### Step 3: Detect CI-vs-local discrepancies

Run the local test suite first (detect the runner: `npm test`, `pytest`, `make test`, etc). If local passes but GitHub CI fails, that's a discrepancy — common causes: Python/dependency version drift, missing CI env vars, race conditions only manifesting in CI, timezone/locale differences, filesystem case-sensitivity (CI often Linux, local often macOS).

**When discrepancy detected, trigger `/redgreen` (alias `/tdd`)**:
1. **RED**: `/redgreen --pr <PR> --check "<check-name>" --gh-log "<the exact GitHub error>"` — reproduce the GitHub failure as a local failing test.
2. **GREEN**: fix the code so both local and GitHub pass.
3. **REFACTOR**: clean up while keeping coverage.

Do not modify code for a CI-vs-local discrepancy until `/redgreen` has produced the matching local failure — fixing blind against a discrepancy you haven't reproduced is how "fixes" that don't actually fix GitHub happen.

### Step 4: Apply fixes

Focus on the immediate blockers in this PR. Common categories: environment issues (deps, env vars, timeouts), code issues (imports, assertions, types), test issues (expectations, races, edge cases).

**Pattern detection** (optional `--scope=pattern`): after fixing the immediate blocker, scan the codebase for the same pattern elsewhere (e.g. a Firestore-mocking mismatch that recurs across several test files) and fix all instances — prevents the same class of failure recurring in the next PR.

### Step 5: Merge conflicts (if present)

```bash
git pull origin main
# resolve conflicts
PR_NUMBER="<pr-number>"
BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
DOCS_DIR="docs/conflicts/$(echo "$BRANCH_NAME" | tr '/' '-')-pr${PR_NUMBER}"
mkdir -p "$DOCS_DIR"
# document EACH conflict resolution in $DOCS_DIR/conflict_summary.md, then:
# re-run full test suite, only then commit+push
```

**Every conflict resolution must document**: file, conflict type, original markers, resolution, WHY, risk level (Low/Medium/High). Preservation priority: never lose functionality (combine features when possible), prefer bug fixes over new features on conflict, maintain backward compatibility, keep security improvements from both branches.

Example `conflict_summary.md` entry:
```markdown
### File: src/auth.py
**Conflict Type**: Authentication logic
**Risk Level**: High
**Original Conflict**:
\```python
<<<<<<< HEAD
def login(user, password):
    return basic_auth(user, password)
=======
def login(user, password, mfa=None):
    if mfa:
        return mfa_auth(user, password, mfa)
    return basic_auth(user, password)
>>>>>>> main
\```
**Resolution**: Kept main branch version with MFA support
**Reasoning**: Main branch added MFA (security improvement), backward compatible (mfa is optional), no conflicting business logic on our branch.
```

### Step 6: Pre-push checklist (mandatory — do not push if any item unchecked)

```
[ ] Reproduced the failure locally (saw the exact error locally)
[ ] Full local test suite passes (all tests, not just the affected one)
[ ] If merge conflicts existed: pulled main, resolved, documented in docs/conflicts/, re-ran full suite
[ ] git status is clean (no uncommitted changes)
```

### Step 7: Push and re-verify GitHub (never claim success from local state alone)

```bash
git add -A && git commit -m "fix: address CI failures / merge conflicts for PR #${PR_NUMBER}"
git push origin HEAD
sleep 60   # let GitHub CI process
gh pr view "$PR_NUMBER" --json statusCheckRollup,mergeable,mergeStateStatus
```

## Auto-apply mode (`--auto-apply`)

More autonomous, but scoped to safe fixes only: import corrections, whitespace/formatting, doc updates, bot-suggested non-logic-changing improvements. Always preserve existing functionality, business logic, and security patterns from both branches. Apply one category at a time, test after each, stop on unexpected failure.

## Risk classification for conflict/fix decisions

- **Low**: docs, comments, formatting, test additions.
- **Medium**: UI changes, non-critical features, config updates.
- **High**: auth, data handling, payment processing, API contract changes.

## Complex/parallel mode — 4 specialist agent roles

For PRs with >10 distinct issues or extensive CI failures, spawn specialists instead of one linear pass (Claude/the orchestrator retains overall workflow control):
1. **CI-Analysis-Agent** — GitHub CI failure analysis and fix recommendations.
2. **Conflict-Resolution-Agent** — merge conflict analysis and safe resolution.
3. **Bot-Feedback-Agent** — processes automated bot comments, implements applicable suggestions.
4. **Verification-Agent** — validates fix effectiveness, re-checks mergeability.

This is also the shape the `copilot-fixpr` subagent type embodies for automated/parallel dispatch across a PR fleet.

## Examples

```bash
/fixpr 1234                                # analyze + fix, default scope
/fixpr 1234 --auto-apply                   # auto-apply safe fixes only
/fixpr 1234 --scope=pattern                # fix + scan codebase for the same pattern elsewhere
/fixpr 1234 --scope=comprehensive --auto-apply

# CI-vs-local discrepancy (auto-triggers /redgreen):
# Local: all tests pass. GitHub: test-unit FAILING.
/fixpr 1234
# -> detects discrepancy, issues:
/redgreen --pr 1234 --check "test-unit" --gh-log "AssertionError: Expected 'foo' but got 'FOO'"
# -> reproduces locally, fixes, verifies both environments
```

## Integration points

- `/copilot` — comprehensive PR workflow orchestration (fixpr is one phase of it).
- `/commentreply` — respond to review feedback after fixing.
- `/pushl` — push fixes to remote.
- `/redgreen` (alias `/tdd`) — auto-triggered for CI-vs-local discrepancies.
- Project test suite — verify locally before every push.

## Error recovery

Gracefully handle missing tools by trying alternatives; explain clearly what failed and why; suggest manual steps when automation isn't possible; preserve partial progress rather than failing completely.
