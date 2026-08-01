#!/usr/bin/env python3
"""
per_scene_dialog_audit.py — end-to-end driver for wa-campaign-content-analysis.

Pulls the last N campaigns with >= M entries from $USER's Firestore,
streams the `story` subcollection, classifies each gemini scene for
PC vs NPC dialog, aggregates per agent, and writes summary JSON + JSONL dump.

Usage:
    WORLDAI_DEV_MODE=true GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json \
        .venv/bin/python ~/.hermes/skills/worldarchitect/wa-campaign-content-analysis/scripts/per_scene_dialog_audit.py \
        --last 10 --min-entries 50 --out-dir ~/.hermes/dialog_review_2026-07-13

Output:
    <out-dir>/all_scenes_by_agent.jsonl  — one row per scene
    <out-dir>/agent_summary.json         — per-agent medians + % silent + % two-way
    <out-dir>/last_n_campaigns.json      — candidate campaign list

Verified: 2026-07-13 on 2,464 gemini scenes in 10 campaigns. Total wall time ~15s
on a single-thread `execute_code` call (after venv + auth setup).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

# --- Environment setup (same as download-campaign Phases 1-3) ---
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", os.path.expanduser("~/serviceAccountKey.json"))
os.environ.setdefault("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS", os.path.expanduser("~/serviceAccountKey.json"))
os.environ.setdefault("WORLDAI_DEV_MODE", "true")

# Insert mvp_site BEFORE project root (path ordering matters)
WA_ROOT = "$HOME/your-project.com"
sys.path.insert(0, f"{WA_ROOT}/mvp_site")
sys.path.insert(0, WA_ROOT)

# --- Imports (after path setup) ---
import firebase_admin  # noqa: E402
from clock_skew_credentials import apply_clock_skew_patch  # noqa: E402
from firebase_admin import auth, credentials, firestore  # noqa: E402

apply_clock_skew_patch()
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(os.path.expanduser("~/serviceAccountKey.json")))

# --- Constants ---
USER_EMAIL = "$USER@gmail.com"

# Dialog classifier constants (mirror SKILL.md Phase 4)
DIALOG_PATTERNS = [
    re.compile(r'"([^"\n]{2,500})"'),
    re.compile(r"'([^'\n]{2,500})'"),
    re.compile(r'"([^"\n]{2,500})"'),
    re.compile(r"'([^'\n]{2,500})'"),
]
VERB_DIALOG_RE = re.compile(
    r"\b([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?)\s+"
    r"(?:said|asked|replied|shouted|whispered|cried|answered|murmured|muttered|stated|declared|"
    r"exclaimed|gasped|snapped|hissed|sneered|smiled|laughed|grumbled|rejoined|added|continued|noted|"
    r"remarked|observed|responded|countered|suggested|insisted|protested|begged|pleaded|warned|"
    r"told|commanded|ordered|demanded|inquired|queried|wondered|breathed|sighed|drawled|babbled)\b"
    r"[^.!?\n]{0,80}",
    flags=re.MULTILINE,
)
NAME_COLON_RE = re.compile(
    r"^\s*([A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)?)\s*:\s*([^\n]{2,500})",
    flags=re.MULTILINE,
)
FIRST_PERSON_RE = re.compile(r"^(I |I'm |I've |I'll |I'd |My |We |Our |Me |Im |Ive |Ill |Id )", re.IGNORECASE)
MECHANIC_LABELS = frozenset({
    "Intelligence Check", "Wisdom Check", "Charisma Check", "Persuasion Check",
    "Deception Check", "Intimidation Check", "Performance Check", "Insight Check",
    "Social HP", "Resistance", "Objective", "Outcome", "IMMUNITIES", "DISSONANCE",
    "IDENTITY", "DIVINE BONUSES", "LEVEL", "DIVINE LEVERAGE", "XP",
    "Administrative Log", "Strategic Note", "Session Summary",
})


def norm(v):
    """Normalize Firestore timestamp to epoch seconds float."""
    if v is None:
        return 0.0
    if hasattr(v, "timestamp"):
        try:
            return float(v.timestamp())
        except Exception:
            pass
    if isinstance(v, (int, float)):
        if v > 1e12:
            return float(v) / 1000.0
        return float(v)
    return 0.0


def get_pc_name(db, uid, cid):
    """Pull player_character_data.name from game_states/current_state."""
    gs = db.collection("users").document(uid).collection("campaigns").document(cid).collection("game_states").document("current_state").get()
    if gs.exists:
        g = gs.to_dict() or {}
        pc = g.get("player_character_data") or {}
        return pc.get("name") or pc.get("character_name")
    return None


def count_dialog(text, pc_name):
    """Return (pc_lines, npc_lines, speakers) for a single scene text."""
    if not text:
        return 0, 0, []
    pc_lines = npc_lines = 0
    speakers = []
    seen = set()
    quoted = []
    for pat in DIALOG_PATTERNS:
        for m in pat.finditer(text):
            line = m.group(1).strip()
            key = line[:50]
            if key in seen:
                continue
            seen.add(key)
            quoted.append(line)
    for q in quoted:
        if FIRST_PERSON_RE.match(q):
            pc_lines += 1
        else:
            npc_lines += 1
    for m in NAME_COLON_RE.finditer(text):
        sn = m.group(1).strip()
        line_text = m.group(2).strip().strip("'\"")
        if not line_text:
            continue
        if sn in MECHANIC_LABELS:
            continue
        if pc_name and sn.lower() == pc_name.lower():
            pc_lines += 1
        else:
            npc_lines += 1
            speakers.append(sn)
    for m in VERB_DIALOG_RE.finditer(text):
        sn = m.group(1).strip()
        if sn in MECHANIC_LABELS:
            continue
        if pc_name and sn.lower() == pc_name.lower():
            pc_lines += 1
        else:
            npc_lines += 1
            speakers.append(sn)
    return pc_lines, npc_lines, list(set(speakers))


def find_last_n_with_min_entries(db, uid, last_n, min_entries):
    """Return list of {id, name, entries, last_ts_norm} sorted by last_ts DESC."""
    camps = db.collection("users").document(uid).collection("campaigns").stream()
    out = []
    for c in camps:
        cid = c.id
        cd = c.to_dict() or {}
        name = cd.get("name") or cd.get("title") or "Untitled"
        agg = db.collection("users").document(uid).collection("campaigns").document(cid).collection("story").count().get()
        entry_count = int(agg[0][0].value)
        if entry_count < min_entries:
            continue
        q = (db.collection("users").document(uid).collection("campaigns").document(cid)
             .collection("story").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(1).stream())
        docs = list(q)
        last_ts_raw = None
        if docs:
            d = docs[0].to_dict() or {}
            last_ts_raw = d.get("timestamp") or d.get("created_at")
        out.append({"id": cid, "name": name, "entries": entry_count, "last_ts_norm": norm(last_ts_raw), "last_ts_raw": str(last_ts_raw)})
    out.sort(key=lambda c: c["last_ts_norm"], reverse=True)
    return out[:last_n]


def stream_story(db, uid, cid):
    """Stream story subcollection in ASC timestamp order."""
    return list(db.collection("users").document(uid).collection("campaigns").document(cid)
                .collection("story").order_by("timestamp", direction=firestore.Query.ASCENDING).stream())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--last", type=int, default=10, help="last N campaigns to analyze")
    ap.add_argument("--min-entries", type=int, default=50, help="min story entries to qualify")
    ap.add_argument("--out-dir", required=True, help="output directory for JSON + JSONL dumps")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    user = auth.get_user_by_email(USER_EMAIL)
    uid = user.uid
    db = firestore.client()
    print(f"UID: {uid}")

    print(f"Finding last {args.last} campaigns with >= {args.min_entries} entries...")
    last_n = find_last_n_with_min_entries(db, uid, args.last, args.min_entries)
    print(f"Found {len(last_n)} candidates")
    for i, c in enumerate(last_n, 1):
        print(f"  {i:2d}. {c['id'][:8]}  entries={c['entries']:>4}  ts={c['last_ts_norm']:.0f}  {c['name'][:60]}")

    with open(out_dir / "last_n_campaigns.json", "w") as f:
        json.dump(last_n, f, indent=2)

    # Per-scene classification
    all_scenes = []
    for i, c in enumerate(last_n, 1):
        cid = c["id"]
        pc_name = get_pc_name(db, uid, cid)
        print(f"[{i}/{len(last_n)}] {cid[:8]}  pc={pc_name}  processing...", end=" ", flush=True)
        docs = stream_story(db, uid, cid)
        scene_count = 0
        for d in docs:
            dd = d.to_dict() or {}
            if (dd.get("actor") or "").lower() != "gemini":
                continue
            text = dd.get("text") or ""
            di = dd.get("debug_info") or {}
            if not isinstance(di, dict):
                di = {}
            agent = di.get("agent_name") or dd.get("mode") or "(unknown)"
            mode = dd.get("mode") or ""
            ts = dd.get("timestamp")
            pc_lines, npc_lines, speakers = count_dialog(text, pc_name)
            all_scenes.append({
                "campaign_id": cid,
                "campaign_name": c["name"],
                "id": d.id,
                "agent": agent,
                "mode": mode,
                "ts": str(ts),
                "words": len(text.split()),
                "pc_lines": pc_lines,
                "npc_lines": npc_lines,
                "speakers": speakers,
            })
            scene_count += 1
        print(f"{scene_count} gemini scenes")

    # Per-agent aggregation
    by_agent = defaultdict(list)
    for s in all_scenes:
        by_agent[s["agent"]].append(s)

    agent_summary = []
    for a, sl in sorted(by_agent.items(), key=lambda kv: -len(kv[1])):
        n = len(sl)
        if n == 0:
            continue
        agent_summary.append({
            "agent": a,
            "scenes": n,
            "pct_of_total": round(100 * n / len(all_scenes), 2),
            "median_pc_lines": round(statistics.median([s["pc_lines"] for s in sl]), 2),
            "median_npc_lines": round(statistics.median([s["npc_lines"] for s in sl]), 2),
            "mean_pc_lines": round(statistics.mean([s["pc_lines"] for s in sl]), 2),
            "mean_npc_lines": round(statistics.mean([s["npc_lines"] for s in sl]), 2),
            "pct_pc_silent": round(100 * sum(1 for s in sl if s["pc_lines"] == 0) / n, 2),
            "pct_two_way": round(100 * sum(1 for s in sl if s["pc_lines"] >= 1 and s["npc_lines"] >= 1) / n, 2),
            "median_words": round(statistics.median([s["words"] for s in sl]), 0),
        })

    with open(out_dir / "agent_summary.json", "w") as f:
        json.dump(agent_summary, f, indent=2)
    with open(out_dir / "all_scenes_by_agent.jsonl", "w") as f:
        for s in all_scenes:
            f.write(json.dumps(s) + "\n")

    print(f"\n=== AGGREGATE across {len(last_n)} campaigns ({len(all_scenes)} scenes) ===")
    print(f"Median of medians — PC lines/scene: {statistics.median([s['median_pc_lines'] for s in agent_summary if s['scenes'] >= 10])}")
    print(f"Median of medians — NPC lines/scene: {statistics.median([s['median_npc_lines'] for s in agent_summary if s['scenes'] >= 10])}")
    total_scenes = len(all_scenes)
    total_silent = sum(round(s["scenes"] * s["pct_pc_silent"] / 100) for s in agent_summary if s["scenes"] >= 10)
    total_two_way = sum(round(s["scenes"] * s["pct_two_way"] / 100) for s in agent_summary if s["scenes"] >= 10)
    print(f"Scenes with PC silent:  {total_silent}/{total_scenes} ({100*total_silent/total_scenes:.1f}%)")
    print(f"Scenes with two-way:    {total_two_way}/{total_scenes} ({100*total_two_way/total_scenes:.1f}%)")
    print(f"\nOutputs: {out_dir}/agent_summary.json, {out_dir}/all_scenes_by_agent.jsonl, {out_dir}/last_n_campaigns.json")


if __name__ == "__main__":
    main()