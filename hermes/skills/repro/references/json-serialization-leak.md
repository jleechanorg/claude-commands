---
name: json-serialization-leak
description: get_campaign returns HTTP 500 because response_data contains a Python set or _Sentinel singleton that Flask's jsonify cannot serialize. Intermittent — second click usually succeeds.
tags: [repro, worldarchitect, mvp_site, main.py, jsonify, sentinel, set, serialization, http-500]
---

# JSON-serialization leak in `get_campaign`

## Symptom

`GET /api/campaigns/<id>?story_limit=50` returns **HTTP 500** with body `Failed_to_retrieve_campaign`. The first attempt after a specific game-state shape (active modal, partial merge, planning-block projection) fails; a second click ~10 seconds later returns **200 OK** with the full payload.

Users describe this as "can't load the campaign" or "the campaign is broken." Affected campaigns are inconsistent — `a1OGXHNxNdw1Id0iRfpR` may fail while `a1OGXHNxNdw1Id0iRfpR` loaded fine an hour ago. The intermittency is the strongest signal: it's NOT auth, NOT Firestore, NOT a deployed regression.

## Root cause

`$PROJECT_ROOT/main.py`'s `get_campaign` handler builds `response_data` (around lines 2712-2740) from several sources that aren't fully sanitized before `return jsonify(response_data)`:

```python
response_data = {
    KEY_CAMPAIGN: campaign_data,                              # not sanitized
    KEY_STORY: processed_story,                                # not sanitized
    "game_state": world_logic.sanitize_rewards_state_for_context(game_state_dict),  # sanitized
    "story_pagination": {...},                                # primitives
}
```

Two non-JSON-encodable types leak through:

1. **`_Sentinel`** — singleton from `$PROJECT_ROOT/firestore_service.py:108-129`:
   ```python
   class _Sentinel:
       __slots__ = ()
       def __reduce__(self) -> tuple:
           return (_restore_sentinel, ())
   _DELETED = _Sentinel()
   ```
   Used by `_deep_merge` to mark explicit field deletions. Preserves identity through `copy.deepcopy` / pickle via `__reduce__`. **Flask's `json.dumps` has no encoder for it.** There IS a guard at `$PROJECT_ROOT/game_state.py:2586` (`if obj.__class__.__name__ == "Sentinel": return dt.now(UTC).isoformat()`) but it lives in `GameState._json_serializable`, which is **only called on `game_state_dict`**. The synthesised `planning_block` from `world_logic._inject_modal_finish_choice_if_needed` (line 2624) and the synthesised `rewards_box` (line 2728) skip the sanitiser.

2. **`set` instances** — Python `set` (not `frozenset`, not `list`). Most likely origin is a deduplication path that uses `set(...)` then forgets to `list(...)`-wrap before returning the value into `processed_story` or `campaign_data`. Two distinct campaigns exhibited the `set` variant on the same minute, ruling out a one-off LLM emission.

## Diagnostic — pull the symptom from Cloud Logging

The deployed `get_campaign` handler logs the Python traceback to stderr (`logger: "root"`), and Cloud Run's `requests` log records the HTTP status. Both can be queried together:

```bash
gcloud logging read \
  'resource.labels.service_name="mvp-site-app-dev" AND timestamp>="2026-07-13T01:00:00Z" AND (
      severity=ERROR
      OR (textPayload:"/api/campaigns/a1OGXHNxNdw1Id0iRfpR" AND severity!=INFO)
      OR jsonPayload.message:"Sentinel"
      OR jsonPayload.message:"JSON serializable"
   )' \
  --project=worldarchitecture-ai \
  --freshness=24h --limit=100 \
  --format='json(timestamp,resource.labels.service_name,severity,textPayload,jsonPayload.message)'
```

What you get back:

```
2026-07-13T02:12:39.049Z  mvp-site-app-dev  -  GET /api/campaigns/a1OGXHNxNdw1Id0iRfpR?story_limit=50  500  56
2026-07-13T02:12:46.384Z  mvp-site-app-dev  ERROR  🔥🔴 Traceback (...): ... TypeError: Object of type Sentinel is not JSON serializable
2026-07-13T02:12:50.770Z  mvp-site-app-dev  -  GET /api/campaigns/a1OGXHNxNdw1Id0iRfpR?story_limit=50  200  86189
```

The 500 then 200 in quick succession (12 seconds here) confirms intermittency.

