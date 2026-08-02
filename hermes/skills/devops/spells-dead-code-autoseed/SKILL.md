---
name: spells-dead-code-autoseed
description: Bug class — spell-repair LLM function defined but never called, leaving caster characters with "No spell list recorded" until user manually asks "fix my spells". Trigger on /repro when the Spells panel shows the fallback warning OR the LLM-generated spell list is in prose but not in player_character_data.
---

# Spells panel "No spell list recorded" — dead-code autoseed bug class

## Symptom

Spells panel shows the fallback warning:

```
▸ Spell Slots:
  • Level 1: 4/4
  • Level 2: 3/3

▸ Spells:
  No spell list recorded. Type: "What spells do I know?" to set them up.
```

— for a character with `spell_slots` populated AND `cantrips`/`spells_known`/`spells_prepared` missing in `player_character_data`. The panel rendering gate is at `$PROJECT_ROOT/main.py:3631-3641`:

```python
if (
    spell_slots
    and not spells_known
    and not cantrips
    and not spells_prepared
):
    lines.append("  No spell list recorded. Type: ...")
```

## Root cause (canonical)

The codebase has three relevant functions in `$PROJECT_ROOT/world_logic.py`:

| Function | Lines | Behavior |
|---|---|---|
| `_spells_missing_for_class(pc)` | 6852 | **Detector** — returns matched caster class name or None |
| `_seed_starting_spells_if_missing(pc)` | 6873 | **Warn-only** — logs `⚠️ Spellcasting class 'X' has missing spells after creation.` and returns pc unchanged |
| `_generate_spells_via_llm(pc, user_id)` | 6978 | **LLM-backed repair** — calls Gemini with the SpellRepairAgent prompt at line 6957, parses JSON, writes `cantrips`/`spells_known`/`spells_prepared` to pc. Wraps the call in BQ logging via `_bq_log_spell_repair_interaction`. **Fail-soft: returns pc unchanged on any error.** |

`_generate_spells_via_llm` is **defined but never called** — `grep -rn "_generate_spells_via_llm" $PROJECT_ROOT/` finds only the definition + its BQ log helper, no callers.

The 4 sites that *could* call it (`world_logic.py:4881`, `:7384`, `:7596`, `:7693`) all invoke the warn-only `_seed_starting_spells_if_missing` instead. So the detector fires, the warning is logged, but no repair ever runs.

End state: any caster whose first creation turn doesn't emit spell fields will show the "No spell list recorded" warning forever, unless the user manually types "fix my spells" — which still doesn't invoke the repair function. The LLM just hallucinates the spells because the prompt context now implies it.

## Diagnostic recipe

### 1. Static-evidence greps (run BEFORE asking user for phenotype anchors)

```bash
# Confirm dead-code condition
grep -rn "_generate_spells_via_llm" $PROJECT_ROOT/ | wc -l   # expect 1 (defn only)
grep -rn "_seed_starting_spells_if_missing" $PROJECT_ROOT/world_logic.py | wc -l   # expect 5 (defn + 4 calls)

# Confirm the symptom rendering gate
grep -n "No spell list recorded" $PROJECT_ROOT/main.py  # expect 1 match near line 3640

# Find sibling repros (campaigns with caster + missing spells)
gh issue list --repo $GITHUB_REPOSITORY --state all \
  --search "spells panel OR spell list recorded OR fix my spells" \
  --json number,title,state
```

### 2. Confirm phenotype from a real campaign

```bash
export WORLDAI_DEV_MODE=true
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"

# Resolve UID + download campaign
python3 scripts/download_campaign.py --campaign-id <ID> --email <OWNER_EMAIL>
# Inspect game_state JSON: pc.spells_known / pc.cantrips / pc.spells_prepared
```

Symptom markers in `game_state.json`:
- `resources.spell_slots` populated (e.g. `{"level_1": {"current": 4, "max": 4}}`)
- `player_character_data.spells_known` missing or `[]`
- `player_character_data.cantrips` missing or `[]`
- `player_character_data.spells_prepared` missing or `[]`

### 3. Verify dead code (the smoking gun)

```python
# In a Python REPL with mvp_site on path:
from mvp_site import world_logic
assert hasattr(world_logic, "_generate_spells_via_llm")  # exists
import inspect
src = inspect.getsource(world_logic._generate_spells_via_llm)
# Note: no callers anywhere in $PROJECT_ROOT/. The function has been in the codebase
# since the spell-repair feature was added but had no caller wired in.
```

## Fix shape (Track A — wiring)

Add a wrapper that calls the LLM-backed repair when a caster has missing spells, falling back to the warn-only path on LLM error:

```python
def _repair_or_warn_missing_spells(
    player_character_data: dict[str, Any],
    user_id: str | None = None,
) -> dict[str, Any]:
    matched_class = _spells_missing_for_class(player_character_data)
    if not matched_class:
        return player_character_data
    try:
        return _generate_spells_via_llm(player_character_data, user_id)
    except Exception as exc:
        logging_util.warning(
            f"_repair_or_warn_missing_spells: LLM repair failed for class='{matched_class}' "
            f"on '{player_character_data.get('name')}': {exc!r}; falling back to warn-only."
        )
        return _seed_starting_spells_if_missing(player_character_data)
```

Replace all 4 call sites of `_seed_starting_spells_if_missing` in `world_logic.py`:

