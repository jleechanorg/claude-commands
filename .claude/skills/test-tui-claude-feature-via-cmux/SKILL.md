---
name: test-tui-claude-feature-via-cmux
description: When asked to verify whether a Claude Code feature works (especially slash commands, dialogs, pickers, status indicators), spawn a real interactive TUI session in cmux — never use `claude --print "/feature"` as a test, because --print is non-interactive and will always return "isn't available in this environment" regardless of whether the feature actually works.
when_to_use: "Use when the user asks 'does Claude Code feature X work', 'verify /feature works', 'test the slash command', or any verification question about a Claude Code TUI-only feature. Also use proactively when about to write `claude --print \"/<feature>\"` to test anything — that's the wrong test. Trigger phrases: 'verify /', 'test /', 'check that /', 'is /feature available', 'does the advisor work', 'does the model picker work', 'is the slash command working'."
allowed-tools: [Bash, Read]
context: inline
---

# Test TUI-only Claude Code features via cmux, not `--print`

## When to use this skill

Use this skill any time a verification question is about a Claude Code feature
that is implemented in the TUI (slash commands, dialogs, pickers, status bar
indicators, settings menus). The most common failure mode is treating
`claude --print "/feature"` as a test — it isn't, and the resulting
"isn't available in this environment" error leads to wasted time reading
minified binary strings chasing phantom gates.

**Trigger phrases** (load this skill when you see any of these):

- "Does /advisor work?"
- "Does the /config menu show X?"
- "Is the /model picker working?"
- "Verify the slash command"
- "Test the Claude Code TUI feature"
- Any verification question where the answer is a slash command, dialog,
  picker, or status indicator

**Do NOT use this skill** for:

- Plain completion questions (`--print "what model are you?"` works)
- Tool use / file reading / API contract tests (`--print` is fine)
- Anything that doesn't involve a TUI slash command, dialog, or picker

## The core rule

`claude --print` is **non-interactive mode**. Slash commands render inside the
Ink TUI as menus, dialogs, or pickers — they have no `--print` representation.
The binary's response to any TUI slash command in `--print` mode is always:

> `/<feature> isn't available in this environment.`

That error specifically means "I cannot show you this in non-interactive
mode," **not** "this feature is broken." Treating it as a feature-gate
failure is the mistake this skill exists to prevent.

## The correct test path

```bash
# 1. Spawn a fresh Claude Code workspace in cmux
export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock
WS_OUT=$(cmux new-workspace --cwd "$PWD" --command "claude")
WS=$(echo "$WS_OUT" | grep -oE 'workspace:[0-9]+' | head -1)

# 2. Find the auto-created surface
sleep 2
SURF=$(cmux list-pane-surfaces --workspace "$WS" 2>/dev/null \
       | grep -oE 'surface:[0-9]+' | head -1)

# 3. Wait for Claude to be ready (look for the `❯` prompt in screen text)
cmux read-screen --workspace "$WS" --surface "$SURF" --scrollback --lines 30

# 4. Send the slash command + press Enter
cmux send --workspace "$WS" --surface "$SURF" "/advisor"
cmux send-key --workspace "$WS" --surface "$SURF" enter

# 5. Read the result (dialog, picker, error message, etc.)
sleep 2
cmux read-screen --workspace "$WS" --surface "$SURF" --scrollback --lines 50

# 6. Clean up — Esc out + close workspace
cmux send-key --workspace "$WS" --surface "$SURF" escape
cmux close-workspace --workspace "$WS"
```

For multi-step TUI flows (multi-screen dialogs, follow-up pickers), repeat
steps 4-5 with appropriate `send-key` calls between (arrow keys, enter,
etc.). See the cmux skill (`~/.hermes/skills/cmux/SKILL.md`) for the
full key set.

## Bundled helper: `scripts/test-tui-feature.sh`

A wrapper script that takes the slash command as an argument and runs the
full spawn-send-read-cleanup cycle:

```bash
~/.claude/skills/test-tui-claude-feature-via-cmux/scripts/test-tui-feature.sh /advisor
~/.claude/skills/test-tui-claude-feature-via-cmux/scripts/test-tui-feature.sh /config
~/.claude/skills/test-tui-claude-feature-via-cmux/scripts/test-tui-feature.sh /model
```

The script:
1. Spawns a cmux workspace running `claude`
2. Waits for the `❯` prompt (polls read-screen with a 30s timeout)
3. Sends the slash command + Enter
4. Reads the resulting screen text
5. Cleans up the workspace
6. Exits 0 on success, 1 on timeout/error

## What this skill prevents

- 30+ minute rabbit holes reading minified JS bundles (`isFirstPartyApiBackend`,
  `xr()`, `VW()`, `oct()`, `isFirstPartyAnthropicBaseUrl`)
- Phantom-gate theorizing: "maybe the proxy is making it not first-party?"
- Adding redundant env vars to `settings.json` (e.g. `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL=1`)
  that don't change behavior
- Burning context on debug output that doesn't apply to the actual test environment
- Forgetting that the user is observing the test (cmux makes it shareable)

## When --print IS valid evidence

`--print` is fine for:

- Simple completion tasks: `claude --print "what model are you?"`
- API contract tests: tool use, file reading, error handling, schema validation
- Streaming behavior, response time, error recovery
- Anything that doesn't require a TUI slash command, dialog, picker, or status bar

**Rule of thumb**: if the question is "does this feature work in the
TUI" or "does this slash command do X" → use cmux. If the question is
"can the model do X" or "does the API return Y" → `--print` is fine.

## Common false alarms

| Symptom | Likely real cause | Test that proves it |
|---|---|---|
| `--print "/advisor"` returns "isn't available" | Normal non-interactive behavior | Open in cmux, see picker |
| `--print "/advisor"` returns 401 / auth error | OAuth or keychain issue | `claude --print "what model are you?"` — if that works, auth is fine |
| `claude` in TUI never reaches `❯` prompt | Workspace trust, settings issue | `cmux read-screen` shows what's actually on screen |
| Slash command opens but shows wrong content | Real bug — model/state issue | Reproduce in cmux, check the actual dialog |

## Verified example (2026-06-23)

**Test target**: `advisorModel: "claude-opus-4-8"` in `~/.claude/settings.json`
— was the advisor actually using Opus 4.8?

- `claude --print "/advisor"` (with and without various `ANTHROPIC_BASE_URL`
  settings) → always returned "isn't available in this environment"
- `cmux send "/advisor" + enter` in `workspace:30 surface:65` → opened the
  picker dialog showing `1. Fable 5 / ❯ 2. Opus 4.8 ✔ / 3. Sonnet 4.6 / 4. No advisor`
- The `✔` on Opus 4.8 = current selection = the `advisorModel` setting was
  being read correctly. Feature was working the whole time.

The user had to push back twice ("are you opening claude code itself and
typing `/advisor`?", "use cmux stop being lazy") before the correct test
was performed.

## References

- cmux skill: `~/.hermes/skills/cmux/SKILL.md`
- Source memory file: `~/.claude/projects/-Users-$USER-.hermes/memory/bestpractice_2026-06-23_test-tui-features-via-cmux.md`
- Wiki source page: `~/llm_wiki/wiki/sources/bestpractice-2026-06-23-test-tui-features-via-cmux.md`
- Wiki concept: `~/llm_wiki/wiki/concepts/TUISlashCommandTesting.md`
- Bead: `$USER-37uv` (closed)
- Roadmap: `~/roadmap/learnings-2026-06.md` entry dated 2026-06-23
- Claude Code binary version: 2.1.185 (verified)
