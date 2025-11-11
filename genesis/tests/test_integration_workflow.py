"""
Matrix 5: Integration & Workflow Tests - TDD RED Phase
Tests all integration scenarios with Git, progress tracking, and consensus.
"""

import json
import os
import subprocess
import tempfile

import pytest

from genesis import (
    append_genesis_learning,
    check_consensus,
    integrate_git_workflow,
    update_progress_file,
)


class TestIntegrationWorkflowMatrix:
    """Matrix 5: Integration & Workflow Testing (Git × Progress × Consensus)"""

    @pytest.fixture
    def temp_git_repo(self):
        """Create temporary git repository for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize git repo
            subprocess.run(["git", "init"], check=False, cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], check=False, cwd=temp_dir)
            subprocess.run(["git", "config", "user.name", "Test User"], check=False, cwd=temp_dir)

            # Create initial commit
            readme_file = os.path.join(temp_dir, "README.md")
            with open(readme_file, "w") as f:
                f.write("# Test Repository\n")
            subprocess.run(["git", "add", "README.md"], check=False, cwd=temp_dir)
            subprocess.run(["git", "commit", "-m", "Initial commit"], check=False, cwd=temp_dir)

            yield temp_dir

    @pytest.mark.parametrize("git_state,progress_tracking,consensus_type,workflow_stage,expected_integration", [
        ("clean", "file_updates", "achieved", "completion", "successful_workflow"),
        ("dirty", "session_state", "failed", "validation", "handle_uncommitted_changes"),
        ("conflicts", "iteration_data", "partial", "execution", "conflict_resolution"),
        ("no_repo", "none", "timeout", "planning", "non_git_mode_operation"),

        # Additional git scenarios
        ("detached_head", "file_updates", "achieved", "execution", "handle_detached_state"),
        ("merge_conflicts", "session_state", "partial", "validation", "resolve_merge_conflicts"),
        ("untracked_files", "iteration_data", "achieved", "completion", "handle_untracked_files"),
    ])
    def test_integration_workflow_matrix(self, git_state, progress_tracking, consensus_type, workflow_stage, expected_integration, temp_git_repo):
        """Test all integration workflow combinations from Matrix 5"""

        # Setup git state
        if git_state == "clean":
            # Repository is already clean
            pass
        elif git_state == "dirty":
            # Create uncommitted changes
            test_file = os.path.join(temp_git_repo, "dirty_file.txt")
            with open(test_file, "w") as f:
                f.write("Uncommitted changes")
        elif git_state == "conflicts":
            # Create merge conflict scenario
            conflict_file = os.path.join(temp_git_repo, "conflict.txt")
            with open(conflict_file, "w") as f:
                f.write("<<<<<<< HEAD\nContent A\n=======\nContent B\n>>>>>>> branch\n")
        elif git_state == "no_repo":
            # Use non-git directory
            temp_git_repo = tempfile.mkdtemp()
        elif git_state == "detached_head":
            # Checkout specific commit (detached HEAD)
            result = subprocess.run(["git", "rev-parse", "HEAD"],
                                  check=False, cwd=temp_git_repo, capture_output=True, text=True)
            commit_hash = result.stdout.strip()
            subprocess.run(["git", "checkout", commit_hash], check=False, cwd=temp_git_repo, capture_output=True)
        elif git_state == "merge_conflicts":
            # Create actual merge conflict
            subprocess.run(["git", "checkout", "-b", "test-branch"], check=False, cwd=temp_git_repo)
            with open(os.path.join(temp_git_repo, "README.md"), "w") as f:
                f.write("# Modified in branch\n")
            subprocess.run(["git", "add", "."], check=False, cwd=temp_git_repo)
            subprocess.run(["git", "commit", "-m", "Branch change"], check=False, cwd=temp_git_repo)
            subprocess.run(["git", "checkout", "main"], check=False, cwd=temp_git_repo)
            with open(os.path.join(temp_git_repo, "README.md"), "w") as f:
                f.write("# Modified in main\n")
            subprocess.run(["git", "add", "."], check=False, cwd=temp_git_repo)
            subprocess.run(["git", "commit", "-m", "Main change"], check=False, cwd=temp_git_repo)
        elif git_state == "untracked_files":
            # Create untracked files
            untracked_file = os.path.join(temp_git_repo, "untracked.txt")
            with open(untracked_file, "w") as f:
                f.write("Untracked content")

        # Setup progress tracking
        progress_data = {}
        if progress_tracking == "file_updates":
            progress_data = {
                "files_changed": 3,
                "lines_added": 150,
                "lines_removed": 25
            }
        elif progress_tracking == "session_state":
            progress_data = {
                "iteration": 2,
                "stage": workflow_stage,
                "start_time": "2025-01-01T10:00:00",
                "status": "active"
            }
        elif progress_tracking == "iteration_data":
            progress_data = {
                "iteration": 1,
                "duration": 300,
                "status": "complete",
                "actions": ["planning", "execution", "validation"]
            }

        # Setup consensus response
        if consensus_type == "achieved":
            consensus_response = "CONVERGED - All objectives achieved successfully"
        elif consensus_type == "failed":
            consensus_response = "Failed to achieve consensus - major gaps remain"
        elif consensus_type == "partial":
            consensus_response = "Partial progress made - some objectives met"
        elif consensus_type == "timeout":
            consensus_response = "Timeout occurred before consensus could be reached"

        # Test integration - these will fail until integration is implemented
        try:
            if git_state != "no_repo":
                # Test git integration
                integration_result = integrate_git_workflow(
                    temp_git_repo,
                    {"stage": workflow_stage, "consensus": consensus_type}
                )

                if expected_integration == "successful_workflow":
                    assert integration_result is not None
                elif expected_integration == "handle_uncommitted_changes":
                    # Should detect and handle uncommitted changes
                    assert "uncommitted" in str(integration_result).lower()
                elif expected_integration == "conflict_resolution":
                    # Should detect conflicts
                    assert "conflict" in str(integration_result).lower()

            # Test progress tracking
            if progress_tracking != "none":
                update_progress_file(temp_git_repo, progress_data)

                progress_files = [f for f in os.listdir(temp_git_repo) if "progress" in f]
                assert len(progress_files) > 0, "Should create progress file"

            # Test consensus checking
            consensus_result = check_consensus(
                "Test goal",
                "Test criteria",
                consensus_response,
                f"Context for {workflow_stage}"
            )

            if consensus_type == "achieved":
                assert consensus_result is True or "success" in str(consensus_result).lower()
            elif consensus_type == "failed":
                assert consensus_result is False or "failed" in str(consensus_result).lower()

        except Exception as e:
            # Should handle integration errors gracefully
            if expected_integration == "non_git_mode_operation":
                # Expected for non-git scenarios
                pass
            else:
                pytest.fail(f"Integration failed for {git_state}/{consensus_type}: {e}")

    def test_git_workflow_edge_cases_matrix(self, temp_git_repo):
        """Test git workflow edge cases from Matrix 5"""

        edge_cases = [
            ("empty_repository", lambda: subprocess.run(["git", "checkout", "--orphan", "empty"], check=False, cwd=temp_git_repo)),
            ("bare_repository", lambda: subprocess.run(["git", "config", "core.bare", "true"], check=False, cwd=temp_git_repo)),
            ("corrupted_git", lambda: os.remove(os.path.join(temp_git_repo, ".git", "HEAD"))),
            ("permission_denied", lambda: os.chmod(os.path.join(temp_git_repo, ".git"), 0o000)),
        ]

        for case_name, setup_func in edge_cases:
            if case_name == "permission_denied":
                # Skip on systems where we can't change .git permissions
                continue

            try:
                setup_func()

                # This will fail until edge case handling is implemented
                result = integrate_git_workflow(temp_git_repo, {"test": True})

                if case_name == "corrupted_git":
                    pytest.fail("Should have detected git corruption")

            except Exception as e:
                # Should handle edge cases gracefully
                if case_name in ["corrupted_git", "bare_repository"]:
                    # Expected failures
                    assert "git" in str(e).lower() or "repository" in str(e).lower()

    def test_consensus_detection_matrix(self):
        """Test consensus detection scenarios from Matrix 5"""

        consensus_scenarios = [
            ("clear_success", "CONVERGED - All criteria met successfully", True, 0.9),
            ("clear_failure", "Failed to achieve any meaningful progress", False, 0.1),
            ("partial_success", "Some progress made but gaps remain", False, 0.6),
            ("ambiguous_response", "Results are mixed with some issues", False, 0.4),
            ("timeout_scenario", "Process timed out before completion", False, 0.2),
            ("error_response", "Error occurred during validation", False, 0.0),
        ]

        goal = "Implement comprehensive test coverage"
        criteria = "All functions tested, edge cases covered, performance validated"

        for scenario_name, response, expected_consensus, expected_confidence in consensus_scenarios:
            # This will fail until consensus detection is implemented
            consensus_result = check_consensus(goal, criteria, response)

            if isinstance(consensus_result, bool):
                assert consensus_result == expected_consensus, \
                    f"Consensus detection failed for {scenario_name}"
            elif isinstance(consensus_result, dict):
                # More detailed consensus result
                assert consensus_result.get("achieved", False) == expected_consensus
                if "confidence" in consensus_result:
                    assert abs(consensus_result["confidence"] - expected_confidence) < 0.2

    def test_learning_integration_matrix(self, temp_git_repo):
        """Test learning integration scenarios from Matrix 5"""

        learning_scenarios = [
            ("successful_iteration", 1, "Test approach worked well - continue pattern"),
            ("failed_iteration", 2, "Approach failed - need different strategy"),
            ("partial_iteration", 3, "Mixed results - refine approach"),
            ("timeout_iteration", 4, "Timeout occurred - optimize for speed"),
        ]

        for scenario_name, iteration_num, learning_note in learning_scenarios:
            # This will fail until learning integration is implemented
            append_genesis_learning(temp_git_repo, iteration_num, learning_note)

            # Verify learning was recorded
            learning_files = [f for f in os.listdir(temp_git_repo) if "learning" in f.lower()]
            if learning_files:
                learning_file = learning_files[0]
                with open(os.path.join(temp_git_repo, learning_file)) as f:
                    content = f.read()
                    assert str(iteration_num) in content
                    assert learning_note in content

    def test_workflow_stage_transitions_matrix(self, temp_git_repo):
        """Test workflow stage transitions from Matrix 5"""

        stage_transitions = [
            ("planning", "execution", "valid_plan"),
            ("execution", "validation", "work_completed"),
            ("validation", "completion", "validation_passed"),
            ("completion", "planning", "new_iteration"),
            ("execution", "planning", "execution_failed"),
            ("validation", "execution", "validation_failed"),
        ]

        for from_stage, to_stage, transition_reason in stage_transitions:
            # This will fail until stage transitions are implemented
            transition_data = {
                "from_stage": from_stage,
                "to_stage": to_stage,
                "reason": transition_reason,
                "timestamp": "2025-01-01T10:00:00"
            }

            update_progress_file(temp_git_repo, transition_data)

            # Verify transition was recorded
            progress_files = [f for f in os.listdir(temp_git_repo) if "progress" in f]
            if progress_files:
                with open(os.path.join(temp_git_repo, progress_files[0])) as f:
                    progress_data = json.load(f)
                    if isinstance(progress_data, dict):
                        assert progress_data.get("to_stage") == to_stage


if __name__ == "__main__":
    # These tests MUST fail in RED phase
    pytest.main([__file__, "-v", "--tb=short"])
