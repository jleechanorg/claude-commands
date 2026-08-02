# Sibling-campaign cluster: `xK3fp5XrV24oarIINTF7` (Visenya v7) — 7+ NPC-status persistence siblings over 9 days

**Updated 2026-07-12** to add issue #8335 ("queen is supposed to be dead but LLM forgot") as the 7th confirmed sibling instance.

## Confirmed sibling instances on this campaign

| # | Issue | PR | Scene(s) | NPC | Symptom | Sub-class (from `npc-status-persistence-bug.md`) |
|---|---|---|---|---|---|---|
| 1 | [#8266](https://github.com/$GITHUB_REPOSITORY/issues/8266) | [#8267](https://github.com/$GITHUB_REPOSITORY/pull/8267) | 86/89/97/100/149/151 | Prince Aemond Targaryen | "captured" hallucinated 14 turns later | missing-write + wrong-write + prompt-anchor |
| 2 | [#8283](https://github.com/$GITHUB_REPOSITORY/issues/8283) | [#8284](https://github.com/$GITHUB_REPOSITORY/pull/8284) | 314/315 | Visenya | "daughter of the queen" inversion | confused-state (`with`/`replace`) |
| 3 | [#8275](https://github.com/$GITHUB_REPOSITORY/issues/8275) | [#8276](https://github.com/$GITHUB_REPOSITORY/pull/8276) | 107/123/136/137/142/156 | Queen Rhaenyra | level 14 → 10 in bundle | stale-bundle (separate sub-class from NPC persistence) |
| 4 | [#8293](https://github.com/$GITHUB_REPOSITORY/issues/8293) | [#8294](https://github.com/$GITHUB_REPOSITORY/pull/8294) | 375 | (treasure) | hidden gold hallucinated | stale-context (natural-language prose) |
| 5 | [#8320](https://github.com/$GITHUB_REPOSITORY/issues/8320) | [#8321](https://github.com/$GITHUB_REPOSITORY/pull/8321) | (custom) | (player) | Conqueror's Insight mechanic | god-mode-grant-not-operationalized (separate skill family) |
| 6 | [#7885](https://github.com/$GITHUB_REPOSITORY/issues/7885) | [#7886](https://github.com/$GITHUB_REPOSITORY/pull/7886) | (character creation) | Visenya | Spells / ability points setup | missing-write (separate skill family: char creation) |
| 7 | **[#8335](https://github.com/$GITHUB_REPOSITORY/issues/8335)** | **[#8336](https://github.com/$GITHUB_REPOSITORY/pull/8336)** | **628/648/652/653** | **Queen Rhaenyra Targaryen** | **death state forgotten, narrative revival 4h after god-mode forced death** | **wrong-write + missing-write + wrong-key write** |

## The two NEW sub-classes introduced by #8335 (2026-07-12)

### Sub-class 5: God-mode-retcon missing-write

God-mode agent emits an admin-retcon narrative acknowledging a state change (e.g. "I have corrected the record regarding Queen Rhaenyra's death") but does NOT write `state_updates.npc_data[NPC]`. The narrative is locked, canonical never re-anchored.

Verified: scene 653 (`VyBGG4po`, 2026-07-12 07:58 UTC). Narrative: *"I have corrected the record regarding Queen Rhaenyra's death. You are correct; she passed of old age, and I have removed the 'Ontological Shock' fr..."*. `state_updates.npc_data`: **absent for Queen Rhaenyra**.

Why this is a distinct sub-class: the god-mode agent treats the turn as "narrative freeze" (no story progression) and doesn't think it needs to write `npc_data`. The fix is to give the god-mode agent its own structured `## NPC Status` anchor in its system prompt.

### Sub-class 6: Wrong-key write / key-confusion

LLM writes `state_updates.npc_data[NPC_WITHOUT_CANONICAL_SUFFIX]` instead of `npc_data[NPC_WITH_CANONICAL_SUFFIX]`. The merge layer accepts fuzzy-key writes; canonical state retains BOTH entries with diverging statuses.

Verified: scene 628 (`TO5ErOMN`, 2026-07-12 04:08 UTC). The LLM was supposed to mark Queen Rhaenyra Targaryen as dead, but instead wrote to `npc_data["Queen Rhaenyra"]` (without "Targaryen") with `status: "__DELETE__"`. The canonical `npc_data["Queen Rhaenyra Targaryen"]` was unaffected by this turn.

Why this is a distinct sub-class: the merge layer's fuzzy-key acceptance (a separate bug) allows the LLM's key-confusion to silently leave both keys live. The fix is twofold — (a) prompt layer: tell the LLM the canonical NPC key explicitly via the `## NPC Status` block, (b) merge layer: tighten fuzzy-key acceptance (orthogonal fix on the backend).

## Scene-by-scene npc_data[Queen Rhaenyra*] table (the canonical diagnostic for this case)

| Scene | ts (UTC) | Doc ID (first 8) | What happened | `state_updates.npc_data[Queen Rhaenyra*]` write | Sub-class hit |
|---|---|---|---|---|---|
| 628 | 2026-07-12 04:08:53 | `TO5ErOMN` | God-mode retcon: "The Queen and Prince Daemon passed within a moon of each other in 156 AC" | `{"Queen Rhaenyra": {"status": "__DELETE__", "name": "Queen Rhaenyra"}}` — **wrong key, wrong value** | **WRONG-KEY WRITE (sub-class 6) + WRONG-VALUE WRITE (sub-class 2)** |
| 648 | 2026-07-12 07:52:30 | `4LnxX5Ei` | LLM narratively revives Queen: "paranoid / interrogation_ready, attitude: hostile" | `{"Queen Rhaenyra Targaryen": {"status": "paranoid / interrogation_ready", "attitude_to_party": "hostile"}}` | **WRONG-WRITE (sub-class 2)** — narrative revival 4h after god-mode death |
| 652 | 2026-07-12 07:57:29 | `K4dq7iC9` | God-mode forced: "The Death of the Dragon Queen" | `{"Queen Rhaenyra Targaryen": {"status": "dead", "health": {"hp_max": 75, "hp": 0}, "hp_current": 0, "hp_max": 75}}` | **CORRECT** (god-mode forced the canonical write) |
| 653 | 2026-07-12 07:58:52 | `VyBGG4po` | User: "queen is supposed to be dead but LLM forgot" → LLM admin-retcon narrative | **(no npc_data write at all)** | **GOD-MODE-RETCON MISSING-WRITE (sub-class 5)** |

## Why this isn't a per-scene bug

The campaign itself has a structural state-merge correctness issue — NOT a per-scene bug. The fix belongs at the prompt layer, not per-NPC bandaids. The minimum viable fix (per `npc-status-persistence-bug.md` "Fix shape", Option C):

```
## NPC Status (CANONICAL — must match this)
- Queen Rhaenyra Targaryen: status=dead, hp_current=0/75  ← canonical key
- Queen Rhaenyra: (minimal entry — NOT the canonical queen; do not write here)
- Prince Aemond Targaryen: status=[captured, stable, imprisoned], location=Dragonstone (The Dungeons), hp=1/45
```

This anchors the LLM against (a) writing `__DELETE__` to mark death, (b) narratively reviving dead NPCs without re-checking canonical, (c) writing to the wrong NPC key, and (d) silently dropping `npc_data[NPC]` writes on god-mode retcon turns.

## Diagnostic recipe (Python, no worktree required)

This is a **static-evidence repro** — no live LLM replay was triggered. Per `references/static-evidence-sufficient-no-live-turn.md`, the bug is observable entirely from pre-state + bug-origin story doc:

```python
import os, subprocess, json
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser("~/serviceAccountKey.json")
os.environ["WORLDAI_GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser("~/serviceAccountKey.json")
os.environ["WORLDAI_DEV_MODE"] = "true"

PY = "$HOME/projects/your-project.com/venv/bin/python"
code = '''
import json
from google.cloud import firestore
db = firestore.Client(project="worldarchitecture-ai")
UID = "<resolved_uid>"  # from scripts/campaign_manager.py find-user
CID = "xK3fp5XrV24oarIINTF7"

state_doc = db.collection("users").document(UID).collection("campaigns").document(CID)\
    .collection("game_states").document("current_state").get()
sd = state_doc.to_dict() or {}
nd = sd.get("npc_data", {}) or {}
queen_keys = {k: v for k, v in nd.items() if "queen" in str(k).lower() or "Queen" in str(k)}
print(json.dumps(queen_keys, indent=2, default=str))

# Most recent queen-mentioning story entries
story = sorted(
    db.collection("users").document(UID).collection("campaigns").document(CID).collection("story").stream(),
    key=lambda d: (d.to_dict().get("user_scene_number") or 0),
    reverse=True)
hits = []
for s in story:
    sd_ = s.to_dict() or {}
    narr = (sd_.get("narrative") or "") + " " + (sd_.get("text") or "")
    if "rhaenyra" in narr.lower() or "queen" in narr.lower():
        hits.append({
            "scene": sd_.get("user_scene_number"),
            "ts": str(sd_.get("timestamp")),
            "narrative_excerpt": narr[:300],
            "npc_data_writes": sd_.get("state_updates", {}).get("npc_data", {}),
        })
for h in hits[:8]:
    print(json.dumps(h, indent=2, default=str))
'''
subprocess.run([PY, "-c", code], env=os.environ, check=True)
```

## Sibling-campaign structural issue flag

This is the 7th confirmed sibling instance on `xK3fp5XrV24oarIINTF7` in 9 days. The campaign itself is a repro cluster for LLM state-merge correctness bugs. New issues against this campaign MUST link all 6 prior siblings in the body (per `repro` skill's sibling-campaign structural-issue flag rule).