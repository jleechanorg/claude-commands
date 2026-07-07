---
name: cmux-surface-report-4h
version: 1.2.0
description: "Every-4h cmux terminal surface inventory + classification. Lists every selected cmux workspace/surface, reads each pane briefly, classifies as Healthy/Risky/Blocked, and posts a per-surface digest (with pinned-first priority, full PR hyperlinks, and smarter 'working on' extraction) to Slack home channel. Runs via launchd plist + LLM-cron job (deterministic-scheduler sibling). Script is mature; v1.2 (2026-06-24) adds 4 improvements per Jeffrey's request."
tags: [cmux, monitoring, launchd, cron, periodic, slack]
category: monitoring
triggers:
  - cmux surface report
  - cmux 4h report
  - cmux inventory
  - cmux health digest
  - 4h cmux check
  - what is cmux doing
  - cmux status
related_skills:
  - cmux
  - cmux-terminal-review
  - launchd-job-authoring
  - cron
  - slack-messaging
  - skillify
---

# cmux-surface-report-4h

**Every-4h cmux terminal inventory + Slack digest.** This skill composes the production-grade `cmux-surface-report-4h.sh` (already live in `~/.hermes/scripts/`, scheduled via launchd plist at `~/Library/LaunchAgents/com.$USER.cmux-surface-report-4h.plist` AND an LLM-cron twin in `~/.hermes/cron/jobs.json`) with the contracts: SKILL.md, tests, RESOLVER trigger entry, and the deploy-pipeline sync.

## v1.2 improvements (2026-06-24, per Jeffrey's request)

Four quality-of-life improvements landed in one turn:

1. **Pinned workspaces float to the top.** A new file
   `~/.config/cmux/pinned-workspaces.txt` lets Jeffrey pin specific
   workspaces by exact ref (`workspace:14`) or by case-insensitive
   name fragment (`agento`, `latency`). Pinned surfaces always appear
   first in the report (priority 1, regardless of class), marked with
   📌. Empty lines and `#` comments are allowed.

2. **Full PR hyperlinks** in the `next:` line. Bare `#N` references
   are now emitted as `[#N](https://github.com/jleechanorg/<repo>/pull/N)`
   markdown hyperlinks per `.cursor/rules/pr-hyperlink.mdc`. The repo
   is auto-detected from the screen text. Falls back to the
   `$CMUX_REPORT_GH_REPO` env var (default: `$GITHUB_REPOSITORY`)
   when no repo is mentioned. Three real bugs were caught and fixed
   during this pass: the doubled-owner pattern
   `github.com/jleechanorg/jleechanorg/<repo>/pull/N` (Slack renders
   BOTH the visible hyperlink text AND the raw URL), the bare-`#N`
   branch falsely linking to the default repo when the screen
   references an unrelated repo, and a template bug that doubled
   the `jleechanorg/` prefix when `default_repo` already contained it.

3. **Smarter "working on" extractor.** Instead of the first matching
   line, the extractor now scores each line by (PR-mention = +3,
   activity-keyword = +2, later-in-screen = fractional) and picks the
   best. This means a deep log line like `※ recap: Shipped P4
   prompt-substitution audit to dark-factory via PR #99 (merged at
   d68d52b)…` wins over a header line that happens to say "Running".

4. **Skillify pass.** Tests, RESOLVER entry, and SKILL.md contract
   refreshed to cover the new behavior. Test file grew from 31 to 51
   passing cases.

## Why this skill exists

Three drift patterns were observed before this skillification (2026-06-20 to 2026-06-22):

1. **Parser regression producing 72 bogus "blocked" entries** — the 2026-06-20 08:29 tick double-counted surfaces because awk couldn't parse Unicode box-drawing chars. Replaced with Python parser + sanity cap (TOTAL > 100 aborts post).
2. **launchd job had no Slack token** — the wrapper script (`-wrapper.sh`) was added to source `launchd-env-wrapper.sh` so `HERMES_SLACK_BOT_TOKEN` reaches the script. Without the wrapper, every tick silently no-ops.
3. **Two duplicate scheduler entries** (one launchd, one LLM-cron) — both posting to the same channel. Verified harmless because both call the same script; documented for audit clarity.

