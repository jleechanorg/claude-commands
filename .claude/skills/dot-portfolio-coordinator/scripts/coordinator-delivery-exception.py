"""One separately authorized delivery without clearing a historical receipt hold.

Local operator pins are trusted inputs, not independently authenticated human
approval. One claim per preserved hold is consumed before sender invocation,
including crashes/timeouts. There is deliberately no reset or retry command.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
from modules.process_utils import run_bounded_command
from modules.sender import ACCOUNT_RE, _atomic_write, validate_operator_grant


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def private_directory(path, create=False):
    if create:
        path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('invalid_private_directory')


def owned_bytes(path, *, private=True):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
                raise ValueError('invalid_owned_file')
            if private and info.st_mode & 0o077:
                raise ValueError('file_not_private')
            raw = stream.read(1_000_001)
        if len(raw) > 1_000_000:
            raise ValueError('file_too_large')
        return raw
    except OSError as error:
        raise ValueError('file_unavailable') from error


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def execute(manifest_file, expected_sha):
    manifest_path = Path(manifest_file)
    private_directory(manifest_path.parent)
    raw = owned_bytes(manifest_path)
    if digest(raw) != expected_sha:
        raise ValueError('manifest_hash_mismatch')
    data = json.loads(raw)
    fields = {'schema_version', 'authorization_ref', 'account', 'historical_ledger',
        'historical_ledger_sha256', 'historical_event_id', 'historical_message_sha256',
        'event_id', 'message_file', 'message_sha256', 'grant_file', 'grant_sha256',
        'destination', 'config_file', 'config_sha256', 'transport', 'transport_sha256',
        'chrome_sha256', 'node', 'node_sha256'}
    if (not isinstance(data, dict) or set(data) != fields or
            type(data['schema_version']) is not int or data['schema_version'] != 1 or
            any(not isinstance(data[k], str) or not data[k] for k in fields-{'schema_version'})):
        raise ValueError('invalid_exception_manifest')
    account = data['account']
    if not ACCOUNT_RE.fullmatch(account) or account in ('.', '..'):
        raise ValueError('invalid_account')
    if len(data['authorization_ref']) > 500 or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', data['event_id']):
        raise ValueError('invalid_exception_identity')
    if data['event_id'] == data['historical_event_id'] or data['message_sha256'] == data['historical_message_sha256']:
        raise ValueError('historical_attempt_cannot_be_retried')
    for key in fields:
        if key.endswith('sha256') and not re.fullmatch(r'[a-f0-9]{64}', data[key]):
            raise ValueError('invalid_digest')
    if not re.fullmatch(r'https://chatgpt\.com/dots/[a-f0-9-]{36}', data['destination']):
        raise ValueError('invalid_destination')
    old_path = Path(data['historical_ledger'])
    if old_path.name != f'account_{account}.json':
        raise ValueError('historical_account_mismatch')
    private_directory(old_path.parent)
    lock_fd = os.open(old_path.parent/'sender.lock', os.O_RDWR | os.O_NOFOLLOW)
    try:
        info = os.fstat(lock_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('invalid_historical_lock')
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        historical = owned_bytes(old_path)
        if digest(historical) != data['historical_ledger_sha256']:
            raise ValueError('historical_ledger_changed')
        previous = json.loads(historical)
        pending = previous.get('pending_delivery')
        if (not isinstance(pending, dict) or pending.get('account') != account or
                pending.get('event_id') != data['historical_event_id'] or
                pending.get('message_sha256') != data['historical_message_sha256'] or
                data['event_id'] in previous.get('retained_event_ids', [])):
            raise ValueError('historical_hold_binding_mismatch')
        # Canonical sibling location: changing manifest/event/output paths cannot
        # obtain another attempt for this same preserved hold.
        root = old_path.parent.with_name(old_path.parent.name + '.exception-' + digest(historical))
        private_directory(root, create=True)
        sync_directory(root.parent)
        claim_path = root/'attempt.json'
        if os.path.lexists(claim_path):
            raise ValueError('exception_already_consumed')
        message = owned_bytes(Path(data['message_file']))
        text = message.decode('utf-8')
        if digest(message) != data['message_sha256'] or text != text.strip() or not 1 <= len(text) <= 32000:
            raise ValueError('message_binding_mismatch')
        valid, _, grant = validate_operator_grant(data['grant_file'], data['grant_sha256'], account)
        if (not valid or grant['action'] != 'send_dot_test_message' or grant['max_messages'] != 1 or
                grant['expiry_epoch']-grant['activated_at_epoch'] > 900 or
                grant['expiry_epoch']-time.time() < 660):
            raise ValueError('single_finite_grant_required')
        config_raw = owned_bytes(Path(data['config_file']), private=False)
        if digest(config_raw) != data['config_sha256']:
            raise ValueError('configuration_changed')
        config = json.loads(config_raw).get('accounts', {}).get(account, {})
        if config.get('url') != data['destination'] or not config.get('user_data_dir') or '@' not in config.get('profile_match', ''):
            raise ValueError('configured_destination_or_identity_mismatch')
        profile = Path(config['user_data_dir']).expanduser()
        if not profile.is_dir():
            raise ValueError('existing_profile_required')
        node_input = Path(data['node'])
        if not node_input.is_absolute():
            raise ValueError('absolute_node_path_required')
        node = node_input.resolve(strict=True)
        transport = Path(data['transport'])
        def verify_transport():
            if node_input.resolve(strict=True) != node or not os.access(node, os.X_OK):
                raise ValueError('node_changed')
            with node.open('rb') as stream:
                if stream.read(4) not in (b'\x7fELF', b'\xcf\xfa\xed\xfe', b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'):
                    raise ValueError('native_node_required')
                stream.seek(0)
                actual = hashlib.file_digest(stream, 'sha256').hexdigest()
            if actual != data['node_sha256']:
                raise ValueError('node_changed')
            if (digest(owned_bytes(transport, private=False)) != data['transport_sha256'] or
                    digest(owned_bytes(transport.parent/'dot_chrome.mjs', private=False)) != data['chrome_sha256']):
                raise ValueError('transport_changed')
        verify_transport()
        env = {k: v for k, v in os.environ.items() if not k.startswith(('DOT_', 'COORDINATOR_'))
               and k not in ('NODE_OPTIONS', 'NODE_PATH')}
        env.update(DOT_NODE=str(node), DOT_ACCOUNT=account, DOT_CONFIG_FILE=data['config_file'],
            DOT_URL=data['destination'], DOT_CHROME_USER_DATA=str(profile), DOT_BACKEND='chrome',
            DOT_NO_REMOTE='1', DOT_ROTATE_ON_LIMIT='0', DOT_EXISTING_PROFILE_ONLY='1')
        expected_identity = digest(config['profile_match'].encode('utf-8'))
        rc, output, _ = run_bounded_command([str(transport), '--account', account, 'probe', expected_identity],
            cwd=str(root), timeout_secs=60, env=env)
        frames = [json.loads(line[len('DOT_SESSION_PROBE '):]) for line in output.splitlines()
                  if line.startswith('DOT_SESSION_PROBE ')]
        if rc != 0 or len(frames) != 1:
            raise ValueError('identity_probe_failed')
        probe = frames[0]
        age = (datetime.now(timezone.utc)-datetime.fromisoformat(probe.get('timestamp', '').replace('Z', '+00:00'))).total_seconds()
        if (type(probe.get('schema_version')) is not int or probe['schema_version'] != 1 or
                probe.get('status') != 'authenticated' or probe.get('identity_match') is not True or
                probe.get('endpoint_status') != 200 or
                probe.get('cleanup_state') not in ('context_closed', 'browser_disconnected') or not -5 <= age <= 60):
            raise ValueError('identity_probe_failed')
        verify_transport()
        if owned_bytes(old_path) != historical:
            raise ValueError('historical_ledger_changed')
        backup = root/'historical-ledger.json'
        if os.path.lexists(backup):
            if owned_bytes(backup) != historical:
                raise ValueError('backup_mismatch')
        else:
            fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(historical)
                stream.flush()
                os.fsync(stream.fileno())
        sender_state = root/'sender'
        private_directory(sender_state, create=True)
        claim = {k: data[k] for k in ('authorization_ref', 'account', 'event_id', 'message_sha256',
                                    'historical_ledger', 'historical_ledger_sha256',
                                    'historical_event_id', 'historical_message_sha256', 'grant_sha256', 'destination')}
        claim.update(schema_version=1, manifest_sha256=expected_sha, consumed_at_epoch=time.time())
        _atomic_write(str(claim_path), claim, str(root))
        sync_directory(root)  # Durable claim before the first possible send.
        env.update(COORDINATOR_CHANGE_ID=data['event_id'], COORDINATOR_CHANGE_SUMMARY=text)
        command = [sys.executable, str(SCRIPTS/'modules/sender.py'), '--account', account,
            '--state-dir', str(sender_state), '--grant-file', data['grant_file'],
            '--grant-sha256', data['grant_sha256'], '--transport-script', str(transport)]
        verified = False
        try:
            rc, output, _ = run_bounded_command(command, cwd=str(root), timeout_secs=650, env=env)
            results = [json.loads(line[len('COORDINATOR_RESULT '):]) for line in output.splitlines()
                       if line.startswith('COORDINATOR_RESULT ')]
            verified = (rc == 0 and len(results) == 1 and results[0].get('delivery_verified') is True and
                        results[0].get('outcome') == 'delivered' and results[0].get('account') == account and
                        results[0].get('event_id') == data['event_id'])
        except Exception:
            pass  # Claim stays consumed, including timeout and malformed result.
        unchanged = owned_bytes(old_path) == historical
        result = {'schema_version': 1, 'event_id': data['event_id'], 'message_sha256': data['message_sha256'],
            'delivery_verified': verified and unchanged, 'historical_ledger_unchanged': unchanged,
            'exception_state': str(root), 'completed_at_epoch': time.time()}
        _atomic_write(str(root/'result.json'), result, str(root))
        sync_directory(root)
        return result
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        os.close(lock_fd)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--sha256', required=True)
    args = parser.parse_args()
    try:
        result = execute(args.manifest, args.sha256)
        print('COORDINATOR_EXCEPTION_RESULT '+json.dumps(result, sort_keys=True))
        raise SystemExit(0 if result['delivery_verified'] else 4)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print('COORDINATOR_EXCEPTION_RESULT '+json.dumps({'delivery_verified': False,
            'reason': str(error) if isinstance(error, ValueError) and re.fullmatch(r'[a-z_]{1,80}', str(error)) else 'exception_preflight_failed'}))
        raise SystemExit(2)
