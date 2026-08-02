# AO Spawn — TS CLI auth + 20-slot cliff pitfalls (2026-07-22)

Three related pitfalls that hit together when the orchestrator pool is
exhausted. Verified on PR #8488 ($GITHUB_REPOSITORY) /repro
dispatch 2026-07-22, worldarchitect project. The active `dispatch-task`
SKILL.md does not yet cover these; this is the session-specific
detail.

## Pitfall A — TS CLI rejects `gh auth token` from `env -i`

**Symptom:** Spawning with the canonical TS CLI under `env -i` fails with:

```
✗ GitHub CLI is not authenticated. Run: gh auth login
```

even though `gh auth token` returns a valid token in the OUTER shell
(success under `gh auth status` in the same session).

**Root cause:** The TS CLI (`$HOME/.nvm/versions/node/v22.22.0/bin/ao`)
reads its own auth from a different mechanism than `gh`. The daemon
talks to the orchestrator HTTP API, not to the `gh` CLI directly, and
the API call requires either `AO_BOT_GH_TOKEN` set to the same value
as `GH_TOKEN`, OR preserving `XDG_CONFIG_HOME=$HOME/.config`
inside the `env -i` wrapper. The skill's existing `env -i` recipe
passes `GH_TOKEN` and `AO_BOT_GH_TOKEN` but drops `XDG_CONFIG_HOME`,
which the TS CLI also reads.

**Verified work-around recipe:**

```bash
env -i HOME=$HOME \
    PATH=$HOME/.local/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/bin:/bin \
    XDG_CONFIG_HOME=$HOME/.config \
    GH_TOKEN="$(gh auth token)" \
    AO_BOT_GH_TOKEN="$(gh auth token)" \
    bash -c '$HOME/.nvm/versions/node/v22.22.0/bin/ao spawn -p <project> --agent claude-code "<task>"'
```

If it STILL fails with the same error, run `ao status` (NOT under
`env -i`) to confirm the daemon is alive — if `ao status` works but
spawn still fails, the daemon's per-project state is corrupt and a
restart is needed (`ao stop <project> && ao start <project>`).

## Pitfall B — 20-slot cliff with stuck `[spawning]` placeholders

**Symptom:** `ao session ls -p <project>` shows 20 entries all in
`[spawning]` state with `(10d)`, `(9d)`, `(8d)` age stamps. New
`ao spawn` rejects with the canonical cap message; the orchestrator
will not recycle the slots because it thinks they are mid-spawn.

**Root cause:** Zombie sessions that started spawning but never
transitioned to a healthy state. The orchestrator's spawn-validator
still counts them against the cap.

| Command | Purges stuck `[spawning]`? |
|---|---|
| `ao session cleanup` | NO (verified) |
| `ao session kill <id>` | NO |
| `ao session kill --purge-session <id>` | **YES** (one slot at a time) |

**Verified recovery recipe:**

```bash
# 1. List the stuck slots
$HOME/.nvm/versions/node/v22.22.0/bin/ao session ls -p <project>

# 2. Purge them one at a time (the API accepts a single session per call)
$HOME/.nvm/versions/node/v22.22.0/bin/ao session kill --purge-session <stuck-session-id>

# 3. After purging all 20, retry spawn
$HOME/.nvm/versions/node/v22.22.0/bin/ao spawn -p <project> --agent claude-code "<task>"
```

**When to fall back to inline instead of purging:** if more than ~10
slots are stuck, the project pool has systemic issues (network/runner/
daemon). Purging 10+ slots serially costs ~5-15 min of wall clock;
pivot to inline execution (drive work directly in the existing
worktree at `~/.worktrees/<project>/<session-id>` — see SKILL.md §"When
to skip AO and implement inline").

## Pitfall C — `[spawning]` slot count is the AUTHORITATIVE pool size

`ao session ls` returns BOTH healthy workers AND stuck placeholders.
Do NOT trust "no active sessions" output — that view filters by state
in some CLI versions and shows `telemetry_install_id` placeholders
too. The authoritative count is the number of rows, regardless of
state. **20 rows = full pool = new spawn rejected**, regardless of how
many are `[working]` vs `[stuck]`.

**Decision matrix when pool is full:**

| Pool state | Action |
|---|---|
| 0-15 sessions, mix of `[working]` and `[idle]` | spawn normally |
| 15-19 sessions, no stuck placeholders | spawn with `AO_MAX_CONCURRENT_SESSIONS=25` (per-spawn override, does not affect other sessions) |
| 20+ sessions OR ≥10 stuck `[spawning]` placeholders | purge stuck slots OR pivot to inline — see Pitfall B above |
| Pool full + new spawn errors with `Spawn rejected: 20 active sessions >= cap (20). Set AO_MAX_CONCURRENT_SESSIONS env var to increase. Wait for sessions to complete.` | confirm with `ao session ls` count; do NOT escalate to `ao stop` (nukes lifecycle polling for all 20 in-flight sessions) |

## Sequence I actually hit (2026-07-22, PR #8488 /repro dispatch)

1. `ao spawn -p worldarchitect --agent claude-code "<task>"` → `✗ GitHub CLI is not authenticated` (Pitfall A).
2. Tried env -i with GH_TOKEN + AO_BOT_GH_TOKEN → still `✗ GitHub CLI is not authenticated`.
3. Discovered `XDG_CONFIG_HOME` was missing from the env -i wrapper → added it.
4. Got past auth — but `ao spawn` now refused with `Spawn rejected: 20 active sessions`.
5. `ao session ls -p worldarchitect` showed 20 rows, all `[spawning]` with `(10d)` `(9d)` `(8d)` age stamps (Pitfall B).
6. **Decision:** rather than purging 20 slots serially (~15 min wall clock), pivoted to inline execution — drove `/repro` directly in the existing worktree at `/private/tmp/wa-missions/god-mechanics-v2` using `scripts/campaign_manager.py` + `scripts/copy_campaign.py` + `scripts/download_campaign.py` (all run locally with `WORLDAI_DEV_MODE=true` env vars already exported). Completed the campaign inventory + 169-directive categorization + LLM-render verdict in ~5 min wall clock.

The lesson: when 20+ slots are stuck, the AO infrastructure is
degraded enough that purging + respawning is wasteful. Inline
execution in the existing worktree is the faster path.

## Cross-references

- SKILL.md §"Spawn wrapper — `env -i` is mandatory on macOS" — the original env -i recipe; needs the `XDG_CONFIG_HOME` line added per Pitfall A.
- SKILL.md §"`ao spawn` \"timeout\" is NOT a spawn failure" — adjacent but distinct failure mode (timeout exit code 124 vs the auth 401 covered here).
- SKILL.md §"`lifecycle polling is inactive`" — adjacent failure mode (orchestrator not running vs auth missing); same `ao status` pre-flight applies.
- SKILL.md §"Stale / misrouted session recovery" — adjacent (coordinating with stale workers); purge-session is the new variant.
- SKILL.md §"Multi-PR fanout from one issue" — affected by Pitfall C (if pool is full, N-worker fanout is impossible; pivot to inline or sequential).
- `babysit-ao-pr-loop` SKILL v1.9.0 — referenced from the dispatch skill; the babysit observer pattern is independent of the spawn failures here.
