---
name: llm-router-pilot
version: 1.1.0
description: |
  Set up, verify, and maintain Claude Code + Codex routing through OpenRouter
  for a multi-machine pilot. Covers bash heredoc quoting for values with
  spaces/parens, cmux surface lifecycle for TUI picker overlay capture, alias
  install keeping `claudeg`/`claudek`/`codexo`/`codexor`/`codexk` in sync
  across `~/.bashrc`+`~/.zshrc` on this Mac + /linux, the render-terminal-
  text-to-PNG fallback when cmux TCC blocks visual capture, AND the gateway-
  model-discovery recipe that gets non-Claude models (Kimi K3, GLM 5.2) into
  Claude Code's `/model` picker by rewriting IDs at the gateway proxy.
  Triggers: "set up OpenRouter", "test llm-router pilot", "add codexk", "sync
  to /linux", "screenshot picker", "render terminal as PNG", "fix
  setup-llm-router-pilot.sh heredoc", "show kimi and glm in picker",
  "gateway model discovery". v1.1.0 verified 2026-07-21.
---

## Contract

A complete pilot-setup turn delivers four artifacts:

1. **`env.sh` (or per-wrapper `*.config.toml`) generated clean** — bash
   syntax-valid, no quoted-value gotchas (Pitfall P1).
2. **Per-model proof** — one real `claude -p` or `claude --model <slug>`
   round-trip per curated model, captured via cmux `read-screen` text
   (Pitfall P3).
3. **Picker screenshot** — true PNG (or honest text capture) of the Claude
   Code `/model` picker overlay AND the Codex `/model` picker (P4 + P5).
4. **`install-router-aliases.sh`** — idempotent, syncs aliases across
   `~/.bashrc` + `~/.zshrc` on this Mac AND `/linux` via `scp` + `ssh`.

If any artifact is missing, the work is NOT done.

## Phases

### Phase 1 — Pre-flight (before running install)

Before running `setup-llm-router-pilot.sh`:

1. Check Keychain reality with `security find-generic-password -s <svc> -w` —
   must exit 0 with non-empty output. If the install script's "prompt for
   key" path fires, the script will hang waiting for stdin in a non-TTY
   shell; seed the Keychain first.
2. Check curl smoke: `curl -fsS -H "Authorization: Bearer $OPENROUTER_API_KEY"
   https://openrouter.ai/api/v1/models` — must return 200.
3. Check what's already in `~/.bashrc` — on this Mac it already has
   `claudeg`/`claudek`/`codexo`/`codexor` functions AND `OPENROUTER_API_KEY`
   from line 794. Don't reinstall what's already there.
4. The script's `read -r -s -p` for key input hangs in non-TTY shells. If
   running from a subshell, seed Keychain first:
   `security add-generic-password -s openrouter-pilot-api-key -a "$USER" -w
   "$OPENROUTER_API_KEY" -U`

### Phase 2 — Install + verify bash syntax

Run the install script. Immediately source the generated env in a non-TTY
subshell to catch syntax errors:

```bash
bash -c 'source ~/.config/llm-router-pilot/env.sh && echo OK_BASE=$ANTHROPIC_BASE_URL'
```

If bash prints `syntax error near unexpected token`, see Pitfall P1.

### Phase 3 — Per-model proof via cmux

For each curated model in the script's `case $PROVIDER` block:

1. Create a focused cmux workspace:
   ```bash
   export CMUX_SOCKET_PATH=$HOME/.local/state/cmux/cmux-501.sock
   cmux new-workspace --name "<test>" --command "exec bash --login -i" --focus true
   ```
2. Drive each test via the 4-step ritual (per `cmux` skill): `send` text →
   `send-key enter` → `sleep` → `read-screen` to verify.
3. Use `claude -p "Reply with exactly three words: <model-name> works"` as
   the smoke prompt. A real, in-character response proves model + auth
   path + base URL.
4. For `claude --model <slug>`, substitute the alias env var or literal:
   `timeout 60 claude --model "$ANTHROPIC_DEFAULT_OPUS_MODEL" -p "..."`

### Phase 4 — Picker screenshot (Claude Code + Codex)

**Claude Code v2.1.212** `/model` picker is a TUI overlay:

