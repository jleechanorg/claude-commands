---
name: claude-codex-provider-routing
description: Add a new third-party API provider (DeepSeek / GLM / OpenRouter / Minimax / etc.) as a Claude Code and Codex CLI shell wrapper, mirroring the existing `claudem` (Minimax) / `claudeds` (DeepSeek) / `claudeg` (GLM) pattern in `~/.bashrc`. The canonical recipe is bashrc-function ONLY (no `~/bin/` shim). Non-interactive callers (pytest, launchd, AO workers, GitHub Actions) use `bash -lic 'wrapper …'` to source the bashrc. Trigger when the user says "set up <provider> like claudem", "add <provider> as a Claude/Codex wrapper", "route Claude Code through <provider>", "use OpenRouter in the terminal", "new claudem-style alias for <X>", or when wiring any new model provider behind the existing Claude Code / Codex CLIs.
---

# Claude/Codex Third-Party Provider Routing

Class-level recipe for adding a new third-party model provider (Minimax, DeepSeek, GLM, OpenRouter, …) as a Claude Code / Codex CLI shell wrapper, mirroring the existing `claudem`/`claudeds`/`claudeg` family.

The set already wired on this machine (2026-07-13):

| Wrapper | Provider | Default model | Env path |
|---|---|---|---|
| `claudem` | MiniMax | `MiniMax-M3` | `claude` + `ANTHROPIC_*` |
| `claudeds` | DeepSeek (Anthropic-compat) | `deepseek-v4-flash` | same |
| `claudeg`  | GLM 5.2 (OpenRouter, Anthropic-protocol) | `z-ai/glm-5.2` | `ANTHROPIC_BASE_URL=https://openrouter.ai/api` |
| `claudegz` | GLM 5.1 (Z.AI direct, Anthropic-protocol) | `glm-5.1` | `ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic` |
| `claudek`  | Kimi K3 (OpenRouter, Anthropic-protocol) | `moonshotai/kimi-k3` | see § Reasoning models |
| `claudeaf` | Agent-F enterprise acct | `sonnet` | `claude` + `CLAUDE_CONFIG_DIR=~/.claude-agent-f` |
| `claudewa` / `claude2` | WorldArchitect.ai acct | `fable` | `claude` + `CLAUDE_CONFIG_DIR=~/.claude-wa` + Aside u1 dance |
| `claudeor` | OpenRouter (Anthropic-protocol) | `anthropic/claude-sonnet-4.5` | new, this skill |
| `claudeo`  | (alias → `claudeg`) | `z-ai/glm-5.2` | back-compat for legacy alias |
| `codexor`  | OpenRouter (OpenAI-protocol) | `openai/gpt-5` | broken on v0.142.3, see Pitfall below |
| `codexo`   | OpenRouter → GLM 5.2 (OpenAI-protocol) | `z-ai/glm-5.2` | broken on v0.142.3, see Pitfall below |

## Two layers every wrapper must ship

When adding a `<x>` provider to Claude Code AND/OR Codex, ship ONLY the layers that don't have a single-command workaround — skipping any one breaks a class of callers:

1. **Interactive bash function** in `~/.bashrc` (works in shells, AO, PTY sessions, AND any non-interactive caller via `bash -lic 'wrapper …'`).
2. **(Codex only) profile layer TOML** at `~/.codex/<wrapper>.config.toml` (so the wrapper doesn't clobber the user's main `~/.codex/config.toml` / trusted-projects / ChatGPT-account config).

> **Why no `~/bin/<wrapper>` binary shim?** Previous versions of this skill (v1.4.0 and earlier) mandated a `~/bin/<wrapper>` shim for non-interactive callers. The shim was removed 2026-07-28 because (a) it drifted from the bashrc function (`${VAR:-default}` inherited `ANTHROPIC_MODEL=sonnet` from the bashrc global, silently routing to the wrong model), and (b) `bash -lic 'wrapper …'` is a one-token substitution for the binary that needs no second source of truth. If a future caller genuinely cannot use `bash -lic` (none has surfaced on this host), reconsider then — do NOT preemptively ship the shim.

**Verification for non-interactive callers** — every bashrc-function wrapper must work in all four contexts:

```bash
# 1. Interactive shell (bashrc auto-sourced)
bash -ic 'type claudem'                # → "claudem is a function"

# 2. Login shell (forces bashrc sourcing)
bash -lic 'type claudem'               # → "claudem is a function"

# 3. From Python subprocess
python3 -c "import subprocess; print(subprocess.run(['bash','-lic','claudem --version'], capture_output=True, text=True).stdout)"

# 4. From cron / launchd / env -i
env -i bash -lic 'claudem --version'   # → 2.1.220 (Claude Code)
```

If any of these returns `claudem: command not found`, the wrapper is missing from `~/.bashrc` — fix the bashrc, do NOT add a binary shim.

Naming convention (verified stable since at least 2026-06):
- `claude<short>` for Claude wrappers (sonnet default), `claude<short>c` for `--continue`.
- `claude<short>op` = Opus variant, `claude<short>opc` = Opus + continue.
- `codex<short>` for Codex wrappers, `codex<short>c` for `resume --last`.
- The spelled-out alias form is also a bashrc function: `claudem → claudeminimax`, `claudeds → claudedeepseek`, etc. No underscores — matches the family convention (`claudeg`, `claudek`, `claudeds`, `claudegz`, `claudem`). If the user explicitly wants underscores, ask before adding (the family form is the default).
- `claudeo` is historically taken (legacy alias at `~/.bashrc:686` for `claude --dangerously-skip-permissions --chrome --model opus`). When the user asks for a wrapper by name and the name already exists as either an alias OR an existing function, **deconflict via rename** rather than refuse or silently collide:
  - If the user's preferred name collides with a legacy **alias**, replace the alias with a function (aliases shadow function definitions, so the alias wins if both exist — confirmed in production). Test by `type -a <name>` after editing — if it shows both `alias` and `function`, the alias wins and your function is dead code.
  - If the user's preferred name collides with an existing **function** of a different target, rename the existing function (suffix the model family: `g`→`gz` for "Z.AI direct", `o`→`of` for OpenRouter-former, etc.) and free the preferred name. Verified pattern (2026-07-16): user asked for `claudek` (Kimi K3) + `claudeg` (GLM 5.2 via OpenRouter). Existing `claudeg` was wired to Z.AI direct glm-5.1; renamed to `claudegz`/`claudegzc`. Back-compat alias `claudeo() { claudeg "$@"; }` preserves the legacy shortcut.
  - Tested suffixes in active use (2026-07-16): `m`=minimax, `ds`=deepseek, `g`=glm-via-OpenRouter (z-ai/glm-5.2), `gz`=glm-via-Z.AI-direct (glm-5.1), `k`=kimi (moonshotai/kimi-k3), `or`=openrouter-with-Anthropic-default, `af`=agent-f.

