---
name: download-campaign
description: "Download a Your Project campaign from Firestore, write raw archive + wiki source page. Use when the user says download a campaign, pull this campaign, fetch campaign from firestore, ingest campaign N, copy a campaign by id, or wants to walk a specific WA campaign for analysis. Single-campaign or filtered-batch modes. Wraps and supersedes ad-hoc subprocess-based approaches that hit gRPC FD inheritance bugs."
when_to_use: "Use when the user says: download campaign, fetch this campaign, pull from firestore, ingest campaign, get campaign by id, copy campaign X, batch download recent campaigns, scan last N days, scan for >50 entries, last 2 weeks of campaigns, the campaign wizard walked. Do NOT use for: full wiki page writing (use wiki-ingest), Firestore read only with no download (use firestore_service.get_campaign_by_id directly)."
arguments:
  - campaign_id
  - filters
argument-hint: "[campaign_id or 'recent' or 'batch'] [--min-entries N] [--days N] [--skip-existing] [--campaigns-dir <path>]"
context: inline
allowed-tools: terminal, file
---

# download-campaign — Your Project Firestore → raw archive + wiki source

Canonical home for the "get a campaign out of Firestore and put it on disk" workflow.
This skill exists because ad-hoc one-liners repeatedly hit three pitfalls:

1. **Subprocess-from-Firebase parents gRPC FD inheritance** — `download_campaign.py`
   spawned from a Firebase-initialized process fails with
   `ev_poll_posix.cc:593 FD from fork parent still in poll list: fd(13, generation: 1)`
   on every single download. Fix: call `firestore_service.get_campaign_by_id()` and
   `document_generator.get_story_text_from_context_enhanced()` directly in the same
   process. Never use `download_campaign.py` as a subprocess.

2. **`story` vs `story_entries` subcollection** — The WA campaign story subcollection
   is `story`. Querying `story_entries` returns 0 entries for every campaign.

3. **`.venv` ships without pip and deps** — Run `ensurepip` then install the full
   dep chain (firebase-admin, google-cloud-firestore, flask, pydantic, jsonschema,
   python-docx, fpdf2). Missing any one causes `firestore_service` or
   `document_generator` import failure cascades.

## Quick usage

```bash
cd $HOME/your-project.com

# IMPORTANT: prefix with `env -u MOCK_SERVICES_MODE` to defeat parent-shell
# env trap (see Pitfall #13). Required when the parent shell has
# MOCK_SERVICES_MODE=true exported (common in hermetic-test sessions).
WORLDAI_DEV_MODE=true \
GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
env -u MOCK_SERVICES_MODE \
  .venv/bin/python ~/.hermes_prod/skills/download-campaign/scripts/download_campaign.py \
    --mode one --campaign-id vNU3AAXHd9N7adqWSM2p

# Or batch mode with filters (one user — $USER by default)
.venv/bin/python ~/.hermes_prod/skills/download-campaign/scripts/download_campaign.py \
    --mode batch --min-entries 50 --days 14 --skip-existing

# Or all-users mode (every real user, skip test fixtures; $USER included)
.venv/bin/python ~/.hermes_prod/skills/download-campaign/scripts/download_campaign.py \
    --mode all-users --min-entries 50 --skip-existing
```

The script prints progress, writes:
- `~/llm_wiki/raw/campaigns/<title>_<id8>/<title>_<id8>.txt` (story text)
- `~/llm_wiki/raw/campaigns/<title>_<id8>/<title>_<id8>_game_state.json`
- `~/llm_wiki/wiki/sources/<slug>-<id8>.md` (frontmatter + body)

## Modes

`download_campaign.py` supports three modes:

- `--mode one --campaign-id <id>` — pull a specific campaign (one user, $USER by default).
- `--mode batch [--min-entries N] [--days N] [--skip-existing]` — one user ($USER by default; override with `WA_EMAIL` env).
- `--mode all-users [--min-entries N] [--exclude-$USER] [--skip-existing]` — every real user across `auth.list_users()`, filtered by `is_test_email()`. Use this for the daily cron (`wiki-campaign-daily-ingest.sh`).

### `--all-users` mode (multi-user batch)

Walks `auth.list_users()` paginated, filters out test fixtures via
`is_test_email()` (matches `test`, `anon`, `dev-runner`, `example.com`,
`jleechantest` — same tokens as `wa-prod-data-query/scripts/query_real_users.py`),
then iterates `query_candidates()` + `download_one()` per real user. $USER
is **included by default**; pass `--exclude-$USER` to skip him.

