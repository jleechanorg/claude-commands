# 2026-07-15 — the "fabrication" failure class: looks-clean-but-is-fake signals

This file documents a class of bug-hunt / cron / monitoring failure modes where the **upstream signal looks healthy but the actual content is fabricated**, plus the inbound re-echo pattern from the same day. Both share the property that the agent must look PAST the surface text of the report / message and verify the underlying mechanics. The reference exists because `slack-thread-routing-investigation` covers routing failures (5+ known modes), but the deeper class is "the signal IS the failure" — and that class deserves its own worked example for future agents.

## Class taxonomy

Two distinct shapes, both observed on 2026-07-15:

### Shape A — Slack inbound re-echo (Failure 6)

The agent posts a Slack reply, then the gateway re-delivers the *just-posted* text wrapped in a synthetic sender prefix as a brand-new inbound user message. Replying to the re-echo loops indefinitely. **Mitigation**: byte-compare against the prior outbound post; if identical, end the turn silently. Full write-up at SKILL.md "Failure 6" section.

### Shape B — fail-closed guard miswired to the wrong failure path (bug-hunt 2026-07-15)

A cron / script / monitor has a "fail-closed" guard meant to surface fleet-wide failures, but the guard fires only on a *narrow* failure path while the *most common* failure mode bypasses it entirely. The report then says "clean sweep / 0 failures" while the underlying fleet never ran at all.

**Concrete instance — `bug-hunt-daily.sh` daily report**, jleechanorg/jleechanclaw, run 2026-07-15 09:00 PT.

- **Script path** — `scripts/bug-hunt-daily.sh`. The script launches 3 agents (claude / codex / minimax) via the `hermes` CLI. Each agent's preflight runs `configure_hermes_agent()`, which calls `hermes agent --agent <name> --help` and checks the exit code to set `HERMES_AGENT_AVAILABLE`.
- **The bug** — `hermes` on this box has no `agent` subcommand. `configure_hermes_agent()` therefore sets `HERMES_AGENT_AVAILABLE=0` for every agent. The preflight branch at line 199-204 does `log_warn` + writes `[]` (valid JSON, length 0) + `continue` — but does **NOT** increment `AGENT_FAILURES`.
- **The downstream loop** (line 247-265) parses the per-agent JSON output. A valid `[]` parses cleanly via `jq`, contributing `0` to `ACTUAL_BUGS`. `AGENT_FAILURES` stays at 0 because the output file is valid + non-empty.
- **The fail-closed guard** at line 287 (`if [ "$AGENT_FAILURES" -eq "${#AGENTS[@]}" ]`) only fires when `AGENT_FAILURES == 3` (all output-parse failures). For preflight failures, `AGENT_FAILURES == 0` → the guard is **never reached** → the report says "0/3 agent failures, clean sweep" even though zero agents actually ran.
- **The bug-class invariant** — the fail-closed guard fires on a narrow failure path while the most-common failure mode (preflight-unavailable) bypasses it entirely. The symptom in the user-facing report is "looks clean / 0 problems" — which is the *opposite* of true operational state.

**How the agent caught it (2026-07-15)**:
1. The user posted the Daily Bug Hunt Report to `#all-$USER-ai` with the standard "0 bugs / 0 agent failures / clean sweep" template, flagged as suspicious ("0 bugs is odd").
2. The agent ran `session_search` for prior "0 bugs is odd" hits, which surfaced 2026-05-29 thread where the same flag had been raised. (Memory loaded via 9-store fan-out.)
3. The agent probed the actual log: `tail -120 ~/.hermes/logs/bug-hunt-daily.log` → 4 consecutive daily runs with the canonical `[WARN] hermes agent unavailable` triple.
4. The agent inspected the per-agent output files: `/tmp/hermes/bug_reports/bug-hunt-{claude,codex,minimax}-20260715_090002.json` were all `[]` (3 bytes); the `.err` files all said `ERROR: hermes agent subcommand not found`.
5. Cross-referenced `BUG_REPORTS_DIR` in the script (`/tmp/openclaw/bug_reports/`) vs the actual write location (`/tmp/hermes/bug_reports/`) → **path drift** (Shape C below) made the diagnostic harder because the script-defined report dir was empty.
6. Posted the diagnosis to the thread with a 1-line fix recipe + a followup question to the user about whether to dispatch an AO worker.

**Recipe to detect Shape B in any monitoring script**:

```bash
# 1. Find all fail-closed guards in the script
grep -nE 'AGENT_FAILURES|fail.closed|ALL_AGENTS_FAILED|exit.*[1-9]|return.*[1-9]' scripts/<name>.sh

# 2. For each guard, identify which FAILURE PATH bumps the counter
#    vs which paths only log_warn + continue

# 3. For each log_warn-only path, ask: is this the most-common failure mode?
#    If yes, the guard is wired wrong.

# 4. Run the script with the upstream dependency BROKEN (kill the daemon,
#    remove the CLI, set the env var to garbage) and see if the report
#    shows the failure or hides it.
```

