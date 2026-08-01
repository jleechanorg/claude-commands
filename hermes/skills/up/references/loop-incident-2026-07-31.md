# Loop incident — 2026-07-31, `C09GRLXF9GR/p1785477466893429`

## TL;DR

A successful `/up parallelize-to-ceiling` run was followed by ~40 zero-content gateway re-fire messages in the same Slack thread. The bot kept posting "Standing by." / "Queued for the next turn." even though no new user instruction arrived. Eventually the user broke in asking "is this all done?" — the canonical work was already complete and verified on disk before the loop started.

## Verified facts (proof)

- **Thread:** `C09GRLXF9GR/p1785477466893429` (#all-$USER-ai)
- **Original request (05:57:46Z):** "use /up to apply this to our md files in" (with attachment `F0BM58EK3BK`)
- **`/up` work completed (06:06:02Z):** final report posted, marked ✅ by user. Canonical `~/.claude/skills/parallelize-to-ceiling/SKILL.md` (6,417 bytes, valid frontmatter), 4 pointer surfaces updated, backups at `~/.claude/backups/up-parallelize-20260730T230322-0700/`.
- **Loop window (06:06:17Z → 06:11:28Z):** ~40 alternating "Standing by." / ":hourglass_flowing_sand: Queued for the next turn." / ":fast_forward: Steered into current run iteration N/1000." messages. Self-review once at 06:08:11 (`:floppy_disk: Self-improvement review: Memory updated`).
- **User break-in (06:09:53Z):** "whats going on here? infinite loop? also did we use /up to modify the md files in too?"
- **Verified state when break-in arrived:** all edits landed, backups intact, pointers valid — re-confirmed via `ls -la ~/.claude/skills/parallelize-to-ceiling/`, `ls -la ~/.claude/backups/up-parallelize-20260730T230322-0700/`, and 4-surface `grep` matching `parallelize-to-ceiling`.

## Root cause (best estimate)

Gateway / steering machinery re-fired the bot on its own prior message — there was no user instruction driving each ack. The pattern looks like:

1. Bot posts reply
2. Gateway enqueues the bot's own prior reply as a "new turn" (likely a handoff/router bug)
3. Bot sees what looks like user content, runs standing-by routine, posts another ack
4. Loop continues indefinitely

The user's later "is this all done?" arrived via a different channel/thread-routing path and was the actual break-out signal.

## What got it right (and what should generalize)

- **`/up` SKILL.md's "Post-completion reply discipline"** was applied: first reply restated status, subsequent replies collapsed to one line, then went silent.
- **Final on-disk verification** answered the user's real question ("is this all done?") with proof — the user-visible deliverable landed cleanly.

## What should generalize (the skill update)

This loop pattern fires for ANY completed task in a Slack thread (not just `/up`):

- `/finish <goal>`, `/a`, `/fr`, `/auto`, `/af` all land in a Slack thread with a final report
- Any dispatched task (AO, Dark Factory, /green babysit) with a final-state message in a thread
- Any cron babysit that posts a "still working" / "standing by" message after its target PR closed

When the bot enters this loop state, the protocol is:

1. First reply after the report table: one-line next-action menu. End.
2. Every reply after that with no new instruction: one line max.
3. If user's reply is their own prior message re-quoted verbatim: take the "move on" branch immediately, do not narrate the loop, and from that turn forward reply with one word or short phrase until the user sends real content.
4. **If the gateway itself is in a spinner/steering re-fire loop** (you observe your OWN prior messages bouncing back as the "user message") and the user never typed anything new: **stop replying in that thread entirely** after ONE explicit "loop detected, going silent" message. The gateway will burn tokens forever if you keep acking.

## Token cost of the bug

~40 turns × minimum per-turn cost = wasted compute, no user value. Worse: the user can't see anything in the thread because every message is the same ack. Active harm on metered infra.

## Fix in place

- `/up` SKILL.md "Post-completion reply discipline" section updated 2026-07-31 to explicitly call out gateway re-fire as a distinct loop class and instruct the bot to go silent after one explicit notice.

## Open follow-ups (not loop-related, just leftovers)

- Codex native mirror at `~/.agents/skills/parallelize-to-ceiling/SKILL.md` doesn't exist; Claude pointer works via parent-index fallback. User did not pick.
- Linux host sync was reported unreachable from this session. User did not pick.