**Also look for the SPA's own telemetry** — the frontend's `client_diag` instrumentation sends `[client_diag]` rows to the same log bucket. Filter for `cdiag_field_status=500` and `cdiag_field_url=/api/campaigns/<id>` to find *what the user's browser actually saw* (the SPA records `cdiag_field_error_message=Failed_to_retrieve_campaign`):

```bash
gcloud logging read \
  'resource.labels.service_name="mvp-site-app-dev" AND jsonPayload.message:"Failed_to_retrieve_campaign"' \
  --project=worldarchitecture-ai --freshness=24h --limit=50 \
  --format='json(timestamp,jsonPayload.message)'
```

## Sibling-issue scan

Check whether the bug has hit other campaigns under the same user (or across the codebase):

```bash
gcloud logging read \
  'resource.labels.service_name=("mvp-site-app-stable" OR "mvp-site-app-dev") AND (
      textPayload:"TypeError" OR jsonPayload.message:"TypeError"
   )' \
  --project=worldarchitecture-ai --freshness=7d --limit=200 \
  --format='json(timestamp,resource.labels.service_name,textPayload,jsonPayload.message)' \
  | python3 -c "
import json, sys, re
data = json.loads(sys.stdin.read())
hits = {}
for e in data:
    body = (e.get('jsonPayload') or {}).get('message','') or e.get('textPayload','')
    for m in re.finditer(r'/api/campaigns/([A-Za-z0-9_-]{20,})', body):
        cid = m.group(1)
        hits.setdefault(cid, 0)
        hits[cid] += 1
for cid, n in sorted(hits.items(), key=lambda x: -x[1]):
    print(f'{n:4d}  {cid}')
"
```

In the 2026-07-12 verified case, this produced:

```
   3  a1OGXHNxNdw1Id0iRfpR     ← Re:zero Theresa
   2  5MYrGMUZovrK6hgv3Qiu
   1  FsiyESY987DF2lfgolCI
   1  (unknown — textPayload had no campaign_id in the matching context)
```

All from the same client IP within ~13 minutes. Confirms the user's "i can access some campaigns but not others" framing is real, not a misreport.

## Why it doesn't fire on every load

The leak requires `response_data` to *actually contain* a `set` or `_Sentinel` value at the time of `jsonify`. Both types are created and stripped during normal flows:

- `_DELETED` sentinel — placed during `_deep_merge` for explicit field deletions; stripped by `_strip_deleted` before persistence. **But** if the in-memory `game_state_dict` carries an unresolved `_DELETED` (e.g. mid-merge when the modal-finish injection runs at line 2624), the strip hasn't happened yet.
- `set` — created by dedup paths; persists only if the code path returns `set(...)` instead of `list(set(...))`.

A retry after ~10s finds the partial merge completed and the second request builds `response_data` from clean state → serializes fine.

## Fix shape (root-cause-first, per `AGENTS.md`)

The leak point is **`$PROJECT_ROOT/main.py`'s `get_campaign` `response_data` construction**. The cheapest, root-cause-first fix is to extend the existing `GameState._json_serializable` sanitizer to also handle `set`/`frozenset`, then call it on `response_data` (or at minimum on `processed_story`, `campaign_data`, and the synthesised `planning_block`) before `jsonify`. Symmetric with the existing `Sentinel` handling at `game_state.py:2586`.

```python
# $PROJECT_ROOT/game_state.py:2580-2592
@staticmethod
def _json_serializable(obj: Any) -> Any:
    """Recursively convert non-JSON types for wire serialization."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if obj.__class__.__name__ == "Sentinel":
        return None  # sentinel markers are wire-irrelevant
    if isinstance(obj, (set, frozenset)):
        return list(obj)  # canonical list representation
    if isinstance(obj, dict):
        return {k: GameState._json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [GameState._json_serializable(item) for item in obj]
    return obj
```

Then at the `get_campaign` exit point, BEFORE `return jsonify(response_data)`:

```python
response_data = GameState._json_serializable(response_data)
return jsonify(response_data)
```

Or, alternatively, register a custom Flask JSON provider that handles `set` and the Sentinel class globally:

```python
# $PROJECT_ROOT/main.py boot
from flask.json.provider import DefaultJSONProvider
class WAJSONProvider(DefaultJSONProvider):
    def default(self, o):
        if o.__class__.__name__ == "Sentinel":
            return None
        if isinstance(o, (set, frozenset)):
            return list(o)
        return super().default(o)
app.json = WAJSONProvider(app)
```

