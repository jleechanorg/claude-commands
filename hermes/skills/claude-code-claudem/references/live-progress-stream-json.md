# Live progress via `claudeminimax` streaming output

Verified 2026-07-28 in $GITHUB_REPOSITORY Spellblade/Valeria campaign
review thread (Slack `C0AJ3SD5C79`). Use this when the user asks "tell me
what's happening" during a long-running coding worker.

## When this applies

- User explicitly wants live progress during a worker run.
- You don't want to invoke tmux orchestration (lighter weight).
- The worker is producing flushed, line-delimited output you can grep.

## The recipe

1. Build a local program that emits a heartbeat marker at known cadence:

   ```python
   #!/usr/bin/env python3
   from __future__ import annotations
   import sys, time


   def fibonacci(n: int) -> int:
       a, b = 0, 1
       for _ in range(n):
           a, b = b, a + b
       return a


   def main() -> int:
       count = int(sys.argv[1]) if len(sys.argv) > 1 else 8
       delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.05
       for i in range(count):
           print(f"FIBONACCI_PROGRESS index={i} value={fibonacci(i)}", flush=True)
           time.sleep(delay)
       print("FIBONACCI_DONE", flush=True)
       return 0


   if __name__ == "__main__":
       raise SystemExit(main())
   ```

   Note `flush=True` on every print — without it, Python's stdout buffering
   hides progress until the process exits or the buffer fills.

2. Invoke `claudeminimax` (or `claudem`) with `stream-json` output:

   ```bash
   bash -lic 'claudeminimax -p "Run exactly: python3 /tmp/<heartbeat>.py 8 0.2 ; \
   then report every FIBONACCI_PROGRESS line and whether FIBONACCI_DONE \
   appeared. Do not edit files." \
   --max-turns 3 \
   --output-format stream-json --verbose --include-partial-messages'
   ```

3. Capture from the parent Hermes process with
   `terminal(command="...", background=true, notify_on_complete=true, pty=true)`.
   `pty=true` matters for streamed output.

## Verified round-trip (2026-07-28)

```text
canonicalModel: minimax-m3
provider: firstParty
api_error_status: null
subtype: success
FIBONACCI_PROGRESS index=0 value=0
FIBONACCI_PROGRESS index=1 value=1
FIBONACCI_PROGRESS index=2 value=1
FIBONACCI_PROGRESS index=3 value=2
FIBONACCI_PROGRESS index=4 value=3
FIBONACCI_PROGRESS index=5 value=5
FIBONACCI_PROGRESS index=6 value=8
FIBONACCI_PROGRESS index=7 value=13
FIBONACCI_DONE
exit code: 0
```

The agent returned the full sequence verbatim (8 progress markers + DONE)
with `subtype: success`, confirming both the wrapper routing AND that the
program's flushed output is observable by Hermes.

## What this proves

- `claudeminimax` resolves correctly on this host (bashrc function visible).
- `claudem` routes to `minimax-m3` (`canonicalModel: minimax-m3`).
- It can execute a local program and capture its flushed stdout.
- `stream-json` output is observable by the parent Hermes process.

## What this does NOT prove

- The worker cannot post to Slack from inside its own process — see the
  SKILL.md "Worker scope vs gateway scope" gotcha and
  `references/round-trip-dispatch-proof.md` for the curl-based worker-to-Slack
  pattern.
- This is NOT live progress from the worker *itself* — it is the worker's
  *result payload* captured by the parent. For genuinely streaming partial
  progress mid-worker-turn, use tmux orchestration instead.