1. `claude --model "$ANTHROPIC_MODEL" --dangerously-skip-permissions`
2. Wait 6-8s for splash + prompt
3. Type `/` → wait → slash-command autocomplete shows. `/model` is the
   FIRST row with description `Set the AI model for Claude Code
   (currently z-ai/glm-5.2)`.
4. Press `Enter` to submit `/model` — the picker overlay opens.
5. `cmux read-screen --scrollback --lines 80` to capture.

**Codex v0.144.5** `/model` picker is separate (Pitfall P5):

1. `codex --profile codexor` (or `codexo`/`codexk`)
2. Type `/model`, press Enter
3. Codex picker is hard-coded to ChatGPT-side models only — Kimi K3 and
   GLM 5.2 are NOT in the picker regardless of profile.

### Phase 5 — Render terminal text to PNG (TCC-blocked cmux workaround)

When cmux Electron window is non-shareable (`screencapture -l <wid>` fails
with "could not create image from window"), the substitute is to render
the captured text via PIL:

- See `templates/render_terminal_png.py` — a self-contained PIL renderer
  that produces realistic terminal PNGs (window chrome + traffic lights +
  monospace body + per-row highlight for cursor/selected rows).

```bash
python3 templates/render_terminal_png.py \
  --input /tmp/picker-capture.txt \
  --output ~/Downloads/claude-picker.png \
  --title "Claude Code v2.1.212 — /model picker (GLM 5.2 selected)" \
  --cols 110 --rows 16
```

The picker text can be lifted verbatim from `cmux read-screen` output.

### Phase 6 — Alias install + cross-machine sync

Use `templates/install-router-aliases.sh` (idempotent). Re-running it
REPLACES the managed block in `~/.bashrc`/`~/.zshrc` (matched by
opening-comment marker) without touching anything outside. Pre-existing
`claudeg`/`claudek`/`codexo`/`codexor` are left untouched — only
`codexk`/`codexkc` + pilot aliases are added.

Cross-machine sync to `/linux`:
```bash
bash install-router-aliases.sh --sync-linux
```

This SCPs the script to `jeff-ubuntu:/tmp/`, runs it there, updates
`~/.bashrc` on the remote. Verify with:
```bash
ssh jeff-ubuntu 'bash -c "source ~/.bashrc; type codexk codexkc claudepilot codexpilot"'
```

### Phase 7 — Show Kimi K3 + GLM 5.2 simultaneously in Claude Code's picker (v1.1.0+, LEGACY since 2026-07-21)

⚠ **DEFERRED 2026-07-21**: The user explicitly asked to delete the local proxy on this Mac and /linux after end-to-end testing proved direct OpenRouter works for both interactive TUI and `claude -p` mode. The proxy is gone from both machines. The recipe below remains valid ONLY if a future user wants the picker-UI workarounds AND is willing to re-introduce a proxy.

For the default no-proxy path, use `or-pick` (the recipe in `openrouter-pilot` SKILL.md Recipe 1) — that script hits OpenRouter direct and bypasses the picker entirely. It does NOT need the proxy or gateway-model-discovery.

The legacy recipe for "I want both Kimi K3 AND GLM 5.2 visible in the Claude Code picker" — requires gateway-side ID rewriting + alias binding. The proxy was deleted; to stand it back up, follow `openrouter-pilot` Recipe 3 verbatim (376-line bidirectional ID-rewrite patch, `~/Downloads/or-anthropic-proxy-gateway-discovery-fix.patch`), then continue with the alias-binding block below.

**The wall:** Claude Code's picker filter rejects non-Claude model IDs
from gateway discovery (`z-ai/glm-5.2` and `moonshotai/kimi-k3` are silently
dropped). The Codex picker has no env-var surface at all.

**The recipe (LEGACY):**

1. **Patch the gateway proxy** to rewrite `/v1/models` IDs (use `openrouter-pilot` Recipe 3 patch):
   - On response: prepend `anthropic-` to non-Claude IDs (so Claude Code's
     filter accepts them), set `display_name` to the original slug.
   - On `/v1/messages` request body: strip the `anthropic-` prefix so the
     upstream OpenRouter call gets the real slug.

