# opencode-go / GLM-5.1 Provider Setup

## Quick Diagnosis

The `opencode-go` provider uses `${OPENCODE_GO_API_KEY}` from bashrc/env — it is NOT stored in keychain like some other keys.

**Symptom: circuit breaker locked to fallback, primary fails silently**
- Primary model: `glm-5.1` via `opencode-go`
- Circuit breaker locks to `fallback` (minimax/MiniMax-M2.7) for 1 hour
- Logs show: `🔌 CircuitBreaker: pre-locked to fallback (minimax), bypassing primary.`
- **Root cause**: `OPENCODE_GO_API_KEY` not in bashrc when gateway last started, so primary failed all requests

**Verify the key is in bashrc:**
```bash
grep 'OPENCODE_GO_API_KEY' ~/.bashrc | head -1
# Should show: export OPENCODE_GO_API_KEY=sk-...
```

**Verify the key is in the running gateway's env:**
```bash
# The gateway's environment variables are injected by the launchd-env-wrapper.sh script or configured in the launchd plist (~/Library/LaunchAgents/ai.hermes.gateway.plist).
# Verify the running gateway's environment by querying launchd directly:
launchctl print gui/$(id -u)/ai.hermes.gateway | grep OPENCODE_GO_API_KEY
```

## env var Name

| Provider | env var |
|---|---|
| `opencode-go` | `OPENCODE_GO_API_KEY` |
| `zai` (fallback) | `GLM_API_KEY` |
| `minimax` (final fallback) | `MINIMAX_API_KEY` |

## Restart Gateway to Pick Up New env var

**NEVER use `--replace`** — it causes restart storms with launchd KeepAlive.

```bash
# Correct restart:
pkill -x hermes
# Let launchd restart it (it will pick up the new bashrc env)

# Or kickstart:
launchctl kickstart -k gui/$(id -u)/ai.hermes.gateway
```

## Circuit Breaker — Manual Reset

If locked and you want to reset immediately (after fixing the root cause):

```python
import json, time

state_path = "$HOME/.hermes_prod/state/circuit_breaker.json"
state = json.load(open(state_path))

# Show current state
print(f"Locked to: {state['locked_to']}")
print(f"Lock expires at: {state['lock_expires_at']:.0f} ({time.ctime(state['lock_expires_at'])})")
print(f"Remaining: {(state['lock_expires_at'] - time.time())/60:.1f} minutes")

# To reset: set lock_expires_at to past
if state['locked_to'] == 'fallback' and state['lock_expires_at'] > time.time():
    state['lock_expires_at'] = time.time() - 1  # expired
    state['locked_to'] = None
    json.dump(state, open(state_path, 'w'), indent=2)
    print("Reset: lock_expires_at set to past, locked_to = null")
```

Or via Hermes CLI if available:
```bash
hermes circuit-breaker reset
```

## Full Restore Sequence

1. Add `OPENCODE_GO_API_KEY=sk-Zorf...` to `~/.bashrc` (done)
2. Verify: `source ~/.bashrc && echo $OPENCODE_GO_API_KEY | head -c 10`
3. Reset circuit breaker: set `locked_to: null` in `~/.hermes_prod/state/circuit_breaker.json`
4. Restart gateway: `pkill -x hermes` (let launchd restart)
5. Verify: check logs for `Using provider: opencode-go` / `model: glm-5.1`

## Provider Config (config.yaml)

```yaml
model:
  default: glm-5.1
  provider: opencode-go
  fallback_model:
    provider: zai
    model: GLM-5.1
providers:
  opencode-go:
    name: opencode-go
    base_url: https://opencode.ai/zen/go/v1
    api_key: ${OPENCODE_GO_API_KEY}
    models:
      glm-5.1:
        context_length: 202752
        max_tokens: 32768
fallback_providers:
  - provider: zai
    model: GLM-5.1
  - provider: minimax
    model: MiniMax-M2.7
```