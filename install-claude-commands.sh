#!/bin/bash

# 🚨 Claude Commands Installation Script
# Installs the complete Claude Code command system for development workflows

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Source directory (where plugin files live)
PLUGIN_SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Active Claude Code directories (system-level)
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"
CLAUDE_AGENTS_DIR="$CLAUDE_HOME/agents"
CLAUDE_COMMANDS_DIR="$CLAUDE_HOME/commands"
CLAUDE_SCRIPTS_DIR="$CLAUDE_HOME/scripts"
CLAUDE_SKILLS_DIR="$CLAUDE_HOME/skills"

# Source directories in plugin repo
SRC_AGENTS_DIR="$PLUGIN_SRC_DIR/.claude/agents"
SRC_COMMANDS_DIR="$PLUGIN_SRC_DIR/.claude/commands"
SRC_SCRIPTS_DIR="$PLUGIN_SRC_DIR/.claude/scripts"
SRC_SKILLS_DIR="$PLUGIN_SRC_DIR/.claude/skills"
SRC_BEADS_LAUNCHER="$PLUGIN_SRC_DIR/scripts/beads-converge"
SRC_BEADS_RUNTIME_DIR="$PLUGIN_SRC_DIR/scripts/beads_convergence"
INSTALL_MODE="refuse"
INSTALL_ROOT="$CLAUDE_HOME"
STAGING_DIR=""
BACKUP_PATH=""
ACTIVATION_BACKUP_PATH=""
LOCK_DIR=""
LOCK_ACQUIRED=0
RETAIN_STAGING=0
TARGET_WAS_PRESENT=0
TARGET_IDENTITY=""
STAGING_IDENTITY=""

show_usage() {
    cat <<EOF
Usage: $(basename "$0") [--merge | --backup]

Installs into CLAUDE_HOME (default: ~/.claude). A nonempty target is refused
by default. Use --merge to explicitly update source-managed files in place, or
--backup to move the existing target aside before installing.
EOF
}

parse_arguments() {
    while [ "$#" -gt 0 ]; do
        case "$1" in
            --merge) INSTALL_MODE="merge" ;;
            --backup) INSTALL_MODE="backup" ;;
            -h|--help) show_usage; exit 0 ;;
            *) log_error "Unknown option: $1"; show_usage >&2; return 1 ;;
        esac
        shift
    done
}

directory_is_nonempty() {
    [ -d "$1" ] && [ -n "$(find "$1" -mindepth 1 -maxdepth 1 -print -quit)" ]
}

directory_mode() {
    if stat -c '%a' "$1" >/dev/null 2>&1; then
        stat -c '%a' "$1"
    else
        stat -f '%Lp' "$1"
    fi
}

path_identity() {
    if stat -c '%d:%i' "$1" >/dev/null 2>&1; then
        stat -c '%d:%i' "$1"
    else
        stat -f '%d:%i' "$1"
    fi
}

path_is_present() {
    [ -e "$1" ] || [ -L "$1" ]
}

acquire_install_lock() {
    local parent
    parent="$(dirname "$CLAUDE_HOME")"
    mkdir -p "$parent"
    LOCK_DIR="${CLAUDE_HOME}.install.lock"
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
        log_error "Another installer is active for CLAUDE_HOME: $CLAUDE_HOME"
        return 1
    fi
    LOCK_ACQUIRED=1
}

validate_merge_destination_path() {
    local destination="$1"
    local source_label="$2"
    local relative path parent

    if path_is_present "$destination" && { [ -L "$destination" ] || [ ! -d "$destination" ]; }; then
        log_error "Merge destination is not a real directory: $source_label"
        return 1
    fi
    [ -d "$3" ] || return 0
    while IFS= read -r -d '' relative; do
        relative="${relative#./}"
        path="$destination/$relative"
        parent="$(dirname "$path")"
        while [ "$parent" != "$destination" ]; do
            if path_is_present "$parent" && { [ -L "$parent" ] || [ ! -d "$parent" ]; }; then
                log_error "Merge destination ancestor is unsafe: $parent"
                return 1
            fi
            parent="$(dirname "$parent")"
        done
        if path_is_present "$path" && { [ -L "$path" ] || [ ! -f "$path" ]; }; then
            log_error "Merge destination is not a regular file: $path"
            return 1
        fi
    done < <(
        cd "$3"
        list_installable_files "$4"
    )
}

