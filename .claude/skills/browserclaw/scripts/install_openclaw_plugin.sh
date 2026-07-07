#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_COMMANDS_DIR="${HOME}/.claude/commands"
CODEX_SKILLS_DIR="${HOME}/.codex/skills"

python3 -m pip install "${ROOT}"

mkdir -p "${CLAUDE_COMMANDS_DIR}" "${CODEX_SKILLS_DIR}"
cp "${ROOT}/.claude/commands/browserclaw.md" "${CLAUDE_COMMANDS_DIR}/browserclaw.md"
rm -rf "${CODEX_SKILLS_DIR}/browserclaw"
cp -R "${ROOT}/.codex/skills/browserclaw" "${CODEX_SKILLS_DIR}/browserclaw"

echo "Installed browserclaw CLI, Claude command, and Codex skill."

