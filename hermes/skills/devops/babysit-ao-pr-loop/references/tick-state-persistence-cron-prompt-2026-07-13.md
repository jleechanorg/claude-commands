# Tick-state persistence for polling crons (added 2026-07-13, v1.4.0)

## TL;DR

Any cron prompt that gates Slack posting on a tick-number cadence (e.g. "post only on tick #4, #8, #12… every ~20m; all other ticks silent; bail after tick #24") MUST persist the tick counter to a durable file path. Agent-internal counting breaks across session boundaries — every cron tick is a fresh agent session; the prior session's `if tick == 4` branch never executes.

## The bug class

**Symptom:** cron prompt says "post on tick #4, #8, #12, #16, #20, #24, #28, #32" and the cron keeps firing silently because the agent has no way to know what tick it's on. First tick silently bootstraps a counter to 0/1, decides "this isn't tick 4, exit silently", and the thread gets zero updates until the counter happens to land on a multiple of 4 by coincidence (or never).

**Root cause:** each `hermes cron` invocation is a fresh LLM session. The agent has no carryover memory of `tick` from the prior session — the only durable state across session boundaries is the filesystem. A prompt that says "IF this is tick #4" assumes a counter exists somewhere; the prompt must also specify WHERE that counter lives.

**Verified case:** 2026-07-13, `wa-cookies-poll #8353` (cron job `1f0822aae664`, thread C0BDEAJH8PK/1783908854.786439). The cron prompt templated "tick #4, #8, #12, #16, #20, #24, #28, #32 (every ~20m)" with no tick-state file path. The first agent session at 2026-07-12T19:19 PDT had no counter and was forced to bootstrap `/tmp/repro-a1OGXH/.tick_counter=1` ad-hoc. Every prior tick (and there were many — the cron started well before the agent's first read of the prompt) ran without producing the intended heartbeat because nothing recorded tick state.

## The recipe

### Step 1 — cron prompt must name the state path

In the cron prompt's `EVERY tick` section, the FIRST action must read+increment a tick counter file BEFORE deciding what to post:

```bash
STATE=/tmp/<job-name>/.tick_counter
mkdir -p "$(dirname "$STATE")"
TICK=$(($(cat "$STATE" 2>/dev/null || echo 0) + 1))
echo "$TICK" > "$STATE"
echo "tick=$TICK ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$STATE.log"
```

`<job-name>` should be unique per cron so two simultaneous crons don't share a counter. `/tmp/<job-name>/` is a natural choice because the cron already has scratch files in that dir.

### Step 2 — gate posting on the persisted tick

Replace the prompt's "IF this is tick #4, #8, #12…" prose with a deterministic check:

```bash
# Suppress Slack noise on off-cadence ticks; only post on every-4th tick
if (( TICK % 4 == 0 )); then
  echo "posting on tick $TICK"
  mcp__slack__conversations_add_message ...  # or whatever the post primitive is
fi
```

Using `TICK % 4 == 0` instead of enumerating `#4, #8, #12, …` is more robust — the prompt doesn't drift if the cadence changes from "every 20m" to "every 15m" (which would make tick #3, #6, #9 the new posting rhythm).

### Step 3 — terminal-state timeout reads the same file

```bash
if (( TICK > 24 )); then
  echo "polling timed out after $TICK ticks, dropping watch"
  # Post terminal message
  # Self-cancel: hermes cron remove $CRON_JOB_ID
  rm -f "$STATE" "$STATE.log"
fi
```

The timeout MUST also remove the counter file so a re-spawn starts clean at tick 1.

### Step 4 — on terminal self-cancel, clean the file

When the cron self-cancels (whatever triggered the cancel — terminal state, user "stop", etc.), remove the tick counter. Otherwise a re-spawn of the same cron job name would resume at tick #25+ and immediately hit its own timeout.

## Anti-pattern (the one we just fixed)

```text
# Prompt says:
EVERY tick (every 5 min):
1. Run browserclaw cookies decrypt
2. If "Wrote 0 cookies" → IF this is tick #4, #8, #12, #16, #20, #24, #28, #32 (every ~20m)
   post a single line: ":hourglass: still polling for X (tick N)"
   then exit. Else EXIT SILENTLY.

# What the agent does:
- "What tick am I on?" (no idea — fresh session)
- Decides "I'm probably not tick 4, exit silently"
- Thread gets nothing for hours
```

The right shape:

```text
EVERY tick (every 5 min):
1. Tick state:
   STATE=/tmp/repro-a1OGXH/.tick_counter
   mkdir -p "$(dirname "$STATE")"
   TICK=$(($(cat "$STATE" 2>/dev/null || echo 0) + 1))
   echo "$TICK" > "$STATE"

2. Run browserclaw cookies decrypt --db "$HOME/.../Cookies" --output "$STATE.cookies.json" \
     --domain-filter '%worldarchitecture-ai%' --summary

3. If output starts with "Wrote N cookies" (N>0) → COOKIES FOUND. Drive the repro.
   Self-cancel at the end: hermes cron remove $CRON_JOB_ID; rm -f "$STATE" "$STATE.log"

4. If output starts with "Wrote 0 cookies":
   a. If (( TICK % 4 == 0 )) → post one ":hourglass: still polling (tick $TICK)" line.
      Else EXIT SILENTLY.
   b. If (( TICK > 24 )) → post "polling timed out after $TICK ticks, dropping watch",
      self-cancel, and clean state files.
```

## Why not other approaches

- **Pass tick via env var in the cron definition?** Hermes cron doesn't expose per-invocation env injection — every tick would need the same `--env TICK=N` set at creation time, which defeats the purpose.
- **Hold tick in `~/.hermes/state.db`?** Adds DB-write contention for what is supposed to be a low-noise background watcher. The `/tmp/<job>/` path is fine — the state lives as long as the cron is alive and dies with it.
- **Use `last_run_at` timestamps to derive tick?** `date_diff_minutes(last_run_at, now) / 5` rounds badly when the cron slips, and changes the moment the schedule changes. A persisted counter is the source of truth.
- **Just post every tick and let Slack collapse noise?** That's the opposite of the cron contract — the user invoked this cron explicitly to suppress noise. Posting every tick defeats the purpose.

## Provenance

- 2026-07-13 wa-cookies-poll #8353 (cron `1f0822aae664`, thread C0BDEAJH8PK/1783908854.786439). First agent session bootstrapped `.tick_counter=1` ad-hoc; without this recipe, the cron would have produced zero heartbeat updates to the thread until tick #4 (≈15 min later) and the user would have assumed the watcher was dead.
- Cross-references: SKILL.md Anti-patterns §"Tick-number cadence gated without persistent tick state"; related to v1.3.0 post-skeptic green protocol (both are about "what does the watcher know about its own state across ticks").