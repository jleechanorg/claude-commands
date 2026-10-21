# Rendering inactive coordinator schedules

`scripts/render_native_schedule.py` validates a private machine-local JSON file and writes inactive service definitions into a new staging directory. The compatibility installer entrypoints require `--render-only` and call this renderer; they never install, enable, start, stop, or remove a service. Review and activation are separate operator actions.

Copy `schedule.example.json` to a mode-0600 file under `~/.config/dot-coordinator/`. Replace the example account keys, identity SHA-256 bindings, tasks, and executable paths with the machine's reviewed local values. The three entries are ordered: macOS minutes are `00, 20, 40`; Linux minutes are `30, 50, 10`. The renderer verifies those keys exist in the configured Dot account map and requires Chrome DevTools MCP 1.6.0. Do not put credentials or API keys in this file.

Example invocations:

```sh
~/.claude/skills/dot-coordinator/scripts/install-service.sh --render-only \
  --config ~/.config/dot-coordinator/schedule.json \
  --output /tmp/dot-schedule-stage
```

The output directory and files are private (0700/0600), and the renderer refuses to overwrite an existing destination. macOS output contains three independent LaunchAgent plists. Reviewed macOS activation must create the private `~/.local/state/ai.gemini.agy-dot-coordinator/` log directory before loading them; launchd opens their stdout/stderr paths before starting the launcher. Linux output contains one environment file, service, and timer for each account. For reviewed Linux activation, the `.service` and `.timer` files belong in `~/.config/systemd/user/`; each `<unit>.env` belongs in `~/.config/dot-coordinator/` with mode 0600. The service requires `EnvironmentFile=%h/.config/dot-coordinator/<unit>.env`, including `DOT_EXPECTED_IDENTITY_SHA256`. The launcher no longer acquires profile flock or reads STOP/pending/legacy delivery state; shared dot.sh helpers remain unchanged. See MIGRATION.md for accepted race/duplicate risks and separately approved quiescent transition. The PATH includes the installed nvm Node 22 and `~/.local/bin` for the Pi adapter and `lunaroute` command. Linux rendering carries the current `DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`, and `XDG_RUNTIME_DIR` when present for the system keychain session.

The old single-service templates have been retired; the renderer uses the account-bound sources in `templates/`. Platform-specific entrypoints are `install-launchagent.sh --render-only ...` and `install-systemd.sh --render-only ...`; `install-service.sh --render-only ...` selects the host. Without `--render-only`, each entrypoint exits before writing anything. Activation is handled by the machine owner after reviewing the staged files.

The portable `cli` object selects an executable plus a literal argument array. The example uses `pi-lunaroute-adapter.sh` and configurable `--thinking medium`; it selects Pi's lunaroute provider with the alias-compatible `deepseek-4.1-flash` default and optional `PIL_MODEL`. `PI_EXECUTABLE` can select the real Pi executable. Legacy `pi_bin` remains supported with an empty prefix; specifying both is rejected. Both forms render `PI_BIN`, and the new form renders JSON in `COORDINATOR_CLI_ARGS`. A shell alias is not an executable: translate its existing executable/arguments to this configuration without sourcing shell startup files. Arguments containing spaces or shell metacharacters stay single literal arguments. The executable must accept the coordinator's existing Pi/MCP flags; this is not automatic translation for arbitrary CLIs. Do not put keys in argv/config or copy embedded secret fallbacks; retain the existing environment/credential helper. Check noninteractive PATH and provider readiness separately on each host before activation; no new credentials or global defaults are implied. Existing schedules stay unchanged until separately reviewed activation.

No new attempt receipts or task state are written. Existing unresolved-send data is transport safety, not a task ledger. Old receipts and holds are preserved for explicit migration reconciliation; do not delete them automatically. There is no exactly-once guarantee.

Before host activation, follow MIGRATION.md: old/new packages share legacy state and lock anchors; unregister the old schedule set before registering neutral labels. No automatic migration is performed.

The legacy per-account `task` field now supplies reminder/inspection mode context only; it does not delegate project tasks or persist work state. Each Dot owns that work.
