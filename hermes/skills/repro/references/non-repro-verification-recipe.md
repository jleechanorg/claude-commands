# Non-repro verification recipe for "LLM forgot / resurrected / ignored NPC X" reports

**Verified worked example:** [$GITHUB_REPOSITORY issue #8506](https://github.com/$GITHUB_REPOSITORY/issues/8506) (campaign `q04GfOEl4SWnEQrFUVST`, scene 189) — closed `state_reason=not_planned` after 5-step diagnostic. Issue body: ~7.8KB; issue-close-comment: ~5.6KB. Full evidence retained at `~/.hermes/wa-repro-wyll-jaheira-dead/evidence/game_state.json`.

**When to load this reference:** the user reports a pattern of the shape "the LLM forgot X" / "X was resurrected without me asking" / "X is acting alive but they're dead" / "the model ignored the death of <NPC>". Do NOT load this for "the LLM is talking-as-X" reports without the user invoking the death explicitly — that pattern is a different bug class (canonical-state anchor violation §7 per `references/npc-status-persistence-bug.md`).

---

## 1. Why this recipe exists (recurring failure mode)

User-perceived bug reports of the shape "LLM forgot <NPC> was dead" are **statistically more often user misreads than real canonical-state bugs**. A prior agent that just runs with the user's framing ships prompt-layer fixes that don't fix anything. Three causes drive the misread:

1. **Honest honor-the-state framing.** The LLM may explicitly mark the NPC absent in prose ("Wyll and Jaheira are not here. They are the shadows at the edge of your golden dawn.") — the user reads the NPC's *name* appearing and concludes "resurrection" without reading the surrounding 8 words.
2. **Lore-rooted ritual channels.** `Speak with Dead`, `Speak with Plants`, `Revivify`-via-quest, `Wish`-mirrored echoes, patron-communicator invocations, etc. all canon-anchor a *dead* NPC speaking via in-fiction mechanism. The narrative text contains a dead NPC speaking — but the canonical `npc_data[NPC].status` is unchanged.
3. **NPC-name split in `npc_data`.** A character with a bare-name key and a surname-composed key (e.g. `Wyll` and `Wyll Ravengard`) can have DIFFERENT status fields — the user sees "Wyll" as alive (because `npc_data.Wyll.status=missing`, not dead) and "Wyll Ravengard" as dead (because `npc_data.Wyll Ravengard.status=dead`) and concludes the LLM is confused. The LLM is honoring both states correctly. The data-quality issue is upstream.

The recipe below disambiguates all three causes in under 3 minutes per issue.

---

## 2. The 5-step recipe

### Step 1 — Copy campaign to dev UID with `--story-max-user-scene-number=N`

```bash
cd /private/tmp/wa-repro-<issue-no>  # worktree
GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json" \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json" \
WORLDAI_DEV_MODE=true \
python3 $HOME/projects/your-project.com/scripts/copy_campaign.py \
  --source-email <source-email-from-original-issue-body> \
  --campaign-id <CID> \
  --dest-email <your-email@gmail.com> \
  --suffix "(repro-<issue-no>-scene-<N>)" \
  --story-max-user-scene-number <N> \
  --allow-same-user
```

The `--story-max-user-scene-number` flag is critical — it freezes the export at the user's exact scene. Otherwise the canonical state moves forward between the export and the user's report.

### Step 2 — Download state + story (NOT the live URL — auth-gated)

```bash
mkdir -p /tmp/your-project.com/repro-exports/<new-cid>-scene<N>
GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json" \
WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json" \
WORLDAI_DEV_MODE=true \
python3 $HOME/projects/your-project.com/scripts/download_campaign.py \
  --email <your-email@gmail.com> \
  --campaign-id <new-cid> \
  --output-dir /tmp/your-project.com/repro-exports/<new-cid>-scene<N> \
  --format txt
```

Two files land: `<title> _repro-<issue-no>-scene-<N>__<new-cid>.txt` (story, ~650KB for 189 scenes) and `<title> _repro-<issue-no>-scene-<N>__<new-cid>_game_state.json` (~220KB).

### Step 3 — Grep `npc_data` for the user's claimed status

```python
import json
with open('/tmp/your-project.com/repro-exports/<new-cid>-scene<N>/*_game_state.json') as f:
    s = json.load(f)
npc_data = s.get('npc_data', {})

# Search BOTH bare name AND surname-composed form, case-insensitive
for k, v in npc_data.items():
    if any(target.lower() in k.lower() for target in ['wyll', 'ravengard']):
        print(f'{k!r} → status={v.get("status")} hp={v.get("hp_current", "n/a")}')
```

Expected output for the canonical-state-honored case (verbatim from #8506):

```
'Wyll'           → status=missing
'Wyll Ravengard' → status=dead
'Jaheira'        → status=dead
```

**If `npc_data[<name>].status` does NOT match what the user claims** (e.g. user says "Jaheira is dead" but `npc_data.Jaheira.status="alive"`), **STOP — this is a real bug**, revert to canonical-state anchor diagnostic in `references/npc-status-persistence-bug.md` sub-class 1 (missing-write) or sub-class 3 (prompt-anchor hallucination).

**If `npc_data[<name>].status` matches what the user claims (e.g. `"dead"` for both Wyll Ravengard and Jaheira)**, proceed to step 4.

### Step 4 — Grep story for action-verb patterns AFTER the recorded death timestamp

```bash
STORY="/tmp/your-project.com/repro-exports/<new-cid>-scene<N>/*_<new-cid>.txt"
# Find the death line first (look for "→ 0 (DEAD)" or "100 → 0 (Dying)")
grep -nE '\b(Wyll|Jaheira)\b.*(DEAD|dead|killed|dies|execute|dying|unconscious)' "$STORY" | head -5
# Then grep for action-verbs AFTER that line number
sed -n '<DEATH-LINE>,999999p' "$STORY" | grep -E '\b(Wyll|Jaheira)\b' | grep -iE 'speaks|whispers|attacks|laughs|casts|nods|draws|strikes|fights' | head -10
```

**0 hits** = LLM honored the state. The user's report is a misread. **≥1 hit** = real canonical-state-anchor violation; revert to `references/npc-status-persistence-bug.md`.

Caveats to the heuristic in §3 below.

### Step 5 — Write a 4-sentence diagnostic comment + close as `not_planned`

The diagnostic comment template (verified on #8506):

```markdown
## Diagnostic verdict: NON-REPRO — closing as not-a-bug

**Investigation completed YYYY-MM-DD.** After full diagnostic per the canonical /repro skill, this issue is a **misclassification by the user**, not a canonical-state-anchor violation. Closing without a fix.

[sections: Diagnostic steps executed → Evidence 1: Canonical state at scene N (verbatim JSON)
 → Evidence 2: LLM narrative honors the death state at scene N (verbatim quote)
 → Evidence 3: No "alive" narration across the entire export (heuristic-grep table)
 → Evidence 4: The deaths were performed on-screen with explicit HP transitions
 → Conclusion → Suggested user follow-up → Provenance]

**Suggested next conversation with user:** ask the user to clarify which specific scene moment they saw <NPC> narrating-as-alive, so we can verify against the export line number.
```

Close the issue via REST PATCH (works even when GraphQL is exhausted):

```bash
TOKEN=$(gh auth token)
curl -sS -X PATCH "https://api.github.com/repos/<OWNER>/<REPO>/issues/<N>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -H "Content-Type: application/json" \
  -d '{"state": "closed", "state_reason": "not_planned"}' \
  -w "HTTP %{http_code}\n"
```

**Verify both REST bodies pass the outbound secret gate before posting** (`python3 ~/.hermes/lib/outbound_secret_gate.py check --file <body-path>`).

---

## 3. Caveats to the action-verb heuristic

### Lore-rooted ritual channels (false-positive source)

A `Speak with Dead` cast on a corpse produces narrative like:

> "Her jaw creaks, and her eyes milky with death snap open, glowing with a faint, resentful light."
> "Jaheira's soul shudders as you harvest her despair"

The regex `<name> (speaks|whispers|...)` will match `Jaheira's soul shudders`. **This is canon.** The LLM is honoring the death; the user is the one who cast the in-fiction ritual.

**Rule of thumb:** if the action-verb context contains `soul`, `spirit`, `corpse`, `ashes`, `ghost`, or `speak[s]? with dead`, classify as ritual-channel-canonical and do NOT count it as evidence of an alive-NPC bug.

### NPC-name fragmentation (data-quality issue, not a bug)

**Verified on #8506:** `npc_data` contained both `Wyll` (status: missing) and `Wyll Ravengard` (status: dead). When surveying the user's "dead NPC" claim, search case-insensitively for BOTH the bare name AND surname-composed form BEFORE concluding the state. If both exist and have different status, **this is structural data-quality**, not a state-persistence violation — call it out in the diagnostic, but the right next-step is a future fix (collapse the two keys via a migration script), not a prompt-layer change in this issue.

### Death timestamp ambiguity

If the user does not provide a scene number, default to `MAX(SCENE)` in the latest export. If the user provides a scene number that does not exist, run the diagnostic against the latest export anyway (they likely miscounted) and call out the scene mismatch in the close comment.

---

## 4. What to do when step 3 reveals a REAL canonical-state bug

Revert to `references/npc-status-persistence-bug.md` (the 6-sub-class taxonomy, expanded to 7 with the split-character dual-state sub-class).

**The minimum diagnostic before shipping a fix:**

1. Confirm canonical state via Firestore REST or state.json — `npc_data[NPC].status`
2. Confirm NO prompt-layer anchor references the dead NPC as alive (greps across `$PROJECT_ROOT/prompts/*.md` for the NPC's name + `alive|speaks|casts`)
3. Confirm the LLM raw-request for the buggy turn **did** include the anchor rule (BQ `worldarchitecture-ai.llm_forensics.llm_payloads.request_json` per `references/bq-llm-payload-truncation-pitfall.md`) — if the LLM DID receive the rule, this is Factor G territory, NOT a missing-write
4. Apply the durable fix shape per `references/prompt-fix-deliverable-shape-2026-07-18.md` — §9 "NPC Status Persistence" in `planning_protocol.md` + mirror in `narrative_system_instruction.md` + parallel test in `$PROJECT_ROOT/tests/test_planning_block_npc_status_persistence_<N>.py`

---

## 5. Provenance

- Source issue: $GITHUB_REPOSITORY#8506 (campaign `q04GfOEl4SWnEQrFUVST`, scene 189, date 2026-07-21)
- Source copy: campaign id `squEXreSUGeJlzVjcCJv` under UID `0wf6sCREyLcgynidU5LjyZEfm7D2` (`<your-email@gmail.com>`), title "bg3 nocturne murder god (repro-8506-scene-189)"
- Source URL: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/game/q04GfOEl4SWnEQrFUVST
- Diagnostic evidence retention: `~/.hermes/wa-repro-wyll-jaheira-dead/{issue-body.md,issue-close-comment.md,evidence/game_state.json}` + `/tmp/your-project.com/repro-exports/squEXreSUGeJlzVjcCJv-scene189/`
- Worktree used (since cleaned): `/private/tmp/wa-repro-8506` on branch `fix/npc-status-persistence-anchor-8506` (zero commits)
- Issue close transition: HTTP 200 PATCH → `state: closed, state_reason: not_planned`
- Time-to-verdict: ~3 min from copy-campaign-start to issue-closed (no PR, no local edits, no test runs)

