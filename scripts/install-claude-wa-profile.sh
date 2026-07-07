#!/usr/bin/env bash
# Install ~/.claude-wa as a WorldArchitect Claude Code profile that shares
# tooling with ~/.claude while keeping auth/sessions local.
#
# Canonical source: jleechanorg/user_scope (this script).
# Restore on a new machine:
#   git clone https://github.com/jleechanorg/user_scope.git
#   ~/projects_other/user_scope/scripts/install-claude-wa-profile.sh
#
# Shared settings (permissions, experiment env, hooks/skills/commands) live in
# ~/.claude/settings.json and are symlinked into ~/.claude-wa.
set -euo pipefail

SRC="${CLAUDE_TOOLING_DIR:-$HOME/.claude}"
DST="${CLAUDE_WA_DIR:-$HOME/.claude-wa}"
BACKUP_ROOT="$DST/backups/pre-symlink-$(date +%Y%m%d-%H%M%S)"

log() { echo "[install-claude-wa] $*"; }

require_dir() {
  if [[ ! -d "$1" ]]; then
    echo "Missing required directory: $1" >&2
    exit 1
  fi
}

require_dir "$SRC"
mkdir -p "$DST"

SYMLINK_NAMES=(
  skills
  commands
  hooks
  scripts
  agents
  plugins
  mcp-servers
  settings.json
  mcp-strict.json
  CLAUDE.md
  CLAUDE-global-reference.md
  CLAUDE-policy-layering.md
  statusline-command.sh
  RTK.md
  bin
  learnings
  capture
  conversation-index
  ide
  servers
  supervisor
  venvs
  claude
  downloads
  paste-cache
  projects
)

LOCAL_ONLY=(
  .claude.json
  sessions
  session-env
  cache
  chrome
  telemetry
  tasks
  todos
  debug
  file-history
  history.jsonl
  statsig
  shell-snapshots
  plans
  plugins.blocked
  teams
  workflows
  backups
  .wa-shared-from-claude.txt
)

merge_wa_projects_into_tooling() {
  local wa_projects="$DST/projects"
  local tooling_projects="$SRC/projects"
  if [[ -L "$wa_projects" ]]; then
    return 0
  fi
  if [[ ! -d "$wa_projects" ]]; then
    return 0
  fi
  mkdir -p "$tooling_projects"
  local entry
  for entry in "$wa_projects"/*; do
    [[ -e "$entry" ]] || continue
    local name
    name="$(basename "$entry")"
    local dest="$tooling_projects/$name"
    if [[ -e "$dest" ]]; then
      log "projects merge: keeping existing tooling dir for $name"
      continue
    fi
    log "projects merge: moving WA-only project dir $name -> $tooling_projects/"
    mv "$entry" "$dest"
  done
}

link_one() {
  local name="$1"
  local src_path="$SRC/$name"
  local dst_path="$DST/$name"

  if [[ ! -e "$src_path" ]]; then
    log "skip missing source: $src_path"
    return 0
  fi

  if [[ -L "$dst_path" ]]; then
    local current
    current="$(readlink "$dst_path")"
    if [[ "$current" == "$src_path" ]]; then
      log "already linked: $name -> $src_path"
      return 0
    fi
    mkdir -p "$BACKUP_ROOT"
    mv "$dst_path" "$BACKUP_ROOT/$name.symlink"
    log "replaced symlink: $name (old -> $current)"
  elif [[ -e "$dst_path" ]]; then
    mkdir -p "$BACKUP_ROOT"
    mv "$dst_path" "$BACKUP_ROOT/$name"
    log "backed up local copy: $name"
  fi

  ln -s "$src_path" "$dst_path"
  log "linked: $name -> $src_path"
}

write_manifest() {
  local manifest="$DST/.wa-shared-from-claude.txt"
  {
    echo "# ~/.claude-wa entries symlinked to ~/.claude (tooling shared; auth/sessions local)"
    echo "# installed by: $0"
    echo "# created $(date -Iseconds)"
    echo "# backup of replaced paths: $BACKUP_ROOT"
    echo
    for name in "${SYMLINK_NAMES[@]}"; do
      if [[ -L "$DST/$name" ]]; then
        printf 'LINKED     %-30s %s\n' "$name" "$(readlink "$DST/$name")"
      fi
    done
    echo
    echo "# Local-only (not symlinked):"
    for name in "${LOCAL_ONLY[@]}"; do
      if [[ -e "$DST/$name" ]]; then
        printf 'LOCAL      %s\n' "$name"
      fi
    done
  } >"$manifest"
  log "wrote manifest: $manifest"
}

main() {
  log "tooling source: $SRC"
  log "WA profile dir: $DST"
  merge_wa_projects_into_tooling
  local name
  for name in "${SYMLINK_NAMES[@]}"; do
    link_one "$name"
  done
  write_manifest
  log "done — use: CLAUDE_CONFIG_DIR=$DST claude …  (or claudewa from ~/.bashrc)"
}

main "$@"