validate_merge_destinations() {
    [ "$INSTALL_MODE" = "merge" ] || return 0
    validate_merge_destination_path "$CLAUDE_HOME/agents" "agents" "$SRC_AGENTS_DIR" "agents" || return 1
    validate_merge_destination_path "$CLAUDE_HOME/commands" "commands" "$SRC_COMMANDS_DIR" "commands" || return 1
    validate_merge_destination_path "$CLAUDE_HOME/scripts" "scripts" "$SRC_SCRIPTS_DIR" "scripts" || return 1
    validate_merge_destination_path "$CLAUDE_HOME/scripts/beads_convergence" "beads convergence runtime" "$SRC_BEADS_RUNTIME_DIR" "scripts" || return 1
    validate_merge_destination_path "$CLAUDE_HOME/skills" "skills" "$SRC_SKILLS_DIR" "skills" || return 1
    if path_is_present "$CLAUDE_HOME/scripts/beads-converge" && { [ -L "$CLAUDE_HOME/scripts/beads-converge" ] || [ ! -f "$CLAUDE_HOME/scripts/beads-converge" ]; }; then
        log_error "Merge destination is not a regular file: $CLAUDE_HOME/scripts/beads-converge"
        return 1
    fi
}

revalidate_target_before_activation() {
    if [ "$TARGET_WAS_PRESENT" -eq 1 ]; then
        if ! path_is_present "$CLAUDE_HOME" || [ "$(path_identity "$CLAUDE_HOME")" != "$TARGET_IDENTITY" ]; then
            log_error "CLAUDE_HOME changed during installation; refusing activation"
            return 1
        fi
    elif path_is_present "$CLAUDE_HOME"; then
        log_error "CLAUDE_HOME reappeared during installation; refusing activation"
        return 1
    fi
}

prepare_target() {
    if [ -L "$CLAUDE_HOME" ] || { [ -e "$CLAUDE_HOME" ] && [ ! -d "$CLAUDE_HOME" ]; }; then
        log_error "Target exists but is not a directory: $CLAUDE_HOME"
        return 1
    fi

    if directory_is_nonempty "$CLAUDE_HOME"; then
        case "$INSTALL_MODE" in
            refuse)
                log_error "Refusing to modify nonempty target: $CLAUDE_HOME"
                log_error "Re-run with --merge to update it or --backup to preserve it as a backup."
                return 1
                ;;
            backup) ;;
            merge)
                log_warning "Merging source-managed files into explicit target: $CLAUDE_HOME"
                ;;
        esac
    fi
    mkdir -p "$(dirname "$CLAUDE_HOME")"
    if path_is_present "$CLAUDE_HOME"; then
        TARGET_WAS_PRESENT=1
        TARGET_IDENTITY="$(path_identity "$CLAUDE_HOME")"
    else
        TARGET_WAS_PRESENT=0
        TARGET_IDENTITY=""
    fi
    STAGING_DIR="$(mktemp -d "${CLAUDE_HOME}.staging.XXXXXX")"
    INSTALL_ROOT="$STAGING_DIR"
    if [ -e "$CLAUDE_HOME" ] && [ "$INSTALL_MODE" != "backup" ]; then
        cp -a "$CLAUDE_HOME/." "$STAGING_DIR/"
        chmod "$(directory_mode "$CLAUDE_HOME")" "$STAGING_DIR"
        log_info "Seeded staged installation from existing target"
    else
        log_info "Staging installation in $STAGING_DIR"
    fi
}

