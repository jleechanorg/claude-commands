# PC-silent prompt diagnosis — worked example (2026-07-13)

> ⚠️ **Correction (2026-07-14):** This reference describes the original diagnosis path. The user's actual complaint was **NPC-silent**, not PC-silent. The PC-silent numbers below were real but were a *symptom* of the same root cause (prompt bias toward NPC internal monologue over spoken dialog). When using this reference, verify which axis the user is complaining about before writing the fix. See `references/prompt-fix-effectiveness-verification.md` for the post-merge verification recipe that surfaced this correction.

Session provenance: Hermes slack thread `C0AH3RY3DK6 / ts 1783986579.477669`.
Jeffrey's literal ask: "Review the last 10 campaigns with 50+ scenes ignoring copies and duplicates and see why other characters seem to rarely talk or give dialogue besides main character. Check the prompts and especially dialog and heavydialog agent should have other characters talking."

Outcome: confirmed PC-silent bias across all 10 campaigns; root-caused to 3 prompt files; recommended prompt-only fix; bead `rev-nvbw0` opened.

## What "PC-silent" means here

Across 2,464 gemini-authored scenes in 10 long campaigns:

| Agent | Scenes | % of total | median PC lines | median NPC lines | % PC-silent | % two-way |
|---|---:|---:|---:|---:|---:|---:|
| HeavyDialogAgent | 676 | 27% | 0 | 17 | 67.8% | 32.2% |
| DialogAgent | 286 | 12% | 0 | 20 | 75.5% | 24.5% |
| StoryModeAgent | 344 | 14% | 0 | 15.5 | 79.7% | 20.3% |
| GodModeAgent | 476 | 19% | 0 | 6 | 99.8% | 0.2% |

96% of scenes have ≥1 NPC line; only 17% have any two-way dialog. The PC is silent in 3 out of 4 HeavyDialog scenes despite the agent's stated purpose ("high-stakes conversations where richer mechanics/world context improves output quality").

## Diagnostic recipe (use whenever a per-agent analysis shows %silent anomaly)

### Step 1 — Identify the affected agent's prompt files

In `$PROJECT_ROOT/agents.py`, find the agent's class and read its `REQUIRED_PROMPT_ORDER`. Example for HeavyDialogAgent:

```python
# $PROJECT_ROOT/agents.py L2686-2697
REQUIRED_PROMPT_ORDER: tuple[str, ...] = (
    constants.PROMPT_TYPE_MASTER_DIRECTIVE,
    constants.PROMPT_TYPE_GAME_STATE,
    constants.PROMPT_TYPE_PLANNING_PROTOCOL,
    constants.PROMPT_TYPE_DIALOG,            # ← dialog_system_instruction.md
    constants.PROMPT_TYPE_NARRATIVE,         # ← narrative_system_instruction.md
    constants.PROMPT_TYPE_MECHANICS,
    constants.PROMPT_TYPE_CHARACTER_TEMPLATE,
    constants.PROMPT_TYPE_RELATIONSHIP,
    constants.PROMPT_TYPE_REPUTATION,
    constants.PROMPT_TYPE_LIVING_WORLD,
)
```

Map each `PROMPT_TYPE_*` constant to its `.md` file in `$PROJECT_ROOT/prompts/`. Each prompt file is the candidate root-cause surface.

### Step 2 — Search for NPC-only bias in dialog prompts

For `dialog_system_instruction.md` (or any dialog-class prompt), run these greps:

```bash
rg -c "player.character" $PROJECT_ROOT/prompts/dialog_system_instruction.md
rg -c "speak.*as.*PC|speak.*as.*the PC|PC voice|player.character speaks|your character says|on behalf of the player" $PROJECT_ROOT/prompts/dialog_system_instruction.md
rg -c "Section 9|Anti-Patterns" $PROJECT_ROOT/prompts/dialog_system_instruction.md
```

Expected findings for a NPC-biased prompt:

- `player.character` hits > 0 (any reference) but no instruction to put words in PC's mouth
- `speak as the PC` / `PC voice` / etc → 0 hits (no instruction)
- Section 9 "Anti-Patterns" exists but doesn't list "PC silent" or "NPC monologue dominance"

### Step 3 — Search for authority-split bias in narrative prompts

For `narrative_system_instruction.md` and `narrative_lite_system_instruction.md`:

