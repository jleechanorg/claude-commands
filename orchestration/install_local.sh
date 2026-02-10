#!/usr/bin/env bash
set -euo pipefail

PKG="jleechanorg-orchestration"
VERSION="${1:-0.1.40}"
MODE="${2:-active}"  # active|all

unique_add() {
  local value="$1"
  local entry
  for entry in "${PYTHON_TARGETS[@]:-}"; do
    if [[ "${entry}" == "${value}" ]]; then
      return 0
    fi
  done
  PYTHON_TARGETS+=("${value}")
}

discover_python_targets() {
  PYTHON_TARGETS=()

  if command -v pyenv >/dev/null 2>&1; then
    local pyenv_root
    pyenv_root="$(pyenv root 2>/dev/null || true)"
    if [[ -n "${pyenv_root}" && -d "${pyenv_root}/versions" ]]; then
      while IFS= read -r py; do
        [[ -x "${py}" ]] && unique_add "${py}"
      done < <(
        find "${pyenv_root}/versions" -maxdepth 3 -type f \
          \( -name "python" -o -name "python[0-9]*" \) \
          ! -name "*config*" \
          2>/dev/null | sort
      )
    fi
  fi

  if command -v python3 >/dev/null 2>&1; then
    unique_add "$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    unique_add "$(command -v python)"
  fi
}

run_install() {
  local py="$1"
  echo "==> Installing ${PKG}==${VERSION} via ${py}"
  "${py}" -m pip install --upgrade --no-cache-dir --index-url https://pypi.org/simple "${PKG}==${VERSION}"
  "${py}" -m pip show "${PKG}" | sed -n '1,20p'
}

if [[ "${MODE}" == "all" ]]; then
  discover_python_targets
  for py in "${PYTHON_TARGETS[@]:-}"; do
    run_install "${py}"
  done
else
  if command -v pyenv >/dev/null 2>&1 && pyenv version-name >/dev/null 2>&1; then
    ACTIVE_PY="$(pyenv which python)"
    run_install "${ACTIVE_PY}"
    pyenv rehash || true
  elif command -v python3 >/dev/null 2>&1; then
    run_install "$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    run_install "$(command -v python)"
  else
    echo "No python interpreter found on PATH." >&2
    exit 1
  fi
fi

echo

echo "==> ai_orch resolution"
(type -a ai_orch || true)
(which -a ai_orch || true)

echo
if command -v ai_orch >/dev/null 2>&1; then
  echo "==> ai_orch --version"
  ai_orch --version || true
fi
