# Sweep Monitoring Channels

Authoritative channel ID table for the executive-assistant sweep. Verified 2026-07-10; pitfall section added 2026-07-13.

## Action channels (where operator-direct asks live)

| Channel | ID | Notes |
|---|---|---|
| `#all-$USER-ai` | `C09GRLXF9GR` | Operator direct line; never skip |
| `#worldai` | `C0AH3RY3DK6` | your-project.com product work |
| `#worldai-bugs` | `C0BDEAJH8PK` | bug repros, `/repro` results |
| `#jleechanclaw` | `C0AJ3SD5C79` | harness / skill / SOUL.md work |
| `#agent-orchestrator` | `C0ALSKLU9KM` | AO PR drives |
| `#life` | `C0AMM2B4319` | personal reminders + cron self-narration |
| DM `hermes` | `D0AFTLEJGJU` | prior brief, dedup target (residual ref; live DM is `D0A418NEHHC`) |

## Infra alert channels (system + runner fleet)

| Channel | ID | What lands here | Surface as |
|---|---|---|---|
| `#worldai-alerts` | `C0BCVG4F560` | GCP daily cron FAILs (Level Up / Dice Audit), GCP cost spikes | `:rotating_light:` if FAIL within last 12h |
| `#mcp-mail` | `C0A0AG6EELB` | **ezgha fleet / runner / canary CRITICAL+WARNING**: INV-1 violations, missing runners, queued-not-draining, canary SLO breaches | `:rotating_light:` immediately |
| `#