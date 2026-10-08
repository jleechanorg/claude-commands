"""One trusted operator's shared, per-account admission ledger.

Run on one designated host. Existing SSH authenticates callers; tokens correlate
claims, not human authority. No lease expiry, process death or new hour clears a
pending claim. Historical sender files are read-only inputs, never reconciled.
"""
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import socket
import platform
import time
import uuid

from modules.sender import ACCOUNT_RE, _atomic_write, _read_json_file

PHASES = {'mac': 0, 'linux': 1800}
START_WINDOW = 120
MAX_CLOCK_SKEW = 60
OPERATION_WINDOW = 1200
SAFE_TERMINALS = {'no_action', 'no_eligible_task', 'cycle_complete', 'driver_failed',
                  'deadline_hold', 'grant_invalid'}


def due_slot(now, role, account_index):
    offset = PHASES[role] + account_index * 1200
    return int((now - offset) // 3600) * 3600 + offset


def private_directory(path, create=False):
    path = Path(path)
    if create:
        path.mkdir(mode=0o700, parents=False, exist_ok=True)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private_directory_required')
    return path


def authority_host_matches(config):
    return (platform.system() == 'Linux' and
            socket.gethostname() == config.get('hosts', {}).get('linux', {}).get('hostname'))


def read_pinned_bytes(path, expected_sha):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            raise ValueError('invalid_private_file')
        raw = stream.read(1_000_001)
    if len(raw) > 1_000_000 or hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('pin_mismatch')
    return raw


def read_private_pinned(path, expected_sha):
    raw = read_pinned_bytes(path, expected_sha)
    data = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('non_finite')))
    if not isinstance(data, dict):
        raise ValueError('invalid_json_object')
    return data


def load_schedule(path, expected_sha):
    data = read_private_pinned(path, expected_sha)
    if (data.get('schema_version') != 1 or not isinstance(data.get('schedule_id'), str) or
            not ACCOUNT_RE.fullmatch(data['schedule_id']) or not data.get('authority') or
            not isinstance(data.get('accounts'), list) or len(data['accounts']) != 3 or
            len({a.get('account') for a in data['accounts']}) != 3 or
            any(not ACCOUNT_RE.fullmatch(a.get('account', '')) for a in data['accounts'])):
        raise ValueError('schedule_invalid')
    return data


