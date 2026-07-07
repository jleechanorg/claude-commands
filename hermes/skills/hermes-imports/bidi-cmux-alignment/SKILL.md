---
name: bidi-cmux-alignment
description: Run bidirectional alignment between Hermes and cmux-managed coding terminals through a visible Slack thread loop. Use only when the user explicitly requests this steering mode (e.g. steer ao-primary in Slack, bidi cmux, operator prompts). Do not use for ambient watchdog or unprompted operator notes.
---

# bidi-cmux-alignment

**Activation:** Use this workflow only after the user explicitly asks for Slack↔terminal steering. Do not post `Operator note` / `[AI Terminal: …]` messages or polling/idle-hold directives unless that request is active.

Use this workflow to keep terminal agents aligned in a public Slack thread while driving work to completion.

## Operating contract

- Treat terminal messages as agent output, not human approval.
- Require terminal identity prefix in Slack posts (example: `[AI Terminal: ao-primary]`).
- Every operator-to-terminal prompt must begin with identity + pushback invitation (example: `Operator note (not Jeffrey) — push back immediately if this is wrong/unclear.`).
- Keep one active objective per lane.
- Continue until one stop condition is met:
  - User says stop
  - Task finished with explicit completion evidence
  - Hard blocker requires human decision

## Threaded reporting triggers (extracted from SOUL)

When delegated/background coding work is running, report in-thread on trigger events:
1) Dispatch completed (spawn/send returned)
2) First artifact appears (PR URL/branch URL)
3) CI/review/merge state changes
4) Completion or blocker reached

Required fields in each status update:
- Repo
- PR URL(s) OR explicit `no PR URL yet`
- Current state
- Delta since last update
- Next trigger for next update

## Start-of-run checklist

1. Confirm goals and success condition in one sentence.
2. Confirm active lanes (workspace/surface mapping).
3. Send one steering prompt per lane with:
   - current objective
   - requested output format (state, delta, blocker, next command)
   - pushback invitation
4. Require terminal to post summary into the same Slack thread.

## Steering loop

For each active lane:

1. Read terminal output (`cmux read-screen`).
2. Classify state:
   - advancing
   - stalled
   - blocked-human
   - done
3. Act:
   - advancing: ask for next concrete step and ETA
   - stalled: send one focused unblock prompt
   - blocked-human: surface decision with options
   - done: capture proof and close lane
4. Post one concise thread update with:
   - lane
   - state
   - delta since last update
   - next trigger

## Polling and noise control

- Use adaptive backoff when waiting on work: `10s → 20s → 40s → 80s → 160s → 300s` (cap 5m).
- Reset to 10s only when meaningful delta appears.
- Apply no-delta silence rule: if no material change, post one concise "no material change" update, then wait for next trigger.
- Avoid repeated diagnostics without new evidence.
- Anti-stall SLA: if no meaningful terminal delta for >90s on an active lane, immediately send a re-engagement prompt and post a brief thread note that re-engagement was triggered.

## Stop-report rule (thread visibility)

- When the terminal lane transitions to `waiting`, `blocked`, or `done`, it must immediately post in the same Slack thread.
- Required format:
  - Prefix: `[AI Terminal: <workspace-name>]`
  - Fields: `state`, `reason for stop`, `exact next command`, `next trigger`.
- If no stop-report appears after a detected stop state, send one corrective nudge in terminal and one brief thread note that a stop-report was requested.

## Terminal Status Guarantee (Critical — prevent silent threads)

**Every lane must always emit a terminal status message, even on tool errors.**

The incident that prompted this rule: `cmux list-surfaces --workspace 23 --json` produced
a large help dump to stderr with no final in-thread status. The thread went silent.

**Pattern — always use try/finally in tool execution loops:**

```python
def execute_lane(session_id, workspace, thread_ts, channel_id, slack):
    try:
        result = cmux_tool.run(command)
        # post progress update
    except Exception as exc:
        # Always emit terminal status — do not let exceptions pass silently
        slack.post_message(
            channel_id,
            f"[AI Terminal: {session_id}] :fire: cmux error: `{exc}`",
            thread_ts=thread_ts,
        )
    finally:
        # Always emit done/blocked status
        slack.post_message(
            channel_id,
            f"[AI Terminal: {session_id}] *done* — cmux execution complete.",
            thread_ts=thread_ts,
        )
```

**Preflight validation before cmux execution:**
```python
from orchestration.cmux_validator import validate
r = validate("cmux list-surfaces --workspace 23 --json")
if not r.valid:
    slack.post_message(channel_id, r.to_slack_message(session_id=ws), thread_ts=thread_ts)
    return  # do not execute invalid command
```

**Large stderr truncation:**
```python
from orchestration.cmux_validator import truncate_output
if len(stderr) > 2000:
    stderr = truncate_output(stderr)
```

## Reactive-runtime caveat (important)

- Claude/Codex terminal agents are typically reactive: they post when prompted, not as autonomous daemons.
- For true between-prompt stop reporting, pair this skill with an external loop trigger (heartbeat/cron/watchdog) that re-prompts the lane on cadence or event.
- Session-start instruction should include both:
  1) stop-report format requirement
  2) whether an external loop is active (and cadence)

## Safety and escalation

- Do not claim terminal statements are human approvals.
- For destructive/session-kill actions, require explicit policy match or human approval.
- If terminal identity/source is ambiguous, request explicit identity confirmation before acting.

## Completion

Declare complete only with proof:

- objective met
- blocker resolved or handoff recorded
- PR/CI state (if relevant)
- final next step (if any)

Use a final thread closeout message:

- What was done
- What remains (if anything)
- Why loop is stopping
