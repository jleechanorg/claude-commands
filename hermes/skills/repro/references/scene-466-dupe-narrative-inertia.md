# Scene-level dupe + ignored-input pattern (sibling class)

**Verifiable**: campaign `8Q3ipgQIxRs2YvK1flng` ("Visenya V8 dupe scene 466"), issue [#8397](https://github.com/$GITHUB_REPOSITORY/issues/8397), draft PR [#8398](https://github.com/$GITHUB_REPOSITORY/pull/8398), 2026-07-14.

**2nd verified instance**: campaign `VHzYHoXaCqdibZuTjc07` ("bg3 nocturne murder god (dupe content)"), issue [#8493](https://github.com/$GITHUB_REPOSITORY/issues/8493), draft PR [#8494](https://github.com/$GITHUB_REPOSITORY/pull/8494), 2026-07-21. **Cross-campaign cluster now 2/3** — 1 more sibling triggers root-cause-first prompt overhaul.

## What this reference covers

The combined "scene N looks like a dupe + LLM ignored user input" symptom pattern. Distinct from the existing god-mode-directive-missing class (where the LLM narrates a directive but `directives.add` is empty in Firestore) — this is the **LLM re-using the previous scene's narrative frame** even when the user introduced a new directive.

## Five new lessons from this session

### 1. Campaign-title-as-bug-name signal

When the source campaign's `title` field literally encodes the bug being reported (e.g. "Visenya V8 dupe scene 466"), that's a stronger signal than just the user's Slack report:

- The user is **not** reporting a fresh discovery — they're reporting on a campaign they **already named with the bug label**, often after creating it specifically to reproduce
- The dupe pattern is therefore **already a known/expected feature** of the campaign from the user's perspective
- This means: skip the "find the bug" phase; go straight to "verify the dupe pattern is conclusive from the existing story log"

Diagnostic: read the `campaigns/{cid}` meta doc's `title` field. If the title contains words like `dupe`, `bug`, `repro`, `test`, `ignored` — treat the bug as already-identified and the repro target as already-named.

### 2. Cross-campaign cluster trigger (extension)

The existing `phenotype-lock-static-evidence.md` rule fires when **≥3 open repros share the same `campaign_id`**. This session proved the trigger should also fire when **≥3 open repros share a campaign-family keyword** (e.g. all titled "Visenya V8") even on different `campaign_id`s.

In this case: 4 sibling issues #8384/#8386/#8388/#8395 on campaign `RMCPAPdfuErh8MgRuj6n` (titled "Visenya V8") plus this issue on `8Q3ipgQIxRs2YvK1flng` (titled "Visenya V8 dupe scene 466") — 5 repros across 2 campaigns in 24h.

**Extension to the existing rule**: when the campaign title contains a family keyword (e.g. "Visenya V8"), `gh issue list --search "<family_keyword>"` should be the trigger, not `--search "<campaign_id>"`. Update the trigger to:

1. Primary: ≥3 open repros on same `campaign_id` (existing rule)
2. **NEW**: ≥3 open repros whose titles contain the same family keyword (e.g. all "Visenya V8..."), even across different `campaign_id`s
3. Both trigger the same action: branch a root-cause-first prompt fix instead of per-scene patch

### 3. Structural dupe sibling sub-class

A new bug sub-class distinct from god-mode-directive-missing. Symptom: two consecutive **gemini** responses (i.e. assistant turns) both open with:

- The same timestamp (e.g. `Midday (12:00:00).`)
- The same character motif (e.g. Hugh Hammer in landed-knights station)
- The same narrative frame (e.g. re-indexing the realm)

…even when the intervening **user** turn introduced a new directive with a different scope (e.g. "Total Realm Audit — re-index the Seven Kingdoms").

Root-cause hypothesis (from `npc-status-persistence-bug.md` / `references/narrative-inertia`): the LLM is failing to **reset the narrative frame** when the user introduces a new directive that targets a different scope than the previous turn. The canonical-anchor discipline from PR #8336 (NPC death state) and PR #8391 (NPC location) covers state-level anchoring but **does not cover narrative-frame reset**.

**Recommended fix scope**: extend canonical-anchor discipline to narrative-frame reset + audit `$PROJECT_ROOT/world_logic.py:8644-8896` (the section PR #8066 flagged as depending entirely on LLM-emitted `structured_response.directives.add`) for prompt-frame construction that passes user directives through as structured input, not just keyword-matched in prose.

**Diagnostic table** (add to `npc-status-persistence-bug.md` as sub-class "F: structural narrative-frame dupe"):

| Scene pair | Doc A opening | Doc B opening | Shared motif | User input between | Verdict |
|---|---|---|---|---|---|
| 466/468 | `Midday (12:00:00). You descend...` | `Midday (12:00:00). You return to King's Landing...` | dragonseeds (Hugh/Ulf/Addam) + re-indexing | "The Total Realm Audit — Seven Kingdoms" | REPRO |

### 4. HISTORICAL RED ARTIFACT threshold definition

PR #8066 documented the pattern (16/16 god-mode directives cleared but 0/16 persisted = quantitative conclusive evidence). This session proved the same pattern works for **qualitative** conclusive evidence:

- 1 consecutive gemini pair exhibits the dupe pattern = 1/1
- 1 user input at scene 467 ignored in scene 468's response = 1/1
- Both conclusive without live replay because the pattern is **structural** (not probabilistic)

**Threshold rule** (update §3 "Red/green code provenance requirement" in canonical skill):

- **Quantitative conclusive** (PR #8066 pattern): N/M sample satisfies the criterion where N is statistically meaningful (e.g. ≥10/10, ≥16/16). Label `HISTORICAL RED ARTIFACT — quantitative`.
- **Qualitative conclusive** (this session's pattern): N=1 consecutive pair satisfies the criterion where the pattern is **structural** (same timestamp + same characters + same frame). Label `HISTORICAL RED ARTIFACT — qualitative`.
- Both satisfy the same-symptom requirement; both skip live replay when the evidence is conclusive.

What does NOT qualify as conclusive: a single gemini response that mentions a key phrase but the surrounding narrative is distinct from the previous scene's frame (keyword-overlap ≠ structural dupe).

### 5. Story-doc schema pitfall (Firestore direct read)

When capturing first-touch pre-state via direct Firestore read of `users/{uid}/campaigns/{cid}/story/`:

- Schema is `text / part / mode / timestamp / actor` — **no `sequence_number` field**
- Scene numbers must be **derived from timestamp-sorted index** (1-indexed: scene N = parsed[N-1])
- Doc IDs are random alphanumeric strings (e.g. `NqkT5t3pswjtccBHDctp`) — they are **not** ordered

Pitfall: do NOT try `where('sequence_number', '==', N)` or `where('scene_number', '==', N)` — they will all return 0 hits. Pull all docs, sort by `timestamp` asc, then assign scene number = index + 1.

Pitfall: do NOT use the alphabetical doc_id order — it's random and will give garbage scene numbers.

Pitfall: doc IDs may collide in their first few chars across the corpus (e.g. multiple docs starting with `02`) — this is normal and not an indication of duplicate data.

## Proactive diagnostic that worked

**Before any `gh` CLI call**: `gh api rate_limit | python3 -c "..."` to print core/graphql/search budgets. In this session: core 4625/5000, graphql 2392/5000, search 30/30 — both buckets healthy. Made it safe to use `gh issue create` + `gh pr create --draft` without REST fallback.

Add this to the hard-gate workflow as **Gate 0** (runs before Gate 1):

```bash
gh api rate_limit | python3 -c "
import sys, json
d = json.load(sys.stdin); r = d['resources']
print(f\"core: {r['core']['remaining']}/{r['core']['limit']}\")
print(f\"graphql: {r['graphql']['remaining']}/{r['graphql']['limit']}\")
print(f\"search: {r['search']['remaining']}/{r['search']['limit']}\")
"
```

If either core or graphql is <500, fall back to `urllib.request` REST (per `references/gh-rate-limit-rest-fallback.md`) BEFORE creating issue/PR. If both buckets are healthy, proceed with `gh` CLI.

## Cross-references

- `references/npc-status-persistence-bug.md` — narrative-inertia / canonical-anchor discipline (existing reference, should gain sub-class F: structural narrative-frame dupe)
- `references/god-mode-directive-missing-subclasses.md` — sibling god-mode-directive-missing class (existing reference)
- `references/phenotype-lock-static-evidence.md` — 3 static-evidence greps + sibling-campaign cluster trigger (existing reference, should gain extension #2 above)
- `references/gh-rate-limit-rest-fallback.md` — REST fallback when GraphQL exhausted (existing reference, complementary to Gate 0 above)
- `references/static-evidence-sufficient-no-live-turn.md` — when HISTORICAL RED ARTIFACT is sufficient (existing reference, should be cross-linked from §3 of canonical skill)
- Skill `repro-twin-clone-evidence` §3 Red/green code provenance — should gain the threshold definitions from lesson #4
- Skill `repro-twin-clone-evidence` §0.5 Campaign ID extraction — should gain the title-as-bug-name signal from lesson #1

## Update checklist (for the next agent who picks up this file)

- [ ] Add lesson #1 to canonical skill §0.5 as a "Title-as-bug-name signal" subsection
- [ ] Add lesson #2 to `phenotype-lock-static-evidence.md` as a cross-campaign cluster trigger extension
- [ ] Add lesson #3 as sub-class F to `npc-status-persistence-bug.md` with the diagnostic table
- [ ] Add lesson #4 to canonical skill §3 as "HISTORICAL RED ARTIFACT threshold" definition (quantitative vs qualitative)
- [ ] Add lesson #5 to canonical skill §2.1 or to a new `references/story-doc-schema.md`
- [ ] Add Gate 0 (rate-limit pre-flight) to the hard-gate workflow at the top of the canonical skill