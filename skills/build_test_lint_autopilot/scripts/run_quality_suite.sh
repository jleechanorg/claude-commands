#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../../.. && pwd)"

"${PROJECT_ROOT}/run_tests.sh" "$@"
"${PROJECT_ROOT}/run_lint.sh"