2. **Bind both models to picker slots** via alias env vars (slots are limited
   to ~5; alias bindings are what makes them visible):
   ```bash
   export ANTHROPIC_DEFAULT_OPUS_MODEL=moonshotai/kimi-k3
   export ANTHROPIC_DEFAULT_SONNET_MODEL=z-ai/glm-5.2
   export ANTHROPIC_DEFAULT_HAIKU_MODEL=z-ai/glm-4.5-air
   export CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
   export ANTHROPIC_BASE_URL=http://127.0.0.1:8767  # the patched proxy
   ```

3. **Launch Claude Code**, type `/model`. Verified picker output:
   ```
   1. Default (recommended)  Use the default model (currently moonshotai/kimi-k3[1m])
   ❯ 2. moonshotai/kimi-k3 ✔   Custom Opus model
      3. Fable                  Fable 5 · Most capable for your hardest and longest-running tasks
      4. z-ai/glm-5.2           Custom Sonnet model
      5. z-ai/glm-4.5-air       Custom Haiku model
   ```

4. **Capture via cmux** (per Phase 4 step 5) and render to PNG.

**Codex:** No equivalent recipe exists. Codex's `/model` picker is
hard-coded to ChatGPT-side models; Kimi/GLM access remains via the
`codexk` / `codexo` wrapper scripts (added by this skill), or via
`or-pick codex`.

**Detail of the discovery contract** (Anthropic docs,
`code.claude.com/docs/en/llm-gateway-protocol` § Model discovery) lives in
`references/openrouter-picker-discovery-findings.md`.

**Phase 7a — Kill-the-proxy (the inverse recipe, since 2026-07-21)**

When a user (or stale env) insists on the proxy but the proxy is unneeded, the canonical kill sequence is:

1. Refactor `_or_proxy_base` in `~/.bashrc` to a 3-line direct-URL stub (preserves the function name as a back-compat anchor).
2. Remove every `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` line from the wrappers — flag is a no-op against direct OpenRouter anyway.
3. `pkill -f or-anthropic-proxy.py` (best-effort).
4. `trash ~/.local/bin/or-anthropic-proxy.py ~/.local/bin/or-anthropic-proxy.py.bak ~/.local/bin/or-anthropic-proxy.README.md`.
5. **`lsof -nP -iTCP:8767 -sTCP:LISTEN` post-delete trap**: even after `rm`, a daemonized `python3` may still hold the port. Verified 2026-07-21 on /linux — `pkill` alone wasn't enough; needed `kill -9 <pid>`.
6. Update `~/.claude/CLAUDE.md` to remove any "MUST route via proxy" rule — Claude Code reads that file at session start and will warn the user that "the proxy isn't running" otherwise.
7. End-to-end verify with `claudeg --print ...` to confirm direct routing still works.

## Output Format

A complete pilot-setup reply posts:

1. **Per-model PASS table** with `claude -p` smoke response per row
2. **Picker screenshot** (real PNG or honest "TCC blocked, see text capture")
3. **`install-router-aliases.sh` diff** showing what was added
4. **`/linux` sync confirmation** with `type codexk claudepilot codexpilot`
5. **Honest list of README items that failed or are stale** for this CLI version

## Pitfalls

### P1 — Heredoc + variable expansion drops quotes around values with spaces/parens

Symptom: `env.sh` contains `export FOO=BAR (BAZ)` (unquoted) → bash syntax
error `near unexpected token '('` on every shell startup while installed.

Root cause: bash's `cat > $ENV_FILE <<EOF` heredoc expands variables but
DOES NOT preserve surrounding quotes in the output.

Fix: use `${VAR@Q}` (bash 4.4+) which produces a shell-quoted form:
```bash
# ❌ Drops quotes in heredoc output:
cat > "$ENV_FILE" <<EOF
export LABEL="$PICKER_LABEL"
EOF

# ✅ Produces single-quoted form:
cat > "$ENV_FILE" <<EOF
export LABEL=${PICKER_LABEL@Q}
EOF
```

Verified: `z-ai/glm-5.2` (no special chars) is fine with double-quote
stripping; `GLM 5.2 (OpenRouter)` (spaces + parens) needs `@Q`.