- `:4881` (unified action path — primary entry for character creation completion)
- `:7384` (God-mode character creation — also write back to `player_character_data` since the return value is otherwise discarded)
- `:7596` (Dragon Knight template merge — write back via `initial_game_state["player_character_data"] = ...`)
- `:7693` (merged-pc path — write back via `initial_game_state["player_character_data"] = ...`)

Two of the call sites discard the return value (`_seed_starting_spells_if_missing` returns `pc` but the call sites pass `pc` as the only argument and don't reassign). When switching to `_repair_or_warn_missing_spells`, you MUST either:
- Reassign the local variable: `player_character_data = _repair_or_warn_missing_spells(player_character_data, user_id)`, OR
- Write back to the parent dict: `initial_game_state["player_character_data"] = _repair_or_warn_missing_spells(_dk_pc, user_id)`

Otherwise the LLM-generated spells land in a transient dict that never persists.

## Track B (out of scope — file as follow-up)

Prompt-level enforcement: add a hard rule in the character-creation prompts at `$PROJECT_ROOT/prompts/` that `state_updates.player_character_data` MUST include `cantrips[]`/`spells_known[]`/`spells_prepared[]` for any class flagged as a caster. Empty arrays or missing fields will trigger an automatic SpellRepairAgent call.

## Track C (out of scope — file as follow-up)

Frontend fallback at `$PROJECT_ROOT/frontend_v1/app.js:789` (`buildSpellsHTML`): when `data.spells_summary` is non-empty AND `data.spells_known`/`cantrips`/`spells_prepared` are empty, render the prose `spells_summary` as a fallback list instead of the "No spells available" default. Degradation pattern, not a fix.

## Evidence requirements (per AGENTS.md)

Track A modifies `$PROJECT_ROOT/world_logic.py` (production backend). Per AGENTS.md:
- Real-server proof: local Flask server with `WORLDAI_DEV_MODE=true` + real Firestore creds.
- Real LLM capture: the SpellRepairAgent Gemini response that populates spell fields.
- Browser/video evidence: headless Chrome recording of the Spells panel transition from "No spell list recorded" → populated list.
- BQ `event_type=spell_repair` row confirms the auto-repair ran.
- Same-symptom coverage on a second campaign (twin-copy via `scripts/copy_campaign.py`).

## Worked example

- **Issue**: [#8358](https://github.com/$GITHUB_REPOSITORY/issues/8358) — campaign `H9rwoizUNH01vpJhVhF4` ("Visenya V8 (spells not set)"), Level 6 Sovereign Shadow custom Charisma caster, 6 entries (3 user, 3 AI).
- **Twin copy**: `3x4nyLgEzZ7yjDSPVwkv` under `<your-email@gmail.com>` (UID `0wf6sCREyLcgynidU5LjyZEfm7D2`).
- **PR**: [#8359](https://github.com/$GITHUB_REPOSITORY/pull/8359) — branch `fix/spell-autoseed-8358`, commit `4efe51549f`, diff +44/-10 lines on `$PROJECT_ROOT/world_logic.py`.
- **Deployed dev SHA at repro**: `aaa03c4d566a160715b170c209aad8c6447b84bb` (branch `chore/skip-draft-pr-workflow-runs`).

## Sibling bug classes (NOT this one)

- **Level-up exit classifier** ([#7554](https://github.com/$GITHUB_REPOSITORY/issues/7554), [#7609](https://github.com/$GITHUB_REPOSITORY/issues/7609)) — `LEVEL_UP_EXIT_ANCHOR_PHRASES` too narrow, freeform "apply recommended ..." not matched. Different file (`$PROJECT_ROOT/intent_classifier.py`), different mechanism (semantic routing), different fix (anchor coverage).
- **God-mode directive missing** — custom features granted in narrative but never persisted. See `references/god-mode-directive-missing-subclasses.md`.
- **NPC status persistence** — narrative-only state changes that never reach `state_updates.npc_data`. See `references/npc-status-persistence-bug.md`.

The dead-code-autoseed bug is **distinct** because the fix surface is **server-side wiring** (existing LLM call), not prompt-only.

## Pitfalls

- **Don't assume the LLM is the bug.** The LLM DOES generate correct spells when the user nudges it (Scene 3 of `H9rwoizUNH01vpJhVhF4` shows a verbatim SpellRepairAgent-quality spell list in prose). The bug is purely the wiring.
- **Don't add a regex/keyword guard for "fix my spells"**. That's a fix to a different (perceptual) symptom; the user should NOT have to know the magic phrase.
- **Don't change the prompt to hard-require spells for casters only** as the primary fix. That works as Track B but doesn't address the existing dead code. Both tracks ship.
- **Be careful with the 4 call sites**: two of them discard the return value. Wiring without reassigning leaves the repair in a transient dict. Use the write-back pattern shown above.
- **The `_generate_spells_via_llm` function is fail-soft**: it returns pc unchanged on any error. The `_repair_or_warn_missing_spells` wrapper around it should ALSO be try/except (LLM errors shouldn't crash the turn). On failure, fall back to the warn-only path so we still log the gap.

## Verification commands

```bash
# After applying the fix, verify wiring
grep -rn "_generate_spells_via_llm" $PROJECT_ROOT/ | wc -l   # expect >= 5 (1 defn + 4 callers + 1 in helper)
grep -rn "_repair_or_warn_missing_spells" $PROJECT_ROOT/world_logic.py | wc -l   # expect 5 (1 defn + 4 callers)

# Confirm import still loads
python3 -c "from mvp_site import world_logic; print('OK', world_logic._repair_or_warn_missing_spells.__name__)"
```