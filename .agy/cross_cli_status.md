# agy cross-cli Stop wiring

The agy CLI (`~/.local/bin/agy`, v1.1.8) wraps an OpenAI-compatible request
envelope around Claude/Codex payloads. Its Stop event uses the same JSON
shape as Codex; the cross-cli hook auto-detects this case and applies the
`codex` extractor (or, with `HERMES_HOOK_CLI=agy`, the dedicated `agy`
extractor that prefers `model` over the deeper `model.*` path).

## Install

1. Symlink the repo-local hook to your home hooks dir (Codex auto-discovers):

   ```bash
   ln -sf "$(git rev-parse --show-toplevel)/.claude/hooks/cross_cli_status.py" \
          "$HOME/.claude/hooks/cross_cli_status.py"
   ```

2. Add the `Stop` event to your agy config (`~/.agy/config.toml` or the
   project `.agy/config.toml`):

   ```toml
   [[stop_hook]]
   command = "python3"
   args = ["~/.claude/hooks/cross_cli_status.py"]
   env = { HERMES_HOOK_CLI = "agy" }
   timeout = 30
   ```

The hook writes `~/.claude/var/cross_cli_status/last.json` after every
Stop event. Use `jq '.cli,.model,.rate_limit_pct,.rate_limit_window' \
"~/.claude/var/cross_cli_status/last.json"` to inspect.
