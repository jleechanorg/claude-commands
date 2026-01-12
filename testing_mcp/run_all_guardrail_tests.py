#!/usr/bin/env python3
"""Run all 3 guardrail tests in parallel with evidence saving enabled by default."""

import subprocess
import sys
from pathlib import Path

# Run all 3 tests in parallel
tests = [
    'testing_mcp/test_outcome_declaration_guardrails.py',
    'testing_mcp/test_llm_refuse_impossible_actions.py',
    'testing_mcp/test_resource_consumption_lifecycle.py',
]

procs = []
for test in tests:
    cmd = [sys.executable, test, '--start-local', '--models', 'gemini-3-flash-preview']
    print(f'🚀 Starting: {test}')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    procs.append((test, proc))

# Wait for all to complete
results = []
for test, proc in procs:
    stdout, _ = proc.communicate()
    results.append((test, proc.returncode, stdout))
    status = '✅ PASSED' if proc.returncode == 0 else '❌ FAILED'
    print(f'{status}: {test}')

# Print summaries
for test, code, output in results:
    print(f'\n{"="*70}')
    print(f'{test} (exit code: {code})')
    print(f'{"="*70}')
    # Show last 30 lines of output
    lines = output.split('\n')
    print('\n'.join(lines[-30:]))

sys.exit(max(code for _, code, _ in results))