## Contract

**When this skill fires, ONE end-state is provably true:**

| End-state | Proof artifact |
|---|---|
| **Slack post landed in `#ai-general`** | One message per tick: `*cmux Surface Report (4h)* :emoji: {healthy\|risky\|blocked}\nWorkspaces: N surfaces checked \| Healthy: H \| Risky: R \| Blocked: B\n_Tick: ISO8601 \| Socket: <name>_` |
| **Tick skipped cleanly** | Log line `No live cmux socket — skipping this tick.` at `~/.hermes/logs/cmux-surface-report/YYYY-MM-DDTHH.log` |
| **Tick aborted due to parser regression** | Log line `TOTAL=N exceeds sanity cap (100) — aborting to avoid bogus post.` (exits 1, no Slack post) |

**NOT acceptable end-states:**

- ❌ Tick runs but posts to wrong channel (the SOUL.md `slack-channel-routing-policy` COMMIT pins `#ai-general` (`C0AJQ5M0A0Y`) for all periodic traffic — never `#all-$USER-ai`).
- ❌ Tick runs with `HERMES_SLACK_BOT_TOKEN` unset and silently exits (the wrapper enforces this — if launchd-env-wrapper.sh is missing, the wrapper FATALs, never silently no-ops).
- ❌ Tick runs with > 100 surfaces (capped and aborted, NOT posted).

## Phases (every 4h cadence)

### Phase 0 — Wrapper sources launchd env

The wrapper (`cmux-surface-report-4h-wrapper.sh`) is the only entry point. It:

