# PR #8485 — production-code disable path that needed Gate-0 Tenets + gate-by-gate fix transcript

**Repo:** `$GITHUB_REPOSITORY`
**PR:** https://github.com/$GITHUB_REPOSITORY/pull/8485
**Branch:** `feat/multiverse-disabled` ← `origin/main`
**Title:** `feat: disable sovereign/multiverse tier (PR #1 of 2 for god-mechanics redesign)`
**Head SHA:** `afaaf4aaf886ac3d4c51ba2bb68f1bf09c1b3a9a` (then `cf74e8db55`, then `ee9e9c7b45` for the body-shape commits)
**Author:** $USER
**Date:** 2026-07-20

## Why this PR is the canonical reference case

PR #8485 hit **four distinct gate failures** simultaneously and required **three empty commits** to drive to N-green (4/7 — GATE-1 / GATE-3 still red from vendor throttles):

1. **GATE-0 (Design Doc Grep)** — the production-code PR (5 backend files) lacked `## Tenets` + linked `world_reference/*.md` artifact
2. **GATE-1 (CI=failure)** — CodeRabbit rate-limited + Bugbot usage-limited (vendor throttle, not code issue)
3. **GATE-3 (CR=FAIL)** — CodeRabbit 95th-percentile rate-limit (vendor throttle)
4. **GATE-6 (evidence link)** — body had no `.mp4|.gif|.cast|.png|gist.github.com|user-attachments` URL
5. **GATE-6b (PR description gate)** — `## Non-Unit Test Evidence` and `## Evidence` lacked URL anchors and fenced code blocks; 8 sections present but conditional_violations fired

Plus the **user's mid-session steer**: "merge approved once /green and if only prompt or test changes" — which excludes this PR (5 production files), so even after all the gates cleared, the explicit condition blocks auto-merge.

## Gate matrix as resolved (after 3 empty commits)

| Gate | Pre-fix | Post-fix (3 empty commits) | Notes |
|---|---|---|---|
| GATE-0 Design Doc Grep | FAIL | PASS | After empty commit `cf74e8db55`; needed `## Tenets (or ## Design Decision)` + `world_reference/aizen_god_mechanics.md` reference |
| GATE-1 CI green | FAIL | FAIL | CodeRabbit rate-limited + Bugbot usage-limited (vendor throttle) |
| GATE-2 no merge conflicts | PASS | PASS | — |
| GATE-3 CodeRabbit APPROVED | FAIL | FAIL | CodeRabbit 95th-percentile rate-limit; review ETA ~51min; both `@coderabbitai full review` AND `@coderabbitai summary` return ack comment without `state=success` commit status under throttle (drive-pr-to-green v2.5.7 trap) |
| GATE-5 comments resolved | PASS | PASS | — |
| GATE-6 evidence link | FAIL | PASS | After body edit adding `https://gist.github.com/jleechan2015/5d9a7c76ac5b9bee19a8aa550dabf96e` |
| GATE-6b PR description gate | FAIL | PASS | All 8 sections present, anchors satisfied |
| GATE-7 Skeptic | not run | not run | doc-only / content-only not the case here |

**Net: 5/7 green after the body+anchor work. GATE-1 + GATE-3 remained red from vendor throttles.**

## Branch protection state (verified at PR #8485 push time)

```bash
gh api repos/$GITHUB_REPOSITORY/branches/main/protection \
  --jq '{required_status_checks_contexts: .required_status_checks.contexts,
         required_approving_review_count: .required_pull_request_reviews.required_approving_review_count,
         enforce_admins: .enforce_admins.enabled}'
# { "required_status_checks_contexts": [], "required_approving_review_count": 0, "enforce_admins": false }
```

**Branch protection is empty — `gh pr merge --merge` would succeed regardless of Green Gate Precheck failure.** But the user's mid-session steer conditioned merge on `/green AND only prompt/test changes`, which excludes this PR. The merge was held despite branch protection allowing it.

## The Gate-0 anchor that worked (PR body excerpt)

```markdown
## Tenets (or Design Decision)

The disable is the safe prelude to the god-mechanics redesign. Original spec: `world_reference/aizen_god_mechanics.md` (11K, 161 lines). Bead: `$USER-d8lo`. Design intent: PR #1 of 2 — this disable unblocks the redesign PR #2 (post-`/superpowers brainstorm`).
```

Verified: the Gate 0 grep script in `design-doc-gate.yml` accepts either:
- `## Tenets` OR `## Design Decision` header, OR
- A reference to a file under `world_reference/` (or `docs/`, `.beads/issues.jsonl`)

