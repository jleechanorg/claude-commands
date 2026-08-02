# Evidence Extraction Patterns for God-Mode Directive Violations

## Pattern: Confirm directive is saved in Firestore

After `download_campaign.py` export, load the `_game_state.json` and inspect:

```python
import json
with open("<export_dir>/<campaign>_game_state.json") as f:
    gs = json.load(f)
custom_state = gs.get("custom_campaign_state", gs.get("custom_state", {}))
directives = custom_state.get("god_mode_directives", [])
player_level = gs.get("player_character_data", {}).get("level", "NOT FOUND")
```

Key fields:
- `custom_campaign_state.god_mode_directives[]` — list of `{added, rule}` dicts
- `player_character_data.level` — character level at time of violation

## Pattern: Search story text for violation keywords

After `download_campaign.py --format txt`, search for narrative content that violates the directive:

```python
with open("<export_dir>/<campaign>.txt") as f:
    lines = f.readlines()

# Find violating text — adapt keywords to the directive's gated content
for i, line in enumerate(lines):
    if any(kw in line.lower() for kw in ['coordinated strike', 'coup', 'rebellion']):
        start = max(0, i-2)
        end = min(len(lines), i+3)
        for j in range(start, end):
            print(f"  {j}: {lines[j][:300]}")
```

## Pattern: Scene/turn marker mapping

Story entries contain `SCENE <N>` and `============================================================` delimiters. Map violations to scene numbers:

```python
for i, line in enumerate(lines):
    if line.strip().startswith("SCENE "):
        print(f"  Line {i}: {line.strip()}")
```

## Pattern: God-mode correction detection

Search for "**Correction Applied:**" or "GOD MODE DIRECTIVE:" markers in story text to find where corrections were applied and whether violations recurred afterward.

## Pattern: NPC status persistence divergence (sister bug class)

The narrative-only state change class — LLM emits a status outcome
(`captured`, `killed`, `defected`, `moved`) in the `narrative` block but never
writes the corresponding `state_updates.npc_data[NPC].status` field. Pattern
for proving it from an exported campaign:

```python
import json
with open("<export_dir>/<campaign>_game_state.json") as f:
    gs = json.load(f)
state = gs.get("state", gs)
npc_data = state.get("npc_data") or state.get("custom_campaign_state", {}).get("npc_data") or {}
core_memories = (state.get("custom_campaign_state", {}) or {}).get("core_memories", [])

# 1. Find every core_memory that mentions the NPC
for m in core_memories:
    s = str(m)
    if "<NPC_NAME>" in s and any(kw in s.lower() for kw in ("captured", "killed", "defected", "moved", "broken", "yielded")):
        print("NARRATIVE-EVIDENCE:", s[:200])

# 2. Check canonical npc_data for the same NPC
status = npc_data.get("<NPC_NAME>", {}).get("status", [])
print(f"CANONICAL-STATUS: {status}")
# If NARRATIVE-EVIDENCE present and CANONICAL-STATUS absent/contradictory → bug class confirmed
```

Full investigation recipe (GCP log filter + Firestore direct read + repro
template) lives in `references/npc-status-persistence-bug.md`. Adjacent to
god-mode directive violations structurally: both are "narrative diverges
from canonical state." Different fix surface — directive violations are
advisory-only enforcement; NPC-status persistence is a missing write that
canonicalizer (PR #8120) cannot fix.