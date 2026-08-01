# Merge-conflict treadmill + race-with-AO-worker — PR #8292 incident

**Date:** 2026-07-23
**Affected PR:** [$GITHUB_REPOSITORY#8292](https://github.com/$GITHUB_REPOSITORY/pull/8292)
**Branch:** `feat/provenance-narrow`
**Initial state:** `mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`, `addb6147f1..ca86adc95b` (89 commits behind `origin/main`)
**Final state:** `mergeable: MERGEABLE`, `headRefOid: dc5fb638165200cf37c5ed1ab9e17b16608e200e` (race landed)

## TL;DR

Resolving the conflict was the easy part. The hard part was (1) accepting that the PR would re-dirty within minutes, and (2) discovering that an automated AO worker using my `jleechan2015` credentials had already pushed the same conflict resolution while I was preparing mine. Both failure modes have recipes now; this reference is the deep-dive.

## Part 1 — The merge-conflict treadmill

### Why it happened

PR #8292 had been open for ~5 days. During that time, `origin/main` advanced from `7fe41fda80` (PR base) to `b58d9142fb` (current main HEAD at the time of my second merge). That's **84+ new commits on main** while the PR was untouched. The PR's branch had 5 prior merge commits pulling in main at older states, but those states were themselves 30+ commits behind the new main.

### Symptom (round 1)

```
$ git fetch origin --quiet
$ git -C /tmp/wa-8292-merge merge --no-ff origin/feat/provenance-narrow
Updating files: 100% (7146/7146), done.
HEAD is now at 44561c26b0 Merge pull request #8050 from jleechanorg/codex/cache-utilization-harness-8046
Auto-merging $PROJECT_ROOT/prompts/game_state_instruction.md
CONFLICT (content): Merge conflict in .github/workflows/design-doc-gate.yml
```

**Result:** 1 conflict in `.github/workflows/design-doc-gate.yml` (info comment collision). Everything else auto-merged cleanly. I resolved it with a `12000 → 12050` line-count ratchet bump and pushed.

### Symptom (round 2, after 8 min CI wait)

```
$ git ls-remote origin feat/provenance-narrow
dc5fb638165200cf37c5ed1ab9e17b16608e200e    refs/heads/feat/provenance-narrow
$ gh pr view 8292 ... --json mergeStateStatus,mergeable
{"mergeable":"CONFLICTING","mergeStateStatus":"DIRTY"}
```

While I waited for CI, `origin/main` advanced another 67 commits (10+ new merge commits). The PR was dirty again. I started round 2:

```
$ git -C /tmp/wa-8292-merge reset --hard origin/main --quiet  # HEAD now b58d9142fb
$ git merge --no-ff origin/feat/provenance-narrow
Auto-merging .github/workflows/evidence-gate.yml
Auto-merging $PROJECT_ROOT/llm_service.py
CONFLICT (content): Merge conflict in $PROJECT_ROOT/llm_service.py
Auto-merging $PROJECT_ROOT/prompts/game_state_instruction.md
Auto-merging $PROJECT_ROOT/schemas/prompt_tool_contracts.json
CONFLICT (content): Merge conflict in $PROJECT_ROOT/schemas/prompt_tool_contracts.json
Auto-merging $PROJECT_ROOT/tests/test_llm_service_context.py
CONFLICT (content): Merge conflict in $PROJECT_ROOT/tests/test_llm_service_context.py
```

**Result:** 3 new conflicts (vs 1 in round 1). All in `$PROJECT_ROOT/*` files because main touched them during the 8-min CI wait. Resolved them all, prepared the merge commit, ran tests locally — then noticed `dc5fb6381652` already on the remote.

## Part 2 — The race-with-AO-worker

### The smoking gun

```
$ git log -1 origin/feat/provenance-narrow --pretty=format:"%H %an %ae %s"
dc5fb638165200cf37c5ed1ab9e17b16608e200e jleechan2015 jleechan2015@users.noreply.github.com
   merge: PR #8292 — re-merge origin/main (r2) to clear Gate 2

$ git show --stat origin/feat/provenance-narrow | head -10
commit dc5fb638165200cf37c5ed1ab9e17b16608e200e
Merge: 51c9c0e806 b58d9142fb
Author: jleechan2015 <jleechan2015@users.noreply.github.com>
Date:   Thu Jul 23 15:52:39 2026 -0700

    merge: PR #8292 — re-merge origin/main (r2) to clear Gate 2
```

Same `jleechan2015` credentials I was using. Different actor. The AO worker / babysit cron / drive loop raced me to the same resolution (helper-function refactor + `core_memories` strip + auto-merged hash).

### Why I let it stand (vs. pushing my own)

The AO worker's commit `dc5fb6381652` had:
- ✅ All 3 round-2 conflicts resolved identically to my planned resolution
- ✅ Helper-function refactor in `$PROJECT_ROOT/llm_service.py` (matches my plan)
- ✅ `core_memories` strip inside `_strip_llm_campaign_redundancies` (matches my plan)
- ✅ Auto-merged hash for `game_state_instruction.md` (matches my plan)
- ✅ Detailed docstring in test file (matches my plan)

Pushing my competing commit would have:
- Forced a `git push --force-with-lease` that **rejected** as non-FF (because AO worker's commit was not my ancestor)
- OR worse: my push overwriting AO worker's correct commit with my identical-but-non-bit-exact version, losing the AO worker's git provenance chain

Per `push-pr-donot-stop-halfway`, the deliverable is durable state on the remote. **Durable state already exists.** Pushing a competing commit gains nothing and risks losing real work. I let AO's commit stand and deleted my local `feat/provenance-narrow-merge` branch + prunable worktree.

### The missed guard recipe

What I should have done at minute 1 (before starting round 2):

```bash
LOCAL_HEAD=$(git -C <worktree> rev-parse HEAD)  # 51c9c0e806 (round 1)
REMOTE_HEAD=$(git ls-remote origin feat/provenance-narrow | awk '{print $1}')  # ALSO 51c9c0e806 at this point
# Match — proceed normally

# After CI wait, BEFORE preparing round 2:
git ls-remote origin feat/provenance-narrow  # would have returned dc5fb6381652 (AO already pushed)
# If AO already pushed → STOP, check their resolution, let it stand if equivalent
```

## Part 3 — Evidence Gate freshness vs post-merge-main

### Why it failed (same PR #8292)

The PR body references the wave-2 fix gist `4d82e3802745b59b2b5b21d08ae908bc`. That gist's `metadata.json.git_provenance.git_head` is `d5d7254607` (the wave-2 fix commit). The PR's current HEAD (after AO's merge) is `dc5fb6381652`. The gate does:

```bash
CHANGED=$(git diff --name-only "$EVIDENCE_SHA" "$HEAD_SHA" -- .)
```

`git diff d5d7254607 dc5fb6381652 -- .` returns **80+ changed files** — all of main's behavioral changes since `d5d7254607` landed. Most are filtered out by `EVIDENCE_DOC_POLICY_RE` etc., but the `EVIDENCE_MVP_PRODUCTION_RE = ^$PROJECT_ROOT/` filter catches every `$PROJECT_ROOT/*.py` main touched. Stale.

**Pre-existing issue (NOT caused by my merge):** The wave-2 gist was already stale at `addb6147f1` (the prior PR head) — `d5d7254607` → `addb6147f1` = 16+ commits behind. The PR body's evidence claim ("git_provenance matches this update's HEAD exactly") was already self-inconsistent before any of my work. My merge simply widened the gap from 16 commits to ~80 commits.

### Three valid responses (verified PR #8292 chose option 3)

| Option | Action | Cost | Use when |
|---|---|---|---|
| 1 | Re-capture `/es` at `dc5fb6381652` | ~15min real LLM execution | Production readiness is paramount; PR is otherwise ready to merge |
| 2 | Label wave-N gist `(historical)` in PR body | 5-line edit | Wave-N scope is genuinely unchanged at current head; gap is only freshness window |
| 3 | Document and accept the gate failure | 0 lines | `/er` is already BLOCKED on a separate bead (`rev-cwq21` for PR #8292); Evidence Gate failure is consistent with that disclosure |

PR #8292 chose option 3 — the PR body already disclosed `/er` BLOCKED on `rev-cwq21` independently, so the Evidence Gate failure on freshness is consistent with that, not a new failure.

## Part 4 — Prompt contract hash on merge conflict

### When both sides modified the same `.md` prompt

`$PROJECT_ROOT/schemas/prompt_tool_contracts.json` has a `version` field = first 12 chars of the prompt file's SHA-256, plus a full `sha256` field. When both sides modified the same prompt (PR added "Identity Provenance Policy" section, main added "Reconcile Core Memories" section), the merge produces a content-hash conflict:

```json
<<<<<<< HEAD
"version": "583051ce016c",  // = sha256[:12] of main's version
"sha256": "583051ce016c6166...",
||||||| ca86adc95b
"version": "478405646beb",
"sha256": "478405646beb...",
=======
"version": "043a2f8eb83e",  // = sha256[:12] of PR's version
"sha256": "043a2f8eb83e...",
>>>>>>> origin/feat/provenance-narrow
```

**Neither pre-merge hash matches the merged file.** Resolution: take the auto-merged file's actual SHA-256.

```bash
$ sha256sum $PROJECT_ROOT/prompts/game_state_instruction.md
be7bc959b197bd9d3e820fbb3293d2718b50d3df5da3cab30867c017a1400f55

$ python3 -c "import json; m=json.load(open('$PROJECT_ROOT/schemas/prompt_tool_contracts.json')); ..."  # patch in new sha256
```

This applies to ANY prompt contract hash conflict (the worldai skill encodes this in `$PROJECT_ROOT/prompts/*.md` + `$PROJECT_ROOT/schemas/prompt_tool_contracts.json`). After every merge that touches a prompt, verify the contracts file's hashes match the actual prompt bytes — both before AND after the merge.

## Part 5 — Helper-function structural merge

### `$PROJECT_ROOT/llm_service.py::_strip_llm_redundancies`

This is the canonical "structural vs inline" conflict. Main had:

```python
wd = state_dict.get("world_data")
if isinstance(wd, dict):
    wd_copy = dict(wd)
    # ... inline location normalization
state_dict["world_data"] = wd_copy

ccs = state_dict.get("custom_campaign_state")
if isinstance(ccs, dict):
    ccs_copy = dict(ccs)
    ccs_copy.pop("last_location", None)
    # ... 3 pops + core_memories strip (main's da683e6515 fix)
```

PR refactored to helper-function calls:

```python
if "world_data" in state_dict:
    state_dict["world_data"] = _normalize_llm_world_data(state_dict["world_data"])
if "player_character_data" in state_dict:
    state_dict["player_character_data"] = _strip_llm_parentage_cache_markers(...)
if "custom_campaign_state" in state_dict:
    state_dict["custom_campaign_state"] = _strip_llm_campaign_redundancies(...)
```

**Resolution pattern:** Keep the PR's structural helper-based version (the helpers exist in the PR's tree, auto-merged above the conflict). Add the MISSING behavioral pieces from HEAD (in this case, the `core_memories` strip inside `_strip_llm_campaign_redundancies`) to the PR's helper. This gives you BOTH:
- The PR's cleaner structure + extra parentage stripping (PR's net-new value)
- Main's `core_memories` strip that prevents the gpt-5 nested core-memory budget bypass (main's net-new value)

**Anti-pattern:** Choosing one side verbatim and losing the other side's behavior. The PR's tree predates main's `core_memories` fix; main's tree predates the PR's structural refactor. Picking either verbatim loses the merge's intent.

## Pitfalls (BANNED)

1. **Banned — `git push origin HEAD:refs/heads/<branch> --force-with-lease` without first checking the remote tip.** Verified wasted 5min: an AO worker had already pushed an equivalent resolution; my push would have either failed as non-FF or clobbered their work. Always `git ls-remote origin <branch>` first.

2. **Banned — Assuming your CI wait is benign.** If you start a merge-main resolution and then poll for 5+ minutes for CI results, `origin/main` may have moved and your prepared resolution is stale. Re-fetch and re-verify before push.

3. **Banned — Picking one side of a structural-vs-inline merge verbatim.** The PR's tree and main's tree each have unique value. Structural-vs-inline conflicts require preserving both. Add main's missing behavioral changes to the PR's helper functions (or vice versa).

4. **Banned — Re-running `/es` capture to "fix" an Evidence Gate freshness failure caused by a merge-main resolution.** The freshness check is SHA-based, not behavioral. New merged HEAD = new required capture. The fix is structural (re-capture, label historical, or accept), not behavioral.

5. **Banned — Labeling a gist `(historical)` when the wave-N scope has actually drifted since capture.** Verify the wave-N scope is unchanged at the current head before relabeling. If the wave-N code paths have changed since capture, `(historical)` becomes fabrication.

6. **Banned — Treating the Evidence Gate's `git diff --name-only $EVIDENCE_SHA $HEAD_SHA -- .` as a PR-diff check.** It's a full-repo diff. Main's behavioral changes count even when the PR did not touch them. Always decompose: which files did the PR change vs which files did main change. Only the PR's changes are evidence-bearing.

## Recovery recipe — when the AO worker raced you

```bash
# 1. Confirm AO's resolution is equivalent (not regressing)
git diff <your-prepared-commit> origin/<branch> --stat
git diff <your-prepared-commit> origin/<branch> -- <conflict-files>

# 2a. If equivalent or better: let AO's commit stand. Delete your local branch + worktree.
git worktree remove <your-worktree> --force
git worktree prune
git branch -D <your-local-branch>

# 2b. If AO's resolution regresses something: cherry-pick ONLY the missing fix
git -C <shared-worktree> fetch origin --quiet
git -C <shared-worktree> checkout origin/<branch>
git -C <shared-worktree> cherry-pick <single-fix-sha>  # do NOT merge
git -C <shared-worktree> push origin HEAD:refs/heads/<branch>  # fast-forward OK
```

## See also

- `~/.hermes/skills/workflow/drive-pr-to-green/SKILL.md` — v2.5.10 overlay (this addendum's parent)
- `~/.hermes/skills/github/patch-port-protocol/SKILL.md` — Phase 1c multi-canonical-repo discovery
- `~/.hermes/skills/finish-the-job/SKILL.md` — end-state contract for drive loops
- `references/evidence-gate-freshness-contract-2026-07-13.md` — PR #8380 evidence-gate deep dive (Check 6/7 mechanics)
- `~/.hermes/SOUL.md` — `push-pr-donot-stop-halfway`, `never-push-onto-someone-elses-pr-head`, `pr-clean-branch-from-main-no-history-bloat` commitments