**Recipe to fix Shape B** (1-line counter bump + sentinel JSON + 1-line guard change):

```bash
# In the preflight branch, replace:
log_warn "hermes agent unavailable, writing empty findings for $AGENT"
write_empty_findings "$OUTPUT_FILE"
continue
# with:
log_warn "hermes agent unavailable, writing sentinel findings for $AGENT"
printf '{"findings":[],"error":"agent_unavailable"}\n' > "$OUTPUT_FILE"
AGENT_FAILURES=$((AGENT_FAILURES + 1))
continue

# And widen the fail-closed guard from "all 3 failed" to "at least 1 failed":
if [ "$AGENT_FAILURES" -ge 1 ]; then
    log_warn "Some bug hunt agents failed — bug count may be incomplete"
    ALL_AGENTS_FAILED=1
fi
```

**Test recipe** (RED-GREEN-REFACTOR):
- RED — write `tests/test_bug_hunt_preflight.py` that (a) sets `HERMES_AGENT_AVAILABLE=0` for all agents, (b) runs the script end-to-end, (c) asserts the report contains "agent_unavailable" or "fleet unavailable" — current script fails this (report says "clean sweep").
- GREEN — apply the 1-line fix above + the guard-widening change.
- REFACTOR — clean up the test fixtures; consider whether `AGENT_FAILURES` and `ACTUAL_BUGS` should be collapsed into a single `RUN_STATUS` enum (`OK` / `PARTIAL` / `FAILED` / `BYPASSED`).

### Shape C — script-default config drift vs deployed config (the bug-hunt BUG_REPORTS_DIR case)

The same incident also surfaced a second-order config drift:

- `scripts/bug-hunt-daily.sh:9-10` defines `BUG_REPORTS_DIR=/tmp/openclaw/bug_reports`
- But the actual file writes went to `/tmp/hermes/bug_reports/bug-hunt-20260715_090002.md` (5.3K)
- `launchctl print gui/$(id -u) | grep -i bug-hunt` showed **two** enabled labels — `ai.hermes.schedule.bug-hunt-9am` (from `~/.hermes/launchd/`) AND `ai.openclaw.schedule.bug-hunt-9am` (from `~/.openclaw/launchd/`), both running on the same Mon-Fri 09:00 trigger

Result: each weekday 09:00 tick produces TWO report files in TWO different directories — one from the hermes-side plist (writing to `/tmp/hermes/bug_reports/`) and one from the openclaw-side plist (writing to `/tmp/openclaw/bug_reports/`). The diagnostic was harder because the user looked at `/tmp/openclaw/bug_reports/` first (matches the script's `BUG_REPORTS_DIR` default) and found nothing — the real files were in the other tree.

**Class invariant** — when a script defines a default `*_DIR` config value AND is also launched by a plist that injects an override via `EnvironmentVariables` / `launchd-wrapper.sh`, the two paths can silently disagree if either side was updated without the other. **The fail-closed guard for this class is `find / -name '<script's expected output file pattern>' -mtime -2 2>/dev/null`** — if the canonical path is empty but a different path has fresh files, config drift is the cause.

This shape is already covered in `hermes-deploy-pipeline` SKILL.md "Anti-Patterns" section; cross-link added in the new pitfall there.

## Why this reference lives under `slack-thread-routing-investigation/references/`

The umbrella skill covers "diagnose why a Slack reply misbehaved" — 5 known failure modes + 5 sub-classes, all about outbound routing. Shape A (Failure 6 — inbound re-echo) is a direct extension of that taxonomy and lives in the SKILL.md body. Shape B and Shape C are NOT Slack routing failures — they are *content fabrication* failures where the Slack post (or daily report) looks healthy but the underlying mechanics are broken. They live here as a reference rather than a new SKILL.md section because:

1. The user-facing signal is the SAME — a Slack post that says "all good / clean sweep / 0 problems" when the truth is the opposite.
2. The diagnostic instinct is the SAME — read past the surface text, probe the actual mechanics, compare against prior instances via `session_search`.
3. Future agents searching for "0 bugs is odd" or "looks clean but is fake" should land here via `references/` cross-link from the umbrella's "Patches / known followups" section.

## Cross-references

- SKILL.md "Failure 6" section — inbound re-echo class-level write-up.
- SOUL.md `## COMMIT: never-hallucinate-no-new-content` — the inbound version of "do not fabricate framing for empty messages."
- SOUL.md `## COMMIT: proof-before-claim` — the outbound version of "do not claim a Slack post landed correctly without verifying with `conversations_replies`."
- `hermes-deploy-pipeline` SKILL.md → Anti-Patterns → script-default vs plist-installed path drift (new pitfall added in this session).
- `systematic-debugging` SKILL.md → Phase 1 (Reproduce) — the "run the upstream dependency as broken, see if the report surfaces the breakage" recipe is a Phase 1 diagnostic for any monitoring-signal class.
- MEMORY.md line `(5)` — inbound re-echo heuristic as a personal note (added 2026-07-15, currently 88% full).