"""
Red/Green test for narrative cutoff bug fix.

This test demonstrates the bug where narratives containing quotes would be cut off
at the first unescaped quote, causing incomplete extraction.

Bug example: Narrative was cut off at:
"2. **Ask Gareth for more details:** Inquire about the"

The fix improves the extract_field_value function in json_utils.py to properly
handle escaped quotes and track the true end of string values.
"""

import unittest
import sys
import os

# Add the parent directory to path to enable imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from json_utils import extract_field_value


class TestNarrativeCutoffBug(unittest.TestCase):
    """Test the narrative cutoff bug fix using red/green methodology."""
    
    def setUp(self):
        """Set up test data with narratives that would trigger the bug."""
        # This is the actual JSON that caused the bug - narrative with embedded quotes
        self.bug_triggering_json = '''{
            "narrative": "You are standing in the bustling market square of Waterdeep. The sun is high, and merchants call out their wares. An old man approaches you, his eyes gleaming with urgency.\\n\\n\\"Adventurers!\\" he calls out. \\"I have urgent news about the missing caravan. Please, you must help!\\"\\n\\nWhat do you do?\\n\\n1. **Listen to the old man:** Hear what he has to say about the missing caravan.\\n2. **Ask Gareth for more details:** Inquire about the caravan's last known location and what goods it was carrying.\\n3. **Ignore him and explore the market:** You're more interested in shopping than another quest.\\n4. **Intimidate him for information:** Use your imposing presence to get him to spill everything quickly.",
            "state_updates": {
                "scene": "Market Square - Quest Hook"
            }
        }'''
        
        # Expected full narrative (properly extracted)
        self.expected_narrative = '''You are standing in the bustling market square of Waterdeep. The sun is high, and merchants call out their wares. An old man approaches you, his eyes gleaming with urgency.

"Adventurers!" he calls out. "I have urgent news about the missing caravan. Please, you must help!"

What do you do?

1. **Listen to the old man:** Hear what he has to say about the missing caravan.
2. **Ask Gareth for more details:** Inquire about the caravan's last known location and what goods it was carrying.
3. **Ignore him and explore the market:** You're more interested in shopping than another quest.
4. **Intimidate him for information:** Use your imposing presence to get him to spill everything quickly.'''
        
        # What the bug would produce (cut off at first quote in options)
        self.bug_cutoff_narrative = '''You are standing in the bustling market square of Waterdeep. The sun is high, and merchants call out their wares. An old man approaches you, his eyes gleaming with urgency.

"Adventurers!" he calls out. "I have urgent news about the missing caravan. Please, you must help!"

What do you do?

1. **Listen to the old man:** Hear what he has to say about the missing caravan.
2. **Ask Gareth for more details:** Inquire about the'''
        
        # Additional test case with nested quotes
        self.complex_json = '''{
            "narrative": "The wizard says, \\"The ancient tome reads: 'Beware the curse of the shadow realm, for it whispers \\\\\\"death\\\\\\" to all who enter.' We must be careful.\\"\\n\\nHe continues, \\"I've studied these texts for years. The curse can only be broken by someone who truly understands the meaning of sacrifice.\\"\\n\\nOptions:\\n1. Ask about the curse\\n2. \\"Tell me more about this 'sacrifice' you mentioned\\"\\n3. Leave immediately",
            "debug": true
        }'''
        
        self.expected_complex_narrative = '''The wizard says, "The ancient tome reads: 'Beware the curse of the shadow realm, for it whispers \\"death\\" to all who enter.' We must be careful."

He continues, "I've studied these texts for years. The curse can only be broken by someone who truly understands the meaning of sacrifice."

Options:
1. Ask about the curse
2. "Tell me more about this 'sacrifice' you mentioned"
3. Leave immediately'''

    def test_narrative_extraction_with_quotes_RED_phase(self):
        """
        RED PHASE: Demonstrate that a naive regex approach would fail.
        
        This test shows how the old approach would cut off the narrative
        at an embedded quote within the content.
        """
        # Simulate the old buggy regex that would fail
        import re
        
        # This pattern is too simple and doesn't handle escaped quotes properly
        buggy_pattern = r'"narrative"\s*:\s*"([^"]*)"'
        
        match = re.search(buggy_pattern, self.bug_triggering_json)
        if match:
            buggy_result = match.group(1)
        else:
            buggy_result = None
            
        # The buggy pattern cuts off at the first unescaped quote
        self.assertIsNotNone(buggy_result)
        self.assertNotEqual(buggy_result, self.expected_narrative)
        # It would cut off much earlier, at the first quote
        self.assertTrue(len(buggy_result) < len(self.expected_narrative) // 2)
        
        print(f"\n🔴 RED PHASE: Buggy extraction got only {len(buggy_result)} chars instead of {len(self.expected_narrative)}")
        print(f"Cutoff happened at: ...{buggy_result[-50:]}")

    def test_narrative_extraction_with_quotes_GREEN_phase(self):
        """
        GREEN PHASE: Demonstrate that the fixed implementation works correctly.
        
        The new implementation in json_utils.extract_field_value properly
        handles escaped quotes and extracts the complete narrative.
        """
        # Use the fixed implementation
        result = extract_field_value(self.bug_triggering_json, 'narrative')
        
        # The fixed version should extract the complete narrative
        self.assertIsNotNone(result)
        self.assertEqual(result, self.expected_narrative)
        
        print(f"\n🟢 GREEN PHASE: Fixed extraction successfully got all {len(result)} chars")
        print("Narrative ends correctly with: ...{}".format(result[-50:]))

    def test_complex_nested_quotes(self):
        """Test extraction with complex nested quotes and escape sequences."""
        result = extract_field_value(self.complex_json, 'narrative')
        
        self.assertIsNotNone(result)
        print(f"\nActual result: {repr(result)}")
        print(f"\nExpected result: {repr(self.expected_complex_narrative)}")
        self.assertEqual(result, self.expected_complex_narrative)
        
        # Verify specific nested quote patterns are preserved
        self.assertIn('\\"death\\"', result)  # Triple-nested quote (properly escaped)
        self.assertIn("'Beware the curse", result)  # Single quotes within doubles
        self.assertIn('"Tell me more about this \'sacrifice\' you mentioned"', result)  # Mixed quotes

    def test_incomplete_json_narrative(self):
        """Test that incomplete JSON (cut off mid-narrative) still extracts what's available."""
        incomplete_json = '''{
            "narrative": "The adventure begins in a dark forest. You hear strange noises coming from the shadows.\\n\\n\\"Help me!\\" a voice cries out. You see a figure trapped under fallen logs.\\n\\nWhat do you do?\\n\\n1. Rush to help\\n2. Call out \\"Who's there'''
        
        result = extract_field_value(incomplete_json, 'narrative')
        
        self.assertIsNotNone(result)
        # Should extract everything up to the truncation
        self.assertIn("The adventure begins", result)
        self.assertIn('"Help me!"', result)
        self.assertIn("Who's there", result)  # Even partial option extracted

    def test_narrative_with_json_special_chars(self):
        """Test narratives containing JSON special characters."""
        json_with_special = r'''{
            "narrative": "The sign reads: \"Price: 100gp per night (includes breakfast)\".\n\nThe innkeeper adds, \"We also have a special: stay 3 nights, get 10% off!\"\n\nYour options:\n1. Accept the offer\n2. Negotiate: \"How about 80gp?\"\n3. Look elsewhere"
        }'''
        
        result = extract_field_value(json_with_special, 'narrative')
        
        self.assertIsNotNone(result)
        self.assertIn("Price: 100gp per night (includes breakfast)", result)
        self.assertIn("stay 3 nights, get 10% off!", result)
        self.assertIn('"How about 80gp?"', result)

    def test_extraction_performance(self):
        """Test that the fix handles very long narratives efficiently."""
        # Create a very long narrative with many quotes
        long_narrative_parts = []
        for i in range(100):
            long_narrative_parts.append(f'Character {i} says, "This is dialogue number {i}!"')
        
        long_json = '{{"narrative": "{}"}}'.format('\\n'.join(long_narrative_parts).replace('"', '\\"'))
        
        result = extract_field_value(long_json, 'narrative')
        
        self.assertIsNotNone(result)
        # Verify all 100 dialogues were extracted
        for i in range(100):
            self.assertIn(f'This is dialogue number {i}!', result)


if __name__ == '__main__':
    # Run tests with verbose output to see RED/GREEN phases clearly
    unittest.main(verbosity=2)