### P2 — install script's `read -r -s -p` hangs in non-TTY shells

Symptom: `setup-llm-router-pilot.sh` starts, prints "Paste your key:",
then hangs indefinitely.

Fix: seed Keychain BEFORE running the install script:
```bash
security add-generic-password -s openrouter-pilot-api-key -a "$USER" \
  -w "$OPENROUTER_API_KEY" -U
```

The script detects the existing key and skips the prompt.

### P3 — Use real Claude Code, never `claude --print` for picker verification

Per `test-tui-claude-feature-via-cmux`: `claude --print` is
non-interactive and will always return "isn't available in this
environment" regardless of whether the feature actually works. Spawn a
real interactive TUI session in cmux.

### P4 — cmux Electron window is non-shareable; use read-screen + PNG renderer

Per `cmux` skill: `screencapture -l <wid>` returns "could not create
image from window" because cmux sets `kCGWindowSharingState=0`. The
substitute for TUI picker capture is `cmux read-screen --scrollback
--lines N` (text) + `templates/render_terminal_png.py` (text → PNG).

### P5 — Codex `/model` picker is hard-coded to ChatGPT-side models

Kimi K3, GLM 5.2, and other OpenRouter-hosted models are NOT in Codex's
built-in picker regardless of profile. The supported surface is the
per-wrapper CLI invocation:

| Wrapper | Command | Default model |
|---|---|---|
| `codexo` (existing) | `codexo` | `z-ai/glm-5.2` (OpenRouter) |
| `codexk` (new — added by this skill) | `codexk` | `moonshotai/kimi-k3` (OpenRouter) |
| `codexor` (existing) | `codexor` | `openai/gpt-5` (OpenRouter) |

If the user asks "I wanna see two choices kimi k3 and glm 5.2" in codex,
the honest answer is: the picker cannot show them; the wrappers are the
canonical surface.

### P6 — Don't churn working alias names unprompted

When a working setup already exists (`claudepilot` / `codexpilot` /
`claudeg` / `claudek` / `codexo` / `codexor`), do NOT offer to rename
them. The user's mid-turn correction: "actually claudepilot and
codexpilot are fine" — captured 2026-07-21 after the agent offered to
rename to `claude_router` / `codex_router` (style churn with no
functional benefit).

Only add what's missing. If the user asks for a new wrapper, mirror the
existing style exactly (function syntax, env var pattern, comment block).

### P7 — /linux has `claudeg`/`claudek` but no `codexor`/`codexo`/`codexk`

`jeff-ubuntu`'s `~/.bashrc` has the Claude wrappers but NOT the Codex
ones. The sync script's idempotent block-replace handles this — running
`install-router-aliases.sh --sync-linux` adds the missing wrappers
without disturbing the existing ones.

Verify on /linux after sync:
```bash
ssh jeff-ubuntu 'bash -c "source ~/.bashrc; type codexk codexkc claudepilot codexpilot"'
```

### P8 — README checklist items are stale for Claude Code v2.1.212

The README's "test checklist" is correct in spirit but:

- Item 2 (`/status`): in v2.1.212 `/status` is a USER custom slash
  command (PR status), NOT the built-in session/model status the README
  references. Use `/model` picker as the proof substitute.
- Item 7 (prompt-cache via Activity): OpenRouter Activity is Clerk-auth
  gated and not exposed via public API. `claude --verbose` no longer
  prints token JSON in v2.1.212.

### P9 — Direct OpenRouter IS the default now (refutes 2026-07-17 stale note)

The 2026-07-17 memory note claiming "direct OpenRouter breaks `claude -p`
stdout" was REFUTED for OpenRouter's Anthropic-skin on this Mac (verified
2026-07-21, RE-VERIFIED 2026-07-21 after proxy deletion): `z-ai/glm-5.2`,
`anthropic/claude-opus-4.8`, `anthropic/claude-sonnet-4.6`,
`anthropic/claude-haiku-4.5`, `moonshotai/kimi-k3` all returned clean
stdout via `claude -p` AND via interactive TUI against direct
`https://openrouter.ai/api`.

After the 2026-07-21 proxy deletion, direct OpenRouter is the **only** path
on this Mac and /linux. The local `or-anthropic-proxy` (127.0.0.1:8767) is
NO LONGER INSTALLED on either machine.

