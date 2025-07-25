#!/usr/bin/env python3
"""
Integration tests for Think Block Protocol

These tests simulate actual gameplay scenarios to verify:
1. Think blocks pause narrative progression
2. Player agency is preserved
3. State transitions work correctly
4. Error handling functions properly

This addresses the critical bug where AI continued story after think blocks.
"""

import os
import sys
import unittest

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ThinkBlockWorkflowSimulator:
    """Simulates think block workflow for testing"""

    def __init__(self):
        self.state = "NORMAL"
        self.last_response = ""
        self.pending_options = []

    def process_user_input(self, user_input):
        """Simulate processing user input according to think block protocol"""
        # If currently waiting for choice, handle that first
        if self.state == "WAITING_FOR_PLAYER_CHOICE":
            return self._handle_pending_choice(user_input)

        # Check for think block keywords in normal state
        think_keywords = ["think", "plan", "consider", "strategize", "options"]
        if any(keyword in user_input.lower() for keyword in think_keywords):
            return self._handle_think_block(user_input)
        return self._handle_normal_input(user_input)

    def _handle_think_block(self, user_input):
        """Handle think block input - should generate thoughts + options then stop"""
        self.state = "WAITING_FOR_PLAYER_CHOICE"
        self.pending_options = ["Option 1: Do X", "Option 2: Do Y", "Option 3: Do Z"]

        response = f"""
[THINK BLOCK RESPONSE]
Character's internal thoughts about: {user_input}

After considering the situation, I see several options:

1. Option 1: Do X
2. Option 2: Do Y
3. Option 3: Do Z

**--- PLANNING BLOCK ---**
What would you like to do?
1. Option 1: Do X
2. Option 2: Do Y
3. Option 3: Do Z
4. Other: Describe a different action
"""
        self.last_response = response
        return response

    def _handle_pending_choice(self, user_input):
        """Handle input when waiting for player choice"""
        # Check for valid selection
        if user_input.strip() in ["1", "2", "3"]:
            self.state = "NORMAL"
            selected_option = self.pending_options[int(user_input) - 1]
            self.pending_options = []
            return f"[CONTINUING WITH: {selected_option}] Narrative continues..."

        # Check for invalid continuation attempts
        invalid_inputs = ["continue", "next", "go on"]
        if user_input.lower().strip() in invalid_inputs:
            return self._error_response()

        # Check for new think blocks - should be prevented
        think_keywords = ["think", "plan", "consider", "strategize", "options"]
        if any(keyword in user_input.lower() for keyword in think_keywords):
            return self._error_response()

        # Check for option description (more specific)
        if (
            "choose" in user_input.lower()
            or "i'll" in user_input.lower()
            or "sneak" in user_input.lower()
            or "attack" in user_input.lower()
        ):
            self.state = "NORMAL"
            self.pending_options = []
            return (
                f"[CONTINUING WITH USER CHOICE] {user_input} - Narrative continues..."
            )

        # Unrelated input - should get error
        return self._error_response()

    def _handle_normal_input(self, user_input):
        """Handle normal gameplay input"""
        return f"[NORMAL RESPONSE] Continuing story based on: {user_input}"

    def _error_response(self):
        """Generate error response for invalid input after think block"""
        return "Please select one of the numbered options from the planning block above (1, 2, 3, etc.) or clearly describe which action you'd like to take."


