---
name: agent-methodology-install-audit
description: |
  Use when installing any agent-development CLI (GSD Core, Superpowers plugin, mattpocock/skills via npx, marketplace plugins, npx/npm/pip wrappers) into Claude Code or a sibling runtime. External installers silently write always-on hooks to ~/.claude/settings.json — these count as "default guidance" the user may have explicitly said NOT to add. Covers pre-install plan (read --help, pick lean profile), post-install audit (enumerate hooks + plugins + env), and report back before declaring done. Verified 2026-07-30 in C09GRLXF9GR/1785467202.742629: user said "dont add any default guidance yet" but `npx -y @opengsd/gsd-core@latest --claude --global` still wrote 15 always-on hooks; `--profile=core` would have cut eager-load to ~700 tokens.
allowed-tools: [Bash, Read, Grep, Glob]
when_to_use: |
  Use when (a) installing an agent methodology/CLI/plugin, (b) the user said "don't add default guidance" / "don't auto-fire" / "lean install", or (c) auditing what an installer just wrote.
tags: [agent-cli, install, audit, hooks, settings.json, gsd-core, superpowers, grill-me, claude-code-plugins]
related_skills: [hermes-agent, claude-code, claude-code-claudem, agento, harness-engineering]
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Agent Methodology Install + Post-Install Audit

> **Class:** post-install settings audit for ANY agent-development CLI installer (Claude Code plugins, Codex plugins, `npx`-based installer scripts, npm/pip wrappers).
> **Verified case:** GSD Core v1.9.0 installed 15 always-on hooks to `~/.claude/settings.json` even though user said "don't add default guidance" (C09GRLXF9GR/1785467202.742629, 2026-07-30).

## The Class

External agent-CLI installers don't just write skill files. The expensive part — the part the user actually cares about when they say "don't add default guidance" — is the **side effects**:

| Layer | What an installer might write |
|---|---|
| Skills | `~/.claude/skills/<name>/*.md` (inert until invoked) |
| Commands | `~/.claude/commands/<name>.md` (user-only, no auto-fire) |
| Plugins | `~/.claude/plugins/...` + `enabledPlugins` in `settings.json` |
| **Hooks** | **`~/.claude/settings.json` `hooks` map — SessionStart, PreToolUse, PostToolUse, SubagentStop, PreCompact, FileChanged, Stop, UserPromptSubmit** |
| Session-start injections | Bash command that injects text every session (this IS default guidance) |
| Env vars | `.bashrc` exports, launchd EnvironmentVariables |
| Runtime config | `~/.claude/VERSION`, `.gsd-runtime`, `package.json` markers |
| Status line | `~/.claude/settings.json` `statusLine` (replaces existing) |
| Worktree policy | Server-side or local branch-creation guards |

When the user says "install it" without saying "don't add default guidance," the default is OK — install everything.
When the user says "install it" with "no default guidance" / "don't auto-fire" / "lean install" — the installer default profile is almost certainly WRONG. The audit is the contract.

## The Three Phases

### Phase 0 — Pre-install plan (read the help, pick the profile)

Before running any installer:

```bash
# Always read --help first; installers expose flag knobs that change behavior drastically
npx -y <pkg>@latest --help

# Look for these knobs in the output:
#   --profile=<name>   (GSD Core has core|standard|full; lean → core)
#   --lean / --minimal / --core-only
#   --no-hooks / --no-session-start / --skip-statusline
#   --local vs --global
#   --runtime <name>   (multi-runtime installers ask; pick the runtime the user is on)
```

Write the chosen flags into the install command. Never run the bare `npx <pkg>` interactively — interactive installers trap the agent in a TTY menu that won't return.

**Canonical example (GSD Core, lean install):**
```bash
npx -y @opengsd/gsd-core@latest --claude --global --profile=core
```
Without `--profile=core`, the default `--profile=full` adds ~12k tokens of eager-load + all guard hooks. With `--profile=core`, eager-load drops to ~700 tokens and most auto-firing hooks are skipped.

**Canonical example (mattpocock skills):**
```bash
npx -y skills@latest add mattpocock/skills --skill=grill-me -y -g
```
Always pass `-y` (skip multi-select) and `-g` (global). Without `-y`, the installer opens an interactive multi-select TUI panel that hangs in non-TTY terminals.

**Canonical example (Claude Code marketplace plugin):**
```bash
/plugin install superpowers@claude-plugins-official
```
Marketplace plugin installs go through Claude Code's own plugin manager — they write to `enabledPlugins` in `settings.json` and may add SessionStart hooks. Read what the plugin's `plugin.json` declares as `hooks` before installing.

