# TUI Feature Testing Recipe — "does /feature work in Claude Code?"

**When this applies:** user asks "verify /advisor works", "does /config show X",
"is the /model picker picking the right model", or any "does Claude Code
TUI feature X work" question. The "feature" is implemented as a TUI slash
command, dialog, picker, or status indicator — anything that's part of the
Ink TUI, not the CLI.

## The trap: `claude --print` is not a test

`--print` is non-interactive. Slash commands have no `--print` representation.
The binary's response to **any** TUI slash command in `--print` mode is:

> `/<feature> isn't available in this environment.`

That error specifically means "I cannot show you this in non-interactive
mode," **not** "this feature is broken." Treating it as a feature-gate
failure leads to:

- 30+ minute rabbit holes reading minified JS bundles
  (`isFirstPartyApiBackend`, `xr()`, `VW()`, `oct()`,
  `isFirstPartyAnthropicBaseUrl`)
- Phantom-gate theorizing: "maybe the proxy is making it not first-party?"
- Adding redundant env vars to `settings.json`
  (e.g. `_CLAUDE_CODE_ASSUME_FIRST_PARTY_BASE_URL=1`) that don't change behavior
- Burning context on debug output that doesn't apply to the actual test env

The cmux skill (and a dedicated `test-tui-claude-feature-via-cmux` skill) is
the right tool. Load the dedicated skill first; fall back to the cmux recipe
inline.

## The full recipe (verified end-to-end on 2026-06-23)

```bash
export CMUX_SOCKET_PATH=/private/tmp/cmux-debug-may-18.sock

# 1. Spawn fresh Claude Code workspace
WS_OUT=$(cmux new-workspace --cwd "$PWD" --command "claude" 2>&1)
WS=$(echo "$WS_OUT" | grep -oE 'workspace:[0-9]+' | head -1)
# Example output: "Created workspace:31" → WS=workspace:31

# 2. Discover the surface (always re-discover; never hardcode from prior session)
sleep 2
SURF=$(cmux list-pane-surfaces --workspace "$WS" 2>/dev/null \
       | grep -oE 'surface:[0-9]+' | head -1)
# Example: SURF=surface:66

# 3. Wait for the `❯` prompt (poll, up to 30s)
READY=0
for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  SCREEN=$(cmux read-screen --workspace "$WS" --surface "$SURF" \
           --scrollback --lines 30 2>/dev/null)
  if echo "$SCREEN" | grep -q "❯"; then READY=1; break; fi
  sleep 2
done
[ "$READY" -eq 1 ] || { echo "claude never reached ❯ prompt"; exit 1; }

# 4. Send the slash command + press Enter
cmux send --workspace "$WS" --surface "$SURF" "/<feature>"
cmux send-key --workspace "$WS" --surface "$SURF" enter

# 5. Read the dialog/picker/result
sleep 2
cmux read-screen --workspace "$WS" --surface "$SURF" --scrollback --lines 50

# 6. Clean up
cmux send-key --workspace "$WS" --surface "$SURF" escape
cmux close-workspace --workspace "$WS"
```

For multi-step TUI flows (multi-screen dialogs, follow-up pickers), repeat
steps 4-5 with appropriate `send-key` calls between (arrow keys, enter, etc.).

## The surface-rediscovery pitfall (verified 2026-06-23)

I almost hardcoded `surface:65` in the helper script header because that's
what I had in a prior workspace. The new spawn returned `surface:66`. The
helper script now always re-discovers the surface from `list-pane-surfaces`
output — never trust a surface number from a prior session.

**Why this matters:** `cmux list-pane-surfaces` returns surfaces for the
**current** workspace's first pane, not the most recently created surface
across the whole window. Two workspaces can coexist with overlapping
surface numbers (e.g., `workspace:30 surface:65` from a session 30
minutes ago, and `workspace:31 surface:66` from a fresh spawn). If you
hardcode a surface number from a prior workspace, you may either:

