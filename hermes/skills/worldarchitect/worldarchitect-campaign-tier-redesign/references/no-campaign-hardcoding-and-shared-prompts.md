# No-Campaign-Hardcoding + Shared Prompts — canonical reference (v0.5.0)

The user's explicit preference (verified 2026-07-28, Slack `C0AUXSVFSA2`):

> *"I never want anything hardcoded to a single campaign except Dragon Knight."*

The user's review comment on PR #8661 (verified 2026-07-28, PR #8661 review comment 3670171626 by `jleechan2015` on `$PROJECT_ROOT/agent_prompts.py:175`):

> *"No I dont want anything hardcoded to a single campaign"*

The CodeRabbit P1 reviewer (verified 2026-07-28, PR #8661 review comment 3670115816 on `$PROJECT_ROOT/agent_prompts.py:177`) flagged the same issue independently:

> *"`P1` Load the Spellblade overlay for opted-in campaigns. Registering this path does not load the overlay: no agent prompt set or builder references `PROMPT_TYPE_SPELLBLADE_VALERIA_CAMPAIGN`, so even campaigns with `custom_campaign_state.spellblade.enabled=true` never send the Hidden Power, custody, or Valeria contracts to the model. Add it to the owning agent's conditional prompt path and test the assembled served payload rather than only the registry and file contents."*

The P1 reviewer (id 3670115816) and the user's comment (id 3670171626) are structurally identical: **hardcoding a path in `PATH_MAP` does not load the overlay.**

## The canonical contract — "one rule, one authoritative file + state-keyed generic gate"

### The five-layer rule

1. **Generic rules live in `$PROJECT_ROOT/prompts/shared/`** (one rule, one authoritative file per AGENTS.md). Six canonical contracts (verified 2026-07-28 PR-A):
   - `$PROJECT_ROOT/prompts/shared/npc_personality_trifecta.md` — Want/Fear/Boundary + evolution rule (trifecta updates when an event plausibly fulfills/negates/mutates it).
   - `$PROJECT_ROOT/prompts/shared/hidden_identity_knowledge_boundaries.md` — direct observation rule + rumor tier shift + no aggregate suspicion meter.
   - `$PROJECT_ROOT/prompts/shared/witness_based_reveal_continuity.md` — witness set persistence in `custom_campaign_state.reveal_witnesses[<reveal_id>]`.
   - `$PROJECT_ROOT/prompts/shared/fair_high_power_challenge.md` — 5 axes (specialized counters, environmental pressure, real choices, hidden stakes, specialized skills).
   - `$PROJECT_ROOT/prompts/shared/no_forced_ruler_progression.md` — NPCs don't volunteer rulership unless PC asks.
   - `$PROJECT_ROOT/prompts/shared/ai_generated_mystery_and_internal_drive_plot_arc.md` — mystery template + per-act growth/insecurity/reframe requirement.

2. **Every agent that needs a contract wires it into `REQUIRED_PROMPT_ORDER` or `OPTIONAL_PROMPTS`.** Per AGENTS.md rule: "Do not infer ownership from directory names. Inspect the concrete agent class and prompt builder path before changing a rule. Conditional prompt tails, requested detail sections, campaign-tier overlays, and disabled prompt families are loaded only through their explicit code paths."

3. **The `custom_campaign_state.campaign_overlays` generic gate.** `$PROJECT_ROOT/agents.py` `build_system_instructions` iterates `custom_campaign_state.campaign_overlays = [{name, path, gate_key}, ...]` and loads each file when the gate_key is true. Adding a new campaign overlay = add `custom_campaign_state.campaign_overlays` to the campaign's seed state + ensure the campaign's file references shared contracts by name. **Do NOT add a per-campaign branch in `prompt_order()`.**

4. **NO per-campaign constants in `$PROJECT_ROOT/constants.py`** — except Dragon Knight's fast-path constants (which are sha256-guarded LLM-bypass shortcuts, not a per-campaign hardcoding). The 6 generic shared contracts are the only constants in `$PROJECT_ROOT/constants.py` for the prompt-loader side.

5. **NO new top-level `$PROJECT_ROOT/prompts/<campaign>/` subdirectory.** The campaign-specific instance lives wherever the campaign's existing artifacts already live (e.g. `world_reference/campaign_module_<campaign>.md` for Spellblade), and references the shared contracts by relative path.

### The 5 CodeRabbit blockers on PR #8661 and how they were fixed

| Comment ID | Severity | File | Issue | Fix |
|---|---|---|---|---|
| 3670115816 | P1 | `$PROJECT_ROOT/agent_prompts.py:177` | "Load the Spellblade overlay for opted-in campaigns" — registering `PATH_MAP` entry is not enough | Drop the `PROMPT_TYPE_SPELLBLADE_VALERIA_CAMPAIGN` registration; register Spellblade via the `campaign_overlays` generic gate |
| 3670115820 | P2 | `$PROJECT_ROOT/prompts/combat_system_instruction.md:1212` | "Serve the rulership contract on non-combat turns" — rule in combat prompt but it's a dialog rule | Move rule to `$PROJECT_ROOT/prompts/shared/no_forced_ruler_progression.md`; remove local copy from combat prompt |
| 3670115822 | P2 | `$PROJECT_ROOT/prompts/narrative_system_instruction.md:348` | "Allow NPC goals to evolve after state changes" — rule forbids evolution entirely | Move rule to `$PROJECT_ROOT/prompts/shared/npc_personality_trifecta.md` with explicit 4-condition evolution trigger |
| 3670115825 | P2 | `$PROJECT_ROOT/prompts/spellblade/spellblade_valeria_campaign.md:52` | "Consume hidden-power charges on Surprise Strikes" — `hidden_power_charges` never decrements | Add `Consume 1 charge per Surprise Strike; if 0 charges, fire without bonus and set `hidden_power_charges` to 0` |
| 3670115827 | P2 | `$PROJECT_ROOT/prompts/spellblade/spellblade_valeria_campaign.md:5` | "Extract mirrored rules into a shared prompt" — Spellblade's Personality Trifecta + 5 challenge axes duplicate generic versions | Reference shared files by relative path; remove mirrored sections |

### The test contract

`$PROJECT_ROOT/tests/test_no_campaign_hardcoding.py` (NEW v0.5.0) verifies:

```python
# 1. No per-campaign prompts/<campaign>/ subdirectory exists (excluding Dragon Knight)
for campaign_dir in PROMPTS_DIR.iterdir():
    if campaign_dir.is_dir() and campaign_dir.name != "dragon_knight":
        assert False, f"per-campaign directory {campaign_dir} is a hardcoding violation"

# 2. No PROMPT_TYPE_*_CAMPAIGN constant in $PROJECT_ROOT/constants.py (excluding Dragon Knight)
import mvp_site.constants as c
for name in dir(c):
    if "CAMPAIGN" in name and not name.startswith("DRAGON_KNIGHT"):
        assert False, f"per-campaign constant {name} is a hardcoding violation"

# 3. No per-campaign PATH_MAP entry references $PROJECT_ROOT/prompts/<campaign>/
import mvp_site.agent_prompts as ap
for prompt_type, path in ap.PATH_MAP.items():
    if "/spellblade/" in path or any(f"/{name}/" in path for name in OTHER_CAMPAIGNS):
        assert False, f"PATH_MAP entry {prompt_type} -> {path} is a hardcoding violation"

# 4. The campaign_overlays generic gate is exercised
fixture = {
    "custom_campaign_state": {
        "campaign_overlays": [
            {"name": "spellblade_valeria_campaign", "path": "...", "gate_key": "spellblade.enabled"},
        ],
        "spellblade": {"enabled": True},
    }
}
loaded = build_system_instructions(fixture)
assert "Surprise Strike" in loaded  # the contract was loaded
```

## Why Dragon Knight is the exception

The Dragon Knight fast-path is a sha256-guarded LLM-bypass shortcut. The canonical description is hashed in `$PROJECT_ROOT/constants.py:DRAGON_KNIGHT_CANONICAL_PROMPT_SHA256` and matched against the user's first-turn prompt; on match, the canonical opening story loads without an LLM call. Verified PR #8004 (feat/quick-start-campaign) — the canonicalization hash is the runtime contract. Removing this would regress the first-turn UX by ~3 seconds. The user's explicit carve-out for Dragon Knight is therefore load-bearing and the rule must not be extended to cover it.

## Companion references

- `references/ai-mystery-internal-drive-plot-recipe.md` — the AI-mystery + internal-drive plot design pattern (Phase 2.5 recipe).
- `~/.hermes/skills/worldai-campaign-to-google-doc/SKILL.md` — the Google Doc consolidation skill (separate domain; not directly affected by this rule).
- `~/.hermes/skills/campaign-creation/SKILL.md` v1.2.0 — the campaign DESIGN skill; consumes the shared contracts and the `custom_campaign_state.campaign_overlays` gate.
- `~/.hermes/skills/workflow/always-pr-never-local-edit/SKILL.md` — the PR lifecycle skill; the no-campaign-hardcoding rule is a sibling precondition (every campaign integration MUST end in a PR).
- `~/.hermes/skills/llm-wiki/SKILL.md` — the wiki authoring skill; the 16 MBTI pages at `~/llm_wiki/wiki/concepts/mbti/*.md` are the AI-background source for the personality/insecurity architecture.
- AGENTS.md (`$PROJECT_ROOT/prompts/AGENTS.md`) — the authoritative rule source for "one rule, one authoritative file" and "do not infer ownership from directory names." This skill's Pitfall #18 is the runtime enforcement.
