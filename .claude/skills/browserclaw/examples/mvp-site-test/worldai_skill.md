# WorldAI — Browserclaw Skill
# Captures HTTP from WorldAI via Playwright, generates curl/httpie commands + MCP tools
# Auth: Firebase Bearer token (get via: firebase.auth().currentUser.getIdToken() in logged-in browser)

env:
  BASE_URL: https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app
  AUTH_HEADER: Authorization
  AUTH_VALUE_PREFIX: "Bearer "
  # Token (expires ~24h): get fresh from superpower chrome eval: firebase.auth().currentUser.getIdToken()
  # Or use browserclaw's --extra-headers to inject dynamically

endpoints:

  - name: server_time
    path: /api/time
    method: GET
    auth: false
    description: Server timestamp — no auth required
    response_fields: [server_time_utc, server_timestamp, server_timestamp_ms]

  - name: settings
    path: /api/settings
    method: GET
    auth: true
    description: LLM provider config, model names, API key presence flags
    response_fields: [cerebras_model, gemini_model, llm_provider, openrouter_model, debug_mode, has_custom_*_key]

  - name: list_campaigns
    path: /api/campaigns
    method: GET
    auth: true
    description: List all campaigns for logged-in user
    response_fields: [id, title, updated_at, created_at]

  - name: get_campaign
    path: /api/campaigns/{campaign_id}
    method: GET
    auth: true
    description: Full campaign detail — includes game_state, story, rewards_box, planning_block
    params:
      - name: story_limit
        type: integer
        default: 300
        description: Max story characters to return
    response_fields: [campaign, game_state, story, rewards_box, planning_block, story_pagination]

  - name: get_story
    path: /api/campaigns/{campaign_id}/story
    method: GET
    auth: true
    description: Paginated story entries only (no game state)
    params:
      - name: story_limit
        type: integer
        default: 100
    response_fields: [story[actor,text,mode,sequence_id], pagination]

  - name: export_campaign
    path: /api/campaigns/{campaign_id}/export
    method: GET
    auth: true
    description: Full campaign export as formatted text (God Mode narrative)

  - name: send_interaction
    path: /api/campaigns/{campaign_id}/interaction
    method: POST
    auth: true
    description: Send player action — non-streaming (returns full result)
    body:
      - name: user_input
        type: string
        required: true
        description: The player's action/decision
      - name: mode
        type: string
        required: true
        enum: [god, char, think]
        description: "Interaction mode: god (omniscient), char (first-person), think (internal monologue)"
      - name: stream
        type: boolean
        default: false
        description: Set true for SSE streaming response
    response_fields: [story, game_state, rewards_box]

  - name: stream_interaction
    path: /api/campaigns/{campaign_id}/interaction?stream=true
    method: POST
    auth: true
    description: Send player action with SSE streaming response
    body:
      - name: user_input
        type: string
        required: true
      - name: mode
        type: string
        required: true
        enum: [god, char, think]
    response: SSE stream of delta story entries

example_curl: |
  BASE="https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app"
  TOKEN="<firebase_id_token>"

  # Get settings
  curl -s -X GET "$BASE/api/settings" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json"

  # List campaigns
  curl -s -X GET "$BASE/api/campaigns" \
    -H "Authorization: Bearer $TOKEN"

  # Get campaign detail
  curl -s -X GET "$BASE/api/campaigns/cntvDfj7cGUhUFkxcmV3?story_limit=300" \
    -H "Authorization: Bearer $TOKEN"

  # Send interaction (non-streaming)
  curl -s -X POST "$BASE/api/campaigns/cntvDfj7cGUhUFkxcmV3/interaction" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_input":"I attack the goblin with my sword","mode":"god","stream":false}'

  # Streaming SSE
  curl -s -N -X POST "$BASE/api/campaigns/cntvDfj7cGUhUFkxcmV3/interaction?stream=true" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"user_input":"I attack the goblin","mode":"god"}'

how_to_get_token: |
  In a browser logged into WorldAI:
  1. Open DevTools console (F12)
  2. Run: firebase.auth().currentUser.getIdToken()
  3. Copy the returned JWT string

  Or via browserclaw capture with superpower chrome (already logged in):
  browserclaw capture --url https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app \
    --extra-headers "Authorization=Bearer <token>"

  Note: Token expires in ~24h. Firebase sessions expire, requiring re-login.

notes:
  - The app uses Firebase Firestore for real-time game state (WebSocket, not HTTP).
    HTTP endpoints cover REST operations (campaign CRUD, settings, interactions).
  - Firestore WebSocket traffic is NOT captured by fetch/XHR interceptors.
    Use superpower chrome eval to call firebase.firestore() directly for real-time data.
  - The SSE streaming endpoint returns Server-Sent Events with story deltas.
  - OpenClaw gateway is used as LLM proxy (configured to example.com in dev — fix for prod).
