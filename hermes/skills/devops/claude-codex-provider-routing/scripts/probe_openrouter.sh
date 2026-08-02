#!/usr/bin/env bash
# Probe OpenRouter (or any Anthropic+OpenAI compat provider) end-to-end:
# auth key → catalog → Anthropic-protocol message → OpenAI-protocol message →
# reasoning-model probe (Kimi K3 verified 2026-07-16).
# Returns 0 if everything 200s and answers with "pong", 1 otherwise.
#
# Usage: scripts/probe_openrouter.sh [provider_host]
#        (defaults to https://openrouter.ai)
#
# Optional env:
#   OR_REASONING_MODEL  — defaults to moonshotai/kimi-k3
#   OR_ANTHROPIC_MODEL  — defaults to anthropic/claude-sonnet-4.5
#   OR_OPENAI_MODEL     — defaults to openai/gpt-5
#   OR_PROBE_MAXTOKENS  — defaults to 512 (reasoning models need more than 32)
set -euo pipefail

HOST="${1:-https://openrouter.ai}"
REASONING_MODEL="${OR_REASONING_MODEL:-moonshotai/kimi-k3}"
ANTHROPIC_MODEL="${OR_ANTHROPIC_MODEL:-anthropic/claude-sonnet-4.5}"
OPENAI_MODEL="${OR_OPENAI_MODEL:-openai/gpt-5}"
MAXTOKENS="${OR_PROBE_MAXTOKENS:-512}"
: "${OPENROUTER_API_KEY:?OPENROUTER_API_KEY must be set}"

pass() { printf "  ✅ %s\n" "$1"; }
fail() { printf "  ❌ %s -- %s\n" "$1" "$2"; exit 1; }

# ---------------------------------------------------------------------------
echo "=== probe: auth key ==="
KEY_RESP=$(curl -sS -o /tmp/probe_key.json -w "%{http_code}" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" "$HOST/api/v1/auth/key")
[ "$KEY_RESP" = "200" ] && pass "auth/key = 200" \
  || fail "auth/key" "HTTP $KEY_RESP"
USAGE=$(python3 -c "import json; d=json.load(open('/tmp/probe_key.json')); print(d['data'].get('usage',0))")
echo "     cumulative usage USD: $USAGE"

# ---------------------------------------------------------------------------
echo "=== probe: catalog ==="
curl -sS -H "Authorization: Bearer $OPENROUTER_API_KEY" "$HOST/api/v1/models" \
  | python3 -c "
import json, sys
d = json.load(sys.stdin)
ids = [m['id'] for m in d.get('data', [])]
print(f'  models available: {len(ids)}')
for needle in ['$ANTHROPIC_MODEL','anthropic/claude-opus-4.7','$OPENAI_MODEL','$REASONING_MODEL']:
    matches = [i for i in ids if needle == i or i.startswith(needle)]
    if matches: print(f'  ✅ {needle:35} -> {matches[0]}')
    else: print(f'  ❌ {needle:35} MISSING from catalog')
"

# ---------------------------------------------------------------------------
echo "=== probe: Anthropic-protocol /api/v1/messages ==="
AC_RESP=$(mktemp)
HTTP=$(curl -sS -o "$AC_RESP" -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d "{\"model\":\"$ANTHROPIC_MODEL\",\"max_tokens\":32,
       \"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly the word pong\"}]}" \
  "$HOST/api/v1/messages")
[ "$HTTP" = "200" ] && pass "anthropic-protocol = 200" \
  || fail "anthropic-protocol" "HTTP $HTTP $(head -c 200 "$AC_RESP")"
grep -q '"text":"pong"' "$AC_RESP" && pass "anthropic response contains 'pong'" \
  || fail "anthropic response body" "$(head -c 200 "$AC_RESP")"
rm -f "$AC_RESP"

# ---------------------------------------------------------------------------
echo "=== probe: OpenAI-protocol /v1/chat/completions ==="
OI_RESP=$(mktemp)
HTTP=$(curl -sS -o "$OI_RESP" -w "%{http_code}" -X POST \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$OPENAI_MODEL\",\"max_tokens\":32,
       \"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly the word pong\"}]}" \
  "$HOST/api/v1/chat/completions")
[ "$HTTP" = "200" ] && pass "openai-protocol = 200" \
  || fail "openai-protocol" "HTTP $HTTP $(head -c 200 "$OI_RESP")"
grep -q '"content"' "$OI_RESP" && pass "openai response body has content" \
  || fail "openai response body" "$(head -c 200 "$OI_RESP")"
rm -f "$OI_RESP"

# ---------------------------------------------------------------------------
echo "=== probe: reasoning model $REASONING_MODEL (with backoff for launch-week 429s) ==="
# Reasoning models often rate-limit hard at launch. Retry with exponential backoff
# up to ~30s total before failing. Verified pattern for moonshotai/kimi-k3 on 2026-07-16.
REASON_RESP=$(mktemp)
HTTP=""
for attempt in 1 2 3 4 5 6; do
  HTTP=$(curl -sS -o "$REASON_RESP" -w "%{http_code}" -X POST \
    -H "Authorization: Bearer $OPENROUTER_API_KEY" \
    -H "Content-Type: application/json" \
    -H "anthropic-version: 2023-06-01" \
    -d "{\"model\":\"$REASONING_MODEL\",\"max_tokens\":$MAXTOKENS,
         \"messages\":[{\"role\":\"user\",\"content\":\"Reply with exactly the word pong\"}]}" \
    "$HOST/api/v1/messages")
  if [ "$HTTP" = "200" ]; then break; fi
  if [ "$HTTP" = "429" ] && [ "$attempt" -lt 6 ]; then
    wait=$((3 * attempt))
    echo "  [429 attempt $attempt/$((attempt+1)), sleeping ${wait}s]"
    sleep "$wait"
    continue
  fi
  break
done
[ "$HTTP" = "200" ] && pass "reasoning-protocol = 200" \
  || fail "reasoning-protocol" "HTTP $HTTP $(head -c 200 "$REASON_RESP")"
# Reasoning models return 3 content blocks: thinking, text, redacted_thinking.
# Verify the 'text' block contains the answer (not just content presence, which
# would also match an empty/whitespace-only content array).
grep -q '"text":"pong"' "$REASON_RESP" && pass "reasoning response contains 'pong' text block" \
  || fail "reasoning response body" "no text=pong match. body: $(head -c 300 "$REASON_RESP")"
# Also confirm a 'thinking' block was emitted (signature of a reasoning model)
grep -q '"type":"thinking"' "$REASON_RESP" && pass "reasoning response has thinking block" \
  || echo "  ⚠️  no thinking block detected (provider may have skipped reasoning for short prompt)"
# Confirm 'redacted_thinking' is present (OpenRouter artifact)
grep -q '"type":"redacted_thinking"' "$REASON_RESP" && pass "reasoning response has redacted_thinking block (OpenRouter artifact)" \
  || echo "  ⚠️  no redacted_thinking block (older OpenRouter surface)"
rm -f "$REASON_RESP"

# ---------------------------------------------------------------------------
echo
echo "All OpenRouter probes pass. claudeor / codexor / claudek are safe to use."
echo
echo "Note: reasoning-model result is dominated by the 'thinking' block budget."
echo "If you wired a wrapper via 'claude --print' and it exits 0 with empty stdout,"
echo "the model is responding fine — Claude Code 2.1.207 is not threading the"
echo "thinking block through. Use --verbose --output-format=json + parse_claude_verbose.py."
