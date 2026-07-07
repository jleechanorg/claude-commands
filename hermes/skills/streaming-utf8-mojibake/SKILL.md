---
name: streaming-utf8-mojibake
description: When a Python requests-based LLM provider silently corrupts multi-byte UTF-8 (em-dash, curly quotes) in streaming SSE responses, the cause is iter_lines(decode_unicode=True) using ISO-8859-1 default. Use when user reports "weird â\x80\x94" characters in LLM output, or when adding new streaming providers.
---

# Streaming UTF-8 Mojibake Bug

## Symptom

User sees LLM output containing mojibake sequences like:

- `â\x80\x94` instead of `—` (em-dash)
- `â\x80\x99` instead of `'` (right single quote / curly apostrophe)
- `â\x80\x9c` / `â\x80\x9d` instead of `"` / `"` (curly quotes)
- Other `\u00e2\u0080\u009X` patterns

Output is **non-deterministic per turn** — some turns are clean, some are corrupt. The pattern is non-deterministic because chunk boundaries sometimes split multi-byte UTF-8 characters and sometimes don't.

## Root cause

`requests.Response.iter_lines(decode_unicode=True)` decodes SSE bytes using `Response.encoding`. When the upstream SSE response doesn't set a `charset=` in `Content-Type`, `Response.encoding` defaults to **ISO-8859-1**. Every 3-byte UTF-8 character is then decoded as 3 separate ISO-8859-1 characters, producing the mojibake.

This is a well-known Python `requests` behavior. The library function `requests.utils.stream_decode_response_unicode` calls `r.encoding` (defaulting to ISO-8859-1) — NOT the Content-Type charset, NOT auto-detection.

## How to identify

In any file under `your_app/llm_providers/`, search for:

```python
response.iter_lines(decode_unicode=True)  # BUG
http_response.iter_lines(decode_unicode=True)  # BUG
```

These two patterns are the smoking gun. They appear in:
- `your_app/llm_providers/openrouter_provider.py:390`
- `your_app/llm_providers/openai_proxy_provider.py:391`

(As of 2026-06-04, both are still buggy.)

## How to fix

Replace `iter_lines(decode_unicode=True)` with `iter_lines()`. The downstream consumer in `your_app/llm_service.py:8029-8030` already does `chunk.decode("utf-8", errors="replace")` for bytes:

```python
# BEFORE (buggy):
for raw_line in response.iter_lines(decode_unicode=True):
    line = raw_line.strip()
    ...

# AFTER (safe):
for raw_line in response.iter_lines():
    if raw_line is None:
        continue
    line = raw_line.decode("utf-8", errors="replace").strip()
    ...
```

The safe pattern is already used in `your_app/llm_providers/openclaw_provider.py:291`:

```python
for line in response.iter_lines():
    if not line:
        continue
    decoded_line = line.decode("utf-8").strip()
    ...
```

The Gemini provider uses the official `google-genai` SDK stream (`for chunk in stream: yield part.text`) and does not have this issue.

## Alternative fix (also 1-line)

Force the response encoding before iteration:

```python
response.encoding = "utf-8"
for raw_line in response.iter_lines(decode_unicode=True):
    ...
```

This works but is less robust than dropping `decode_unicode` entirely because the response object's encoding can be reset by other code.

## Recovery of already-corrupted data

The mojibake mapping is exactly reversible:

| Mojibake | Original | Bytes (UTF-8) |
|----------|----------|---------------|
| `\u00e2\u0080\u0094` | `\u2014` (em-dash) | `e2 80 94` |
| `\u00e2\u0080\u0099` | `\u2019` (right single quote) | `e2 80 99` |
| `\u00e2\u0080\u009c` | `\u201c` (left double quote) | `e2 80 9c` |
| `\u00e2\u0080\u009d` | `\u201d` (right double quote) | `e2 80 9d` |

Recovery is provably exact because each mojibake sequence corresponds to a unique original character. Walk all string fields in the document, do `str.replace` for each pair. Reference implementation: `your_app/repro/evidence/7248/recover_mojibake_entries.py` in PR #7249.

## Why tests miss this bug

The existing test mocks (`DummyStreamResponse.iter_lines` in `your_app/tests/test_openrouter_provider.py:31` and `MagicMock().iter_lines` in `your_app/tests/test_openai_inference_proxy.py:323`) **silently swallow** the `decode_unicode` flag and yield pre-decoded strings:

```python
def iter_lines(self, decode_unicode=True):
    del decode_unicode
    yield from self._lines  # already str
```

The real `iter_lines` is never exercised in tests, so the ISO-8859-1 decode never happens. To write a regression test:

1. Use a mock that yields raw `bytes` (not pre-decoded str).
2. Set the mock's `encoding` attribute to `iso-8859-1` (or leave it unset) to mimic the real-world default.
3. Feed a multi-byte UTF-8 sequence in a chunk and assert the output is clean UTF-8 (not mojibake).

Reference repro: `your_app/repro/evidence/7248/repro_utf8_mojibake_streaming.py` in PR #7249.

## Investigation pattern (when user reports "weird characters in LLM output")

1. **Find owner UID** via `collection_group('campaigns')` filtered by document ID.
2. **Count mojibake per story entry** — pattern `str.count("\u00e2\u0080\u0094")` etc.
3. **Correlate mojibake with model + execution_path + system_prompt_char_count** by looking at `debug_info` on each entry. The bug is provider-specific, so this will show 100% correlation with the buggy provider.
4. **Code-trace** from the model name to the provider file to the streaming function.
5. **Find the `iter_lines(decode_unicode=True)` call** — that is the bug.
6. **Demonstrate with bytes**: use real UTF-8 bytes (`'\u2014'.encode('utf-8')` = `b'\xe2\x80\x94'`) and decode with `iso-8859-1` to show the mojibake. This is the most convincing proof.
7. **Verify the fix** by swapping `decode_unicode=True` for `decode_unicode=False` (or removing it) and re-running the bytes-level repro.

## Pitfalls

- **Don't use `ensure_ascii=False` only in JSON serialization** — `json.dumps` with `ensure_ascii=True` would have produced `\u2014` ASCII escapes, which would have survived the bug. The bug only manifests when the LLM's text actually contains real UTF-8 bytes.
- **Don't assume the bug is model-specific** — it's provider-specific. The same model (e.g. Grok-4.3) can be served cleanly via a different provider.
- **Don't try to fix this in the consumer (`llm_service.py`)** — the consumer is already correct (it decodes bytes as UTF-8). The fix must be in the provider, where `iter_lines(decode_unicode=True)` is called.

## Related

- Issue: $GITHUB_REPOSITORY#7248
- PR: $GITHUB_REPOSITORY#7249
- Skill: `repro` (the workflow that produced this finding)
- WA campaign used for evidence: `mXhtOccHYGHgV2Tdf0lc` (owner UID `vnLp2G3m21PJL6kxcuAqmWSOtm73`), 25 entries affected, 511 mojibake sequences
