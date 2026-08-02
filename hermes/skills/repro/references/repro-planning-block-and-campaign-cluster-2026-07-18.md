# Planning-block emission + campaign-cluster structural threshold (2026-07-18, verified #8440 / PR #8441, extended 2026-07-18 #8444 / PR #8445, 5th-sibling cross-link verified 2026-07-18)

## Changelog

- **1.0.1 (2026-07-18)** — Added §7 (cross-link instead of file at 5+ siblings) + §8 (bash backtick/bracket pitfall when embedding JSON in `terminal('python3 -c ...')`). Verified by Aenar-defeated repro → cross-link comment on #8444 (`issuecomment-5012707073`) + Slack summary, no new issue filed. Decision tree for sibling-count → action mapping is now explicit.
- **1.0.0 (2026-07-18)** — Initial playbook. 5-anchor taxonomy (directive retcons / NPC co-presence / future-event gates / canonical milestones / level-up rewards). 3 verified workhorses (PRs #8439, #8441, #8445) + 1 in-progress (PR #8443 anti-tracking prompt rule).

Trigger: A `/repro` request where the symptom is "the planning block says X" or
"the planning block contains Y", OR where this is the 2nd+ repro on the same
`campaign_id` (i.e. "at threshold, next sibling crosses the campaign-cluster
trigger").

## 1. `copy_campaign.py` CLI gotcha (verified 2026-07-18)

The script takes POSITIONAL args, not `--source-uid` / `--source-campaign-id` flags:

```bash
# WRONG — fails with "unrecognized arguments"
./venv/bin/python scripts/copy_campaign.py \
  --source-uid X --source-campaign-id Y --dest-email <your-email@gmail.com>

# RIGHT — positional source_user_id source_campaign_id
./venv/bin/python scripts/copy_campaign.py \
  X Y --dest-email <your-email@gmail.com> --suffix '(descriptive-slug)'
```

Always run `--find-by-id` first to get the source UID confirmed in stdout
(returned as `User ID: <uid>`). Then copy positional. The `--find-by-id` step
ALSO prints `✅ Found under default source email` — the script runs `--find-by-id`
internally before the actual copy.

## 2. Static-evidence fast path for planning-block bugs

When the bug class is "the LLM emits a planning block that depends on a
retconned/suppressed premise":

- The `planning_block` field is **first-class** in `users/<uid>/campaigns/<cid>/game_states/current_state` — it survives `download_campaign.py` JSON export and `copy_campaign.py`.
- After copy, compare source vs test-copy story `.txt` byte size: if the story is **byte-faithful** (`size_src == size_test_copy`), the planning_block in the test copy will also be identical (modulo JSON field ordering in `game_states/current_state`, which is harmless).
- A byte-faithful copy IS the red evidence — no live replay needed for static `planning_block` bugs. Saves $0.50-2.00 in LLM tokens and avoids the GEMINI context-window race.
- Citation: verified on campaign `D3iZvnGiBl9wyveQBFj9` repro #8440 — source story 329925 == test copy 329925 (byte-faithful); game_state 150703 == 150703 (modulo JSON field ordering). Also #8444 — source story 467442 == test copy 467442; game_state 161967 == 161967.

`planning_block.choices[N].description` and `planning_block.thinking` are the
literal places to grep for the bug. Don't rely on grepping the `.txt` export —
those choices live in the JSON's `planning_block` field, NOT in the story text.

## 3. Campaign-cluster pre-threshold warning (2nd repro)

Per `references/phenotype-lock-static-evidence.md`, the campaign-cluster trigger
fires at **≥3 open repros on the same `campaign_id`**. At the 2nd repro (i.e.
right before the trigger), EXPLICITLY flag in the issue body AND the PR body:

```markdown
⚠️ **Campaign cluster signal** — 2 repros on `<campaign_id>` in <time period>.
Per `references/phenotype-lock-static-evidence.md` ≥3-open threshold: this is
at the threshold. Next sibling crosses the trigger — open a structural-issue
bead at that point and consider a root-cause-first prompt fix that addresses
the common anchor layer (e.g. "LLM does not cross-check planning_block against
god_mode_directives[]").
```

This is SOP at 2 siblings, not just at 3+. The 2nd-repro PR should ALSO link
the 1st sibling by URL in both issue body and PR body, and explicitly say
"durable fix should cover BOTH repros together".

## 4. Sibling PR linkage when earlier repro is still open

When filing a repro and discovering an earlier repro on the SAME campaign is
still open (e.g. #8438 + draft PR #8439 still open when filing #8440):

- Cross-link in the new issue's "Bug summary" section and the PR body
- Recommend the prompt reviewer verify the earlier PR's fix covers the new repro's root-cause class, OR open a new PR if it's a different sub-class
- Pair the prompt-side fix recommendations across both PRs in the "Next-step guidance" section

## 5. Planning-block bug class — sibling issues + 5-anchor taxonomy

Quick lookup of planning-block emission siblings (canonical skill
`repro-twin-clone-evidence` references `references/phenotype-lock-static-evidence.md`
for the structural trigger):

- [#8293](https://github.com/$GITHUB_REPOSITORY/issues/8293) — planning block re-shows hidden gold already found (`xK3fp5XrV24oarIINTF7`)
- [#7373](https://github.com/$GITHUB_REPOSITORY/issues/7373) — planning block emits "Necropolis Heist" despite all 3 anchors integrated
- [#7781](https://github.com/$GITHUB_REPOSITORY/issues/7781) / [#7785](https://github.com/$GITHUB_REPOSITORY/issues/7785) / [#7334](https://github.com/$GITHUB_REPOSITORY/issues/7334) — planning block missing level-up choice
- [#7710](https://github.com/$GITHUB_REPOSITORY/issues/7710) — Character Creation opening banner has empty `planning_block`
- [#7763](https://github.com/$GITHUB_REPOSITORY/issues/7763) — planning block leaks unrevealed future events before player_aware=true
- [#8438](https://github.com/$GITHUB_REPOSITORY/issues/8438) / [PR #8439](https://github.com/$GITHUB_REPOSITORY/pull/8439) — LLM invents "Blood-Scent" silver vial in prose (`D3iZvnGiBl9wyveQBFj9`, 1st sibling)
- [#8440](https://github.com/$GITHUB_REPOSITORY/issues/8440) / [PR #8441](https://github.com/$GITHUB_REPOSITORY/pull/8441) — planning block ignores Directive [3] retcon (`D3iZvnGiBl9wyveQBFj9`, 2nd sibling)
- [#8442](https://github.com/$GITHUB_REPOSITORY/issues/8442) — MBTI / Alignment codes leak to player-facing narrative (`D3iZvnGiBl9wyveQBFj9`, 3rd sibling)
- [#8444](https://github.com/$GITHUB_REPOSITORY/issues/8444) / [PR #8445](https://github.com/$GITHUB_REPOSITORY/pull/8445) — "Rejoin the Host" choice assumes Aegon at Mander mouth while co-present at Highgarden (`D3iZvnGiBl9wyveQBFj9`, 4th sibling)
- **2026-07-18 cross-link on #8444 (5th-sibling signal)** — Aenar-defeated premise ("Prevents Aenar from sabotaging your success" while `npc_data["Aenar Vaelaros"].status = "disgraced_front_line"`). Filed as cross-link comment on #8444 (`issuecomment-5012707073`) + Slack summary, NOT a 6th per-scene issue. Recommended extending PR #8443's anti-tracking prompt rule with two new clauses (NPC `status` exclusion + NPC `location` co-presence). See §7 below for the "cross-link instead of file" mechanism.

All share the bug class **"LLM emits `planning_block` content that contradicts canonical state"** — different anchors. The canonical-state anchors that planning_block choices can violate form a 5-type taxonomy:

| # | Anchor | Source field | Example sibling |
|---|---|---|---|
| (a) | Directive retcons | `custom_campaign_state.god_mode_directives[]` (rules marked `retcon` / `suppressed`) | #8440 / #8441 |
| (b) | NPC co-presence | `npc_data[<X>].location`, `npc_data[<X>].co_presence` | **#8444 / PR #8445 (NEW sub-class)** |
| (c) | Future-event gates | `world_events[i].revealed_at`, `player_aware` flag | #7763 |
| (d) | Canonical milestones / inventory | `milestones_completed`, `inventory`, `discovered_loot` registry | #7373, #8293 |
| (e) | Level-up rewards | `rewards_box.level_up_available`, `level_up_pending` | #7781 / #7785 / #7334 |

The sibling cluster is at `references/god-mode-directive-missing-subclasses.md`
for the directive-persistence side (anchor a) and `references/npc-status-persistence-bug.md`
for the canonical-state anchor side (anchors b/d); **planning-block** bugs sit at the
intersection (directive layer + emit-side render layer).

### 5.1 NPC co-presence sub-class (NEW — #8444 / PR #8445)

User-reported symptom: *"this planning block choice doesn't make sense and seems like a theme where planning blocks dont have the full information about the story while the narrative seems fine — Aegon is with me so departing to give him the reach compliance as a gift doesn't make sense."*

The pattern: a planning_block choice whose `description` references a directional movement (depart/arrive/rejoin/leave/return) where the **player or the target NPC is already at the destination in canonical state**. Verified via `player_character_data.world_data.current_location_name` + `npc_data[<X>].location` cross-check. Frequently the **thinking** block inside the same emit correctly reasons about co-presence, but the **choice description** simultaneously reasons as if the NPC were elsewhere — i.e. **the thinking and the choice are self-contradictory in the same emit**.

Diagnostic steps:
1. Extract `planning_block.choices[N].description` + `planning_block.thinking` verbatim
2. Extract `player_character_data.world_data.current_location_name` + `npc_data[<NPC>].location` (if present) or use narrative `grep` for NPCs named in the choice
3. If the choice's destination != player's location OR the NPC's location != choice's claimed location, it's anchor (b)
4. Check thinking for self-contradiction: thinking says X, choice says ¬X → highest-confidence anchor-(b) signal

Verdict row: `HISTORICAL RED ARTIFACT — NPC co-presence violation` (extends the 4-label enum from `phenotype-lock-static-evidence.md`). The `planning_block` field is first-class in `game_states/current_state` and survives `copy_campaign.py` — a byte-faithful test copy is sufficient red evidence; no live replay needed.

## 5.5 `copy_campaign.py` — extra flags & gotchas (verified 2026-07-18, #8444)

Building on §1: the script has **two more gotchas** beyond positional args:

### 5.5.1 `--allow-same-user` flag for cross-UID copies

When source UID and dest UID are different BUT the script's heuristic can't tell (e.g. two accounts in the same Firebase auth domain), the script bails with a warning and **creates no campaign in Firestore**, returning only the `{dest_uid, dest_email}` JSON line. Verified 2026-07-18 on #8444: copying `vnLp2G3m21PJL6kxcuAqmWSOtm73` ($USER@gmail.com) → `0wf6sCREyLcgynidU5LjyZEfm7D2` (<your-email@gmail.com>) bailed silently with only the JSON output and no Firestore write. Adding `--allow-same-user` forces the copy through.

**Always include `--allow-same-user` for any $USER → jleechantest test copy** even though they're distinct UIDs — the script's heuristic is conservative.

```bash
# WRONG — bails silently, returns {dest_uid, dest_email}, no Firestore write
./venv/bin/python scripts/copy_campaign.py \
  vnLp2G3m21PJL6kxcuAqmWSOtm73 D3iZvnGiBl9wyveQBFj9 \
  --dest-email <your-email@gmail.com> --suffix "(aegon-repro)"

# RIGHT — actually copies
./venv/bin/python scripts/copy_campaign.py \
  vnLp2G3m21PJL6kxcuAqmWSOtm73 D3iZvnGiBl9wyveQBFj9 \
  --dest-email <your-email@gmail.com> --suffix "(aegon-repro)" \
  --allow-same-user
```

Verification step after copy: check that the new campaign appears in `download_campaign.py --list` for the dest user. If only `{dest_uid, dest_email}` returned AND `--list` doesn't show the new title, the copy didn't land — re-run with `--allow-same-user`.

### 5.5.2 `orderBy=createTime desc` on Firestore REST `list` is unreliable

`?orderBy=createTime%20desc` against `users/{uid}/campaigns` returned **0 documents** on the test user's 296-campaign collection (verified 2026-07-18, #8444). The index may not be set, OR the syntax may not work for this REST endpoint. **Fallback**: drop `orderBy`, paginate through `nextPageToken` manually, sort client-side by `doc.createTime` field. See `references/find-new-campaign-id-after-copy.md` for the 4-step recipe.

### 5.5.3 `CONTAINS` operator not supported on Firestore REST structuredQuery

When searching by title substring, `op: CONTAINS` returns `HTTP 400: Invalid value at 'structured_query.where.field_filter.op'`. Use `ARRAY_CONTAINS` for array fields or `page through + client-side filter` for string fields. Same `references/find-new-campaign-id-after-copy.md` recipe applies.

## 6. Recommended durable-fix shape — 5-anchor Choice Premise Validation rule

The `## COMMIT: god-mode-directive-missing` fix (Factor A+B in PR #8132) and
PR #8439 (Blood-Scent prose) cover **anchor (a)** and the narrative side of
**anchor (b)** respectively. PR #8441 covers the planning_block side of
**anchor (a)**. PR #8445 (this fix's evidence) covers **anchor (b)** as it
appears in planning_block. Together they cover 3 of 5 anchors.

The complete durable fix needs a **single new section in
`$PROJECT_ROOT/prompts/planning_protocol.md`** between **Field Requirements by Mode**
and **Choice ID Naming**, titled **"Choice Premise Validation (Canonical State
Anchors)"**:

> *"When emitting `planning_block.choices[N].description` or
> `planning_block.thinking`, validate every premise against canonical state
> BEFORE emit. Drop or rewrite any choice whose premise depends on:*
>
> *(a) an NPC marked `retcon` or `suppressed` in
> `custom_campaign_state.god_mode_directives[]`;*
>
> *(b) an NPC whose `npc_data[<X>].location` differs from the player's
> current scene location AND whose presence is required for the choice to
> make sense (i.e. the choice claims "depart to find them" when they're
> already at your location; or "rejoin them" when they are co-present);*
>
> *(c) a future / unrevealed event whose `revealed_at` is still null
> (extending `narrative_system_instruction.md` §5 §1101-1138 from narrative
> prose to planning_block);*
>
> *(d) a canonical milestone or inventory item marked `completed` /
> `discovered` (e.g. gold re-emit, Necropolis Heist re-emit);*
>
> *(e) a `rewards_box.level_up_available=false` state with a `level_up_now`
> choice, OR a `level_up_available=true` state with NO `level_up_now` choice.*
>
> *If a choice's premise fails any of (a)-(e): rewrite the choice to a
> premise that observes canonical state, OR drop the choice and emit a
> different one. The `planning_block.thinking` field must explicitly cite
> the canonical-state line that supports each choice's premise."*

This is advisory (per AGENTS.md "Root-cause-first prompt discipline"); backend
enforcement only after documenting why prompt correction is insufficient.

**Pair with PR #8439** (Blood-Scent prose invention fix, anchor (b) narrative side)
**+ PR #8441** (Directive [3] retcon fix, anchor (a) planning_block side)
**+ PR #8445** (Aegon co-presence fix, anchor (b) planning_block side) —
together they cover the same canonical-state-vs-LLM-prose misalignment class
for all 5 anchors at the planning_block layer.

## Related references

- `references/god-mode-directive-missing-subclasses.md` — directive-persistence bugs (Factor A/B/C/D/E)
- `references/npc-status-persistence-bug.md` — canonical-state anchor bugs
- `references/phenotype-lock-static-evidence.md` — campaign-cluster structural trigger
- `references/static-evidence-sufficient-no-live-turn.md` — when static evidence satisfies §2.1
- `references/find-new-campaign-id-after-copy.md` — find-by-title vs REST API after copy
- `convergent-bug-triage` skill (software-development) — 3+ siblings on same campaign within 24h OR 5+ within 9 days

---

## 7. ≥5 siblings on same campaign → CROSS-LINK instead of file new issue (verified 2026-07-18, Aenar-defeated repro)

Per §3 the cluster trigger fires at ≥3 siblings — at which point we STOP filing per-scene issues. **But what does "stop" look like mechanically?** Verified mechanism from session 2026-07-18 (Aenar-defeated repro → #8444 cross-link):

When the user files another `/repro` on a campaign that already has ≥3 open repro issues AND ≥3 open draft PRs, the durable action is:

1. **DO NOT create `issue N+1`.** It's the same root-cause class as the existing siblings; filing more issues is noise.
2. **Post a cross-link COMMENT on the most recent sibling issue** (the one with the closest sub-class) using `POST /repos/<OWNER>/<REPO>/issues/<N>/comments` via REST (works when GraphQL rate-limited). The comment body is the durable record — it stays in the issue timeline forever, is searchable via `gh issue list --search`, and notifies the assignees.
3. **Post a Slack summary** in the originating thread/ channel with the bug class confirmation + cross-link URL + recommended next-step (extend an existing PR's prompt rule OR branch a fresh root-cause-first worktree).
4. **Wait for human decision on next-step.** Do NOT auto-dispatch an AO worker to "fix" — at this point there are usually multiple open PRs covering different sub-classes, and only the human knows whether to extend PR #8443, branch a new `feat/planning-block-npc-anchor-rule`, or merge the open ones first.

**Comment body template** (adapted from issuecomment-5012707073):

```markdown
## (N+1)th sibling on `<campaign_id>` — <one-line symptom>

Jeffrey just filed another repro via Slack (verbatim):
> *"<user's verbatim quote>"*

Live canonical-state confirms the bug class:
- `<state field> = <contradicting value>` (<field path>)
- `<other contradicting evidence>`

### Root-cause class — same as #<prior sibling 1>, #<prior sibling 2>, ..., #<prior sibling N>

| # | Symptom | Anchor contradiction | Status |
|---|---|---|---|
| #<X> / PR #<X> | <symptom> | <anchor> | OPEN draft |
...
| **#<N+1> (NEW)** | **<this symptom>** | **<this anchor>** | **covered by <fix path>** |

### Why I'm not filing a (N+1)th per-scene issue

Per `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` §3 (cluster trigger ≥3 siblings on same campaign_id, exceeded at N+1): STOP filing per-scene issues and branch a root-cause-first prompt fix that addresses the common anchor layer.

<specific recommendation: extend existing PR X with clauses Y+Z, OR branch fresh `feat/<topic>` from origin/main SHA>

### Evidence

- `<exact Firestore field path + value proving contradiction>`
- All <N> prior repro PRs are visible and tracked.
```

**When to use this mechanism (decision tree):**

| Sibling count | Action |
|---|---|
| 1st repro on this campaign | Normal `/repro` flow — file issue + draft PR per canonical skill |
| 2nd repro | Per §3: flag cluster signal in issue + cross-link 1st sibling |
| 3rd-4th repro | Per §3: STOP filing per-scene issues. Post cross-link comment on most recent sibling. Recommend root-cause-first prompt fix in <existing PR>. |
| 5th+ repro | **Use §7 cross-link mechanism (this section)**. Slack the user with next-step recommendation. WAIT for human decision — do NOT auto-dispatch. |

This mechanism was verified 2026-07-18 on the Aenar-defeated repro (would-have-been #8446): comment posted as `issuecomment-5012707073`, Slack summary posted, no new issue created. Bug class recorded durably in the #8444 timeline.

## 8. bash backtick/bracket pitfall — embedding JSON in `terminal('python3 -c "..."')` (verified 2026-07-18)

**Symptom:** When using `terminal(command="python3 -c \"<inline python with JSON payload containing brackets/backticks/path-like text>\"")`, bash interprets backticks (`` ` ``), `$()`, `[]` (in some contexts), and `{` in the shell BEFORE Python sees the string. Result: bash tries to execute the bracketed text as a command, fails with `command not found`, AND the JSON payload that reaches Python is corrupted (or empty).

**Verified failure mode 2026-07-18:** Posted a Slack-style comment via REST API. The Python source contained:
- Backtick-wrapped field references like `` `current_state.npc_data[\"Aenar Vaelaros\"].status` ``
- Markdown-style references like `` `references/repro-planning-block-and-campaign-cluster-2026-07-18.md` ``
- Bracketed array access like `npc_data[<NPC>].location`
- GitHub URL-like strings

Bash expanded ALL of these to commands. Output showed ~16 `command not found` errors from bash expansion attempts. **HOWEVER, the JSON payload still went through intact** because Python received the `json.dumps` output as a `urllib.request.Request.data` parameter — bash only mangled the SOURCE text, not the runtime data. **The comment was successfully posted (`id=5012707073`)**, but the bash error spam polluted the response stream.

**Anti-pattern:**

```bash
# BAD — bash expands brackets/backticks in the heredoc source
terminal(command='python3 -c "
import json, urllib.request
body = \"\"\"
## Live state:
- npc_data[\"Aenar Vaelaros\"].status = disgraced_front_line
- See references/repro-planning-block-and-campaign-cluster-2026-07-18.md
\"\"\"
print(\"ok\")
"')
```

**Correct pattern — use `execute_code` for any non-trivial Python with brackets/backticks/path-like text in the source:**

```python
# GOOD — execute_code() runs Python directly, no shell interpretation
code = '''
import json, urllib.request, subprocess
tok = subprocess.run(["gh","auth","token"], capture_output=True, text=True, timeout=10).stdout.strip()
body = """## Live state:
- npc_data["Aenar Vaelaros"].status = disgraced_front_line
- See references/repro-planning-block-and-campaign-cluster-2026-07-18.md
"""
payload = json.dumps({"body": body}).encode()
req = urllib.request.Request("https://api.github.com/...", data=payload, headers={...}, method="POST")
with urllib.request.urlopen(req, timeout=30) as resp:
    d = json.loads(resp.read())
    print(f"OK id={d['id']}")
'''
execute_code(code=code)
```

**When `execute_code` is unavailable** (Hermes runtimes without the tool exposed), use a temp file:

```bash
# GOOD — write Python to a file, then execute it
write_file(path="/tmp/post_comment.py", content="<python source with brackets/backticks>")
terminal(command="python3 /tmp/post_comment.py")
```

**Detection heuristic (when to switch from `terminal('python3 -c ...')` to `execute_code` or temp file):**

If the Python source contains ANY of: `[]` (array indexing), `{}` (dict literal), backticks, `$()`, `$(command)`, or paths/URLs that bash could misinterpret — use `execute_code` instead. The heuristic is "would a shell try to interpret any token in this string as syntax?". When in doubt, switch.
