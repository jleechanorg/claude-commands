"""RED-first contract for stale Chrome singleton recovery in the coordinator launcher.

A killed tick leaves <profile>/SingletonLock -> <host>-<pid>. When that host is this
machine and that pid is gone and no Chrome process uses the profile, the lock is
provably stale and must not block the next tick. Every uncertain case must still
block: a live pid, another host, a malformed target, or a non-symlink file.
"""
import importlib.util
import os
import socket
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / '.claude/skills/dot-coordinator/scripts/ping-dots.py'
SPEC = importlib.util.spec_from_file_location('dot_coordinator_launcher', SCRIPT)
PING = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PING)


class StaleSingletonRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.profile = self.home / 'profile'
        self.profile.mkdir()
        self.host = socket.gethostname()

    def _lock(self, target):
        lock = self.profile / 'SingletonLock'
        if lock.exists() or lock.is_symlink():
            lock.unlink()
        if target is None:
            lock.write_text('not a symlink', encoding='utf-8')
        else:
            lock.symlink_to(target)
        for name in ('SingletonCookie', 'SingletonSocket'):
            extra = self.profile / name
            if extra.exists() or extra.is_symlink():
                extra.unlink()
        (self.profile / 'SingletonCookie').symlink_to('cookie-value')
        (self.profile / 'SingletonSocket').symlink_to(str(self.home / 'sock'))

    def test_dead_same_host_pid_is_cleared(self):
        dead_pid = 9_000_000_001
        with patch.object(PING, 'pid_is_alive', return_value=False), \
             patch.object(PING, 'chrome_uses_profile', return_value=False):
            self._lock(f'{self.host}-{dead_pid}')
            PING.clear_stale_singleton(self.profile)
        for name in ('SingletonLock', 'SingletonCookie', 'SingletonSocket'):
            self.assertFalse(os.path.lexists(self.profile / name), name)

    def test_live_pid_is_never_stale(self):
        with patch.object(PING, 'pid_is_alive', return_value=True), \
             patch.object(PING, 'chrome_uses_profile', return_value=False):
            self._lock(f'{self.host}-4242')
            PING.clear_stale_singleton(self.profile)
        self.assertTrue(os.path.lexists(self.profile / 'SingletonLock'))

    def test_other_host_is_never_stale(self):
        with patch.object(PING, 'pid_is_alive', return_value=False), \
             patch.object(PING, 'chrome_uses_profile', return_value=False):
            self._lock('someone-elses-host-4242')
            PING.clear_stale_singleton(self.profile)
        self.assertTrue(os.path.lexists(self.profile / 'SingletonLock'))

    def test_chrome_still_on_the_profile_is_never_stale(self):
        with patch.object(PING, 'pid_is_alive', return_value=False), \
             patch.object(PING, 'chrome_uses_profile', return_value=True):
            self._lock(f'{self.host}-4242')
            PING.clear_stale_singleton(self.profile)
        self.assertTrue(os.path.lexists(self.profile / 'SingletonLock'))

    def test_malformed_or_regular_lock_is_never_stale(self):
        with patch.object(PING, 'pid_is_alive', return_value=False), \
             patch.object(PING, 'chrome_uses_profile', return_value=False):
            self._lock(None)
            PING.clear_stale_singleton(self.profile)
            self.assertTrue(os.path.lexists(self.profile / 'SingletonLock'))
            self._lock('no-pid-suffix')
            PING.clear_stale_singleton(self.profile)
        self.assertTrue(os.path.lexists(self.profile / 'SingletonLock'))


if __name__ == '__main__':
    unittest.main()
