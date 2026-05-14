#!/usr/bin/env bash
set -euo pipefail

PKG="jleechanorg-orchestration"
VERSION="${1:-}"
UV_PYTHON="${UV_PYTHON:-/opt/homebrew/opt/python@3.13/bin/python3.13}"
VENV_DIR="${VENV_DIR:-$HOME/.local/orch-venv}"

if [[ ! -d "$VENV_DIR" ]]; then
  echo "==> Creating venv at $VENV_DIR with $UV_PYTHON"
  mkdir -p "$(dirname "$VENV_DIR")"
  command -v "$UV_PYTHON" >/dev/null 2>&1 || UV_PYTHON="python3.13"
  "$UV_PYTHON" -m venv "$VENV_DIR"
fi

UV_BIN="${UV_BIN:-$(command -v uv || true)}"
if [[ -z "$UV_BIN" ]]; then
  echo "uv not found, installing..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  UV_BIN="$HOME/.local/bin/uv"
fi

install_orchestration() {
  local ver="$1"
  echo "==> Installing ${PKG}${ver:+=}${ver} via uv into $VENV_DIR"
  if [[ -n "$ver" ]]; then
    "$UV_BIN" pip install --python "$VENV_DIR/bin/python" "${PKG}==${ver}"
  else
    "$UV_BIN" pip install --python "$VENV_DIR/bin/python" "${PKG}"
  fi
}

main() {
  if [[ -n "$VERSION" ]]; then
    install_orchestration "$VERSION"
  else
    install_orchestration ""
  fi

  echo
  echo "==> ai_orch version"
  "$VENV_DIR/bin/ai_orch" --version || true

  echo
  echo "==> To use ai_orch, add to your shell profile:"
  echo "    export PATH=\"$VENV_DIR/bin:\$PATH\""
  echo
  echo "==> To upgrade later:"
  echo "    uv pip install --python $VENV_DIR/bin/python --upgrade jleechanorg-orchestration"
}

main "$@"