## Template — Claude wrapper (Anthropic-protocol endpoint)

Use this for any provider that exposes an Anthropic-protocol endpoint (Anthropic-compat): OpenRouter `/api`, Minimax `/anthropic`, DeepSeek `/anthropic`, Z.AI `/api/anthropic`, etc.

`~/.bashrc` (insert near other Claude wrappers, e.g. right after `claudemc()` at line 1051):

```bash
# Claude Code via <Provider> (Anthropic-compatible endpoint <BASE_URL>)
# Usage: claude<short> [args]       → <Provider> session, default model <MODEL>
#        claude<short>op [args]     → <Provider> Opus session
#        claude<short>oc [args]     → → --continue
#        claude<short>opc [args]    → Opus + --continue
claude<short>() {
  CLAUDE<SHORT>_MODE=1 \
  ANTHROPIC_BASE_URL="<BASE_URL>" \
  ANTHROPIC_AUTH_TOKEN="$<PROVIDER>_API_KEY" \
  ANTHROPIC_API_KEY="$<PROVIDER>_API_KEY" \
  ANTHROPIC_MODEL="<MODEL>" \
  CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL=0 \
  claude --dangerously-skip-permissions --effort high "$@"
}

claude<short>op() {
  CLAUDE<SHORT>_MODE=1 \
  ANTHROPIC_BASE_URL="<BASE_URL>" \
  ANTHROPIC_AUTH_TOKEN="$<PROVIDER>_API_KEY" \
  ANTHROPIC_API_KEY="$<PROVIDER>_API_KEY" \
  ANTHROPIC_MODEL="<OPUS_MODEL>" \
  CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL=0 \
  claude --dangerously-skip-permissions --effort high "$@"
}

claude<short>oc()  { claude<short> --continue "$@"; }
claude<short>opc() { claude<short>op --continue "$@"; }
```

`~/bin/claude<short>` (executable shim, mirrors `~/bin/claudem`):

> **⚠ DEPRECATED 2026-07-28:** the binary shim pattern was removed in v1.5.0 of the `claude-code-claudem` umbrella skill. The bashrc function form is the source of truth; non-interactive callers (pytest, launchd, AO workers, GitHub Actions) must use `bash -lic 'claude<short> …'` to source the bashrc and make the function visible. This block remains as a historical reference for the `default-if-unset vs force` lesson, but the canonical recipe going forward is the bashrc function only.

```bash
#!/usr/bin/env bash
# DEPRECATED — see warning above. Real claude<short> CLI — <Provider>-routed Claude Code.
# Historical: Usable from Go AO PATH shims, cron, and non-interactive shells.
set -euo pipefail
: "${<PROVIDER>_API_KEY:?<PROVIDER>_API_KEY must be set (same as ~/.bashrc claude<short>)}"
export CLAUDE<SHORT>_MODE=1
# Force every ANTHROPIC_* var. Do NOT use ${VAR:-default} — bashrc sets
# ANTHROPIC_MODEL="sonnet" globally (so bare `claude` defaults to sonnet), and
# a default-if-unset export inherits that global into the wrapper, silently
# sending the upstream MiniMax-compatible endpoint the wrong model identity.
# See "Pitfall — ANTHROPIC_MODEL/ANTHROPIC_BASE_URL leak from bashrc into the
# wrapper shim" below for the full bug class. If you genuinely want a caller-
# overrideable model, gate it explicitly so the bashrc global cannot leak:
if [[ -n "${ANTHROPIC_MODEL_OVERRIDE:-}" ]]; then
  export ANTHROPIC_MODEL="$ANTHROPIC_MODEL_OVERRIDE"
else
  export ANTHROPIC_MODEL="<DEFAULT_MODEL>"
fi
export ANTHROPIC_BASE_URL="<BASE_URL>"
export ANTHROPIC_AUTH_TOKEN="$<PROVIDER>_API_KEY"
export ANTHROPIC_API_KEY="$<PROVIDER>_API_KEY"
export CLAUDE_CODE_ENABLE_EXPERIMENTAL_ADVISOR_TOOL=0
# CLAUDE_EFFORT defaults to "high" but is caller-overridable: this is safe
# because bashrc does NOT set CLAUDE_EFFORT globally, so the default expansion
# here is the only fallback path and there is no cross-talk source.
export CLAUDE_EFFORT="${CLAUDE_EFFORT:-high}"
exec claude --dangerously-skip-permissions --effort high "$@"
```

The override pattern lets callers swap models with `ANTHROPIC_MODEL_OVERRIDE=<X>` without editing the shim, but gates against the bashrc-global cross-talk class. `CLAUDE_EFFORT` keeps simple `${VAR:-default}` because bashrc does not export it.

## Template — Codex wrapper (OpenAI-protocol endpoint)

Use this for Codex, which reads `OPENAI_API_KEY` + `OPENAI_BASE_URL`. Codex v0.142+ has a **known auth conflict** — see §Auth conflict pitfall below.

