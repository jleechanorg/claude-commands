#!/usr/bin/env python3
"""Run one scheduler-bound Dot coordinator turn using Pi and Chrome DevTools MCP."""
import argparse, json, os, re, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_native_schedule import node22_bins
SKILL = Path(__file__).resolve().parents[1] / 'SKILL.md'
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36'
TIMEOUT, GRACE = max(int(os.environ.get('COORDINATOR_TIMEOUT_SECS', '720')), 1), 8
class Blocked(RuntimeError):
    pass
def stop(proc):
    if not proc: return
    if proc.poll() is None:
        try: proc.terminate()
        except ProcessLookupError: pass
    deadline = time.monotonic() + GRACE
    while time.monotonic() < deadline:
        if proc.poll() is None:
            time.sleep(.1)
            continue
        try: os.killpg(proc.pid, 0)
        except ProcessLookupError: return
        time.sleep(.1)
    try: os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError: return
    try: proc.wait(timeout=GRACE)
    except subprocess.TimeoutExpired: pass
    time.sleep(GRACE)
    try: os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError: pass
def open_pi_log(account):
    fd, name = tempfile.mkstemp(prefix=f'dot-coordinator-pi-{account}-', suffix='.log', dir=tempfile.gettempdir())
    os.fchmod(fd, 0o600); return fd, Path(name)
def finalize_pi_log(pi_log, expected):
    text = pi_log.read_text(errors='replace').replace(expected, '[identity redacted]')
    pi_log.write_text(text); return text
