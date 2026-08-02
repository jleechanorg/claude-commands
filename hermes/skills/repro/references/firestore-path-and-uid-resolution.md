# Firestore path map + UID resolution + fresh-worktree venv pitfall

The canonical repro skill (`$HOME/projects/your-project.com/.claude/skills/repro-twin-clone-evidence/SKILL.md`)
documents the workflow but leaves these concrete mechanics under-specified.
This reference fills the gaps with the actual code paths and pitfalls hit
in every repro session.

## 1. Firestore doc-path map (where state actually lives)

```
users/{uid}/campaigns/{cid}                   # campaign metadata (name, title, initial_prompt, selected_prompts, living_world_state — NOT state)
users/{uid}/campaigns/{cid}/game_states/current_state   # THE canonical game state (npc_data, custom_campaign_state, combat_state, …)
users/{uid}/campaigns/{cid}/story/{doc_id}    # one doc per turn — actor=user|gemini, narrative, text, state_updates, planning_block, user_scene_number, …
```

**Common wrong-path errors** that look like missing data:

| Wrong path | Symptom | What to do instead |
|---|---|---|
| `campaigns/{cid}` (top-level collection, no users prefix) | `Document not found` | Add the `users/{uid}/` prefix |
| `users/{uid}/campaigns/{cid}/state` | `state` key missing from top-level | Read `game_states/current_state` instead |
| `users/{uid}/campaigns/{cid}/state.npc_data` | npc_data is empty `{}` | `state` is in `game_states/current_state`, not in the campaign doc |

**The campaign doc top-level** has these keys (NOT state): `created_at`,
`last_played`, `living_world_state`, `use_default_world`, `avatar_url`,
`title`, `initial_prompt`, `selected_prompts`. `living_world_state` only
contains `last_time` and `last_turn` — it is NOT the game state.

## 2. Email → UID resolution (use Firebase Auth, not Firestore)

User docs at `users/{uid}` do **not** carry an `email` field. The user docs
are:

```python
['createdAt', 'lastUpdated', 'settings']
```

So `db.collection("users").where("email","==","<your-email@gmail.com>")` returns
nothing. The canonical path is `scripts/campaign_manager.py find-user <email>`,
which queries Firebase Auth (the production identity provider) and prints
the UID:

```bash
export WORLDAI_DEV_MODE=true
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
PY="$HOME/projects/your-project.com/venv/bin/python"
"$PY" $HOME/projects/your-project.com/scripts/campaign_manager.py find-user $USER@gmail.com
```

Output:
```
✅ Firebase initialized with: $HOME/serviceAccountKey.json
✅ Found user: $USER@gmail.com
🆔 Firebase UID: vnLp2G3m21PJL6kxcuAqmWSOtm73
```

The `copy_campaign.py --dest-email` flag uses this same path internally;
calling it from Python directly requires the `find-user` wrapper.

## 3. Story-doc schema (what each scene actually carries)

Every story doc in `users/{uid}/campaigns/{cid}/story/{doc_id}` has these keys:

| Key | Type | Notes |
|---|---|---|
| `actor` | str | `"user"` or `"gemini"` |
| `user_scene_number` | int \| null | The scene counter the user sees — **null on user-turn docs**, populated on gemini docs that open a scene |
| `part` | int | Turn number (sometimes called `turn_number` on game_states doc) |
| `timestamp` | datetime | UTC |
| `narrative` | str | The long prose from the LLM |
| `text` | str | Same content as `narrative` for many docs — prefer `narrative` |
| `state_updates` | dict | The structured payload the LLM emitted (player_character_data, npc_data, custom_campaign_state, etc.) |
| `entities_mentioned` | list[str] | NPC + PC names referenced |
| `action_resolution` | dict | The deterministic action resolution (often null for narrative-only turns) |
| `planning_block` | dict | LLM-generated planning block (objectives, choices) |
| `directives` | list | God-mode directives injected/active |
| `social_hp_challenge` | dict | Social-skill-challenge state |
| `dice_rolls`, `dice_audit_events` | list | Dice system records |
| `debug_info` | dict | Agent selection, prompt token counts, etc. |