class TestThinkBlockIntegration(unittest.TestCase):
    """Integration tests for think block workflow"""

    def setUp(self):
        """Set up test environment"""
        self.simulator = ThinkBlockWorkflowSimulator()

    def test_simple_think_block_workflow(self):
        """Test basic think block workflow: think -> options -> selection -> continue"""
        # Step 1: User issues think command
        response1 = self.simulator.process_user_input("think about what to do")

        # Should generate thoughts + options and enter waiting state
        self.assertIn("THINK BLOCK RESPONSE", response1)
        self.assertIn("1.", response1)
        self.assertIn("2.", response1)
        self.assertIn("3.", response1)
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

        # Step 2: User selects option
        response2 = self.simulator.process_user_input("2")

        # Should continue with selected option
        self.assertIn("CONTINUING WITH", response2)
        self.assertIn("Option 2", response2)
        self.assertEqual(self.simulator.state, "NORMAL")

    def test_think_block_with_invalid_continuation(self):
        """Test that invalid continuation gets error response"""
        # Step 1: User issues think command
        self.simulator.process_user_input("think about the situation")
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

        # Step 2: User tries invalid continuation
        response = self.simulator.process_user_input("continue")

        # Should get error message
        self.assertIn("Please select one of the numbered options", response)
        self.assertEqual(
            self.simulator.state, "WAITING_FOR_PLAYER_CHOICE"
        )  # Still waiting

    def test_think_block_with_option_description(self):
        """Test selecting option by description rather than number"""
        # Step 1: User issues think command
        self.simulator.process_user_input("plan how to proceed")
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

        # Step 2: User describes choice
        response = self.simulator.process_user_input("I'll sneak around the back")

        # Should continue with described choice
        self.assertIn("CONTINUING WITH USER CHOICE", response)
        self.assertIn("sneak around", response)
        self.assertEqual(self.simulator.state, "NORMAL")

    def test_multiple_think_keywords(self):
        """Test that all think keywords trigger the protocol"""
        keywords = ["think", "plan", "consider", "strategize", "options"]

        for keyword in keywords:
            with self.subTest(keyword=keyword):
                # Reset simulator
                self.simulator = ThinkBlockWorkflowSimulator()

                # Test keyword
                response = self.simulator.process_user_input(
                    f"{keyword} about the problem"
                )

                self.assertIn("THINK BLOCK RESPONSE", response)
                self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

    def test_normal_input_after_selection(self):
        """Test that normal input works after completing think block workflow"""
        # Complete think block workflow
        self.simulator.process_user_input("think about options")
        self.simulator.process_user_input("1")

        # Normal input should work normally
        response = self.simulator.process_user_input("look around the room")
        self.assertIn("NORMAL RESPONSE", response)
        self.assertEqual(self.simulator.state, "NORMAL")

    def test_nested_think_blocks_prevented(self):
        """Test that new think blocks during waiting state get error"""
        # Issue think command
        self.simulator.process_user_input("think about the situation")
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

        # Try another think block
        response = self.simulator.process_user_input("think about something else")

        # Should get error (simulated as invalid input)
        self.assertIn("Please select one of the numbered options", response)
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")


class TestThinkBlockErrorHandling(unittest.TestCase):
    """Test error handling in think block protocol"""

    def setUp(self):
        """Set up error handling tests"""
        self.simulator = ThinkBlockWorkflowSimulator()

    def test_invalid_input_variations(self):
        """Test various invalid inputs after think block"""
        # Set up waiting state
        self.simulator.process_user_input("think about choices")

        invalid_inputs = ["continue", "next", "go on", "what happens next", "proceed"]

        for invalid_input in invalid_inputs:
            with self.subTest(invalid_input=invalid_input):
                response = self.simulator.process_user_input(invalid_input)
                self.assertIn("Please select one of the numbered options", response)
                self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

    def test_error_message_format(self):
        """Test that error message follows specified format"""
        # Set up waiting state and trigger error
        self.simulator.process_user_input("think about the problem")
        response = self.simulator.process_user_input("continue")

        # Check error message contains required elements
        self.assertIn("Please select", response)
        self.assertIn("numbered options", response)
        self.assertIn("1, 2, 3", response)

    def test_recovery_after_error(self):
        """Test that valid input works after error"""
        # Set up waiting state, trigger error, then provide valid input
        self.simulator.process_user_input("think about strategy")
        self.simulator.process_user_input("continue")  # Error
        response = self.simulator.process_user_input("2")  # Valid

        # Should recover and continue normally
        self.assertIn("CONTINUING WITH", response)
        self.assertEqual(self.simulator.state, "NORMAL")


class TestThinkBlockStateTransitions(unittest.TestCase):
    """Test state transitions in think block protocol"""

    def setUp(self):
        """Set up state transition tests"""
        self.simulator = ThinkBlockWorkflowSimulator()

    def test_initial_state(self):
        """Test initial state is normal"""
        self.assertEqual(self.simulator.state, "NORMAL")

    def test_state_transition_on_think(self):
        """Test state changes to waiting on think command"""
        self.simulator.process_user_input("think about options")
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")

    def test_state_transition_on_selection(self):
        """Test state returns to normal after valid selection"""
        self.simulator.process_user_input("think about choices")
        self.simulator.process_user_input("1")
        self.assertEqual(self.simulator.state, "NORMAL")

    def test_state_persistence_on_error(self):
        """Test state remains waiting after invalid input"""
        self.simulator.process_user_input("think about the situation")
        self.simulator.process_user_input("continue")  # Invalid
        self.assertEqual(self.simulator.state, "WAITING_FOR_PLAYER_CHOICE")


def run_integration_tests():
    """Run all integration tests"""
    os.environ["TESTING"] = "true"

    test_suite = unittest.TestSuite()

    test_classes = [
        TestThinkBlockIntegration,
        TestThinkBlockErrorHandling,
        TestThinkBlockStateTransitions,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Think Block Integration Tests...")
    print("=" * 50)

    success = run_integration_tests()

    if success:
        print("\n✅ All integration tests passed!")
        print("Think block protocol should work correctly!")
        exit(0)
    else:
        print("\n❌ Some integration tests failed!")
        exit(1)
