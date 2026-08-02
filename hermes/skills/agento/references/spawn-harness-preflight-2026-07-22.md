---
name: agento
version: 1.5.1 (addendum)
last_verified: 2026-07-22
trigger: pre-spawn harness authStatus check (companion to spawn-model-preflight.md)
---

# Pre-spawn harness authStatus check (companion to `spawn-model-preflight.md`)

The original `references/spawn-model-preflight.md` covers the **post-spawn** failure mode: worker boots, hits a provider-side usage-limit banner mid-prompt, goes idle >90s, must be killed and respawned on a different harness.

This addendum covers the **pre-spawn** gap: even before any worker boots, `ao agent ls --json` can report the project's fallback-chain top entry as `authStatus: "unknown"` (not `"unauthorized"` and not `"authorized"` — **unknown**). Spawning against an `unknown` harness wastes a session slot and stalls the daemon.

## When this fires

Before any `ao spawn` against a project that declares a `fallbackAgents` chain (e.g. `worldarchitect: [codex, claude-code]`), run:

```bash
ao agent ls --json | python3 -c '
import json, sys
d = json.load(sys.stdin)
auth = {a["id"]: a.get("authStatus") for a in d["supported"]}
print(json.dumps(auth, indent=2))'
```

Then read the project entry from `~/.hermes_prod/agent-orchestrator.yaml` (or `~/agent-orchestrator.yaml` symlink target):

```bash
grep -A3 "^  <project>:" ~/.hermes_prod/agent-orchestrator.yaml
```

If the **first** entry in `fallbackAgents` has `authStatus != "authorized"`, pin `--harness <next-authorized-entry>` explicitly instead of letting the chain default. Verified 2026-07-22 on `worldarchitect` (codex = `unknown`, claude-code = `authorized` → spawned with `--harness claude-code`; no idle stall).

## Decision table

| First fallback authStatus | Action |
|---|---|
| `authorized` | No `--harness` flag needed; chain default works |
| `unknown` or `null` or missing key | Pin the first `authorized` entry via `--harness <id>` |
| `unauthorized` AND no other `authorized` entry in chain | Refuse the spawn; surface the auth gap to the user — do NOT spawn a session that will 401 mid-prompt |
| All entries `unknown`/`null` | `ao agent ls --json` is stale; restart daemon (`ao stop && ao start`) and re-probe; if still broken, refuse spawn |

## Pitfall — authStatus drift after `ao start`

A freshly-restarted AO daemon can take 1–5 seconds to populate `authStatus` correctly. If the first `ao agent ls` right after `ao start` shows everything as `unknown`, sleep 3s and re-probe before declaring the chain healthy. Verified 2026-07-22 — after `ao stop && ao start`, `ao agent ls` initially showed codex as `unknown` for ~3s before resolving to its actual state.

## Why this is a separate file, not a paragraph in spawn-model-preflight.md

The post-spawn rule is "kill+respawn when banner appears." The pre-spawn rule is "skip the doomed harness when `ao agent ls` already says so." Different gate, different probe, different fix. Future agents that load the parent preflight reference should ALSO load this one — `agento/SKILL.md` should reference both.

## Cross-references

- `references/spawn-model-preflight.md` — post-spawn usage-limit + idle-90s rule
- `~/.hermes/skills/finish-the-job/SKILL.md` v1.7.1 — Phase 0.5 disambiguation rule (fetch Slack thread to ground ambiguous task names BEFORE dispatching — see `references/finish-ambiguous-ta[REDACTED_OPENAI_KEY]`)
