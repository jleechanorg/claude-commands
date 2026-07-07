# Iteration Budget: `agent.max_turns` (verified 2026-06-25)

**Read this before any "bump the iteration budget" / "raise the agent loop cap" / "make sessions longer" task.** The Hermes install on this machine currently has TWO YAML configs that ARE byte-identical mirrors (NOT separate bot configs as of the v0.13.0 install), and the knob the user is asking about is `agent.max_turns` — **not** `max_iterations`, **not** `delegation.max_iterations`. Conflating these three is the #1 cause of "I made the change but the bot doesn't see it."

## The actual knob

```yaml
# ~/.hermes/config.yaml AND ~/.hermes_prod/config.yaml, line 20
agent:
  max_turns: 60
```

- **Code default** (`projects_other/hermes-agent/hermes_cli/config.py:402`): `"max_turns": 90`
- **Active value in this install** (verified 2026-06-25 03:47 UTC, both files): `60`
- **Implication:** the value `60` was *deliberately lowered* from the code default `90` — by you, by an upgrade script, or by hand. It is NOT a "wrong default" bug. If your edit "doesn't stick," the edit isn't reaching this key.

## The three confusable knobs

| Config key | Where | What it limits | Why you might be misled |
|------------|-------|----------------|------------------------|
| `agent.max_turns` | `~/.hermes/config.yaml` line 20 | **The Hermes agent loop's per-session iteration cap.** This is what users mean by "iteration budget" / "session budget." | Old references in this skill (and in memory) called it `max_iterations` and pointed at line 348. **Both are wrong for v0.13.0+.** |
| `delegation.max_iterations` | `~/.hermes/config.yaml` line 348 | Subagent fan-out cap (delegated children per parent). Different system, unrelated. | Easy to confuse because the word "iterations" is in the key. Currently `500`. |
| `goals.max_turns` | `~/.hermes/config.yaml` line 361 | Goal-mode session cap. Currently `20`. | Same name, different subsystem (the Goals/heartbeat loop). |

**Diagnostic one-liner** — before editing anything:
```bash
grep -nE "^\s*max_turns:|^\s*max_iterations:" ~/.hermes/config.yaml ~/.hermes_prod/config.yaml
```
You should see THREE lines: `agent.max_turns`, `delegation.max_iterations`, `goals.max_turns`. If you only see `max_iterations` (no `agent.` prefix), you're on an older install — `doctor.sh` will still enforce the protected values, but the iteration cap mechanism may differ.

## The two files are mirrors (verified 2026-06-25)

| File | Purpose | Verified state on 2026-06-25 03:47 UTC |
|------|---------|---------------------------------------|
| `~/.hermes/config.yaml` | Staging tree, source of truth (gitignored) | 12,534 bytes, `agent.max_turns: 60` |
| `~/.hermes_prod/config.yaml` | Prod tree, what the running gateway reads | **Byte-identical** to staging (same size, same birth/mtime `Jun 25 03:47:26`) |

**Both files MUST be edited together.** They were both atomically re-created at the same second (birth time == mtime), so something synchronizes them — but no automated synchronizer was found in any of: `scripts/hermes-upgrade-safe.sh`, `scripts/sync-to-smartclaw.sh`, `scripts/deploy.sh`, `cron/`, `launchd/`, or `doctor.sh`. The most likely answer is the Hermes binary itself rewrites both on certain operations. **Treat them as a pair: edit staging, then `cp -p` to prod, then verify with `diff -q` BEFORE the restart.** A change to only one file may be silently overwritten on the next sync.

`config.staging.yaml` (referenced in older versions of this skill) **does not exist** in this install — verified by `ls`. The earlier "two separate bot configs" model was correct for an older install; the current install has one config read by one gateway.

## Running binary (verified 2026-06-25)

```
/opt/homebrew/bin/hermes → Hermes Agent v0.13.0 (2026.5.7)
Python 3.14.4
Install: $HOME/projects_other/hermes-agent
Launchd label: ai.hermes.prod
Gateway PID: 31853, port 8642
```

**The install dir is `$HOME/projects_other/hermes-agent/`** — this is the read-only runtime install that the gateway actually executes. Editing files there is NOT how you change the budget; you edit `~/.hermes_prod/config.yaml`. The install dir only matters for: (a) checking code defaults via `grep -nE "max_turns" hermes_cli/config.py`, (b) reading config-loading logic in `hermes_cli/config.py` (around line 4030, the `_load_config_cache` + `_normalize_max_turns_config` flow).

## Decision tree — "the user says raise the iteration budget"