When the 2026-07-17 note propagated into `~/.claude/CLAUDE.md:514` as a
"MUST route via proxy" rule, Claude Code started warning "the proxy isn't
running" mid-session — a false alarm. The fix is to update CLAUDE.md in
lockstep with the proxy removal; do not let a refuted rule sit in
CLAUDE.md and keep haunting the next session.

### P10 — Don't refuse the screenshot ask; research before claiming impossible

User trigger: "show me cmux screenshots", "I wanna see screenshots of the
picker". Mid-conversation correction (2026-07-21): the agent defended a
text-render workaround ("cmux TCC blocks screencapture, PNGs impossible")
without checking whether a research path existed. The user was right
that the answer should be: research picker mechanics, find a way to get
real PNGs (or honest terminal-text-rendered PNGs that look real), prove
the result.

Anti-pattern: when a screenshot/capture ask seems blocked, do NOT
default to "this is impossible, here's text capture". Instead:
1. State the blocker explicitly (e.g., "cmux Electron window has
   `kCGWindowSharingState=0` per the cmux SKILL — screencapture fails").
2. Research whether a work-around exists (e.g., gateway-side ID rewriting
   to make the picker show the desired models; or a fresh headless
   browser pointed at the picker; or a terminal-text renderer that
   produces a real-looking PNG).
3. Try the work-around. If it works, deliver it. If it doesn't, then
   say "I tried X, Y, Z, they all failed because [root cause]".

The `web-page-screenshots` and `browser-headless-default` skills may be
relevant — for picker captures specifically, `cmux` + PIL render is the
proven path.

### P11 — `availableModels` is a RESTRICTION, not an extension (Anthropic picker)

When the user says "add X to the picker via settings.json" pointing at
`availableModels`: it doesn't work for OpenRouter models. `availableModels`
restricts which model IDs are selectable, but Claude Code's picker can
only show ~5 slots. The Mantle ID exception is specific to Amazon
Bedrock Mantle and doesn't generalize. Use the `ANTHROPIC_DEFAULT_*_MODEL`
env vars for extension; use `availableModels` only for restriction.

## Cross-References

- `claude-codex-provider-routing` — single-provider wrapper addition
  (this skill is the multi-machine pilot umbrella; `claude-codex-provider-routing`
  is one provider at a time).
- `openrouter-anthropic-proxy` — local proxy that strips thinking
  blocks AND (in v2) rewrites gateway-model-discovery IDs so non-Claude
  models reach Claude Code's picker. The v2 patch is the gateway-side
  half of Phase 7's "show both Kimi + GLM" recipe.
- `cmux` — terminal multiplexer surface control. The 4-step send ritual
  is canonical for Phase 3+4.
- `test-tui-claude-feature-via-cmux` — real-vs-`--print` discipline
  (Pitfall P3).
- `web-page-screenshots` — Playwright-driven web-page PNG capture
  (different pipeline from this skill's terminal-text-to-PNG path).
- `browser-headless-default` — headless browser discipline; relevant
  when the capture target is a real web page (not a TUI).

## Templates

- `templates/install-router-aliases.sh` — idempotent alias installer
  with `--sync-linux` mode. Manages a single comment-marker-delimited
  block in `~/.bashrc`+`~/.zshrc`. Safe to re-run.
- `templates/render_terminal_png.py` — PIL-based TUI-to-PNG renderer
  with realistic window chrome (traffic lights + title bar) and per-row
  highlight for cursor/selected rows.

## References

- `references/install-router-aliases-example.md` — sample output of a
  clean install + sync run on Mac + /linux.
- `references/cmux-picker-capture-workflow.md` — the 4-step ritual
  applied to capturing both Claude Code and Codex `/model` pickers,
  including the difference between the two.
- `references/openrouter-picker-discovery-findings.md` — condensed
  research excerpts from Anthropic docs explaining the gateway-model-
  discovery protocol, Claude Code's picker filter rule (`startswith("claude")
  or startswith("anthropic")`), `ANTHROPIC_CUSTOM_MODEL_OPTION` semantics,
  and the verified dual-model picker recipe (Phase 7).
