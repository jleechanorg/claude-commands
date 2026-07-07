# jleechanorg PR Automation Topology

Live map of all systems that can post automated comments to PRs in `$GITHUB_REPOSITORY` and related repos.

## Current Disabled State (as of 2026-05-29)

| System | Status | Action Taken |
|--------|--------|--------------|
| Skeptic Cron (GHA) | **DISABLED** | `gh workflow disable 253141151` |
| PR Monitor (local) | **DISABLED** | Process killed, plist renamed to `.disabled` |
| Agent PR Fix Trigger | **INACTIVE** | Never runs (idle since 2026-03-09) |

Active systems (read-only / safe):
- `ai.hermes.schedule.pr-monitor-worldai` — 7-green status checks only
- `ai.hermes.schedule.pr-monitor-worldai` — same 7-green script, duplicate agent

## Local Processes (macOS launchd + crontab)

### PR Monitor (Python: `jleechanorg_pr_automation`) — DISABLED
- **Label**: `ai.worldarchitect.pr-automation.pr-monitor`
- **Binary**: `~/Library/Python/3.13/bin/jleechanorg-pr-monitor --max-prs 10`
- **CWD**: `~/projects/your-project.com/automation`
- **Logs**: `~/Library/Logs/${PROJECT_NAME:-your-project}-automation/pr-monitor.err.log` (detailed) and `pr-monitor.out.log`
- **Posts as**: `jleechan2015` (uses PAT — appears as the user, NOT a bot)
- **Comment format**: `@codex @coderabbitai @cursor @copilot [AI automation] Codex will implement...`
- **Python package**: `jleechanorg-pr-automation` (v0.2.128 as of 2026-05-29)
- **Source**: `automation/jleechanorg_pr_automation/jleechanorg_pr_monitor.py` in your-project.com repo
- **Key method**: `_build_codex_comment_body_simple()` → posts the `[AI automation]` template
- **Plist path**: `~/Library/LaunchAgents/ai.worldarchitect.pr-automation.pr-monitor.plist.disabled`

### Other pr-automation launchd agents (same package)
- `ai.worldarchitect.pr-automation.fixpr` — FixPR workflow (not running)
- `ai.worldarchitect.pr-automation.fix-comment` — Fix-comment workflow (not loaded)
- `ai.worldarchitect.pr-automation.comment-validation` — Comment validation (not loaded)
- `ai.worldarchitect.pr-automation.codex-api` — Codex API calls (not loaded, disabled months ago)
- **All plist files**: `~/Library/LaunchAgents/ai.worldarchitect.pr-automation.*.plist`

### AO 7-Green Monitor (Bash) — ACTIVE, read-only
- **Label**: `ai.hermes.schedule.pr-monitor-worldai`
- **Script**: `~/.hermes/scripts/ao7green-pr-monitor.launchd.sh` → `ao7green-pr-monitor.sh`
- **Interval**: 3600s (1 hour)
- **Read-only**: Checks 7-green criteria, does NOT post PR comments
- **Logs**: `~/.hermes/logs/pr-monitor-worldai.log`

### AO 7-Green Monitor (Hermes variant) — ACTIVE, read-only
- **Label**: `ai.hermes.schedule.pr-monitor-worldai`
- **Script**: `~/.hermes/scripts/ao7green-pr-monitor.launchd.sh`
- **Same function as the Hermes variant above** (duplicate agent)

## GitHub Actions Workflows (your-project.com)

| Workflow | ID | State | Posts Comments? | Schedule |
|----------|----|-------|-----------------|----------|
| Skeptic Cron | 253141151 | **DISABLED** | YES — `SKEPTIC_CRON_TRIGGER` | `*/30 * * * *` |
| Skeptic Self-Verify | 265950193 | active | YES — verdicts | workflow_dispatch |
| Post Skeptic Verdict (one-shot) | 266061222 | active | YES — verdicts | workflow_dispatch |
| Green Gate | 259332740 | active | NO — checks only | pull_request |
| Agent PR Fix Trigger | 241865195 | active (idle) | YES (when triggered) | workflow_dispatch (last ran 2026-03-09) |
| CodeRabbit ping on push | 244474201 | active | NO — pings webhook only | push |
| Codex Skill Sync Check | 268112193 | active | NO — CI only | pull_request |

### Skeptic Cron Architecture

The critical chain:

```
skeptic-cron.yml (every 30 min)
  └── skeptic-cron-reusable.yml@main (agent-orchestrator repo)
       ├── Step 3: Posts SKEPTIC_CRON_TRIGGER comment on each open PR
       └── Step 4: Check 7-green and merge
```

**Key behavior**: The reusable workflow posts a trigger HTML comment with:
- `SKEPTIC_CRON_TRIGGER` (visible text)
- `<!-- skeptic-request-id-cron-{RUN_ID}-{ATTEMPT}-{PR_NUM}-{SHA} -->` (hidden marker)
- `<!-- skeptic-cron-trigger-{SHA} -->` (suppress dedup marker)

**FAIL/SKIPPED suppression**: If a FAIL or SKIPPED verdict exists within 4 hours for the same SHA, the cron skips posting a new trigger (4-hour `FAIL_SUPPRESS_WINDOW_SECS=14400`).

**STOPPING the trigger comments**: Either disable the workflow (`gh workflow disable 253141151`) or modify the reusable workflow to skip the comment-posting step.

## External Bots

| Bot | GitHub Login | Trigger | Control |
|-----|-------------|---------|---------|
| CodeRabbit | `coderabbitai[bot]` | Push event, `@coderabbitai` mention | GitHub App settings |
| Codex Connected App | `chatgpt-codex-connector[bot]` | `SKEPTIC_CRON_TRIGGER`, `[AI automation]`, push | GitHub App settings |
| Copilot | `copilot` | Push event (review) | GitHub App settings |
| Cursor | `cursor[bot]` | Various | GitHub App settings |

## Comment Deduplication Chain

When multiple systems fire on the same PR:
1. `SKEPTIC_CRON_TRIGGER` posted (visible + HTML markers) ← every 30 min by skeptic-cron
2. CodeRabbit responds to `@coderabbitai all good?` ← triggered by skeptic-cron
3. `[AI automation]` posted by pr-monitor (via PAT) ← triggered by push event or schedule
4. Codex Connected App responds to `[AI automation]` ← triggered by comment
5. CodeRabbit responds to Codex's summary ← triggered by comment
6. Go to 1 (30 min later)

**To fully stop the cascade**, you must disable ALL three trigger sources:
1. Skeptic Cron (GHA workflow) — ✅ DISABLED 2026-05-29
2. PR Monitor (local launchd) — ✅ DISABLED 2026-05-29
3. External bots (CodeRabbit, Codex) — STILL ACTIVE via GitHub App settings