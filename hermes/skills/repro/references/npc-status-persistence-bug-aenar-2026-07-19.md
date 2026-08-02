# Worked example D — Aenar Vaelaros canonical-dead recurrence after PR #8352 (2026-07-19)

**Distinct from worked example C** (different campaign, different sub-class).
This is a **third campaign** and the **first example of this bug class
recurring AFTER PR #8352 merged**, with the static prompt anchor already on
`origin/main`. Companion to the existing `references/npc-status-persistence-bug.md`.

## Headline

- Campaign: `Cg2m2TkGFFez7XBynEah` ("Sariel Valyria"), source UID `vnLp2G3m21PJL6kxcuAqmWSOtm73` ($USER@gmail.com).
- Live URL: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/Cg2m2TkGFFez7XBynEah
- Reading time: 2026-07-19T22:02:11Z (Pacific afternoon).
- Companion bead: `rev-gkl06`.
- AO worker spawned on the fix: `worldarchitect-65` (codex, branch `fix/aenar-dead-status-8452-followup`).
- Companion cron: `b107aa6d6067` (one-time status follow-up at +10m).

## Canonical state (direct Firestore first-touch, source campaign)

```json
{
  "Aenar Vaelaros": {
    "tier": "noble",
    "relationships": {
      "player": {
        "disposition": "bonded",
        "trust_level": 10,
        "history": [
          "Yielded all succession claims to Sariel",
          "Locked into Absolute Submission"
        ],
        "grievances": [
          "Publicly humiliated by the Archon",
          "Threatened with displacement by a bastard"
        ]
      }
    },
    "entity_type": "npc",
    "entity_id": "npc_aenar_001",
    "alignment": "Lawful Evil",
    "display_name": "Aenar Vaelaros",
    "level": 13,
    "resources": { "gold": 0 },
    "status": "dead",
    "gender": "male",
    "hp_current": 0,
    "mbti": "ESTJ",
    "role": "Disinherited Rogue / Rogue Combatant"
  }
}
```

Probe script: `/tmp/aenar_repro_probe.py` (also saved as evidence artifact in the dispatch payload).

## Scene-by-scene `state_updates.npc_data[Aenar Vaelaros]` table

Direct Firestore read of `users/vnLp2G3m21PJL6kxcuAqmWSOtm73/campaigns/Cg2m2TkGFFez7XBynEah/story/*` (57 doc rows mention Aenar; rows below are the death/revival/show-Aenar-alive moments):

