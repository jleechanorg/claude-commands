---
name: durable-bug-hunt-harness
description: Drive a forked bug-hunt PR (scripts/bug-hunt-daily.sh) to durable green by chunking hermes -z workers under one global deadline, retrying failed chunks on a proven surviving model, repairing truncated JSON, and verifying with real-agent dry runs before requesting review.
---

# durable-bug-hunt-harness

When the daily bug hunt cron in `jleechanorg/jleechanclaw` fires, the underlying `scripts/bug-hunt-daily.sh` script dispatches hermes `-z` workers (one per agent lane) over the merged-PRs list. The original version ran each lane sequentially, ate 30 minutes per lane, and silently dropped any chunk that timed out, ran out of tokens, or emitted truncated JSON — producing false-clean reports.

This recipe drives the PR that fixes that harness end-to-end on the `fix/durable-bug-hunt-harness` branch.

## Trigger

- Cron fires (`ai.hermes.schedule.bug-hunt-9am`), every chunk JSON is 0 bytes, and the report says "All bug hunt chunks failed — 0 bugs recorded".
- LLM rewrites PR body or labels mention "durable bug hunt harness", "chunk", "retry on proven", or "truncated JSON repair".
- AO session named `bughunt-dedupe` (or any AO worker) starts a fix branch for `scripts/bug-hunt-daily.sh`.

## Workflow

1. **Confirm the failure mode**
   - `ls /tmp/bughunt-*` — inspect the most recent run dir; look for 0-byte JSON outputs and oversized stderr.
   - Read the launchd plist `~/Library/LaunchAgents/ai.hermes.schedule.bug-hunt-9am.plist` and the script header for the active lane config.
   - Capture the symptom (timeout? truncated JSON? `|| true` swallowed exit code?) before designing a fix.

2. **Branch from `origin/main`**
   - `git worktree add -b fix/durable-bug-hunt-harness <wt> origin/main`
   - Do **not** stack unrelated commits. Keep the diff scoped to `scripts/bug-hunt-daily.sh` + `tests/test_bug_hunt_daily_script.py`.

3. **Add TDD coverage for each gap you close**
   Required tests (one per fix):
   - **chunk-size guard**: `BUG_HUNT_CHUNK_SIZE=10` honored even when 32 PRs are discovered; no monolithic 32-PR prompt.
   - **per-chunk exit status**: `wait` returns the PID exit code; `chunks/<id>.exit` files written.
   - **summary fix**: `PRs Discovered:` and `PRs Reviewed:` are two separate lines.
   - **fail-closed RC**: when ALL chunks fail (prose / 0-byte), script exits 2, not 0.
   - **retry on proven surviving model**: gemini completes, claude/minimax killed at deadline, retry runs on gemini, all PRs reviewed.
   - **truncated JSON repair**: chunk JSON ends mid-string; aggregation calls `repair_truncated_json` and salvages complete array elements.
   - **proven model requires valid JSON**: a non-empty truncated JSON file does NOT steal the proven slot from a healthy sibling chunk.

4. **Patch the script**
   - Default `BUG_HUNT_CHUNK_SIZE=10` (4 chunks × ~10 PRs each).
   - Capture hermes exit code per chunk: `_hermes_rc=0; hermes -z ... || _hermes_rc=$?; echo $_hermes_rc > EXIT_FILE`.
   - Drop `|| true` on the chunk-spawn wrapper so failures are visible.
   - Add `BUG_HUNT_GLOBAL_DEADLINE_SECONDS` (default 600) — one watchdog terminates **all** chunks at the wire instead of three sequential 10-min per-lane watchdogs.
   - Implement `repair_truncated_json()` as a python3 one-shot:
     - Try `json.loads`; on `JSONDecodeError` import `json_repair` if available, else walk the buffer back to the last `}` and reparse.
     - Return salvaged array on stdout, exit 0; exit 1 if nothing usable.
   - Proven-model detection iterates chunks and picks the first `jq empty <OUTPUT_FILE>`-valid one.
   - Retry loop re-runs failed chunks (`! [ -s "$OUTPUT_FILE" ] || ! jq empty`) on `PROVEN_MODEL` under `BUG_HUNT_RETRY_DEADLINE_SECONDS` (default = GLOBAL_DEADLINE_SECONDS).
   - Add `BUG_HUNT_DISABLE_RETRY=1` for deterministic tests/debugging.
   - On `jq empty` failure during aggregation, call `repair_truncated_json` first; on success update `OUTPUT_FILE` in place; on final failure count as `AGENT_FAILURE`.
   - Summary block emits both counts on separate lines; exit 2 if `ALL_AGENTS_FAILED=1`.

