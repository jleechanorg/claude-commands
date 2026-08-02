# In-House Cron Silent Failure — Verified 2026-07-15 (Bug Hunt Report)

> Companion to `verify-telemetry-alert` SKILL.md. Use this reference when the "alert" comes from an **in-house scheduled script** (not a third-party telemetry alert), and the report claims a clean/healthy result that you suspect is wrong.

## The symptom class

A cron-driven in-house script posts a templated report claiming a clean result. You suspect the result is a false negative because:

- The headline numbers are suspiciously round / zero
- The user has flagged the pattern before (e.g. "0 bugs is odd", "all clean again?")
- The report's tone ("All agents healthy", "clean sweep") doesn't match the script's actual exit path
- A prior session flagged the same script producing the same false-negative shape

**The most-common root cause is NOT in the agent outputs — it's in the script's failure-counter arithmetic.** Scripts that aggregate results from N agents commonly track a single failure counter that only increments on the *output-parse* path (missing file, empty file, invalid JSON). They miss the *preflight* path (host unavailable, subcommand not found, auth missing) which writes a valid-empty JSON file (`[]`) that the parser then counts as "0 bugs, valid output, success."

## Verified recipe — Daily Bug Hunt cron, 2026-07-15

Source script: `$HOME/project_jleechanclaw/jleechanclaw/scripts/bug-hunt-daily.sh`

