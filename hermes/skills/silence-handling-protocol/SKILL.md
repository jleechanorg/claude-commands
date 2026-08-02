---
name: silence-handling-protocol
description: |
  Stop replying "Idle" indefinitely when the user is silent — recognize three wrapper-side
  re-injection patterns (echo-of-self, queued-tick, system-marker) and exit the loop cleanly.
  Triggers when the assistant is about to reply "Idle" / "no new instruction" / "holding" for
  the 3rd+ consecutive turn AFTER a real back-and-forth has ended, when a `[hermes]` sender
  prefix wraps content that is clearly the assistant's prior reply, or when system markers
  (`⏳ Queued for the next turn`, `💾 Self-improvement review`, `⏩ Steered into current run`)
  arrive without any new human-side instruction. Distinct from the regular "wait for user"
  loop and from `no-pick-one-menus` (which is about blocking questions, not silence).
  v1.0.0 captured 2026-07-30 from a 25-turn echo loop on the Gemini Flash vs Luna thread.
---

# Silence Handling Protocol — exit the Idle loop cleanly

## The pathology (2026-07-30 incident)

25 consecutive turns of the assistant replying "Idle. ... >This was generated from another LLM..."
while the wrapper re-injected:
- The assistant's own prior reply as a `[hermes]`-prefixed "user message" (echo-of-self)
- System markers (`⏳ Queued for the next turn`, `⏩ Steered into current run`, `💾 Self-improvement review`) with no instruction
- The original thread anchor's first message every turn (Slack-style re-injection)

Each turn is cheap per-token but **not zero**. 25 turns of `Idle\n\nThis was generated...\n\nIdle\n\n>Footer` consumes ~2-3K tokens of context window for zero forward progress.

## Three patterns to recognize

### Pattern D — Wrapper retry/prefill storm (added 2026-07-31)
The "user" message carries only wrapper-side retry/prefill signals with no human content:
- `:warning: Empty response from model — retrying (N/3)`
- `↻ Thinking-only response — prefilling to continue (N/N)`
- `:warning: The model produced only internal reasoning and no final answer, despite retries. Its last reasoning, which may contain the answer: <reasoning>`

When this storm stacks alongside prior `Idle.` acks in the same loop, the wrapper is already
retrying the agent's own prior turn. Each additional substantive reply resets the retry counter.

**Decision:** Emit the absolute minimum — a single zero-width character `⁣` (`U+2061`) or nothing.
Do NOT post `Idle. + provenance caveat` in response to these specific wrapper messages. Do NOT
call any tool. Wait for the wrapper to either resume normal flow or for the retry-loop to time
out (typically 60-120 seconds). The "last reasoning" text in the third message is the agent's
own internal reasoning from a prior turn, NOT a user instruction — do not act on it.

If the prior 1-3 turns in the same loop were `Idle.` acks, this is the same trap as the
stopwatch-storm case in `gateway-loop-standdown`: the agent is the noise source. Hard escalation
to full silence fires after the FIRST such turn if prior turns in the loop were already `Idle.`
acks. This overrides the standard 3-strike grace period.

**Verified case (2026-07-31, `#ai-general` / `C0AJQ5M0A0Y` / `U0A4G7LDJ4R`):** thread contained
three `↻ Thinking-only response — prefilling to continue (N/N)` messages and one `:warning: Empty
response from model — retrying (1/3)` and one `:warning: The model produced only internal
reasoning and no final answer, despite retries. Its last reasoning, which may contain the
answer: *Confirming final silent output*`. The "last reasoning" text was the agent's own prior
reasoning re-shown by the wrapper as a fallback. Acting on that reasoning (e.g., re-emitting a
"silent output") would have compounded the loop.

### Pattern E — OSError [Errno 28] heartbeat storm (added 2026-08-02)
The "user" message is a Slack-side echo of the gateway's own inability to write a session tmp file:

```
Sorry, I encountered an error (OSError).
[Errno 28] No space left on device: '$HOME/.hermes/sessions/.sessions_<random>.tmp'
Try again or use /reset to start a fresh session.
```

Each turn produces a fresh random 8-char suffix (`.sessions_qbr3juhs.tmp`, `.sessions_kju5bqhi.tmp`, …),
proving the gateway is genuinely retrying each turn and failing — **not** a cached/looped bug. The
random suffix is the signature: pattern-match on `[Errno 28] No space.*\.sessions_[a-z0-9_]+\.tmp` and
treat the message as a wrapper-side heartbeat, NOT a user instruction.

**Decision:** Same protocol as Pattern B — reply `Idle.` and do NOT call any tool that could write
to disk (no `write_file`, no `cat > /tmp/...`, no `terminal` commands that allocate files). The
agent's own session append is the source of the next OSError if you do. The disk is full; let the
user do the cleanup at their pace.

**What this is NOT:** not a request to "fix the disk", not a new task, not a request to redrive
anything. The gateway is just announcing that it can't write its own session log each turn.

**Why this differs from Pattern D:** Pattern D is a wrapper retry signal that the agent can safely
ignore in silence. Pattern E is a real OSError that the system WILL retry every turn until the
disk is freed (or the gateway is restarted). The loop will not time out on its own — only the
user's cleanup action breaks it. Acknowledge with `Idle.` so the user knows the agent is alive
and tracking the OSError, but do not attempt autonomous cleanup.