next_activation_backup_path() {
    local candidate
    candidate="${CLAUDE_HOME}.activation-$(date +%Y%m%d%H%M%S)-$$"
    local suffix=0
    while [ -e "$candidate" ]; do
        suffix=$((suffix + 1))
        candidate="${CLAUDE_HOME}.activation-$(date +%Y%m%d%H%M%S)-$$-$suffix"
    done
    printf '%s' "$candidate"
}

activate_staged_install() {
    [ -n "$STAGING_DIR" ] || return 0
    revalidate_target_before_activation
    STAGING_IDENTITY="$(path_identity "$STAGING_DIR")"

    if [ "$INSTALL_MODE" = "backup" ] && [ -e "$CLAUDE_HOME" ]; then
        BACKUP_PATH="${CLAUDE_HOME}.backup-$(date +%Y%m%d%H%M%S)"
        if [ -e "$BACKUP_PATH" ]; then
            log_error "Backup path already exists: $BACKUP_PATH"
            return 1
        fi
        mv "$CLAUDE_HOME" "$BACKUP_PATH"
        if ! mv "$STAGING_DIR" "$CLAUDE_HOME"; then
            log_error "Failed to activate staged installation; restoring original target."
            mv "$BACKUP_PATH" "$CLAUDE_HOME" || log_error "Original target remains at $BACKUP_PATH"
            return 1
        fi
        log_info "Moved existing target to $BACKUP_PATH"
        if [ "$(path_identity "$CLAUDE_HOME")" != "$STAGING_IDENTITY" ]; then
            log_error "Activated target identity does not match staged installation"
            RETAIN_STAGING=1
            return 1
        fi
        STAGING_DIR=""
        return 0
    fi

    if [ -e "$CLAUDE_HOME" ]; then
        ACTIVATION_BACKUP_PATH="$(next_activation_backup_path)"
        if ! mv "$CLAUDE_HOME" "$ACTIVATION_BACKUP_PATH"; then
            log_error "Failed to reserve original target for activation."
            return 1
        fi
    fi
    if ! mv "$STAGING_DIR" "$CLAUDE_HOME"; then
        log_error "Failed to activate staged installation; restoring original target."
        if [ -n "$ACTIVATION_BACKUP_PATH" ]; then
            mv "$ACTIVATION_BACKUP_PATH" "$CLAUDE_HOME" || log_error "Original target remains at $ACTIVATION_BACKUP_PATH"
        fi
        return 1
    fi
    if [ "$(path_identity "$CLAUDE_HOME")" != "$STAGING_IDENTITY" ]; then
        log_error "CLAUDE_HOME was recreated or staging was nested during activation"
        local nested_stage="$CLAUDE_HOME/$(basename "$STAGING_DIR")"
        if [ -d "$nested_stage" ] && mv "$nested_stage" "$STAGING_DIR"; then
            :
        elif [ -d "$nested_stage" ]; then
            STAGING_DIR="$nested_stage"
        fi
        RETAIN_STAGING=1
        return 1
    fi
    STAGING_DIR=""
    if [ -n "$ACTIVATION_BACKUP_PATH" ]; then
        if rm -rf "$ACTIVATION_BACKUP_PATH"; then
            ACTIVATION_BACKUP_PATH=""
        else
            log_warning "Installation activated; retained recoverable previous target at $ACTIVATION_BACKUP_PATH"
        fi
    fi
}

list_installable_files() {
    local component_name="$1"
    if [ "$component_name" = "skills" ]; then
        find . -type d \( \
            -name _archive -o \
            -name _archived_loose_md -o \
            -name _archived_loose_md_2026-08-23 -o \
            -name __pycache__ -o \
            -name .pytest_cache \
        \) -prune -o -type f ! -name '*.py[co]' ! -name '.DS_Store' -print0
    else
        find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune \
            -o -type f ! -name '*.py[co]' ! -name '.DS_Store' -print0
    fi
}