`~/.bashrc` (insert near other Codex wrappers, around line 568 after `codexsc`):

```bash
# Codex via <Provider> (OpenAI-compatible <BASE_URL>)
# Usage: codex<short> [args]    → <Provider>-routed Codex, default model <MODEL>
#        codex<short>c [args]   → resume last
# Layers ~/.codex/<wrapper>.config.toml on top of the user's main config so
# their ChatGPT-account config and trusted-projects list stay untouched.
codex<short>() {
  OPENAI_API_KEY="$<PROVIDER>_API_KEY" \
  OPENAI_BASE_URL="<BASE_URL>" \
  command codex --profile <wrapper> -m <MODEL> --config model_reasoning_effort=high "$@"
}

codex<short>c() {
  OPENAI_API_KEY="$<PROVIDER>_API_KEY" \
  OPENAI_BASE_URL="<BASE_URL>" \
  command codex --profile <wrapper> -m <MODEL> resume --last "$@"
}
```

`~/bin/codex<short>` and `~/bin/codex<short>c` (mirror the bash-function pattern):

```bash
#!/usr/bin/env bash
# Real codex<short> CLI — <Provider>-routed Codex via <BASE_URL>.
# Layers ~/.codex/<wrapper>.config.toml.
set -euo pipefail
: "${<PROVIDER>_API_KEY:?<PROVIDER>_API_KEY must be set (same as ~/.bashrc codex<short>)}"
export OPENAI_API_KEY="$<PROVIDER>_API_KEY"
export OPENAI_BASE_URL="<BASE_URL>"
exec command codex --profile <wrapper> -m <MODEL> --config model_reasoning_effort=high "$@"
```

`~/.codex/<wrapper>.config.toml`:

```toml
# Layered via `codex --profile <wrapper>` so ChatGPT-account config +
# trusted projects in the user's main ~/.codex/config.toml stay untouched.

model = "<MODEL>"
model_reasoning_effort = "high"
approval_policy = "never"
sandbox_mode = "danger-full-access"

[model_providers.<provider_short>]
name = "<Provider Display Name>"
base_url = "<BASE_URL>"

model_provider = "<provider_short>"
```

## Class — multi-`~/.claude*` account wrappers (different OAuth, same binary)

Sibling class to provider routing: instead of routing `claude` to a different **model provider** via `ANTHROPIC_*` env, you route it to a different **Anthropic OAuth account** via `CLAUDE_CONFIG_DIR`. Each `~/.claude*` dir isolates: OAuth credentials, conversation history, MCP servers, and (optionally) settings. On this box (verified live 2026-07-17):

| Wrapper family | Config dir | Model | OAuth | Use for |
|---|---|---|---|---|
| `claude` (bare) | `~/.claude` | `sonnet` (default) | $USER tooling | scratch / tooling |
| `claudewa` / `claude2` (and `*c` variants) | `~/.claude-wa` | `fable` | $USER@your-project.com | WorldArchitect.ai work |
| `claudeaf` / `claudeafc` | `~/.claude-agent-f` | `sonnet` | jeffrey@agent-f.com | Agnt-F (org Agnt-F) work |

The bashrc template (~`~/.bashrc:712-731`) is a function that:
1. Saves the current Aside account via `aside account status` (which prints one line per account, prefixed with `*` for active).
2. Calls `aside account use <aside-id>` to align the Chrome profile cookies.
3. Runs `claude` with `CLAUDE_CONFIG_DIR=~/.claude-<account> --dangerously-skip-permissions --chrome --model <X> "$@"`.
4. Restores the Aside account on exit (the buggy bit — see Pitfall below).

The `*c` suffix on the wrapper name is the `--continue` variant — append `--continue` so `--continue` resolves against the account's conversation pool instead of starting fresh.

### Pitfall — `awk '/^\*/ {print $1; exit}'` captures `*` not the account id (Aside stuck on u1 after `claudewa` exits)

The bashrc restore step is:
```bash
_aside_prev=$(aside account status 2>/dev/null | awk '/^\*/ {print $1; exit}')
aside account use u1 >/dev/null 2>&1 || true
CLAUDE_CONFIG_DIR=~/.claude-wa claude --dangerously-skip-permissions --chrome --model fable "$@"
local _rc=$?
if [[ -n "$_aside_prev" && "$_aside_prev" != "u1" ]]; then
  aside account use "$_aside_prev" >/dev/null 2>&1 || true
fi
```

`aside account status` output:
```
* u0  $USER@gmail.com  signed in  profiles: Profile 0
  u1  $USER@your-project.com  signed in  profiles: Profile 1
```

`awk '/^\*/ {print $1; exit}'` extracts `$1` of the line starting with `*`. That field is the literal `*` (the active marker), **not** the account id `u0`. Result: `_aside_prev="*"`, the restore runs `aside account use "*"`, Aside CLI rejects with `Account must be a non-negative account id, for example 0 or u0`, the error is swallowed by `>/dev/null 2>&1 || true`, and Aside stays on `u1` after `claudewa` exits — even if it started on `u0`. Verified live 2026-07-17 by reproducing the exact bashrc flow manually.

**Fix:** change `$1` to `$2` (the second whitespace-separated field, which is the account id):
```bash
_aside_prev=$(aside account status 2>/dev/null | awk '/^\*/ {print $2; exit}')
```

Or use `sed -n 's/^\* //p' | awk '{print $1; exit}'` if you want to be more explicit about stripping the marker.

**Workaround until fixed:** after any `claudewa` invocation, manually run `aside account use u0` (or whichever account you want active) to restore.

### Pitfall — `~/.claude-wa/{settings.json,projects}` are symlinks to `~/.claude/`, NOT isolated copies

Verified live 2026-07-17:
- `~/.claude-wa/settings.json` → `~/.claude/settings.json` (same permissions/env/hooks)
- `~/.claude-wa/projects/` → `~/.claude/projects/` (same conversation history)

