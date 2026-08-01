---
name: preflight-sibling-pr-same-campaign
description: Before dispatching a `/repro` or any campaign-scoped PR, surface sibling open PRs on the same campaign ID even when they target different symptoms. Prevents parallel-branch races when two agents independently dispatch on a campaign's symptoms. Verified 2026-07-14 on $GITHUB_REPOSITORY: dispatched PR #8385 (campaign-difficulty) for RMCPAPdfuErh8MgRuj6n, while sibling PR #8383 (NPC speech, feat/pc-voice-in-heavy-dialog) on the same campaign was already in flight — caught via the pre-flight, kept them separate.
---

# Preflight: surface sibling PRs on the same campaign ID before dispatch

The canonical `finish-the-job` "PR-topology pre-flight" checks for existing open PRs matching **the failure's topic/branch/issue**. That misses a different class: **sibling PRs on the same campaign ID that target a different symptom**. When two agents (or two of the user's messages) trigger PRs against the same campaign, the second dispatch can land in parallel with the first, cross-polluting prompt changes.

**Symptom:** User dispatches PR-A for symptom-X on campaign Z. Hours later (or the same session), user dispatches PR-B for symptom-Y on campaign Z. Both PRs touch `$PROJECT_ROOT/prompts/` or `$PROJECT_ROOT/prompts/dialog_*`, both add tests, both bump bead state. Reviewer reviews are duplicated, prompt files get conflicting edits, the worker for PR-B sees PR-A's commits and either rebases on top (loses ZFC independence) or ignores them (conflict at merge time).

**Pre-flight (≤30s, do this BEFORE `ao spawn` for any `/repro` on a campaign ID):**

```bash
# 1. Surface all open PRs touching the same campaign ID or the same prompt surface
CAMPAIGN_ID="<e.g. RMCPAPdfuErh8MgRuj6n>"
gh pr list --repo $GITHUB_REPOSITORY --state open \
  --json number,title,headRefName,createdAt,files \
  --jq ".[] | select(
      (.title | test(\"$CAMPAIGN_ID|${CAMPAIGN_ID:0:8}\"; \"i\")) or
      (.body | test(\"$CAMPAIGN_ID\"; \"i\")) or
      (.headRefName | test(\"$CAMPAIGN_ID|${CAMPAIGN_ID:0:8}\"; \"i\"))
    ) | {n: .number, t: .title, br: .headRefName, files: [.files[].path] | .[0:5]}"

# 2. Broader sweep — any open PR touching the same prompt files you'll edit
PROMPT_FILES="$PROJECT_ROOT/prompts/narrative_system_instruction.md $PROJECT_ROOT/prompts/dialog_system_instruction.md"
gh pr list --repo $GITHUB_REPOSITORY --state open \
  --json number,title,headRefName,files \
  --jq --arg f1 "${PROMPT_FILES%% *}" --arg f2 "${PROMPT_FILES##* }" \
    ".[] | select(([.files[].path] | any(. == \$f1 or . == \$f2))) | {n: .number, t: .title, br: .headRefName}"

# 3. Issue scan — same campaign ID may have multiple issues (one per symptom)
gh issue list --repo $GITHUB_REPOSITORY --state open \
  --search "$CAMPAIGN_ID" --json number,title,state
```

**Decision matrix after pre-flight:**

| Finding | Action |
|---|---|
| 0 sibling PRs | Standard dispatch. |
| 1 sibling PR on same campaign ID, different symptom | Keep as **separate PRs**. Cross-reference each other's issue numbers in both PR descriptions ("Related: #N"). Pin which agent owns which prompt file set if prompts overlap. Do NOT bundle — bundle produces a 2-in-1 fix that reviewers reject one half of. |
| ≥2 sibling PRs on same campaign ID, same root-cause class | Treat as a **campaign-cluster structural issue** — load `convergent-bug-triage` skill, consider a single root-cause-first PR that supersedes both. |
| 1 sibling PR on same campaign ID, same symptom | **Pivot.** Don't dispatch a parallel branch. Pivot to driving the existing PR — even if the user asked for a fresh `/repro`. Document the pivot in the originating thread per `finish-the-job` "PR-topology pre-flight" rules. |

**Verified 2026-07-14 (PR #8385 dispatch):**

User's request was a `/repro` for campaign `RMCPAPdfuErh8MgRuj6n` difficulty regression. Pre-flight found:
- `gh pr list --search "RMCPAPdfuErh8MgRuj6n OR difficulty OR too easy"` → returned PR #8383 (`fix/pc-voice-in-heavy-dialog`, NPC speech) and a few unrelated PRs (signature detection, roadmap sweep).
- PR #8383 was opened 17 hours earlier by a sibling agent on a different symptom (NPC speech scarcity) for the same campaign. It touched `$PROJECT_ROOT/prompts/dialog_system_instruction.md` and `$PROJECT_ROOT/prompts/narrative_system_instruction.md`.
- Pre-flight found it. Decision: keep PR #8385 (difficulty) and PR #8383 (NPC speech) as **separate PRs**, cross-reference each other's issues in both PR bodies, instruct the worker to scope prompt edits to the difficulty surfaces only and not touch NPC-speech changes. PR #8383 stays in its lane.

**Anti-pattern:** dispatching a `/repro` PR on a campaign with an existing sibling PR open on the same campaign ID, without checking, produces one of these:
- **Silent conflict:** the new PR re-edits a prompt file the sibling PR already touched; the worker doesn't see the sibling's commit history and the diff merges cleanly but produces a logically inconsistent prompt.
- **Stale rebase:** the new PR rebases onto main, accidentally pulls in the sibling PR's prompt changes, and the worker assumes those changes are its own — losing ZFC independence and contaminating the diff.
- **Reviewer fatigue:** CodeRabbit and Bugbot see two open PRs on the same campaign and review them in parallel, often producing duplicated review comments on the shared prompt files.

**Cross-reference:** `finish-the-job` §"PR-topology pre-flight: mandatory before Phase 2 dispatch on recurring alerts" covers the same-root-cause-class case. This file is the missing sibling-symptom case — same campaign ID, different symptoms.

`convergent-bug-triage` skill covers the ≥3-same-campaign case. This file covers the 1-2-sibling case where keeping them separate is still right.