# PR #8564 — Divine prompt compaction (verified case)

Full transcript of the compaction recipe that produced PR
[#8564](https://github.com/$GITHUB_REPOSITORY/pull/8564) on 2026-07-24.
This is the canonical example for `prompt-compaction-safe`. The recipe is
described in SKILL.md; this file shows the exact sequence applied.

## Input

- **Repo:** `$GITHUB_REPOSITORY`
- **Targets:**
  - `$PROJECT_ROOT/prompts/divine/divine_leverage_system.md` (1023 lines, 64228 bytes)
  - `$PROJECT_ROOT/prompts/divine/divine_ascension_ceremony.md` (282 lines, 11764 bytes)
- **Contract test:** `$PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py`
  (1098 lines, 53 tests)
- **Broader tests:** `$PROJECT_ROOT/tests/test_agents.py` (332 tests, 7 of which
  are divine-related and pin `divine_leverage_system.md` filename inclusion)

## Pre-flight: worktree from `origin/main`

```bash
cd $HOME/repos/$GITHUB_REPOSITORY
git fetch origin
git worktree add -b feat/compact-divine-prompts /tmp/wa-compact-divine origin/main
# Verify clean: HEAD at origin/main HEAD (530f34e9cb), no extra commits
git -C /tmp/wa-compact-divine log --oneline origin/main..HEAD   # MUST be empty
```

Why a separate worktree (not the main checkout): the main checkout was on
branch `fix/cron-exit-semantics-and-oom-watchdog` with divergent commits
(unmerged paths in `.claude/commands/code-standards.md`). Per
`pr-clean-branch-from-main.mdc` and `never-push-onto-someone-elses-pr-head`
the PR must branch from `origin/main`, not from a divergent local branch.

## Phase 0 — Find the contract test file

```bash
# Discovered in 1 step:
grep -rln "divine_leverage_system" $PROJECT_ROOT/tests/ --include="*.py"
# → $PROJECT_ROOT/game_state.py (just a comment ref)
# → $PROJECT_ROOT/constants.py (DIVINE_SYSTEM_PATH const ref)
# → $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py (the contract test)
# → $PROJECT_ROOT/tests/test_agents.py (agent-loader test, pins the filename)
```

Two test files surface. The contract test is `test_divine_prompts_setting_agnostic.py`;
`test_agents.py` is the broader surface that pins filename inclusion.

## Phase 1 — Anchor inventory

Reading the contract test in full (1098 lines, 5 chunks of 350 lines each)
revealed these anchor categories:

### Hard anchors (verbatim strings)

- `stat_divine(L, F, Repr) = stat_mortal × tier_multiplier(L) + bonus_f(F, L) + bonus_repr(Repr, L)`
- `bonus_f(F, L) = stat_floor(L) × (F / 1,000,000) × 0.25`
- `DAC(L) = clamp(mortal_AC + Divine_Rank_Bonus(L), 18, 50)`
- `(L − 19) × 10 + 100`
- `DPP does NOT carry across dawns`
- `setting_agnostic`, `Overseer`, `source-fabric`
- All 10 XP milestones: 501050, 536758, 577822, 625045, 679352, 741805, 1226048, 2200031, 4159058, 8099360
- HUD example: `XP: 1,536,630/1,727,674`

### Verbatim table rows

- `| DHP | 138 | 745 |` (V3.2 worked example)
- `| DAIR | +5 | 27 |` (V3.2 worked example)
- `| **Celestial Coup** | 400 |` (V3.13 AT-3 menu)
- `| **Cleansing Strike** | 300 |` (V3.13 AT-3 menu)
- `| **Deicide** | 400 |` (V3.13 AT-3 menu)
- `| **Intermediate God** | 36-40 |` (V3.1 tier ladder)
- `| **DPP** | Divine Power Pool / day | 110-410 |` (V3.0 vocabulary)
- `| **AT-3 Legendary** | 100-400 |` (V3.0 vocabulary)
- `| **Tyrant** | Smite a heretic |` (V3.18 archetype)

### Numbered tokens with regex (word-order-sensitive)

- `(\d+) DPP` — for §V3.13 cost ceiling test
- `Celestial Coup to seize…DPP 400` (V3.20 example)
- `Cleansing Strike on all temples…DPP 300` (V3.20 example)

### Section-spanning regexes (preserve section hierarchy)

- `r"## V3\.13 [^\n]*\n(.*?)(?=\n## V3\.14|\Z)"` — captures §V3.13 body up to §V3.14
- `r"## V3\.2 [^\n]*\n(.*?)(?=\n## |\Z)"` — captures §V3.2 body up to next ##
- `r"## V3\.20[^\n]*\n(.*?)(?=\n## |\Z)"` — captures §V3.20 body

### Forbidden-entity regexes (must NOT appear in default text)

- `Mystra`, `Helm`, `Oghma`, `Savras`, `Torm`, `Shar`, `Karsus`, `Mystryl`,
  `Netheril`, `Forgotten Realms`, `the Weave`, `Loki`, `Vecna`, `Chauntea`,
  `Demeter`, `Hoder`, `Osiris`, `Iuz`, `Nocturne`, `Aizen`, `Sōsuke`, `Drow`,
  `Arachne`
- `\bAo\b` (regex word-boundary)
- `Dale Reckoning`, `Netherese`

### APPENDIX_MARKER (must remain as section delimiter)

- `# Appendix A: D&D Forgotten Realms Adaptation Appendix` — splits "default
  text" (must avoid forbidden entities) from "appendix text" (allowed)

Saved the inventory to `/tmp/divine_anchor_inventory.md` for reference.

## Phase 2 — Prose headroom classification

Walked both files section by section:

| Section | Classification | Headroom |
|---|---|---|
| Setting Adaptation preamble (leverage L9-27) | Redundant prose (restated 3× in adjacent paragraphs) | **High** |
| Layer 0/1/2 (leverage L46-75) | Anchors (rule tables) + redundant Constraint/Risk bullets | **Medium** |
| Rule 0/1/2/3 (leverage L108-148) | Anchors + Rule 0's two bullet lists restating the same point | **Medium** |
| Automatic Dissonance subsection (leverage L170-174) | Pure pointer to Rule 2 (no anchors) | **High** (delete) |
| Orphan "Phase 1: Ascension" sentence (leverage L319) | Pure prose, no anchors, no parent section | **High** (delete) |
| Apex Predator subsection (leverage L287-289) | Short, but restates V3.14 cross-ref | **Medium** (compress to 1 sentence) |
| V3.13.1 Chosen prose (leverage L715-740) | Anchored (250 DPP, cap formula, DC 25 check) + narrative | **Medium** |
| V3.13.2 Avatar prose (leverage L744-771) | Anchored (400 DPP, cap formula) + narrative | **Medium** |
| V3.20 worked examples (leverage L891-952) | Required labels (F (LLM-only), narrative hint, DPP does NOT carry across dawns) + narrative | **Medium** |
| Ceremony Steps 1-8 (ceremony L31-208) | Anchor strings (V3 contract tokens) + redundant narrative fences duplicating leverage mechanics | **Very High** (32% reduction) |
| Ceremony State Updates JSON (ceremony L214-238) | Required (test pins `"mortal_sheet"`, `"divine_sheet"`) | Zero (untouchable) |

Highest headroom first: leverage preamble + ceremony Steps 1-8.

## Phase 3 — Compaction edits

### Pass A — leverage prompt preamble + sections

Edits applied:

1. Collapsed 3× Setting Adaptation preamble to one tight block (saved ~12 lines).
2. Inlined Layer 0/1/2 Constraint/Risk bullets into single sentences (saved ~9 lines).
3. Replaced Rule 0's two bullet lists with one paragraph (saved ~6 lines).
4. Deleted "Automatic Dissonance from Stat Overflow" subsection (saved ~4 lines).
5. Deleted orphan "Phase 1: Ascension (21-30)" sentence (saved ~1 line).
6. Compressed "Apex Predator" subsection to one sentence (saved ~3 lines).
7. Tightened V3.13.1/V3.13.2 prose (preserved `250 DPP` and `400 DPP` literally).
8. Compressed V3.20 worked examples (kept both, kept all required labels).

### Pass B — ceremony prompt

Edits applied:

1. Collapsed 8 narrative fences into short bullet headers + prose paragraphs.
2. Replaced duplicate V3 mechanics prose with cross-reference
   "see `divine_leverage_system.md` for the canonical formulas".
3. Preserved all required anchor strings (`(L − 19) × 10 + 100`,
   `Primary Divine Vessel`, `True Divine Form`, `"mortal_sheet"`,
   `"divine_sheet"`).

## Phase 4 — Mid-pass regression (the `250 DPP` → `DPP 250` incident)

After Pass A, ran the contract test:

```
$ pytest $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py
... 52 passed, 1 failed ...
FAILED test_v3_legendary_actions_fit_the_max_dawn_budget
AssertionError: [] is not true : Expected numeric DPP costs in §V3.13.
```

Root cause: Pass A's V3.13.1 rewrite read:

```diff
-**Creation cost:** 250 DPP (one-time, AT-3 Legendary Action); DHP binding …
+**Creation cost:** DPP 250 (one-time, AT-3 Legendary Action); DHP binding …
```

The test regex is `r"(?:\*\*)?(\d+) DPP"` — digit, then space, then literal
"DPP". My rewrite swapped to "DPP 250" (word then digit). The regex returned
no matches in the §V3.13 span, and the test asserted `costs` was non-empty.

**Fix:** reverted the word order. Did not accept the prose ugliness — kept
"250 DPP" because the test demands it.

**Lesson:** word-order-sensitive regex anchors are the most-overlooked
constraint. The test message (`Expected numeric DPP costs in §V3.13`)
clearly identified the failure mode; without per-edit test verification,
this regression would have stacked on top of subsequent edits and made the
diagnosis harder.

## Phase 5 — Final verification

```bash
$ cd /tmp/wa-compact-divine
$ pytest $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py
============================== 53 passed in 0.09s ==============================

$ pytest $PROJECT_ROOT/tests/test_agents.py $PROJECT_ROOT/tests/test_divine_prompts_setting_agnostic.py
======================== 382 passed, 3 skipped in 1.89s ========================
```

Per-file reduction:

| File | Lines (before → after) | Bytes (before → after) |
|---|---|---|
| `divine_leverage_system.md` | 1023 → 894 (-12.6%) | 64228 → 62517 (-2.7%) |
| `divine_ascension_ceremony.md` | 282 → 192 (-31.9%) | 11764 → 9808 (-16.6%) |
| **Combined** | **1305 → 1086 (-16.8%)** | **75992 → 72325 (-4.8%)** |

## Phase 6 — Branch, commit, push, PR

```bash
cd /tmp/wa-compact-divine

# Verify clean worktree topology
git log --oneline origin/main..HEAD     # MUST show only the new commit
git status --short                       # MUST be empty after commit

# Path-scoped commit (do NOT git add -A)
git add $PROJECT_ROOT/prompts/divine/divine_leverage_system.md \
        $PROJECT_ROOT/prompts/divine/divine_ascension_ceremony.md
git diff --staged --stat                 # 2 files, +127 / -346

git config user.email "hermes@nous.local"
git config user.name "Hermes"
git commit -m "refactor(prompts): compact divine tier prompts without changing V3 contract

Compresses $PROJECT_ROOT/prompts/divine/divine_leverage_system.md (1023 -> 894 lines,
-12.6%) and $PROJECT_ROOT/prompts/divine/divine_ascension_ceremony.md (282 -> 192 lines,
-31.9%) for a combined reduction of 1305 -> 1086 lines (-16.8%) and 75992 -> 72325
bytes (-4.8%).

[... full audit trail in commit message ...]"

git push origin feat/compact-divine-prompts
# git secret guard scanned + approved; no real PR URL yet at this point

gh pr create --base main --head feat/compact-divine-prompts \
             --title "refactor(prompts): compact divine tier prompts without changing V3 contract" \
             --body "[... full PR body with anchor list + test counts ...]"
```

Final state: PR [#8564](https://github.com/$GITHUB_REPOSITORY/pull/8564)
opened with 2 files changed, +127 / -346.

## Recipe summary (use for any future prompt compaction)

1. Find the contract test (`grep -rln <prompt_filename> <repo>/tests/`).
2. Read the contract test in full; build the anchor inventory (verbatim
   strings, regex anchors, forbidden-entity lists, section hierarchy).
3. Walk the prompt section by section; classify each as
   anchor-only / dense-prose / redundant-prose / free-prose.
4. Apply prose-only edits in headroom order (highest first).
5. After every meaningful edit, run the contract test; revert on failure.
6. When the contract test is green, run the broader agent-loader tests.
7. Commit (path-scoped, never `git add -A`), push, open PR with full audit
   trail including the mid-pass regressions caught.