validate_beads_convergence_inputs() {
    local runtime_file
    if [ ! -f "$SRC_BEADS_LAUNCHER" ] || [ ! -d "$SRC_BEADS_RUNTIME_DIR" ]; then
        log_error "Required beads convergence release input is missing"
        log_error "Expected $SRC_BEADS_LAUNCHER and $SRC_BEADS_RUNTIME_DIR"
        return 1
    fi
    runtime_file="$(find "$SRC_BEADS_RUNTIME_DIR" -type f ! -name '*.py[co]' ! -name '.DS_Store' ! -path '*/__pycache__/*' ! -path '*/.pytest_cache/*' -print -quit)"
    if [ -z "$runtime_file" ]; then
        log_error "Required beads convergence runtime package is empty: $SRC_BEADS_RUNTIME_DIR"
        return 1
    fi
}

validate_staged_file() {
    local path="$1"
    local parent
    if [ -L "$path" ] || [ ! -f "$path" ]; then
        return 1
    fi
    parent="$(dirname "$path")"
    while [ "$parent" != "$INSTALL_ROOT" ]; do
        if [ -L "$parent" ] || [ ! -d "$parent" ]; then
            return 1
        fi
        parent="$(dirname "$parent")"
    done
}

# Shared recursive install function
install_component() {
    local src_dir="$1"
    local dest_dir="$2"
    local component_name="$3"
    local relative

    if [ -f "$src_dir" ]; then
        mkdir -p "$dest_dir"
        cp -a "$src_dir" "$dest_dir/$(basename "$src_dir")"
        log_success "Installed $component_name"
    elif [ -d "$src_dir" ]; then
        mkdir -p "$dest_dir"
        while IFS= read -r -d '' relative; do
            relative="${relative#./}"
            mkdir -p "$(dirname "$dest_dir/$relative")"
            cp -a "$src_dir/$relative" "$dest_dir/$relative"
        done < <(
            cd "$src_dir"
            list_installable_files "$component_name"
        )
        log_success "Installed recursive $component_name tree"
    else
        log_warning "No $component_name source directory found at $src_dir"
    fi
}

# Copy agents to ~/.claude/agents/
install_agents() {
    install_component "$SRC_AGENTS_DIR" "$INSTALL_ROOT/agents" "agents"
}

# Copy commands to ~/.claude/commands/
install_commands() {
    install_component "$SRC_COMMANDS_DIR" "$INSTALL_ROOT/commands" "commands"
}

# Copy scripts to ~/.claude/scripts/
install_scripts() {
    install_component "$SRC_SCRIPTS_DIR" "$INSTALL_ROOT/scripts" "scripts"
}

# The convergence launcher and its sibling package are installed together so
# the isolated launcher can import the runtime from CLAUDE_HOME/scripts.
install_beads_convergence() {
    install_component "$SRC_BEADS_RUNTIME_DIR" "$INSTALL_ROOT/scripts/beads_convergence" "scripts"
    install_component "$SRC_BEADS_LAUNCHER" "$INSTALL_ROOT/scripts" "beads convergence launcher"
}

# Copy skills to ~/.claude/skills/
install_skills() {
    install_component "$SRC_SKILLS_DIR" "$INSTALL_ROOT/skills" "skills"
}

