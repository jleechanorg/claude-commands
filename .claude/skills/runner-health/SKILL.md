---
name: runner-health
description: Operational health snapshot for the jleechanorg self-hosted runner fleet. Use when user says "check runners", "are runners up", "is jeff-ubuntu down", "diagnose runner health", or before/after runner operations. Produces a structured Markdown report at /tmp/runner-health-<ts>.md with multi-method checks (GitHub API + local Docker + Lima VM + jeff-ubuntu ssh + optional hermes-pc cross-check). Works when jeff-ubuntu is unreachable (key insight: busy=true on runners is itself proof of liveness even when ssh fails).
type: skill
scope: repo
owner: $USER
version: 1.0.0
triggers:
  - "check runners"
  - "are runners up"
  - "is jeff-ubuntu down"
  - "diagnose runner health"
  - "runner status snapshot"
  - "fleet health"
  - "verify ubuntu runners"
allowed-tools:
  - Bash
  - Read
  - mcp__slack__*
  - Skill (memory-search, history-search)
context:
  - "GitHub /actions/runners org endpoint shows status (online/offline) and busy (true/false) only — no last_active field. busy=true IS the live-heartbeat proof: a runner can only be busy if it actively polled GitHub and accepted a job."
  - "The fleet has 16 Linux runners (org-runner-1..16) on jeff-ubuntu + 6 mac runners (org-runner-mac-1..6) on the local Mac. AO per-repo auxiliaries (worldai_claw, mctrl_test, $ORG, ai_universe_living_blog) live on jeff-ubuntu and suffer RUNNER_TOKEN expiry (PR #702 fixes root cause)."
  - "When user is on a different wifi than jeff-ubuntu, ssh/ping from local host to jeff-ubuntu fails (different L3 subnet) but the runners themselves are still up if busy=true. Do NOT misdiagnose this as 'host down' — it's 'host unreachable from this network'."
  - "hermes-pc (Slack user U0BC138QXUJ / #hermes-pc channel) is on a separate network (172.20.5.90/19). Use as cross-check when local signals are ambiguous."
  - "Self-hosted-runner-preflight skill already exists for FIX-ORIENTED checks. This skill is different: it's an OPERATIONAL health snapshot (no fix proposed). Use this BEFORE preflight."
---

# /runner-health — Operational Health Snapshot

## When to use this skill

- User asks "are the runners up?", "is jeff-ubuntu down?", "show me runner health", "fleet health", "diagnose runners"
- Before any operation that depends on the fleet being healthy (e.g., before a 7-green drive)
- After a long gap (wifi change, host reboot) to verify reconnect
- Anytime a user reports "all alerts are noise" or "transient alerts" — this skill gives the ground truth

## What this skill does NOT do

- This is NOT a fix tool. It does not propose remediations.
- This is NOT a deep dive. For specific failures, use `self-hosted-runner-preflight` after this skill reports AMBER/RED.
- This does NOT modify any state. It only reads.

## The 5 deterministic health checks

Each is a standalone bash script in `scripts/` that outputs structured JSON to stdout.

| # | Script | What it checks | Failure mode (graceful) |
|---|---|---|---|
| 1 | `check_api.sh` | `gh api orgs/jleechanorg/actions/runners` — 22-runner snapshot + busy count + in-flight jobs (per-repo) + rate limit | exits non-zero on API error; runner fleet unreadable |
| 2 | `check_docker.sh` | local `docker ps` for mac-side runners + AO auxiliaries | exits non-zero if Docker daemon is down |
| 3 | `check_lima.sh` | `limactl list` — colima VM status, SSH port, resources | exits non-zero if limactl missing |
| 4 | `check_jeff_ubuntu.sh` | `ssh -o ConnectTimeout=5 jeff-ubuntu 'uptime; df -h /home; free -h; DOCKER_HOST=... docker ps | wc -l'` | exits non-zero on SSH timeout — but script still produces JSON with `reachable: false` |
| 5 | `cross_check_hermes.sh` | Posts thread to `#hermes-pc` and polls for reply (configurable wait) | exits non-zero if Slack MCP unavailable |

## How to invoke

### Direct script (cron / ad-hoc)

```bash
# Basic (no cross-check)
bash .claude/skills/runner-health/scripts/runner-health.sh

# With hermes-pc cross-check, 1 call
bash .../runner-health.sh --cross-check 1

# Cross-check max 3 calls (deep investigation)
bash .../runner-health.sh --cross-check 3
```

Output: console table + Markdown file at `/tmp/runner-health-<ts>.md`.

### As a slash command (via /skill)

User runs `/runner-health` (or natural-language equivalent like "check runners"). The LLM:

1. **Phase 1 — load context** (optional but recommended):
   - Invoke `memory-search` skill with query "self-hosted runner jeff-ubuntu health check transient"
   - Invoke `history-search` skill to find any prior runner-health invocations in the last 30 days
   - Note any prior transient-pattern memory entries that should bias the verdict

2. **Phase 2 — run all 4 local checks in parallel** (subagents or sequential bash):
   ```bash
   bash .claude/skills/runner-health/scripts/check_api.sh
   bash .claude/skills/runner-health/scripts/check_docker.sh
   bash .claude/skills/runner-health/scripts/check_lima.sh
   bash .claude/skills/runner-health/scripts/check_jeff_ubuntu.sh
   ```
   Each produces JSON. The LLM parses + aggregates.