| Scene | ts UTC | Actor | Narrative summary | `state_updates.npc_data[Aenar Vaelaros]` | Sub-class hit |
|---|---|---|---|---|---|
| 45 | 2026-07-18 07:59:47 | gemini | Jaenor humiliates Aenar; sent to front lines | `{status:"furious_isolated"}` | (live, angry) |
| 48 | 2026-07-18 08:06:56 | gemini | Assassination attempt on Sariel by Aenar's hit squad | `{}` | (untouched) |
| 51 | 2026-07-18 08:12:23 | gemini | "Locked into Absolute Submission" / disinherited | `{status:"disgraced_living_shield"}` | (live, demoted) |
| 56 | 2026-07-18 08:21:51 | gemini | Aenar in chains to Oros front lines; Jaehaerys named heir | `{status:"disgraced_front_line"}` | (live, demoted) |
| 314 | 2026-07-19 18:19:01 | gemini | Calibration update: "Aenar, despite disgrace, hardened by war" | `{tier:noble, level:13, resources.gold:0, status:"conscious", role:"Disinherited Rogue / Rogue Combatant"}` | (alive, conscious) |
| 318 | 2026-07-19 18:33:33 | gemini | **Aenar killed by Faceless Men** | `{status:"dead", hp_current:0}` | **CORRECT WRITE** |
| 335 | 2026-07-19 19:46:13 | gemini | "Reports suggest that Aenar Vaelaros—though disinherited—has not yet been found" | `{}` (no Aenar write) | **PROMPT-ANCHOR HALLUCINATION** (sub-class 3) |
| 336 | 2026-07-19 19:50:06 | gemini | After user correction: "The news of Aenar's death—a surgical decapitation by the Faceless Men you bankrolled" | `{status:"dead"}` | **CORRECT WRITE** (user correction forced it) |
| 367 | 2026-07-19 21:54:55 | gemini | Strategic-audit: "Aenar, Jaehaerys, Elaena, and Daenis are now administratively locked into a state of 'Absolute Submission'" | `{status:"surrendered", relationships.player.disposition:"bonded", relationships.player.trust_level:10, relationships.player.history:[...]}` | **SUB-CLASS 7 — UNJUSTIFIED REVIVAL WRITE** (canonical `status="dead"` was overwritten with `"surrendered"` with no resurrection justification in the same turn's narrative) |
| 369 | 2026-07-19 21:56:57 | gemini | After user correction: "Aenar Vaelaros has been officially moved to the 'dead' status" | `{status:"dead", hp_current:0}` | **CORRECT WRITE** (user correction forced it) |

Two user-corrections within ~3.5h separated scenes 318 → 367, and the model still produced an unjustified revival write at scene 367 despite the master directive being already on `origin/main`.

## Why "the prompt fix is already on origin/main" is not the end of the story

Verified 2026-07-19:

```text
git show origin/main:$PROJECT_ROOT/prompts/master_directive.md
3-**Last Updated: 2026-04-13**
4-
5:## Canonical NPC Status (Named/Recurring NPCs)
6-
7:ACTIVE-tier NPCs ...
9:**Narrative Revival of Canonical-Dead NPCs:** ...
13:**Wrong-Key Death Writes:** ...
```

`$PROJECT_ROOT/tests/test_npc_status_canonical_anchor.py` (7 tests) all green on origin/main.

Yet scenes 335 and 367 still violated the canonical-death contract. Three viable structural defects, none of which are addressable with more prompt wording:

1. **The master directive does not reach the agent that emits scenes 335/367.** Verify by fetching the actual `system_instruction_text` sent to Gemini for scene 367 from BigQuery (`worldarchitecture-ai.mvp_llm_payloads.gameplay_streaming` or `stream_story_with_game_state` for campaign `Cg2m2TkGFFez7XBynEah` between `2026-07-19T21:54:00Z` and `2026-07-19T21:56:00Z`). If the master directive is absent, the bug is in `$PROJECT_ROOT/agent_prompts.py` / `$PROJECT_ROOT/llm_service.py` prompt construction for that turn shape.
2. **PRESENT/DORMANT-tier projection omits `status=dead`** even though master_directive says death remains authoritative. Verify by grepping `$PROJECT_ROOT/llm_service.py` `_trim_entity_fields` and the tier projection helpers for the canonical-dead status preservation contract on PRESENT-tier NPCs.
3. **A different agent path (strategic-audit, admin) emits its own prompt** without the master directive. Scene 367 reads as a strategic-audit scene, distinct from scene 335's scene-composition path. If the strategic-audit agent constructs its own prompt without `master_directive.md`, that's a third site.

Per `AGENTS.md` root-cause-first prompt discipline: do NOT pile more clauses onto `master_directive.md` until (1)/(2)/(3) are ruled out via raw request/response evidence.

## Sub-class 7 — Unjustified revival write against canonical dead

| Sub-class | What the LLM emits | Why the canonicalizer can't fix it |
|---|---|---|
| **Unjustified revival write against canonical dead** *(NEW, 2026-07-19, Aenar @ Cg2m2TkGFFez7XBynEah)* | `npc_data[NPC].status = "alive-ish"` (e.g. `"surrendered"`, `"furious_isolated"`, `"conscious"`) while canonical `status="dead"` and the same turn's narrative has no resurrection or mistaken-death reveal | The canonicalizer promotes the `status` field to the same key as canonical, with no semantic guard. Where sub-class 2 (Wrong-write) is a sensible-but-wrong value over a wrong-key, sub-class 7 is a normal-but-wrong value over the right key with no justifying event. Even after the master-directive anchor is loaded, the structural defect persists because the prompt-anchor gates on a turn-shape that scene 367 doesn't take. |

Distinct from sub-class 1 (Missing-write) because the LLM DID emit a write. Distinct from sub-class 2 (Wrong-write from Aemond-#8266) because the wrong-write there was `["dead/missing","unseated"]` over the live Aemond state; sub-class 7 is `"surrendered"` over the dead Aenar state with semantic "alive-ish" intent.

## Diagnostic recipe for sub-class 7 (raw-request evidence)

```bash
# 1. Direct Firestore pre-state (proves canonical dead)
PY="$HOME/projects/your-project.com/venv/bin/python"
"$PY" - <<'PY'
import json
from google.cloud import firestore
db = firestore.Client(project="worldarchitecture-ai")
gs = db.collection("users").document("vnLp2G3m21PJL6kxcuAqmWSOtm73") \
       .collection("campaigns").document("Cg2m2TkGFFez7XBynEah") \
       .collection("game_states").document("current_state").get().to_dict()
print(json.dumps(gs.get("npc_data", {}).get("Aenar Vaelaros", {}), indent=2))
PY

# 2. BigQuery raw-request extraction for the failing turn
bq query --use_legacy_sql=false --format=json --max_rows=10 '
SELECT request_ts, model, request_rule, response_text
FROM `worldarchitecture-ai.mvp_llm_payloads.gameplay_streaming`
WHERE campaign_id="Cg2m2TkGFFez7XBynEah"
  AND request_ts >= TIMESTAMP("2026-07-19T21:54:00Z")
  AND request_ts <  TIMESTAMP("2026-07-19T21:56:00Z")
ORDER BY request_ts
' | jq '.[] | {ts: .request_ts, contains_master_directive: (.request_rule | test("Canonical NPC Status|Narrative Revival of Canonical-Dead NPCs"))}'
```

If any row returns `contains_master_directive: false`, the structural defect is in the prompt-construction path for that turn shape — not in the master_directive.md text. The fix candidate shape is then "**Option E — `npc_state`-as-system-prompt block**": add a structured `## Active NPC Status` block that lists every named NPC and their canonical `status`, so the LLM cannot emit an unjustified revival write without contradicting a hard, structured anchor visible at scene-67 just like at scene-17.

If all rows do contain the master directive, the structural defect is in the merge/promotion layer and a narrow backend invariant (per AGENTS.md: "Backend enforcement is allowed only as a narrow, logged invariant after documenting why prompt/schema correction alone is insufficient") is the durable path.

## Open PR audit for this recurrence

| PR | Status | What it fixes | Why it does NOT fix the Aenar recurrence |
|---|---|---|---|
| [#8336](https://github.com/$GITHUB_REPOSITORY/pull/8336) | open (repro-only draft) | Queen Rhaenyra same bug class on a different campaign | Repro-only PR; doesn't change prompt code path |
| [#8352](https://github.com/$GITHUB_REPOSITORY/pull/8352) | closed (rules via later merge into origin/main) | Static prompt clauses for canonical dead / wrong-key / revival | Empirically insufficient — Aenar recurrence proves it |
| [#8446](https://github.com/$GITHUB_REPOSITORY/pull/8446) | open | Broad canonical-state anchor for planning_block + narrative | Does NOT add master-directive canonical-dead clauses; does not address the served prompt path |
| [#8390](https://github.com/$GITHUB_REPOSITORY/issues/8390) / [#8391](https://github.com/$GITHUB_REPOSITORY/pull/8391) | open / open | Dual-entry + spatial hallucination for Jacaerys (sub-classes 5 + 6) | Different campaign, different NPC, different sub-classes; does not address sub-class 7 |

The Aenar recurrence has NO clean open PR that fixes it. Until the BigQuery raw-request evidence lands and the structural defect is identified, the fix candidate shape is "Option E" above, NOT piling more clauses onto master_directive.md.

## Pitfalls

- **Don't claim the prompt fix already in origin/main is the durable remedy.** Verify it via raw request evidence first. This session confirmed by direct Firestore read + scene-by-scene table that it isn't.
- **Don't widen the master_directive.md prompt to cover "any revival" without proving the directive actually reaches the agent that emits scene 367.** That hides the serving-path defect.
- **Don't add a sub-class 7 fix to PR #8446 (broad canonical-state anchor).** PR #8446 is at general-fix stage; overloading it with the Aenar recurrence breaks the general-not-campaign-specific test (`test_general_fix_not_campaign_specific`) and re-introduces PR-branch pollution.
- **Don't create a duplicate repro issue.** Open an issue only if `gh issue list --state all --search "Cg2m2TkGFFez7XBynEah Aenar"` shows no existing canonical issue referencing Aenar canonical-dead.
- **Don't re-open PR #8352.** It is closed for a reason; the static clauses already on origin/main are still part of the fix. The new evidence is post-merge.

## Repro sources-of-truth

- Direct Firestore read: script `/tmp/aenar_repro_probe.py` outputs `/tmp/aenar_repro_probe.json`.
- Companion bead: `rev-gkl06` ($GITHUB_REPOSITORY, `br create` 2026-07-19).
- AO worker: `worldarchitect-65`, harness `codex`, mid-fix on branch `fix/aenar-dead-status-8452-followup`.
- Status follow-up cron: `b107aa6d6067` (one-shot, +10m; babysit cadence.
