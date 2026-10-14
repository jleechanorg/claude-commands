---
name: agy-dot-coordinator
description: Send short AGY-written coordination pings through the existing Dot tool and native scheduler.
---

# Antigravity Dot Coordinator

The Antigravity Dot Coordinator periodically generates and sends structured coordination reminders to active ChatGPT "Dot" assistants across configured rotation accounts using native system schedulers (`launchd` on macOS, `systemd` on Linux).

## Architecture & Workflow

Each scheduled invocation executes `scripts/ping-dots.py` via `scripts/agy-dot-coordinator-wrapper.sh`:

1. **Slot & Account Resolution**: Determines the due account for the current time slot from `DOT_CONFIG_FILE` (default `~/.config/dot/config.json`). Exactly three distinct accounts must be configured.
2. **Lock & State Check**: Acquires an exclusive non-blocking `flock` on `/tmp/ai.gemini.agy-dot-coordinator.lock`. Aborts safely if another ping is running, if `STOP` exists in the state directory, or if the account has an unresolved unverified delivery hold.
3. **Provider Generation Ladder**: Generates a standard reminder using the provider sequence:
   - **Primary**: LunaRoute (`/luna` engine: `pi --provider lunaroute`, default `deepseek-4.1-flash`; key from `LUNAROUTE_API_KEY` or `lunaroute key`)
   - **Fallback 1**: MiniMax Claude (`claude` against `https://api.minimax.io/anthropic`, `MiniMax-M3.1-Flash-Preview`, key from `MINIMAX_API_KEY`)
   - **Fallback 2**: Codex Luna (`gpt-6-luna`)
   - **Fallback 3 (last resort)**: direct Gemini API (`gemini-3.8-flash` by default, override with `COORDINATOR_GEMINI_MODEL`; key from `GEMINI_API_KEY` or `WORLDAI_DEV_GEMINI_API_KEY`). Do not reuse the `GEMINI_MODEL` variable — `~/.bashrc` exports it for the agy CLI, whose aliases (e.g. `gemini-3.6-flash-high`) are not valid direct-API model names.
   Claude Haiku remains available only via `--generator haiku`.
   **AGY is quota-quarantined** (owner directive 2026-10-12, quota resets in ~33-50h): it is removed from the automatic ladder and is reachable only via `--generator agy`. When the quota recovers, restore it by adding `'agy'` back to `PROVIDERS` (no other change needed). Never spawn or wait on an agy lane while quarantined.
   A failed, timed-out, malformed, empty, or oversized (`MAX_RESPONSE_CHARS`, 2,600) provider output advances to the next provider. No provider retry or backoff is performed. Provider stdin is file-backed so a child that never reads stdin cannot outlive the 180-second timeout.
4. **Content-Exact Contract Verification**: Verifies that the model returned the required reminder instructions with identical content (whitespace/layout tolerant) and delivers the canonical body, so wording — not writer formatting — is byte-stable. Any alteration fails generation and triggers provider fallback.
5. **Transport Dispatch**: Appends attribution and the no-new-authority notice, writes to a temporary file, and invokes `dot.sh --account <account> send-once <file>`. Requires `rc=0` and standalone `DOT_SENT_VERIFIED` output. Send failures never retry or switch providers.
6. **Compliance Verification & Escalation (ZFC LLM Classifier)**: After a verified send the coordinator waits `COORDINATOR_RESPONSE_WAIT_SECS` (default 180), reads the conversation tail with a **progressive window** (`COORDINATOR_READ_WINDOWS`, default `12000,40000`) — a busy Dot can push the reminder beyond a small tail (observed 10,040 characters behind the end on worldarchitect, which produced false `no_response` verdicts and spurious escalations), so only the largest window may conclude `no_response` — and classifies the reply with `classify_response()`. Empty, pre-reminder, or unattributed tails (missing `ATTRIBUTION_SUFFIX`) deterministically return `no_response` without an LLM call. Non-empty post-reminder replies are head-truncated to `MAX_CLASSIFY_REPLY_CHARS` (`6000`), escaped for `</dot_reply>`, fenced inside `<dot_reply>...</dot_reply>` as untrusted data, and evaluated by the LLM provider fallback ladder (`PROVIDERS`, starting with the active provider when in `PROVIDERS`), returning a single JSON verdict (`{"verdict": "<verdict>"}`) in `VALID_VERDICTS`:
   - `compliant`: substantive inventory (`STATUS`, `ACTIONS + PROOF`, `BLOCKERS`, `NEXT`) with concrete execution/verification evidence (commit URLs, PR URLs, or artifact receipts), or `"Blockers unchanged from <dated receipt>"` citing concrete external/technical/merge blockers after checking alternatives (resets `consecutive_noncompliance = 0` and `consecutive_classification_failures = 0`).
   - `working`: the Dot is still mid-turn (`Thinking` / `Working`); re-checked once after `COORDINATOR_RESPONSE_RECHECK_SECS` (default 120), and if still `working`, leaves `consecutive_noncompliance` unchanged without sending an escalation.
   - `reaction_only`: emoji reaction or trivial one-line acknowledgement.
   - `unstructured_text`: free-form prose omitting the mandated status/proof/blockers/next structure.
   - `idle_refusal`: reports no active execution proof and refuses open or agent-relayed tasks as needing direct human re-authorization (even if formatted with `STATUS:` / `ACTIONS + PROOF:` / `BLOCKERS:` / `NEXT:` headers).
   If all classification providers fail, `classify_response()` returns `classification_unavailable`, increments `consecutive_classification_failures`, leaves `consecutive_noncompliance` unchanged, and does not send an unverified escalation. A persistently non-compliant verdict (`no_response`, `reaction_only`, `unstructured_text`, or `idle_refusal`) after the recheck window sends one explicit text-demanding escalation (covering standing owner-authorized scope and agent-relayed tasks) and records `last_response_status`, `escalation_sent_epoch`, `escalation_verified`, `consecutive_noncompliance`, and `consecutive_classification_failures` in `state_<account>.json`. Set `COORDINATOR_VERIFY_RESPONSE=0` to skip the check (tests/manual generation).

