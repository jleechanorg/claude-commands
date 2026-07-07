---
name: wa-prod-data-query
version: 1.0.0
category: worldarchitect
description: Read YourProject production Firestore and produce a real-user engagement / retention report for a date window. Use when asked to review last week's real-user activity, analyze WA retention, look at WA prod data, find recent WA campaigns from real users, count active WA users, see who actually played WA this week, or compute signup→first-turn→next-session funnels. Critical insight it encodes: WA prod Firestore `campaigns` and `conversations` collections contain ZERO real-user docs as of 2026-06-23 — every doc there is a test fixture. The only reliable real-user gameplay signal is `rate_limits/{uid}.turn_timestamps`. Queries against `campaigns`/`conversations` will silently mislead you into "nobody is using WA". Use this skill first whenever the question is about WA real-user activity.
related_skills:
  - download-campaign
  - repro
  - wa-visual-proof-playwright
last_verified: 2026-06-23
---

# WA prod-data query — real-user engagement in production Firestore

> ## ⚠️ LOAD THIS SKILL BEFORE QUERYING WA PROD FIRESTORE FOR REAL-USER DATA
>
> Verified 2026-06-23 (Slack thread `C0AH3RY3DK6/1782231566.821589`): the WA
> production Firestore (`worldarchitecture-ai` project) stores real-user
> campaigns and stories under **subcollections of `users/{uid}`**, NOT at the
> root `campaigns` collection. The root `campaigns` collection has only
> 20 test fixtures (`test-user`, `test-user-manual`, etc., last 2026-02-11).
> **Real-user data lives at `users/{uid}/campaigns/{camp_id}/story/{entry_id}`
> (and `game_states`).** A naive query that walks the root `campaigns`
> collection will report "0 real-user campaigns" — which is wrong. The
> correct path is to (1) resolve the user's UID via `auth.list_users()` by
> email, then (2) walk `users/{uid}/campaigns/*` for their actual content.

## When to use this skill

- "Review last week's WA real-user activity"
- "What's our WA retention look like?"
- "Who actually played WA this week?"
- "Show me signup → first turn → next session funnel for WA"
- "How many real users touched WA in the last N days?"
- Any "did real users do X in WA?" question that would naively query `campaigns` or `conversations`
- Cross-checking AO worker claims about WA user activity

## When NOT to use

- Reading a single specific campaign's full story text → use `download-campaign`
- Investigating a bug in a specific user session → use `repro`
- Capturing visual proof of a UI change → use `wa-visual-proof-playwright`
- Reading WA test fixtures intentionally (`test-user-*` data) → no skill needed; just query

## Critical insight: the data model

The WA production Firestore has these relevant collections (sizes as of 2026-06-23):

| Collection | Docs | Real-user docs? | Notes |
|---|---|---|---|
| `campaigns` | 20 | **0** | All test fixtures (`test-user`, `test-user-manual`, `test-prod-user`); last real-user write is from before 2025-09-30 |
| `conversations` | 6 | **0** | All test fixtures (`e2e-test-user-crud`, `firestore-test-user-20251002-local`); last 2025-10-02 |
| `users` | 20,706 | ~200 | One doc per authenticated user; `lastUpdated` is the activity signal |
| `rate_limits` | 9,374 | ~37 | `turn_timestamps` array grows on every LLM turn — **THE** gameplay signal |
| `waitlist_requests` | 7 | 0 | All test/example.com |
| `shared_links` | 54 | ~0 | Mostly `jleechantest` |

**The only reliable real-user engagement signal is `rate_limits/{uid}.turn_timestamps`.** A `turn` is one LLM invocation (one user action). Gaps between turns cluster into sessions.

## Hard rules (proven correct by 2026-06-23 analysis)

