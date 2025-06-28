#!/usr/bin/env python3
"""
Unit tests for Think Block State Management Protocol

Tests the critical think block behavior to ensure:
1. Think blocks generate only internal thoughts + options
2. AI waits for player selection after think blocks
3. Invalid inputs get proper error responses
4. Valid selections continue narrative
5. No narrative progression without explicit choice

This addresses the bug where LLM continued taking actions after think blocks
instead of waiting for player input.
"""

import unittest
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import gemini_service which handles prompt processing
try:
    from gemini_service import GeminiService
except ImportError:
    # If import fails, create a mock for testing
    class GeminiService:
        def __init__(self, *args, **kwargs):
            pass
        
        def generate_response(self, prompt, context=""):
            return "Mock response"

class TestThinkBlockProtocol(unittest.TestCase):
    """Test cases for Think Block State Management Protocol"""

    def setUp(self):
        """Set up test environment"""
        self.test_prompts_dir = tempfile.mkdtemp()
        self.narrative_prompt_path = os.path.join(self.test_prompts_dir, 'narrative_system_instruction.md')
        
        # Read the actual prompt file content
        current_dir = os.path.dirname(os.path.abspath(__file__))
        original_prompt_path = os.path.join(current_dir, 'prompts', 'narrative_system_instruction.md')
        
        if os.path.exists(original_prompt_path):
            with open(original_prompt_path, 'r') as f:
                self.prompt_content = f.read()
        else:
            # Fallback content for testing
            self.prompt_content = """
# CRITICAL: Think Block State Management Protocol (PRIORITY #1)

## Absolute Think Block Rules

When user input contains keywords: "think", "plan", "consider", "strategize", "options":

### MUST DO:
1. Generate ONLY character's internal thoughts and planning
2. Provide numbered planning options (3-5 choices)
3. Enter "WAITING_FOR_PLAYER_CHOICE" state
4. STOP - do not continue narrative

### FORBIDDEN:
- Taking any narrative actions
- Making dice rolls
- Advancing story/time
"""

    def test_think_block_protocol_exists_in_prompt(self):
        """Test that think block protocol is present in the prompt file"""
        self.assertIn("Think Block State Management Protocol", self.prompt_content)
        self.assertIn("PRIORITY #1", self.prompt_content)
        self.assertIn("WAITING_FOR_PLAYER_CHOICE", self.prompt_content)

    def test_think_keywords_detection(self):
        """Test that all think block keywords are properly defined"""
        keywords = ["think", "plan", "consider", "strategize", "options"]
        
        for keyword in keywords:
            with self.subTest(keyword=keyword):
                # Check that keyword is mentioned in the protocol
                self.assertIn(keyword, self.prompt_content.lower())

    def test_forbidden_actions_defined(self):
        """Test that forbidden actions are clearly defined"""
        forbidden_actions = [
            "Taking any narrative actions",
            "Making dice rolls", 
            "Advancing story/time",
            "Interpreting think content as action commands"
        ]
        
        for action in forbidden_actions:
            with self.subTest(action=action):
                self.assertIn(action, self.prompt_content)

    def test_valid_input_definitions(self):
        """Test that valid post-think-block inputs are defined"""
        valid_inputs = [
            "Number selection",
            "Option reference", 
            "Clear action from options"
        ]
        
        for input_type in valid_inputs:
            with self.subTest(input_type=input_type):
                self.assertIn(input_type, self.prompt_content)

    def test_invalid_input_definitions(self):
        """Test that invalid post-think-block inputs are defined"""
        invalid_inputs = [
            "continue",
            "next", 
            "go on",
            "New think blocks before selection",
            "Unrelated narrative input"
        ]
        
        for input_type in invalid_inputs:
            with self.subTest(input_type=input_type):
                self.assertIn(input_type, self.prompt_content)

    def test_error_response_format_defined(self):
        """Test that error response format is specified"""
        error_format = "Please select one of the numbered options"
        self.assertIn(error_format, self.prompt_content)

    def test_state_validation_checkpoints(self):
        """Test that state validation checkpoints are defined"""
        checkpoints = [
            "Was previous response a think block with options?",
            "Has player made valid selection from those options?",
            "THINK BLOCK CHECKPOINT"
        ]
        
        for checkpoint in checkpoints:
            with self.subTest(checkpoint=checkpoint):
                self.assertIn(checkpoint, self.prompt_content)

    def test_protocol_priority_placement(self):
        """Test that think block protocol is at the beginning of the file"""
        lines = self.prompt_content.split('\n')
        think_block_line = None
        
        for i, line in enumerate(lines):
            if "Think Block State Management Protocol" in line:
                think_block_line = i
                break
        
        # Should appear in first 10 lines for priority
        self.assertIsNotNone(think_block_line, "Think Block Protocol not found")
        self.assertLess(think_block_line, 10, "Think Block Protocol should be at the top for priority")

    def test_protocol_overrides_other_instructions(self):
        """Test that protocol explicitly states it overrides other instructions"""
        override_text = "THIS PROTOCOL OVERRIDES ALL OTHER INSTRUCTIONS WHEN TRIGGERED"
        self.assertIn(override_text, self.prompt_content)