Each ingested campaign's wiki frontmatter carries `user_email:` + `user_uid:`
so multi-user pages are auditable in the `jleechanorg/llm-wiki` private repo.

Use case: the daily `ai.$USER.wiki-campaign-daily-ingest` launchd job uses
`--mode all-users --min-entries 50 --skip-existing` to keep the private
llm-wiki repo in sync with every real WA user's over-50-scene campaigns.

## Phases

### Phase 1 — Venv bootstrap (one-time per machine)

The WA `.venv` ships without pip. Run from `~/your-project.com`:

```bash
.venv/bin/python -m ensurepip
.venv/bin/python -m pip install \
  firebase-admin google-cloud-firestore \
  flask pydantic jsonschema python-docx fpdf2
```

All five are required — `flask` and `jsonschema` are transitive imports of
`firestore_service` and `document_generator`. Missing `pydantic` breaks
`firestore_service.get_campaign_by_id()`. Missing `python-docx` breaks
`document_generator.get_story_text_from_context_enhanced()`. Missing `fpdf2`
breaks `document_generator` import. **Install all of them, every time.**

### Phase 2 — sys.path ordering (every run)

The `clock_skew_credentials` module lives in `$PROJECT_ROOT/`, not the project root.
Path order matters — insert `mvp_site` BEFORE the root:

```python
sys.path.insert(0, "$HOME/your-project.com/mvp_site")
sys.path.insert(0, "$HOME/your-project.com")
```

`WORLDAI_DEV_MODE=true` is **required** for any local Firestore query. The
clock-skew validator raises `ValueError` if `WORLDAI_GOOGLE_APPLICATION_CREDENTIALS`
is set without `WORLDAI_DEV_MODE=true` to explicitly acknowledge dev mode.

### Phase 3 — Auth + clock skew

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser("~/serviceAccountKey.json")
os.environ["WORLDAI_DEV_MODE"] = "true"

from clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()  # adjusts time by -720 seconds

import firebase_admin
from firebase_admin import auth, credentials, firestore
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.expanduser("~/serviceAccountKey.json"))
    firebase_admin.initialize_app(cred)

user = auth.get_user_by_email("$USER@gmail.com")
uid = user.uid  # do not use Firestore user docs for email lookup
```

### Phase 4 — Pull campaign data

```python
import firestore_service
import document_generator
from google.cloud import firestore

campaign_id = "vNU3AAXHd9N7adqWSM2p"
campaign_data, story_context = firestore_service.get_campaign_by_id(uid, campaign_id)

# campaign_data is a Firestore DocumentSnapshot
cd = campaign_data.to_dict() if hasattr(campaign_data, "to_dict") else campaign_data
title = cd.get("name", cd.get("title", "Untitled"))

# story_context is a list of story entry dicts
story_text = document_generator.get_story_text_from_context_enhanced(
    story_context, include_scenes=True
)

# Game state (separate call)
gs = firestore_service.get_campaign_game_state(uid, campaign_id)
gs_data = gs.to_dict() if gs is not None else {}
```

**Cross-check the helper — see Pitfall #8 below.** Some campaigns (e.g.
`WlfgzI0ReBrFkmagW3wU` "Nocturne bg3 v5 succubus copy") return a
zero-length story_context from `firestore_service.get_campaign_by_id`
even though the `story` subcollection has hundreds of entries. The
helper has at least one bug path that drops entries silently. Before
trusting any "0 entries" result, cross-check with a direct
aggregation count and fall back to a direct stream if the helper
count disagrees with the direct count. The driver uses this pattern:

```python
db = firestore.client()
direct_count = int(db.collection("users").document(uid)
                  .collection("campaigns").document(campaign_id)
                  .collection("story").count().get()[0][0].value)
if direct_count > len(story_context):
    # helper returned truncated/missing — pull directly
    docs = list(db.collection("users").document(uid)
                .collection("campaigns").document(campaign_id)
                .collection("story").stream())
    story_context = [d.to_dict() for d in docs]
    story_text = document_generator.get_story_text_from_context_enhanced(
        story_context, include_scenes=True
    )
