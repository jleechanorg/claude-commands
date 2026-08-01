#!/bin/bash
set -eo pipefail

if [[ -f "$HOME/.bash_profile" ]]; then
  # shellcheck disable=SC1090
  set +u
  source "$HOME/.bash_profile"
  set -u
fi

unset OPENAI_API_KEY
unset CMUX_SOCKET
unset CMUX_SOCKET_PATH
export PATH="$HOME/.local/bin:/Applications/cmux.app/Contents/Resources/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

for candidate in "$HOME/.local/orch-venv/bin/python3" /opt/homebrew/bin/python3; do
  if [[ -x "$candidate" ]] && "$candidate" -c 'import fastembed, numpy, onnxruntime' >/dev/null 2>&1; then
    exec "$candidate" "$HOME/projects/user_scope/scripts/cmux_resume_watchdog.py" --daemon --interval 120
  fi
done

echo "No Python runtime with fastembed, numpy, and onnxruntime is available" >&2
exit 1
