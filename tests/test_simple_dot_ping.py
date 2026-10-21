"""Fail-closed contract tests for the scheduler-bound Pi coordinator launcher."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import fcntl
import hashlib
import io
import json
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.claude/skills/agy-dot-coordinator/scripts/ping-dots.py'
SPEC = importlib.util.spec_from_file_location('dot_coordinator_launcher', SCRIPT)
PING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PING)


class LauncherContractTests(unittest.TestCase):
    def test_account_is_mandatory_and_rejects_injection(self):
        with patch.object(sys, 'argv', ['ping-dots.py']):
            with self.assertRaises(SystemExit):
                PING.main()
        with patch.object(sys, 'argv', ['ping-dots.py', '--account', '../other']):
            with self.assertRaises(PING.Blocked):
                PING.main()

    def test_missing_identity_binding_fails_before_config_or_process_launch(self):
        with patch.dict(os.environ, {'DOT_EXPECTED_IDENTITY_SHA256': ''}):
            with patch.object(sys, 'argv', ['ping-dots.py', '--account', 'alpha']):
                with self.assertRaisesRegex(PING.Blocked, 'identity binding'):
                    PING.main()

    def test_dangling_singleton_lock_is_detected(self):
        import tempfile
        with tempfile.TemporaryDirectory(dir='/tmp') as temp:
            profile = Path(temp)
            (profile / 'SingletonLock').symlink_to(profile / 'missing-target')
            self.assertFalse((profile / 'SingletonLock').exists())
            self.assertTrue(os.path.lexists(profile / 'SingletonLock'))
            self.assertIn("os.path.lexists(profile / 'SingletonLock')", SCRIPT.read_text())

    def test_pending_send_lifecycle_is_owned_by_markdown_agent(self):
        source = SCRIPT.read_text()
        skill = (SCRIPT.parent.parent / 'SKILL.md').read_text()
        self.assertIn('COORDINATOR_PENDING_FILE', source)
        self.assertIn('COORDINATOR_PENDING_FILE', skill)
        self.assertIn('atomically create', skill)
        self.assertIn('sending nothing', skill)
        self.assertNotIn('COORDINATOR_OUTCOME', source)
        self.assertNotIn('send_unknown', source)
        self.assertNotIn('--provider', source)
        self.assertNotIn('--model', source)
        self.assertIn('read-only', skill)
        self.assertIn('Use only the directly exposed `mcp__dot_browser__*` tools', skill)
        self.assertIn('Do not invoke nested Pi/runtime sessions, Codemode', skill)
        self.assertIn('do not retry or send a correction', skill.lower())

    def test_stop_and_legacy_delivery_holds_block_fresh_send(self):
        skill = (SCRIPT.parent.parent / 'SKILL.md').read_text()
        self.assertIn('Before preparing any fresh message', skill)
        self.assertIn('os.path.lexists', skill)
        self.assertIn('state.json', skill)
        self.assertIn('state_<COORDINATOR_SELECTED_ACCOUNT>.json', skill)
        self.assertIn('unresolved or unknown delivery', skill)
        self.assertIn('unreadable, corrupt, or ambiguous', skill)
        self.assertIn('Immediately before the submit click', skill)
        self.assertIn('recheck `<parent>/STOP`', skill)
        self.assertIn('exact unchanged payload', skill)
        self.assertIn('latest user instruction', skill)
        self.assertIn('they cannot authorize a send', skill)
        self.assertIn('flush the file and its parent directory', skill.lower())
        self.assertIn('do not claim mechanical exactly-once delivery', skill)

    def test_scheduler_wrapper_is_thin_and_does_not_choose_account(self):
        wrapper = (SCRIPT.parent / 'agy-dot-coordinator-wrapper.sh').read_text()
        self.assertIn('exec python3', wrapper)
        self.assertNotIn('--account', wrapper)
        self.assertNotIn('rotation', wrapper)


class FakePiProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode
        self.pid = 2_000_000_000
    def poll(self): return self.returncode
    def communicate(self, timeout): return ('agent result', '')
    def terminate(self): self.returncode = -15
    def wait(self, timeout=None): return self.returncode


class LauncherExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.profile = self.home / 'profile'
        (self.profile / 'Default').mkdir(parents=True)
        self.state = self.home / 'state'
        self.lock = self.home / 'coordinator.lock'
        self.lock_base = self.home / 'locks'
        self.config = self.home / 'dot.json'
        self.config.write_text(json.dumps({'accounts': {'alpha': {
            'user_data_dir': str(self.profile), 'profile_directory': 'Default',
            'url': 'https://example.invalid/chat'}}}))
        self.chrome = self.home / 'chrome'
        self.chrome.touch()
        self.pi = self.home / 'pi'
        self.pi.touch()
        self.node_home = self.home / '.nvm/versions/node/v22.22.0'
        (self.node_home / 'bin').mkdir(parents=True)
        (self.node_home / 'bin/node').touch()
        self.mcp = self.node_home / 'lib/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js'
        self.mcp.parent.mkdir(parents=True)
        self.mcp.touch()
        (self.node_home / 'lib/node_modules/chrome-devtools-mcp/package.json').write_text(json.dumps({'version': '1.6.0'}))
        self.pi_config = self.home / '.pi/agent'
        self.pi_config.mkdir(parents=True)
        (self.pi_config / 'mcp.json').write_text(json.dumps({'mcpServers': {'unrelated': {'command': 'no-start'}}}))
        self.env = {
            'HOME': str(self.home), 'DOT_EXPECTED_IDENTITY_SHA256': 'a' * 64,
            'DOT_CONFIG_FILE': str(self.config), 'DOT_CHROME_BIN': str(self.chrome),
            'CHROME_DEVTOOLS_MCP_JS': str(self.mcp), 'PI_BIN': str(self.pi),
            'PI_CODING_AGENT_DIR': str(self.pi_config), 'COORDINATOR_STATE_DIR': str(self.state),
            'COORDINATOR_LOCK_FILE': str(self.lock), 'DOT_LOCK_BASE': str(self.lock_base),
            'DISPLAY': ':9', 'PATH': str(self.node_home / 'bin') + os.pathsep + os.environ.get('PATH', ''),
        }

    def invoke(self, fake_proc=None, on_spawn=None):
        spawned = {}
        def spawn(command, **options):
            spawned['command'] = command
            spawned['mcp'] = json.loads((Path(options['cwd']) / '.pi/mcp.json').read_text())
            if on_spawn: return on_spawn(command, **options)
            return fake_proc or FakePiProcess()
        with ExitStack() as stack:
            stack.enter_context(patch.object(PING.Path, 'home', return_value=self.home))
            stack.enter_context(patch.object(PING, 'STATE', self.state))
            stack.enter_context(patch.object(PING, 'STOP', self.state / 'STOP'))
            stack.enter_context(patch.object(PING, 'LOCK', self.lock))
            stack.enter_context(patch.dict(os.environ, self.env, clear=False))
            stack.enter_context(patch.object(PING.subprocess, 'check_output', return_value=''))
            stack.enter_context(patch.object(PING.subprocess, 'Popen', side_effect=spawn))
            stack.enter_context(patch.object(sys, 'argv', ['ping-dots.py', '--account', 'alpha']))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                result = PING.main()
        return result, spawned

    def test_launcher_uses_owned_mcp_with_isolated_global_config(self):
        result, spawned = self.invoke()
        self.assertEqual(result, 0)
        servers = spawned['mcp']['mcpServers']
        self.assertFalse(servers['unrelated']['enabled'])
        browser = servers['dot_browser']
        self.assertEqual(browser['exposure'], 'direct')
        self.assertEqual(browser['command'], str(self.node_home / 'bin/node'))
        self.assertIn(str(self.mcp), browser['args'])
        self.assertIn('--userDataDir=' + str(self.profile.resolve()), browser['args'])
        self.assertFalse({'--provider', '--model'} & set(spawned['command']))

    def test_attempt_receipt_survives_cleanup_and_new_invocation_gets_new_path(self):
        receipts = []
        def agent(command, **options):
            receipt = Path(options['env']['COORDINATOR_ATTEMPT_FILE'])
            self.assertEqual(receipt.parent, self.state)
            # Model the prescribed artifact operation, not real browser delivery.
            fd = os.open(receipt, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.write(fd, b'{"payload_sha256":"test","attempted":true}')
            os.close(fd)
            for scenario in ('ACK arrived', 'revised payload', 'pending removed'):
                with self.subTest(scenario=scenario):
                    with self.assertRaises(FileExistsError):
                        os.open(receipt, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            receipts.append(receipt)
            return FakePiProcess()
        self.invoke(on_spawn=agent)
        self.assertTrue(receipts[0].is_file())
        self.invoke(on_spawn=agent)
        self.assertNotEqual(*receipts)
        self.assertTrue(all(path.is_file() for path in receipts))

    def test_configured_cli_prefix_is_literal_argv(self):
        prefix = ['--thinking', 'medium', 'literal spaces; $HOME $(never-run)']
        self.env['COORDINATOR_CLI_ARGS'] = json.dumps(prefix)
        _, spawned = self.invoke()
        self.assertEqual(spawned['command'][:1 + len(prefix)], [str(self.pi), *prefix])

    def test_invalid_cli_prefix_is_rejected_before_spawn(self):
        for value in ('"--thinking medium"', '{}', '[4]', '["bad\\u0000arg"]'):
            with self.subTest(value=value):
                self.env['COORDINATOR_CLI_ARGS'] = value
                with self.assertRaisesRegex(PING.Blocked, 'CLI arguments'):
                    self.invoke()

    def test_stop_dangling_symlink_prevents_pi_spawn(self):
        self.state.mkdir()
        (self.state / 'STOP').symlink_to(self.home / 'missing-stop-target')
        spawned = []
        with self.assertRaisesRegex(PING.Blocked, 'STOP marker'):
            self.invoke(on_spawn=lambda *args, **kwargs: spawned.append(args))
        self.assertEqual(spawned, [])

    def test_global_and_profile_locks_prevent_pi_spawn(self):
        self.lock.parent.mkdir(parents=True, exist_ok=True)
        with self.lock.open('a') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            spawned = []
            with self.assertRaisesRegex(PING.Blocked, 'coordinator lock'):
                self.invoke(on_spawn=lambda *args, **kwargs: spawned.append(args))
            self.assertEqual(spawned, [])
        path = self.lock_base / 'dot-profile-locks' / (hashlib.sha256(str(self.profile.resolve()).encode()).hexdigest()[:16] + '.lock')
        path.parent.mkdir(parents=True)
        with path.open('a') as held:
            fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
            spawned = []
            with self.assertRaisesRegex(PING.Blocked, 'shared Dot profile lock'):
                self.invoke(on_spawn=lambda *args, **kwargs: spawned.append(args))
            self.assertEqual(spawned, [])

    def test_timeout_terminates_pi_and_preserves_agent_owned_marker(self):
        class TimedOut(FakePiProcess):
            def __init__(self): self.returncode, self.pid = None, 2_000_000_000
            def communicate(self, timeout): raise subprocess.TimeoutExpired('pi', timeout)
            def terminate(self): self.returncode = -15
        old_timeout = PING.TIMEOUT
        self.addCleanup(setattr, PING, 'TIMEOUT', old_timeout)
        PING.TIMEOUT = 1
        self.state.mkdir()
        pending = self.state / ('send-' + hashlib.sha256(b'alpha').hexdigest()[:16] + '.pending')
        pending.write_text('private send intent')
        process = TimedOut()
        with self.assertRaisesRegex(PING.Blocked, 'deadline'):
            self.invoke(process)
        self.assertEqual(process.returncode, -15)
        self.assertEqual(pending.read_text(), 'private send intent')

    def test_sigterm_cleans_pi_process_group_before_releasing_locks(self):
        ready, cleaned = self.home / 'child.ready', self.home / 'child.cleaned'
        child = self.home / 'child.py'
        child.write_text('''import fcntl, os, signal, time
from pathlib import Path
def cleanup(*_):
    with open(os.environ["COORDINATOR_LOCK_FILE"], "a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            state = "released"
        except BlockingIOError:
            state = "held"
    Path(os.environ["DOT_CHILD_CLEANED_FILE"]).write_text(state)
    raise SystemExit
signal.signal(signal.SIGTERM, cleanup)
Path(os.environ["DOT_CHILD_READY_FILE"]).write_text("ready")
time.sleep(60)
''')
        self.pi.write_text(f'''#!{sys.executable}
import os, subprocess, sys, time
from pathlib import Path
child = subprocess.Popen([sys.executable, {str(child)!r}])
Path(os.environ["DOT_CHILD_PID_FILE"]).write_text(str(child.pid))
time.sleep(60)
''')
        self.pi.chmod(0o755)
        env = dict(os.environ, **self.env, DOT_CHILD_SCRIPT=str(child),
                   DOT_CHILD_PID_FILE=str(self.home / 'child.pid'),
                   DOT_CHILD_READY_FILE=str(ready), DOT_CHILD_CLEANED_FILE=str(cleaned))
        harness = f'''import importlib.util, sys
spec = importlib.util.spec_from_file_location("dot_launcher", {str(SCRIPT)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.GRACE = 0.4
sys.argv = [{str(SCRIPT)!r}, "--account", "alpha"]
module.main()
'''
        launcher = subprocess.Popen([sys.executable, '-c', harness], env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(ready.exists(), 'dummy owned child did not start')
            launcher.terminate()
            launcher.communicate(timeout=5)
            self.assertEqual(launcher.returncode, 128 + PING.signal.SIGTERM)
            self.assertEqual(cleaned.read_text(), 'held')
            with self.lock.open('a') as contender:
                fcntl.flock(contender, fcntl.LOCK_EX | fcntl.LOCK_NB)
        finally:
            if launcher.poll() is None: launcher.kill()
            launcher.wait()
            launcher.stdout.close()
            launcher.stderr.close()

    def test_nonzero_exit_preserves_agent_owned_marker(self):
        self.state.mkdir()
        pending = self.state / ('send-' + hashlib.sha256(b'alpha').hexdigest()[:16] + '.pending')
        pending.write_text('private send intent')
        with self.assertRaisesRegex(PING.Blocked, 'inspect pending-send state'):
            self.invoke(FakePiProcess(returncode=7))
        self.assertEqual(pending.read_text(), 'private send intent')


if __name__ == '__main__':
    unittest.main()
