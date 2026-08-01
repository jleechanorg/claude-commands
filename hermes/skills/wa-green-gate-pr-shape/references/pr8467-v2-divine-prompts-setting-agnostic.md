# PR #8467 v2 — Divine prompts setting-agnostic regression + PR-already-merged early-exit

**Date:** 2026-07-21
**PR:** [#8467](https://github.com/$GITHUB_REPOSITORY/pull/8467) — `fix(prompts): hide dissonance, remove apex attention, track per god/faction`
**Branch:** `feat/divine-faction-dissonance-hidden`
**Final state:** MERGED at `a659905baa` by `jleechan2015` at 2026-07-21T02:11:18Z

## What this session demonstrates

Two distinct things went wrong, and both are now captured in the parent SKILL.md as new sections:

1. **Setting-agnostic invariant regression** — the original PR (`0314a434e4`) introduced D&D entity leaks (`Oghma`, `Forgotten Realms`, standalone `Ao`) into the default-text portion of `divine_leverage_system.md` AND dropped the `[DIVINE HUD ... ACTIVE OBSERVERS: ...]` block from the HUD template as part of the "remove apex attention" refactor. The test `test_divine_prompts_setting_agnostic.py` caught all three on `Directory tests (core-mvp-2)`.

2. **PR-already-merged polling loop** — after pushing the fix commit (`9f6fbc9bd6`), the session got stuck in an empty-commit-retrigger loop because Green Gate Precheck kept reporting `GATE-1 FAIL: CI=failure` during a transition window. The user (`jleechan2015`) merged the PR at 02:11:18Z while I was polling; I pushed two more empty commits (`ba9b69091b`, `e3df733ce3`) onto a now-merged PR head before noticing.

## Fix commit `9f6fbc9bd6` — diff (5 insertions, 3 deletions, 1 file)

```diff
--- a/$PROJECT_ROOT/prompts/divine/divine_leverage_system.md
+++ b/$PROJECT_ROOT/prompts/divine/divine_leverage_system.md
@@ -236,1 +236,1 @@
-`faction_dissonance` is a map keyed by faction id (use the campaign's own deity/divine-cast names; for D&D Forgotten Realms see Appendix A.3). Initialize as `{}` and add faction ids as the player interacts with or interferes with them:
+`faction_dissonance` is a map keyed by faction id (use the campaign's own deity/divine-cast names; the Appendix A.3 mapping is for reference only when the campaign is D&D). Initialize as `{}` and add faction ids as the player interacts with or interferes with them:

@@ -287,1 +287,1 @@
-The previously-separate "Apex Attention" / "Apex Predator" mechanic has been **removed**. Apex-tier intervention is now handled by whichever faction reaches 100% first — including the campaign's supreme authority (e.g. Ao in D&D Forgotten Realms), which can be a faction in `faction_dissonance` like any other and triggers its own intervention at 100%.
+The previously-separate "Apex Attention" / "Apex Predator" mechanic has been **removed**. Apex-tier intervention is now handled by whichever faction reaches 100% first — including the campaign's supreme authority (the top-tier cosmic entity), which can be a faction in `faction_dissonance` like any other and triggers its own intervention at 100%.

@@ -434,6 +434,7 @@
 DISSONANCE: [Hidden] (per faction; player sees only Vibe Cue)
   > STATUS: [Safe/Suspicion/Investigation/Exposure] — applies to the highest faction
+  > ACTIVE OBSERVERS: [None / The Watchers / The Seers / etc.] (use the campaign's own divine cast)
   > VIBE: The air feels... [Still/Heavy/Charged/Screaming] (derived from max(faction_dissonance))

@@ -452,7 +452,8 @@
 DISSONANCE: [Hidden] (per faction; player sees only Vibe Cue)
-  > STATUS: Suspicion (Oghma's faction is the most suspicious)
+  > STATUS: Suspicion (the watch-god's faction is the most suspicious)
+  > ACTIVE OBSERVERS: The Watchers (passive scrying)
   > VIBE: The air feels... Heavy
```

## Exact test failure trace (from shard2 artifact)

`mvp-shard2-test-results/test_divine_prompts_setting_agnostic.py.513970e7.log`:

```
FAIL: test_hud_observers_are_generic
AssertionError: unexpectedly None : Could not find the '[DIVINE HUD ... ACTIVE OBSERVERS: ...]' block in the default text.

FAIL: test_no_ao_in_default_text
AssertionError: <re.Match object; span=(19490, 19492), match='Ao'> is not None : 'Ao' (as a standalone entity) leaked into default text of divine_leverage_system.md.

FAIL: test_no_dnd_default_entities
AssertionError: Lists differ: ['Oghma', 'Forgotten Realms'] != []
```

`mvp-shard2-test-results.zip` is the standard artifact for `Directory tests (core-mvp-2)` self-hosted runs. Each failed test has a per-test log with the failure trace + assertion context.

## Setting-agnostic contract (recap)

The test reads `divine_leverage_system.md`, splits at the literal marker `# Appendix A: D&D Forgotten Realms Adaptation Appendix`, and asserts the **default-text portion** (everything above the marker) contains zero D&D entity references. Specifically:

- **Forbidden in default text:** `Mystra`, `Helm`, `Oghma`, `Savras`, `Torm`, `Shar`, `Karsus`, `Mystryl`, `Netheril`, `Forgotten Realms`, `the Weave`, standalone `Ao`, `Dale Reckoning`, `Netherese`
- **Required in default text:** `Overseer` placeholder, `source-fabric` placeholder
- **Required block:** `[DIVINE HUD ... ACTIVE OBSERVERS: ...]` line with generic placeholders

The `divine_ascension_ceremony.md` prompt has no appendix marker, so its `_default_text` is the entire file (and it must also avoid D&D entities outside `(D&D ...)` callout blocks).

## PR-already-merged timing log

| Time (UTC) | Event | What I did | What I should have done |
|---|---|---|---|
| 02:03:37Z | First push (fix `9f6fbc9bd6`) | `git push origin HEAD` | ✅ correct |
| 02:04:54Z | GATE-1 FAIL: CI=failure (precheck ran while tests pending) | Waited 60s | ✅ correct |
| 02:08:30Z | core-mvp-{1,2,3} all PASS | Polled `gh pr checks` | ✅ correct |
| 02:11:18Z | **PR #8467 merged by jleechan2015** | (I didn't notice) | **should have run `gh pr view 8467 --json state` and stopped** |
| 02:11:30Z | Green Gate Precheck still showing stale failure | Pushed empty commit `ba9b69091b` | ❌ wasted push — PR was already MERGED |
| 02:13:54Z | Pushed another empty commit `e3df733ce3` | ❌ second wasted push |
| 02:18:44Z | Discovered PR state=MERGED via `gh pr view` | Stopped polling, verified fix in origin/main | ✅ recovery, but 2 commits too late |

**Heuristic for next time:** if the gate has been red for >5 minutes AND `gh pr checks` shows all real CI green AND no new commits have landed on the PR branch since your last push, **run `gh pr view <N> --json state` BEFORE pushing another empty commit**. If state=MERGED, you're done — verify the merge commit is in `origin/main` and report success.

## Verification recipe (post-merge)

```bash
# 1. Confirm PR state
gh pr view 8467 --repo $GITHUB_REPOSITORY --json state,mergedAt,mergedBy,mergeCommit
# Expect: state=MERGED, mergedBy.login=jleechan2015

# 2. Confirm fix commit is reachable from origin/main
git -C ~/.worktrees/<branch> fetch origin
git -C ~/.worktrees/<branch> merge-base --is-ancestor <fix-commit-sha> origin/main
# Expect: exit 0

# 3. Run the invariant test against origin/main's prompt file
cd ~/.worktrees/<branch>
python3 -m unittest mvp_site.tests.test_divine_prompts_setting_agnostic
# Expect: exit 0, 19/19 pass

# 4. Spot-check the merged prompt file
git -C ~/.worktrees/<branch> show origin/main:$PROJECT_ROOT/prompts/divine/divine_leverage_system.md \
  | grep -E 'ACTIVE OBSERVERS|Overseer|source-fabric'
# Expect: all three present in default-text
```

## Key commits on origin/main after the merge

```
a659905baa Merge pull request #8467 from jleechanorg/feat/divine-faction-dissonance-hidden
ba9b69091b ci: re-trigger green gate after CI green              ← wasted empty commit
9f6fbc9bd6 fix(prompts): restore setting-agnostic HUD block + remove D&D leaks  ← the real fix
2699507432 (origin of original branch)
ec74ca2dda fix(prompts): hide dissonance, remove apex attention, track per god/faction
0314a434e4 fix(prompts): align threshold bands + clarify Ao + dedupe Exposure label
```

The two empty-commit pushes (`ba9b69091b`, `e3df733ce3`) are now historical noise in the merge commit's ancestry — harmless but unnecessary. The lesson encoded in `wa-green-gate-pr-shape` v1.8.0 prevents the next session from repeating this loop.

## Cross-references

- Parent skill: `wa-green-gate-pr-shape` SKILL.md (sections "PR already merged early-exit check" + "Setting-agnostic invariant regression")
- Sibling case (PR #8467 v1, same day earlier): the GATE-6b "5 missing sections" pre-amble anti-pattern in the same skill — different failure mode, same PR
- Sibling case (PR #8485): Gate-0 Tenets anchor requirement + the user's mid-session "merge approved if only prompt/test" conditional
- Test contract source: `$PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py`
- Backing contract: `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` Appendix A marker line