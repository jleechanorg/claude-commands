# OpenRouter Attribution Headers — Diagnostic Reference

## What the dashboard columns mean

The OpenRouter dashboard (`openrouter.ai` → Activity → Logs) has four columns that look opaque unless you know which HTTP headers drive them:

| Dashboard column | HTTP header source | Default value in hermes-agent |
|------------------|-------------------|-------------------------------|
| **App**          | `X-Title`         | `Hermes Agent` (hardcoded) |
| **Referer**      | `HTTP-Referer`    | `https://hermes-agent.nousresearch.com` (hardcoded) |
| **Subject**      | First user-message text in the chat-completions call | Varies — see "Favicon for X" pattern below |
| **Model**        | `model` param     | e.g. `google/gemini-3-flash-preview` |
| **Provider**     | OpenRouter's routing decision | e.g. `Google Vertex` (OpenRouter's upstream for that model) |

If a user says "why is my OpenRouter dashboard showing 'Hermes Agent' on every call?" — the answer is: the auxiliary client hardcodes attribution headers in `agent/auxiliary_client.py:311-315` and there's no way to differentiate sub-flows from the OpenRouter side. Every call from Hermes via the OpenRouter provider will be tagged the same way.

## Source of the headers

`projects_other/hermes-agent/agent/auxiliary_client.py`:

```python
# OpenRouter app attribution headers (base — always sent).
_OR_HEADERS_BASE = {
    "HTTP-Referer": "https://hermes-agent.nousresearch.com",
    "X-Title": "Hermes Agent",
    "X-OpenRouter-Categories": "productivity,cli-agent",
}

# Vercel AI Gateway app attribution headers
_AI_GATEWAY_HEADERS = {
    "HTTP-Referer": "https://hermes-agent.nousresearch.com",
    "X-Title": "Hermes Agent",
    "User-Agent": f"HermesAgent/{_HERMES_VERSION}",
}
```

Both are sent on every call routed through the OpenRouter or Vercel AI Gateway provider. There's no per-call-site override — if you want different attribution, you have to change the constants.

## "Favicon for X" Subject pattern

When a user browses a URL and the auto-image-attachment handler runs, it captions every embedded image (including favicons) via `vision_analyze`. The caption prompt is constructed as `"Favicon for {domain}"` for favicons, which is what shows up as the "Subject" in OpenRouter.

Source: `run_agent.py:8842-8865` — when an image part is detected in the conversation, it calls `vision_analyze_tool(image_url=..., user_prompt=analysis_prompt)` with the analysis prompt being something like "Favicon for google" or "Favicon for https://hermes-agent.nousresearch.com/".

So if you see ~160 OpenRouter calls in a week with subjects like:
- `Favicon for google`
- `Favicon for x-ai`
- `Favicon for https://hermes-agent.nousresearch.com/`

…the source is Hermes' browse flow auto-captioning favicons on every page load. Each call is ~178 input tokens + 6-8 output tokens (~$0.0001). Cheap individually, but adds up over many browses.

## Why "Gemini 3 Flash" via OpenRouter

The `vision_analyze` tool defaults to `google/gemini-3-flash-preview` (set in `tools/vision_tools.py:652` and `_OPENROUTER_MODEL = "google/gemini-3-flash-preview"` in `agent/auxiliary_client.py:391`). When `config.yaml` has `auxiliary.vision.provider: openrouter`, the call goes to OpenRouter, which then forwards to Google's Vertex backend. OpenRouter's dashboard reflects this as `Model: google/gemini-3-flash-preview, Provider: Google Vertex` — but the BILLING is via OpenRouter (the user's OPENROUTER_API_KEY), not Google directly.

If you want the call to go to Google directly (skip OpenRouter markup, use your `GEMINI_API_KEY` instead), set `auxiliary.vision.provider: gemini` in `~/.hermes/config.yaml` (line 161) and sync to prod. The model name changes from `google/gemini-3-flash-preview` (OpenRouter-prefixed) to `gemini-3-flash-preview` (native Gemini).

## Diagnostic recipe

When the user reports "Hermes is using X via OpenRouter" or "I see N calls on OpenRouter I didn't make":

1. **Identify the prompt** — read the OpenRouter "Subject" column. If it looks like `Favicon for <domain>`, it's the browse flow auto-captioning.
2. **Find the call site** — search `projects_other/hermes-agent` and `tools/vision_tools.py` for the model name. Default model for vision: `google/gemini-3-flash-preview` (OpenRouter) or `gemini-3-flash-preview` (native).
3. **Check `config.yaml`** — look for `auxiliary.<role>.provider: openrouter`. The supported roles are `vision`, `web_extract`, `compression`, `session_search`, `skills_hub`.
4. **If the user wants to stop using OpenRouter for a role** — change `provider: openrouter` → a direct provider (e.g. `gemini`, `xai`, `zai`) and `model: google/<model>` → `<model>` (drop the OpenRouter prefix). Requires a working key for that provider in `auth.json` or as an env var.
5. **Verify the loader picked up the change** — restart the gateway and run:
   ```bash
   python3 -c "from hermes_cli.config import load_config; print(load_config().get('auxiliary', {}).get('vision', {}))"
   ```
   Expect the new `provider` and `model` values to print.

## Default auxiliary models per provider

From `agent/auxiliary_client.py:_API_KEY_PROVIDER_AUX_MODELS_FALLBACK`:

| Provider | Default aux model |
|----------|-------------------|
| `gemini` | `gemini-3-flash-preview` |
| `zai` | `glm-4.5-flash` |
| `kimi-coding` | `kimi-k2-turbo-preview` |
| `stepfun` | `step-3.5-flash` |
| `anthropic` | `claude-haiku-4-5-20251001` |
| `ai-gateway` | `google/gemini-3-flash` |
| `opencode-zen` | `gemini-3-flash` |
| `opencode-go` | `glm-5` |
| `kilocode` | `google/gemini-3-flash-preview` |
| `ollama-cloud` | `nemotron-3-nano:30b` |
| `tencent-tokenhub` | `hy3-preview` |

`xai` and others not listed fall back to empty string (caller must specify).

## Case study: 2026-06-08 vision provider switch

**Symptom:** OpenRouter dashboard showed 160+ calls in one week, all `Model: google/gemini-3-flash-preview`, all `Provider: Google Vertex`, all `App: Hermes Agent`, all `Subject: Favicon for X`.

**Diagnosis:** `~/.hermes/config.yaml:161` had `auxiliary.vision.provider: openrouter`. The vision_analyze tool was using OpenRouter as the transport (paying OpenRouter pricing for what is ultimately a Google Vertex call).

**Fix applied:**
```yaml
# Before
auxiliary:
  vision:
    provider: openrouter
    model: google/gemini-2.5-flash

# After
auxiliary:
  vision:
    provider: gemini
    model: gemini-3-flash-preview
```

Files edited: `~/.hermes/config.yaml` (staging) + `cp` to `~/.hermes_prod/config.yaml` (prod). Gateway restart via `launchctl print gui/$(id -u)/ai.hermes.prod` + SIGTERM. Canary passed in 8s.

**Result:** Vision calls now go directly to Google's API (using `GEMINI_API_KEY` from `~/.bashrc`). No more entries in OpenRouter dashboard for vision work. OpenRouter credential `0f9477` in `auth.json` still has `request_count: 0` for this purpose.
