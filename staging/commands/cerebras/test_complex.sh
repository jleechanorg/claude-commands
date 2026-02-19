#!/bin/bash
set -x
export CEREBRAS_DEBUG=1
echo "Testing with complex prompt..."
./cerebras_direct.sh "Write a complete Python function to calculate the Fibonacci sequence with memoization, include docstrings, type hints, and error handling for negative numbers. Make sure it handles large numbers efficiently."