```

### Phase 5 — Idempotent writes

Two campaigns with the same title (e.g. "Vespera Thul (copy)") must NOT
overwrite each other. Use `campaign_id[:8]` suffix in BOTH the raw archive
path and the wiki source path:

```python
slug = slugify(title)
wiki_path = Path(f"~/llm_wiki/wiki/sources/{slug}-{campaign_id[:8]}.md").expanduser()
raw_dir = Path(f"~/llm_wiki/raw/campaigns/{campaign_id}").expanduser()
```

Idempotency check: skip if `wiki_path.exists()` AND its size > 500 bytes
(skips blank/partial frontmatter-only stubs).

### Phase 5b — Verify the export (mandatory for batch runs)

After a batch run, re-pull each exported campaign from Firestore and
byte-diff the live `get_story_text_from_context_enhanced` output against
the on-disk raw `.txt`. Campaigns are live — users keep typing in another
tab while a batch runs, so any candidate that took >1s to export can
have a newer entry by the time the verify pass runs.

Pass criteria:
- `live_count == on-disk entry_count` from frontmatter (no story loss)
- `len(live_text)` within 1% of `len(on_disk_text)` (allow tiny drift from
  new entries; >5% means the export raced with writes and should be
  re-pulled)

Output a `/tmp/verify_<batch_tag>_report.jsonl` with one row per
candidate, then run a repair pass for any row with `drift_pct > 1.0`
(only those — re-pulling everyone wastes ~3 minutes on a 228-campaign batch).

For the 2026-07-12 batch-50plus run, 28/228 candidates drifted between
batch and verify due to user activity; repair pass re-pulled only those
in ~30s. Total verify+repair wall time: under 4 minutes for 228 candidates.

### Phase 6 — Output contract

Each campaign gets:

1. **Raw archive** at `~/llm_wiki/raw/campaigns/<id8>/<safe_title>_<id8>.txt`
   — full story text, scenes included.
2. **Game state** at `~/llm_wiki/raw/campaigns/<id8>/<safe_title>_<id8>_game_state.json`
   — full Firestore game_state doc, JSON serialised with `default=str` for datetimes.
3. **Wiki source page** at `~/llm_wiki/wiki/sources/<slug>-<id8>.md` — frontmatter:

   ```yaml
   ---
   title: "<title>"
   type: source
   tags: [campaign, worldarchitect, <slug>]
   date: YYYY-MM-DD
   source_file: <raw path>
   campaign_id: <id>
   entry_count: <N>
   last_updated: <ts>
   ingest_batch: <batch tag>
   ---
   ```

   Body: the story text, truncated to 100,000 chars per page.

4. **Manifest entry** appended to `/tmp/campaign_ingest_manifest.jsonl`.

## Batch mode filters

```bash
--min-entries 50      # only campaigns with ≥N story entries
--days 14             # only campaigns active in last N days (by max story timestamp)
--skip-existing       # skip if wiki page already exists with content
--campaigns-dir <path> # output raw archive dir (default /tmp/campaign_downloads)
```

## Discovery scan — entry-count recipe (replaces `.limit(2000).stream()`)

For scanning $USER's full campaign list (1,000+ campaigns in practice),
do NOT use `.limit(2000).stream()` for entry counts — it caps at 2000 and
gives wrong answers for any campaign with more. Use Firestore aggregation
queries (preferred) or a single `.stream()` with no limit when count > 2000:

```python
db = firestore.client()
# Preferred: aggregation count (1 read, no document materialization)
agg = (db.collection("users").document(uid).collection("campaigns")
       .document(cid).collection("story").count().get())
entry_count = int(agg[0][0].value)

# Fallback for when aggregation isn't enough (need actual entries to sort by
# timestamp / author etc.):
docs = list(db.collection("users").document(uid).collection("campaigns")
            .document(cid).collection("story").stream())
