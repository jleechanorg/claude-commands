---
name: convergent-bug-triage
version: 1.4.0
description: Triage when a single campaign (or single LLM/prompt surface) has accumulated multiple sibling bug investigations — the prompt-discipline family where "LLM emits right structured field, render/persistence/propagation path drops it", the now-merged NPC-status persistence family where "LLM omits/writes-wrong `state_updates.npc_data[NPC]`", AND the canonical-state-anchor family where "LLM forgets what canonical `core_memories` / faction / NPC already established" (the LLM re-derives or contradicts canon). Trigger on /repro requests where session_search reveals 3+ sibling issues on the same campaign within 24h OR 5+ within 9 days, "is this a duplicate", "this feels like the same bug as #X", "is this related to other bugs? what's in core memories?", "LLM forgot X", "LLM ignores Y", "LLM forgot my dad is dead", "LLM re-narrated dead NPC", or when gh issue list shows N issues against the same campaign in one day. Updated 2026-07-20 to add the canonical-dead-NPC revival sub-class (scene 492 on `EROaUnSbmDhqBedTbJMg`, issue #8472 / PR #8473), the 3-layer durable-fix architecture (narrative-emit / state-update / planning-block), and the resurrection-exception pattern.
tags: [worldarchitect, repro, prompt-discipline, bug-class, npc-status-persistence, canonical-state-anchor, canonical-dead-npc-revival, 3-layer-durable-fix, sibling-campaign-cluster, deployed-vs-branch-state]
---

# Convergent Bug Triage

When a single campaign (or single LLM/prompt surface) has accumulated **3 or more sibling bug investigations within a 24h window**, the dispatcher is not looking at a single bug — they are looking at a **bug class with N surface symptoms**. Filing each as an isolated PR creates cascade churn; bundling them creates mixed-scope PRs that stall on review. This skill covers the triage decision tree.

## When this skill fires

- A `/repro` request lands on a campaign ID where `gh issue list --repo <OWNER>/<REPO> --state all --limit 50` shows ≥3 issues opened against the same campaign in the last 24h, OR ≥5 within 9 days.
- The user asks **"is this related to other bugs?"** AND **"what's in core memories?"** — this is the canonical-state-anchor question pattern (see Pitfall 9); route here after confirming ≥3 siblings exist.
- The user describes a symptom where the LLM "forgot", "ignored", or "contradicts" canonical state — `core_memories`, `npc_data.<NPC>.status`, faction control, NPC co-presence, scene history — even when the served prompt context likely contains the anchor.
- The issues share a family pattern even when their surfaces differ — e.g. "Aemond capture persistence", "queen-level-14 directive", "scene event not rendered", "NPC status propagation", "lineage canonicalization" are 5 different surfaces but they all reduce to **"LLM emits correct structured field; render/persistence/propagation path drops it."**
- The operator's instinct is "is this a duplicate?" — the answer is usually NO, but a sibling that should cross-reference.

## The five-step triage

### 1. Classify the new symptom into the family

Load the candidate symptoms for the campaign:

```bash
gh issue list --repo <OWNER>/<REPO> --state all --limit 30 \
  --json number,title,state,labels,createdAt \
  --jq '.[] | select(.createdAt > (now - 86400 | strftime("%Y-%m-%dT%H:%M:%SZ"))) | "\(.number) [\(.state)] \(.title)"'
```

For each issue in the last 24h, ask: **does the bug reduce to "structured field present, downstream path drops it"?**

| Symptom surface | Field written correctly by LLM? | Drop happens in... |
|---|---|---|
| Aemond capture persistence (status=`captured`) | Yes | `npc_data` persistence path |
| Queen-level-14 directive | Yes (or never written by parser) | `state_updates.god_mode_directives` save path |
| Scene event `companion_request` in narrative | Yes | render path (narrative_integration vs narrative) |
| NPC narrative status propagation | Sometimes | `state_updates.npc_data` write path |
| Lineage canonicalization | Sometimes | `player_character_data_extras` move path |
| **NPC status persistence — god-mode-retcon missing-write** (added 2026-07-12, #8335) | No — god-mode agent emits admin-retcon narrative but **never writes `npc_data`** because it is locked into "narrative freeze" mode | prompt layer — god-mode agent needs a structured `## NPC Status` anchor in its system prompt too, not just the gameplay agent |
| **NPC status persistence — wrong-key write / key-confusion** (added 2026-07-12, #8335 scene 628) | Yes but to wrong NPC key (e.g. `Queen Rhaenyra` instead of `Queen Rhaenyra Targaryen`) | prompt layer + state layer — fuzzy-key writes accepted by merge layer; canonical state retains both keys with diverging statuses |

If the new symptom also fits the family: it is a **sibling**, NOT a duplicate. File a new issue with explicit cross-references.

> **Note on the 9-day / N-instance cluster pattern (added 2026-07-12):** the original trigger of "3+ in 24h" misses the most common shape — a campaign that accumulates 1-2 issues per day across many days because the underlying bug class is structural, not per-scene. The trigger threshold should be **`≥5 issues against the same campaign in any 9-day window`** in addition to the original 24h rule. The 2026-07-12 repro of "queen is supposed to be dead but LLM forgot" was the **7th sibling** on `xK3fp5XrV24oarIINTF7` over 9 days; ruling it out as "just another scene bug" because no other issues opened today would have been wrong.

> **Note on the 7+ sibling floor (added 2026-07-19):** the canonical-state-anchor family on `Cg2m2TkGFFez7XBynEah` accumulated **8 siblings in 24h** (scenes 78/82/171/318/335/367/369/386/392). At this density, the durable fix is **already in PR branches but unmerged** — see Pitfall 8's three-check pre-flight. Filing per-scene issues beyond the 5th sibling is almost always wrong; the correct action is to flag the deployment gap (existing PRs not on origin/main) and request merge approval.

### 2. Decide sibling-vs-bundle vs duplicate

| Pattern | Decision | Why |
|---|---|---|
| Same root mechanism, different surface, different files | **Siblings — N parallel PRs** | Mixed-scope PRs stall on review; bundling conflates measurement-integrity and structural changes |
| Same root mechanism, same surface, same file | **Duplicate — fold into existing PR** | One fix covers both; second PR is churn |
| Different root mechanism, same surface | **Siblings — parallel PRs** | Different root = different fix; bundling forces reviewer to accept unrelated trade |
| Different root mechanism, different surface | **Different class entirely — file normally** | Not in scope for this skill |

The default for the prompt-discipline family is **siblings, one PR per symptom**. Each PR owns its own file/section.

### 3. Cross-reference in the new issue body

Open the new issue with explicit cross-references in a "Sibling investigations" section:

```markdown
### Sibling investigations on the same campaign (today)

- #8160 (closed dup) — character-creation spells/abilities
- #8266 / PR #8267 (closed) — Aemond capture persistence
- #8275 / PR #8276 (open scaffold) — queen-level-14 god-mode directive
- PR #8271 (open) — NPC narrative status propagation in $PROJECT_ROOT/prompts/game_state_instruction.md
- PR #8265 (open) — lineage canonicalization
- #8277 (this issue) — scene_event not rendered into narrative

All five share the same family: LLM emits correct structured field, downstream path drops it.
```

Without these refs the next dispatcher will re-investigate from scratch.

### 4. Dispatch ONE AO worker per sibling, not a fan-out

Even when the family is clear, dispatch **one AO worker per sibling issue** — do NOT fan out N workers for N siblings in one shot. Why:

- Each PR's GREEN fix is in a different file (`living_world_instruction.md` vs `game_state_instruction.md` vs `world_logic.py` vs `game_state.py`). Parallel workers will step on each other's edits.
- Each PR has its own `/es` evidence requirement (real-LLM replay with the new prompt on a copy campaign). Two parallel `/es` replays on the same campaign compete for the same test copy.
- The operator can read the first PR's GREEN before deciding whether the second sibling's fix recipe is even right.

**Order of dispatch:** file the issue → spawn the worker → wait for the worker's PR to reach a verdictable state → then dispatch the next sibling. Use a 1-worker babysit cron, not N workers in parallel.

### 5. In the AO worker brief, force a "step around siblings" clause

When the new symptom is a sibling, the worker MUST NOT touch files owned by sibling PRs. Encode this in the brief:

```markdown
## Files to NOT touch (sibling PRs own these)

- $PROJECT_ROOT/prompts/game_state_instruction.md — PR #8271 owns
- $PROJECT_ROOT/game_state.py — PR #8265 owns
- $PROJECT_ROOT/world_logic.py — PR #8276 owns the god-mode save path
- Any branch in the Sibling investigations list above — DO NOT rebase onto, cherry-pick from, or merge with
```

The worker reading this brief won't waste cycles asking "should I also fix the lineage bug?" — the brief already says no.

## The canonical-state-anchor family (added 2026-07-19)

A third bug family has emerged distinct from prompt-discipline and NPC-status persistence. Triggered when the LLM emits prose that contradicts **canon already established in `core_memories`, faction rules, NPC `status`, or location/state co-presence** — even when those facts are present in the served prompt context.

| Sub-class | Symptom | Canonical anchor the LLM forgot |
|---|---|---|
| **Magic-sensor / invention** | "Vaelaros-tuned Blood-Scent focus", "frequency-sensitive ward", "draconic resonance detection", "Reaver-Hounds", "Ghost-Hunter" | `custom_campaign_state.rule` explicitly forbids magical tracking; setting is non-/low-magic |
| **NPC status erased** | "Aenar would sabotage your success" while Aenar is `status="disgraced_front_line"` / `status="dead"` | `npc_data.<NPC>.status` |
| **NPC co-presence violated** | "Rejoin the Host" choice presupposes Aegon at Mander mouth while canonical state has him co-present at Highgarden | `entity_tracking.active_entities[].status.location` |
| **Faction-control anchor** | "the Iron Bank in control" emitted without validating who actually controls the Iron Bank per `core_memories` section 5 | `core_memories` section anchor |
| **Argella-suspicion continuity** | Scene 386 should reference Argella's earlier "you are more than you seem" suspicion but the planning_block drops it | `narrative_history.remove` of earlier scenes that established the suspicion |
| **Canonical-dead-NPC revival** (added 2026-07-20, #8472) | "Archon Jaenor Vaelaros (Lvl 20) stands at the base of the dais, his heavy signet ring extended in a trembling hand" while `npc_data["Archon Jaenor Vaelaros"].status = "dead"` and `hp_current = 0` | `npc_data.<NPC>.status == "dead"` + `hp_current == 0` + `core_memories[N].rule` re-affirms death |

**Canonical-dead-NPC revival recipe (verified 2026-07-20, scene 492, campaign `EROaUnSbmDhqBedTbJMg`, issue #8472, PR #8473):**

User verbatim: *"My dad is dead why did you forget"* (turn 493 after LLM narrated `Archon Jaenor Vaelaros` as physically present extending his signet ring at the Consular Coronation).
Model self-admission (scene 493): *"Administrative Correction: Archon Jaenor Vaelaros is canonically deceased. I have corrected the game state and added a persistent directive to ensure he no longer appears in the narrative. The previous turn's description of him at the coronation was a continuity error."*
Canonical contradiction: `npc_data["Archon Jaenor Vaelaros"].status = "dead"`, `hp_current = 0`, `core_memories[363]` + `[392]` re-affirm *"Archon Jaenor is dead; Sariel has ascended as God Empress"*.

The 7 forbidden-pattern categories the durable fix must enumerate (each maps to a scene-492 example):

1. **Physical presence** — "stands at the base of the dais" while dead
2. **Hand-object action** — "extends his signet ring" / "presses his signet into the wax"
3. **Voicing dialogue** — direct line from a dead NPC
4. **Vehicle/dragon/mount operation** — "Jaehaerys rode Vermax toward..." when rider dead
5. **Physical posture** — kneeling / bowing / leaning / sitting
6. **Multi-NPC group activity with present-tense verbs** — "feared your father's indifference" presupposes father's current existence
7. **Artifact custody transfer** — "Jaenor yields the signet ring" (transfer of one's own artifact requires physical agency)

**Resurrection exception (verified 2026-07-20):** the rule must explicitly enumerate when a canonical-dead NPC's physical presence IS permitted. Verified shape from PR #8473:
- Same-turn `state_updates.npc_data.<npc_id>` write must (a) remove `"dead"` from the status list, (b) restore `hp_current > 0`, AND (c) provide explicit narrative justification (resurrection ritual, confirmed mistaken-death reveal, spiritual return).
- The justification MUST appear in the same turn's `state_updates` AND the same narrative block — a deferred resurrection is not a resurrection.
- The planning_block mirror must DROP (not hedge) any choice whose premise requires a canonical-dead NPC's presence without the resurrection write.

**Verified 8 instances on `Cg2m2TkGFFez7XBynEah` over 24h (2026-07-18 → 2026-07-19):**
- #8438 / PR #8439 — Blood-Scent focus / Vaelaros-tuned silver vial (scene 78, magic-sensor invention)
- #8440 / PR #8441 — Inquisition choice emits despite retcon (directive vs prose)
- #8442 — MBTI / Alignment leak (internal-only vs player-facing)
- #8444 / PR #8445 — Aegon Mander-mouth while co-present at Highgarden (NPC co-presence)
- #8451 / PR #8452 — "frequency-sensitive ward" / "Ghost-Hunter" / "Reaver-Hounds" (scene 171, magic-sensor invention)
- "Aenar is dead" follow-up — dispatched via AO worker `worldarchitect-65`, bead `rev-gkl06` (NPC status)
- "Argella suspicion scene 386" — repro session `20260719_160921_3faa1909` (continuity)
- "Iron Bank in control scene 392" — repro session `20260719_160921_...` continuation (faction-control anchor)

**Durable-fix shape:** add a §"NPC CANON ANCHORING (MANDATORY)" section to `$PROJECT_ROOT/prompts/narrative_system_instruction.md` that mandates anchoring every NPC behavior/prop/equipment to `core_memories`, the entity manifest, and `npc_data`; AND add §"Canonical-State Anchor" to `$PROJECT_ROOT/prompts/planning_protocol.md` covering NPC Co-Presence / God-Mode Directive Compliance / NPC Reachability / NPC Status Alignment.

**Two PRs already contain the durable fix but NEITHER is on `origin/main`:**

| PR | Branch | Status | Contains |
|---|---|---|---|
| [PR #8443](https://github.com/$GITHUB_REPOSITORY/pull/8443) | `fix/narrative-anti-tracking-prompt-rule` | OPEN, NOT DRAFT, mergeable=true | NPC CANON ANCHORING + Anti-Invented-Artifact + 17 follow-up commits (incl. `b7b2620671` "prioritize explicit canon over stale memories", `dd5f94b279` "preserve NPC canon rule through compaction") |
| [PR #8445](https://github.com/$GITHUB_REPOSITORY/pull/8445) | `fix/aegon-rejoin-co-presence-8444` | CLOSED (branch alive, head `ff419d7a7`) | Commit `4524525569` adds §"Canonical-State Anchor" to `planning_protocol.md` |

**This is the deployed-vs-branch-state gap** — the deployed DEV bundle is still serving prompts WITHOUT either rule because neither commit is on `origin/main` (HEAD `444c83d825`). The LLM is forgetting canonical state because the fix exists in PR branches but hasn't shipped. See Pitfall 8 for the pre-flight check.

## Pitfalls

### Pitfall 1: Treating siblings as duplicates

Bug-ref: 2026-07-08 — issue #8160 on campaign `xK3fp5XrV24oarIINTF7` was closed as "duplicate of #7885" but the two symptoms (character-creation spells vs scene-event rendering) are different root mechanisms. The cross-campaign audit never happened because the duplicate closeout skipped the investigation. **Rule:** if the user describes a NEW user-visible symptom on the same campaign, file a new issue. The triage step above decides if it's truly duplicate, not surface similarity.

### Pitfall 2: Bundling siblings into one PR

A common anti-pattern is "since these are all prompt-discipline, let me fix all five in one PR." This stalls because:
- Reviewer accepts the smallest fix and asks to split the rest
- /es evidence covers only one symptom, not all five
- Green-gate /er verdict is per-symptom, mixed verdicts block merge
- Conflict surface grows — each sibling's GREEN rewrite touches adjacent prompt fields

### Pitfall 3: Conflating the prompt-discipline family with state-persistence family

Two distinct families share surface similarity:

- **Prompt-discipline family** (this skill): LLM emits the right structured field; downstream path drops it. Fix is in `$PROJECT_ROOT/prompts/<X>.md` field definitions and ESSENTIALS rules.
- **State-persistence family**: LLM emits correct structured field; server-side persistence re-asserts a stale value. Fix is in `$PROJECT_ROOT/world_logic.py` or `$PROJECT_ROOT/game_state.py` save paths.

If the bug surface looks like prompt-discipline but the actual root is a backend override (e.g. Factor D from issue #7453 — "LLM commits level=14 but state shows different"), the fix is in backend code, not the prompt. The triage step that distinguishes them: read the corresponding BQ `llm_forensics.llm_payloads` row — does the LLM request actually contain the corrected value? If yes, it's prompt-discipline. If the response contains it but Firestore state doesn't, it's state-persistence.

## Reference

- `references/2026-07-08-xK3fp5XrV24oarIINTF7-sibling-table.md` — worked example: 4 sibling investigations + 2 sibling-PRs on the same campaign in one day, all reduced to one root family with 5 different surfaces
- `references/2026-07-12-xK3fp5XrV24oarIINTF7-queen-death-sibling-8335.md` — worked example: 7th sibling on the same campaign over 9 days; introduces the god-mode-retcon missing-write and wrong-key write sub-classes; full scene-by-scene npc_data table + diagnostic recipe
- `references/2026-07-19-Cg2m2TkGFFez7XBynEah-canonical-state-anchor-cluster.md` — worked example: 8 canonical-state-anchor siblings on the Sariel Valyria campaign in 24h (Blood-Scent / Vaelaros-tuned / frequency-shield / Reaver-Hounds / Aenar-dead / Argella-suspicion / Iron-Bank-in-control); introduces the "durable fix exists in unmerged PR branch" pre-flight (Pitfall 8), the "what's in core memories" answer shape (Pitfall 9), the `custom_state_keys == []` architectural-gap diagnostic (Pitfall 10), and the deployed-vs-branch-state gap (PR #8443 + PR #8445's commit `4524525569` not on `origin/main`)
- `references/2026-07-20-EROaUnSbmDhqBedTbJMg-canonical-dead-npc-revival-8472.md` — worked example: 5th sibling on `EROaUnSbmDhqBedTbJMg` (scene 492 Archon Jaenor Vaelaros at coronation, issue #8472 / PR #8473); introduces the canonical-dead-NPC revival sub-class (Pitfall 11's 3-layer architecture: state-update + narrative-emit + planning-block), the 7 forbidden-pattern categories, the resurrection exception, and the twin-clone workflow for scene-by-scene regression evidence
- `~/.hermes/skills/repro/SKILL.md` — thin pointer to the canonical /repro workflow
- `~/.hermes/skills/repro/references/npc-status-persistence-bug.md` — 6 sub-classes of the NPC-status persistence family; canonical worked examples A/B; scene-by-scene table diagnostic; Option C fix shape (structured `## NPC Status` block in system prompt)
- `~/.hermes/skills/repro/references/repro-llm-invented-lore-artifacts-2026-07-18.md` — the bug-class-4 (LLM-prose invention) durable fix (NPC Development section in `narrative_system_instruction.md`); the canonical-state-anchor family's magic-sensor sub-class is the same root cause
- `~/.hermes/skills/repro/references/repro-planning-block-and-campaign-cluster-2026-07-18.md` — the 5-anchor taxonomy for planning_block canonical-state violations (NPC co-presence / God-Mode Directive Compliance / NPC Reachability / NPC Status Alignment); the planning-block emit side of the canonical-state-anchor family
- `~/.hermes/skills/hermes-imports/dispatch-task/SKILL.md` — AO worker dispatch mechanics (now patched with 20-session-cap and GitHub-rate-limit preflight gates)
- `~/.claude/skills/root-cause-first/SKILL.md` — backend-enforcement avoidance for prompt-discipline fixes

### Pitfall 4: Confusing campaign convergence with daily-cron regression

The campaign-convergence pattern (this skill) and the daily-cron-failure pattern (sibling skill `wa-daily-cron-failure-diagnosis`) overlap on the SAME campaign but are different classes of investigation:

- **convergent-bug-triage (this skill):** user-visible behavior on the campaign is broken — directives ignored, lineage erased, scene events dropped. Fix surface is in `$PROJECT_ROOT/prompts/*.md` or `$PROJECT_ROOT/world_logic.py`.
- **wa-daily-cron-failure-diagnosis:** GCP cron job exits 1 because the audit script can't parse the LLM's dice rolls. Fix surface is in `scripts/audit_dice_rolls.py` + structural fix #7695.

Both classes hit the same campaigns (e.g. `xK3fp5XrV24oarIINTF7` / Visenya v7 has been touched by 6+ PRs in BOTH classes in the last 24h). When diagnosing, classify first, then route to the right skill. Cross-references the sibling investigations don't substitute for one — you must apply each skill's protocol separately, in sequence.

**Rule:** if the trigger is a `[GCP Cron] ... - FAIL` email or a FAIL in `~/.cache/wa_daily_test_watcher/<job>/YYYY-MM-DD.posted`, load `wa-daily-cron-failure-diagnosis` first. If the trigger is a `/repro` request about user-visible campaign behavior with 3+ sibling issues, load this skill first. Don't try to handle both classes with one protocol — they have different fix surfaces and different dispatch templates.

### Pitfall 5: `gh api` GraphQL rate limit vs REST API (added 2026-07-12)

When the diagnostic step tries to enumerate sibling issues via `gh issue list --repo X --search "..."`, the GraphQL-backed `gh` CLI frequently returns `GraphQL: API rate limit already exceeded for user ID <N>` even when REST endpoints still have budget. Verified 2026-07-12: rate-limit fired at the start of a 6-issue triage on `$GITHUB_REPOSITORY` while REST API still worked.

**Workaround (Python, no `gh` dependency):**
```python
import urllib.request, json
req = urllib.request.Request(
    "https://api.github.com/search/issues?q=<KEYWORD>+repo:<OWNER>/<REPO>+type:issue&per_page=30",
    headers={"Accept": "application/vnd.github+json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    items = json.loads(resp.read().decode()).get("items", [])
```

For PR creation, use the REST API directly with a token from `~/.config/gh/hosts.yml` (parse the `oauth_token:` line). This bypasses the `gh` CLI's rate-limited path entirely. Use this fallback in any triage that needs to file issues + create draft PRs in one batch.

### Pitfall 6: Branch must exist on origin before `gh pr create` will accept it (added 2026-07-12)

The "branch-not-on-origin" failure mode is subtle and has two distinct error messages that look unrelated:

1. **422 Validation Failed `{"field": "head", "code": "invalid"}`** — the head ref doesn't exist on the remote.
2. **422 Validation Failed `{"message": "No commits between main and <branch>"}`** — the branch exists but is at the same SHA as `main`.

The fix is the same sequence: `git worktree add` with `-b <branch> origin/main` → `git push -u origin <branch>` (even if it's empty — push just creates the ref) → commit evidence files → push again → THEN call the PR API. **Don't try to skip the empty-push step** — the API checks `origin/<branch>` before it accepts the request, even for a no-commit branch.

### Pitfall 7: Confusing the NPC-status persistence family with prompt-discipline (added 2026-07-12)

The NPC-status persistence family (worked example: campaign `xK3fp5XrV24oarIINTF7`, 6+ siblings over 9 days) superficially looks like prompt-discipline (LLM emits wrong narrative) but is structurally different:

| Family | LLM behavior | Fix surface |
|---|---|---|
| **Prompt-discipline** | Emits correct structured field; downstream path drops it | `$PROJECT_ROOT/prompts/<X>.md` field definitions + ESSENTIALS rules |
| **NPC-status persistence** | Emits narrative but **no/wrong `state_updates.npc_data[NPC]` write**, OR writes to wrong NPC key, OR god-mode agent doesn't write at all | Prompt layer — needs structured `## NPC Status` block as system-prompt anchor (Option C from `~/.hermes/skills/repro/references/npc-status-persistence-bug.md` "Fix shape") |

The 6 known sub-classes of NPC-status persistence (as of 2026-07-12): missing-write, wrong-write, prompt-anchor hallucination, confused-state `with`/`replace`, **god-mode-retcon missing-write**, **wrong-key write**. All six have the same fix shape — pre-render every known NPC's current status as a structured block in the system prompt. The god-mode sub-class is the trickiest because the god-mode agent treats its turn as "narrative freeze" and doesn't even consider writing `npc_data`; it needs its own system-prompt anchor.

**Cross-reference (sibling references):** `~/.hermes/skills/repro/references/npc-status-persistence-bug.md` holds the worked examples and the diagnostic (scene-by-scene `npc_data[NPC]` write table).

### Pitfall 8: Durable fix exists in unmerged PR branch — check before filing N+1 sibling (added 2026-07-19)

When the cluster signal fires (≥3 siblings on same campaign), the **first check** before filing a new issue is to scan existing PRs/branches for the durable fix. If the fix is sitting in an open or closed-but-branch-alive PR, the correct action is **merge the existing branches, not file a new issue**.

**Three-check pre-flight (run BEFORE filing):**

```bash
# 1. Find the canonical-state-anchor commit/PR (or any prompt-fix commit matching the bug family)
cd <repo>
git log --all --oneline --grep="Canonical-State\|NPC CANON\|canon-state\|NPC canon\|NPC.*anchor" --since="<campaign-first-sibling-date>"
git log --all --oneline --grep="magic-sensor\|anti-invent\|anti-tracking\|forbidden invention"

# 2. For each candidate commit, find which branch + PR owns it
COMMIT=<candidate-sha>
git branch --contains $COMMIT -a
gh pr view <candidate-PR-number> --repo <OWNER>/<REPO> --json number,title,state,draft,headRefName,baseRefName,mergeable,url

# 3. Confirm the commit is NOT on origin/main
git log origin/main --oneline | grep -E "<short-sha>|<commit-subject-words>"
```

**Decision matrix:**

| Check 1 (commit found) | Check 2 (PR found) | Check 3 (on main) | Action |
|---|---|---|---|
| ✅ | ✅ OPEN | ❌ NOT on main | Comment on PR requesting merge review + cross-link this N+1 sibling |
| ✅ | ✅ CLOSED (branch alive) | ❌ NOT on main | Reopen PR OR cherry-pick onto fresh `feat/<topic>` from origin/main |
| ✅ | ✅ MERGED | ✅ ON main | This is a NEW bug — file issue normally; the existing fix doesn't cover this sub-class |
| ❌ | ❌ | n/a | No existing durable fix — branch a fresh worktree for root-cause-first prompt fix |

**Why this matters:** filing N+1 per-scene issues when the durable fix is sitting in an unmerged PR is **churn**. The user will keep hitting the same canonical-state-anchor bug class because the deployed prompts haven't changed. The fix has been waiting — sometimes for days — for someone to merge the PR branch to `origin/main`.

**Verified case 2026-07-19 (campaign `Cg2m2TkGFFez7XBynEah`, scene 392 "Iron Bank in control"):** the LLM forgets canonical state because PR #8443 + PR #8445's commit `4524525569` exist in branches but neither is on `origin/main`. Filing a 7th per-scene issue would have been wrong; the correct response is to flag the deployment gap and request `MERGE APPROVED` on the existing branches.

**PR-closed-but-branch-alive detection (added 2026-07-19):** a PR can be closed without merge, leaving the fix branch alive and reachable via `git fetch origin <branch>`. Always check the branch state alongside the PR state:
- `gh pr view <N> --json state` returns `CLOSED` (the PR was closed)
- `git branch --contains <fix-commit> -a` shows `remotes/origin/fix/<topic>` is still alive
- → the fix is reachable; reopen the PR or cherry-pick onto a fresh branch

**Wrong JSON field-name pitfall (re-verified 2026-07-19):** `gh pr view --json changed_files` returns `Unknown JSON field: "changed_files"` — the correct field is `changedFiles` (camelCase, per `gh pr view --json` schema). Use `gh pr view <N> --json changedFiles` or skip the field and use `gh pr diff <N>` instead.

### Pitfall 9: User asks "is this related to other bugs? what's in core memories?" — answer directly (added 2026-07-19)

When the user's question contains "related to other bugs?" + "what's in core memories?", they want a **contextual answer grounded in canonical state**, not a verdict. The /repro skill's cluster-recipe answers the bug-class question, but the user is also asking for the **direct read of canonical state** to confirm the LLM is contradicting established canon.

**Answer shape (run these in parallel):**

1. **Sibling enumeration:** `gh issue list --repo <OWNER>/<REPO> --state all --search "<entity-name> OR <campaign-id>" --limit 30 --json number,title,state,createdAt`
2. **Core-memories direct read:** pull the test subject's `_game_state.json` export, search for the named entity (Iron Bank, Aenar, Argella, etc.) in `core_memories` and `custom_campaign_state.rule`
3. **Canonical anchor validation:** for each entity the user named, check `npc_data.<entity>.status`, `entity_tracking.active_entities[].status.location`, and `core_memories` section content
4. **Deployed-vs-branch gap check:** see Pitfall 8 — is the durable fix in a merged PR or in an unmerged branch?

**Format the answer with 4 sections:**

| Section | Content |
|---|---|
| **Related?** | Yes/No + sibling table (issue#, scene#, symptom, anchor violation, status) |
| **In core memories?** | Direct quote from `core_memories` for the named entity + any `custom_campaign_state.rule` field |
| **Root-cause direction** | One-line: same family as N prior siblings, durable fix in PR #X but not yet merged |
| **Recommended next step** | Either "merge the existing branches" or "branch fresh prompt-fix worktree" |

**Anti-pattern:** answering only the bug-class question ("yes, this is the canonical-state-anchor family") without showing the direct canonical-state evidence. The user explicitly asked "what's in core memories?" — give them the verbatim canonical anchor, not just the cluster signal.

### Pitfall 10: Forgetting the `custom_state_keys == []` architectural gap (added 2026-07-19)

The canonical-state-anchor family has an architectural root cause beyond prompt wording: **most campaigns have empty `custom_state`** — there is no per-campaign surface for the user to enforce "no magic detection", "Iron Bank is faction X-controlled", or "Argella knows Y". The LLM re-derives these constraints from `core_memories` archetype descriptors every turn.

**Diagnostic:** in the test subject's `_game_state.json`, check:
```python
state = json.load(open(test_subject_state_path))
custom_keys = list(state.get('custom_campaign_state', {}).keys())
# If custom_keys is empty or only contains game-state plumbing (not user-set canon rules),
# the campaign has no architectural surface to anchor per-campaign "do not invent" rules.
```

**Verified case 2026-07-19 (`Cg2m2TkGFFez7XBynEah`):** `custom_state_keys == []` despite the `custom_campaign_state` containing a `rule: "Explicitly forbid magical 'Iron-Scent' or 'Shadow-Signature' tracking of..."` directive. The rule lives in the prompt but is **not materialized as a structured state field** the LLM can check on every emit.

**Recommended durable-fix extension:** add `custom_campaign_state.no_magic_detection_zone: bool`, `custom_campaign_state.faction_control: {<faction>: <owner-npc>}`, and `npc_data.<NPC>.lore_origin = "user-introduced" | "LLM-invented"` provenance fields to `$PROJECT_ROOT/game_state.py`. This converts the prompt-only canon rules into structured state the LLM can validate against on every emit, not just the scenes where the user actively retcons.

This extension belongs in a follow-up prompt-fix PR, not in the existing PR #8443 / PR #8445 branches — those fix the prompt layer; the custom_state extension fixes the data-model layer.

### Pitfall 11: Durable-fix shape lives at the prompt layer, but in THREE places (added 2026-07-20)

A canonical-state-anchor durable fix requires **three coordinated prompt-layer sections**, not one. The 2026-07-20 PR #8473 / issue #8472 (canonical-dead-NPC revival, scene 492) landed the missing two halves after PR #8352's state-update-only half was insufficient for 4 weeks.

**The three layers:**

| Layer | Where it lives | What it governs | Bug it catches |
|---|---|---|---|
| **State-update layer** | `$PROJECT_ROOT/prompts/game_state_instruction.md` | `state_updates.npc_data` writes | "LLM resurrects dead NPC via state write" |
| **Narrative-emit layer** | `$PROJECT_ROOT/prompts/narrative_system_instruction.md` (NEW §NPC Presence at Canonical Status) | The prose the LLM produces | "LLM narrates dead NPC physically present in scene" — what PR #8352 alone did NOT catch |
| **Planning-block layer** | `$PROJECT_ROOT/prompts/planning_protocol.md` (NEW §NPC Presence at Canonical Status (Choice Premise Validation)) | `planning_block.choices[]` premise validation | "LLM emits choice whose premise requires dead NPC's presence" |

**Why all three must land together:**

The state-update layer alone is insufficient because the LLM's narrative-emit pass can re-introduce a canonical-dead NPC into the prose even when the game-state pass correctly suppresses the resurrection write. Verified 2026-07-20: PR #8352 / commit `31d8b452c5` (June 28) shipped §"Narrative Revival of Canonical-Dead NPCs" into `game_state_instruction.md`. The rule said "do not resurrect canonical-dead NPCs in `state_updates.npc_data`". On 2026-07-20, scene 492, the LLM correctly did NOT emit a `state_updates.npc_data` resurrection write — but the narrative-emit agent still narrated `Archon Jaenor Vaelaros` as physically present at the coronation, *"stands at the base of the dais, his heavy signet ring extended in a trembling hand"*. The state-update-layer half held; the narrative-emit-layer half did not exist.

**The architecture discovery (added 2026-07-20):**

Each canonical-state-anchor sub-class (NPC co-presence, NPC knowledge-of-PC, faction-control, canonical-dead-NPC revival, Argella-suspicion, magic-sensor invention) maps to the same 3-layer prompt architecture. When filing the durable-fix PR for a new sub-class:

1. **Check the state-update layer first** (`game_state_instruction.md`). If a rule already exists for the sub-class, you have the state-update half — the bug is in one of the other two layers.
2. **Check the narrative-emit layer** (`narrative_system_instruction.md`). This is the most-missing layer; PR #8352's commit history shows the team fixed state-update-only first.
3. **Check the planning-block layer** (`planning_protocol.md`). Often forgotten because the choices look "advisory" but they bind NPC presence in subsequent turns.

**PR #8473 cross-reference map (verified 2026-07-20):**

```
state-update half (PR #8352 / commit 31d8b452c5):
  game_state_instruction.md §"Narrative Revival of Canonical-Dead NPCs"
  → Governs: state_updates.npc_data.<npc_id> writes

narrative-emit half (PR #8473 / commit f4bb3a6687):
  narrative_system_instruction.md §"NPC Presence at Canonical Status (Forbidden Revival Patterns)"
  → Governs: the prose the LLM produces
  → Enumerates: 7 forbidden-pattern categories + permitted patterns + resurrection exception

planning-block half (PR #8473 / commit f4bb3a6687):
  planning_protocol.md §"NPC Presence at Canonical Status (Choice Premise Validation)"
  → Governs: planning_block.choices[] premise validation
  → DROP-not-hedge rule for choices whose premise requires a canonical-dead NPC's presence
```

**Anti-pattern: "fix it in the prompt file and ship":**

If the new sub-class fix only touches `game_state_instruction.md`, it will land fast but the narrative-emit bug will re-emerge 1-4 weeks later (as it did with PR #8352 → #8472). Always ship the narrative-emit + planning-block halves in the same PR (or a chained PR with the state-update half on the same branch).

**Anti-pattern: "extend PR #8469's anchor because it covers the same area":**

PR #8469 / issue #8468 anchors NPC knowledge claims against mask-layer prohibitions. PR #8473 / issue #8472 anchors NPC physical presence against canonical-dead status. The two sub-classes are structurally distinct — keeping them as independent PRs lets reviewers merge in either order, and avoids coupling that complicates CodeRabbit review. Cross-reference via cluster-sibling mention in the PR body, NOT via branch merge.

**Verification recipe for the 3-layer architecture:**

After shipping the durable fix, verify with a fresh `git worktree add -b feat/<topic> origin/main` + copy campaign + replay LLM call. If the bug surfaces in any of the three layers, the corresponding half is missing. The test file pattern (`tests/test_<subclass>_<issue#>.py`) ships alongside each PR; PR #8473's `test_canonical_dead_npc_revival_8493.py` has 14 prompt-contract pins covering all three layers, with one skipped (Layer-C server-side post-LLM guard pending human approval per AGENTS.md).

### Pitfall 12: Opt-in features — mirror the faction minigame pattern (added 2026-07-20)

When a user reports "X activates without my permission, I want it opt-in like faction mode", the canonical template is `FactionManagementAgent` + `faction_minigame.enabled`. The template has three pieces that ALL must ship together; shipping any subset leaves the user visible-bug intact:

| Template piece | Where it lives | What it does |
|---|---|---|
| **Opt-in flag in state** | `custom_campaign_state.<feature>_minigame.enabled = False` (default off for new campaigns) | The user-controlled toggle |
| **`matches_game_state` gates on the flag** | `<Feature>Agent.matches_game_state()` returns False when flag is False | Stops state-driven hijack of ordinary turns |
| **Enablement patterns** | `<FEATURE>_ENABLEMENT_PATTERNS` list (e.g. `enable faction mode`, `enable multiverse minigame`) with `matches_input` accepting them unconditionally | Lets the user opt in WITHOUT a god-mode prefix |

**Anti-patterns (verified on $GITHUB_REPOSITORY PR #8475, issue #8474 — multi-verse activating without consent):**

- ❌ Implementing only the flag (state-only opt-in). The bug recurs whenever the threshold crosses during ordinary play because `matches_game_state` doesn't check the flag.
- ❌ Implementing only `matches_input` patterns. Enablement phrases still get blocked when the LLM happens to emit the right input but state flag is False.
- ❌ Adding a "backwards-compat shim" that auto-opts-in when a legacy flag is set (e.g. `multiverse_upgrade_available=True`). This re-introduces the original bug for every existing sovereign-tier campaign. Delete the shim; existing campaigns explicitly opt in.
- ❌ Forgetting `get_pending_upgrade_type()` (or the equivalent state-readable signal) when adding the flag to `matches_game_state`. The narrative-surfacing path still fires on the threshold even when routing doesn't — which is fine, but make sure the helper reads the flag too so downstream `agent._upgrade_type` and `matches_game_state` agree.

**Test recipe for opt-in features:**

1. RED: with flag=False, ordinary gameplay input routes to `<DefaultAgent>`, not `<Feature>Agent`, even when state threshold is crossed.
2. GREEN: with flag=True, the same input routes to `<Feature>Agent` and existing modal-lock / completed-tier guards behave identically to before.
3. ENABLE PATTERN: `<enable phrase>` without god-mode prefix flips the flag through god-mode directive processing and the next turn routes to `<Feature>Agent`.
4. The test helper for `<Feature>Agent` should accept the flag as a parameter, NOT derive it from other state flags (otherwise the test silently bypasses the new gate).

**Verified case (PR #8475, 2026-07-20):** the multi-verse fix shipped flag + `matches_game_state` gate + enablement patterns in one PR. 447 tests pass; 4 pre-existing tests had to be updated to opt-in (one had a backwards-compat-shim bug that the user would have hit immediately). The "ship all three pieces" rule was the lesson — even small partial implementations of this pattern will fail at runtime.

### Pitfall 13: Static path unambiguous — ship the fix on the same draft PR (added 2026-07-20)

When the canonical `/repro` workflow opens the issue → draft PR → reproduction → report gates, but **the bug class is unambiguous from static review alone** (no live LLM turn can falsify the root cause), ship the fix on the same draft PR. The gate contract requires the issue be filed BEFORE any other work; it does NOT require the draft PR wait for a fresh session.

**Triggers — static path is unambiguous when ALL of these hold:**

1. The user message names the exact symptom (e.g. "multi-verse activates without consent"), the desired behavior (opt-in like faction mode), and the canonical comparison target (faction minigame opt-in flag).
2. Static review confirms the bug class: `is_<feature>_upgrade_available()` returns true on threshold, `matches_game_state` does not gate on a flag, `matches_input` returns false.
3. The fix shape is a known pattern (Pitfall 12's opt-in template, Pitfall 11's 3-layer prompt architecture, etc.) — the fix is a copy-and-adapt, not a discovery.
4. A live production-ingress replay cannot falsify the static review because the routing decision is determined by code, not by the LLM's prose output.

**Anti-pattern:** holding the fix back because the canonical `/repro` skill says "Step 6: production-ingress replay". For unambiguously-static bugs, the replay is theater — you already know what it would show.

**The "honest gap" requirement:** the PR body MUST say "no live production-ingress replay was run; the local fix cannot be falsified by a static review alone. CI + green-gate + a 3-turn streaming lifecycle test on top of this branch will give the final verdict." Do not claim `REPRO` for the live verdict when no live turn was run; claim `REPRO → FIXED` for the static path only.

**Verified case (PR #8475, 2026-07-20, campaign `EROaUnSbmDhqBedTbJMg`, issue #8474):** static review of `$PROJECT_ROOT/campaign_divine.py:is_multiverse_upgrade_available()` + `$PROJECT_ROOT/agents.py:CampaignUpgradeAgent.matches_game_state()` was unambiguous — there is NO path where the LLM could emit a `state_updates` write that bypasses the routing code, because routing happens before the LLM is called. The fix landed on the same draft PR (`fix/multiverse-opt-in-8474`, head `d72e990ed5`) as the original repro scaffold. 447 tests pass. CI + green-gate verdict still pending but the static path is closed.

**Cross-reference:** Pitfall 8 covers the "durable fix exists in unmerged PR branch" pattern. Pitfall 13 is the inverse — the durable fix does NOT exist yet, the user wants it, and shipping it on the same draft PR is the right move.