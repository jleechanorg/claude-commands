"""The coordinator skill owns the one-turn judgment and send policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.claude/skills/agy-dot-coordinator/SKILL.md'


class CoordinatorWorkflowTests(unittest.TestCase):
    def test_identity_and_account_binding_precede_any_send(self):
        text = SKILL.read_text()
        for phrase in ('--account <configured-key>', 'DOT_EXPECTED_IDENTITY_SHA256',
                       'authenticated identity', 'stop without sending'):
            self.assertIn(phrase, text)

    def test_ambiguous_send_is_held_for_read_only_reconciliation(self):
        text = SKILL.read_text()
        self.assertIn('do not retry or send a correction', text)
        self.assertIn('read-only inspection', text)
        self.assertIn('durable marker', text)
        self.assertIn('must not send', text)

    def test_coordinator_has_no_classifier_or_fallback(self):
        text = SKILL.read_text().lower()
        self.assertIn('without code-based routing', text)
        self.assertIn('automatic fallback', text)
        self.assertIn('account rotation', text)


if __name__ == '__main__':
    unittest.main()
