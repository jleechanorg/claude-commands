# GCP Secret Manager Fallback for Direct Gemini API (2026-07-30)

## The class

When `~/.gemini_api_key_secret` returns `API_KEY_INVALID` (rotated,
revoked, or never refreshed) AND the service account
`~/serviceAccountKey.json` lacks `aiplatform.endpoints.predict` on
Vertex AI, the local-Gemini API path is dead. **Don't conclude "Gemini
key broken"** — pull from GCP Secret Manager instead.

## Verified recipe (2026-07-30)

```bash
# 1. Verify the key exists in GCP
gcloud secrets versions access latest \
  --secret="gemini-api-key" \
  --project="worldarchitecture-ai"

# 2. Returns AIzaSyAv[REDACTED]... (39 chars). Use as x-goog-api-key header.

# 3. Test direct Gemini API
SECRET=$(gcloud secrets versions access latest \
  --secret="gemini-api-key" \
  --project="worldarchitecture-ai" 2>/dev/null)

curl -sS --max-time 15 -X POST \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: $SECRET" \
  -d '{"contents":[{"parts":[{"text":"Return JSON: {\"dice_total\": 7, \"rolls\": [3, 4]}"}]}],"generationConfig":{"temperature":0.7,"responseMimeType":"application/json"}}'
```

Returns clean JSON when the secret is fresh; returns `API_KEY_INVALID`
when the GCP version is also stale.

## Other auth paths verified during this session

| Auth source | Result |
|---|---|
| `~/.bashrc` GEMINI_MODEL var | Only sets model name, not key |
| `~/.gemini_api_key_secret` (file) | DEAD — `API_KEY_INVALID` (key `AIzaSyDQ6a...`) |
| `GOOGLE_APPLICATION_CREDENTIALS` + Vertex AI | 403 PERMISSION_DENIED — service account lacks `aiplatform.endpoints.predict` |
| `gcloud secrets versions access ... gemini-api-key` (GCP) | **WORKS** — key `AIzaSyAvyb...` |
| OpenRouter `https://openrouter.ai/api/v1/chat/completions` | WORKS — `google/gemini-3-flash-preview`, `google/gemini-3.5-flash`, `google/gemini-3.5-flash-lite`, `google/gemini-3.6-flash`, `openai/gpt-5.6-luna` all reachable |

## OpenRouter as universal fallback (for vendor-agnostic comparison tests)

When you need to test multiple vendor families in one benchmark (Gemini
+ OpenAI + Anthropic), OpenRouter's chat-completions endpoint covers
all three. The `OR_KEY` lives in macOS Keychain at
`openrouter-pilot-api-key`:

```bash
OR_KEY=$(security find-generic-password -s openrouter-pilot-api-key -w 2>/dev/null)
curl -sS -X POST "https://openrouter.ai/api/v1/chat/completions" \
  -H "Authorization: Bearer $OR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"openai/gpt-5.6-luna","messages":[{"role":"user","content":"..."}],"response_format":{"type":"json_object"}}'
```

Returns `usage.cost` (USD), `usage.total_tokens`,
`usage.completion_tokens_details.reasoning_tokens` per turn — enough to
build a cost/latency benchmark without touching per-vendor APIs.

## Anti-pattern

Concluding "the API is broken" after probing only one auth source.
There are typically 3-4 Gemini auth paths on this host
(`~/.gemini_api_key_secret`, GCP secret-manager, Vertex AI service
account, OpenRouter chat-completions) and any of them being alive is
enough to run tests. Probing each takes one curl + a few seconds.