```bash
rg -n "NARRATIVE AUTHORITY|Player.*describe|Players describe|GM/AI describe" $PROJECT_ROOT/prompts/narrative_system_instruction.md
rg -n "NARRATIVE AUTHORITY|Player.*describe|Players describe|GM/AI describe" $PROJECT_ROOT/prompts/narrative_lite_system_instruction.md
```

Expected for biased prompts — a block like:

```markdown
**NARRATIVE AUTHORITY:**
- Players describe their CHARACTER'S actions and intentions
- The GM/AI describes the WORLD'S response, NPC reactions, and outcomes
```

The LLM interprets this strictly: PC actions are the player's exclusive domain. When "actions and intentions" doesn't explicitly carve out *dialogue*, the LLM defaults to PC-silent because the GM side is reserved for "NPC reactions and outcomes."

### Step 4 — Cross-reference agent coverage

Check whether the affected agent has a PC-voice prompt slot in `REQUIRED_PROMPT_ORDER`:

```bash
rg -n "PROMPT_TYPE_PC_VOICE|pc_voice_instruction" $PROJECT_ROOT/agents.py
```

If no hits and the agent inherits a NPC-biased dialog prompt, that's the structural cause.

## Recommended fix shape (prompt-only, no backend enforcement)

### For dialog prompts (`dialog_system_instruction.md`)

1. Add a new Section 10 "PC Voice in Conversations" that:
   - Authorizes direct quoted speech for the PC using `player_character_data` persona
   - Sets minimum PC-voice cadence: "in any scene where ≥2 NPCs speak, the PC should also speak at least once via direct quote, unless the scene explicitly depicts the PC as silent/incognito"
2. Update Section 2.1 turn-taking to include PC turn entry
3. Add Section 9 anti-pattern entry: "NPC monologue dominance / PC silent"

### For narrative prompts (`narrative_system_instruction.md`, `narrative_lite_system_instruction.md`)

Replace or supplement the "NARRATIVE AUTHORITY" block to clarify: PC dialogue IS within AI scope during conversation scenes, even though PC actions are player-domain.

### For agent prompt-stack (`agents.py`)

Optionally add a new `PROMPT_TYPE_PC_VOICE` constant + `pc_voice_instruction.md` file + slot in HeavyDialogAgent's `REQUIRED_PROMPT_ORDER`. This makes the fix auditable via `debug_info.system_instruction_files`.

## Anti-patterns to avoid in the fix

- ❌ Adding backend enforcement (e.g. "PC must speak ≥1 line, retry if not"). Per `root-cause-first` skill: doubles token cost, LLM finds ways to bypass, masks the real prompt issue.
- ❌ Modifying the schema to add a `pc_voice_quotient` field. The bug is in the prompt, not in the data shape.
- ❌ Adding a re-prompt loop on heavy-dialog scenes. Same cost concern.
- ✅ Add the prompt-layer instruction; rely on the LLM following the new instruction.

## Artifacts (durable)

- Wiki source page (full diagnosis): `~/llm_wiki/wiki/sources/pc-silent-dialog-analysis-2026-07-13.md`
- Per-scene dump (2,464 rows): `~/.hermes/dialog_review_2026-07-13/all_scenes_by_agent.jsonl`
- Per-agent summary JSON: `~/.hermes/dialog_review_2026-07-13/agent_summary.json`
- Last-10 candidate list: `~/.hermes/last10_50plus_2026-07-13.json`
- Sample verbatim HeavyDialog scene with best-case PC voice (8 PC / 50 NPC / 852 words): included in the wiki page
- Bead: `rev-nvbw0` (priority 2, type=bug, opened via `br create`)

## Verification recipe (after the fix lands)

Once the prompt fix is deployed:

1. Wait ≥3 days for new scenes to accumulate under the new prompt.
2. Re-run this skill's Phase 2-5 on the same 10 campaigns (or last 10 with 50+ scenes).
3. Expected before/after:
   - HeavyDialogAgent PC-silent rate: 67.8% → <30%
   - HeavyDialogAgent two-way dialog rate: 32.2% → >60%
   - Median PC lines/scene in HeavyDialog: 0 → ≥2
4. If targets not met: the fix is incomplete — re-read the changed prompt files and search for any remaining NPC-only bias.