entry_count = len(docs)
last_scene_ts = max(
    (d.to_dict().get("timestamp") or d.to_dict().get("created_at") for d in docs),
    default=None,
)
```

For the 1,080 $USER campaign discovery scan (2026-07-12 batch) the
aggregation path returned correct counts in ~3 minutes total wall time.
Scanning all story subcollections in one process is safe — gRPC FD bug
only fires when `download_campaign.py` is spawned as a subprocess.

## Pitfalls (this list IS the skill — review before running)

1. **Never subprocess `download_campaign.py`** — gRPC FD inheritance
   (`ev_poll_posix.cc:593 FD from fork parent still in poll list`) makes
   every download fail. Always inline.
2. **Subcollection is `story`, not `story_entries`** — `story_entries`
   returns 0 entries. The 2026-05-31 discovery cost a full day of confusion.
3. **`WORLDAI_DEV_MODE=true` is mandatory** — the clock-skew validator
   raises `ValueError: WORLDAI_GOOGLE_APPLICATION_CREDENTIALS requires
   WORLDAI_DEV_MODE=true. Set WORLDAI_DEV_MODE=true to explicitly acknowledge
   development mode.` without it.
4. **`/private/tmp/types.py` collision** — if running from `/tmp/`, a stale
   `types.py` can shadow the stdlib module, causing
   `ImportError: cannot import name 'GenericAlias'`. Fix: `rm /private/tmp/types.py`.
5. **2000-entry Firestore limit** — counting entries with `.limit(2000).stream()`
   shows exactly 2000 for any campaign with 2000+ entries. Use aggregation
   queries or no limit for precise counts. For ≥50 detection, limit(2000) is
   fine since the threshold is well below the cap.
6. **Slug collision on duplicates** — campaigns with the same name (e.g.
   "Vespera Thul (copy)") must use `campaign_id[:8]` in BOTH raw dir name
   AND wiki page filename, or the second copy overwrites the first.
7. **`.venv` dep chain** — must install `flask pydantic jsonschema python-docx fpdf2`
   in addition to `firebase-admin google-cloud-firestore`. The five-app stack
   import chain pulls in all of them transitively.
8. **`firestore_service.get_campaign_by_id` can return an empty story list** —
   some campaigns silently drop to `len(story_context)==0` even though their
   `story` subcollection has hundreds of entries. Discovered 2026-07-12 on
   `WlfgzI0ReBrFkmagW3wU` ("Nocturne bg3 v5 succubus copy", 554 entries on
   disk, helper returns 0). Cause: an internal helper bug in
   `firestore_service.get_campaign_by_id` — root-cause not yet isolated, but
   the failure mode is consistent (helper returns 0, direct collection stream
   returns full count). Fix: always cross-check with
   `db.collection(...).collection("campaigns").document(cid).collection("story").count().get()`
   and fall back to a direct `.stream()` if the direct count > helper count.
   Treat any "0 entries" result from the helper as a bug, not as data.
9. **macOS BSD `find -newermt @<epoch>` is silently broken — use a human-readable
   date string instead.** GNU `find` accepts `-newermt @1784583090` (epoch
   seconds). macOS BSD `find` does NOT — it silently returns 0 matches and
   your batch script will look like "no work was done" when in fact it wrote
   a dozen new files. This bites any launchd-managed batch script that uses
   `find -newermt` for change detection. Verified 2026-07-20 on
   `wiki-campaign-daily-ingest.sh`: after the `--mode all-users` ingest wrote
   12 new wiki pages, the shell's `find -newermt "@$RUN_START_TIME"` returned
   0, the script's "Files added/modified: added=0" branch fired, and the
   git push was skipped — leaving the 12 new files uncommitted in the
   working tree. Fix: store BOTH the epoch AND a formatted date string
   (`RUN_START_DATE=$(date -r "$RUN_START_TIME" '+%Y-%m-%d %H:%M:%S')`) and
   use `-newermt "$RUN_START_DATE"` — works on both BSD and GNU find. The
   `4 minutes ago` relative form also works but is unreliable when the run
   wall-clock differs from the script's mtime capture.

10. **`slack_post_message | tee` swallows the function's return code.** When
    wrapping `slack_post_message` (or any helper that can fail) inside an
    `if` guard with `| tee`, the pipeline's exit code is tee's, not the
    helper's — Slack posts silently fail and the script logs "sent". Always
    capture `$?` via `$()` command substitution:
    ```bash
    local out rc
    out=$(slack_post_message "$CHAN" "$TEXT" 2>&1)
    rc=$?
    echo "$out" | tee -a "$LOG" >/dev/null
    if [[ $rc -eq 0 ]]; then log "sent"; else log "WARN: rc=$rc"; fi
    ```
    Caught 2026-07-20: bot was posting to #ai-general which it wasn't a
    member of, but the script reported "Slack notification sent" anyway.

11. **`[[ -z "$X" ]] && X=0` returns non-zero when X is non-empty** — the `&&`
    short-circuits to the false branch, and the whole expression exits 1.
    Combined with an ERR trap (or `set -e`), this fires spurious failure
    notifications on every successful run. Use explicit assignment:
    ```bash
    # WRONG: ERR trap fires on every populated X
    eval "[[ -z \"\${$v}\" ]] && $v=0"
    # RIGHT: plain assignment, always exits 0
    eval "val=\${$v}"
    val=$(printf '%s' "$val" | tr -cd '0-9')
    if [[ -z "$val" ]]; then val=0; fi
    eval "$v=$val"
    ```
    Caught 2026-07-20: the wiki-campaign-daily-ingest.sh ingest-counter
    loop was firing `notify_error()` on every run because the variable
    assignment used the wrong pattern.

12. **mcp_agent_mail bot is NOT a member of every channel.** The bot
    (`U0A4G7LDJ4R`, app `A0A3WSV6BM1`) is in `#life` (`C0AMM2B4319`) and
    `#all-$USER-ai` (`C09GRLXF9GR`) but NOT in `#ai-general`
    (`C0AJQ5M0A0Y`). Verify with `conversations.info` before picking a
    notification channel, or you'll get silent failures. To re-invite the
    bot to a new channel, see `slack-mcp-mail-bot-reinstall` skill §6
    (Aside-driven `slack.getClient()` recipe). For the daily wiki-campaign
    cron, #life is the safe default.

