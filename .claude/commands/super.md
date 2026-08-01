---
description: Resilient /super — delegates to Prime Radiant's cloud-build plugin. **Uses the fresh-slot pattern by default** (each /super call gets a UNIQUE subdirectory under ~/.cb-runs/, which = UNIQUE project_slug = UNIQUE box slot). Auto-retries on stale lock + handles parallel boxes. NEVER silently substitute local subagents. For one-liner LLM calls, use `claudeg -p "<task>"` directly.
---

# /super — resilient thin shim → Prime Radiant cloud-build plugin

`/super <task>` is the canonical entry point. It delegates to Prime Radiant's `cloud-build@superpowers-cloud-build` plugin skill. The plugin owns the canonical workflow: preflight → enrollment → handoff → follow loop → needs_input / abort / done → land.

## CRITICAL: the fresh-slot pattern (READ THIS FIRST)

**The cloud build lock is per `(enrolled_fp_hash × project_slug)`.**

- `enrolled_fp_hash` = your SSH key fingerprint
- `project_slug` = derived from your local git directory name

If you `/super` twice from the SAME directory, the second one waits for the first to release its lock. **To get parallel boxes (or to escape a stuck lock), use a different directory each time.**

That's what the **`cloud-build-fresh-slot.sh`** wrapper does: every invocation creates a fresh subdirectory like `~/.cb-runs/<timestamp>-<branch>/` with a unique `project_slug`, so every `/super` call gets its own box.

## What `/super` does (now with resilience)

1. **Validate intent**: `$ARGUMENTS` non-empty. If empty, ask the user.
2. **Create a fresh slot**: run `~/.claude/hooks/cloud-build-fresh-slot.sh` from the current directory. This:
   - Creates `~/.cb-runs/<timestamp>-<branch>/`
   - Sets up an orphan-snapshot recipe (README + plan + .claude/plans/ + hermetic flag)
   - Initializes a fresh git repo + private branch
   - Pushes to a fresh GitHub repo (one per slot)
   - Dispatches via the upstream `cloud-build-super-dispatch.sh`
3. **Polls for completion** every 30s, up to 10 min
4. **Lands the result** automatically when `state=done`
5. **Surfaces errors** verbatim — never silently substitutes

## Usage

```
/super add a /healthz endpoint with tests
/super fix issue #8059 (rewards_box XP recovery edge case)
/super build <feature>
```

Or natural-language (auto-routed via the UserPromptSubmit hook):

```
build on cloud add a /healthz endpoint
run this plan on the cloud
kick off a cloud build
build this remotely
```

The hook routes the request to `/super`, which then runs `cloud-build-fresh-slot.sh` from your current directory. **The slot is unique per call** — so multiple `/super` calls in parallel don't block each other.

## Parallel slots — how to actually use them

Each `/super` invocation creates a fresh `~/.cb-runs/<timestamp>-<branch>/` subdirectory, which gets:

1. Its own GitHub repo (named after the slot)
2. Its own `private/<branch>` work branch
3. Its own `project_slug` (= directory name)
4. **Its own box slot on the bastion**

To dispatch 5 things in parallel:
```bash
/super task-1   # creates ~/.cb-runs/task-1-<ts>/ → slot 1
/super task-2   # creates ~/.cb-runs/task-2-<ts>/ → slot 2
/super task-3   # creates ~/.cb-runs/task-3-<ts>/ → slot 3
/super task-4   # creates ~/.cb-runs/task-4-<ts>/ → slot 4
/super task-5   # creates ~/.cb-runs/task-5-<ts>/ → slot 5
# All 5 run in parallel on different boxes
```

Each slot is independent. One failing doesn't block the others.

## Resilient error handling

| Error | What it means | What `/super` does |
|---|---|---|
| `preflight FAIL: ...` | Local pre-check failed (uncommitted changes, missing plan, etc.) | Surfaces verbatim. Fix the plan and re-run. |
| `lock busy: fp:<hex>` | Stale lock from previous abandoned run (same fingerprint) | Fresh-slot pattern auto-escapes this (different project_slug = different box). If locked on this exact directory, switch to a different CWD. |
| `cloud-bastion: run is preflight_failed` | Bastion refused | Surface verbatim; check plan content. |
| `cloud-bastion: delivery-only evidence could not be inspected` | Bastion overload / transient error | Wrapper auto-retries 3× with backoff. |
| `ssh: connect refused` / `kex_exchange` | Transport error | Auto-retries with backoff. |
| Other / unknown | Various | Surfaces verbatim, exits 1. |

## Hard rules

1. **NEVER silently substitute** local subagents or `claudeg` for the Cloud Build box. If the user said "use cloud" / "build on cloud" / etc., the answer is to dispatch to the box OR fail loudly.
2. **NEVER bypass the plugin** by calling `cloud-build-super-dispatch.sh` directly. The plugin's skill orchestrates the full workflow.
3. **The wrapper is the only place** that auto-retries on stale locks. The plugin itself does not retry.
4. **If 3 attempts fail**, surface the error verbatim. Switch to a different directory (fresh slot) and retry.

## Escape hatch

For one-liner LLM calls with no pipeline and no dispatch, run `claudeg -p "<task>"` directly. That bypasses `/super` and the box entirely — by design.

## File locations (both machines)

- `/super` slash command: `~/.claude/commands/super.md`
- UserPromptSubmit hook v2.2: `~/.claude/hooks/cloud-build-trigger.sh`
- **Fresh-slot wrapper (NEW)**: `~/.claude/hooks/cloud-build-fresh-slot.sh`
- Resilient dispatch wrapper: `~/.claude/hooks/cloud-build-dispatch.sh`
- Plugin source mirror: `~/superpowers-cloud-build-main/` (Prime Radiant)
- Cloud Build state: `~/.config/cloud-build/state.json`
- Cloud Build SSH key: `~/.ssh/cloud-build/id_ed25519`

## Sources

- **Master gist**: https://gist.github.com/jleechan2015/a15e331ffc62993376e4d7d5ed15fbfe
- **Clean-room repro** (per-fp lockout details): https://gist.github.com/jleechan2015/c78274c001a933f384d04cf593cd0de6
- **Public issue tracker** (obra viewer): https://github.com/jleechan2015/pb-archive-2026
- **Plugin source mirror** (private): https://github.com/jleechanorg/superpowers-cloud-build-source
- **Companion gists**: usability, confusion-patterns, 30-code-defects (linked from master)