So `claudewac` does **not** find a WA-only conversation pool — `--continue` resolves against the shared `~/.claude/projects/` directory. The only things `CLAUDE_CONFIG_DIR=~/.claude-wa` actually isolates are:
1. OAuth credentials (`.credentials.json`)
2. Per-account MCP server registrations (`mcp-servers/`, `mcp-strict.json`)
3. The fact that the bashrc command chose WA's Aside account (`u1`)

If you genuinely need WA conversations to be isolated from tooling, you must replace the symlink with a real directory + copy/replay the WA history into it (or stop creating the symlink when bootstrapping a new account). `~/.claude-agent-f/` has concrete files (own `settings.json` with hooks, own `projects/`), so it IS properly isolated.

### Verification recipe for a new account wrapper

Before declaring a `claudexxx` wrapper "done", run the four-layer probe in priority order:

```bash
# 1. Binary resolution under the config dir
CLAUDE_CONFIG_DIR=~/.claude-<account> timeout 6 claude --version 2>&1 | head -3

# 2. OAuth / auth probe (cheap non-interactive)
timeout 10 bash -c 'claudexxx --print --output-format text --model <X> "reply with just the word pong"' 2>&1 | tail -5

# 3. --continue target resolution (must find at least one conversation)
ls -la ~/.claude-<account>/projects/ 2>&1 | head -3

# 4. Aside restore round-trip
START=$(aside account status 2>/dev/null | awk '/^\*/ {print $2; exit}')
claudexxx --print "..."  # should auto-switch Aside
aside account status 2>/dev/null | awk '/^\*/ {print $2; exit}'
# If still on u1 and START was different, the awk bug above is biting you
aside account use "$START"  # manual restore
```

Step 4 is the trap — `claudeaf` returned HTTP 401 on this box (2026-07-17) because `~/.claude-agent-f/` has no valid `.credentials.json`. The fix is `node ~/.claude/scripts/auth-cli.mjs login --project <account>` (or whichever auth script the account ships), but OAuth logins require user approval — don't run them autonomously.

### Verified live 2026-07-17 (test transcript)

| Wrapper | Result | Note |
|---|---|---|
| `claudewac --print "reply with just the word pong"` | `pong` ✅ | WA account OK |
| `claudeafc --print "reply with just the word pong"` | `401 Invalid authentication credentials` ❌ | Agnt-F needs re-auth via `auth-cli.mjs` |
| `claude --version` under `CLAUDE_CONFIG_DIR={~/.claude,~/.claude-wa,~/.claude-agent-f}` | `2.1.207 (Claude Code)` (all 3) | binary resolves identically |
| `aside account use u1` → `aside account use u0` round-trip | works manually; **broken** via `claudewa` because of the awk bug | restore does not actually restore |

## Pitfall — `claude --print` swallows body in non-TTY bash

When smoke-testing from `bash -lc`, `claude --print "<prompt>"` may return `exit=0` but produce empty stdout even though the model generated a real answer. Symptom:

```
rc=0 stderr-bytes=279 stdout-bytes=1
```

This is **not a wrapper bug**. The model IS responding. To prove it, use verbose JSON streaming and the canonical parser in `scripts/parse_claude_verbose.py`:

```bash
claude --dangerously-skip-permissions --print --verbose --output-format=json \
  "<prompt>" > /tmp/c.out 2>/tmp/c.err
python3 scripts/parse_claude_verbose.py < /tmp/c.out
```

A successful run prints `ASSISTANT_TEXT: 'pong'` (or whatever was asked) and `IS_ERROR=False STOP_REASON=end_turn` — that is the proof the wrapper works end-to-end. The script also exits non-zero if no `result` event is emitted (the symptom of the wrapper actually being broken, not just the stdout-flush quirk).

**Reasoning-model variant (Kimi K3, DeepSeek R1, o1-series, etc., 2026-07-16):** The same silent-exit symptom occurs with reasoning models **even when the model is producing a real answer**, because Claude Code 2.1.207's `-p` non-interactive mode is not threading the model's `thinking`/`redacted_thinking` content blocks through to stdout. Verified with `claudek` (moonshotai/kimi-k3): the raw API returns `pong-kimi-k3-claudek` in the Anthropic-format `text` block with `stop_reason: end_turn`, but `bash -lic 'claudek -p "Reply with pong"'` exits 0 with empty stdout. The same wrapper + same prompt against a non-reasoning model (`claudeor` / `claudeo`) returns "pong" normally. Diagnose by hitting `/v1/messages` directly with `curl` (see `scripts/probe_openrouter.sh --reasoning`) before assuming the wrapper is broken. Bead: `$USER-3e4o`.

## Pitfall — bash functions aren't exec targets; `timeout <N> <function>` fails

A bash function defined in `~/.bashrc` is *not* on the exec path. From a `bash -lic` shell where the function is loaded, you can call `claudek -p "..."` directly — bash resolves it as a function and runs the body. But:

- `timeout 90 claudek -p "..."` from a separate shell fails with `timeout: failed to run command 'claudek': No such file or directory`.
- Same error even inside `bash -lic 'timeout 90 claudek -p "..."'` — `timeout` execs the name as a binary.

**The 2026-07-28 fix (canonical):** `timeout` itself is a function-aware bash builtin when called from inside bash, but its child process is `exec`-based. The fix is to call the wrapper as a function inside bash, so bash's function resolution applies:

```bash
# Works — bash function is resolved by the parent bash, not exec'd
bash -lic 'timeout 90 claudek -p "..."'

# Or with explicit function-resolution:
bash -lic 'claudek -p "..." & pid=$!; (sleep 90; kill $pid 2>/dev/null) & wait $pid'
```

**DO NOT** revert to the v1.4.0-era "ship `~/bin/<wrapper>`" workaround. The binary shim was removed 2026-07-28 because it drifted from the bashrc function (default-if-unset vs force ANTHROPIC_MODEL). Bashrc-only is the canonical recipe; the `timeout`-from-non-bash-shell case is solved by `bash -lic`.