13. **`MOCK_SERVICES_MODE=true` parent shell env silently redirects Firestore to an in-memory mock.** Several launchd and
    shell sessions export `MOCK_SERVICES_MODE=true` (it's set in `~/.bashrc` / `~/.bash_profile` for hermetic-test tooling).
    When `download_campaign.py` runs under such a parent, `firestore_service.get_firestore_client()` detects the env var
    and returns a singleton in-memory client (`firestore_service.py` L3567-3575). Every Firestore read then returns
    "data not found" or empty collections — the script logs `MOCK_SERVICES_MODE enabled - creating singleton in-memory
    Firestore client` and exits with `RuntimeError: no data for <campaign_id>` even though the real campaign has
    hundreds of entries. **Detection**: scan the script's stdout for that exact log line; if present, the env var is
    active and you must drop it. **Fix**: run with `env -u MOCK_SERVICES_MODE` prefix on the command line
    (`env -u MOCK_SERVICES_MODE .venv/bin/python ...`). Always add this prefix in any download / ingest script
    unless you specifically want the mock client. Verified 2026-07-26 on `qoQtHsU7DxZnR24VNU9w` (Visenya v9):
    first run hit `RuntimeError: no data for qoQtHsU7DxZnR24VNU9w`; with `env -u` it pulled 824 entries in ~3s.

## Game state key fields (for analysis)

- `player_character_data` — PC stats, features, equipment, relationships.
  Note: no personality fields (motivation, fear, speech patterns).
- `npc_data` — dict keyed by NPC name; entries have `level`, `role`,
  `relationships`, sometimes `mbti` / `alignment` (labels only, no deep profile).
- `custom_campaign_state` — `core_memories` (list of narrative milestone
  strings), `active_missions`, `active_constraints`, `faction_minigame`,
  `god_mode_directives`.
- `npc_agendas` — often empty dict even in long campaigns.
- `combat_state` — current encounter data.

## Related

- `wiki-ingest` — broader skill covering ported-source, Firestore batch, and
  external-source ingest paths.
- `~/llm_wiki/tools/batch_campaign_ingest_inline.py` — older version of the
  batch tool (slug-only paths, no id8 suffix). Superseded by the script
  under `scripts/download_campaign.py` in this skill.
- `~/llm_wiki/wiki/sources/wa-firestore-campaign-schema.md` — schema reference.
- `references/batch-50plus-2026-07-12.md` — session notes from the
  228-campaign batch run: scan numbers, verification numbers, driver
  scripts, Git workflow, daily-cron opportunity.
- `references/multi-user-batch-rollout-2026-07-20.md` — session notes from
  extending the daily cron to all real users (auth.list_users + is_test_email
  filter). Includes the `find -newermt @<epoch>` bug caught during
  verification.

## Tests

- `tests/test_slugify.py` — slug generation, including id8 suffix.
- `tests/test_idempotent_path.py` — verifies no slug collision for
  duplicate titles ("Vespera Thul (copy)" 11× → 11 unique paths).
- `tests/test_dependencies.py` — verifies the .venv dep chain is present.

Run: `cd ~/.hermes_prod/skills/download-campaign && python3 -m unittest discover -s tests`