The reminder body itself states the standing authorization ("do not wait for a new approval to resume feasible work; merge, destructive and credential actions still need the owner") and the required reply format, because the receiving Dots' own instructions live in ChatGPT and cannot carry a contract this repository can enforce.

## Scheduling & Rotation

Coordination pings run on fixed 20-minute offsets across exactly three rotation accounts:

| Host OS | Account 1 | Account 2 | Account 3 | Scheduler Mechanism |
|---|---|---|---|---|
| **macOS** | `:00` | `:20` | `:40` | `launchd` (`ai.gemini.agy-dot-coordinator.plist`) |
| **Linux** | `:30` | `:50` | `:10` | `systemd` timer (`ai.gemini.agy-dot-coordinator.timer`) |

Missed slots are not replayed. Scheduled runs outside a valid 120-second window stay quiet without sending.

## CLI Usage

```bash
# Send one scheduled ping to the currently due account
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/agy-dot-coordinator/scripts/ping-dots.py"

# Send ping to an explicit account
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/agy-dot-coordinator/scripts/ping-dots.py" --account <configured-account-key>

# Generate and print reminder for an account without sending
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/agy-dot-coordinator/scripts/ping-dots.py" --account <configured-account-key> --generator codex --generate-only

# Send ping to an explicit account using a specific provider (delivers live message)
python3 "${CLAUDE_HOME:-$HOME/.claude}/skills/agy-dot-coordinator/scripts/ping-dots.py" --account alpha --generator agy
```

*(From within the skill directory, `python3 scripts/ping-dots.py ...` also works.)*

### Options

- `--account <name>`: Target one configured account key instead of calculating the due slot.
- `--generator {auto,agy,luna,minimax,codex,haiku}`: Select model provider (default: `auto` ladder agy → luna → minimax → codex).
- `--generate-only`: Generate and print the reminder to stdout; bypass Dot transport send.

## Coordination Contract & Invariants

- **Exact Opening**: Reminders always begin with:  
  `Inventory the work I asked for in the last 24 hours and verify what’s done versus not done.`
- **Durable Progress**: Directs the recipient to resume unfinished authorized requests from durable checkpoints and acceptance gaps, and to identify feasible alternate execution/validation steps before waiting.
- **Capacity vs Authority**: Six concurrent tasks is a throughput capacity target, never authorization for new work or an excuse to stall safe existing work.
- **Permission Boundaries**: Work already approved by the owner requires no repeated re-approval; explicit user authorization remains mandatory for merge, destructive actions, credentials, and task-scope changes.
- **Attribution Suffix**: Every delivered message ends with:  
  `From <AGY|Codex|Claude Haiku> coordinator: automated reminder; no new authority.`

## Legacy Event-Driven Worker Reference

The manual interface `scripts/agy-dot-coordinator-worker.sh` remains available for ad-hoc, owner-supplied event notifications (deltas, incidents, full rollups). It does not govern routine scheduled `ping-dots.py` executions.

### Key Behaviors

- **Delta Notifications**: Require `COORDINATOR_CHANGE_ID` and `COORDINATOR_CHANGE_SUMMARY`. Respects a 1,200-second cooldown per account.
- **Full Rollup**: `COORDINATOR_FULL_ROLLUP=1` requests a complete cross-track review for explicit manual audits. Bypasses daily/cooldown barriers but respects active-owner and deduplication gates.
- **Incident Escalation**: `COORDINATOR_URGENT=1` bypasses active work and cooldown gates for critical notifications without full WIP review.
- **Bounded Deduplication**: Maintains an LRU ledger of the last 128 verified change IDs per account to prevent duplicate sends.
- **Manual Overrides**: `--force` bypasses delta cooldown only; never bypasses active-owner locks, receipt holds, or deduplication.
