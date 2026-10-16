# Rendering inactive coordinator schedules

`scripts/render_native_schedule.py` validates a private machine-local JSON file and writes inactive service definitions into a new staging directory. The compatibility installer entrypoints require `--render-only` and call this renderer; they never install, enable, start, stop, or remove a service. Review and activation are separate operator actions.

Copy `schedule.example.json` to a mode-0600 file under `~/.config/agy-dot-coordinator/`. Replace the example account keys, identity SHA-256 bindings, tasks, and executable paths with the machine's reviewed local values. The three entries are ordered: macOS minutes are `00, 20, 40`; Linux minutes are `30, 50, 10`. The renderer verifies those keys exist in the configured Dot account map and requires Chrome DevTools MCP 1.6.0. Do not put credentials or API keys in this file.

Example invocations:

```sh
~/.claude/skills/agy-dot-coordinator/scripts/install-service.sh --render-only \
  --config ~/.config/agy-dot-coordinator/schedule.json \
  --output /tmp/dot-schedule-stage
```

The output directory and files are private (0700/0600), and the renderer refuses to overwrite an existing destination. macOS output contains three independent LaunchAgent plists. Linux output contains one environment file, service, and timer for each account. Both preserve the coordinator's STOP marker and shared global/profile locks through the common launcher. The PATH includes the installed nvm Node 22 and `~/.local/bin` for the Pi adapter and `lunaroute` command. Linux rendering carries the current `DISPLAY`, `DBUS_SESSION_BUS_ADDRESS`, and `XDG_RUNTIME_DIR` when present for the system keychain session.

The old single-service templates have been retired; the renderer uses the account-bound sources in `templates/`. Platform-specific entrypoints are `install-launchagent.sh --render-only ...` and `install-systemd.sh --render-only ...`; `install-service.sh --render-only ...` selects the host. Without `--render-only`, each entrypoint exits before writing anything. Activation is handled by the machine owner after reviewing the staged files.