# Environment validation
validate_installation() {
    local component source_dir relative destination_file files_checked=0
    for component in agents commands scripts skills; do
        source_dir="$PLUGIN_SRC_DIR/.claude/$component"
        [ -d "$source_dir" ] || continue
        while IFS= read -r -d '' relative; do
            relative="${relative#./}"
            destination_file="$INSTALL_ROOT/$component/$relative"
            if ! validate_staged_file "$destination_file" || ! cmp -s "$source_dir/$relative" "$destination_file"; then
                log_error "Manifest validation failed for $component/$relative"
                return 1
            fi
            files_checked=$((files_checked + 1))
        done < <(
            cd "$source_dir"
            list_installable_files "$component"
        )
    done
    if [ -f "$SRC_BEADS_LAUNCHER" ]; then
        destination_file="$INSTALL_ROOT/scripts/beads-converge"
        if ! validate_staged_file "$destination_file" || ! cmp -s "$SRC_BEADS_LAUNCHER" "$destination_file"; then
            log_error "Manifest validation failed for scripts/beads-converge"
            return 1
        fi
        files_checked=$((files_checked + 1))
    fi
    if [ -d "$SRC_BEADS_RUNTIME_DIR" ]; then
        while IFS= read -r -d '' relative; do
            relative="${relative#./}"
            destination_file="$INSTALL_ROOT/scripts/beads_convergence/$relative"
            if ! validate_staged_file "$destination_file" || ! cmp -s "$SRC_BEADS_RUNTIME_DIR/$relative" "$destination_file"; then
                log_error "Manifest validation failed for scripts/beads_convergence/$relative"
                return 1
            fi
            files_checked=$((files_checked + 1))
        done < <(
            cd "$SRC_BEADS_RUNTIME_DIR"
            list_installable_files "scripts"
        )
    fi
    log_success "Source-derived manifest validation passed ($files_checked files)"
}

# Post-install information
show_next_steps() {
    log_info "Start Claude Code to use the installed commands and skills."
    log_info "Documentation: https://github.com/jleechanorg/claude-commands"
}

# Main installation flow
main() {
    parse_arguments "$@"
    echo
    log_info "Claude Commands Installation Script"
    log_info "Installing complete Claude Code command system..."
    log_info "Source: $PLUGIN_SRC_DIR"
    log_info "Target: $CLAUDE_HOME"
    echo

    validate_beads_convergence_inputs
    acquire_install_lock
    validate_merge_destinations
    prepare_target
    install_agents
    install_commands
    install_scripts
    install_beads_convergence
    install_skills
    validate_installation
    activate_staged_install

    echo
    show_next_steps
    echo
    log_success "Installation complete!"
}

cleanup_failed_install() {
    local status=$?
    if [ "$status" -eq 0 ]; then
        if [ "$LOCK_ACQUIRED" -eq 1 ]; then
            if rmdir "$LOCK_DIR"; then
                LOCK_ACQUIRED=0
            else
                log_error "Cleanup failed; installer lock retained at $LOCK_DIR"
                return 1
            fi
        fi
        return 0
    fi
    if [ -n "$ACTIVATION_BACKUP_PATH" ] && [ ! -e "$CLAUDE_HOME" ] && [ -e "$ACTIVATION_BACKUP_PATH" ]; then
        if mv "$ACTIVATION_BACKUP_PATH" "$CLAUDE_HOME"; then
            ACTIVATION_BACKUP_PATH=""
        else
            log_error "Original target remains at $ACTIVATION_BACKUP_PATH"
        fi
    fi
    if [ -n "$BACKUP_PATH" ] && [ ! -e "$CLAUDE_HOME" ] && [ -e "$BACKUP_PATH" ]; then
        if mv "$BACKUP_PATH" "$CLAUDE_HOME"; then
            BACKUP_PATH=""
        else
            log_error "Original target remains at $BACKUP_PATH"
        fi
    fi
    if [ "$RETAIN_STAGING" -eq 1 ] && [ -n "$STAGING_DIR" ] && [ -d "$STAGING_DIR" ]; then
        log_error "Staged installation retained at $STAGING_DIR"
    elif [ -n "$STAGING_DIR" ] && [ -d "$STAGING_DIR" ]; then
        if rm -rf "$STAGING_DIR"; then
            STAGING_DIR=""
        else
            log_error "Cleanup failed; staged installation retained at $STAGING_DIR"
        fi
    fi
    if [ "$LOCK_ACQUIRED" -eq 1 ]; then
        if rmdir "$LOCK_DIR"; then
            LOCK_ACQUIRED=0
        else
            log_error "Cleanup failed; installer lock retained at $LOCK_DIR"
            status=1
        fi
    fi
    log_error "Installation failed. Check the output above for details."
    return "$status"
}

trap cleanup_failed_install EXIT

# Run main installation if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
