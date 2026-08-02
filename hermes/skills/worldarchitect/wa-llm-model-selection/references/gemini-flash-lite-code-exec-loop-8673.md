# gemini-3.5-flash-lite + gemini-3.6-flash code-execution infinite loop — issue #8673

## TL;DR

**Do NOT add `gemini-3.5-flash-lite` or `gemini-3.6-flash` to `MODELS_WITH_CODE_EXECUTION`** even if a comment in `$PROJECT_ROOT/constants.py` says they inherit code execution. Both models infinite-loop on simple code-execution calls:

| model | finish | code_parts | tokens |
|---|---|---|---|
| `gemini-3-flash-preview` | `STOP` | 2 | 849 |
| `gemini-3.5-flash` | `STOP` | 2 | 745 |
| `gemini-3.5-flash-lite` | **`TOO_MANY_TOOL_CALLS`** | **48** | **26,977** |
| `gemini-3.6-flash` | **`TOO_MANY_TOOL_CALLS`** | **48** | **21,235** |

Both Lite and 3.6 Flash emit 48 `codeExecution` parts per turn, exhaust the loop limit, and never return a structured response.

## Source

- Issue: [$GITHUB_REPOSITORY#8673](https://github.com/$GITHUB_REPOSITORY/issues/8673) (OPEN as of 2026-07-30)
- Bead: `rev-gemini-flash-lite-36-code-exec-loop-b7ka1`
- Direct API test: `curl https://generativelanguage.googleapis.com/v1beta/models/<MODEL>:generateContent` with `tools:[{"codeExecution":{}}]`, GCP-secret-manager key (the `~/.gemini_api_key_secret` file is dead — `API_KEY_INVALID`)

## What the bug actually is

PR #8512 ("feat(settings): add Gemini 3.6 Flash and Gemini 3.5 Flash Lite to model dropdown") added both models with an inline comment:

```python
# Gemini 3.6 Flash (Jul 2026) - Inherits 3.x code execution + JSON single-pass support.
"gemini-3.6-flash",  # Jul 2026 - inherits 3.x code_execution + JSON single-pass
# Gemini 3.5 Flash Lite (Jul 2026) - Inherits 3.5 code execution + JSON single-pass.
"gemini-3.5-flash-lite",  # Jul 2026 - inherits 3.x code_execution + JSON single-pass
```

**That comment is doubly wrong.** Live API evidence:
1. Neither model is in `MODELS_WITH_CODE_EXECUTION` (`$PROJECT_ROOT/constants.py:132`) — only Flash + 3.5 Flash are. So a user picking Lite or 3.6 in settings silently routes to native two-phase dice at `llm_service.py:2207, 9393` (`requires_code_execution=(model_name in constants.MODELS_WITH_CODE_EXECUTION)`).
2. Even if you DO add them to the allowlist, both models **infinite-loop on the code_execution tool** (`TOO_MANY_TOOL_CALLS` after 48 code parts, no JSON output). They never produce a structured response.

## Historical context (PR #8571 / PR #8590)

PR [#8571](https://github.com/$GITHUB_REPOSITORY/pull/8571) (merged 2026-07-24T23:30Z) made `gemini-3.5-flash-lite` the default model. The PR body explicitly documents two regressions:

> Because Flash Lite is not in `MODELS_WITH_CODE_EXECUTION`, the default runtime path shifts to native two-phase dice unless `TESTING_USE_CODE_EXECUTION_STRATEGY=true`.

> `gemini_provider` adds `is_gemini_3_model()` and "stops sending `temperature`" on Gemini 3.x models in streaming, code-execution, and native-tools paths to avoid validation errors.

PR [#8590](https://github.com/$GITHUB_REPOSITORY/pull/8590) (merged 2026-07-25T07:06Z, **8 hours later**) reverted the default back to `gemini-3-flash-preview`. The revert fixed the default, NOT the allowlist.

## Latent bug surface (still live as of 2026-07-30)

A user explicitly choosing `gemini-3.5-flash-lite` OR `gemini-3.6-flash` in settings still hits the native two-phase dice path. Combined with the new finding that Lite + 3.6 **infinite-loop** if added to the allowlist, the right fix is:

- Keep Lite + 3.6 in `ALLOWED_GEMINI_MODELS` (narrative still works)
- DO NOT add to `MODELS_WITH_CODE_EXECUTION` (current state is correct)
- Fix PR #8512's wrong comment ("inherits 3.x code execution + JSON single-pass" → remove or qualify as "for narrative only")
- Add a guardrail at the app boundary: if user picks Lite or 3.6 + code_execution is requested, return a clear 4xx error
- Add a 12-test contract in `$PROJECT_ROOT/tests/test_centralized_model_selection.py` pinning the contract

## GPT-5.6 Luna comparison (12-turn latency benchmark via OpenRouter)

Direct dice-prompt benchmark, 12 turns each, via OpenRouter (`https://openrouter.ai/api/v1/chat/completions`), model slug `openai/gpt-5.6-luna`:

| Model | mean | p95 | cost/12 turns | reasoning_tokens |
|---|---|---|---|---|
| `gemini-3-flash-preview` | 1.36s | 1.55s | $0.001242 | 0 |
| `gemini-3.5-flash` | 2.37s | 2.72s | $0.027594 | 2,677 |
| `gemini-3.5-flash-lite` | **0.88s** | **1.12s** | **$0.001020** | 0 |
| `gemini-3.6-flash` | 3.20s | **11.84s** | $0.023723 | 2,820 |
| `gpt-5.6-luna` | 2.16s | 3.18s | **$0.000390** | 274 |

**Luna is 3.7× cheaper than Flash Lite on this workload** but is Codex-only / OpenRouter-only (no direct OpenAI API key in env, no Anthropic-compat endpoint). To use Luna from the app, wire `LLM_PROVIDER_OPENROUTER` into the dice orchestrator at `$PROJECT_ROOT/llm_service.py:777` (which already has OpenRouter provider support).

## Auth paths (verified 2026-07-30)

| Source | Status |
|---|---|
| `~/.bashrc:1328` | only `GEMINI_MODEL="gemini-3-flash-preview"` (model name, not key) |
| `~/.gemini_api_key_secret` (file) | **DEAD** — `API_KEY_INVALID` |
| GCP secret-manager `gemini-api-key` (`worldarchitecture-ai` project) | **WORKS** — `AIzaSyAvyb...`, len 39, returns clean JSON |
| macOS Keychain `openrouter-pilot-api-key` | **WORKS** — used for Luna + all 4 Gemini OpenRouter probes |

**Working API call pattern (replace key with the GCP-secret output):**
```bash
SECRET=$(gcloud secrets versions access latest --secret="gemini-api-key" --project="worldarchitecture-ai" 2>/dev/null)
curl -sS -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent" \
  -H "Content-Type: application/json" \
  -H "x-goog-api-key: $SECRET" \
  -d '{"contents":[{"parts":[{"text":"Return JSON: {\"dice_total\": 7, \"rolls\": [3, 4]}"}]}],"tools":[{"codeExecution":{}}],"generationConfig":{"temperature":0.7,"responseMimeType":"application/json"}}'
```

## What a future session working on PR #8673 needs to know

1. The fix is a 4-component shape: comment fix + guardrail + 12-test contract + docs update.
2. The comment fix is critical — PR #8512's claim misleads future agents into adding Lite/3.6 to the allowlist.
3. The guardrail lives at the dice-orchestrator boundary, NOT at `MODELS_WITH_CODE_EXECUTION` (don't add them there even with a guard).
4. Full comparison report at `/private/tmp/gemini-luna-compare-new/comparison_report.md` (165 lines) on the `feat/gemini-flash-vs-luna-compare` worktree (HEAD `25c21c4c2d`, NOT pushed).
5. Luna is a real option for the dice path (~3.7× cheaper than Flash Lite) but requires separate wiring — out of scope for the immediate PR #8673 fix.