3. **Phase 3 — synthesize verdict (GREEN/AMBER/RED)** based on the JSON:
   - **GREEN**: 22/22 GitHub-registered, ≥1 Linux busy=true, no Restarting loops
   - **AMBER**: GitHub shows 22/22 but no Linux busy=true, OR some Restarting loops
   - **RED**: GitHub shows <22/22, OR all Linux runners idle (likely host down), OR multiple critical signals off

   **RED sub-classification — name the cause, don't just count.** A generic
   "RED — 14/22 online" line hides whether this is a scattered multi-host
   problem or one specific physical host going fully dark. Check whether the
   RED is fully explained by ALL runners of a single host prefix
   (`org-runner-1`..`org-runner-16` = jeff-ubuntu, `org-runner-mac-*` = local
   Mac) being simultaneously offline/idle AND `check_jeff_ubuntu.sh` (or the
   equivalent SSH/ping probe) timing out. If so, report it as:
   - **RED — jeff-ubuntu host dark (16/16 Linux runners online=0/busy=0 +
     SSH/ping timeout confirmed)** rather than the generic "RED — 6/22
     online". This is the two-signal confirmation from
     `self-hosted-runner-preflight` SKILL.md Class E — cite it in the report
     so the reader knows the fix is "wait / accept degraded capacity /
     log to `rev-runn001`", not "restart a container".
   - If the offline set spans BOTH host prefixes, or Linux runners are
     offline while `check_jeff_ubuntu.sh` succeeds (host reachable but
     runners not registered), keep the generic RED framing — that's a
     process-level problem for `self-hosted-runner-preflight` Class B/D, not
     a host-dark event.

4. **Phase 4 — cross-check** (only if user asks or AMBER detected):
   ```bash
   bash .../cross_check_hermes.sh <0|1|2|3>
   ```
   Posts to `#hermes-pc` thread ts (use existing thread or new one), polls for reply, parses response.

5. **Phase 5 — write Markdown report**:
   - `bash .../runner-health.sh --write-report` (or include in the master script by default)
   - File: `/tmp/runner-health-<unix-ts>.md`
   - Contents: 4-tables (one per check), verdict, recommendations

6. **Phase 6 — present to user**:
   - Print the verdict + table summary to console
   - Reference the Markdown file path

## Output format

### Console (default)

```
=== runner-health @ 2026-06-29 07:50 PDT ===
GitHub API:   22/22 runners online, 11/22 busy (8 Linux, 3 mac)
Docker:       6/6 mac Up, 0 stuck
Lima:         colima running, 4GiB mem, 100GiB disk
jeff-ubuntu:  unreachable from this host (different wifi subnet)
hermes-pc:    cross-checked — 14/22 busy confirmed independently

VERDICT: GREEN — runners healthy, host just on different subnet
```

Host-dark example (two-signal confirmed, see preflight Class E):

```
=== runner-health @ 2026-07-02 09:10 PDT ===
GitHub API:   6/22 runners online (all 6 mac), 16/16 jeff-ubuntu Linux runners online=0/busy=0
Docker:       6/6 mac Up, 0 stuck
Lima:         colima running, 4GiB mem, 100GiB disk
jeff-ubuntu:  ssh timeout + ping timeout — both signals confirm host dark

VERDICT: RED — jeff-ubuntu host dark (16/16 Linux runners offline + SSH/ping timeout confirmed).
NOT a generic <22/22 — this is a single-host outage. See rev-runn001 for tracking; do not open a new bead.
```

### Markdown file (`/tmp/runner-health-<ts>.md`)

```markdown
# Runner Health Report — 2026-06-29 07:50 PDT

## Verdict: GREEN

## Check 1: GitHub API
| Metric | Value |
|---|---|
| Total runners | 22 |
| Online | 22 |
| Busy | 14 |
| Linux busy | 11 |
| mac busy | 5 |
| Rate limit (core) | 4284/5000 |

## Check 2: Docker (local)
| Container | Status |
|---|---|
| org-runner-mac-1..6 | Up |
| AO auxiliaries | 7/8 Restarting (1) (PR #702 fix pending) |

## Check 3: Lima VM
| Field | Value |
|---|---|
| Name | colima |
| Status | Stopped |
| CPUS | 4 |
| Memory | 4GiB |
| Disk | 100GiB |

## Check 4: jeff-ubuntu
| Field | Value |
|---|---|
| Reachable | No (different wifi) |
| Subnet | 192.168.x.x (prior) |
| Recommendation | Check router DHCP lease for new IP |

## Check 5: hermes-pc cross-check
(only if invoked)

## Notes
- PR #702 (AO spawn fix) not yet merged — bake-in bug recurs every ~1h
- 4 PRs open as DRAFT: #702, #8039, #8040, #8041
```

## Conventions

- Scripts are independent: each can run standalone for debugging
- All scripts output JSON (jq-friendly) and exit non-zero on hard error
- Master script `runner-health.sh` runs all + writes report
- Cross-check is opt-in via `--cross-check=<0|1|2|3>`
- Markdown report is in `/tmp/` (clears on reboot; user can persist by copying elsewhere)

## Anti-patterns

- Treating GitHub "online" as proof of liveness — it's registration cache, not heartbeat. Use busy=true.
- Diagnosing "host down" from ssh timeout alone — could be routing. Use busy=true as ground truth.
- Modifying `self-hosted-oss/` from this skill — that's `setup-org-runners` / `self-hosted-runner-preflight` territory.
- Storing state in `~/.local/share/runner-health/` — this skill is stateless by design.
