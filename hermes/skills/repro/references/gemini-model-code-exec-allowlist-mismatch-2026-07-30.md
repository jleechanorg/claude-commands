# Gemini model code-execution allowlist mismatch — a new bug class (2026-07-30)

## Class signature

A model is **advertised as code-execution-capable** (PR comment, vendor docs, or internal mapping comment) but the actual API behavior is one of two failure modes:

1. **Allowlist gap** — model not in `MODELS_WITH_CODE_EXECUTION` allowlist. Code path silently falls back to native two-phase / structured-output, not code-execution tool. Symptom: latency/cost bump; users rarely notice unless they compare baseline.
2. **Infinite loop** — model IS exposed to the `code_execution` tool but the model loops forever, returning `finish_reason: TOO_MANY_TOOL_CALLS` with 40-50 code parts and 20-27k tokens, never producing a structured response.

Both modes were caught on `$GITHUB_REPOSITORY` during a flash-vs-Luna benchmark. See [issue #8673](https://github.com/$GITHUB_REPOSITORY/issues/8673).

## Diagnostic recipe (API-level probe)

A static allowlist read (`grep` for `MODELS_WITH_CODE_EXECUTION`, `m.model_to_use in constants.MODELS_WITH_CODE_EXECUTION`, etc.) catches **mode 1** but **misses mode 2 entirely**. You must probe the live API to detect infinite-loop models.

```python
# Run for every model claimed to support code execution, with a trivial structured-output request:
import requests
MODEL = "gemini-3.5-flash-lite"  # example
SECRET = "$(gcloud secrets versions access latest --secret=gemini-api-key --project=worldarchitecture-ai)"
body = {
    "contents": [{"parts": [{"text": 'Return JSON: {"dice_total": 7, "rolls": [3, 4]}. Use the code execution tool to roll the dice.'}]}],
    "tools": [{"codeExecution": {}}],
    "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
}
r = requests.post(
    f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent",
    headers={"x-goog-api-key": SECRET, "Content-Type": "application/json"},
    json=body, timeout=30,
).json()
parts = r["candidates"][0]["content"]["parts"]
text = "".join(p.get("text", "") for p in parts)
finish = r["candidates"][0]["finishReason"]
code_parts = sum(1 for p in parts if "executableCode" in p or "codeExecutionResult" in p)
# Verdict:
#   finish == "STOP" and code_parts <= 4 → working
#   finish == "STOP" and code_parts > 10 → may be looping, increase n
#   finish == "TOO_MANY_TOOL_CALLS" → INFINITE LOOP, do NOT add to code-exec allowlist
```

## Verified findings (2026-07-30)

Tested against `gemini-api-key` from GCP Secret Manager (`worldarchitecture-ai` project):

| model | finish | code_parts | tokens | result |
|---|---|---|---|---|
| `gemini-3-flash-preview` | `STOP` | 2 | 849 | clean JSON ✓ |
| `gemini-3.5-flash` | `STOP` | 2 | 745 | clean JSON ✓ |
| `gemini-3.5-flash-lite` | `TOO_MANY_TOOL_CALLS` | 48 | 26,977 | empty (infinite loop) ❌ |
| `gemini-3.6-flash` | `TOO_MANY_TOOL_CALLS` | 48 | 21,235 | empty (infinite loop) ❌ |

## What history says (PR bodies, not guessed)

- [PR #8512](https://github.com/$GITHUB_REPOSITORY/pull/8512) added `gemini-3.5-flash-lite` + `gemini-3.6-flash` to the dropdown with comment "inherits 3.x code execution + JSON single-pass" — the comment was **doubly wrong** for both models.
- [PR #8571](https://github.com/$GITHUB_REPOSITORY/pull/8571) made 3.5-flash-lite the default → reverted by [PR #8590](https://github.com/$GITHUB_REPOSITORY/pull/8590) within 8 hours after cost/latency regression was noticed in prod.
- PR #8590 only fixed the **default**, not the allowlist. The latent mode-1 bug (allowlist gap) is still live for any user explicitly picking 3.5-flash-lite or 3.6-flash in settings.

## Recommended fix shape (for future similar bugs)

1. Keep the failing model in `ALLOWED_GEMINI_MODELS` (narrative still works)
2. DO NOT add it to `MODELS_WITH_CODE_EXECUTION`
3. Fix the misleading comment in the PR that introduced the model
4. Add a guardrail at app boundary: if the user picks an "incompatible" model and code execution is requested, return a 4xx with a clear "this model can't do code execution" message
5. Pin the contract with a 12-test suite (Lite + 3.6 MUST NOT be in the allowlist) so a future agent doesn't re-add them

## Auth path for direct Gemini API testing (verified)

- `~/.gemini_api_key_secret` (local file) → **DEAD** (`API_KEY_INVALID`, key `AIzaSyDQ6a...` len 39)
- `gcloud secrets versions access latest --secret=gemini-api-key --project=worldarchitecture-ai` → **WORKS** (key `AIzaSyAvyb...` len 39)
- Bashrc `~/.bashrc:1328` only sets `GEMINI_MODEL="gemini-3-flash-preview"` (model name, not a key)
- Direct Gemini API via this key: `POST https://generativelanguage.googleapis.com/v1beta/models/<MODEL>:generateContent` with `x-goog-api-key` header

## Related verification (Cross-cutting)

The same allowlist-vs-API-behavior gap could exist for any "structured output + tool use" capability claim. Future agents verifying a new model class should run this 3-step probe:

1. **Static allowlist check** — is the model in the relevant allowlist? If yes, proceed. If no, but the model is in `ALLOWED_*`, this is mode 1.
2. **API behavior probe** — does the model actually use the tool without infinite-looping? This is mode 2.
3. **Cost/latency benchmark** — is the model actually cheaper/faster than the baseline? Mode 1 sometimes still ships with a cost regression vs the tool-use path (because native two-phase is slower than code-execution tool use on dice-style workloads).

## Files (this session, worktree)

- Comparison report: `/private/tmp/gemini-luna-compare-new/comparison_report.md`
- Worktree branch: `feat/gemini-flash-vs-luna-compare` at `25c21c4c2d` (committed, NOT pushed)
- Direct API probe scripts: `run_compare.py`, `run_latency_bench.py`
- Issue: [#8673](https://github.com/$GITHUB_REPOSITORY/issues/8673)
- Bead: `rev-gemini-flash-lite-36-code-exec-loop-b7ka1`