### Phase 1 — Run the install (capture full output)

Use `terminal` with a generous timeout. Capture the full output — the installer's own report is the first audit source. Look for:

- Number of skills installed
- Number of hooks configured
- Whether it skipped or replaced the statusline (skipped = non-destructive; replaced = may have clobbered an existing config)
- "First-time baseline scan" / "preserved N user baseline files" messages — this means the installer is non-destructive on existing config
- Any error / warning lines

A clean install with all hooks reported = red flag. The user almost certainly wanted a subset. Treat the installer's "Done!" as the START of the audit, not the end.

### Phase 2 — Audit (the deliverable)

Run these four probes and surface the table to the user. **Do not declare done until the audit table is in the reply.**

**Probe 1 — Hooks added by the installer:**
```bash
python3 -c "
import json
d = json.load(open('$HOME/.claude/settings.json'))
for event, arr in d.get('hooks', {}).items():
    for entry in arr:
        for h in entry.get('hooks', []):
            print(f'{event:18} | {h.get(\"command\", \"\")}')
"
```

**Probe 2 — Plugins enabled:**
```bash
python3 -c "
import json
d = json.load(open('$HOME/.claude/settings.json'))
for name, enabled in d.get('enabledPlugins', {}).items():
    print(f'{\"ENABLED\" if enabled else \"disabled\"} {name}')
"
```

