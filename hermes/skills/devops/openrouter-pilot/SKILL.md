---
name: openrouter-pilot
description: "Route Claude Code and Codex through OpenRouter (Anthropic-Messages + OpenAI-Responses endpoints) directly without local proxies. Use when the user wants to test/use open models (GLM, Kimi, Qwen, etc.) or frontier models (Claude, GPT) under a single OpenRouter API key, when proxies are forbidden, when Codex/Claude model picker needs workarounds, or when the user references `or-pick` / `claudeg` / `claudek` / `codexo` / `codexor` / `codexk` wrapper aliases. Encodes the no-proxy preference and the picker-mechanism workarounds documented in Slack thread C09GRLXF9GR/p1784672360.870519."
when_to_use: User asks for OpenRouter, multi-provider Claude/Codex routing, open-model evaluation, or wants to switch Claude/Codex away from a proxy
allowed-tools: terminal, edit, Bash, Read, Write
context: hermes
---

# OpenRouter Pilot (no-proxy direct routing)

**Core principle: hit `https://openrouter.ai/api` (Anthropic-Messages) and `https://openrouter.ai/api/v1` (OpenAI-Responses) direct. No proxy.** The user's 2026-07-21 explicit preference: *"I do not want to need to install proxies or anying, just hit openrouter endpoint directly"*.

This skill covers three recipes, ordered by simplicity:

1. **`or-pick`** — interactive picker script (preferred — no env-var juggling)
2. **Wrapper aliases (`claudeg`, `claudek`, `codexo`, `codexk`)** — direct env exports
3. **`or-anthropic-proxy` patch** — only if Claude Code picker UI must show non-Claude model rows

## Recipe 1 — `or-pick` (the default, install this)

A single-file bash script at `~/Downloads/or-pick` (~9.3 KB) that:

1. Asks which tool: Claude Code vs Codex
2. Asks which model (per-tool curated list)
3. Sets env vars + `exec claude` / `exec codex`

```bash
# Install
cp ~/Downloads/or-pick ~/.local/bin/or-pick && chmod +x ~/.local/bin/or-pick

# Use
or-pick                # interactive
or-pick claude         # 7 choices (3 open + 3 Claude + default)
or-pick codex          # 3 choices (2 GPT via OpenRouter + default)
or-pick --list         # print curated choices, no exec
or-pick claude -m "..."  # passes -m flag to claude
```

The Claude side just sets 3 env vars and `exec claude`:
```bash
ANTHROPIC_BASE_URL=https://openrouter.ai/api
ANTHROPIC_AUTH_TOKEN=$OPENROUTER_API_KEY
ANTHROPIC_API_KEY=$OPENROUTER_API_KEY
ANTHROPIC_MODEL=<slug>
```

The Codex side writes a tiny profile file on first run (`~/.codex/orpick.config.toml`, 305 bytes) and runs:
```bash
codex --profile orpick --model <slug>
```
The profile sets `model_provider = "openrouter"` so Codex uses BYOK (`env_key = "OPENAI_API_KEY"`) instead of the user's saved ChatGPT login in `~/.codex/auth.json`.

**Without the profile, Codex errors:** *"The 'openai/gpt-5.5' model is not supported when using Codex with a ChatGPT account"* — because v0.144.5 prefers the saved ChatGPT token over `OPENAI_API_KEY` env. The profile file is the workaround.

### Curated model menu (edit `or-pick` to add)

Claude side (7 choices):
- `z-ai/glm-5.2` — Z.AI GLM 5.2 (current "open model under eval")
- `moonshotai/kimi-k3` — Moonshot Kimi K3
- `z-ai/glm-4.5-air` — cheaper open
- `anthropic/claude-opus-4.8` — real Opus 4.8 via OpenRouter
- `anthropic/claude-sonnet-4.6`
- `anthropic/claude-haiku-4.5`
- `__default-claude__` — fall back to user's own Anthropic login (env-unset)

Codex side (3 choices):
- `openai/gpt-5.5` — default codex via OpenRouter Responses
- `openai/gpt-5` — older default via OpenRouter
- `__default-codex__` — fall back to user's own ChatGPT login (env-unset)