- Get a different surface than intended (misroute)
- Get an `Error: invalid_params: Surface is not a terminal` if the ref
  doesn't exist in the current workspace
- Get the right ref by coincidence (lucky, but not reliable)

**Always re-discover.** Cost is one extra `cmux list-pane-surfaces` call
(< 200ms).

## The non-interactive-mode detector

After step 5, check whether the screen output contains the literal
"isn't available in this environment" string. **If it does, something is
wrong** — you ARE in an interactive TUI session, so a slash command should
have rendered a dialog/picker/menu, not that error. The most likely cause
is that the slash command text was malformed (typo, missing slash) or
that the `❯` prompt wasn't actually ready (race condition). The helper
script exits 2 with the message "Slash command produced no visible
output" or "ERROR: slash command returned non-interactive error despite
being in TUI" — both are actionable signals.

## Worked example: /advisor with Opus 4.8 (2026-06-23)

**Test target:** `advisorModel: "claude-opus-4-8"` in `~/.claude/settings.json`
— was the advisor actually using Opus 4.8?

**Test execution:**

```
$ ~/.claude/skills/test-tui-claude-feature-via-cmux/scripts/test-tui-feature.sh /advisor

>>> Spawning claude in cmux workspace...
    workspace: workspace:31
    surface: surface:66
>>> Waiting for claude to be ready...
    ready (prompt visible)
>>> Sending: /advisor
>>> Screen after /advisor:
---
claude
Last login: Tue Jun 23 17:25:07 on ttys059
You have new mail.
$USER@Mac:~$ claude
 ▐▛███▜▌   Claude Code v2.1.185
▝▜█████▛▘  Opus 4.8 (1M context) with high effort · Claude Max
  ▘▘ ▝▝    $HOME


❯ /advisor

───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
  Advisor (experimental)

  When Claude needs stronger judgment — a complex decision, an ambiguous failure, a problem it's circling without progress — it escalates to the
  advisor model for guidance, then resumes. The advisor runs server-side and uses additional tokens.

    1. Fable 5
  ❯ 2. Opus 4.8 ✔
    3. Sonnet 4.6
    4. No advisor

  Recommended setup: Sonnet as the main model with Opus as the advisor. For certain workloads this gives near-Opus performance with reduced token
  usage.

  Learn more: https://claude.com/blog/the-advisor-strategy

  Enter to confirm · Esc to cancel
---
>>> OK
```

**Verdict:** The picker shows `❯ 2. Opus 4.8 ✔` — the `❯` is the cursor
on the current selection and the `✔` confirms it's the active advisor
model. The `advisorModel: "claude-opus-4-8"` setting in
`~/.claude/settings.json` was being read correctly the whole time. The
feature was working. The 20-minute earlier failure mode (reading
minified binary strings, guessing at gates, trying env-var combinations)
was a complete waste — the user had to push back twice ("are you opening
claude code itself and typing /advisor?", "use cmux stop being lazy")
before the correct test was performed.

## When --print IS valid evidence (don't over-correct)

`--print` is fine for:

- Simple completion tasks: `claude --print "what model are you?"`
- API contract tests: tool use, file reading, error handling, schema validation
- Streaming behavior, response time, error recovery
- Anything that does NOT involve a TUI slash command, dialog, picker, or status bar

**Rule of thumb:** if the question is "does this feature work in the TUI"
or "does this slash command do X" → use cmux. If the question is
"can the model do X" or "does the API return Y" → `--print` is fine.

## Reference: the dedicated skill

`~/.claude/skills/test-tui-claude-feature-via-cmux/`:

- `SKILL.md` — the class-level "test TUI features via cmux" skill
- `scripts/test-tui-feature.sh` — one-liner wrapper around the recipe above
- `tests/test_test-tui-feature.sh` — 6/6 unit tests (argument validation,
  socket detection, `isn't available` detector)

**Load the dedicated skill when the user asks "does /feature work"** —
it has the helper script, the unit tests, and a worked example inline,
which is more efficient than re-deriving the recipe from this reference
each time.
