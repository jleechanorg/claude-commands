# PR #8548 — `$PROJECT_ROOT/prompts/injection/` extraction closing the path-filter loophole

**Session:** 2026-07-23
**Repo:** $GITHUB_REPOSITORY
**Original PR:** #8527 (companion-quest cadence mirror)
**Replay PR:** #8548 (clean replay with `.md` extraction)
**Commits:** `e883887` + `4350849` (cherry-picks from #8527) + `ea24a32` (refactor)
**Diff vs `origin/main cb88231d8d`:** 5 files / +401 / -1

## The trap

PR #8527 inlined a 16-line LLM-bound prompt block as a Python f-string inside
`build_living_world_instruction` ($PROJECT_ROOT/agent_prompts.py:2649-2673). The PR
body honestly filed `## Real LLM Evidence` as N/A — the validator's path-filter
("Prompt change (any $PROJECT_ROOT/prompts/** file)") didn't fire because the change
was in `.py`. Jeffrey flagged it:

> "Even if this PR doesnt change prompts/ it is injecting a prompt. Maybe we
> should move all the injectable prompts from inline code to
> $PROJECT_ROOT/prompts/injection/ ?"

## Diagnosis (before fix)

- 13 `build_*_instruction` methods in `$PROJECT_ROOT/agent_prompts.py` (lines
  1631-2743) return inline-string prompts concatenated into the served prompt.
- `read_file_cached` was already in use at 6+ sites in `agent_prompts.py` (the
  codebase's existing injection pattern — `shared/`, `divine/`, `multiverse/`
  subdirs were loaded this way).
- `$PROJECT_ROOT/prompts/injection/` subdir did NOT exist yet.
- `agent_prompts.PATH_MAP` ($PROJECT_ROOT/agent_prompts.py:97) is the registry that
  `test_all_prompt_files_are_registered_in_service` (test_prompts.py:241) walks
  to detect orphan files.

## Original PR #8527 — dirty branch

```
$ git diff --stat origin/main..HEAD
57 files changed, 1561 insertions(+), 5265 deletions(-)
```

Branched from a stale `origin/main` (pre-merge of #8478 Argella memory anchor
+ #8520 daemon guardrails) — the diff carries reverts of unrelated work. Per
SOUL.md `pr-clean-branch-from-main-no-history-bloat`, the branch needed replay.

## Clean replay recipe (Phase 1 Strategy A from `pr-cleanup-replay`)

```bash
# 1. Fresh worktree from origin/main
cd $HOME/projects/your-project.com
git worktree add -b fix/companion-quest-cadence-mirror-8526-clean \
  $HOME/projects/wt-companion-quests-8526-clean origin/main

# 2. Cherry-pick load-bearing commits
cd $HOME/projects/wt-companion-quests-8526-clean
git cherry-pick a19e5a8cf1  # cadence mirror
git cherry-pick f81ef7a573  # CR fix
# Both auto-merged cleanly into agent_prompts.py — no conflicts.

# 3. Add the injection extraction (single new commit)
# - Write $PROJECT_ROOT/prompts/injection/living_world_companion_cadence.md
# - Patch agent_prompts.py: replace f-string with read_file_cached + .format
# - Add constants: PROMPT_TYPE_LIVING_WORLD_COMPANION_CADENCE,
#                  INJECTION_PROMPTS_DIR, LIVING_WORLD_COMPANION_CADENCE_PATH
# - Register in PATH_MAP
# - Add to conditional_prompts in test_prompts.py
# - Add TestCompanionCadenceInjectionFileContract (4 cases) to existing test
git add <the 5 files>
git -c user.email=hermes@nousresearch.com -c user.name="Hermes Agent" \
  commit -m "refactor(prompts): extract cadence mirror to $PROJECT_ROOT/prompts/injection/"

# 4. Push + open PR (REST fallback covered gh pr create GraphQL rate-limit)
git push -u origin HEAD:refs/heads/fix/companion-quest-cadence-mirror-8526-clean
# (REST PR creation per gh-rate-limit-and-transient-failures v1.3.0)
```

## Diff composition

```
$PROJECT_ROOT/agent_prompts.py                          |  32 +-      (replace f-string with read_file_cached)
$PROJECT_ROOT/constants.py                              |  12 +       (new PROMPT_TYPE_* + paths)
$PROJECT_ROOT/prompts/injection/living_world_companion_cadence.md |   6 +  (NEW FILE — 879 bytes)
$PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py | 351 +  (12 original + 4 new contract)
$PROJECT_ROOT/tests/test_prompts.py                     |   1 +       (add to conditional_prompts set)
```

No dirty history, no reverts of unrelated work, no large refactors. Just the
load-bearing changes for the architectural extraction.

## Dynamic block byte-equivalence check

```python
# After the extraction, verify the rendered output is byte-equivalent:
from mvp_site.file_cache import clear_file_cache
from mvp_site.agent_prompts import PromptBuilder
from unittest.mock import MagicMock

clear_file_cache()
builder = PromptBuilder(game_state=None)
mock_gs = MagicMock()
mock_gs.last_living_world_turn = 0
mock_gs.check_living_world_trigger.return_value = (True, "test_force", None)
mock_gs.get_companion_arcs_summary.return_value = ""
mock_gs.custom_campaign_state = {"next_companion_arc_turn": 3, "companion_arcs": {}}
builder.game_state = mock_gs
out = builder.build_living_world_instruction(3)
# Expected: 1364 chars (vs 1361 in PR #8527; +3 from os.path.join indirection)
# All 9 marker strings present: COMPANION QUEST CADENCE, PER-TURN OBLIGATION,
# current_turn = 3, current_turn + 1, current_turn + 2, Turn 3: MANDATORY,
# next_companion_arc_turn, companion_arcs, NO {current_turn} (template substituted)
```

## Test outcomes

```
$PROJECT_ROOT/tests/test_living_world_companion_quest_cadence_8526.py: 16/16 pass
$PROJECT_ROOT/tests/test_prompts.py: 177/178 pass
  - 1 pre-existing failure: TestVictoryRippleProtocol::test_victory_ripple_protocol_present_in_narrative
  - Verified on origin/main HEAD cb88231d8d with my changes stashed
  - Per SOUL.md `## COMMIT: same-test-name-rule` — same-test-name verified
```

## What did NOT land in this PR (deliberate scope discipline)

1. The 12 other inline `build_*_instruction` methods (`build_companion_instruction`,
   `build_arc_completion_reminder`, etc.). Each gets its own follow-up PR using
   #8548's pattern as the template.
2. Broadening the `pr_description_gate.py` rule to detect Python f-string prompt
   injection. That requires a behavior change to the validator — separate PR.
3. Closing PR #8527 (still open with the 57-file / +1561 dirty diff). The
   correct sequence: #8548 merges first, then `gh pr close 8527 --delete-branch`.

## Why this matters

Jeffrey's framing — "Even if this PR doesnt change prompts/ it is injecting a
prompt" — is the load-bearing insight. The `pr_description_gate.py` rule was
*a path filter on what is fundamentally a behavior change* (did we alter
LLM-served content?). The extraction makes the path filter correct (because the
new `.md` file lives under `$PROJECT_ROOT/prompts/**`) and adds a regression-guard
test class (`TestCompanionCadenceInjectionFileContract`) that catches future
re-inlining attempts.

The same pattern applies to the 12 remaining inline builders. Each is a
single-file refactor following the recipe in the parent skill — should be
~30 minutes per PR once the recipe is in muscle memory.