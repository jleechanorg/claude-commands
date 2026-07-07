# Environment & Channel Mapping

Verified against `~/.bashrc` and the active launchd-env-wrapper on **2026-07-04 12:43 PDT**. This is the canonical source for variable lookups in the executive-assistant sweep. Re-verify once per quarter or after a Hermes deploy.

## Environment variables (set in `~/.bashrc`, loaded via launchd-env-wrapper)

```bash
# Resolve these once at the top of each run:
bash -lc 'source ~/.bashrc && env | grep -iE "EMAIL|JLEE|HERMES"'
```

| Variable | Value | Notes |
|---|---|---|
| `EMAIL_USER` | `$USER@gmail.com` | Primary Gmail for `gog -a` |
| `BACKUP_EMAIL` | `$USER@gmail.com` | (same) |
| `JLEECHAN_DM_CHANNEL` | `D0AFTLEJGJU` | **Operator DM — the only channel the brief posts to** |
| `JLEECHAN_SLACK_USER_ID` | `U09GH5BR3QU` | Used to filter bot vs human in conversations_history |
| `HERMES_BOT_USER_ID` | `U0AEZC7RX1Q` | hermes-bot identity — exclude from "Jeffrey's most recent message" |
| `HERMES_SLACK_BOT_TOKEN` | `xoxb-9...AjyN` | For curl fallback when Slack MCP is unavailable |
| `GOG_KEYRING_PASSWORD` | `hermes-gog-2026` | OAuth client — do NOT print; just pass through to gog |
| `TIMEZONE` | (not set) | OS default America/Los_Angeles — confirm with `date` |

**Notably ABSENT** (don't waste time probing):
- `OWNER_NAME` — not set; hardcode "Jeffrey"
- `ASSISTANT_EMAIL` — not set; use `EMAIL_USER`
- `PERSONAL_EMAIL` / `PRIMARY_WORK_EMAIL` — not set; only `$USER@gmail.com` exists in this profile

## Slack channel mapping

| Channel | ID | Why monitor |
|---|---|---|
| `#worldai` | `C0AH3RY3DK6` | Primary product PRs + AO babysit threads |
| `#worldai-bugs` | `C0BDEAJH8PK` | Long-running bug investigations (cost consolidation, etc.) |
| `#ai-slack-test` | `C0AKALZ4CKW` | agento respawn-cap escalations; PR-test failures |
| `#all-$USER-ai` | `C09GRLXF9GR` | Direct operator-Hermes line (per `slack-channel-routing-policy`) |
| `#jleechanclaw` | `C0AJ3SD5C79` | Harness / SOUL.md / skill / workflow work |
| `#ralph-status` | `C0AGX2Q0EA3` | Ralph pipeline status (low traffic) |
| `#mcp-mail` | `C0A0AG6EELB` | MCP Agent Mail session-complete updates |
| `#agent-orchestrator` | `C0ALSKLU9KM` | AO worker reports (usually low-traffic) |

| Jeffrey's DM | `D0AFTLEJGJU` | **Brief destination — only place to post the sweep** |

For `@hermes` PR-tag auto-routing per repo, see `hermes-tag-webhook-per-repo-routing` COMMIT — most `jleechanorg/*` repos auto-route to `#worldai`, `#jleechanclaw`, `#agent-orchestrator`, etc., based on repo name.

## Gmail search recipes

```bash
# Starred only
gog gmail search "is:starred" -a $USER@gmail.com --max 20 --json --results-only

# Unread last 24h, human senders only (recommended)
gog gmail search "is:unread newer_than:1d \
  -from:$USER -from:noreply -from:no-reply -from:no_reply \
  -from:donotreply -from:support -from:notifications -from:notification \
  -from:auto-confirm -from:alerts -from:newsletter -from:reports -from:daily -from:bot" \
  -a $USER@gmail.com --max 30 --json --results-only

# Get a specific message body
gog gmail get <messageId> -a $USER@gmail.com --format full
```

**Pitfall:** the `--max` flag is per-thread, not per-message. A thread with `messageCount: 9` (e.g. Cindil delayed regi…) counts as 1.

## Local probe commands

```bash
uptime                                                     # load avg
df -h / | head -3                                          # disk
ps aux | grep -E '(hermes|agy|claude|cmux)' | grep -v grep | wc -l
launchctl print gui/$(id -u) 2>/dev/null | grep -E '(dropped-thread|ao-notifier|auto-push-llm-wiki)' | head -10
```

## Cron cadence observations

The `ai.hermes.schedule.executive-assistant` cron fires on a schedule. Observed run timestamps in `#jleechanclaw`-operator DM (D0AFTLEJGJU) for 2026-07-04:

| Run | PDT | Type |
|---|---|---|
| 1 | 08:01 | Full morning brief |
| 2 | 11:09 | Full brief |
| 3 | 12:01 | Full mid-day brief |
| 4 | 12:43 | **Delta brief** (this run — verified cadence + new tooling) |

Expected cadence on weekdays is typically 07:00 / 12:00 / 18:00 PDT (3x daily). Weekends observed at ~1.5h intervals.

## Pitfalls

- `gog` requires the keyring password (`GOG_KEYRING_PASSWORD`); if the keyring is locked, `gog` will prompt and block — preflight with `security find-generic-password -s hermes-gog-2026 -w` if uncertain.
- Slack MCP is workspace-scoped to the hermes bot's home workspace. For cross-workspace channels (rare; mostly Vendelux/Riday recruiters), fall back to the `SLACK_USER_TOKEN` XOX-P path per `slack-cross-workspace-fallback-xoxp` COMMIT.
- `JLEECHAN_DM_CHANNEL` is `D0AFTLEJGJU` — note the `D` prefix (DM channel). `C0AFTLEJGJU` would be a channel; the README sometimes shows it differently, but the live env value is `D0AFTLEJGJU`.