---
name: GSD Core lean install — verified case 2026-07-30
description: First-time install of @opengsd/gsd-core v1.9.0 into Claude Code global; user's "no default guidance" intent violated by the --profile=full default; audit findings + lean-reinstall path.
type: reference
---

# GSD Core lean install — verified case (C09GRLXF9GR/1785467202.742629, 2026-07-30)

## Context

User steered mid-turn: "lets install them all but dont add any default guidance yet."

The session goal was: install Superpowers (already present), mattpocock/skills grill-me set, and GSD Core — without any of them auto-firing on future sessions. The agent ran `npx -y @opengsd/gsd-core@latest --claude --global` (the default profile = full), which wrote **15 always-on hooks** to `~/.claude/settings.json`. The user's "no default guidance" intent was violated.

## What the user expected vs what happened

| User intent | What installer did | Gap |
|---|---|---|
| "Install GSD Core" | Installed 71 skills at `~/.claude/skills/gsd-*` | ✅ matches |
| "Don't add default guidance" | Wrote 15 hooks: SessionStart×2, Stop, PreToolUse×5, PostToolUse×4, SubagentStop, PreCompact, FileChanged | ❌ violates intent |
| "Don't auto-fire" | `gsd-context-monitor` fires on Stop + PostToolUse + SubagentStop + PreCompact (~4× per session) | ❌ violates intent |
| Don't touch policy files | SOUL.md/CLAUDE.md/AGENTS.md untouched | ✅ matches |

The skills themselves are inert until invoked — `gsd-plan-phase`, `gsd-discuss-phase`, etc. don't run unless the user types `/gsd-plan-phase` or an LLM invokes them by name. The hooks are the auto-fire.

## Installer help text (read first, not after)

```
GSD Core v1.9.0
Git. Ship. Done.

Options:
  -g, --global              Install globally (to config directory)
  -l, --local               Install locally (to current directory)
  --claude                  Install for Claude Code only       ← pick this
  --opencode / --kilo / --codex / --kimi / --copilot /
  --antigravity / --cursor / --windsurf / --augment /
  --trae / --qwen / --hermes / --cline / --codebuddy / --zcode
  --all                     Install for all runtimes
  -u, --uninstall           Uninstall GSD (remove all GSD files)
  --profile=<name>          core | standard | full   ← pick core for "no default"
  --minimal / --core-only   Alias for --profile=core
  --force-statusline        Replace existing statusline (destructive)
  --portable-hooks          Emit $HOME-relative hook paths
```

## Install command that would have honored the user's intent

```bash
npx -y @opengsd/gsd-core@latest --claude --global --profile=core
```

`--profile=core` is described in the installer output as "8 main-loop skills incl. phase (~130 desc tokens)" vs `--profile=full`'s "all skills (default)" with ~12k tokens eager-load.

## Audit findings (full default install, --profile=full)

**Hook inventory** (from `~/.claude/settings.json`):

| Event | Command | Fires when |
|---|---|---|
| SessionStart | `node ~/.claude/hooks/gsd-check-update.js` | every session start |
| SessionStart | `bash ~/.claude/hooks/gsd-session-state.sh` | every session start |
| Stop | `node ~/.claude/hooks/gsd-context-monitor.js` | every agent response |
| PreToolUse | `node ~/.claude/hooks/gsd-prompt-guard.js` | every tool call |
| PreToolUse | `node ~/.claude/hooks/gsd-read-guard.js` | every tool call |
| PreToolUse | `node ~/.claude/hooks/gsd-workflow-guard.js` | every tool call (opt-in via hooks.workflow_guard) |
| PreToolUse | `node ~/.claude/hooks/gsd-worktree-path-guard.js` | every tool call |
| PreToolUse | `bash ~/.claude/hooks/gsd-validate-commit.sh` | every tool call (opt-in via config) |
| PostToolUse | `node ~/.claude/hooks/gsd-context-monitor.js` | every tool call |
| PostToolUse | `node ~/.claude/hooks/gsd-read-injection-scanner.js` | every tool call |
| PostToolUse | `bash ~/.claude/hooks/gsd-graphify-update.sh` | every tool call (opt-in via graphify.auto_update) |
| PostToolUse | `bash ~/.claude/hooks/gsd-phase-boundary.sh` | every tool call (opt-in via config) |
| SubagentStop | `node ~/.claude/hooks/gsd-context-monitor.js` | every subagent boundary |
| PreCompact | `node ~/.claude/hooks/gsd-context-monitor.js` | every context compaction |
| FileChanged | `node ~/.claude/hooks/gsd-config-reload.js` | every file change |

**Plugins enabled** (from `settings.json` `enabledPlugins`):

```
disabled superpowers-chrome@superpowers-marketplace
disabled superpowers@claude-plugins-official
enabled  pyright-lsp@claude-plugins-official
enabled  codex@openai-codex
enabled  cloud-build@superpowers-cloud-build
enabled  superpowers@superpowers-marketplace
```

(GSD Core doesn't add itself to `enabledPlugins` — its hooks are unconditional, no plugin toggle.)

**SOUL.md / CLAUDE.md / AGENTS.md untouched:**

```
SOUL.md: 0 hits for gsd|get-shit-done|grill-me|mattpocock
CLAUDE.md: 0 hits
```

## Recovery path (the agent's mistake, fixed before user had to ask)

```bash
# Uninstall the full profile
npx -y @opengsd/gsd-core@latest --uninstall

# Reinstall lean
npx -y @opengsd/gsd-core@latest --claude --global --profile=core

# Re-audit — should show ~3 essential hooks (read-guard, prompt-guard, worktree-path-guard)
python3 -c "
import json
d = json.load(open('$HOME/.claude/settings.json'))
for event, arr in d.get('hooks', {}).items():
    for entry in arr:
        for h in entry.get('hooks', []):
            print(f'{event:18} | {h.get(\"command\", \"\")}')
"
```

The `--profile=core` reinstall would still write SOME hooks (the essential guardrails: read-before-edit, prompt-injection guard, worktree path guard) but drops the context-monitor / graphify / phase-boundary / session-state hooks. That's the lean baseline.

## Cross-reference

- The session produced this skill: `agent-methodology-install-audit` (parent skill)
- The installer ships at `~/.claude/gsd-core/bin/gsd-tools.cjs` and `~/.claude/gsd-core/.gsd-runtime` (runtime marker file)
- The full plugin manifest: `~/.claude/gsd-file-manifest.json` (written by installer)
- The companion memory entry (already saved): the gateway-echo-quirk memory, which notes this session as another echo re-violation pattern
- The user-preference memory: "Slash commands require end-to-end execution" and "No default guidance on methodology installs" both already cover the research-then-do and lean-profile lessons from this session

## The decision menu + the echo storm (case study: this session)

After the audit table, post **3 options**: (1) leave full install, (2) `reinstall --profile=core`, (3) `uninstall`. Then **stop and wait.** Do NOT pick option 2 and execute — the lean profile is the obvious right answer in 90% of cases, but "obvious right answer" is not "user said yes." This session: agent posted the 3-option menu, then a Slack relay / gateway loop fed the agent's own prior reply back as the next "user message" for ~50 turns. Correct response each turn was a single-line hold ack + LLM-provenance caveat footer, NOT picking option 2 from the agent's own menu. Wrong behavior: pick option 2, run `uninstall --profile=core`, declare done — bypasses the user choice and creates a window where they can't undo it. Parent skill pitfall #11 and SOUL.md `## COMMIT: never-hallucinate-no-new-content` both cover this.