**Scene-iteration pattern**: to find every Gemini turn for scene N, query the
subcollection with `where('user_scene_number','==',N)`. To find the
*user input* that triggered scene N, look for the user-actor doc whose
`timestamp` is the most recent one before the gemini doc with `user_scene_number=N`.

To get the *latest* turns without filtering:
```python
db.collection("users").document(uid).collection("campaigns").document(cid) \
  .collection("story").order_by("timestamp", direction=firestore.Query.DESCENDING) \
  .limit(N).stream()
```

## 4. Fresh-worktree venv pitfall

`git worktree add <path> -b <branch> origin/main` creates a new working tree
with files synced from `origin/main` — but the **virtualenv is NOT copied**.
Running `./venv/bin/python` inside the worktree fails with
`No such file or directory`.

**Wrong:** `cd worktree && ./venv/bin/python scripts/copy_campaign.py ...`
**Right:** use the **main checkout's venv** directly:

```bash
PY="$HOME/projects/your-project.com/venv/bin/python"
cd $HOME/projects/worktree_<slug>   # for PYTHONPATH / relative imports
"$PY" $HOME/projects/your-project.com/scripts/copy_campaign.py ...
```

The venv python at `~/projects/your-project.com/venv/bin/python` is a
symlink to `python3.12` and is gitignored — it lives only in the main
checkout. Always use the absolute path; never rely on `./venv/` inside a
fresh worktree.

(The `vpython` bash function in `~/.bashrc` activates the venv and is
useful for inline commands, but is invisible inside `bash -c "..."` or
when wrapping with `timeout`. Use the absolute path when scripting.)

## 5. Env-var discipline

`copy_campaign.py` and friends raise `ValueError` without `WORLDAI_DEV_MODE=true`.
The full env block (copy-paste):

```bash
export WORLDAI_DEV_MODE=true
export TESTING_AUTH_BYPASS=true
export ALLOW_TEST_AUTH_BYPASS=true
export MCP_TEST_MODE=real
export MOCK_SERVICES_MODE=false
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS="$HOME/serviceAccountKey.json"
```

`WORLDAI_DEV_MODE=true` is **mandatory** — scripts raise without it. The
TESTING_AUTH_BYPASS pair is needed for the auth-gate fallback (see
`references/auth-gate-fallback-repro.md`).

## 6. Pre-state capture discipline (first-touch rule)

For stale persisted-state bugs (SKILL.md §2.1), do NOT call any of these
before the first-touch direct Firestore read:

- `get_campaign_state`
- `download_campaign.py` (it triggers preview/render paths that may migrate state)
- `/api/campaigns/{id}/...` endpoints
- UI loads via the deployed app URL

The first-touch read must be **a direct Firestore document read** of
`users/{uid}/campaigns/{cid}/game_states/current_state`. After capturing,
the next action is the production ingress under test
(`/api/campaigns/{id}/interaction/stream` for gameplay). Then capture
post-state with the same direct-read pattern. See SKILL.md §2.1 for the
full discipline.

## 7. Source-of-truth helpers

These wrappers are canonical — use them, don't reinvent:

| Need | Wrapper |
|---|---|
| email → UID | `scripts/campaign_manager.py find-user <email>` |
| copy campaign | `scripts/copy_campaign.py --find-by-id <CID> --dest-email <email>` |
| download campaign export | `scripts/download_campaign.py --uid <UID> --campaign-id <CID> --output-dir <DIR> --format txt\|json` |
| analytics / cost | `scripts/campaign_manager.py analytics <email> [--month YYYY-MM]` |
| delete (dry-run first) | `scripts/campaign_manager.py delete <UID> "<name>" [--confirm]` |

The `copy_campaign.py --dest-email` early-exits to JSON if you pass `--format json`
— useful for shell composition:

```bash
DEST_UID=$("$PY" scripts/copy_campaign.py --dest-email <your-email@gmail.com> \
  --format json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['dest_uid'])")
```