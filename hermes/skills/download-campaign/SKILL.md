---
name: download-campaign
description: "Download a YourProject campaign from Firestore, write raw archive + wiki source page. Use when the user says download a campaign, pull this campaign, fetch campaign from firestore, ingest campaign N, copy a campaign by id, or wants to walk a specific WA campaign for analysis. Single-campaign or filtered-batch modes. Wraps and supersedes ad-hoc subprocess-based approaches that hit gRPC FD inheritance bugs."
when_to_use: "Use when the user says: download campaign, fetch this campaign, pull from firestore, ingest campaign, get campaign by id, copy campaign X, batch download recent campaigns, scan last N days, scan for >50 entries, last 2 weeks of campaigns, the campaign wizard walked. Do NOT use for: full wiki page writing (use wiki-ingest), Firestore read only with no download (use firestore_service.get_campaign_by_id directly)."
arguments:
  - campaign_id
  - filters
argument-hint: "[campaign_id or 'recent' or 'batch'] [--min-entries N] [--days N] [--skip-existing] [--campaigns-dir <path>]"
context: inline
allowed-tools: terminal, file
---

# download-campaign — YourProject Firestore → raw archive + wiki source

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
cd /Users/$USER/your-project.com
WORLDAI_DEV_MODE=true \
GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
.venv/bin/python ~/.hermes_prod/skills/download-campaign/scripts/download_campaign.py \
    --mode one --campaign-id vNU3AAXHd9N7adqWSM2p

# Or batch mode with filters
.venv/bin/python ~/.hermes_prod/skills/download-campaign/scripts/download_campaign.py \
    --mode batch --min-entries 50 --days 14 --skip-existing
```

The script prints progress, writes:
- `~/llm_wiki/raw/campaigns/<title>_<id8>/<title>_<id8>.txt` (story text)
- `~/llm_wiki/raw/campaigns/<title>_<id8>/<title>_<id8>_game_state.json`
- `~/llm_wiki/wiki/sources/<slug>-<id8>.md` (frontmatter + body)

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

The `clock_skew_credentials` module lives in `your_app/`, not the project root.
Path order matters — insert `mvp_site` BEFORE the root:

```python
sys.path.insert(0, "/Users/$USER/your-project.com/mvp_site")
sys.path.insert(0, "/Users/$USER/your-project.com")
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
- `~/llm_wiki/tools/batch_campaign_ingest_inline.py` — older version of
  the batch tool (slug-only paths, no id8 suffix). Superseded by the
  script under `scripts/download_campaign.py` in this skill.
- `~/llm_wiki/wiki/sources/wa-firestore-campaign-schema.md` — schema reference.

## Tests

- `tests/test_slugify.py` — slug generation, including id8 suffix.
- `tests/test_idempotent_path.py` — verifies no slug collision for
  duplicate titles ("Vespera Thul (copy)" 11× → 11 unique paths).
- `tests/test_dependencies.py` — verifies the .venv dep chain is present.

Run: `cd ~/.hermes_prod/skills/download-campaign && python3 -m unittest discover -s tests`