def main():
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--account', required=True, help='Exact machine-local Dot account key supplied by scheduler')
    p.add_argument('--instruction', default=os.environ.get('COORDINATOR_TASK', ''), help='Owner-provided task context or mode')
    args = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9._@+-]{1,160}', args.account): raise Blocked('invalid account key')
    cli_args = json.loads(os.environ.get('COORDINATOR_CLI_ARGS', '[]'))
    if not isinstance(cli_args, list) or any(not isinstance(arg, str) or any(ord(c) < 32 or ord(c) == 127 for c in arg) for arg in cli_args): raise Blocked('CLI arguments must be a JSON array of strings without control characters')
    expected = os.environ.get('DOT_EXPECTED_IDENTITY_SHA256', '').lower()
    if not re.fullmatch(r'[0-9a-f]{64}', expected): raise Blocked('expected identity binding is missing or invalid')
    node_bins = node22_bins(Path.home())
    if not node_bins: raise Blocked('Node 22 executable is unavailable')
    node_dir = node_bins[0]
    os.environ['PATH'] = str(node_dir) + os.pathsep + str(Path.home() / '.local/bin') + os.pathsep + os.environ.get('PATH', '')
    config = json.loads(Path(os.environ.get('DOT_CONFIG_FILE', '~/.config/dot/config.json')).expanduser().read_text())
    accounts = config.get('accounts', {})
    if not isinstance(accounts, dict) or args.account not in accounts: raise Blocked('account is not configured')
    info = accounts[args.account]
    if not isinstance(info, dict) or not info.get('user_data_dir'): raise Blocked('account profile root is not configured')
    profile = Path(os.path.abspath(re.sub(r'^~', lambda _: str(Path.home()), info['user_data_dir'])))
    if profile.is_symlink(): raise Blocked('Dot profile root cannot be a symbolic link')
    canonical = profile.resolve()
    subprofile = info.get('profile_directory', 'Default')
    target = info.get('url') or config.get('default_url')
    if (not profile.is_dir() or not isinstance(subprofile, str) or subprofile in ('', '.', '..') or
        '/' in subprofile or '\\' in subprofile or (profile / subprofile).is_symlink() or not (profile / subprofile).is_dir()):
        raise Blocked('configured profile is unavailable')
    if not isinstance(target, str) or not target.startswith(('https://', 'http://')) or any(c.isspace() for c in target):
        raise Blocked('configured target URL is unavailable')
    chrome_root = (Path.home() / ('Library/Application Support/Google/Chrome' if sys.platform == 'darwin' else '.config/google-chrome')).resolve()
    if canonical == chrome_root or canonical in chrome_root.parents or chrome_root in canonical.parents:
        raise Blocked('Dot profile overlaps system Chrome profile')
    proc = None
    try:
        if os.path.lexists(profile / 'SingletonLock'): raise Blocked('Chrome or a stale SingletonLock already owns this Dot profile')
        if any(str(profile) in row and 'Chrome' in row for row in subprocess.check_output(['ps', '-Ao', 'args'], text=True).splitlines()):
            raise Blocked('a Chrome process already uses this Dot profile')
        chrome_bin = os.environ.get('DOT_CHROME_BIN') or ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' if sys.platform == 'darwin' else '/usr/bin/google-chrome')
        mcp_bin = Path(os.environ.get('CHROME_DEVTOOLS_MCP_JS', node_dir.parent / 'lib/node_modules/chrome-devtools-mcp/build/src/bin/chrome-devtools-mcp.js')).expanduser()
        pi_bin = os.environ.get('PI_BIN') or shutil.which('pi')
        if not Path(chrome_bin).is_file() or not mcp_bin.is_file() or not pi_bin: raise Blocked('system Chrome, pinned Chrome DevTools MCP 1.6, or Pi is unavailable')
        if json.loads((mcp_bin.parents[3] / 'package.json').read_text()).get('version') != '1.6.0': raise Blocked('Chrome DevTools MCP must be version 1.6.0')
        mcp_args = [str(mcp_bin), '--executablePath=' + chrome_bin, '--userDataDir=' + str(profile),
            '--chromeArg=--profile-directory=' + subprofile, '--chromeArg=--user-agent=' + UA,
            '--chromeArg=--disable-blink-features=AutomationControlled',
            '--chromeArg=--no-first-run', '--chromeArg=--no-default-browser-check',
            '--ignoreDefaultChromeArg=--enable-automation', '--ignoreDefaultChromeArg=--password-store=basic',
            '--ignoreDefaultChromeArg=--use-mock-keychain']
        if sys.platform == 'darwin': mcp_args += ['--headless', '--chromeArg=--password-store=keychain']
        else:
            if not (os.environ.get('DISPLAY') or os.environ.get('DBUS_SESSION_BUS_ADDRESS')): raise Blocked('Linux keychain session is unavailable')
            mcp_args.append('--chromeArg=--password-store=gnome-libsecret')
            if not os.environ.get('DISPLAY'): mcp_args.append('--headless')
        with tempfile.TemporaryDirectory(prefix='dot-agent-', dir='/tmp') as run_dir:
            project = Path(run_dir) / '.pi'
            project.mkdir(mode=0o700)
            cfg = Path(os.environ.get('PI_CODING_AGENT_DIR', '~/.pi/agent')).expanduser() / 'mcp.json'
            names = json.loads(cfg.read_text()).get('mcpServers', {}) if cfg.exists() else {}
            if not isinstance(names, dict): raise Blocked('global Pi MCP config is invalid')
            servers = {name: {'enabled': False} for name in names}
            servers['dot_browser'] = {'command': str(node_dir / 'node'), 'args': mcp_args, 'exposure': 'direct'}
            mcp_file = project / 'mcp.json'
            mcp_file.write_text(json.dumps({'mcpServers': servers}))
            mcp_file.chmod(0o600)
            prompt = f'Account key: {args.account}\nConfigured target: {target}\nExpected identity SHA-256: {expected} (private binding; compare silently and return booleans only).\nOwner-provided task context: {args.instruction}\nRead and follow the loaded skill.'
            env = dict(os.environ, DOT_EXPECTED_IDENTITY_SHA256=expected, COORDINATOR_SELECTED_ACCOUNT=args.account, COORDINATOR_TARGET_URL=target)
            cmd = [pi_bin, *cli_args, '--print', '--no-session', '--approve', '--no-extensions', '-e', 'builtin:mcp',
                '--no-skills', '--skill', str(SKILL), '--tools', 'read,bash,edit,write,mcp__dot_browser__*', prompt]
            # Stream Pi straight to a retained log: a deadline kill must still leave
            # the evidence of how far the agent got (a piped capture discards it).
            # mkstemp creates the file exclusively with an unpredictable name, so a
            # pre-planted file or symlink cannot be substituted for the log, and the
            # single returned descriptor is the one Pi writes to.
            # Retained log (0600, exclusive name); stop the child before finalizing.
            log_fd, pi_log = open_pi_log(args.account)
            timed_out = False
            proc = subprocess.Popen(cmd, cwd=run_dir, env=env, stdout=log_fd,
                                    stderr=subprocess.STDOUT, text=True, start_new_session=True)
            os.close(log_fd)
            try: proc.wait(timeout=TIMEOUT)
            except subprocess.TimeoutExpired: timed_out = True
            if proc.poll() is None: stop(proc)
            sys.stdout.write(finalize_pi_log(pi_log, expected))
            if timed_out or proc.returncode:
                why = 'exceeded the deadline of %ds' % TIMEOUT if timed_out else 'failed (rc=%s)' % proc.returncode
                raise Blocked(f'Pi {why}; output kept at {pi_log}; verify delivery before any retry')
        return proc.returncode
    finally:
        stop(proc)

if __name__ == '__main__':
    try: raise SystemExit(main())
    except (OSError, ValueError, subprocess.SubprocessError, Blocked, json.JSONDecodeError) as error:
        print('Dot coordinator blocked: ' + str(error), file=sys.stderr)
        raise SystemExit(2)