## Recipe 2 — wrapper aliases in `~/.bashrc`

If the user prefers shell functions (already established for `claudeg`/`claudek`/`codexo`/`codexor`):

```bash
# ~/.bashrc
claude_or() {
  ANTHROPIC_BASE_URL="https://openrouter.ai/api" \
  ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY" \
  ANTHROPIC_API_KEY="$OPENROUTER_API_KEY" \
  ANTHROPIC_MODEL="${1:-anthropic/claude-sonnet-4.6}" \
  exec claude --dangerously-skip-permissions --effort high "${@:2}"
}

codex_or() {
  OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
  OPENAI_API_KEY="$OPENROUTER_API_KEY" \
  command codex --profile orpick --model "${1:-openai/gpt-5.5}" "${@:2}"
}
```

Mirror into `~/.zshrc` (zsh is the default macOS shell; the user's existing `claudeg`/`claudek`/`codexo` are bash-only in `~/.bashrc`).

## Recipe 3 — picker-UI workarounds (LEGACY / OPTIONAL — only if the picker MUST show non-Claude models)

⚠ **DEFERRED 2026-07-21**: The user explicitly asked to delete the local proxy after end-to-end testing proved direct OpenRouter works for both interactive TUI and `claude -p` mode. The `or-anthropic-proxy` is no longer installed on this Mac or /linux (binary deleted, port 8767 listener confirmed dead).

The recipe below is **kept for reference only** — if a future user asks for picker-UI workarounds AND the proxy isn't there, follow this recipe to stand one back up. The pattern is also valid for users who explicitly request a proxy for other reasons (e.g., log capture, thinking-block stripping for non-Kimi reasoning models).

Claude Code's `/model` picker has **5 visible slots**: Default + Opus + Sonnet + Haiku + Fable. Each slot binds via `ANTHROPIC_DEFAULT_OPUS_MODEL` / `_SONNET_MODEL` / `_HAIKU_MODEL`. The picker is NOT hard-coded to Claude-native — it accepts any model id via `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1`, which calls `GET /v1/models` on the gateway.

**Hard wall:** Claude Code filters `/v1/models` entries by `id.startswith("claude") or "anthropic"`. OpenRouter returns `z-ai/glm-5.2`, `moonshotai/kimi-k3`, etc. — these are DROPPED.

**Workaround** (proxy rewrite): patch `~/.local/bin/or-anthropic-proxy.py` to:
- Prefix non-Claude IDs in `/v1/models` responses with `anthropic-` so the filter passes
- Strip the prefix from the `model` field in `/v1/messages` request bodies before forwarding to OpenRouter

The patch is saved as `~/Downloads/or-anthropic-proxy-gateway-discovery-fix.patch` (376 lines, +278/-33). Bidirectional: response rewrite + request unwrap.

**Then set the alias env vars:**
```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8767           # the patched proxy
ANTHROPIC_AUTH_TOKEN=$OPENROUTER_API_KEY
CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1
ANTHROPIC_DEFAULT_OPUS_MODEL=moonshotai/kimi-k3   # ← picker row 2
ANTHROPIC_DEFAULT_SONNET_MODEL=z-ai/glm-5.2       # ← picker row 4
ANTHROPIC_DEFAULT_HAIKU_MODEL=z-ai/glm-4.5-air
```

The picker will then show BOTH Kimi K3 and GLM 5.2 simultaneously.

**Codex picker is hard-coded to ChatGPT-side models.** No env var, no config knob, no `/v1/models` discovery can add Kimi/GLM. They are accessed only via `--profile codexo`/`--profile codexk` wrappers (or `codex --profile orpick -m <slug>` from `or-pick`).

## Disabled on this machine + /linux (2026-07-22, durable user preference)

User typed: *"lets disable claudeg and codexg in bashrc and all the openrouter functions/alias on this machine and /linux and check if cmux or warp terminal is using it"*. Verified 2026-07-22 and treated as a durable per-machine decision, not a one-off ask.

Removed/disabled on Mac (`$HOME`):
- All OpenRouter functions/aliases/exporters in `~/.bashrc` (`claudeg`/`claudegc`, `claudeor`/`claudeorop`/`claudeoroc`/`claudeoropc`, OpenRouter-backed `claudeo`/`claudeoc`, `claudek`/`claudekc`, `codexo`/`codexoc`, `codexor`/`codexorc`, `codexk`/`codexkc`, `_or_proxy_base`, `openrouter-check`, `claudepilot*`, `codexpilot*`) — backed up at `~/.bashrc.pre-openrouter-disable-20260722T222751Z.bak` (mode 600).
- Duplicate OpenRouter blocks in `~/.zshrc` — backed up at `~/.zshrc.pre-openrouter-disable-20260722T222751Z.bak`.
- `OPENROUTER_API_KEY`, `OR_ANTHROPIC_PROXY_PORT`, and DEEPSEEK-via-OpenRouter exports in `~/.profile` — backed up at `~/.profile.pre-openrouter-disable-20260722T222751Z.bak`.
- Standalone OpenRouter executables moved to `~/.disabled/openrouter-20260722T223018Z/`: `claudeor`, `claudeorop`, `codexor`, `codexorc`, `or-pick`.
- zsh startup rewritten to import ONLY `export VAR=...` lines from `~/.bashrc` instead of `source`-ing bash-only functions.
- One active cmux GLM/OpenRouter session terminated (workspace `workspace:43` / surface `surface:46`, pid 89858 — was using `127.0.0.1:8767` + `z-ai/glm-5.2`).
- One inherited `CLAUDEG_MODE=1` background MCP service terminated (pid 19396).

Removed/disabled on Linux (`jeff-ubuntu`):
- All OpenRouter functions/aliases/exporters in `~/.bashrc` — backed up at `~/.bashrc.pre-openrouter-disable-20260722T222759Z.bak`.
- `or-pick` standalone moved to `~/.disabled/openrouter-20260722T223018Z/or-pick`.
- Linux's `claudeo=claudedo` and `claudeoc=claudedco` direct-Opus aliases **PRESERVED** (they were never OpenRouter-routed).

**Consequence for this skill:** `openrouter-pilot` is no longer the active route on either machine. Future sessions that load this skill via `skill_view` or trigger match should treat the install recipes as **REFERENCE-ONLY** — running them will re-install wrappers and aliases that the user explicitly removed. If a future task requires OpenRouter on either host, ASK the user first; restoring the bashrc from the timestamped backup is a destructive operation that crosses the user's durable preference. The `~/.disabled/openrouter-<ts>/` directory is the durable record of the disabled binaries; do not move them back to PATH without explicit user approval.

## Refactor recipe — replace an `_or_proxy_base` stub function (no-regression back-compat)

If you previously wired wrappers through a function like `_or_proxy_base` that auto-spawned the proxy, and want to switch to direct OpenRouter without rewriting every wrapper that references the function:

```bash
# BEFORE: 17-line function with proxy auto-spawn
_or_proxy_base() {
  local proxy_up=0
  if [ "${OR_PROXY_DISABLED:-0}" != "1" ]; then
    if ! lsof -nP -iTCP:${OR_ANTHROPIC_PROXY_PORT:-8767} -sTCP:LISTEN >/dev/null 2>&1; then
      LISTEN_PORT="${OR_ANTHROPIC_PROXY_PORT:-8767}" nohup python3 "$HOME/.local/bin/or-anthropic-proxy.py" >/tmp/or-anthropic-proxy.log 2>&1 </dev/null &
      disown 2>/dev/null || true
    fi
    for _i in 1 2 3 4 5 6 7 8 9 10; do
      if lsof -nP -iTCP:${OR_ANTHROPIC_PROXY_PORT:-8767} -sTCP:LISTEN >/dev/null 2>&1; then proxy_up=1; break; fi
      sleep 0.3
    done
  fi
  if [ "$proxy_up" = "1" ]; then echo "http://127.0.0.1:${OR_ANTHROPIC_PROXY_PORT:-8767}"; else echo "https://openrouter.ai/api"; fi
}

# AFTER: 3-line direct stub (preserves function name as a back-compat anchor)
_or_proxy_base() {
  # Direct OpenRouter (no proxy). Behavior changed 2026-07-21 after
  # end-to-end testing showed direct works for all curated models.
  echo "https://openrouter.ai/api"
}
```

Then also remove `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` lines from wrappers — the flag is a no-op against direct OpenRouter because OpenRouter returns `z-ai/glm-5.2` etc. (not `claude`/`anthropic`-prefixed), so Claude Code's filter drops them anyway.

## Kill-the-proxy recipe (when going from Recipe 3 back to Recipe 1/2)

1. Refactor `_or_proxy_base` to a direct stub (per refactor recipe above).
2. Remove `CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY=1` from every wrapper:
   - On this Mac: 6 occurrences across `claudeg` / `claudek` / `claudeor` / `claudeorop` / `claudegz` / `claudem`.
   - On /linux: 4 occurrences (same set, except `claudem`).
   - Use the python pattern in `scripts/clean-discovery-flag.py` (handles both Mac-style `\` + newline AND /linux-style `\` + literal `n` artifact).
3. `pkill -f or-anthropic-proxy.py` — kills the running listener.
4. `trash ~/.local/bin/or-anthropic-proxy.py ~/.local/bin/or-anthropic-proxy.py.bak ~/.local/bin/or-anthropic-proxy.README.md` — delete the binary + backup + README.
5. **Stale daemon trap**: even after `rm`/`trash`, a daemonized `python3` child process may STILL be listening on port 8767. Verify with `lsof -nP -iTCP:8767 -sTCP:LISTEN` and `kill -9 <pid>` if anything shows up. (Verified 2026-07-21 on /linux — `pkill` alone wasn't enough on the first attempt.)
6. Update `~/.claude/CLAUDE.md` to remove any "MUST route via proxy" rule — Claude Code reads that file at session start and will warn the user that "the proxy isn't running" even though it's not needed.
7. End-to-end verify: `claudeg --print --dangerously-skip-permissions --effort high --output-format text "test"` should produce stdout via direct OpenRouter (no proxy). If `claude -p` (the alleged broken case from the 2026-07-17 stale note) prints cleanly, the refactor is verified.

## End-to-end live proof pattern

```
or-pick → tool=Claude → model=Kimi K3 → Claude Code boots with `moonshotai/kimi-k3 with high ... · API Usage Billing` →
  prompt "reply with exactly: kimi pick works" → response "kimi pick works"
or-pick → tool=Codex → model=GPT-5.5 → codex boots with `openai/gpt-5.5 high` →
  prompt "reply with exactly three words: codex or pick works" → response "codex pick works"
```

Captured via cmux read-screen (text) + PIL render to PNG (no Chrome, no focused window).

## Files

- `~/Downloads/or-pick` — single-file bash script (the canonical install)
- `~/Downloads/or-anthropic-proxy-gateway-discovery-fix.patch` — proxy patch (376 lines)
- `~/Downloads/setup-llm-router-pilot-line137-quoting-fix.patch` — env.sh heredoc quoting bug (1 line)
- `~/Downloads/install-router-aliases.sh` — idempotent alias installer (sync to /linux via `--sync-linux`)
- `~/.codex/orpick.config.toml` — auto-created on first codex launch (305 B)
- `~/.codex/codexo.config.toml`, `~/.codex/codexor.config.toml`, `~/.codex/codexk.config.toml` — pre-existing per-model profiles

## Key gotchas (DO NOT skip)

1. **Codex v0.144.5 prefers saved ChatGPT token over `OPENAI_API_KEY`.** Always use `--profile orpick` (or one of `codexo`/`codexor`/`codexk`) so the profile's `env_key` activates. Bare `codex --model ...` errors with *"model is not supported when using Codex with a ChatGPT account"*.

2. **Codex Responses API vs Chat Completions.** OpenRouter's `/v1/responses` is verified working; `wire_api = "responses"` is the default in the profiles. If a model errors on Responses, edit the profile to `wire_api = "chat"` (most other providers need this — OpenRouter doesn't).

3. **`ANTHROPIC_CUSTOM_MODEL_OPTION_NAME` value contains spaces/parens.** When writing to `~/.config/llm-router-pilot/env.sh` via heredoc, bash strips the surrounding double-quotes during variable expansion. Use `${PICKER_LABEL@Q}` (bash 4.4+) for shell-quoted form. The bug produces `export ANTHROPIC_CUSTOM_MODEL_OPTION_NAME=GLM 5.2 (OpenRouter)` (unquoted) → syntax error on every shell startup.

4. **Claude Code startup banner always says "Claude Opus 4 was retired on June 15, 2026"** for Anthropic-skin models routed through OpenRouter, because Claude Code assumes Anthropic-direct. Cosmetic — model still responds correctly.

5. **OpenRouter key lives in Keychain on macOS** (`security find-generic-password -s openrouter-pilot-api-key -w`). On /linux, just export `OPENROUTER_API_KEY` in `~/.bashrc`. Don't write the key to a file.

## Multi-machine sync

Both machines must have:
- `OPENROUTER_API_KEY` exported in `~/.bashrc` (and `~/.zshrc` on Mac)
- `or-pick` script installed to `~/.local/bin/or-pick`
- Patched proxy (only if using picker-UI workarounds): `~/.local/bin/or-anthropic-proxy.py` updated
- Code CLI binaries (`claude`, `codex`) installed and on PATH

Sync script for /linux:
```bash
scp ~/Downloads/or-pick jeff-ubuntu:~/.local/bin/or-pick
# OPENROUTER_API_KEY already in /linux ~/.bashrc
```

## References (in this skill's `references/` directory)

- `references/picker-mechanism.md` — the 5-slot picker + gateway-model-discovery protocol (Anthropic docs excerpts, OpenRouter `/v1/models` format)
- `references/proxy-patch.md` — the bidirectional `anthropic-` prefix rewrite (line-level diff, test commands)
- `references/codex-quirks.md` — Codex v0.144.5 auth preference, Responses API, profile mechanics
- `references/cmux-tui-render.md` — the cmux read-screen → PIL PNG render pipeline (no Chrome required)

## Related skills

- `browser-headless-default` — for any browser work (not needed for this skill; TUI → PIL is headless by construction)
- `evidence-attach-to-slack` — for posting screenshots / patches to Slack threads (3-stage upload flow)
- `finish-the-job` — drives the work to a verifiable end-state (PR-merged / local-state-verified / dry-run)

## Pitfalls (don't do these)

- ❌ **Assuming `claude --verbose` emits usage JSON.** Claude Code v2.1.212 does NOT — the flag exists but emits nothing. For prompt-cache evidence, load the OpenRouter Activity dashboard in a browser (human-only, Clerk-authed).
- ❌ **Telling the user "OpenRouter Activity is API-accessible."** It is NOT — Clerk-auth gates the per-call cache_read counts. Surface this early as "needs human Activity dashboard check."
- ❌ **Re-running `claude -p --verbose` to surface token counts.** Won't work in v2.1.212; verify on a fresh Claude Code build before retrying.
- ❌ **Telling the user "the picker can't show Kimi/GLM."** It CAN via the proxy patch + alias env vars (Recipe 3, LEGACY). Or via `or-pick` (Recipe 1) which bypasses the picker entirely.
- ❌ **Re-introducing the local proxy unprompted.** The user DELETED the proxy on 2026-07-21 explicitly. Don't auto-spawn it again. If a future task needs picker-UI workarounds, ASK first. The `_or_proxy_base` function stays as a 3-line direct-URL stub so any caller that re-introduces a proxy only needs to swap that one function back.
- ❌ **Trusting stale "MUST route via proxy" rules in `~/.claude/CLAUDE.md`.** The 2026-07-17 rule "direct OpenRouter breaks `claude -p` stdout" was REFUTED for Claude Code v2.1.212. Always verify environment claims before committing them as persistent rules. When refuting a stale rule, update `~/.claude/CLAUDE.md` so the next session doesn't re-encounter it.
- ❌ **Forgetting the stale-daemon trap after `rm`/`trash` of the proxy binary.** Verified 2026-07-21 on /linux: a daemonized `python3` kept port 8767 held even after the file was deleted. `lsof -nP -iTCP:8767 -sTCP:LISTEN` post-delete; `kill -9` any leftover PID.
