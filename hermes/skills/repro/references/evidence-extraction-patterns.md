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