Smoke-test command, in priority order:

```bash
# 1. Best: parse verbose JSON (works for reasoning models too)
bash -lic 'claudeor --print --verbose --output-format=json "Reply with exactly the word pong"' \
  | python3 ~/.hermes/skills/devops/claude-codex-provider-routing/scripts/parse_claude_verbose.py

# 2. OK for non-reasoning models: direct invocation (function shell only)
bash -lic 'claudeor --print "Reply with exactly the word pong"'

# 3. Timeout + wrapper (must wrap the whole bash -lic call, not just the wrapper):
bash -lic 'timeout 90 claudeor --print "..."'   # ✅

# 4. Wrong — fails with "No such file or directory" because timeout execs the name:
timeout 90 claudeor --print "..."               # ❌
bash -lic 'timeout 90 claudeor --print "..."'   # ❌ (timeout execs from inside bash, function table not in scope)
```

For the reasoning-model silent-exit case, option (1) with `--verbose --output-format=json` is the only honest verification — option (2) will print nothing for Kimi K3 even though the API is fine.

## Pitfall — Reasoning models (Kimi K3 / DeepSeek R1 / o1-series) on OpenRouter

Reasoning models expose extra content blocks and have provider-level quirks that bite silent wrappers. Verified 2026-07-16 with `moonshotai/kimi-k3`:

1. **`/v1/chat/completions` returns a separate `reasoning` field** on the message, NOT `reasoning_content` (despite some Anthropic-protocol docs implying otherwise). Sample response excerpt:
   ```json
   {
     "choices": [{"message": {
       "content": "391",
       "reasoning": "17 * 23 = 17 * 20 + 17 * 3 = 340 + 51 = 391."
     }}],
     "usage": {"completion_tokens_details": {"reasoning_tokens": 56}}
   }
   ```
2. **`/v1/messages` returns 3 content blocks per assistant turn**:
   ```json
   "content": [
     {"type": "thinking", "thinking": "...chain-of-thought..."},
     {"type": "text", "text": "...final answer..."},
     {"type": "redacted_thinking", "type": "redacted_thinking", "data": "openrouter.reasoning:eyJ0ZX...cHMg"}
   ]
   ```
   Verify the answer by grepping for `"type":"text"` not just `"content"`.
3. **Reasoning cannot be disabled** for some providers. Sending `"reasoning": {"enabled": false}` to Kimi K3 returns `HTTP 400: Reasoning is mandatory for this endpoint and cannot be disabled.` Don't try to silence chain-of-thought — budget `max_tokens` for both reasoning AND answer (≥2× the answer length for safety).
4. **Upstream rate-limiting at launch.** New reasoning models are usually rate-limited hard for the first days/weeks. Kimi K3 returned HTTP 429 (`Provider returned error … is temporarily rate-limited upstream … retry_after_seconds=1`) on multiple consecutive calls during launch week (2026-07-16). Implement retry-with-backoff (`retry_after_seconds + jitter`) in any smoke-test script — naive single-shot calls will report spurious failures. See `scripts/probe_openrouter.sh` for the retry pattern.
5. **Default `ANTHROPIC_DEFAULT_HAIKU_MODEL` has no obvious fallback.** When adding a reasoning model, you must explicitly set `ANTHROPIC_DEFAULT_HAIKU_MODEL` to *something* — Claude Code will spawn subagents on the haiku tier, and most reasoning models don't expose a smaller sibling. Either reuse the same heavy model (expensive but works) or pick a known-fast fallback like `z-ai/glm-4.5-air`. **`claudek` defaults all subagent tiers to `moonshotai/kimi-k3`** — set `ANTHROPIC_DEFAULT_HAIKU_MODEL` externally if you want a cheaper fallback.

## Pitfall — Codex v0.142.3 ChatGPT-auth conflict

Codex CLI's auth layer wins over env vars: when `~/.codex/auth.json` has `auth_mode = "chatgpt"` (which is the default after `codex login` with a ChatGPT account), Codex ignores `OPENAI_API_KEY` and answers:

> `{"type":"error","status":400,"error":{"type":"invalid_request_error","message":"The '<model>' model is not supported when using Codex with a ChatGPT account."}}`