1. **Never trust `campaigns` or `conversations` for real-user counts.** They are test-only in this database. If a query returns "0 real-user campaigns", that's a property of the data, not a finding to report.
2. **Filter out test users** by email pattern. Mark as test if email contains any of: `test`, `anon`, `dev-runner`, `example.com`, `jleechantest`. Do not try to detect test users from UID alone — the patterns are too varied (`test-user`, `test-user-manual`, `test-user-123`, `final-test`, `test-prod-user`, `test-user-production`).
3. **Exclude $USER by default.** uid is `vnLp2G3m21PJL6kxcuAqmWSOtm73` (email `$USER@gmail.com`). All queries should accept `--exclude-$USER` as default.
4. **Use `auth.list_users()` to resolve email <-> uid.** Do not rely on Firestore user docs for email lookup — they may not have it or may have a stale value.
5. **Cluster turns into sessions using a 30-minute gap.** Default in the helper script. A 1-2 min gap is intra-session; a 30+ min gap is "they came back".
6. **Watch out for the gRPC FD inheritance bug** — see `download-campaign/SKILL.md` § Pitfalls 1. This skill's helper script imports `firestore_service` and friends in-process; do NOT spawn `download_campaign.py` as a subprocess.

## The standard query workflow

### Step 1 — Confirm environment

```bash
ls ~/serviceAccountKey.json                    # service account key
ls ~/your-project.com/.venv/bin/python        # venv with firebase-admin
ls ~/your-project.com/your_app/firestore_service.py  # WA firestore_service
```

If any of these are missing, stop and load `download-campaign/SKILL.md` Phase 1 (venv bootstrap).

### Step 2 — Run the helper script

```bash
cd ~/your-project.com
WORLDAI_DEV_MODE=true .venv/bin/python \
    ~/.hermes_prod/skills/wa-prod-data-query/scripts/query_real_users.py \
    --days 7 --exclude-$USER
```

Output: a text table of top real users by turn count for the window. Use `--json` for machine-readable.

### Step 3 — Drill into a specific user (optional)

If a user looks interesting (high turn count, returning after days), pull their full session timeline:

```python
# In a Python session with the helper's imports done
import sys
sys.path.insert(0, "/Users/$USER/.hermes_prod/skills/wa-prod-data-query/scripts")
from query_real_users import ensure_wa_imports, to_dt
ensure_wa_imports()
from firebase_admin import firestore
db = firestore.client()

uid = "<the user's uid>"
rl = db.collection("rate_limits").document(uid).get()
turns = sorted(rl.to_dict().get("turn_timestamps", []))
for t in turns:
    print(to_dt(t).isoformat(), "UTC")
```

### Step 4 — Write findings

Save the analysis to `~/llm_wiki/wiki/sources/<YYYY-MM-DD>-<topic-slug>.md` per the existing convention. See `2026-06-23-real-user-retention-last-week.md` for a template.

## Common follow-ups

- **"What about `game_state` subcollections?"** — The `campaigns` collection in this DB has no subcollections (verified 2026-06-23). If you see subcollections, those are a different database or a different collection. Check the project (`db.project`) before assuming.
- **"Should I count `users` collection `lastUpdated` as activity?"** — Yes, but separately. A user with updated `lastUpdated` but no `rate_limits.turn_timestamps` is a "bouncer" — they signed in and tweaked settings but never played. Useful as a separate funnel stage.
- **"How do I track this over time?"** — Run the helper on a schedule (weekly cron → `~/.hermes_prod/cron/output/`). Diff `last_turn` across weeks to see who's new vs returning.

## What this skill is NOT

- **Not a replacement for `download-campaign`.** That skill walks a single campaign's story and game_state. This skill analyzes aggregate user activity.
- **Not a bug investigation tool.** If a user reports a bad experience, use `repro` to walk the specific session, not this skill.
- **Not a UI tool.** No Firebase emulator / admin UI; just direct Firestore reads.

## Tests

```bash
cd ~/.hermes_prod/skills/wa-prod-data-query
python3 -m unittest discover -s tests -v
```

Covers: email test-pattern detection, datetime parsing from Firestore Timestamp / int / float, session clustering with the 30-min gap rule, $USER exclusion.

## References

- `references/2026-06-23-findings.md` — initial analysis output (real-user counts, daily turn histogram, cohort table, retention hypotheses). Template for any future "last week's real-user activity" review.
- `~/llm_wiki/wiki/sources/2026-06-23-real-user-retention-last-week.md` — the durable write-up of the 2026-06-23 analysis that produced this skill.
- `download-campaign/SKILL.md` — gRPC FD inheritance workaround, venv deps, clock-skew + dev-mode boilerplate.
- `repro/SKILL.md` — when the question is "what went wrong for user X" rather than "what did users do in aggregate".