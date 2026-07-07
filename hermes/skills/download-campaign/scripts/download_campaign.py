#!/usr/bin/env python3
"""download_campaign.py — single + batch WA campaign download.

Modes:
  --mode one   --campaign-id <id>            # pull a specific campaign
  --mode batch [--min-entries N] [--days N] # pull all matching filters

Required env:
  WORLDAI_DEV_MODE=true
  GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json

Run from inside ~/your-project.com or with the .venv on PATH.

The script inlines the Firestore call (no subprocess) to avoid the
gRPC FD inheritance bug. NEVER spawn download_campaign.py as a child process
of a Firebase-initialized parent — see SKILL.md "Pitfalls #1".
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Defaults — override via env or args
WORLDARCHITECT_REPO = Path(os.environ.get("WORLDAI_REPO", "$HOME/your-project.com"))
CREDENTIALS = Path(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", os.path.expanduser("~/serviceAccountKey.json")))
EMAIL = os.environ.get("WA_EMAIL", "$USER@gmail.com")
WIKI_SOURCES = Path(os.environ.get("WA_WIKI_SOURCES", "$HOME/llm_wiki/wiki/sources"))
RAW_ROOT = Path(os.environ.get("WA_RAW_ROOT", "$HOME/llm_wiki/raw/campaigns"))
MANIFEST = Path("/tmp/campaign_ingest_manifest.jsonl")

# Path order: mvp_site FIRST (for clock_skew_credentials), then root
sys.path.insert(0, str(WORLDARCHITECT_REPO / "mvp_site"))
sys.path.insert(0, str(WORLDARCHITECT_REPO))

from clock_skew_credentials import apply_clock_skew_patch  # noqa: E402
apply_clock_skew_patch()

import firebase_admin  # noqa: E402
from firebase_admin import auth, credentials, firestore  # noqa: E402
import firestore_service  # noqa: E402
import document_generator  # noqa: E402


def slugify(text: str) -> str:
    """Title to kebab-case, max 80 chars."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:80]


def init_firebase():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS)
    os.environ["WORLDAI_DEV_MODE"] = "true"
    if not firebase_admin._apps:
        cred = credentials.Certificate(str(CREDENTIALS))
        firebase_admin.initialize_app(cred)
    return firestore.client()


def download_one(uid: str, campaign_id: str, title: str, entry_count: int = 0,
                 campaigns_dir: Path = None) -> dict:
    """Download a single campaign — returns manifest entry or raises."""
    print(f"  Downloading [{entry_count or '?'}] {title} ({campaign_id[:8]})", flush=True)

    campaign_data, story_context = firestore_service.get_campaign_by_id(uid, campaign_id)
    if campaign_data is None or story_context is None:
        raise RuntimeError(f"no data for {campaign_id}")
    if not isinstance(story_context, list):
        raise RuntimeError(f"story is not a list: {type(story_context)}")

    try:
        story_text = document_generator.get_story_text_from_context_enhanced(
            story_context, include_scenes=True
        )
    except (AttributeError, TypeError):
        story_text = document_generator.get_story_text_from_context(story_context)

    base = campaigns_dir or RAW_ROOT
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:50]
    camp_dir = base / campaign_id
    camp_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{safe_title}_{campaign_id[:8]}"
    raw_path = camp_dir / f"{prefix}.txt"
    raw_path.write_text(story_text, errors="replace")

    # Game state
    try:
        gs = firestore_service.get_campaign_game_state(uid, campaign_id)
        gs_data = gs.to_dict() if gs is not None else {}
        gs_path = camp_dir / f"{prefix}_game_state.json"
        gs_path.write_text(json.dumps(gs_data, indent=2, default=str), errors="replace")
    except Exception as e:
        print(f"    [WARN] game state: {e}")

    # Wiki source page (id8-suffixed to avoid slug collision)
    base_slug = slugify(title)
    wiki_path = WIKI_SOURCES / f"{base_slug}-{campaign_id[:8]}.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    frontmatter = (
        "---\n"
        f'title: "{title}"\n'
        "type: source\n"
        f"tags: [campaign, worldarchitect, {base_slug}]\n"
        f"date: {today}\n"
        f"source_file: {raw_path}\n"
        f"campaign_id: {campaign_id}\n"
        f"entry_count: {entry_count}\n"
        "ingest_batch: download-campaign-skill\n"
        "---\n\n"
    )
    body = story_text[:100000]
    wiki_path.write_text(frontmatter + body, errors="replace")
    print(f"  ✅ Wrote: {wiki_path.name}  ({len(story_text)} chars)", flush=True)

    return {
        "title": title,
        "campaign_id": campaign_id,
        "entry_count": entry_count,
        "wiki_path": str(wiki_path),
        "raw_path": str(raw_path),
        "story_chars": len(story_text),
    }


