#!/usr/bin/env bash
# Helper functions for Oracle CLI usage in browser mode.
# Exposes lightweight wrappers documented in skills/oracle-browser-usage.md.

set -euo pipefail

ORACLE_DEFAULT_GLOBS=(${ORACLE_DEFAULT_GLOBS:-".")}
ORACLE_DEFAULT_EXCLUDES=(${ORACLE_DEFAULT_EXCLUDES:-})
ORACLE_ENGINE=${ORACLE_ENGINE:-browser}

_oracle_or_die() {
  if ! command -v oracle >/dev/null 2>&1; then
    echo "❌ oracle CLI not found. Install it and ensure it's on PATH." >&2
    return 127
  fi
  oracle "$@"
}

_oracle_run() {
  local description="$1"; shift
  local extra=("$@")
  local files=("${ORACLE_DEFAULT_GLOBS[@]}")
  if [ ${#ORACLE_DEFAULT_EXCLUDES[@]} -gt 0 ]; then
    files+=("${ORACLE_DEFAULT_EXCLUDES[@]/#/--exclude }")
  fi
  echo "🔎 Oracle (${description}) -> engine=${ORACLE_ENGINE}" >&2
  _oracle_or_die --engine "${ORACLE_ENGINE}" --wait --files-report "${extra[@]}" -- "${ORACLE_DEFAULT_GLOBS[@]}"
}

oracle_arch_preview() {
  _oracle_run "architecture preview" --dry-run summary "$@"
}

oracle_arch() {
  _oracle_run "architecture review" "$@"
}

oracle_ai_debug() {
  local report_path=${1:-}
  shift || true
  _oracle_run "ai debug" ${report_path:+--note "$report_path"} "$@"
}

oracle_diff_review() {
  _oracle_run "diff review" --diff git "$@"
}

oracle_ui_debug() {
  local report_path=${1:-}
  shift || true
  _oracle_run "ui debug" ${report_path:+--note "$report_path"} "$@"
}

