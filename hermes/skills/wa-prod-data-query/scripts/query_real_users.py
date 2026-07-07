#!/usr/bin/env python3
"""
WA prod-data query helper.

Reads WA prod Firestore and prints a "real user engagement" report
for a date window. Used by the wa-prod-data-query skill.

Usage:
    cd $HOME/your-project.com
    WORLDAI_DEV_MODE=true .venv/bin/python \\
        ~/.hermes_prod/skills/wa-prod-data-query/scripts/query_real_users.py \\
        --days 7 --exclude-$USER

Stdout: human-readable table per active user.
Stderr: progress notes (so stdout stays clean for piping).

NOTE: this script reads Firestore directly using the firebase-admin SDK
and the user's existing service account. It depends on:
    - ~/.serviceAccountKey.json (or env WORLDAI_GOOGLE_APPLICATION_CREDENTIALS)
    - the WA repo's venv at ~/your-project.com/.venv

This is the WA-agnostic helper used by the skill; the SKILL.md
explains when and why to use it.
"""

from __future__ import annotations

import argparse
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

# ---- WA-specific bootstrap (importable only from this skill's context) ----
WA_REPO = "$HOME/your-project.com"


def ensure_wa_imports() -> None:
    """Add WA paths and apply clock-skew + dev-mode boilerplate."""
    sys.path.insert(0, os.path.join(WA_REPO, "mvp_site"))
    sys.path.insert(0, WA_REPO)
    os.environ.setdefault("WORLDAI_DEV_MODE", "true")
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        cred_path = os.path.expanduser("~/serviceAccountKey.json")
        if os.path.exists(cred_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
    from clock_skew_credentials import apply_clock_skew_patch  # type: ignore
    apply_clock_skew_patch()

    import firebase_admin  # type: ignore
    from firebase_admin import credentials  # type: ignore
    if not firebase_admin._apps:
        cred = credentials.Certificate(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        firebase_admin.initialize_app(cred)


def is_test_email(email: str | None) -> bool:
    if not email:
        return True
    e = email.lower()
    return any(
        token in e
        for token in ("test", "anon", "dev-runner", "example.com", "jleechantest")
    )


def to_dt(value) -> datetime | None:
    """Firestore Timestamp, datetime, int (ms), or float (s) -> tz-aware datetime."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    # Firestore Timestamp has .tzinfo and .timestamp()
    if hasattr(value, "timestamp"):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000 if value > 1e12 else value, tz=timezone.utc)
    return None


def collect_real_users(days: int, exclude_jleechan: bool) -> dict:
    """
    Returns {
        "by_email": {email: {uid, last_sign_in_dt, last_updated_dt, settings_keys, n_turns, sessions: [(start, end)]}},
        "summary": {signins_30d, signins_7d, unique_active_7d, total_turns_7d, ...},
    }
    """
    ensure_wa_imports()
    from firebase_admin import auth, firestore  # type: ignore

    db = firestore.client()

    # 1. auth users (email <-> uid, last sign in)
    email_to_uid: dict[str, str] = {}
    uid_to_email: dict[str, str] = {}
    uid_last_sign: dict[str, datetime] = {}
    page = auth.list_users()
    while page:
        for u in page.iterate_all():
            if u.email:
                email_to_uid[u.email.lower()] = u.uid
                uid_to_email[u.uid] = u.email
            if u.user_metadata and u.user_metadata.last_sign_in_timestamp:
                dt = to_dt(u.user_metadata.last_sign_in_timestamp)
                if dt:
                    uid_last_sign[u.uid] = dt
        page = page.get_next_page()

    jleechan_uid = email_to_uid.get("$USER@gmail.com")

    now = datetime.now(timezone.utc)
    cutoff_7 = now - timedelta(days=days)
    cutoff_30 = now - timedelta(days=30)

    # 2. rate_limits (the real engagement signal)
    by_email: dict[str, dict] = {}
    for r in db.collection("rate_limits").stream():
        d = r.to_dict() or {}
        uid = d.get("user_id", "")
        email = uid_to_email.get(uid)
        if not email or is_test_email(email):
            continue
        if exclude_jleechan and uid == jleechan_uid:
            continue
        turns = sorted(d.get("turn_timestamps", []) or [])
        first_turn = to_dt(turns[0]) if turns else None
        last_turn = to_dt(turns[-1]) if turns else None
        rec = by_email.setdefault(email, {"uid": uid, "turns": [], "last_updated": None})
        rec["turns"].extend(turns)
        if last_turn and (rec["last_updated"] is None or last_turn > rec["last_updated"]):
            rec["last_updated"] = last_turn

    # 3. user doc lastUpdated (independent signal — a user can update settings without playing)
    last_doc = None
    while True:
        q = db.collection("users").limit(300)
        if last_doc:
            q = q.start_after(last_doc)
        batch = list(q.stream())
        if not batch:
            break
        for u in batch:
            ud = u.to_dict() or {}
            lu = to_dt(ud.get("lastUpdated"))
            email = uid_to_email.get(u.id)
            if not email or is_test_email(email):
                continue
            if exclude_jleechan and u.id == jleechan_uid:
                continue
            rec = by_email.setdefault(email, {"uid": u.id, "turns": [], "last_updated": None})
            if lu and (rec["last_updated"] is None or lu > rec["last_updated"]):
                rec["last_updated"] = lu
        last_doc = batch[-1]
        if len(batch) < 300:
            break

    # 4. sessions: cluster turns into sessions with >30min gaps
    SESSION_GAP_MIN = 30
    for email, rec in by_email.items():
        turns = sorted(rec["turns"])
        if not turns:
            rec["sessions"] = []
            rec["n_turns"] = 0
            continue
        sessions = []
        cur = [turns[0]]
        for t in turns[1:]:
            gap_min = (t - cur[-1]) / 60
            if gap_min > SESSION_GAP_MIN:
                sessions.append((to_dt(cur[0]), to_dt(cur[-1]), len(cur)))
                cur = [t]
            else:
                cur.append(t)
        sessions.append((to_dt(cur[0]), to_dt(cur[-1]), len(cur)))
        rec["sessions"] = sessions
        rec["n_turns"] = len(turns)

    # 5. summary
    signins_7d = sum(1 for dt in uid_last_sign.values() if dt and dt >= cutoff_7)
    signins_30d = sum(1 for dt in uid_last_sign.values() if dt and dt >= cutoff_30)
    unique_active_7d = sum(
        1 for rec in by_email.values()
        if rec["last_updated"] and rec["last_updated"] >= cutoff_7
    )
    total_turns_7d = sum(
        sum(n for (s, e, n) in rec.get("sessions", []) if s and s >= cutoff_7)
        for rec in by_email.values()
    )

    return {
        "by_email": by_email,
        "summary": {
            "signins_7d": signins_7d,
            "signins_30d": signins_30d,
            "unique_active_7d": unique_active_7d,
            "total_turns_7d": total_turns_7d,
            "window_days": days,
            "now": now.isoformat(),
        },
    }


def render_report(data: dict, top: int = 30) -> str:
    by_email = data["by_email"]
    s = data["summary"]
    out = []
    out.append(f"=== WA prod-data summary (window={s['window_days']}d) ===")
    out.append(f"  Now:                       {s['now']}")
    out.append(f"  Real-user sign-ins (7d):    {s['signins_7d']}")
    out.append(f"  Real-user sign-ins (30d):   {s['signins_30d']}")
    out.append(f"  Unique active users (7d):   {s['unique_active_7d']}")
    out.append(f"  Total turns (7d):           {s['total_turns_7d']}")
    out.append("")
    out.append(f"=== Top {top} users by turns ===")
    sorted_recs = sorted(by_email.items(), key=lambda kv: -kv[1]["n_turns"])[:top]
    out.append(f"{'EMAIL':<35} {'TURNS':>5} {'SESSIONS':>8} {'LAST_ACTIVITY':<19}")
    out.append("-" * 70)
    for email, rec in sorted_recs:
        last = rec["last_updated"].strftime("%Y-%m-%d %H:%M") if rec["last_updated"] else "?"
        out.append(f"{email:<35} {rec['n_turns']:>5} {len(rec['sessions']):>8} {last:<19}")
    return "\n".join(out)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=7, help="Window size in days (default: 7)")
    p.add_argument("--exclude-$USER", action="store_true", default=True)
    p.add_argument("--include-$USER", dest="exclude_jleechan", action="store_false")
    p.add_argument("--top", type=int, default=30)
    p.add_argument("--json", action="store_true", help="Output JSON instead of text")
    args = p.parse_args()

    data = collect_real_users(args.days, args.exclude_jleechan)
    if args.json:
        import json
        print(json.dumps(data, indent=2, default=str))
    else:
        print(render_report(data, args.top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())