**Key gotcha:** the linked file MUST exist on disk at the cited path. PR #8485 had `world_reference/aizen_god_mechanics.md` already on disk (verified with `ls` and `wc -l` before pushing the body update).

## The Gate-0 retrigger gotcha (key learning for this PR)

`design-doc-gate.yml` only fires on `pull_request: [opened, ready_for_review, synchronize, reopened]` — **NOT `edited`**. So `gh pr edit --body-file ...` does NOT re-trigger Gate 0.

**Working recipe:**
```bash
# Body edit alone won't re-trigger Gate 0
gh pr edit 8485 --repo $GITHUB_REPOSITORY --body-file /tmp/body.md

# Need synchronize event:
git -c user.email=jleechan2015@users.noreply.github.com \
    -c user.name=jleechan2015 \
    commit --allow-empty \
    -m "ci: refresh green gates after Gate-0 anchor fix"
git push origin HEAD:refs/heads/feat/multiverse-disabled
```

Each cycle costs ~2-3 minutes on worldai's self-hosted runner pool.

## Evidence-link heuristic patterns (GATE-6)

Verified by the gate log on PR #8485 run `29794371153`:

```bash
# Patterns that satisfy GATE-6 evidence heuristic:
# - .mp4|.gif|.webm|.cast|.png|.jpg|.jpeg|.webp
# - loom.com/share/...
# - asciinema.org/a/...
# - youtu.be or youtube.com URLs
# - gist.github.com/<user>/<id>
# - github.com/<owner>/<repo>/gist/...
# - user-attachments.githubusercontent.com

# Patterns that DON'T satisfy GATE-6:
# - github.com/.../pull/<N> (PR link — common mistake)
# - github.com/.../commit/<sha> (commit link)
# - Plain prose mentioning a URL
```

For PR #8485: `https://gist.github.com/jleechan2015/5d9a7c76ac5b9bee19a8aa550dabf96e` was the accepted pattern. Created via `POST https://api.github.com/gists` with `public: true` + `files: {README.md: ..., probe.log: ...}`. **NOT** `gh gist create` (which stores binary as utf-8 text per env-preferences.mdc).

## The user's mid-session steer that changed the merge decision

> "merge approved once /green and if only prompt or test changes"

This is **conditional approval**, not unconditional. Two conditions, both required:
1. /green achieved (7-green eligible, all gate checks pass)
2. Only prompt or test changes in the PR diff

PR #8485 fails condition (2): 5 production code files (`$PROJECT_ROOT/agent_prompts.py`, `$PROJECT_ROOT/agents.py`, `$PROJECT_ROOT/campaign_divine.py`, `$PROJECT_ROOT/campaign_upgrade.py`, `$PROJECT_ROOT/constants.py`). Even after /green was achieved on the structural gates (0, 2, 5, 6, 6b), condition (2) blocks auto-merge.

**Lesson:** when a user says "merge approved" with a condition, the condition is binding. Don't merge if the condition fails — even when branch protection allows it. Report the state honestly and wait for explicit override.

## What the agent did vs. what the user wanted

The user said "merge approved once /green AND only prompt/test changes". The agent did NOT merge (correct — condition 2 failed). What was reported:
- Gate-by-gate status (4/7 green, 2 vendor throttles, 1 user-conditioned)
- The disable-probe gist URL
- The Tenets anchor that satisfied Gate 0
- The empty-commit re-trigger pattern needed for Gate 0
- Honest acknowledgment that the user's condition excludes this PR

## Pitfalls observed in this session

1. **`world_reference/` exists in TWO roles** — (a) as docs-only exemption for content-only PRs (v1.6.0), (b) as Gate-0 design-doc anchor for production-code PRs. The skill now documents both.
2. **Gate 0 doesn't fire on `edited`** — body-only edits don't trigger the workflow. Need empty commit for `synchronize` event. Same trap as v2.5.6 (workflow_dispatch on `ref=main`).
3. **5/7 green is not /green** — even though GATE-2 / GATE-5 / GATE-6 / GATE-6b / GATE-0 all passed (the structural gates), GATE-1 and GATE-3 stuck on vendor rate-limits. Skeptic (GATE-7) wasn't even run.
4. **User's merge condition is binding** — "merge approved if only prompt/test" excludes PRs with production code diffs, even when branch protection allows direct merge.
5. **Local validator catches all 8 sections + anchors in 1 second** — running `python3 .github/scripts/pr_description_gate.py --body-file ...` before pushing saves 2-3 CI cycles (6-9 min) per push.