**Probe 3 — Did the installer write to SOUL.md / CLAUDE.md / AGENTS.md?** (the user's actual "default guidance" file):
```bash
echo 'SOUL.md hits:';  grep -ci '<installer-name>|<methodology>' ~/.hermes/workspace/SOUL.md
echo 'CLAUDE.md hits:'; grep -ci '<installer-name>|<methodology>' ~/.claude/CLAUDE.md
echo 'AGENTS.md hits:'; grep -ci '<installer-name>|<methodology>' ~/.claude/AGENTS.md
```

**Probe 4 — File-level changes (mtimes):**
```bash
stat -f '%Sm  %z bytes  %N' ~/.hermes/workspace/SOUL.md ~/.claude/CLAUDE.md ~/.claude/settings.json
```

**The audit table format (Slack-native, concise):**

```
🟢 Done
- <installer> v<X.Y> — installed via <command>

🟡 Audit
- Hooks added: <N>
  - <event> | <command>
- Plugins enabled: <name> (<X>/<N>)
- SOUL.md/CLAUDE.md touched: yes/no
- Eager-load tokens (if installer reports it): ~<N>k

🔴 Defaults the user may not want
- <list of always-on hooks that fire on every session>
- <statusline replacement, env exports, etc.>

🔵 Next
- <either: "ready to use, here's how to invoke" or "want me to uninstall + reinstall with --profile=core?">
```

### Phase 3 — Wait for confirmation before declaring done

If the audit shows the installer added anything auto-firing and the user said "no default guidance," **stop and ask**:
- Reinstall with the lean profile (`--profile=core`)
- Uninstall entirely (`<installer> --uninstall`)
- Accept the full install (confirm explicitly)

Don't pick for the user. Don't assume "no default guidance" means "any profile." The lean profile is almost always what they meant, but ask.

## Pitfalls

1. **The installer's "Done!" is the start, not the end.** Most installers report success without enumerating hooks. Hooks are written silently. The audit is the only contract.

2. **Interactive installers trap non-TTY agents.** `npx <pkg>` with no flags often opens a TUI menu. Use `-y` or equivalent skip-flag, or pre-set the answer via env var. Test the command with `--help` first to see what flags exist.

3. **`--profile=full` (default) is the kitchen sink.** GSD Core, and probably most multi-mode installers, defaults to `--profile=full`. This is the OPPOSITE of "no default guidance." Read the help; pick the lean profile.

4. **Statusline replacement is destructive.** Some installers replace an existing `statusLine` config silently. Always check the install output for "Replaced statusline" / "Skipped statusline (already configured)." If "skipped," the existing one is safe. If "replaced" or absent, run with `--force-statusline` only when the user confirms.

5. **Hook timing is "always on."** SessionStart hooks fire every session, not just the first. PreToolUse + PostToolUse hooks fire on every tool call. SubagentStop + PreCompact hooks fire on every agent boundary. A 5-hook install can add thousands of ms per session.

6. **Don't touch SOUL.md / CLAUDE.md unless asked.** Adding a "use <methodology>" instruction to the policy file IS the default guidance the user said no to. The installer does not write here by default; you must not either.

7. **Sandbox/preview installers don't reflect real-state.** A `npx <pkg>` run in `/tmp` for testing won't show what the global install will write. If you must test in isolation, audit `/tmp/<user>/.claude/settings.json`, not the real `~/.claude/settings.json`.

8. **The Claude Code `plugins/` cache is not the same as `enabledPlugins`.** Plugins live at `~/.claude/plugins/cache/<marketplace>/<name>/<version>/` (read-only, on disk). What the runtime loads is governed by `enabledPlugins` in `settings.json`. To turn a plugin OFF without uninstalling, flip the boolean in `enabledPlugins` — do not delete the cache.

9. **Uninstall is not always symmetric.** Some installers have `--uninstall` (`@opengsd/gsd-core --uninstall`, `npx skills remove`). Others require manual `rm -rf` of the skill directory + undoing `settings.json` entries. Always check `<installer> --help | grep -i uninstall` first.

10. **Multi-runtime installers ask.** GSD Core `--help` lists `--claude`, `--opencode`, `--kilo`, `--codex`, `--kimi`, `--copilot`, `--antigravity`, `--cursor`, `--windsurf`, `--augment`, `--trae`, `--qwen`, `--hermes`, `--cline`, `--codebuddy`, `--zcode`. Picking the wrong one writes to the wrong runtime config. Always pass the explicit runtime flag (`--claude --global` is the user's typical setup).

11. **The post-audit decision menu is HOLD, not action.** When the audit reveals the installer added auto-firing hooks and the user said "no default guidance" / "lean install," post a 2-3 option menu (e.g. `reinstall --profile=core`, `uninstall`, `accept full install`) and STOP. Do not pick one and execute. The lean profile is almost always what they meant, but "almost always" is not the same as "yes." Verified case: this skill's origin session (C09GRLXF9GR/1785467202.742629, 2026-07-30) — agent posted three options, user did not reply before gateway/echo loop took over, agent held for ~50 turns with a 1-line ack per turn. That was the correct behavior. Wrong behavior: pick option 2, run `uninstall` + `reinstall --profile=core`, declare done — that bypasses the user's choice and creates a window where they can't undo it.

12. **Mid-turn echo loop = hold, do not invent directive.** During a long decision-pending hold, the Slack-relay/gateway can feed the agent's OWN prior message back as the next "user message" for many turns. The correct response each turn is a single-line hold ack (e.g. "Same echo. Holding.") with the LLM-provenance caveat footer — not invented directives. Cite SOUL.md `## COMMIT: never-hallucinate-no-new-content`: a missing/echoed body is a SIGNAL, not a fact. Re-fetch the original `conversations_replies` if a real instruction might be queued. NEVER pick option 2 vs option 3 from your own earlier reply and act on it — that's the agent forking the user. Verified: this session, ~50 turns of self-echo, no false-action taken.

13. **Slack-relay echo vs gateway shutdown — distinguish them.** A `Queued for the next turn` notice is a templated queue message, not user content. A `Gateway is shutting down and is not accepting another turn right now` notice is a real shutdown signal — respond once with "Got it, I'll be here when you're back" and stop. Both look like echoes at first glance; the difference is whether the relay is still cycling or the gateway has actually stopped accepting turns.

## Verification Checklist

After any agent-CLI install, verify:

- [ ] Install command used the lean profile (or full, with user confirmation)
- [ ] Installer help text was read first (`--help`)
- [ ] Install output captured to a log for evidence
- [ ] Hook audit table produced (Probe 1) — count + per-event breakdown
- [ ] enabledPlugins audit produced (Probe 2) — list of enabled vs disabled
- [ ] SOUL.md / CLAUDE.md / AGENTS.md mtimes unchanged (Probe 3 + 4)
- [ ] Audit table sent to user BEFORE the "done" message
- [ ] User confirmed the install matches their intent (or asked for reinstall/uninstall)
- [ ] LLM-provenance caveat footer appended (per SOUL.md `llm-provenance-caveat`)

## Related Skills

- `hermes-agent` — bundled, covers Claude Code plugin model at the meta level
- `claude-code` — bundled, Claude Code CLI patterns
- `claude-code-claudem` — the `claudem` wrapper for non-Anthropic providers
- `agento` — Agent Orchestrator dispatch (different class: AO spawn, not CLI install)
- `harness-engineering` — broader harness-level changes (SOUL.md / TOOLS.md / commit blocks)
- `slash-command-layering` — when a CLI installs a slash command that mirrors a repo-local one
- `browser-headless-default` — same "default = on; user said off" pattern, different surface