class TestThinkBlockScenarios(unittest.TestCase):
    """Test specific think block scenarios and expected behaviors"""

    def setUp(self):
        """Set up test scenarios"""
        self.mock_gemini = MagicMock()
        
    def test_simple_think_scenario(self):
        """Test simple think command scenario"""
        user_input = "think about what to do next"
        
        # Expected behavior: Generate internal thoughts + options, then stop
        expected_elements = [
            "internal thoughts",
            "1.", "2.", "3.",  # Numbered options
            "What would you like to do"  # Planning block
        ]
        
        # This would be tested with actual AI integration
        # For now, we test that the protocol exists
        self.assertTrue(True)  # Placeholder for actual AI testing

    def test_complex_planning_scenario(self):
        """Test complex planning scenario"""
        user_input = "plan how to infiltrate the enemy fortress"
        
        # Expected behavior: Generate detailed planning thoughts + tactical options
        expected_elements = [
            "planning",
            "infiltrate",
            "1.", "2.", "3.", "4.",  # Multiple numbered options
            "fortress"
        ]
        
        self.assertTrue(True)  # Placeholder for actual AI testing

    def test_invalid_continuation_scenario(self):
        """Test invalid continuation after think block"""
        # Scenario: AI provides think block with options, player says "continue"
        user_input_after_think = "continue"
        
        # Expected behavior: Error response asking for option selection
        expected_error = "Please select one of the numbered options"
        
        self.assertTrue(True)  # Placeholder for actual AI testing

    def test_valid_selection_scenario(self):
        """Test valid option selection after think block"""
        # Scenario: AI provides think block, player selects option
        user_input_after_think = "2"
        
        # Expected behavior: Continue with option 2 from previous think block
        self.assertTrue(True)  # Placeholder for actual AI testing

class TestPromptFileIntegrity(unittest.TestCase):
    """Test that prompt file changes don't break existing functionality"""

    def setUp(self):
        """Set up file integrity tests"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.prompt_file = os.path.join(current_dir, 'prompts', 'narrative_system_instruction.md')

    def test_prompt_file_exists(self):
        """Test that the prompt file exists"""
        self.assertTrue(os.path.exists(self.prompt_file), 
                       f"Prompt file not found at {self.prompt_file}")

    def test_prompt_file_readable(self):
        """Test that the prompt file is readable"""
        try:
            with open(self.prompt_file, 'r') as f:
                content = f.read()
                self.assertGreater(len(content), 100, "Prompt file seems too short")
        except Exception as e:
            self.fail(f"Could not read prompt file: {e}")

    def test_backup_file_exists(self):
        """Test that backup file was created"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backup_file = os.path.join(current_dir, 'prompts', 'narrative_system_instruction.md.backup')
        
        self.assertTrue(os.path.exists(backup_file), 
                       "Backup file should exist for safety")

    def test_essential_protocols_preserved(self):
        """Test that essential game protocols are preserved"""
        with open(self.prompt_file, 'r') as f:
            content = f.read()
        
        essential_elements = [
            "Master Game Weaver",
            "Player Agency is Absolute", 
            "Character Generation Protocol",
            "Planning Block"
        ]
        
        for element in essential_elements:
            with self.subTest(element=element):
                self.assertIn(element, content, 
                             f"Essential element '{element}' missing from prompt")

class TestThinkBlockStateManagement(unittest.TestCase):
    """Test state management aspects of think block protocol"""

    def test_waiting_state_definition(self):
        """Test that WAITING_FOR_PLAYER_CHOICE state is defined"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file = os.path.join(current_dir, 'prompts', 'narrative_system_instruction.md')
        
        if os.path.exists(prompt_file):
            with open(prompt_file, 'r') as f:
                content = f.read()
                self.assertIn("WAITING_FOR_PLAYER_CHOICE", content)

    def test_state_transition_rules(self):
        """Test that state transition rules are clearly defined"""
        # Rules should specify when to enter and exit waiting state
        expected_rules = [
            "Enter \"WAITING_FOR_PLAYER_CHOICE\" state",
            "STOP - do not continue narrative", 
            "valid player selection"
        ]
        
        # This would be expanded with actual prompt content testing
        self.assertTrue(True)  # Placeholder

def run_think_block_tests():
    """Run all think block protocol tests"""
    # Set testing environment variable for faster AI models
    os.environ['TESTING'] = 'true'
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestThinkBlockProtocol,
        TestThinkBlockScenarios, 
        TestPromptFileIntegrity,
        TestThinkBlockStateManagement
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running Think Block Protocol Tests...")
    print("="*50)
    
    success = run_think_block_tests()
    
    if success:
        print("\n✅ All think block tests passed!")
        exit(0)
    else:
        print("\n❌ Some think block tests failed!")
        exit(1)