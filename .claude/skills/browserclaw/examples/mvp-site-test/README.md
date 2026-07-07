# WorldAI MVP Site — browserclaw Test

## What the Site Does

**WorldAI** is a D&D campaign management web app. It lets users:
- Create and manage D&D campaigns/characters
- Play campaigns with AI-generated content
- Generate character avatars (via xAPI image generation)
- Use planning blocks for campaign sessions

The app is a **Firebase-backed SPA**:
- Frontend: Served from Cloud Run (`mvp-site-app-dev-i6xf2p72ka-uc.a.run.app`)
- Auth: Firebase Auth (Google + email/password)
- Data: Firebase Firestore
- Backend: Minimal Flask/FastAPI server (only `/api/time`, `/api/health`)

## Endpoints Discovered

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/time` | No | Server time for clock skew detection |
| GET | `/api/health` | No | Health check (returns HTML on this deploy) |

**Note:** All game data (campaigns, characters, sessions) is stored in **Firebase Firestore**, accessed via Firebase SDK. These calls are NOT captured by standard HAR capture because Firebase uses WebSocket/streaming transports.

## Firebase Config

```javascript
{
  apiKey: 'AIzaSyARs7IekRptvhZIwtV7lwJh3axWFsn_4c8',
  authDomain: 'worldarchitecture-ai.firebaseapp.com',
  projectId: 'worldarchitecture-ai',
  storageBucket: 'worldarchitecture-ai.firebasestorage.app',
  messagingSenderId: '754683067800',
  appId: '1:754683067800:web:3b38787c69de301c147fed'
}
```

## How to Control It

### Option 1: Firebase Admin SDK (recommended for backend control)

```python
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize with service account
cred = credentials.Certificate('service-account.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# List campaigns
campaigns = db.collection('campaigns').stream()
for c in campaigns:
    print(c.to_dict())
```

### Option 2: Firebase REST API (authenticated)

Firebase Firestore has a REST API at `https://firestore.googleapis.com/v1/projects/worldarchitecture-ai/databases/(default)/documents/`. Requires an Firebase ID token from a logged-in user.

### Option 3: browserclaw with Firebase auth injection (needs implementation)

browserclaw currently does NOT support Firebase token injection. See `../../../src/browserclaw/` for the Firebase auth bypass feature that needs to be built.

## browserclaw Commands Used

```bash
# Capture homepage (static assets only)
browserclaw capture \
  --url https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app/ \
  --output examples/mvp-site-test/capture.har \
  --headless \
  --steps /tmp/mvp-steps.json

# Infer endpoints from HAR
browserclaw infer \
  --har examples/mvp-site-test/capture.har \
  --output examples/mvp-site-test/catalog.json \
  --site mvp-site-app-dev

# Generate Python client
browserclaw generate \
  --catalog examples/mvp-site-test/catalog.json \
  --output-dir examples/mvp-site-test/

# Test generated client
python -c "
from generated_client import BrowserClawClient
client = BrowserClawClient()
print(client.get_api_time())
"
```

## What's Missing (browserclaw gaps)

1. **Firebase WebSocket traffic not captured** — Firebase Firestore SDK uses WebSocket connections that HAR recording doesn't capture. browserclaw needs a Firebase-specific interception mode.

2. **No Firebase auth token injection** — browserclaw's `--storage-state` only captures HTTP cookies. Firebase Auth tokens (stored in memory/localStorage) are not captured. Need `--firebase-token` or `--inject-auth` option.

3. **Headless mode defaults to interactive** — `browserclaw capture --headless` still waits for stdin if no `--steps` are provided. The `--headless` flag should imply non-interactive mode.

4. **LLM goal mode requires API keys** — `--goal` mode fails without ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY. No fallback to Claude CLI.

## Files in This Directory

- `capture.har` — Playwright HAR capture of the homepage
- `catalog.json` — Inferred endpoint catalog (only 1 endpoint found)
- `generated_client.py` — Generated Python client (1 method)
- `mcp_tools.json` — Generated MCP tools schema
- `test_campaign.json` — Test campaign metadata
