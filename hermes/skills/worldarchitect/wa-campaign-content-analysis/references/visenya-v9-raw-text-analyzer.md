# Visenya v9 Raw-Text Analyzer — Pipeline Reference

**Companion to `personal-scale-challenge-pattern.md`.** Documented from the 2026-07-26 session where Visenya v9's `debug_info` and `full_state_updates` were both empty for every story entry. The skill's default analyzer (`per_scene_dialog_audit.py`) relies on `debug_info.agent_name` and `text` fields — both unavailable here.

## When this fallback applies

A campaign's `story` subcollection returns docs where:
- `debug_info = {}` (no `agent_name`, `llm_model`, `system_instruction_files`)
- `full_state_updates = {}` (no per-turn state diff)
- `text` field may be present but lacks the canonical schema markers

Verified 2026-07-26 on:
- Campaign: Visenya v9 (The Blood Dragon Apex Stalker)
- Campaign ID: `qoQtHsU7DxZnR24VNU9w`
- Entries: 824 (412 user + 412 gemini)

Detection probe (run before the full analyzer):

```python
sample = next(camp.collection("story").limit(5).stream()).to_dict() or {}
debug = sample.get("debug_info") or {}
fsu = sample.get("full_state_updates") or {}
has_agent_tracking = bool(debug.get("agent_name"))
has_state_updates = bool(fsu)
# On Visenya v9: has_agent_tracking == False, has_state_updates == False
```

## What you lose without the schema fields