**Symptom posted to Slack:**
- "PRs reviewed: 28, Bugs found: 0, Agent failures: 0/3"
- "Clean sweep — 28 PRs reviewed, 0 bugs found, 0 agent failures across all 4 repos. All agents healthy."
- Report file: `/tmp/openclaw/bug_reports/bug-hunt-20260715_090002.md` (script's declared path)

**Reality:**
- Per-agent `.err` files all read `ERROR: hermes agent subcommand not found`
- Per-agent `.json` outputs all read `[]`
- Report file actually landed at `/tmp/hermes/bug_reports/bug-hunt-20260715_090002.md` (5.3K), NOT the declared `/tmp/openclaw/bug_reports/` path
- 3 agents (`claude`, `codex`, `minimax`) were skipped at the preflight check (script line 199-204)

**Root cause class:**
- Script has TWO failure gates: (1) **preflight** (line 199-204) detects unavailable host → `log_warn` + writes `[]` → does NOT bump `AGENT_FAILURES`. (2) **output-parse** (line 247-265) detects missing/empty/non-JSON output → bumps `AGENT_FAILURES`.
- The "fail-closed" guard at line 287 (`if [ "$AGENT_FAILURES" -eq "${#AGENTS[@]}" ]`) only fires when ALL agents fail at the parse path. It does NOT fire when ALL agents fail at the preflight path.
- Net effect: 3/3 agents unavailable at preflight → 0/3 reported failures → "clean sweep" → false negative.

**3-step diagnostic recipe (use whenever an in-house script claims clean / zero / success):**

1. **Read the actual on-disk report + per-agent artifacts.** The script's report and per-agent JSON/err files reveal what really happened. Compare the declared `BUG_REPORTS_DIR` against the actual directory where artifacts landed (path drift is its own class of bug — see below).
   ```bash
   # Find the script's declared output directory
   grep -n 'BUG_REPORTS_DIR\|OUTPUT_FILE=\|REPORT_FILE=' scripts/<script>.sh | head -10
   # Find where artifacts actually landed
   find /tmp -name 'bug-hunt-*' -mtime -2
   # Read the per-agent error files
   cat /tmp/hermes/bug_reports/bug-hunt-{claude,codex,minimax}-*.err 2>/dev/null
   ```

2. **Verify the named subcommand/tool actually exists on this install.** When a per-agent err file repeats the same message, that message is usually the smoking gun. `ERROR: hermes agent subcommand not found` is a real failure mode if the script calls `hermes agent <name>` and the local `hermes` CLI lacks that subcommand.
   ```bash
   # Verify the subcommand actually exists
   hermes --help 2>&1 | grep -E '<subcommand>'
   # Or check the actual CLI for the named binary
   which hermes && hermes agent 2>&1 | head -5
   ```

3. **Trace the failure-counter arithmetic in the script source.** Read the script's two failure gates: preflight (early-exit on host availability / subcommand existence / auth) and output-parse (post-run on artifact validity). The fail-closed sentinel must cover BOTH paths, not just one. If only the parse path increments the counter, a fleet-wide preflight failure produces the false negative.
   ```bash
   # Find the failure gates and counter increments
   grep -nE 'AGENT_FAILURES=|AGENT_FAILURES\+\+|fail-closed|ALL_AGENTS_FAILED' scripts/<script>.sh
   # Find the parse-counter increments
   grep -nE 'continue|log_warn|AGENT_FAILURES' scripts/<script>.sh
   ```

## Path drift (secondary signal in this case)

The script's declared `BUG_REPORTS_DIR=/tmp/openclaw/bug_reports/` did not match the actual writes (`/tmp/hermes/bug_reports/`). Two contributing factors:
- The script's `${BUG_REPORTS_DIR}` env var was overridden somewhere in the launchd plist or wrapper
- A different launchd label (`ai.openclaw.schedule.bug-hunt-9am`) was also enabled alongside `ai.hermes.schedule.bug-hunt-9am`, each writing to its own path

Diagnostic:
```bash
launchctl print gui/$(id -u) 2>/dev/null | grep -i 'bug-hunt'
ls /tmp/openclaw/bug_reports/ 2>/dev/null
ls /tmp/hermes/bug_reports/ 2>/dev/null
```

If two cron labels exist for the same job, that's a duplicate-job signal. If `${BUG_REPORTS_DIR}` is overridden somewhere, that's a config-drift signal. Either way, the path the script *thinks* it's writing to is not the path it's actually writing to — which silently breaks anyone who reads the declared path expecting current data.

## Pre-flight to do BEFORE running this recipe

The "alert" here is not a third-party telemetry alert — it's an in-house cron report. Run SOUL.md's `slack-reply-inherit-thread-ts` pre-flight first if you're responding in-thread, because the cron report lives in a specific Slack thread and you want to reply in the correct one (not in the home channel or a stale thread). Path B curl with `SLACK_USER_TOKEN` is the durable fallback when the MCP bot lacks channel membership.

## Durable fix shape

When the diagnosis confirms the preflight-vs-parse asymmetry:

1. In the preflight branch, bump the same failure counter and write a sentinel JSON marker (`{"findings":[],"error":"agent_unavailable"}`) so the parser can distinguish "agent ran and found nothing" from "agent never ran".
2. Change the fail-closed guard to `[ "$AGENT_FAILURES" -ge 1 ]` (or maintain a parallel `PREFLIGHT_FAILURES` counter) so any agent failure produces the "fleet unavailable" footer.
3. Resolve path drift: pick one canonical `BUG_REPORTS_DIR`, align both launchd plists + the script's `${BUG_REPORTS_DIR}` default.
4. Add `tests/test_<script>_preflight.py` covering: (a) preflight-fail increments counter, (b) sentinel JSON parses, (c) "clean sweep" text is gated on `AGENT_FAILURES==0 AND ACTUAL_BUGS==0`.

Filed as `jleechanorg/jleechanclaw#782` (2026-07-15). The fix PR is dispatched via AO worker on clean branch `feat/bug-hunt-preflight-fail-closed` from `origin/main`.

## Files / SHA references

- Script: `$HOME/project_jleechanclaw/jleechanclaw/scripts/bug-hunt-daily.sh` — preflight at lines 199-204, parse gate at lines 247-265, fail-closed at line 287
- Per-agent err files: `/tmp/hermes/bug_reports/bug-hunt-{claude,codex,minimax}-20260715_090002.err`
- Cron labels: `ai.hermes.schedule.bug-hunt-9am` + `ai.openclaw.schedule.bug-hunt-9am` (both enabled)
- GH issue: https://github.com/jleechanorg/jleechanclaw/issues/782

## When this reference applies

- An in-house scheduled script posts a templated "all clean / zero / no failures" report
- The headline numbers are suspiciously round or exactly zero
- The script aggregates multi-agent or multi-source results
- The user has flagged the same pattern before (suggesting the bug has been latent for several cycles)
- Per-agent or per-source error files all repeat the same short string (subcommand missing, host unavailable, auth missing) — that is the diagnostic

## When this reference does NOT apply

- The "alert" is a third-party telemetry alert (use the main SKILL.md body)
- The script's claim is structurally sound (parse path verified, counter arithmetic correct, agents really did run)
- The false-negative cause is upstream (data source stale, sampling window wrong) rather than in the script's failure-counter arithmetic