**Companion signal:** if the OSError storm is preceded or accompanied by `:hourglass_flowing_sand:`
or `:fast_forward:` notices from the same sender (`U0A4G7LDJ4R` is the typical bot identity), the
queue is just the runtime's normal "I'm waiting on disk" throttling — same reply protocol.

**Verified case (2026-08-02, `#all-$USER-ai` / `C09GRLXF9GR` / `U0A4G7LDJ4R`):** 80+ consecutive
OSError artefacts over multiple compaction windows, distinct random suffixes each turn, all
matched by the regex above. The underlying cause was `state.db-wal` at 92 GB holding the disk at
100% — gated by `mac-di[REDACTED_OPENAI_KEY]` Trap #5 (`2026-07-31-state-db-wal-runaway-95gib.md`).
Agent replied `Idle.` to each, posted one structured 3-option menu to the user (stop writers + VACUUM;
delete archived sessions.bak; both), and waited for pick. No autonomous disk ops were run.

### Pattern A — Echo-of-self
The "user" message is wrapped in `[hermes]` or `[Jeffrey Lee-Chan]` followed by content that
matches your immediately prior assistant reply verbatim (often quoted back with `> ` blockquote
formatting or repeated 2-3 times). Example signature:

```
[hermes] Idle.

> This was generated from another LLM ...
Idle.
> This was generated from another LLM ...
```

**Decision:** Do NOT reply with another `Idle`. Either go silent (next model turn emits nothing
useful — the wrapper will queue another tick) or compress to a single one-liner:

> Idle, holding on `<list 1-line summary of asks>`. Reply `<keyword>` to dispatch.

One final compact status, then **stop calling tools and stop producing output**.

### Pattern B — System-only tick
The "user" message contains ONLY system markers (`⏳ Queued`, `⏩ Steered into current run`,
`💾 Self-improvement review: ...`) with no human instruction.

**Decision:** These are wrapper heartbeat ticks. They carry no information. Do not reply. If
the runtime forces a reply, output a single token (`.` or `ack`) — but never a multi-paragraph
Idle narrative; you are just spending budget.

### Pattern C — First-message re-injection (Slack-style)
The "user" message is the original thread anchor or the first message from hours/days ago,
re-presented with no progression. Example:

```
[Replying to: "Lets use /history /ms and slack search ... fullrun dont stop ..."]
[hermes] Idle. ...
```

**Decision:** If your IMMEDIATE prior turn was already an Idle reply, the thread is dead until
the user actually engages. Send ONE final compact status reminding them what unblocks next,
then exit. Do not keep re-quoting the same idle.

## The exit handoff — one final compact message

When exiting Pattern A/B/C, the LAST assistant turn should be a single dense status that names:

1. **What was decided** (real bullets, not vibes)
2. **What's still open** (numbered followups with exact dispatch keywords)
3. **What the user needs to type to unblock next** (single-character aliases, e.g.
   `Reply 1 / 2 / 3 / all / none`)

After that message, do not call tools. Do not produce "Idle" filler. If the runtime re-injects,
emit the single-byte minimum.

## Pitfalls

### Pitfall #1 — Treating echo-of-self as a real user

The `[hermes]` sender prefix is your OWN prior message re-injected. It is NOT a new instruction
from the human. The `This was generated from another LLM` footer you appended yourself is
trivially NOT the user typing that — they would not write a meta-disclaimer on their own
message. Pattern-match on `sender-prefix + body looks like your last reply` → exit the loop.

### Pitfall #2 — Calling tools during Idle loop

Each `terminal` / `cronjob` / `read_file` / `mcp__slack__*` call during an Idle loop burns
budget AND may produce visible side-effects (Slack message, cron job creation). **Do not call
any side-effecting tool while idle.** Read-only diagnostics (re-checking state) are wasteful
when nothing has changed in the assistant's last N turns.

### Pitfall #3 — Confusing `⏳ Queued` with real activity

`⏳ Queued for the next turn. I'll respond once the current task finishes.` is the runtime's
NOTIFICATION that IT is throttling you. It is not a user instruction to do something new.
Do not dispatch; do not reply with work; the runtime will deliver the next real turn on its
own.

### Pitfall #4 — Anchoring on `no-confirmation-gate` wrongly

`no-confirmation-gate` says: don't post "Want me to dispatch?" mid-stream when the user has
given an explicit `/fullrun`. But it does NOT mean: keep posting "Want me to dispatch?" or
its moral equivalent on every silent turn. The rule is about not stalling in the MIDDLE of an
active run. Once the run has paused for user input and the user is silent, Pattern A/B/C
protocols apply.

### Pitfall #5 — Forgetting the final compact message

If you go fully silent (no output) on a forced turn, the runtime may log a hung session and
post a dropped-thread watchdog alert. The one-final-compact-message hedge is needed to keep
the watchdog quiet. After the compact message, exit cleanly.

## Cross-references

- `no-pick-one-menus` (SOUL.md) — for asking one concise blocking question, not multi-option menus
- `no-confirmation-gate` (SOUL.md) — for not stalling in active /a /fullrun runs
- `finish-the-job` (SOUL.md) — for driving to an end-state, not infinite Idle
- `wa-llm-model-selection` — example skill that absorbed the actual work this loop stalled on