Backend-enforcement-only would be wrong here — `_Sentinel` and `set` are legitimate runtime values with semantic meaning in `_deep_merge` / dedup logic; they should be projected out at the **wire boundary**, not rejected.

## Tests (must land with the fix)

```python
# $PROJECT_ROOT/tests/test_get_campaign_json_serialization.py
import json, pytest
from unittest.mock import MagicMock

class TestGetCampaignJsonSerialization:
    def test_response_data_with_sentinel_is_serializable(self):
        from mvp_site.firestore_service import _DELETED
        response_data = {"campaign": {"x": _DELETED}, "story": []}
        out = GameState._json_serializable(response_data)
        json.dumps(out)  # must not raise

    def test_response_data_with_set_is_serializable(self):
        response_data = {"story": [{"tags": {"a", "b"}}]}
        out = GameState._json_serializable(response_data)
        assert isinstance(out["story"][0]["tags"], list)
        json.dumps(out)  # must not raise

    def test_get_campaign_returns_200_for_set_or_sentinel_payload(self, client, ...):
        """End-to-end: a campaign with a planning-block sentinel still loads."""
        # seed Firestore + game_states, hit /api/campaigns/<id>, assert 200
```

Run the existing `$PROJECT_ROOT/tests/test_world_logic.py` modal-flow tests and `test_get_campaign.py` (if present) to verify no regression on the sanitised `game_state_dict` path.

## Reproduction recipe (for the diagnostic half of /repro)

```bash
# 1. Find the campaign + user
WORLDAI_DEV_MODE=true WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=$HOME/serviceAccountKey.json \
  ./venv/bin/python scripts/campaign_manager.py find-user $USER@gmail.com

# 2. Find candidate campaign ids (substring match)
WORLDAI_DEV_MODE=true ./venv/bin/python scripts/campaign_manager.py \
  query <UID> "re:zero"   # or whatever the user reported

# 3. Inspect Firestore game state for non-JSON-encodable shapes
python3 -c "
import json
import firebase_admin
from firebase_admin import credentials, firestore
import os
os.environ.setdefault('WORLDAI_GOOGLE_APPLICATION_CREDENTIALS', os.path.expanduser('$HOME/serviceAccountKey.json'))
cred = credentials.Certificate(os.path.expanduser(os.environ['WORLDAI_GOOGLE_APPLICATION_CREDENTIALS']))
firebase_admin.initialize_app(cred)
db = firestore.client()
gs = db.document(f'users/<UID>/campaigns/<CID>/game_states/current_state').get().to_dict()
# Walk for set/Sentinel
def walk(o, path=''):
    if o.__class__.__name__ == 'Sentinel':
        print(f'SENTINEL at {path}')
    if isinstance(o, set):
        print(f'SET at {path}')
    if isinstance(o, dict):
        for k,v in o.items(): walk(v, f'{path}.{k}')
    elif isinstance(o, list):
        for i,v in enumerate(o): walk(v, f'{path}[{i}]')
walk(gs)
"

# 4. Hit the deployed API in a loop to catch the intermittent 500
for i in $(seq 1 20); do
  curl -sS -o /dev/null -w '%{http_code}  %{time_total}s\n' \
    -H "Authorization: Bearer <FIREBASE_ID_TOKEN>" \
    "https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/api/campaigns/<CID>?story_limit=50"
  sleep 0.5
done
# Expect mostly 200 with intermittent 500 — that's the intermittent signature.
```

## When this is NOT the bug

- **Symptom is permanent (every load fails)** → check Firebase auth token, deploy health, Firestore rules
- **Symptom is "stuck spinner / never finishes"** → look at the streaming SSE endpoint, not the wire `get_campaign`
- **Symptom is "stuck mid-conversation"** → likely `streaming.a100118c.js` or LLM-side issue, not `get_campaign`
- **No Python traceback in logs** → different bug class; the user may be seeing a JS-side render error after the 200 OK

## Pair with

- `references/auth-gate-fallback-repro.md` — Step 6 (Skip headless Chrome, query GCP Cloud Logging) is the path that surfaces this bug class
- `references/two-pronged-render-and-persist-bug.md` — adjacent pattern; both are "one symptom, multiple code layers"
- `references/evidence-extraction-patterns.md` — for parsing `client_diag` and `cdiag_*` rows from Cloud Logging
