# Design Doc Grep Gate (Gate 0) + Tenets/Design-Decision section + empty-commit re-trigger trick

**Date:** 2026-07-28
**Affected PRs:**
- [$GITHUB_REPOSITORY#8662](https://github.com/$GITHUB_REPOSITORY/pull/8662) — `feat/shared-contracts-mbti-internal-drive`, +1473/-16, 13 files
- [$GITHUB_REPOSITORY#8661](https://github.com/$GITHUB_REPOSITORY/pull/8661) — `feat/spellblade-valeria-prompts`, +725/-0, 5 files

**Affected workflow:** `.github/workflows/design-doc-gate.yml` on `$GITHUB_REPOSITORY`
**Beads created:** `rev-bsyp2` (PR #8662), `rev-jlpp8` (PR #8661)

## Symptom

Both PRs opened with substantive code changes but **PR description bodies that lacked a `## Tenets` or `## Design Decision` section**. Within ~60s of opening, `Design Doc Grep Gates` reported:

```
❌ Tenets / Design Decision section NOT found in PR description
⚠️  No bead ID or .md link found in Tenets / Design Decision section
Non-test production delta lines: 340
❌ Gate 0 FAIL: PR has 340 non-test delta lines (>50) but lacks a Tenets / Design Decision section
   Add a ## Tenets (or ## Design Decision) section to the PR description linking a bead or roadmap doc.
```

`mergeable=MERGEABLE` but `mergeStateStatus=UNSTABLE` because Gate 0 was the upstream gate for Green Gate.

## Root cause

Two distinct facts that are not obvious from the failure log:

1. **The `design-doc-gate.yml` workflow's trigger pattern is `pull_request` events of type `[opened, ready_for_review, synchronize, reopened]`** — not `pull_request_description`. So editing the PR description via `gh pr edit --body-file` does NOT trigger a re-run. This is the same trap that v2.5.6 documented for `gh workflow run head_branch=main` but with the inverse polarity: there, a workflow_dispatch lands on the wrong branch; here, editing the PR body does nothing at all.

2. **The workflow's Gate 0 logic** (in `.github/workflows/design-doc-gate.yml`, the `design-decision-gate` step):
   ```bash
   DELTA_LINES=$(gh api repos/<OWNER>/<REPO>/pulls/<N>/files \
     | jq -s '[.[] | .[]? | select(.filename | test("^(?!.*(test|_test|tests/|spec/)).*$PROJECT_ROOT/.*\\.py$")) | .additions + .deletions] | add // 0')

   if (( DELTA_LINES > 50 )); then
     DESIGN_DECISION_FOUND=$(gh api repos/<OWNER>/<REPO>/pulls/<N> --jq .body | grep -iE '^## (Tenets|Design Decision)' || true)
     if [[ "$DESIGN_DECISION_FOUND" == "false" ]]; then
       DESIGN_GATE_RESULT="FAIL"
       GATE0_FAIL_REASON="PR has $DELTA_LINES non-test delta lines (>50) but lacks a Tenets / Design Decision section"
     elif [ -z "$LINKED_ARTIFACT" ]; then
       DESIGN_GATE_RESULT="FAIL"
       GATE0_FAIL_REASON="PR has Tenets / Design Decision section but no linked bead (rev-xxxx) or .md artifact"
     fi
   fi
   ```

   The regex `^## (Tenets|Design Decision)` requires the heading at line start. Indented or sub-bulleted variants fail. The bead-link check is a separate `grep -iE '(rev-[a-z0-9]+|\.md)'` against the same body.

## Detection recipe (30 seconds)

```bash
# 1. Confirm the gate failed (not just in_progress or transient)
gh api repos/<OWNER>/<REPO>/commits/<HEAD_SHA>/check-runs \
  --jq '.check_runs[] | select(.name|contains("Design Doc")) | {name,status,conclusion,html_url}'

# 2. Confirm the workflow's trigger pattern (catch the pull_request_description trap)
gh api repos/<OWNER>/<REPO>/contents/.github/workflows/design-doc-gate.yml \
  --jq .content | base64 -d | grep -A5 "^on:"

# 3. Read the body for the required sections + bead link
gh pr view <N> --repo <OWNER>/<REPO> --json body --jq .body | grep -E '^## (Tenets|Design Decision|Linked artifacts)|rev-[a-z0-9]+'
```

## Fix recipe (verified end-to-end on PR #8662 + #8661, 2026-07-28)

```bash
# Step 1: Create a bead for traceability (from MAIN CHECKOUT, not worktree)
cd <main-checkout>  # e.g. $HOME/projects/your-project.com
br create "<feature title> (PR #<N>)" --type feature --priority 2 \
  --description "<PR scope summary>"
# Note the returned rev-xxxx ID (e.g. rev-bsyp2)

# Step 2: Write the new PR body with the required sections + bead link
cat > /tmp/pr-<N>-body.md <<EOF
## Tenets

**Goal**: <one-sentence scope summary>.

**Design Decision** (record):

1. <Rule 1 name> — <rule statement + where enforced>
2. <Rule 2 name> — <rule statement + where enforced>
3. <Rule 3 name> — <rule statement + where enforced>
4. <Rule 4 name> — <rule statement + where enforced>

**Linked artifacts**:

- Bead: rev-xxxx — <title>
- Companion PR: [#<N> (<short title>)](<url>)
- Reference docs: [<doc name>](<url>) (optional)

---

<rest of the existing PR body>
EOF

# Step 3: Edit the PR body (no PR state change)
gh pr edit <N> --repo <OWNER>/<REPO> --body-file /tmp/pr-<N>-body.md
# Verify the body landed
gh pr view <N> --repo <OWNER>/<REPO> --json body --jq .body | head -25

# Step 4: Empty-commit + push to force the gate to re-run
cd <worktree>  # e.g. /private/tmp/wt-shared-contracts
git -c user.name=claude -c user.email=claude@anthropic.com \
  commit --allow-empty \
  -m "chore(<scope>): re-trigger Design Doc Grep Gate after adding ## Tenets + ## Design Decision sections"
git push origin HEAD:<branch>

# Step 5: Wait ~30s, verify the gate re-ran and passed
gh api repos/<OWNER>/<REPO>/commits/<new-sha>/check-runs \
  --jq '.check_runs[] | select(.name|contains("Design Doc")) | {name,status,conclusion}'
# Expected: { "name": "Design Doc Grep Gates", "status": "completed", "conclusion": "success" }
```

## Live proof (2026-07-28)

PR #8662 timeline:

| Timestamp | Event | Detail |
|---|---|---|
| T+0 (PR open) | Design Doc Grep Gates FAIL | "Non-test production delta lines: 340. Gate 0 FAIL" |
| T+30s | Parent edits PR body via `gh pr edit --body-file` | Adds `## Tenets` + `## Design Decision` + `## Linked artifacts` with `rev-bsyp2` bead link |
| T+45s | Parent pushes empty commit `9dae74c2c37` | Forces `synchronize` event |
| T+1m 15s | Design Doc Grep Gates re-runs on new SHA | conclusion=success |

PR #8661 followed the identical pattern with commit `ce82f932b00` and bead `rev-jlpp8`. Both flips happened within the same 60s window.

## Anti-patterns (verified wasted time)

1. **Editing the PR body only, then waiting for the gate to re-run.** The gate has no `pull_request_description` trigger — it will not re-run. You'll sit indefinitely thinking your description was updated. Always push a code change (commit + push) to re-trigger.

2. **Creating the bead in the worktree** instead of the main checkout. `br create` reads from the main checkout's `.beads/issues.jsonl`. The worktree may have its own git state that doesn't include the bead file. The bead will be created against the worktree's HEAD, which is the PR head — and not committed to `.beads/issues.jsonl` on `main`. Beads must be committed via the PR's normal flow.

3. **Forgetting to verify the body landed.** GitHub's PR body parser is strict; malformed markdown can cause `gh pr edit` to silently truncate. Always run `gh pr view N --json body --jq .body | head -25` after the edit.

4. **Creating a `## Design Decision` heading but no bead link.** The regex checks for the heading AND for a `rev-xxxx` token or `.md` link in the same body. Both are required.

5. **Using `rev-` lowercase only.** The regex is case-insensitive (`grep -iE 'rev-[a-z0-9]+'`), but in practice `br create` returns lowercase IDs. Stick to `rev-xxxx` lowercase format to match the workflow's examples.

6. **Triggering the workflow before the body is updated.** If you push the empty commit BEFORE editing the body, the gate re-runs against the old description and re-fails. Edit body FIRST, then push the empty commit.

## Recipe ordering (matters!)

The correct order is:

1. Create bead (from main checkout).
2. Edit PR body with `## Tenets` + `## Design Decision` + bead link.
3. Verify body landed.
4. Push empty commit.
5. Verify gate re-ran + passed.

Reversing 2 and 4 wastes a CI cycle (~60s).

## Companion fixes (track separately)

- **`.github/workflows/design-doc-gate.yml` could add a `pull_request_description` trigger** to allow body edits alone to re-trigger. But that's a workflow-shape change that requires its own PR + review. For now, the empty-commit trick is the canonical fix.
- **A PR template at `.github/pull_request_template.md` could pre-include the `## Tenets` and `## Design Decision` sections** so agents don't forget. Track as a harness-level improvement.

## Cross-references

- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` v2.5.13 — the umbrella skill body section with the recipe summary.
- `~/.claude/skills/dispatch-task/SKILL.md` — the `br create` syntax reference.
- `~/.hermes/skills/babysit-stale-watchdog/SKILL.md` — sibling skill for cron-based babysits (not needed for this gate, which is a simple wait-for-30s verification).
- v2.5.6 `gh workflow run head_branch=main` pitfall — symmetric trap (workflow_dispatch on the wrong branch vs pull_request_description trigger missing).
