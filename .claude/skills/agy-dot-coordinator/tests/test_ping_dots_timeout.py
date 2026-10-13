#!/usr/bin/env python3
"""Regression tests: generation fallbacks must not be blocked by provider hangs.

Incident: under Gemini quota exhaustion the agy wrapper's real child process hung
holding the stdout pipe; subprocess.run(timeout=...) killed only the direct child
and then blocked in communicate() because the grandchild kept the pipe open. The
provider fallback chain (agy -> luna -> minimax -> codex) never ran, the tick
wedged, and the coordinator lock stayed held through three subsequent ticks.
"""
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'ping-dots.py'


def load_module():
    spec = importlib.util.spec_from_file_location('ping_dots', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Direct child bash; the backgrounded grandchild inherits the stdout/stderr
# pipes and outlives the direct child once the timeout kills it.
HANG_COMMAND = ['bash', '-c', 'sleep 30 & sleep 30']

CHILD_SOURCE = '''
import importlib.util, subprocess, sys, time
spec = importlib.util.spec_from_file_location("ping_dots", sys.argv[1])
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
try:
    m.run_with_stdin(["true"], "", timeout=5)
except TypeError:
    print("CONTRACT_MISSING_TIMEOUT_PARAM")
    sys.exit(2)
start = time.monotonic()
try:
    m.run_with_stdin(sys.argv[2:], "payload", timeout=1)
except subprocess.TimeoutExpired:
    elapsed = time.monotonic() - start
    print("TIMEOUT_RAISED %.1f" % elapsed)
    sys.exit(0 if elapsed < 5 else 3)
print("NO_TIMEOUT")
sys.exit(4)
'''


def test_regression_timeout_enforced_across_grandchildren():
    """A provider whose grandchild holds the pipe must not wedge the chain.

    Bounded via a child process so a broken implementation fails instead of
    hanging the suite; the child kills nothing itself.
    """
    child = subprocess.Popen(
        [sys.executable, '-c', CHILD_SOURCE, str(SCRIPT), *HANG_COMMAND],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        start_new_session=True)
    try:
        stdout, stderr = child.communicate(timeout=15)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
        raise AssertionError(
            'run_with_stdin blocked far past its timeout while a grandchild '
            'held the output pipe; every later provider fallback is wedged '
            f'behind one hung call. child output: {stdout!r} {stderr!r}')
    assert child.returncode == 0, (
        f'timeout contract not met (rc={child.returncode}): '
        f'{stdout!r} {stderr!r}')
    assert 'TIMEOUT_RAISED' in stdout, stdout
    elapsed = float(stdout.split()[-1])
    assert elapsed < 5, f'TimeoutExpired raised too late: {elapsed:.1f}s'


def test_fallback_chain_continues_after_provider_timeout():
    m = load_module()
    calls = []
    original = m.generate

    def fake_generate(provider):
        calls.append(provider)
        if provider == 'agy':
            raise subprocess.TimeoutExpired(cmd='agy', timeout=180)
        return m.REMINDER_BODY

    m.generate = fake_generate
    try:
        provider, message = m.generate_message(('agy', 'luna'))
    finally:
        m.generate = original
    assert provider == 'luna', provider
    assert message == m.REMINDER_BODY
    assert calls == ['agy', 'luna'], calls


def test_bounded_run_reports_send_failure_without_raising():
    m = load_module()
    result = m.bounded_run(['bash', '-c', 'exit 7'], timeout=10, check=False)
    assert result.returncode == 7
    assert result.stdout == ''


def main():
    tests = [
        test_regression_timeout_enforced_across_grandchildren,
        test_fallback_chain_continues_after_provider_timeout,
        test_bounded_run_reports_send_failure_without_raising,
    ]
    failures = 0
    for test in tests:
        start = time.monotonic()
        try:
            test()
        except Exception as error:
            failures += 1
            print(f'FAIL {test.__name__}: {error}')
        else:
            print(f'PASS {test.__name__} ({time.monotonic() - start:.1f}s)')
    print(f'{len(tests) - failures}/{len(tests)} passed')
    return 1 if failures else 0


if __name__ == '__main__':
    raise SystemExit(main())