To make `codex<short>` actually route through the third-party API:
- **Either** run `codex logout` first (destroys user's ChatGPT login — irreversible without re-login), OR
- **Or** ship `~/.codex/<wrapper>.config.toml` (the profile layer above) AND accept that codexor etc. will still fail at model-list lookup but env-var wiring is correct for any non-ChatGPT-auth environment.

Document the auth-mode requirement in the wrapper's bash comment block — operators need to know one `codex logout` (or running in a CI/no-ChatGPT environment) unblocks the wrapper.

## Pitfall — Codex v0.142.3 `responses_websocket` bypasses `model_provider.base_url` (newer than the ChatGPT-auth conflict)

Codex CLI v0.142+ introduced a `responses_websocket` transport that **hard-codes `wss://api.openai.com/v1/responses` regardless of `[model_providers.<x>].base_url`** in the profile TOML. Symptom: even after `codex logout` removes the ChatGPT-auth conflict, `codex --profile <wrapper>` still produces:

```
ERROR codex_api::endpoint::responses_websocket: failed to connect to websocket:
  HTTP error: 401 Unauthorized, url: wss://api.openai.com/v1/responses
```

And the resolved config dump prints `provider: openai` (not the provider you configured), with `model: <your model id>` — confirming Codex is honoring the model id but routing to api.openai.com anyway.

**Diagnostic — verify the bug, not your config:**

```bash
# Back up auth.json to neutralize ChatGPT auth, then run with --skip-git-repo-check
mv ~/.codex/auth.json ~/.codex/auth.json.bak
OPENAI_API_KEY="$OPENROUTER_API_KEY" \
OPENAI_BASE_URL="https://openrouter.ai/api/v1" \
command codex --profile codexor -m openai/gpt-5 \
  --config model_reasoning_effort=high exec --skip-git-repo-check "echo hi" 2>&1 \
  | grep -iE "model:|provider:|openrouter|wss://api\.openai" | head -10
mv ~/.codex/auth.json.bak ~/.codex/auth.json
```

If you see `provider: openai` + `wss://api.openai.com` even after auth.json is removed, the bug is in Codex v0.142.3 itself, not your wrapper. This was verified 2026-07-14 against `codexor` (openai/gpt-5), `codexo` (z-ai/glm-5.2), and both with auth.json backed up — all three produced identical 401s against `api.openai.com`. `codex --help` and `codex exec --help` confirm there is **no** `--base-url` / `--api-base` / `--provider-override` CLI flag in v0.142.3.

**Workarounds (none complete as of 2026-07-14):**
1. **Downgrade Codex CLI** to a build that uses the legacy `/v1/chat/completions` transport and honors `[model_providers.<x>].base_url`.
2. **Use the OpenAI-protocol endpoint directly via `curl`** for one-off prompts — bypasses Codex entirely.
3. **Use `claude<short>` instead of `codex<short>`** — the `claude` CLI's Anthropic-protocol transport correctly honors `ANTHROPIC_BASE_URL`, so `claudeo`/`claudeor` work end-to-end against OpenRouter while `codexo`/`codexor` cannot.

**Action when you hit this:** the bashrc warning comment already documents the ChatGPT-auth conflict. After this finding, also add a one-liner to any new `codex<short>` wrapper's bash comment block noting that v0.142.3's WebSocket transport is broken regardless of auth state, and recommend `claude<short>` as the working alternative until upstream fixes.

## Pitfall — OpenRouter model id format

OpenRouter exposes **two** API shapes at the same host:

| Path | Protocol | Used by |
|---|---|---|
| `https://openrouter.ai/api/v1/messages` | Anthropic-protocol | `claude` wrappers (`ANTHROPIC_BASE_URL=https://openrouter.ai/api`) |
| `https://openrouter.ai/api/v1/chat/completions` | OpenAI-protocol | `codex` wrappers (`OPENAI_BASE_URL=https://openrouter.ai/api/v1`) |
| `https://openrouter.ai/api/v1/responses` | ❌ rejects generic input | do **not** use |

Model IDs go in the form `<provider>/<model>` — e.g. `anthropic/claude-sonnet-4.5`, `anthropic/claude-opus-4.7`, `openai/gpt-5`, `z-ai/glm-5.2`. The unversioned `anthropic/claude-sonnet-4` is deprecated (returns 11s response, warns "Claude Sonnet 4 was retired") — always pin to a suffixed version (`4.5`, `4.7`, etc.). For non-Anthropic/non-OpenAI models on OpenRouter, query the live catalog before pinning a default:

```bash
curl -sS -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  https://openrouter.ai/api/v1/models \
  | python3 -c "import sys,json; d=json.load(sys.stdin); [print(m['id']) for m in d['data'] if '<substring>' in m['id'].lower()]"
```

Verified GLM family on OpenRouter as of 2026-07-14: `z-ai/glm-4.5`, `z-ai/glm-4.5-air`, `z-ai/glm-4.6`, `z-ai/glm-4.7`, `z-ai/glm-4.7-flash`, `z-ai/glm-5`, `z-ai/glm-5-turbo`, `z-ai/glm-5.1`, `z-ai/glm-5.2`, `z-ai/glm-5v-turbo`. Note: Codex warns `Model metadata for 'z-ai/glm-5.2' not found. Defaulting to fallback metadata` even when the model id is correct — the model still works, the warning is metadata-only.

## Pitfall — `unset ANTHROPIC_*` block is upstream of your wrapper

`~/.bashrc` lines 928-933 unconditionally `unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL` so the bare `claude` command uses OAuth/login. Your wrapper re-exports them **inline as env-var prefixes on the `claude` invocation**, not via `export`, so the unset is preserved for the parent shell but the spawned `claude` sees them. Do NOT use `export ANTHROPIC_BASE_URL="..."` at shell scope inside the wrapper body — the unset will race-wipe it for sibling commands.

## Pitfall — bashrc globals (`ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL`) can leak into ANY wrapper layer that uses default-if-unset

`~/.bashrc` deliberately sets `ANTHROPIC_MODEL="sonnet"` globally (line ~939) so the bare `claude` command defaults to sonnet and `claude --model <X>` does not pollute `~/.claude/settings.json`. Lines ~928-933 `unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL` so the bare `claude` uses OAuth/login. These are inherited by every subprocess launched from a bashrc-sourced shell (pytest, launchd jobs, AO workers, cron via `env -i`, GitHub Actions).

The **bashrc-function wrapper** is safe by design: it sets every `ANTHROPIC_*` env var **inline as env-var prefixes on the `claude` invocation**, not via `export`. So the bashrc globals are preserved for the parent shell but the spawned `claude` sees the wrapper's values. **No leak.**

The leak returns the moment you introduce any layer that does `export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-<default>}"` or `export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-<default>}"`:

- `ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-MiniMax-M3}"` → returns `"sonnet"` (from bashrc) when parent has the default. **Silent model-identity leak** — wrapper answers as `claude-sonnet-5` instead of `MiniMax-M3`, exit 0, no error.
- `ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.minimax.io/anthropic}"` → returns `""` (because bashrc line ~930 `unset` it). Endpoint call fails with a 4xx; the failure is loud and easy to diagnose, so this one is less of a foot-gun.

**Symptom verified live 2026-07-28** (the v1.1.0–v1.4.0 era `~/bin/claudem` shim had this bug; the live M3 test caught it on the first run that exercised the slow suite end-to-end from a bashrc-sourced pytest):
```
$ env | grep ^ANTHROPIC_MODEL=
ANTHROPIC_MODEL=sonnet
$ ANTHROPIC_MODEL=sonnet claudem -p "Output exactly one line: model=<your model>" --max-turns 3
model: claude-sonnet-5          # ← WRONG; should be model=MiniMax-M3
```

**Fix — force, do NOT default-if-unset.** When you need to introduce a layer that exports env vars (e.g., a binary shim if a future caller cannot use `bash -lic`), use the same pattern the bashrc function uses:

```bash
# WRONG (silent cross-talk from bashrc global):
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-<DEFAULT_MODEL>}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-<DEFAULT_URL>}"

# RIGHT (mirrors the bashrc function's inline-set pattern):
export ANTHROPIC_MODEL="<DEFAULT_MODEL>"
export ANTHROPIC_BASE_URL="<DEFAULT_URL>"

# RIGHT with caller override (gated, so bashrc global cannot leak):
if [[ -n "${ANTHROPIC_MODEL_OVERRIDE:-}" ]]; then
  export ANTHROPIC_MODEL="$ANTHROPIC_MODEL_OVERRIDE"
else
  export ANTHROPIC_MODEL="<DEFAULT_MODEL>"
fi
```

`CLAUDE_EFFORT` keeps simple `${VAR:-default}` because bashrc does not export it.

**Audit one-liner — find every wrapper layer with this bug:**

```bash
# Find any executable wrapper (binary or shim) that uses default-if-unset for bashrc-controlled env vars.
# Each hit is a silent cross-talk risk.
rg --hidden -l 'ANTHROPIC_MODEL=.\$\{ANTHROPIC_MODEL:-' ~/bin 2>/dev/null
rg --hidden -l 'ANTHROPIC_BASE_URL=.\$\{ANTHROPIC_BASE_URL:-' ~/bin 2>/dev/null
# Bashrc functions are safe (they set inline, not via export). The audit only applies
# to binary shims, which we no longer ship — these rgs should return zero hits.
```

Verified clean for `~/bin/` as of 2026-07-28 (binary removed). The same probe must run on Linux (`ssh jeff-ubuntu 'rg --hidden -l "ANTHROPIC_MODEL=.\\$\\{ANTHROPIC_MODEL:-" ~/bin'`) for cross-machine parity.

**Class scope:** every wrapper layer in this umbrella that uses default-if-unset for any bashrc-controlled env var (`ANTHROPIC_MODEL`, `ANTHROPIC_BASE_URL`, future globals) is exposed to this bug. Bashrc functions are immune because they set inline; only executable shims are at risk. The `claude-code-claudem` leaf skill documents the M3-specific case in full at `~/.hermes/skills/claude-code-claudem/references/bashrc-global-leak.md`.

## Pitfall — `ANTHROPIC_MODEL="sonnet"` default protects the bare `claude`

`~/.bashrc:939` sets `export ANTHROPIC_MODEL="sonnet"` because `claude` persists `--model` to `~/.claude/settings.json` on first run. If you use `claudem` (or any wrapper) and it changes that file, every subsequent bare `claude` run inherits the wrapper's model. Don't remove that `export`. (Captured in `~/.bashrc` comment lines 935-938.)

## Pitfall — User preference: bashrc functions over binary shims (2026-07-28)

User explicit feedback on the v1.4.0-era `~/bin/claudem` shim: *"I dont think we should use /bin/claudem or have that and it conflicts with bashrc function maybe we just source bashrc."* Encode as a hard rule for this umbrella:

- **Default to bashrc functions, never ship a binary shim by default.** The user's preference is single source of truth (bashrc) over redundant layers. `bash -lic` is the canonical non-interactive invocation; do not preemptively add a `~/bin/<wrapper>` shim.
- **If a future caller cannot use `bash -lic`**, surface that as a class-level question (which caller, why, what env var is missing) before adding any new layer. Do not silently add a shim.
- **Spelled-out aliases** (`claudeminimax`, `claudedeepseek`, etc.) are also bashrc functions — never binary shims, never second wrappers. `claudem() { … }; claudeminimax() { claudem "$@"; }` is the canonical pattern.
- **Naming convention: no underscores.** Matches `claudeg` / `claudek` / `claudeds` / `claudegz` / `claudem`. The form `claude_minimax` (with underscore) was explicitly rejected.

## Verification — minimum bar before claiming "done"

A wrapper is "done" only when ALL of these pass:

1. **bash syntax** — `bash -n ~/.bashrc` exits 0; `bash -n ~/bin/<shim>` exits 0.
2. **shim is executable** — `chmod +x ~/bin/<shim>`; `file ~/bin/<shim>` reports `Bourne-Again shell script`.
3. **API key reachable** — `openrouter-check` (or equivalent) hits `<PROVIDER>/auth` and returns 200.
4. **End-to-end completion** — `claude --print --verbose --output-format=json "<prompt>"` parses out `ASSISTANT_TEXT=<real answer>` + `IS_ERROR=False` + `STOP_REASON=end_turn` + non-zero `COST`.
5. **Documentation in bash comment** — every new function has a `# Usage:` block at the top, matching the existing wrappers.

If only the smoke test 1-3 pass and the verbose parse shows `IS_ERROR=True` or `STOP_REASON` is empty, the wrapper is **not done** — go fix the model id, base URL, or auth conflict before claiming it.

**Codex wrappers on v0.142.3 cannot pass verification step 4** because of the `responses_websocket` transport bypass (see Pitfall below). When wiring `codex<short>` on this Codex version:
- Steps 1-3 + 5 still apply and must pass.
- Step 4 cannot be met — note this explicitly in the wrapper's bash comment block AND in the smoke-test reply, do not claim "done" silently.
- The minimum honest smoke test is: `(mv ~/.codex/auth.json ~/.codex/auth.json.bak; command codex --profile <wrapper> exec ... 2>&1; mv ~/.codex/auth.json.bak ~/.codex/auth.json) | grep -E "provider:|wss://api\.openai" | head` — confirm the bug rather than blaming your config. If the diagnostic shows `provider: openai` + `wss://api.openai.com`, report the upstream Codex bug to the user instead of recommending they switch model ids.

## Subagent for parallel provider research

When wiring a brand-new provider (not just adding OpenRouter next to the existing 4), spawn one `delegate_task` (or `ao spawn`) per of these in parallel:

1. Probe the provider's API docs for the Anthropic-protocol endpoint and one stable model id.
2. Probe the provider's API docs for the OpenAI-protocol endpoint and one stable model id.
3. Probe the provider's auth endpoint (or `auth/key` style probe) to confirm the API key works.
4. Confirm the model id with a real `POST /v1/messages` (or `/chat/completions`) call returning a 200 with `pong`-style response.

Then wire all four artifacts into the three layers above. Do not skip step 4 — model ids change (`claude-sonnet-4` was retired 2026-06-15) and you will set up a default that 404s on first invocation.

## Common mistakes seen across providers

- **Auth header name** — Anthropic-compat endpoints usually expect `Authorization: Bearer $KEY`, sometimes `x-api-key`. Probe with `curl -I` and check the 401/403 response to read the header name.
- **Base URL trailing slash** — `<base>` and `<base>/` are NOT always interchangeable. OpenAI's `OPENAI_BASE_URL` drops trailing slash silently; Anthropic's `ANTHROPIC_BASE_URL` is stricter. Use the form `<host>` (no trailing slash).
- **Model id with vs without provider prefix** — OpenRouter accepts `anthropic/claude-sonnet-4.5` (correct) AND `claude-sonnet-4.5` (incorrect → 404). Always include the prefix.
- **Default model deprecated** — `claude-sonnet-4` (unversioned) is slow and warns. Pin to a suffixed version from day one.

## Verification script

Before declaring any wrapper "done", run the full probe recipe — `scripts/probe_openrouter.sh` (or its template, adapted to a new provider host) hits auth/catalog/Anthropic-protocol/OpenAI-protocol in sequence and exits 0 only when all four return `pong`:

```bash
scripts/probe_openrouter.sh                     # defaults to https://openrouter.ai
scripts/probe_openrouter.sh https://api.deepseek.com   # template for a new provider
```

Required env: `<PROVIDER>_API_KEY` (for OpenRouter: `OPENROUTER_API_KEY`).

## Support files

- `references/openrouter-surfaces.md` — verified probe transcript for `/api/v1/messages`, `/api/v1/chat/completions`, `/api/v1/responses`, plus per-model latency and cost data captured 2026-07-13. Read this before changing a default model id.
- `references/reasoning-models.md` — reasoning-model probe transcripts (Kimi K3 verified 2026-07-16), the 5-step diagnostic ladder for "wrapper silently exits", launch-window 429 backoff pattern, naming convention, and cost data. Read this before wiring a new `claudek`-style wrapper.
- `templates/openrouter-claude-shim.sh` — copy → `~/bin/<wrapper>`, fill the `<...>` placeholders, `chmod +x`.
- `templates/codex-profile-config.toml` — copy → `~/.codex/<wrapper>.config.toml`, fill the `<...>` placeholders.
- `scripts/probe_openrouter.sh` — re-runnable 4-stage probe (auth → catalog → Anthropic → OpenAI). Exit 0 = wrapper is safe.
- `scripts/parse_claude_verbose.py` — JSONL parser that extracts `ASSISTANT_TEXT` + `RESULT` metrics from `claude --print --verbose --output-format=json` output. Use this whenever a smoke test returns `exit=0` but appears to print nothing.

## Files referenced (this skill's reference impl)

- `~/.bashrc:1036-1053` — `claudem`/`claudeme`/`claudemc` (Minimax baseline, v1.5.0 added `claudeminimax`/`claudeminimaxc` aliases)
- `~/.bashrc:953-975` — `claudeds` / `claudedsp` (DeepSeek baseline)
- `~/.bashrc:1058-1072` — `claudeg` / `claudegc` placeholder (older layout)
- `~/.bashrc:1171-1196` — `claudek` / `claudekc` (Kimi K3 via OpenRouter, added 2026-07-16)
- `~/.bashrc:1198-1220` — `claudeg` / `claudegc` (GLM 5.2 via OpenRouter, redefined 2026-07-16; was Z.AI-direct `claudeg` until 2026-07-16)
- `~/.bashrc:1222-1230` — `claudeo` / `claudeoc` back-compat aliases pointing to `claudeg` (added 2026-07-16)
- `~/.bashrc:1232-1251` — `claudegz` / `claudegzc` (Z.AI direct glm-5.1; renamed from `claudeg` 2026-07-16 to free the `g` suffix for OpenRouter GLM)
- `~/.bashrc:570-602` — `codexor` / `codexorc` + `openrouter-check`
- `~/.bashrc:597-630` — `codexo` / `codexoc` (OpenRouter→GLM 5.2 Codex; subject to v0.142.3 WebSocket bypass)
- `~/.bashrc:1117-1138` — (older) `claudeo` / `claudeoc` slot, now superseded by the `claudeg` redefinition at line 1198
- `~/.bashrc:549-558` — base `codex()` function (auto-routes via local proxy)
- `~/.codex/codexor.config.toml` — Codex profile-layer config pattern
- `~/.codex/codexo.config.toml` — Codex profile-layer for GLM 5.2

**No `~/bin/<wrapper>` shim baseline.** Previous versions of this skill mandated a binary shim in `~/bin/` for non-interactive callers. Removed 2026-07-28 (drift bug — see `Pitfall — bashrc globals leak`). Use `bash -lic 'wrapper …'` instead. If a future caller cannot use `bash -lic`, add a `scripts/install-<wrapper>-shim.sh` and document it here — do not preemptively ship shims.

## Beads

- `$USER-3e4o` — Claude Code `-p` silent with reasoning models (Kimi K3). See `references/reasoning-models.md` § "Bead follow-up" for scope.