```
User: "Bump iteration budget" / "agent keeps hitting its cap" / "60 is too low"
  └─ Confirm which knob they mean (default: agent.max_turns)
     ├─ Confirm desired new value
     │   (Note: AGENTS.md "no config changes without approval" still applies;
     │    user must explicitly say the new number. "Make it bigger" is not approval.)
     ├─ Edit ~/.hermes/config.yaml (line 20: agent.max_turns: <NEW>)
     ├─ cp -p ~/.hermes/config.yaml ~/.hermes_prod/config.yaml
     ├─ diff -q ~/.hermes/config.yaml ~/.hermes_prod/config.yaml  # MUST be silent
     ├─ launchctl kickstart -k gui/$(id -u)/ai.hermes.prod
     └─ Verify: /opt/homebrew/bin/hermes config show | grep "Max turns"
```

```
User: "Why is it still 60?"
  └─ Root-cause-first checklist (see below)
```

## Root-cause checklist for "my iteration-budget edit doesn't stick"

1. **Did you edit BOTH files?** `~/.hermes/config.yaml` (staging) AND `~/.hermes_prod/config.yaml` (prod). The running gateway reads prod only.
2. **Did the gateway reload?** A bare `sed -i` does NOT reload config. `launchctl kickstart -k gui/$(id -u)/ai.hermes.prod` is required. (`bootout`+`bootstrap` is the heavier alternative that re-reads plist env vars too — see `hermes-launchd-debug` skill → "Restart Procedures.")
3. **Is something rewriting the value?** Check: `find $HOME/.hermes/scripts $HOME/.hermes_prod/scripts $HOME/.hermes/cron $HOME/.hermes_prod/cron -type f -mtime -1` — any file that mentions `max_turns: 60` could be the synchronizer. As of 2026-06-25, NONE of these write `max_turns` programmatically. The most likely culprit if the value keeps snapping back is the Hermes binary's own config-loading path on restart.
4. **Are you editing the right key?** `agent.max_turns` (cap), NOT `delegation.max_iterations` (subagent fan-out), NOT `goals.max_turns` (goal mode).
5. **Is the plist pointing at the prod config?** `~/Library/LaunchAgents/ai.hermes.prod.plist` has `WorkingDirectory=$HOME/.hermes_prod` and the wrapper sources `~/.bash_profile` → `~/.bashrc`. The `HERMES_HOME` env var defaults to `~/.hermes_prod` in prod plist, so `config_path` resolves to `~/.hermes_prod/config.yaml`. Verify with: `launchctl print gui/$(id -u)/ai.hermes.prod | grep -E "HERMES_HOME|WorkingDirectory"`.

## What AGENTS.md actually protects (re-confirmed 2026-06-25)

AGENTS.md's "no config changes without approval" rule covers:
- `timeoutSeconds`, `maxConcurrent`, `subagents.maxConcurrent`, model selection

It does **NOT** list `agent.max_turns`. `doctor.sh` enforces the four approved values above but does NOT enforce `max_turns`. So bumping `max_turns` is **lower-risk than bumping `maxConcurrent`** — but the user must still explicitly name the new value. "Make it bigger" is not approval; "set `agent.max_turns: 200`" is.

## Quick recipe (verified 2026-06-25)

```bash
# 1. Confirm current value in both files
grep -nE "^\s*max_turns:" ~/.hermes/config.yaml ~/.hermes_prod/config.yaml

# 2. Edit BOTH (use sed or your editor)
sed -i '' 's/^  max_turns: 60$/  max_turns: <NEW>/' ~/.hermes/config.yaml
cp -p ~/.hermes/config.yaml ~/.hermes_prod/config.yaml

# 3. Verify identical
diff -q ~/.hermes/config.yaml ~/.hermes_prod/config.yaml  # expect: silent

# 4. Restart gateway so it reloads config
launchctl kickstart -k gui/$(id -u)/ai.hermes.prod

# 5. Wait + verify via the CLI's own view
sleep 5
/opt/homebrew/bin/hermes config show | grep "Max turns"   # expect: Max turns: <NEW>
```

## Open question for next session

The user observed `agent.max_turns: 60` and was frustrated it had not been raised despite "asking a million times." The investigation showed:
- The value IS what the config says — not a "default that keeps getting reverted" bug.
- Code default is 90, config is 60 → someone lowered it deliberately.
- No automated script found that resets it.

**What still needs investigation:** Is there a Hermes-feature-level UI/explicit-set mechanism (a button or command) that writes to config.yaml on its own, bypassing the user's intent? Or was the value `60` set on purpose years ago and the user forgot? Until proven otherwise, treat `60` as a *current setting*, not a *bug*. If the user wants 200/500/etc., they need to name the value explicitly and approve the AGENTS.md-restricted change.