5. **Run the unit suite until green**
   - `python -m pytest tests/test_bug_hunt_daily_script.py -q`
   - `bash -n scripts/bug-hunt-daily.sh`
   - Expect ≥30 tests pass.

6. **Independent verification — real-agent dry run**
   Before claiming the fix, run a safe dry run under your **worktree**:
   ```bash
   WT=$HOME/.worktrees/jleechanclaw/jc-2064
   DRYRUN_DIR=$(mktemp -d /tmp/bughunt-dry-XXXXXX)
   BUG_REPORTS_DIR="$DRYRUN_DIR" \
   BUG_HUNT_DISABLE_PUBLISH=1 \
   BUG_HUNT_DISABLE_FIXES=1 \
   GLOBAL_DEADLINE_SECONDS=600 \
   BUG_HUNT_RETRY_DEADLINE_SECONDS=600 \
   bash "$WT/scripts/bug-hunt-daily.sh" >"$DRYRUN_DIR/stdout.log" 2>"$DRYRUN_DIR/stderr.log"
   ```
   - **Acceptance**: `PRs Discovered: 32, PRs Reviewed: 32` (or higher). Anything < 32 means a remaining gap.
   - 600+600s exceeds the bash tool's 10-min cap; run via `nohup bash -c '…' > /dev/null 2>&1 &` or background-task API.

7. **Commit, push, request re-review**
   ```bash
   git add scripts/bug-hunt-daily.sh tests/test_bug_hunt_daily_script.py
   git commit -m "fix(bug-hunt): <scope> [claude-code/claude-sonnet-4-6]"
   git push origin fix/durable-bug-hunt-harness
   ```
   Then `gh pr comment 792 --body "Re-review request — …"` with a one-paragraph summary of the surface change.

8. **Skillify on merge**
   After merge to `origin/main`, run `/sk` (skillify) against the diff. Capture any new gaps the harness exposed (e.g. a model variant emitting markdown table rows instead of JSON) into this skill.

## Pitfalls

- **Don't `|| true` on hermes**: it silently produces 0-byte JSON with no diagnostic. Capture exit code and write to `.exit` file.
- **Don't `exit 0` on all-failed**: the script must be fail-closed (exit 2) when every chunk failed; otherwise cron has no signal to alert.
- **Don't trust `-s` for proven-model detection**: a 32 KB truncated JSON file is `-s` true but `jq empty` false. Always use `jq empty`.
- **Don't loop per-chunk watchdogs**: 3 lanes × 10 min = 30 min worst case. One global deadline is bounded and predictable.
- **Don't ignore truncated JSON**: claude and minimax regularly emit valid-looking-but-cut-off output. Repair must happen **before** failure counting.
- **Don't set `GLOBAL_DEADLINE_SECONDS=200` for verification**: it's under the per-chunk latency floor (gemini takes ~6 minutes for 10 PRs). Use 600+.
- **Don't paste Slack tokens into PR comments**: preflight with `python3 ~/.hermes/lib/outbound_secret_gate.py check`.

## Files

- `scripts/bug-hunt-daily.sh` — the harness under test.
- `tests/test_bug_hunt_daily_script.py` — pytest unit tests using a stub `gh` and a stub `hermes` on PATH.
- `~/Library/LaunchAgents/ai.hermes.schedule.bug-hunt-9am.plist` — daily cron entry that invokes the script.
- `jleechanorg/jleechanclaw` PR — `https://github.com/jleechanorg/jleechanclaw/pull/792` — durable bug-hunt harness PR.
- `~/.hermes/scripts/dropped-thread-followup.sh` — sister cron that benefits from same fail-closed discipline.

## Verification

```bash
gh pr view 792 --repo jleechanorg/jleechanclaw --json state,reviewDecision,mergeable,headRefOid,statusCheckRollup
python -m pytest $HOME/.worktrees/jleechanclaw/jc-2064/tests/test_bug_hunt_daily_script.py -q
```

Expect: state=OPEN, reviewDecision=APPROVED, mergeable=MERGEABLE, ≥30 tests passed.