1. Sets `LABEL=com.$USER.cmux-surface-report-4h` and `LOG_TAG=cmux-surface-report-4h`.
2. Sources `~/.hermes/scripts/launchd-env-wrapper.sh` (which extracts `HERMES_SLACK_BOT_TOKEN`, `HOME`, `PATH` from `~/.bashrc`).
3. Execs the actual `cmux-surface-report-4h.sh` via `bash -c "source ...; exec ..."` (the wrapper exec's its arg).

**Why a wrapper:** launchd does NOT source `~/.bashrc`. Without the wrapper, the report script has no Slack token and silently exits 0 with `No Slack token available — skipping post.` in the log.

### Phase 1 — Socket resolution

The script reads `/tmp/cmux-last-socket-path` first (cmux's own pointer file), then falls back to `ls -1 /tmp/cmux*.sock /private/tmp/cmux*.sock`. If neither yields a live socket, the tick exits 0 cleanly (no Slack post).

### Phase 2 — Tree parsing

Tries `cmux tree --window window:1` first (works on dev build `cmux DEV may-18.app`), then falls back to `cmux tree --all`. Both wrapped in `timeout 8`. Parses the tree with Python (NOT awk — Unicode box-drawing chars break awk). Emits a list of `(workspace, surface)` pairs where surface is `[selected]`.

### Phase 3 — Per-surface classification (loop)

For each pair, calls `cmux read-screen --workspace workspace:N --surface surface:N --lines 25`, filters cmux's own `Error:` lines, and classifies into one of three buckets:

| Bucket | Regex on filtered screen | Example signal |
|---|---|---|
| **BLOCKED** | `Traceback\|panic:\|FATAL EXCEPTION\|segmentation fault` | Python traceback visible |
| **RISKY** | `confirm?\|Do you want to\|approve?\|permission to` | Awaiting user approval |
| **HEALTHY** | `Running\|processing\|generating\|building\|claude--\|Working on\|thinking` | Active work |
| **HEALTHY** (idle) | (none of above) | Quiet/idle terminal |

Each classification logs to the per-tick log file. Sanity cap: TOTAL > 100 aborts the post (catches parser regressions before alarming the channel).

### Phase 4 — Slack post (jq + curl)

Builds a one-line `*cmux Surface Report (4h)* :emoji: {label}` digest with up to 3 blocked + 3 risky details, posted to `${HERMES_CMUX_4H_CHANNEL:-C0AJQ5M0A0Y}` via direct `chat.postMessage`. `unfurl_links:false` to keep the message tight.

## Files

| Path | Purpose |
|---|---|
| `~/.hermes/scripts/cmux-surface-report-4h.sh` | Main script (8288 bytes, 220 lines) |
| `~/.hermes/scripts/cmux-surface-report-4h-wrapper.sh` | launchd wrapper (1280 bytes, sources launchd-env-wrapper.sh) |
| `~/.hermes/launchd/com.$USER.cmux-surface-report-4h.plist.template` | launchd plist template (with `@HOME@` placeholders) |
| `~/Library/LaunchAgents/com.$USER.cmux-surface-report-4h.plist` | Rendered plist (substituted `$HOME`) |
| `~/.hermes/cron/jobs.json` | LLM-cron entry `hermes:cmux-surface-report-4h` (id `086ee863b35a`) |
| `~/.hermes_prod/cron/jobs.json` | Prod twin (id `086ee863b35a` — same) |
| `~/.hermes_prod/skills/cmux-surface-report-4h/SKILL.md` | This file (prod mirror) |
| `~/.hermes_prod/skills/cmux-surface-report-4h/tests/test-classify.sh` | Unit tests for the classifier regexes + sanity cap |
| `~/.hermes/skills/RESOLVER.md` | Trigger entry: `cmux surface report`, `cmux 4h report`, etc. |
| `~/.hermes/logs/cmux-surface-report/YYYY-MM-DDTHH.log` | Per-tick logs (one file per hour) |
| `~/Library/Logs/com.$USER.cmux-surface-report-4h.log` | launchd-level log (wrapper output) |

## Loader / auto-fire contract

This skill is registered in `~/.hermes_prod/skills/RESOLVER.md` and `~/.hermes/skills/RESOLVER.md` with trigger phrases: `cmux surface report`, `cmux 4h report`, `cmux inventory`, `cmux health digest`, `4h cmux check`, `what is cmux doing`, `cmux status`. The skill fires when a user asks about cmux state from the LLM session; the launchd plist fires independently of the LLM session on its 4h cadence.

## Deploy sync awareness

This skill is part of the **hermes-deploy-pipeline** deploy set. Stage 4.5 of `scripts/deploy.sh` only syncs `POLICY_FILES=(CLAUDE.md SOUL.md TOOLS.md HEARTBEAT.md)`. So:

1. The script lives in `~/.hermes/scripts/` (staging repo = git-tracked). Commit + push to origin main.
2. The plist template lives in `~/.hermes/launchd/` (staging repo = git-tracked). Commit + push.
3. The rendered plist lives in `~/Library/LaunchAgents/` (NOT git-tracked). Re-render via `sed` from the template after deploy.
4. The cron entry lives in `~/.hermes/cron/jobs.json` (staging repo). After deploy, mirror to `~/.hermes_prod/cron/jobs.json` (gateway live state).

**The cmux entry exists in BOTH staging and prod cron** (job id `086ee863b35a`), so deploy.sh Stage 4.5 is sufficient — no custom rsync needed for the cron entry.

## Related skills — load order when this fires

1. `cmux` (always — the underlying terminal multiplexer that this skill inventories)
2. `launchd-job-authoring` (only when adjusting the plist template)
3. `cron` (only when adjusting the LLM-cron twin)
4. `slack-messaging` (only when adjusting the post format)

## Worked example — 2026-06-22 healthy tick

```
*cmux Surface Report (4h)* :white_check_mark: healthy
Workspaces: 4 surfaces checked | Healthy: 4 | Risky: 0 | Blocked: 0
_Tick: 2026-06-22T20:07:14Z | Socket: cmux-9b80e9da.sock_
```

(Live output from the 2026-06-22 20:07 PT tick; verified in `#ai-general` channel.)