class SharedLedger:
    def __init__(self, config, binding):
        self.config = config
        self.binding = binding
        self.root = private_directory(config['shared_state_dir'])
        self.names = [a['account'] for a in config['accounts']]

    def _lock(self):
        if not authority_host_matches(self.config):
            raise ValueError('authority_host_mismatch')
        fd = os.open(self.root/'ledger.lock', os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
            os.close(fd)
            raise ValueError('invalid_shared_lock')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            os.close(fd)
            raise ValueError('shared_lock_busy')
        return fd

    def _write(self, state):
        _atomic_write(str(self.root/'ledger.json'), state, str(self.root))

    def initialize(self):
        fd = self._lock()
        try:
            if any(p.name != 'ledger.lock' for p in self.root.iterdir()):
                raise ValueError('shared_state_already_enrolled')
            # Marker first: a crash must require operator recovery, never reset.
            _atomic_write(str(self.root/'enrolled.json'), {'binding': self.binding}, str(self.root))
            history = private_directory(self.root/'historical', create=True)
            for account in self.config['accounts']:
                raw = read_pinned_bytes(account['historical_ledger'], account['historical_sha256'])
                target = history/(account['account']+'.json')
                snapshot_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o400)
                os.fchmod(snapshot_fd, 0o400)
                with os.fdopen(snapshot_fd, 'wb') as stream:
                    stream.write(raw); stream.flush(); os.fsync(stream.fileno())
                if read_pinned_bytes(target, account['historical_sha256']) != raw:
                    raise ValueError('historical_backup_verification_failed')
            history_fd = os.open(history, os.O_RDONLY)
            try: os.fsync(history_fd)
            finally: os.close(history_fd)
            private_directory(self.root/'receipts', create=True)
            self._write({'schema_version': 1, 'binding': self.binding, 'last_observed_epoch': 0,
                'accounts': {name: {'last_due': {}, 'pending': None} for name in self.names}})
        finally:
            os.close(fd)

    def _historical_reason(self, account):
        definition = self.config['accounts'][self.names.index(account)]
        path = definition['historical_ledger']
        try:
            if os.path.lexists(path):
                read_pinned_bytes(path, definition['historical_sha256'])
            data = read_private_pinned(self.root/'historical'/(account+'.json'), definition['historical_sha256'])
        except (OSError, ValueError):
            return 'historical_unavailable_or_changed_hold'
        return 'historical_pending_hold' if data.get('pending_delivery') else None

    def apply(self, request, *, now=None):
        now = time.time() if now is None else now
        def held(reason):
            return {'status': 'held', 'reason': reason}
        if type(now) not in (int, float) or not math.isfinite(now):
            return held('invalid_clock')
        role, account = request.get('role'), request.get('account')
        if role not in PHASES or account not in self.names:
            return held('invalid_role_or_account')
        if not authority_host_matches(self.config):
            return held('authority_host_mismatch')
        try:
            fd = self._lock()
        except (OSError, ValueError):
            return held('shared_lock_busy')
        try:
            state, _ = _read_json_file(str(self.root/'ledger.json'), 'ledger')
            if state is None:
                return held('ledger_unavailable_hold')
            if state.get('binding') != self.binding:
                return held('schedule_binding_hold')
            if (state.get('schema_version') != 1 or not isinstance(state.get('accounts'), dict) or
                    set(state['accounts']) != set(self.names) or
                    type(state.get('last_observed_epoch')) not in (int, float)):
                return held('ledger_schema_hold')
            if now < state['last_observed_epoch']:
                return held('clock_rollback_hold')
            state['last_observed_epoch'] = now
            current = state['accounts'][account]
            if not isinstance(current, dict) or not isinstance(current.get('last_due'), dict) or 'pending' not in current:
                return held('ledger_schema_hold')
            pending = current['pending']
            action = request.get('action')
            if action == 'status' and 'token' not in request:
                # Resolve a durably recorded client identity after every claim
                # reply was lost. This reports state, never execution permission.
                request_id, due = request.get('request_id'), request.get('due_epoch')
                if (not isinstance(request_id, str) or len(request_id) != 32 or
                        any(c not in '0123456789abcdef' for c in request_id) or
                        type(due) is not int or due_slot(due, role, self.names.index(account)) != due):
                    return held('claim_mismatch_hold')
                event = hashlib.sha256(json.dumps([self.binding, role, account, due]).encode()).hexdigest()
                prior, _ = _read_json_file(str(self.root/'receipts'/(event+'.json')), 'receipt')
                if isinstance(pending, dict) and pending.get('request_id') == request_id:
                    if any(pending.get(k) != v for k,v in
                           (('role',role),('account',account),('due_epoch',due),('event_id',event))):
                        return held('claim_mismatch_hold')
                    request = {**pending, 'action': 'status'}
                elif (prior is not None and prior.get('request_id') == request_id and
                        prior.get('role') == role and prior.get('account') == account):
                    request = {**prior, 'action': 'status'}
                else:
                    return {'status': 'not_claimed', 'claim_consumed': False}
            # Completion is immutable. A lost reply or failed ledger settlement
            # may refetch/replay this exact result, never replace it.
            if action in ('status', 'finish'):
                event = request.get('event_id')
                if not isinstance(event, str) or len(event) != 64 or any(c not in '0123456789abcdef' for c in event):
                    return held('claim_mismatch_hold')
                prior, _ = _read_json_file(str(self.root/'receipts'/(event+'.json')), 'receipt')
                keys = ('role', 'account', 'token', 'event_id', 'request_id')
                if prior is None or any(request.get(k) != prior.get(k) for k in keys):
                    return held('claim_mismatch_hold')
                if prior.get('outcome') != 'in_progress_hold':
                    response = {'status': 'recorded', 'hold_preserved': prior.get('hold_preserved') is not False,
                                'outcome': prior.get('outcome'), 'delivery_verified': prior.get('delivery_verified') is True}
                    response['settlement_pending'] = (isinstance(pending, dict) and
                        all(pending.get(k) == prior.get(k) for k in keys) and not pending.get('terminal_hold'))
                    if action == 'status':return response  # Observation never grants execution.
                    result = request.get('result')
                    if (not isinstance(result, dict) or result.get('outcome') != prior.get('outcome') or
                            result.get('delivery_verified') is not prior.get('delivery_verified')):
                        return held('completion_conflict_hold')
                    if isinstance(pending, dict) and all(pending.get(k) == prior.get(k) for k in keys):
                        if prior.get('hold_preserved') is False:
                            current['pending'] = None
                        else:
                            current['pending']['terminal_hold'] = True
                        self._write(state)
                    response['settlement_pending'] = False
                    return response
                if action == 'status':return {'status': 'pending', 'hold_preserved': True, 'claim': prior}
            if action == 'claim' and request.get('request_id') is not None:
                request_id = request['request_id']
                if not isinstance(request_id, str) or len(request_id) != 32 or any(c not in '0123456789abcdef' for c in request_id):
                    return held('invalid_request_id')
                if isinstance(pending, dict) and pending.get('request_id') == request_id:
                    if (pending.get('role') != role or pending.get('account') != account or
                            ('due_epoch' in request and request['due_epoch'] != pending.get('due_epoch'))):
                        return held('claim_mismatch_hold')
                    request = {**pending, 'action': 'check'}
                    action = 'check'
            if action in ('check', 'finish'):
                if (not isinstance(pending, dict) or any(request.get(k) != pending.get(k)
                        for k in ('role', 'account', 'token', 'event_id'))):
                    return held('claim_mismatch_hold')
                if pending.get('terminal_hold'):
                    return held('terminal_uncertainty_hold')
                # The receipt is committed before settlement. A terminal receipt
                # must block admission even if that ledger write crashed.
                prior, _ = _read_json_file(str(self.root/'receipts'/(pending['event_id']+'.json')), 'receipt')
                if (prior is None or prior.get('outcome') != 'in_progress_hold' or
                        any(prior.get(k) != pending.get(k) for k in
                            ('role', 'account', 'token', 'event_id'))):
                    return held('completion_already_recorded_or_missing_hold')
                if action == 'finish':
                    result = request.get('result')
                    if not isinstance(result, dict):
                        return held('invalid_result')
                    outcome = result.get('outcome')
                    safe = ((outcome == 'delivered' and result.get('delivery_verified') is True) or
                            (outcome in SAFE_TERMINALS and result.get('delivery_verified') is False))
                    receipt = {**pending, 'completed_at_epoch': now,
                        'outcome': outcome if outcome in SAFE_TERMINALS | {'delivered', 'uncertain'} else 'unknown',
                        'delivery_verified': outcome == 'delivered' and result.get('delivery_verified') is True,
                        'hold_preserved': not safe}
                    # Never record arbitrary child output or private message text.
                    receipts = private_directory(self.root/'receipts')
                    _atomic_write(str(receipts/(pending['event_id']+'.json')), receipt, str(receipts))
                    if safe:
                        current['pending'] = None
                    else:
                        current['pending']['terminal_hold'] = True
                    self._write(state)
                    return {'status': 'recorded', 'hold_preserved': not safe}
            if os.path.lexists(self.root/'STOP') or os.path.lexists(self.root/('STOP-'+account)):
                return held('operator_stop')
            historical = self._historical_reason(account)
            if historical:
                return held(historical)
            if action == 'check':
                self._write(state)
                return dict(pending, status='admitted', authority_epoch=now) if now < pending['deadline_epoch'] else held('claim_expired_hold')
            if action != 'claim':
                return held('invalid_action')
            if pending is not None:
                return held('account_pending_hold')
            due = request.get('due_epoch', due_slot(now, role, self.names.index(account)))
            explicit_due = 'due_epoch' in request
            if (type(due) is not int or due_slot(due, role, self.names.index(account)) != due):
                return held('invalid_due_slot')
            early = MAX_CLOCK_SKEW if explicit_due else 0
            late = START_WINDOW + MAX_CLOCK_SKEW if explicit_due else START_WINDOW
            if not -early <= now - due <= late:
                return held('missed_start_window')
            if due <= current['last_due'].get(role, -1):
                return held('slot_already_claimed')
            event = hashlib.sha256(json.dumps([self.binding, role, account, due]).encode()).hexdigest()
            claim = {'role': role, 'account': account, 'event_id': event, 'token': uuid.uuid4().hex,
                     'due_epoch': due, 'activated_at_epoch': min(now,due), 'deadline_epoch': due + OPERATION_WINDOW}
            if request.get('request_id') is not None:claim['request_id'] = request['request_id']
            current['last_due'][role] = due
            current['pending'] = claim
            self._write(state)  # Claim is consumed durably before returning it.
            receipts = private_directory(self.root/'receipts')
            _atomic_write(str(receipts/(event+'.json')), dict(claim, outcome='in_progress_hold'), str(receipts))
            return dict(claim, status='admitted', authority_epoch=now)
        except (OSError, ValueError, KeyError, TypeError):
            return held('shared_state_unavailable_hold')
        finally:
            os.close(fd)
