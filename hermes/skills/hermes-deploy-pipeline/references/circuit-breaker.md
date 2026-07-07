# Circuit Breaker Diagnostics

## State File
```
~/.hermes_prod/state/circuit_breaker.json
```

## Live Diagnostic (run in any session)

```python
# Python REPL — use hermes-agent venv
import sys
sys.path.insert(0, '$HOME/projects_other/hermes-agent')
from agent.circuit_breaker import CircuitBreaker

cb = CircuitBreaker(state_file='$HOME/.hermes_prod/state/circuit_breaker.json')
import json
print(json.dumps(cb.status(), indent=2))
```

Or via hermes CLI:
```bash
hermes circuit-breaker status  # if implemented
```

## State Transitions

| `locked_to` | Meaning | Behavior |
|---|---|---|
| `null` | NORMAL | Use primary (GLM-5.1/wafer) |
| `"fallback"` | DEGRADED | Locked to fallback (MiniMax) for `degraded_duration` seconds |
| `"primary"` | RECOVERING | Primary allowed again for `cooldown_duration` seconds |

## Key Fields

- `consecutive_failures`: Increments on each primary failure. Resets on success or lock trip.
- `lock_expires_at`: Unix timestamp when current lock expires.
- `threshold`: Configurable via `model.failover.consecutive_failure_threshold` in `config.yaml`.
- `degraded_duration`: Lock duration on primary failure. Configurable via `model.failover.degraded_duration` in `config.yaml`. **Observed: ~24 min lock on first-trip** (not always 1 hour — depends on failure count and config; verify actual remaining time with `lock_expires_at - now` in Python).
- `cooldown_duration`: Default 3600s — how long to stay in RECOVERING state.

## Config (config.yaml)

```yaml
model:
  failover:
    enabled: true
    consecutive_failure_threshold: 3
    degraded_duration: 3600
    cooldown_duration: 3600
```

## Manual Reset

```python
cb = CircuitBreaker(state_file='$HOME/.hermes_prod/state/circuit_breaker.json')
cb.reset()
```