#!/bin/bash
# ao-launcher.sh — thin launchd wrapper that sources shell env then delegates to start-all.sh
# Called by ai.agento.lifecycle-all plist instead of passing env vars directly via plist.
# All API keys, paths, and runtime config come from the shell profile — same as interactive.

set -euo pipefail

# Source shell profile to inherit all env vars (API keys, PATH, etc.)
# Prefer bashrc (Linux) fall back to zshrc (macOS default shell)
if [ -f "$HOME/.bashrc" ]; then
  source "$HOME/.bashrc"
elif [ -f "$HOME/.bash_profile" ]; then
  source "$HOME/.bash_profile"
elif [ -f "$HOME/.zshrc" ]; then
  source "$HOME/.zshrc"
fi

REPO_ROOT="${AO_REPO_ROOT:-$HOME/project_agento/agent-orchestrator}"
exec "$REPO_ROOT/scripts/start-all.sh"
