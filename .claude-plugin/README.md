# WorldArchitect.AI Claude Code Plugin

This repository packages the existing `.claude/` commands, agents, hooks, and supporting scripts as an installable Claude Code plugin. Teams can point Claude Code at this repository (or any mirror) and install the `worldarchitect-ai-suite` bundle without manually copying configuration.

## Contents

- `.claude-plugin/plugin.json` – plugin manifest describing metadata and component entry points.
- `.claude-plugin/marketplace.json` – lightweight marketplace definition so the repository can be added directly via `/plugin marketplace add`.
- `.claude/commands/` – all slash-command definitions.
- `.claude/agents/` – subagents available to Claude Code.
- `.claude/hooks/hooks.plugin.json` – plugin hook configuration that routes back to the scripts under `.claude/hooks/` or project overrides.
- `scripts/slack_notify.sh` – reused by the Stop hook when Slack notifications are configured.

## Local development workflow

1. Trust this repository inside Claude Code.
2. Run `/plugin marketplace add ./` from the project root to register the local marketplace.
3. Install the plugin with `/plugin install worldarchitect-ai-suite@worldarchitect-suite`.
4. Restart Claude Code (terminal or IDE) so the plugin loads.
5. Use `claude --debug` to verify that the plugin, commands, agents, and hooks registered correctly.

The hooks rely on `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}` to prefer project-specific overrides while falling back to the packaged automation scripts, which keeps behaviour identical whether the automation lives in the repo or in a shared plugin install.
