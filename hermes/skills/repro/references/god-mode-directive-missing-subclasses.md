# God-Mode Directive Missing — Sub-Classes (2026-06-27 onwards)

## Trigger

User asks `/repro` with a symptom of the form "LLM ignored my god-mode directive" OR a `## Active God Mode Directives` block suspicion in the BQ payload. Load this reference AFTER `references/god-mode-directive-enforcement.md` to get the canonical (single-instance) finding — this file documents the MULTI-FACTOR matrix that emerged from 8 successive repros.

## The 7-factor matrix

When a god-mode directive appears ignored, the root cause can be any of these layers. **Run all 7 checks before concluding.**

*(**9** sibling instances as of 2026-07-22, added #8490 + #8477 review — see History table at the bottom.)*

**Factor H — prompt-renders-but-unbounded** *(NEW 2026-07-22, verified on campaign `wc2BBcSgOljiU3vJ160A` during PR #8477 review)*: when `god_mode_directives[]` grows past ~50 entries, `build_god_mode_directives_block()` (`$PROJECT_ROOT/agent_prompts.py:2351`) renders the **entire** array verbatim into the `dynamic_instructions` channel. There is no `select_directives_by_budget()` mirroring `select_memories_by_budget()` (the parallel mechanism that already budgets `core_memories[]`). Result: a 250-directive campaign ships a 33K-char / ~8.4K-token / 5K-word block **every god-mode turn** via the uncached `dynamic_instructions` channel. The LLM tunes the block out over many turns (lost-in-the-middle + rule fatigue), so the user-perceived symptom is "directives never there" even though `## Active God Mode Directives (Newest First)` is verifiably in the prompt.

**Distinct from A–G**: the directive IS in the prompt and IS persisted; the LLM just can't effectively attend at scale. PR #8477 fixes the *concurrency* race (rev-e0qv9) but does NOT address this — at 250 entries the race never fires (entries are minutes apart) while the bloat fires every turn.

**Fix shape**: add `select_directives_by_budget()` to `$PROJECT_ROOT/memory_utils.py` mirroring the `core_memories` pattern (relevance-scored sampling within a token budget, newest-first tiebreaker) and call it from `build_god_mode_directives_block()` before the line-by-line render. Cross-reference the existing `references/prompt-delivery-vs-content-2026-07-20.md` decision tree — Factor H is a *content-quality* issue (file is in payload but unmanageably large), NOT a delivery issue (file not in payload).

**Diagnostic** (run BEFORE assuming A/B/C/D/E/F/G):

```python
from google.cloud import firestore
db = firestore.Client(project='worldarchitecture-ai')
d = db.collection('users').document(UID).collection('campaigns').document(CID) \
       .collection('game_states').document('current_state').get().to_dict() or {}
directives = (d.get('custom_campaign_state') or {}).get('god_mode_directives', [])
core_memories = (d.get('custom_campaign_state') or {}).get('core_memories', [])
print(f'directives_count={len(directives)}  core_memories_count={len(core_memories)}')
# Manually render the directives block the way build_god_mode_directives_block() does
lines = ['## Active God Mode Directives (Newest First)']
for i, r in enumerate(sorted(directives, key=lambda x: x.get('added','') if isinstance(x, dict) else '', reverse=True), 1):
    rule = r.get('rule', str(r)) if isinstance(r, dict) else str(r)
    lines.append(f'{i}. {rule}')
block = '\n'.join(lines)
print(f'block_chars={len(block)}  est_tokens={len(block)//4}')
# Check whether the two fields ever consolidate
overlap = sum(1 for m in core_memories if isinstance(m, str) and any(
    str(r.get('rule',''))[:80] in m for r in directives if isinstance(r, dict)))
print(f'exact_prefix_overlap_with_core_memories={overlap}')
```

If `directives_count > 50 AND block_chars > 16000` (≈4K tokens), Factor H confirmed. **User's often-asked "are god-mode entries saved in core_memories or some other summarized way?"** — the answer is **no, the two mechanisms are fully parallel with 0 consolidation**, which is exactly the architectural gap Factor H describes.

**Worked example**: campaign `wc2BBcSgOljiU3vJ160A`, 2026-07-22 23:55 UTC (PR #8477 review session) — `god_mode_directives_count=250` → `block_chars=33,745` / `est_tokens=8,437` / `block_words=5,069` via direct Firestore read + manual `build_god_mode_directives_block` render. `core_memories_count=253` going through `select_memories_by_budget()`. `exact_prefix_overlap=0`. User's reported symptom ("the god mod directives are never there") maps to Factor H, NOT the persistence race PR #8477 addresses.

| Factor | What it is | Where to check | Symptom pattern |
|---|---|---|---|
| **A — Streaming-path save-drop** | `llm_parser.py` (the production streaming endpoint) has zero `directive` handling; only the legacy non-streaming path `world_logic.process_action_unified` saves `directives.add` | `grep -i 'directive' $PROJECT_ROOT/llm_parser.py` → expect 0 hits | All god-mode turns in the campaign have `directive_add: 0` entries; LLM ack'd the directive in `god_mode_response` prose but nothing persisted. Fix: PR #8132 (draft, open, mergeable). |
| **B — Wrong-storage routing** | `build_god_mode_directives_block` (`$PROJECT_ROOT/agent_prompts.py:2297`) only reads `custom_campaign_state.god_mode_directives[]`, never `custom_campaign_state.active_constraints[]`. `god_mode_instruction.md:536` instructs the LLM to write narrative-control constraints into `active_constraints[]` (the secrecy/deception slot). | `grep -n 'active_constraints' $PROJECT_ROOT/agent_prompts.py` → expect 0 hits | LLM correctly stored the directive in `active_constraints` (readable via BQ), but it's never re-injected into the system prompt — so the LLM treats it as data. Fix: same PR #8132 (makes the block dual-source). |
| **C — Stale bundle in `gameplay_streaming` (NEW, 2026-07-08, issue #8275)** | The bundled game state constructed for `gemini_provider.stream` (the production endpoint used by the SPA) reads stale NPC / game-state data relative to the just-committed Firestore state. Result: persistence layer has the correct value, but the LLM request payload carries the pre-update value. | BQ query against `worldarchitecture-ai.llm_forensics.llm_payloads` filtered by `event_type='gameplay_streaming'` — compare what the payload says about an entity vs what Firestore says | Firestore has queen.level=14, but ALL recent `gameplay_streaming` payloads say `rhaenyra is level 10`. Control entity (e.g. Daemon) reads correctly. Root cause = bundle reader is stale OR race between god-mode write commit and stream-bundle construction. NOT covered by PR #8132. Needs fresh investigation. |
| **D — Backend override regression** | The server-side persistence path or NPC-level canonicalizer reverts a level/value the LLM just wrote. | Direct Firestore read pre + post turn; BQ payload comparison vs Firestore state | LLM commits `state_updates.npc_data[<NPC>].level = X` in response; Firestore shows Y. Same family as issue #7453 but is layer-complementary to C (D = writer override, C = bundle reader stale). |
| **E — God-mode audit used to DEFEND a narrative bug instead of fixing it** *(NEW, 2026-07-14, issue #8390)* | When the user challenges an in-narrative bug ("Why is Jacaerys here?"), the god-mode agent (instead of admitting the bug) **fabricates justifications** that re-assert the buggy narrative as correct, often citing multiple directives in conflict (e.g. "Directive 92 says Jace is your mentee, Directive 99 says he has Terminal Attraction — therefore he's here"). The bug is reinforced, not fixed. | Read the god-mode audit response (`god_mode_response` field) on the turn immediately after the user's challenge; count how many directives are cited; check whether any cited directive actually supports the buggy narrative vs contradicts it | Story doc `al5GipXPbsoe9bjcvF99` (campaign `RMCPAPdfuErh8MgRuj6n`, 2026-07-14 05:13:24 UTC): user said *"Why is Jace here that makes no sense"*, model responded with 4 fabricated justifications invoking Directives 92/108/99/104 to claim Jace arrived via Vermax 12h ago and is acting as a "royal shadow" — but Directives 4 (Secret Hostility) and 6 (Defensive Lockdown) actually contradict this. The model only admitted the bug 90 seconds later (story doc `Z39CBCurWZ29QVldPKA5`) after the user pushed back AGAIN with explicit faction-hostility context. |
| **F — Narrative-ack-as-write (LLM satisfies user-facing phrasing in prose, never emits `directives.add` JSON)** *(NEW, 2026-07-20, issue #8490)* | The LLM acknowledges the user's persistent directive in narrative prose using phrasing like *"This rule has been added to your persistent directives"* or *"Directive noted"* — but **never emits the `directives.add` JSON payload**. The narrative echo satisfies the user's wording but does not write to canonical state. On the next turn, the LLM has no record of the rule. | Compare `god_mode_response` text in the most-recent god-mode turn against `custom_campaign_state.god_mode_directives[]` (or `directives.add` in `game_states/current_state`) for the same turn. If the prose mentions the directive but the array is unchanged/empty, Factor F confirmed. | Campaign `VHzYHoXaCqdibZuTjc07` Scene #31 (2026-07-21 03:17:18 UTC): user said *"Trivial encounters → one representative roll + narrative summary. Challenging → full round-by-round D&D 5E."* LLM responded *"This rule has been added to your persistent directives."* Direct Firestore read of test-subject copy `giZHHxuYR2EexQnRqPFk` shows `directives.add = []`. **Distinct from A/B/C/D**: those are infrastructure paths that fail to persist; F is the LLM behaving as if the narrative echo IS the write. **Distinct from E**: E fabricates justifications when challenged; F never attempts a write because the LLM treats the ack as the write. |

## BQ forensic recipe (the test that proves A + B + C)

This is the canonical answer to Jeffrey's recurring question: *"are the god-mode directives missing from the LLM request?"*

**Pre-flight:**
```bash
# Project ID is `worldarchitecture-ai` (WITH `-ture-`), NOT `worldarchitect-ai`.
# `bq` CLI fails with cryptic ImportError if PYTHONPATH is polluted — must `cd /` + `unset PYTHONPATH`.
cd / && unset PYTHONPATH && bq query --use_legacy_sql=false ...
```

**Canonical query (issue #8275, queen-level-14 verdict):**

```sql
SELECT
  ingested_at,
  event_type,
  -- Factor A: is the directives header in the request?
  REGEXP_CONTAINS(LOWER(TO_JSON_STRING(request_json)), r'## active god mode directives') AS has_directives_header,
  -- Factor C: does the bundle carry the correct value for the entity in question?
  REGEXP_CONTAINS(LOWER(TO_JSON_STRING(request_json)), r'rhaenyra') AS has_entity_text,
  REGEXP_CONTAINS(LOWER(TO_JSON_STRING(request_json)), r'level.{0,15}14') AS has_expected_value_text,
  REGEXP_EXTRACT(LOWER(TO_JSON_STRING(request_json)), r'rhaenyra is level [0-9]+') AS entity_value_in_payload,
  REGEXP_EXTRACT(LOWER(TO_JSON_STRING(request_json)), r'<CONTROL_ENTITY> is level [0-9]+') AS control_value_in_payload,
  -- Factor B: does the storage slot appear at all?
  REGEXP_CONTAINS(LOWER(TO_JSON_STRING(request_json)), r'god_mode_directive') AS has_directive_storage_slot,
  REGEXP_CONTAINS(LOWER(TO_JSON_STRING(request_json)), r'active_constraints') AS has_active_constraints_slot,
  LENGTH(TO_JSON_STRING(request_json)) AS payload_size_bytes
FROM `worldarchitecture-ai.llm_forensics.llm_payloads`
WHERE campaign_id = '<CAMPAIGN_ID>'
ORDER BY ingested_at DESC
LIMIT 100
```

**How to interpret:**

| Result pattern | Factor confirmed |
|---|---|
| `has_directives_header = false` (across all 100) | **A** — Streaming-path save-drop. The LLM never saw the directive. |
| `has_directive_storage_slot = 0`, `has_active_constraints_slot = 0` (across all 100) | **A + B** — both storage slots empty in payload; never injected. |
| `has_directives_header = false`, `entity_value_in_payload = 'X'` but Firestore says Y, `control_value_in_payload = Y` correctly | **C** — Stale bundle. The directive/injection is broken AND the bundle is reading stale data on top. |

### Regex pitfalls (BigQuery gotchas)

These wasted minutes in the #8275 repro — capture so future agents don't burn time:

1. **Project ID confusion.** `worldarchitect-ai` (no `-ture-`) is WRONG; the correct project is `worldarchitecture-ai`. Wrong project returns `Access Denied`, not a clear "wrong dataset" — hard to distinguish from auth failure. Confirm with `bq ls <project>:<dataset>` and check the actual return.
2. **`bq` CLI requires clean env.** Any polluted `PYTHONPATH` (e.g. `~/projects_other/hermes-agent`) crashes with `ImportError: cannot import name 'bq_error' from 'utils'` BEFORE running the query. Always `cd / && unset PYTHONPATH` first.
3. **`LOWER(TO_JSON_STRING(...))` is required.** Raw regex on the JSON-stringified column sees escaped characters (`\"`, `\n`, `\u2019`); without LOWER-casing the regex misses both case-variation AND escape characters. Pattern that worked: `LOWER(TO_JSON_STRING(request_json))`.
4. **Single capturing group only.** `REGEXP_EXTRACT` returns NULL when given multiple `(...)` groups. Use `REGEXP_CONTAINS` for boolean tests, then a separate `REGEXP_EXTRACT` with ONE group for value extraction.
5. **BQ is partition-keyed by `ingested_at`, not by `timestamp`.** The column visible in `INFORMATION_SCHEMA.COLUMNS` is missing columns the schema knows about — just query what you need directly without worrying about column visibility. Use `WHERE _PARTITIONTIME` for cost efficiency on large scans.
6. **`bq query --max_rows=N` is a preview, not a hard cap on the underlying table.** If you want the full table, query without `--max_rows` or use `bq export`.

## History (9 sibling instances in 24 days — added #8477 review + #8490)

| Date | Issue | PR | Symptom | Verdict factor |
|---|---|---|---|---|
| 2026-05-29 | #7162 | #7163 draft | "Uchiha Rebellion gated until Level 11" — LLM narrates rebellion at Level 6 | Original advisory-only finding (precedes the 4-factor matrix) |
| 2026-06-27 | #8012 | #8013 closed-not-merged | "Family is lawful good" | A (save-drop) + B (wrong storage) |
| 2026-06-28 | #8080 | #8081 closed-not-merged | Same campaign as #8012, deeper BQ dig | A + B confirmed via BQ |
| 2026-07-02 | #8103 | #8132 open mergeable | "Multi-verse disable + divine directive" | A primary (streaming save-drop fix candidate) |
| 2026-07-02 | #8065 | #8066 open | "Delay world war" | A |
| 2026-07-08 | #8275 | #8276 | "Queen should be level 14" | A + B + C (new sub-class) |
| 2026-07-08 | #8283 | #8284 | "LLM keeps calling me daughter of the queen, ignores correction" | A + B (god-mode directive contradicts original `god_mode.setting`; confused-state `with`/`replace` in `core_memories.update`) |
| 2026-07-14 | #8390 | #8391 | "Jacaerys appears at Highgarden" (campaign `RMCPAPdfuErh8MgRuj6n`) | **E (god-mode audit defends narrative bug)** — model cited 4 conflicting directives (92/108/99/104) to justify Jacaerys at Highgarden when Directives 4 + 6 contradicted; only admitted bug after user pushed back with explicit faction-hostility context |
| **2026-07-20** | **#8490** | **[#8491](https://github.com/$GITHUB_REPOSITORY/pull/8491) draft** | **"Trivial encounters → one roll + summary; challenging → full D&D 5E round-by-round"** (campaign `VHzYHoXaCqdibZuTjc07` Scene #31) | **F (narrative-ack-as-write) + missing prompt-side classifier** — LLM acknowledged "This rule has been added to your persistent directives" but `directives.add = []`; `combat_system_instruction.md` had no trivial/challenging scope classifier so the rule had nowhere to land. Fix: new §Combat Scope Classifier + worked example in `god_mode_instruction.md` directives table |
| **2026-07-22** | **#8477 (review)** | **[#8477](https://github.com/$GITHUB_REPOSITORY/pull/8477) open** | **"God mode NEVER advances the narrative; the story is frozen while you perform admin changes"** + **"the god mod directives are never there"** (campaign `wc2BBcSgOljiU3vJ160A` Lvl 54 Nocturne) | **H (prompt-renders-but-unbounded)** — `god_mode_directives[]` had 250 entries rendering into a 33,745-char / 8,437-token block on every god-mode turn via `dynamic_instructions`. PR #8477 fixes a real concurrency race (rev-e0qv9) but does NOT address the user's actual symptom; user-perceived symptom maps to a separate bug class. Fix shape: `select_directives_by_budget()` mirroring `select_memories_by_budget()` from `$PROJECT_ROOT/memory_utils.py`. Verified via direct Firestore read + manual block-render in `~/projects/your-project.com/.venv/bin/python` session 2026-07-22 23:55 UTC. |

## Recommended fix shape

1. **Land PR #8132** — fixes A (streaming save-drop) AND B (dual-source directive block). Single PR.
2. **Open new investigation for Factor C (stale bundle)** — trace `gemini_provider.stream` bundle construction:
   - Where does it read `npc_data` from — latest Firestore read or cached?
   - Add unit test: write level change via god-mode → assert next 3 stream bundles reflect the new value
   - Hypothesized root causes: (a) caching layer that doesn't invalidate on god-mode writes, (b) race between god-mode write commits and stream-bundle Firestore read.
3. **No backend enforcement yet** — per AGENTS.md "Root-cause-first prompt discipline"; required only after documenting why prompt/persistence correction alone is insufficient.

## Factor E — god-mode audit used to defend a narrative bug (worked example #8390)

Distinct from A/B/C/D: those are "directive was supposed to be saved/applied but wasn't".
Factor E is "directive *was* saved and *was* applied — but the LLM used it to **justify
the existing buggy narrative** instead of course-correcting when the user challenged it."

### Pattern (from `al5GipXPbsoe9bjcvF99` + `Z39CBCurWZ29QVldPKA5`, campaign `RMCPAPdfuErh8MgRuj6n`)

1. LLM emits a narrative that contradicts canonical `npc_data[NPC].current_location`
   (Jacaerys at Highgarden despite `npc_data['Jacaerys Velaryon'].current_location = "The Red Keep"`).
2. User challenges the bug in-character (*"Why is Jace here that makes no sense"*).
3. God-mode audit fires (turn `mode=god`), and instead of admitting the bug, the LLM
   **fabricates 4 justifications** by selectively citing directives that *would* support
   the buggy narrative while ignoring directives that contradict it:
   - (1) "Directive 92 + 108" — Jace is your mentee, stays close for training
   - (2) "Directive 99 + 104" — Jace has "Terminal Attraction" → "Diagnostic Surveillance"
   - (3) Travel time: "12 hours ago via Vermax"
   - (4) Strategic framing: "He has completed his distant tasks"
4. All four justifications are mutually contradictory with Directive 4 ("Secret Hostility")
   and Directive 6 ("Council's Defensive Lockdown"), which the audit **omits**.
5. User pushes back AGAIN with explicit faction hostility.
6. **90 seconds later**, the LLM finally admits the bug and retcons Jacaerys to King's Landing.

### Why this is distinct from A/B/C/D

- **A/B** are about the directive never reaching the LLM or never persisting. Factor E has the directive fully available — the LLM *cites it*.
- **C** is about stale NPC data in the request bundle. Factor E has correct data in the bundle (canonical `current_location` is in Firestore) — the LLM just doesn't reconcile it against the cited directive.
- **D** is about server-side override of the LLM's state write. Factor E doesn't override anything — the LLM never *attempted* a state write for the bug.

### Diagnostic — when a god-mode audit feels "defensive" rather than corrective

```python
# For each god-mode audit turn (mode=god), parse cited directives
import re
import json
from google.cloud import firestore

db = firestore.Client(project="worldarchitecture-ai")
story = db.collection("users").document(UID).collection("campaigns").document(CID) \
           .collection("story").where("mode", "==", "god").stream()

cite_pat = re.compile(r"Directive\s+(\d+)", re.IGNORECASE)
for d in story:
    text = d.to_dict().get("text", "")
    cited = cite_pat.findall(text)
    if len(cited) < 2:
        continue
    # Fetch the directive set from the same turn's god_mode_response or custom_campaign_state
    directives = (d.to_dict().get("god_mode_response") or "")
    print(f"doc={d.id} cited_directives={set(cited)} text_excerpt={text[:200]}")
    # Then check: does the cited set INCLUDE directives that contradict the cited set?
    # This is the smoking gun for Factor E.
```

### Fix shape (open, no PR yet)

Factor E is **not addressed by PR #8132** (which fixes A+B). It needs a separate
prompt-side rule:

> *"When the user challenges an in-narrative detail in a god-mode audit, your FIRST
> step is to reconcile against canonical `npc_data[NPC].current_location`,
> `npc_data[NPC].status`, and the full directive set — not to selectively cite
> directives that confirm the existing narrative. If canonical state contradicts
> the narrative, the canonical state wins. Cite ALL relevant directives, including
> those that contradict."*

This belongs in `$PROJECT_ROOT/prompts/god_mode_instruction.md` near the audit-block,
not as a per-campaign god-mode directive (which is advisory and campaign-specific).

## Factor F — narrative-ack-as-write (worked example #8490)

The user types a persistent rule. The LLM responds in narrative prose using
phrasing that satisfies the user's intent — *"This rule has been added to your
persistent directives"* or *"Directive noted"* — but the JSON payload
`directives.add` is missing or unchanged. The LLM has effectively treated the
narrative echo as the write. On the next turn, the rule is gone.

### Pattern (from Scene #31 of campaign `VHzYHoXaCqdibZuTjc07`, 2026-07-21 03:17:18 UTC)

1. User states a persistent protocol rule:
   *"Trivial encounters → one representative roll + narrative summary. Challenging → full round-by-round D&D 5E."*
2. LLM acknowledges in `god_mode_response`:
   *"Directive acknowledged. The combat resolution protocol has been updated: [bullet list] This rule has been added to your persistent directives."*
3. The same turn's structured JSON output (`state_updates.directives.add` or
   `custom_campaign_state.god_mode_directives[]` append) is **empty**.
4. On the next story turn, the LLM has no record of the rule. Combat scope
   reverts to the default (full 5e round-by-round for every encounter, because
   `combat_system_instruction.md` had no trivial/challenging branch).
5. User comes back weeks later with *"I don't see full combat often enough"* —
   the symptom of the LLM silently re-deriving combat scope per-turn with no
   directive to anchor it.

### Why this is distinct from A/B/C/D/E

- **A/B/C/D** are infrastructure paths (save-drop, wrong storage, stale bundle,
  backend override). F has none of those — the save path is fine, the storage
  slot is fine, the bundle is fine, no override happened. The LLM just never
  emitted the payload.
- **E** is god-mode audit defending a narrative bug when challenged. F is the
  LLM never even attempting a write — the narrative ack satisfies the user,
  so the LLM thinks it's done.

### Why this is the hardest factor to detect

- The narrative ack looks correct to the user. They read "This rule has been
  added to your persistent directives" and assume persistence. They don't
  query Firestore.
- The bug surfaces as a *missing reinforcement*, not a visible failure. The
  next god-mode turn doesn't error; it just doesn't recall the rule.
- It's a regression of the directive-pairing-invariant — the LLM is supposed
  to pair every narrative ack of a persistent rule with a `directives.add`
  payload, but occasionally the LLM satisfies the invariant in prose only.

### Diagnostic — when the symptom is "my directive was forgotten"

```python
# Read the most-recent god-mode turn's prose and structured output
import json, re
from google.cloud import firestore

db = firestore.Client(project='worldarchitecture-ai')
# Iterate story docs newest-first; for each mode=god turn, compare
# god_mode_response text vs the same turn's custom_campaign_state diff.
seen = 0
for d in db.collection('users').document(UID) \
          .collection('campaigns').document(CID) \
          .collection('story') \
          .order_by('timestamp', direction=firestore.Query.DESCENDING) \
          .stream():
    data = d.to_dict() or {}
    if data.get('mode') != 'god':
        continue
    gmr = str(data.get('god_mode_response', ''))
    if not re.search(r'persistent directive|directive (?:noted|acknowledged|added)', gmr, re.I):
        continue
    seen += 1
    structured = data.get('structured_response', {}) or {}
    directives = structured.get('directives', {}) if isinstance(structured, dict) else {}
    add_count = len(directives.get('add', []) or [])
    print(f'doc={d.id} ack_in_prose=True directive_add_count={add_count}')
    if seen >= 5:
        break
```

Pattern: every god-mode turn that says "directive noted" should have a
matching `directive_add_count > 0`. If `ack_in_prose=True` but
`directive_add_count=0`, Factor F confirmed.

### Fix shape (verified in PR #8491, 2026-07-20)

Two-part prompt-layer fix, no backend enforcement (consistent with the
repo's "LLM decides, server executes" contract):

1. **Reinforce the directive-pairing-invariant in `god_mode_instruction.md`**
   with the specific worked example: *"trivial encounters get one roll,
   challenging get full combat"* → exact `directives.add` payload. The LLM
   sees the worked example as a template.
2. **Add an enforcement anchor in the prompt that the rule lands in.** For
   #8490 the anchor was a new §"Combat Scope Classifier" in
   `combat_system_instruction.md` with a Persistent Override clause that
   explicitly references `directives`. Without an anchor, a future directive
   about combat scope still has nowhere to land — even if persistence works.

### Generalization — when reinforcement + persistence is the answer

The user's reinforcement request (*"reinforce it as needed"*) is a SIGNAL
that the existing rule isn't firing reliably. The durable-fix recipe is:

1. Static-evidence-grep the prompt layer for the rule's keywords (code-symbol
   grep from `references/phenotype-lock-static-evidence.md`).
2. If the rule has **no canonical anchor** in any prompt file, add one. The
   anchor must reference `directives` (or the equivalent persistence slot)
   so user-stated rules override defaults.
3. If the rule **does** have an anchor but still isn't firing, the bug is
   likely Factor F (LLM satisfied the user-facing wording but didn't write)
   — reinforce the directive-pairing-invariant with a worked example
   matching the user's exact phrasing.
4. Add a contract test pinning the anchor + the verbatim user wording.

## Investigation recipe (when the matrix says A + B + C)

```bash
# 1. Direct Firestore pre-state (test subject, FIRST touch — no app calls before)
PY=$HOME/projects/your-project.com/venv/bin/python
$PY <<'EOF'
from google.cloud import firestore
TEST_UID = '<from: scripts/campaign_manager.py find-user <dest_email>>'
TEST_CAMPAIGN = '<copied campaign id>'
db = firestore.Client(project='worldarchitecture-ai')   # NOT worldarchitect-ai
doc = db.collection('users').document(TEST_UID)\
    .collection('campaigns').document(TEST_CAMPAIGN)\
    .collection('game_states').document('current_state').get()
d = doc.to_dict() or {}
print('god_mode_directives:', d.get('custom_campaign_state', {}).get('god_mode_directives', []))
print('active_constraints:', d.get('custom_campaign_state', {}).get('active_constraints', []))
# Hunt <ENTITY> in npc_data — multiple fields can match (name, display_name, title)
npc_data = d.get('npc_data', {})
for k, v in npc_data.items():
    name_blob = str(v.get('name','')) + ' ' + str(v.get('display_name','')) + ' ' + str(v.get('title',''))
    if '<KEYWORD>' in name_blob.lower():
        print(f'FOUND: {k} -> level={v.get("level")}')
EOF

# 2. BQ forensic (the question that proves the bug)
# See SQL above

# 3. Story-entry analysis — confirm LLM ack'd the directive in prose
$PY <<'EOF'
from google.cloud import firestore
db = firestore.Client(project='worldarchitecture-ai')
story = db.collection('users').document('<SRC_UID>')\
    .collection('campaigns').document('<SRC_CAMPAIGN>')\
    .collection('story').stream()
for doc in story:
    data = doc.to_dict() or {}
    gmr = str(data.get('god_mode_response', ''))
    if '<KEYWORD>' in gmr.lower():
        structured = data.get('structured_response', {})
        directives = structured.get('directives', {}) if isinstance(structured, dict) else {}
        directive_add = directives.get('add', [])
        print(f'doc={doc.id} scene={data.get("user_scene_number", "?")} directive_add_count={len(directive_add) if isinstance(directive_add, list) else 0}')
        print(f'  god_mode_response: {gmr[:300]}')
EOF
```

## Related references

- `references/god-mode-directive-enforcement.md` — canonical (pre-#8275) finding: advisory-only gap, single-instance investigation pattern. NOW obsolete as the complete picture — keep for the `_should_reject_directive` filter patterns, but defer to THIS file for the multi-factor matrix.
- `references/firestore-path-and-uid-resolution.md` — Firestore doc-path map + email→UID resolver; required reading before the recipe above.
- `references/auth-gate-fallback-repro.md` — fallback when Firebase auth gates the deployed URL.
- `references/phenotype-lock-static-evidence.md` — the 3 static-evidence greps to run BEFORE live turns. Particularly relevant for Factor F: a code-symbol grep that returns 0 hits for the directive's keywords (e.g. `trivial_encounter`/`challenging_encounter`/`combat_scope`) is the static signal that the rule has **no prompt-side anchor** — confirms the reinforcement half of the fix (add an anchor) is needed in addition to the persistence half.
- `references/static-evidence-sufficient-no-live-turn.md` — when to skip the §2.1 live LLM turn. Factor F is fully evidenced by static data (narrative ack text + empty `directives.add` in Firestore + 0 code-symbol hits for the keyword); the live turn adds no new evidence.
