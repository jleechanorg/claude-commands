"""Instruction regression tests only: no scheduler, provider or live Dot execution."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CoordinatorCheckbackContractTests(unittest.TestCase):
    def setUp(self):
        self.text = (ROOT / '.claude/skills/dot/SKILL.md').read_text()
        start = self.text.find('### Coordinator recovery checkbacks')
        end = self.text.find('### Other delegated work', start + 1)
        self.cycle = self.text[start:end] if start >= 0 and end > start else ''

    def test_specific_cycle_precedes_and_overrides_generic_defaults(self):
        self.assertTrue(self.cycle, 'Missing scoped coordinator contract')
        self.assertIn('overrides the generic polling and /goal defaults below', self.cycle)
        self.assertIn('For other delegated work only', self.text)
        self.assertIn('use the coordinator recovery checkback condition when applicable', self.text)

    def test_receipt_starts_exact_bounded_inter_observation_cadence(self):
        self.assertIn('exact transport receipt for the initial reminder in the intended chat', self.cycle)
        delays = re.search(r'Inter-check delays in seconds: `([^`]+)`', self.cycle)
        self.assertIsNotNone(delays)
        self.assertEqual([int(v.strip()) for v in delays.group(1).split(',')],
                         [60, 120, 300, 300, 300, 300, 300, 300, 300, 300])
        self.assertIn('previous completed observation', self.cycle)
        self.assertIn('never reset the count', self.cycle)

    def test_interruptions_timeouts_and_tenth_check_have_exact_accounting(self):
        for clause in ('Increment once per completed observation attempt',
                       'including a recorded timeout or read failure',
                       'resume an interrupted attempt under the same count',
                       'no check eleven or disguised in-check re-observation'):
            self.assertIn(clause, self.cycle)

    def test_direct_user_response_and_existing_mechanism_are_preserved(self):
        for clause in ('Direct user messages take priority', 'respond promptly',
                       'existing supported interruptible wait/wake mechanism',
                       'Do not create jobs, daemons, senders or competing coordinators',
                       'Do not change providers, credentials or installed schedules'):
            self.assertIn(clause, self.cycle)

    def test_source_evidence_and_all_lane_stopping_conditions(self):
        for clause in ('fresh original task artifacts', 'Daemon health',
                       'do not prove task execution or completion',
                       'all remaining necessary observations are blocked',
                       'One blocked lane must not stop other feasible lanes',
                       'Ten checks end the bounded observation cycle, not task ownership'):
            self.assertIn(clause, self.cycle)

    def test_coordinator_uses_normal_preference_and_account_rotation(self):
        self.assertIn('Preserve the cycle checkpoint and the intended chat URL', self.cycle)
        self.assertIn('set `DOT_ROTATE_ON_LIMIT=0` and pass `--url <intended-chat-url>`', self.cycle)
        self.assertIn('automatic retry clears the URL', self.cycle)
        self.assertIn('reading that exact URL with `--account <next>`', self.cycle)
        self.assertIn('cannot reach the intended chat', self.cycle)
        self.assertIn('record the observation as failed', self.cycle)
        self.assertIn('do not use its default URL', self.cycle)
        self.assertIn('do not pin or record a permanent cycle owner', self.cycle)
        self.assertIn('machine-local `DOT_ACCOUNT` preference', self.cycle)
        self.assertIn('configured `rotation` order', self.cycle)
        self.assertIn('Except for coordinator sends bound to a specific intended chat',
                      self.text)
        for clause in ('retain the verified account',
                       'Do not rotate to another account or target'):
            self.assertNotIn(clause, self.cycle)

    def test_small_fix_file_threshold_matches_delegate_rule(self):
        self.assertIn('it touches one or two files', self.text)
        self.assertIn('it spans more than two files', self.text)

    def test_recovery_does_not_become_status_only_work(self):
        for clause in ('Resume unfinished authorized work with its existing owner',
                       'older commitments', 'safe tests or design',
                       'concrete permitted unblock route', 'separately authorized reassignment'):
            self.assertIn(clause, self.cycle)


if __name__ == '__main__':
    unittest.main()
