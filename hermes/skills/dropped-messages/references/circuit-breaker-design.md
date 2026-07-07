# Circuit Breaker — Model Failover Design

## What exists vs. what was built

### Pre-existing: Hermes Fallback Infrastructure
- `agent.error_classifier.FailoverReason` — enum: `rate_limit`, `billing`, `payload_too_large`, `long_context_tier`, `api_error`
- `run_agent.py` `_try_activate_fallback()` (line ~8382) — swaps client/model/provider in-place, advances through chain on each call; returns `False` when exhausted
- `run_agent.py` `api_max_retries` (config: `agent.api_max_retries`, default 3) — per-call retry count before fallback
- Eager fallback: 429/billing errors skip retries and call `_try_activate_fallback()` immediately

### Built this session: `agent/circuit_breaker.py`
**Location:** `$HOME/projects_other/hermes-agent/agent/circuit_breaker.py`

Three-state circuit breaker:

```
NORMAL (primary)
  │ consecutive failures ≥ 3
  ↓
DEGRADED (locked to MiniMax, 1h)
  │ timeout or recovery success
  ↓
RECOVERING (try primary once)
  │ primary succeeds
  ↓
NORMAL
  │ primary fails again
  ↓
DEGRADED (new 1h cooldown)
```

State persisted to `~/.hermes_prod/state/circuit_breaker.json`.

#### Core API
```python
from agent.circuit_breaker import get_circuit_breaker
_cb = get_circuit_breaker()
```

Methods:
- `current_routing_target()` → `"primary"` | `"fallback"`
- `record_failure(error_type: str)` — call when leaving primary → fallback
- `record_success()` — call on successful API response (resets to NORMAL)
- `record_recovery_failure()` — call when already degraded and gets another failure

#### Config keys to add to `config.yaml`
```yaml
model:
  failover:
    enabled: true
    consecutive_failure_threshold: 3
    degraded_duration: 3600        # seconds
    cooldown_duration: 3600         # seconds
```

#### Files modified
- `run_agent.py` — 3 patches:
  1. **Pre-loop check**: if `current_routing_target() == "fallback"`, call `_try_activate_fallback()` and reset retry state before entering the retry loop
  2. **On success**: call `circuit_breaker.record_success()` after `break  # Success`
  3. **On fallback activation**: call `record_failure()` when first fallback triggered from primary; `record_recovery_failure()` if already degraded

## Deploy pipeline note

⚠️ **Circuit_breaker.py was written directly to the projects directory**, NOT through the `~/.hermes/` → `~/.hermes_prod/` deploy pipeline. Before this is production-ready:
1. Move `circuit_breaker.py` to `~/.hermes/agent/` (staging)
2. Test in staging
3. Commit and push via `deploy.sh`

See `hermes-deploy-pipeline` skill for the correct order.

## Key behaviors

- Circuit breaker is **per-machine**, not per-session — state survives restarts
- `record_success()` only resets counter when on primary; if already degraded, success goes through RECOVERING first
- If MiniMax is not in the fallback chain, `_try_activate_fallback()` skips it and tries next entry
- 1h cooldown on degraded state prevents flapping between primary and fallback during extended outages