def query_candidates(uid: str, min_entries: int = 0, days: int = 0) -> list[dict]:
    """Scan all campaigns, return those matching the filters."""
    db = init_firebase()
    campaigns_ref = db.collection("users").document(uid).collection("campaigns")
    cutoff = datetime.now(timezone.utc) - timedelta(days=days) if days else None

    results = []
    for camp in campaigns_ref.stream():
        data = camp.to_dict() or {}
        title = data.get("name", data.get("title", "Untitled"))
        story_ref = camp.reference.collection("story")
        entry_count = sum(1 for _ in story_ref.limit(2000).stream())
        if entry_count < min_entries:
            continue

        # Date filter — use campaign doc last_updated, then fall back to
        # max(timestamp) of story entries
        last_updated = data.get("last_updated") or data.get("updated_at") or data.get("lastActivity")
        if cutoff and not last_updated:
            try:
                last_doc = next(
                    story_ref.order_by("timestamp", direction=firestore.Query.DESCENDING)
                    .limit(1).stream(),
                    None,
                )
                if last_doc:
                    last_updated = last_doc.get("timestamp") or last_doc.get("created_at")
            except Exception:
                pass

        if cutoff and last_updated and hasattr(last_updated, "timestamp"):
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            if last_updated < cutoff:
                continue

        results.append({
            "campaign_id": camp.id,
            "title": title,
            "entry_count": entry_count,
            "last_updated": str(last_updated) if last_updated else "",
        })
    results.sort(key=lambda c: -c["entry_count"])
    return results


def main():
    p = argparse.ArgumentParser(description="Your Project campaign downloader")
    p.add_argument("--mode", choices=["one", "batch"], required=True)
    p.add_argument("--campaign-id", help="for --mode one")
    p.add_argument("--min-entries", type=int, default=0)
    p.add_argument("--days", type=int, default=0, help="filter to last N days of activity")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--campaigns-dir", default=str(RAW_ROOT))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--tag", default="download-campaign-skill")
    args = p.parse_args()

    campaigns_dir = Path(args.campaigns_dir)
    campaigns_dir.mkdir(parents=True, exist_ok=True)

    init_firebase()
    user = auth.get_user_by_email(EMAIL)
    uid = user.uid
    print(f"UID: {uid}")

    if args.mode == "one":
        if not args.campaign_id:
            print("--campaign-id required for --mode one", file=sys.stderr)
            sys.exit(1)
        result = download_one(uid, args.campaign_id, args.campaign_id, campaigns_dir=campaigns_dir)
        with open(MANIFEST, "a") as f:
            f.write(json.dumps(result) + "\n")
        return

    # batch
    print(f"Scanning campaigns (min-entries={args.min_entries}, days={args.days})...")
    t0 = time.time()
    candidates = query_candidates(uid, args.min_entries, args.days)
    print(f"Found {len(candidates)} candidates in {time.time()-t0:.1f}s")

    if args.dry_run:
        for c in candidates:
            print(f"  {c['entry_count']:5d} | {c['title']} ({c['campaign_id'][:8]})")
        return

    results, errors, skipped = [], 0, 0
    for i, c in enumerate(candidates):
        print(f"\n[{i+1}/{len(candidates)}]", flush=True)

        if args.skip_existing:
            slug = slugify(c["title"])
            wp = WIKI_SOURCES / f"{slug}-{c['campaign_id'][:8]}.md"
            if wp.exists() and len(wp.read_text(errors="replace")) > 500:
                print(f"  ⏭️  Exists: {wp.name}")
                skipped += 1
                continue

        try:
            r = download_one(uid, c["campaign_id"], c["title"], c["entry_count"], campaigns_dir)
            results.append(r)
        except Exception as e:
            print(f"  [ERROR] {c['campaign_id'][:8]}: {e}", flush=True)
            errors += 1

    with open(MANIFEST, "a") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")

    print(f"\n=== Done ===")
    print(f"Downloaded: {len(results)}")
    print(f"Skipped:    {skipped}")
    print(f"Errors:     {errors}")
    print(f"Manifest:   {MANIFEST}")


if __name__ == "__main__":
    main()
