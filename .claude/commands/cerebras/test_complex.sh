#!/bin/bash
set -euo pipefail
if [[ "${CB_TEST_TRACE:-0}" == "1" ]]; then
  set -x
fi

export CEREBRAS_DEBUG=1
echo "Testing with complex prompt..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR"/cerebras_direct.sh "Write a complete Python function to calculate the Fibonacci sequence with memoization, include docstrings, type hints, and error handling for negative numbers. Make sure it handles large numbers efficiently."
