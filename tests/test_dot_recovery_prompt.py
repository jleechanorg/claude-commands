"""The coordinator skill owns the one-turn judgment and send policy."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / '.claude/skills/dot-coordinator/SKILL.md'


class CoordinatorWorkflowTests(unittest.TestCase):
    def test_identity_and_account_binding_precede_any_send(self):
        text = SKILL.read_text()
        for phrase in ('--account <configured-key>', 'DOT_EXPECTED_IDENTITY_SHA256',
                       'authenticated identity', 'stop without sending'):
            self.assertIn(phrase, text)

    def test_ambiguous_send_is_held_for_read_only_reconciliation(self):
        text = SKILL.read_text().lower()
        self.assertIn('do not retry or send a correction', text)
        self.assertIn('read-only reconciliation', text)
        self.assertIn('durable marker', text)
        self.assertIn('do not send', text)

    def test_periodic_message_is_exact_and_submission_is_terminal(self):
        text = SKILL.read_text()
        outbound = text.split('## Periodic outbound message', 1)[1].split('## Workflow', 1)[0]
        expected = "Review everything I asked for and everything completed in the last four hours. Make sure every unfinished task has an appropriate owner and is actively being driven. Recover overlooked work, continue existing tasks, and coordinate with the relevant owners without duplicating efforts. Act on what you can, resolve blockers through available permitted approaches, and ask me only when essential information or required approval is missing. Verify actual results rather than relying on assignments or status claims. Keep older unresolved commitments until they are completed or cancelled. Give me a concise update on meaningful progress, remaining blockers, and what happens next; skip unchanged status."
        self.assertEqual([line[2:] for line in outbound.splitlines() if line.startswith('> ')], [expected])
        self.assertIn('Explicit read-only or do-not-send runs still send nothing', outbound)
        self.assertIn('an acknowledgment does not renew', text)
        self.assertIn('perform verification/reconciliation only and return', text)
        self.assertIn('not a security boundary', text)
        self.assertIn('ordinary review callers must not create', text.lower())

    def test_review_guidance_does_not_reintroduce_manual_stop(self):
        dot = (ROOT / '.claude/skills/dot/SKILL.md').read_text()
        coordinator = SKILL.read_text()
        self.assertIn('Do not manually create or remove coordinator STOP for ordinary review', dot)
        self.assertIn('Preserve pre-existing operator STOP and unresolved delivery state', dot)
        self.assertIn('coordinator global review holds are retired', dot)
        self.assertIn('Ordinary review callers must not create a global STOP marker', coordinator)
        self.assertNotIn('set the coordinator STOP marker', dot)

    def test_coordinator_has_no_classifier_or_fallback(self):
        text = SKILL.read_text().lower()
        self.assertIn('without code-based routing', text)
        self.assertIn('automatic fallback', text)
        self.assertIn('account rotation', text)


if __name__ == '__main__':
    unittest.main()
