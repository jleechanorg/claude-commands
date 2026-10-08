"""Internally resolved no-tool CLI profile and private execution fingerprints.

This constrains CLI tools; it is not an OS sandbox. Local installed executables
and managed policy remain trusted. Caller JSON cannot establish admission.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import tempfile
import time

from modules.process_utils import run_bounded_command

PROFILE_VERSION = 'claude-no-tools-v1'
REQUIRED_FLAGS = ('--tools', '--restricted', '--safe-mode', '--strict-mcp-config',
    '--mcp-config', '--disable-slash-commands', '--no-chrome', '--no-session-persistence',
    '--permission-mode', '--permission-prompts', '--setting-sources')
CLAUDE_ARGS = ('-p', '--output-format', 'json', '--verbose', '--restricted', '--safe-mode',
    '--tools', '', '--strict-mcp-config', '--mcp-config', '{"mcpServers":{}}',
    '--disable-slash-commands', '--no-chrome', '--no-session-persistence',
    '--setting-sources', '', '--permission-mode', 'dontAsk', '--permission-prompts', 'none')
ENV_KEYS = frozenset(('HOME', 'PATH', 'TMPDIR', 'TMP', 'TEMP', 'USER', 'LOGNAME',
    'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'TERM', 'SSL_CERT_FILE', 'SSL_CERT_DIR',
    'CLAUDE_CONFIG_DIR', 'CLAUDE_CODE_OAUTH_TOKEN'))


def decision_environment(environment=None):
    environment = os.environ if environment is None else environment
    return {key: value for key, value in environment.items() if key in ENV_KEYS}


def file_fingerprint(filename, *, native=False):
    try:
        selected = Path(filename).absolute()
        resolved = selected.resolve(strict=True)
        info = resolved.stat()
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('execution_dependency_unavailable')
        with resolved.open('rb') as stream:
            if native:
                if not os.access(resolved, os.X_OK) or stream.read(4) not in (
                        b'\x7fELF', b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf',
                        b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
                    raise ValueError('native_executable_required')
                stream.seek(0)
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        return {'selected_path': str(selected), 'resolved_path': str(resolved), 'sha256': digest}
    except OSError as error:
        raise ValueError('execution_dependency_unavailable') from error


def resolve_decision_profile(driver, executable, timeout_secs=20):
    # No execution of unverified script launchers, including AGY's trust-writing
    # wrapper. Read-only Codex still permits private reads; do not silently fall back.
    if driver != 'claude':
        raise ValueError('capability_blocked')
    identity = file_fingerprint(executable, native=True)
    env = decision_environment()
    deadline = time.monotonic() + timeout_secs
    with tempfile.TemporaryDirectory(prefix='dot-admission-', dir='/tmp') as root:
        def inspect(args):
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise ValueError('capability_blocked')
            rc, stdout, _ = run_bounded_command([identity['resolved_path'], *args],
                cwd=root, timeout_secs=remaining, env=env)
            if rc != 0:
                raise ValueError('capability_blocked')
            return stdout
        help_text = inspect(('--safe-mode', '--help'))
        if not all(flag in help_text for flag in REQUIRED_FLAGS):
            raise ValueError('capability_blocked')
        # Status is read-only; require existing first-party subscription auth.
        # API keys/provider routing are neither inherited nor newly configured.
        try:
            auth = json.loads(inspect(('--safe-mode', 'auth', 'status', '--json')))
        except (TypeError, json.JSONDecodeError) as error:
            raise ValueError('subscription_auth_required') from error
        if (not isinstance(auth, dict) or auth.get('loggedIn') is not True or
                auth.get('authMethod') != 'claude.ai' or auth.get('apiProvider') != 'firstParty' or
                auth.get('subscriptionType') not in ('pro', 'max', 'team', 'enterprise')):
            raise ValueError('subscription_auth_required')
    profile = {'version': PROFILE_VERSION, 'driver': driver, 'executable': identity, 'args': CLAUDE_ARGS}
    if not profile_unchanged(profile):
        raise ValueError('execution_dependency_changed')
    return profile


def profile_unchanged(profile):
    try:
        return file_fingerprint(profile['executable']['selected_path'], native=True) == profile['executable']
    except (KeyError, TypeError, ValueError):
        return False


def transport_node():
    # Match dot.sh selection, including its prepended search directories.
    if os.environ.get('DOT_NODE'):
        selected = os.environ['DOT_NODE']
    else:
        preferred = Path.home()/'.nvm/versions/node/v22.22.0/bin/node'
        search = os.pathsep.join(('/opt/homebrew/bin', '/usr/local/bin', str(Path.home()/'.local/bin'), os.environ.get('PATH', '')))
        selected = str(preferred) if os.access(preferred, os.X_OK) else shutil.which('node', path=search)
        if not selected:
            versions = sorted((Path.home()/'.nvm/versions/node').glob('v*'))
            selected = str(versions[-1]/'bin/node') if versions else '/usr/local/bin/node'
    return file_fingerprint(selected, native=True)


def execution_dependencies(profile, transport):
    if not profile_unchanged(profile):
        raise ValueError('execution_dependency_changed')
    selected = Path(transport).absolute()
    return {'schema_version': 1, 'decision_profile': profile,
            'transport': file_fingerprint(selected),
            'chrome_script': file_fingerprint(selected.parent/'dot_chrome.mjs'),
            'node': transport_node()}
