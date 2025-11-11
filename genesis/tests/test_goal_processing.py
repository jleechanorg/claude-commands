"""
Matrix 2: Goal Processing Tests - TDD RED Phase
Tests all goal processing combinations with different types and states.
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from genesis import (
    check_goal_completion,
    detect_goal_ambiguities,
    load_goal_from_directory,
    parse_refinement,
    refine_goal_interactive,
)


class TestGoalProcessingMatrix:
    """Matrix 2: Goal Processing Combinations (Goal Type × Refinement × Iterations)"""

    @pytest.fixture
    def temp_goal_directory(self):
        """Create temporary goal directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            goal_dir = os.path.join(temp_dir, "test-goal")
            os.makedirs(goal_dir)
            yield goal_dir

    @pytest.fixture
    def valid_goal_files(self, temp_goal_directory):
        """Create valid goal definition and success criteria files"""

        goal_def_content = """# Test Goal Definition

## Refined Goal - TEST FOCUS
This is a test goal for comprehensive testing of the Genesis system.

## Context
Testing various goal processing scenarios.
"""

        success_criteria_content = """# Success Criteria - Test Goal Implementation

## Exit Criteria for Completion

### 1. Core Implementation ✅
- **Criteria**: Test implementation working correctly

### 2. Validation Complete ✅
- **Criteria**: All tests passing successfully

## Validation Requirements
- ✅ **Functional Tests**: All components working
- ✅ **Integration Tests**: End-to-end validation complete
"""

        # Write goal files
        with open(os.path.join(temp_goal_directory, "00-goal-definition.md"), "w") as f:
            f.write(goal_def_content)

        with open(os.path.join(temp_goal_directory, "01-success-criteria.md"), "w") as f:
            f.write(success_criteria_content)

        return temp_goal_directory

    @pytest.mark.parametrize("goal_type,goal_state,iterations,exit_status,expected_behavior", [
        # Directory-based goals
        ("directory", "valid", "single", "met", "complete_in_1_iteration"),
        ("directory", "ambiguous", "multiple", "met", "detect_ambiguities_complete"),
        ("directory", "missing_files", "single", "validation_failed", "error_with_file_paths"),

        # Refinement goals
        ("refinement", "valid", "multiple", "met", "refine_execute_complete"),
        ("refinement", "invalid_format", "single", "validation_failed", "format_error_handling"),

        # Interactive goals
        ("interactive", "valid", "multiple", "met", "user_approval_workflow"),

        # Auto-approved goals
        ("auto_approved", "valid", "single", "met", "skip_approval_execute"),
    ])
    def test_goal_processing_matrix(self, goal_type, goal_state, iterations, exit_status, expected_behavior, temp_goal_directory):
        """Test all goal processing combinations from Matrix 2"""

        if goal_type == "directory":
            if goal_state == "valid":
                # Create valid goal files
                self._create_valid_goal_files(temp_goal_directory)

                # This will fail until goal loading is properly implemented
                goal, criteria = load_goal_from_directory(temp_goal_directory)

                assert goal is not None
                assert criteria is not None
                assert "test goal" in goal.lower()

            elif goal_state == "missing_files":
                # Don't create files - should fail gracefully
                with pytest.raises(FileNotFoundError):
                    load_goal_from_directory(temp_goal_directory)

            elif goal_state == "ambiguous":
                # Create goal with ambiguous content
                ambiguous_goal = "TODO: implement something appropriate for various use cases"
                ambiguous_criteria = "Success when it works properly and handles edge cases"

                self._create_goal_files(temp_goal_directory, ambiguous_goal, ambiguous_criteria)

                goal, criteria = load_goal_from_directory(temp_goal_directory)

                # Should detect ambiguities
                ambiguities = detect_goal_ambiguities(goal, criteria)
                assert len(ambiguities) > 0
                assert any("TODO" in amb or "appropriate" in amb for amb in ambiguities)

        elif goal_type == "refinement":
            if goal_state == "valid":
                original_goal = "Build a comprehensive test suite"

                # This will fail until refinement is implemented
                with patch('genesis.execute_claude_command') as mock_execute:
                    mock_execute.return_value = """
                    ## Refined Goal
                    Create comprehensive test coverage for Genesis system

                    ## Success Criteria
                    - All functions tested
                    - Edge cases covered
                    - Performance validated
                    """

                    refined = refine_goal_interactive(original_goal)
                    assert refined is not None
                    assert "comprehensive test" in refined.lower()

            elif goal_state == "invalid_format":
                with patch('genesis.execute_claude_command') as mock_execute:
                    mock_execute.return_value = "Invalid response without proper formatting"

                    # Should handle invalid format gracefully
                    with pytest.raises(ValueError):
                        refine_goal_interactive("test goal")

    def test_goal_completion_detection_matrix(self):
        """Test goal completion detection from Matrix 2"""

        completion_scenarios = [
            ("all_criteria_met", "CONVERGED - All exit criteria satisfied", True),
            ("partial_criteria", "Some criteria met but gaps remain", False),
            ("no_criteria_met", "No significant progress on exit criteria", False),
            ("validation_failed", "Validation errors prevent completion", False),
        ]

        exit_criteria = """
        ### 1. Core Implementation ✅
        ### 2. Testing Complete ✅
        ### 3. Documentation Ready ✅
        """

        for scenario_name, consensus_response, expected_complete in completion_scenarios:
            # This will fail until completion detection is implemented
            is_complete = check_goal_completion(consensus_response, exit_criteria)

            if expected_complete:
                assert is_complete, f"Should detect completion for {scenario_name}"
            else:
                assert not is_complete, f"Should not detect completion for {scenario_name}"

    def test_ambiguity_detection_matrix(self):
        """Test ambiguity detection patterns from Matrix 2"""

        ambiguity_test_cases = [
            ("clear_goal", "Implement user authentication with JWT tokens", []),
            ("vague_goal", "Build something appropriate for users", ["something", "appropriate"]),
            ("placeholder_goal", "TODO: implement feature as needed", ["TODO"]),
            ("multiple_ambiguities", "Fix various issues and make improvements", ["various", "improvements"]),
        ]

        for case_name, goal_text, expected_ambiguities in ambiguity_test_cases:
            # This will fail until ambiguity detection is properly implemented
            detected = detect_goal_ambiguities(goal_text, "Test criteria")

            if expected_ambiguities:
                assert len(detected) > 0, f"Should detect ambiguities in {case_name}"
                for ambiguity in expected_ambiguities:
                    assert any(ambiguity.lower() in d.lower() for d in detected), \
                        f"Should detect '{ambiguity}' in {case_name}"
            else:
                assert len(detected) == 0, f"Should not detect ambiguities in {case_name}"

    def test_refinement_parsing_matrix(self):
        """Test refinement response parsing from Matrix 2"""

        parsing_test_cases = [
            ("valid_format", """
             ## Refined Goal
             Test goal implementation

             ## Success Criteria
             - Feature works correctly
             - Tests pass
             """, True),
            ("missing_sections", "Just some text without proper sections", False),
            ("malformed_headers", "# Wrong Header Format\nSome content", False),
            ("empty_response", "", False),
        ]

        for case_name, response, should_succeed in parsing_test_cases:
            # This will fail until parsing is properly implemented
            try:
                parsed = parse_refinement(response)
                if should_succeed:
                    assert parsed is not None, f"Should parse {case_name}"
                    assert "goal" in parsed or "criteria" in parsed, f"Should extract content from {case_name}"
                else:
                    pytest.fail(f"Should have failed to parse {case_name}")
            except ValueError:
                if should_succeed:
                    pytest.fail(f"Should have successfully parsed {case_name}")
                # Expected failure for invalid formats

    def _create_valid_goal_files(self, goal_dir):
        """Helper to create valid goal files"""
        goal_content = """# Test Goal
        ## Refined Goal - TEST IMPLEMENTATION
        Implement comprehensive testing for Genesis system with full coverage.
        """

        criteria_content = """# Success Criteria
        ### 1. Implementation Complete ✅
        ### 2. Tests Passing ✅
        """

        self._create_goal_files(goal_dir, goal_content, criteria_content)

    def _create_goal_files(self, goal_dir, goal_content, criteria_content):
        """Helper to create goal files with specific content"""
        with open(os.path.join(goal_dir, "00-goal-definition.md"), "w") as f:
            f.write(goal_content)

        with open(os.path.join(goal_dir, "01-success-criteria.md"), "w") as f:
            f.write(criteria_content)


if __name__ == "__main__":
    # These tests MUST fail in RED phase
    pytest.main([__file__, "-v", "--tb=short"])