- **Per-agent breakdown** — every scene falls to `"unknown"` agent. Useless histogram.
- **Per-turn level updates** — `full_state_updates.player_character_data.level` is empty for every entry; can't derive level timeline without parsing `Status:` lines.
- **`mode` field** — still works for user entries (it's "character", "god", "think"); missing on most gemini entries.

## What you still have

The `download-campaign` skill (`~/.hermes_prod/skills/download-campaign/SKILL.md`) produces a flat-text archive at:

```
~/llm_wiki/raw/campaigns/<id8>/<title>_<id8>.txt
```

with `====== SCENE N ======` delimiters and a `Status: Lvl X ...` header per scene. Every scene block contains:
- `Status:` line with current level / HP / XP
- `Game Master:` narrative
- `Player (freeform):` user prompt (where present)
- `God Mode:` directive (where present)
- `Dice Rolls:` block (when relevant)
- Quoted speech, NPC body-language shifts, mechanical annotations

This raw format is **richer than the Firestore schema for diagnostic purposes** — the LLM writes more into the rendered narrative than into the structured fields.

## Pipeline (reference implementation)

The reference pipeline at `/tmp/analyze_visenya_v9_v2.py` walks the raw `.txt` instead of Firestore. Key functions:

```python
from pathlib import Path
import re
from collections import defaultdict
import statistics

RAW = Path("$HOME/llm_wiki/raw/campaigns/<id8>/<title>_<id8>.txt")
OUT_DIR = Path("$HOME/.hermes/<topic>_<date>")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SCENE_RE = re.compile(r"^SCENE (\d+)$", re.MULTILINE)
STATUS_RE = re.compile(r"^Status:\s*Lvl\s*(\d+)", re.MULTILINE)

# Regex classifiers — see references/personal-scale-challenge-pattern.md for the full set
CONCEALED_RE = re.compile(r"(?i)(?:you don't see|no one mentions?|... )")
ZERO_SUM_RE = re.compile(r"(?i)(?:you cannot please both|cannot save both|... )")

# Per-scene PC / NPC classification via quoted-speech + name-colon + verb-indirect
# Same patterns as the in-place analyzer's `count_dialog()` function.

def count_dialog(text, pc_name="Visenya"):
    """Return (pc_lines, npc_lines, speakers_list)."""
    pc = npc = 0
    seen = set()
    for pat in DIALOG_PATTERNS:
        for m in pat.finditer(text):
            line = m.group(1).strip()
            key = line[:50]
            if key in seen: continue
            seen.add(key)
            if FIRST_PERSON_RE.match(line):
                pc += 1
            else:
                npc += 1
    for m in NAME_COLON_RE.finditer(text):
        sn = m.group(1).strip()
        if sn in MECHANIC_LABELS: continue
        if sn.lower() == pc_name.lower():
            pc += 1
        else:
            npc += 1
            speakers.append(sn)
    return pc, npc, list(set(speakers))

def main():
    txt = RAW.read_text()
    scene_positions = [(m.start(), m.end(), int(m.group(1)))
                      for m in SCENE_RE.finditer(txt)]
    scenes = []
    for i, (start, end, n) in enumerate(scene_positions):
        block = txt[end+1 : scene_positions[i+1][0] if i+1 < len(scene_positions) else len(txt)]
        lvl = int(m.group(1)) if (m := STATUS_RE.search(block)) else None
        pc, npc, speakers = count_dialog(block)
        scenes.append({
            "n": n,
            "level": lvl,
            "words": len(block.split()),
            "pc_lines": pc,
            "npc_lines": npc,
            "speakers": speakers[:6],
            "zero_sum_n": len(ZERO_SUM_RE.findall(block)),
            "concealed_n": len(CONCEALED_RE.findall(block)),
            "block_excerpt": block[:600].replace("\n", " | "),
        })
    # Per-level bucket aggregation
    by_level = defaultdict(list)
    for s in scenes:
        by_level[s["level"]].append(s)
    # Pre / post split at the user-defined threshold
    threshold = 15
    pre = [s for s in scenes if s["level"] and s["level"] < threshold]
    post = [s for s in scenes if s["level"] and s["level"] >= threshold]
    # ... aggregate medians, percentages, densities ...
```

## Output artifacts

For each diagnostic pass, write all of these to `~/.hermes/<topic>_<date>/`:

| File | Contents |
|---|---|
| `all_scenes.jsonl` | Per-scene structured rows (one per scene, all fields) |
| `scenes_by_level.json` | Per-level bucket aggregated metrics |
| `summary.json` | Headline numbers + pre/post split summary |
| `samples.json` | Top-N scenes by dynamic score, pre-L15 + post-L15 |
| `diagnosis.md` | Long-form analysis with scene excerpts and prompt recommendations |

Don't write to `/tmp` — per `wa-campaign-content-analysis` Pitfall 3, `/tmp` is sandbox-scoped and disappears on next reboot / between execute_code calls in some runtimes.

## Heuristic classifier caveats

The PC-silent %, zero-sum, concealed-consequence densities use regex patterns that the user explicitly cited. They're directionally correct but under-count cues the simple patterns miss:

- NPC body-language / frequency shifts (e.g. "frequency", "Discordant", "rising panic")
- Dice rolls named in passing (e.g. `1d20+6 = 23 vs DC 18`)
- Explicit cooldowns (e.g. "the 48-hour cooldown protects your identity")
- Witness memory (e.g. "Dunk and Egg are watching your hands with dread")

For more accurate measurement on a verification pass, extend the classifier set with these patterns:

```python
BODY_LANG_RE = re.compile(
    r"(?i)(?:frequency|Discordant|resonant|rising \w+|alarm|pulse|shimmer|"
    r"paralyzed|crossing themselves|hand shakes|gripping|fixed on|"
    r"watching your hands|electrifying terror|quiet panic)"
)
DICE_NAMED_RE = re.compile(
    r"(?:1d20\+?\d*\s*[=:]\s*\d+\s*vs\s*DC\s*\d+|Total\s*\d+\s*vs\s*DC\s*\d+|"
    r"Roll:\s*\d+\s*vs\s*DC\s*\d+)"
)
COOLDOWN_RE = re.compile(
    r"(?i)(?:(N)-?hour cooldown|N-hour cooldown protects|cooldown until|"
    r"\d+?-turn cooldown)"
)
```

Density of these on Visenya v9:
- BODY_LANG: 5-10 / 1k words in dynamic scenes, ~0 in quiet scenes. **Best signal**.
- DICE_NAMED: 1-3 / 1k words in dynamic scenes, 0 in non-combat scenes.
- COOLDOWN: 0.5 / 1k words (sparse but high-signal).

## Verified artifacts from the 2026-07-26 run

```
~/.hermes/visenya_v9_diagnosis_2026-07-26/
├── all_scenes.jsonl         (374 KB, 412 rows)
├── scenes_by_level.json     (432 KB, per-level aggregations)
├── summary.json             (1.2 KB, headline numbers)
├── samples.json             (4.2 KB, 4 representative scenes)
├── summary.md               (3.2 KB, marketing-style summary)
└── diagnosis.md             (16.7 KB, full diagnosis + 5 prompt-only fixes)
```

`/tmp/analyze_visenya_v9_v2.py` is the analyzer (12.6 KB). For a re-run on a new campaign in this format, copy `/tmp/analyze_visenya_v9_v2.py` to a working path, change `RAW` and `OUT_DIR`, re-run.

## Integration with the in-place analyzer

When the schema-zero detection in the parent skill fires, the recommended downstream flow is:

1. **Skip** `per_scene_dialog_audit.py` (it depends on `debug_info.agent_name`).
2. **Run** `download-campaign --mode one --campaign-id <id>` with `env -u MOCK_SERVICES_MODE` (Pitfall 13 from the same skill).
3. **Run** the raw-text pipeline (`/tmp/analyze_visenya_v9_v2.py` or its derivative).
4. **Report** schema-zero state explicitly: *"Agent attribution unavailable (empty `debug_info`); analysis based on raw text export."*
5. **Don't fabricate** per-agent percentages.
