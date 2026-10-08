"""Offline checks for a one-use, separately authorized delivery exception."""
import hashlib
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / '.claude/skills/dot-portfolio-coordinator/scripts'
sys.path.insert(0, str(SCRIPTS))


class DeliveryExceptionTests(unittest.TestCase):
    def setUp(self):
        source = SCRIPTS / 'coordinator-delivery-exception.py'
        self.assertTrue(source.is_file(), 'one-use exception entrypoint is absent')
        spec = importlib.util.spec_from_file_location('delivery_exception', source)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.root.chmod(0o700)
        self.old = self.root / 'old-sender'
        self.old.mkdir(mode=0o700)
        (self.old / 'sender.lock').touch(mode=0o600)
        self.ledger = self.old / 'account_fixture.json'
        self.original = json.dumps({'schema_version': 1, 'attempted_count': 5,
            'retained_event_ids': ['verified-old'], 'pending_delivery': {
                'account': 'fixture', 'event_id': 'held-old',
                'message_sha256': hashlib.sha256(b'old message').hexdigest()}}).encode()
        self.ledger.write_bytes(self.original)
        self.ledger.chmod(0o600)
        self.message = self.root / 'message.txt'
        self.message.write_bytes(b'From coordinator: distinct fixture delivery test.')
        self.message.chmod(0o600)
        self.profile = self.root / 'profile'
        self.profile.mkdir(mode=0o700)
        self.target = 'https://chatgpt.com/dots/00000000-0000-0000-0000-000000000001'
        self.config = self.root / 'dot.json'
        self.config.write_text(json.dumps({'accounts': {'fixture': {
            'url': self.target, 'user_data_dir': str(self.profile),
            'profile_match': 'fixture@example.invalid'}}}))
        self.config.chmod(0o600)
        self.transport = self.root / 'dot.sh'
        self.transport.write_text('#!/bin/sh\nexit 99\n')
        self.transport.chmod(0o700)
        self.chrome = self.root / 'dot_chrome.mjs'
        self.chrome.write_text('// fixture\n')
        now = time.time()
        grant = {'grant_version': 1, 'task_id': 'dot-coordinator-separated-20261007',
            'account_id': 'fixture', 'action': 'send_dot_test_message',
            'activated_at_epoch': now - 1, 'expiry_epoch': now + 850,
            'max_messages': 1, 'min_interval_secs': 3600}
        self.grant = self.root / 'grant.json'
        self.grant.write_text(json.dumps(grant))
        self.grant.chmod(0o400)
        sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
        self.manifest = {'schema_version': 1, 'authorization_ref': 'human-new-test',
            'account': 'fixture', 'historical_ledger': str(self.ledger),
            'historical_ledger_sha256': sha(self.ledger),
            'historical_event_id': 'held-old',
            'historical_message_sha256': hashlib.sha256(b'old message').hexdigest(),
            'event_id': 'distinct-new', 'message_file': str(self.message),
            'message_sha256': sha(self.message), 'grant_file': str(self.grant),
            'grant_sha256': sha(self.grant), 'destination': self.target,
            'config_file': str(self.config), 'config_sha256': sha(self.config),
            'transport': str(self.transport), 'transport_sha256': sha(self.transport),
            'chrome_sha256': sha(self.chrome), 'node': sys.executable,
            'node_sha256': sha(Path(sys.executable).resolve())}
        self.manifest_file = self.root / 'exception.json'
        self.calls = []

    def invoke(self, *, probe_status='authenticated', send_rc=0, marker=True, real=False, timeout=False):
        if self.manifest_file.exists(): self.manifest_file.chmod(0o600)
        self.manifest_file.write_text(json.dumps(self.manifest))
        self.manifest_file.chmod(0o400)
        digest = hashlib.sha256(self.manifest_file.read_bytes()).hexdigest()
        def run(argv, **kwargs):
            self.calls.append((argv, kwargs))
            if 'probe' in argv:
                import datetime
                stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
                frame = {'schema_version': 1, 'status': probe_status,
                    'identity_match': probe_status == 'authenticated', 'endpoint_status': 200,
                    'cleanup_state': 'context_closed', 'timestamp': stamp}
                return 0, 'DOT_SESSION_PROBE '+json.dumps(frame)+'\n', ''
            if timeout: raise TimeoutError('synthetic timeout')
            result = {'outcome': 'delivered' if marker else 'uncertain',
                'delivery_verified': marker, 'event_id': 'distinct-new', 'account': 'fixture'}
            return send_rc, 'COORDINATOR_RESULT '+json.dumps(result)+'\n', ''
        with (nullcontext() if real else mock.patch.object(self.module, 'run_bounded_command', side_effect=run)):
            return self.module.execute(str(self.manifest_file), digest)

    def test_exact_new_attempt_preserves_history_and_consumes_exception(self):
        result = self.invoke()
        self.assertTrue(result['delivery_verified'])
        self.assertEqual(self.ledger.read_bytes(), self.original)
        self.assertEqual(len(self.calls), 2)
        args, kw = self.calls[-1]
        self.assertEqual(kw['env']['COORDINATOR_CHANGE_ID'], 'distinct-new')
        self.assertEqual(hashlib.sha256(kw['env']['COORDINATOR_CHANGE_SUMMARY'].encode()).hexdigest(), self.manifest['message_sha256'])
        self.assertEqual(kw['env']['DOT_URL'], self.target)
        root = Path(result['exception_state'])
        self.assertEqual((root/'historical-ledger.json').read_bytes(), self.original)
        self.assertEqual((root/'historical-ledger.json').stat().st_mode & 0o777, 0o400)
        claim = json.loads((root/'attempt.json').read_text())
        self.assertEqual(claim['authorization_ref'], 'human-new-test')
        self.assertEqual(claim['historical_ledger_sha256'], self.manifest['historical_ledger_sha256'])
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'exception_already_consumed'):
            self.invoke()
        self.assertEqual(self.calls, [])

    def test_same_hold_cannot_be_reused_with_changed_new_event(self):
        self.invoke()
        self.manifest['event_id'] = 'another-new'
        self.calls.clear()
        with self.assertRaisesRegex(ValueError, 'exception_already_consumed'):
            self.invoke()
        self.assertEqual(self.calls, [])

    def test_old_event_or_hash_is_rejected(self):
        for key, value in [('event_id', 'held-old'), ('message_sha256', self.manifest['historical_message_sha256'])]:
            with self.subTest(key=key):
                prior = self.manifest[key]
                self.manifest[key] = value
                with self.assertRaises(ValueError): self.invoke()
                self.manifest[key] = prior
        self.assertEqual(self.calls, [])

    def test_changed_ledger_message_account_or_transport_never_launches(self):
        for key, value in [('historical_ledger_sha256', '0'*64), ('message_sha256', '0'*64),
                           ('account', 'different'), ('transport_sha256', '0'*64),
                           ('config_sha256', '0'*64), ('node_sha256', '0'*64)]:
            with self.subTest(key=key):
                prior = self.manifest[key]
                self.manifest[key] = value
                with self.assertRaises(ValueError): self.invoke()
                self.manifest[key] = prior
        self.assertEqual(self.calls, [])
        self.assertEqual(self.ledger.read_bytes(), self.original)

    def test_unknown_identity_never_sends(self):
        with self.assertRaisesRegex(ValueError, 'identity_probe_failed'):
            self.invoke(probe_status='unknown')
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.ledger.read_bytes(), self.original)

    def test_unverified_send_consumes_exception_without_clearing_history(self):
        result = self.invoke(send_rc=4, marker=False)
        self.assertFalse(result['delivery_verified'])
        self.assertEqual(self.ledger.read_bytes(), self.original)
        with self.assertRaisesRegex(ValueError, 'exception_already_consumed'):
            self.invoke()

    def test_timeout_consumes_exception_before_transport_can_be_retried(self):
        result = self.invoke(timeout=True)
        self.assertFalse(result['delivery_verified'])
        self.assertEqual(self.ledger.read_bytes(), self.original)
        with self.assertRaisesRegex(ValueError, 'exception_already_consumed'):
            self.invoke()

    def test_real_sender_with_fake_transport_commits_once(self):
        commits = self.root/'commits.txt'
        body = """import datetime,json,pathlib,sys
if 'probe' in sys.argv:
    proof={'schema_version':1,'status':'authenticated','identity_match':True,'endpoint_status':200,'cleanup_state':'context_closed','timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print('DOT_SESSION_PROBE '+json.dumps(proof))
else:
    nonce='0123456789abcdef0123456789abcdef'
    print('prepared '+nonce,flush=True)
    if input() != 'commit '+nonce: raise SystemExit(7)
    with pathlib.Path(__COMMITS__).open('a') as f: f.write('commit\\n')
    print('DOT_SENT_VERIFIED',flush=True)
""".replace('__COMMITS__', repr(str(commits)))
        self.transport.write_text('#!'+sys.executable+'\n'+body)
        self.manifest['transport_sha256']=hashlib.sha256(self.transport.read_bytes()).hexdigest()
        result=self.invoke(real=True)
        self.assertTrue(result['delivery_verified'])
        self.assertEqual(commits.read_text(), 'commit\n')
        state=json.loads((Path(result['exception_state'])/'sender/account_fixture.json').read_text())
        self.assertEqual(state['attempted_count'],1)
        self.assertEqual(state['retained_event_ids'],['distinct-new'])
        self.assertIsNone(state['pending_delivery'])
        with self.assertRaisesRegex(ValueError,'exception_already_consumed'): self.invoke(real=True)
        self.assertEqual(commits.read_text(),'commit\n')
        self.assertEqual(self.ledger.read_bytes(),self.original)

    def test_history_lock_contention_prevents_all_calls(self):
        import fcntl
        with (self.old/'sender.lock').open('r') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError): self.invoke()
        self.assertEqual(self.calls, [])

    def test_symlink_history_is_rejected(self):
        alias_dir = self.root/'alias-dir'
        alias_dir.mkdir(mode=0o700)
        (alias_dir/'sender.lock').touch(mode=0o600)
        alias = alias_dir/'account_fixture.json'
        alias.symlink_to(self.ledger)
        self.manifest['historical_ledger'] = str(alias)
        with self.assertRaises(ValueError): self.invoke()
        self.assertEqual(self.calls, [])

    def test_node_replaced_during_probe_prevents_sender(self):
        native = self.root/'node-fixture'
        native.write_bytes(b'\x7fELF' + b'fixture executable')
        native.chmod(0o700)
        self.manifest['node'] = str(native)
        self.manifest['node_sha256'] = hashlib.sha256(native.read_bytes()).hexdigest()
        original_digest = self.module.digest
        def changed_digest(raw):
            value = original_digest(raw)
            # Expected identity is hashed immediately before probe invocation.
            if raw == b'fixture@example.invalid':
                native.write_bytes(b'\x7fELF' + b'replaced executable')
            return value
        with mock.patch.object(self.module, 'digest', side_effect=changed_digest):
            with self.assertRaisesRegex(ValueError, 'node_changed'):
                self.invoke()
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.ledger.read_bytes(), self.original)

    def test_expired_or_multi_attempt_grant_is_rejected(self):
        data = json.loads(self.grant.read_text())
        for field, value in [('max_messages', 2), ('expiry_epoch', time.time()-1)]:
            changed = dict(data, **{field: value})
            self.grant.chmod(0o600)
            self.grant.write_text(json.dumps(changed))
            self.grant.chmod(0o400)
            self.manifest['grant_sha256'] = hashlib.sha256(self.grant.read_bytes()).hexdigest()
            with self.assertRaises(ValueError): self.invoke()
        self.assertEqual(self.calls, [])


if __name__ == '__main__':
    unittest.main()
