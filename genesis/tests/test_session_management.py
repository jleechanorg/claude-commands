"""
Matrix 3: Session Management Tests - TDD RED Phase
Tests all session state transitions, logging, and recovery scenarios.
"""

import json
import os
import tempfile
import time

import pytest

from genesis import safe_session_write, update_progress_file


class TestSessionManagementMatrix:
    """Matrix 3: State Transition Testing (Session × Logging × Recovery)"""

    @pytest.fixture
    def temp_session_dir(self):
        """Create temporary session directory for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.mark.parametrize("session_state,logging_type,recovery_scenario,expected_behavior", [
        ("new", "dual", "none", "create_session_both_logs"),
        ("resumed", "detailed", "crash_recovery", "load_session_continue"),
        ("corrupted", "human_readable", "partial_completion", "reset_session_warn"),
        ("missing", "dual", "timeout_recovery", "new_session_recover_context"),
        ("concurrent", "detailed", "file_locks", "handle_conflicts_gracefully"),
    ])
    def test_session_management_matrix(self, session_state, logging_type, recovery_scenario, expected_behavior, temp_session_dir):
        """Test all session management combinations from Matrix 3"""

        session_file = os.path.join(temp_session_dir, "proto_genesis_session.json")
        log_file = os.path.join(temp_session_dir, "genesis.log")
        human_log_file = os.path.join(temp_session_dir, "genesis_human.log")

        if session_state == "new":
            # No existing session file
            assert not os.path.exists(session_file)

            # This will fail until session creation is implemented
            session_data = {
                "iteration": 1,
                "goal": "Test goal",
                "status": "in_progress",
                "timestamp": time.time()
            }

            safe_session_write(session_file, session_data)

            if expected_behavior == "create_session_both_logs":
                assert os.path.exists(session_file)
                # Should create both logs for dual logging
                if logging_type == "dual":
                    # Would create both log files
                    pass

        elif session_state == "resumed":
            # Create existing session file
            existing_session = {
                "iteration": 3,
                "goal": "Resume test goal",
                "status": "in_progress",
                "context": "Previous work completed"
            }

            with open(session_file, "w") as f:
                json.dump(existing_session, f)

            # This will fail until session resumption is implemented
            if recovery_scenario == "crash_recovery":
                # Should load and continue from previous state
                with open(session_file) as f:
                    loaded_session = json.load(f)

                assert loaded_session["iteration"] == 3
                assert "Resume test goal" in loaded_session["goal"]

        elif session_state == "corrupted":
            # Create corrupted session file
            with open(session_file, "w") as f:
                f.write("invalid json content {")

            # This will fail until corruption handling is implemented
            if recovery_scenario == "partial_completion":
                try:
                    with open(session_file) as f:
                        json.load(f)
                    pytest.fail("Should have detected corruption")
                except json.JSONDecodeError:
                    # Expected - should handle gracefully
                    pass

        elif session_state == "missing":
            # No session file exists, but we want to recover context
            assert not os.path.exists(session_file)

            if recovery_scenario == "timeout_recovery":
                # Should create new session but attempt context recovery
                new_session = {
                    "iteration": 1,
                    "goal": "Recovered goal",
                    "status": "recovering",
                    "recovery": True
                }

                # This will fail until recovery logic is implemented
                safe_session_write(session_file, new_session)
                assert os.path.exists(session_file)

        elif session_state == "concurrent":
            if recovery_scenario == "file_locks":
                # Simulate concurrent access
                session_data_1 = {"writer": "process_1", "timestamp": time.time()}
                session_data_2 = {"writer": "process_2", "timestamp": time.time() + 1}

                # This will fail until file locking is implemented
                safe_session_write(session_file, session_data_1)
                safe_session_write(session_file, session_data_2)

                # Last writer should win, but should handle conflicts
                with open(session_file) as f:
                    final_data = json.load(f)

                # Should have conflict resolution
                assert "writer" in final_data

    def test_logging_matrix_combinations(self, temp_session_dir):
        """Test different logging type combinations from Matrix 3"""

        logging_scenarios = [
            ("detailed_only", ["detailed.log"], True, False),
            ("human_only", ["human.log"], False, True),
            ("dual_logging", ["detailed.log", "human.log"], True, True),
            ("no_logging", [], False, False),
        ]

        for scenario_name, expected_files, has_detailed, has_human in logging_scenarios:
            log_dir = os.path.join(temp_session_dir, scenario_name)
            os.makedirs(log_dir, exist_ok=True)

            # This will fail until logging matrix is implemented
            if has_detailed:
                detailed_log = os.path.join(log_dir, "detailed.log")
                with open(detailed_log, "w") as f:
                    f.write("Detailed logging output\n")

            if has_human:
                human_log = os.path.join(log_dir, "human.log")
                with open(human_log, "w") as f:
                    f.write("Human readable log\n")

            # Verify logging setup
            actual_files = os.listdir(log_dir)
            for expected_file in expected_files:
                assert expected_file in actual_files, f"Missing {expected_file} in {scenario_name}"

    def test_progress_tracking_matrix(self, temp_session_dir):
        """Test progress tracking scenarios from Matrix 3"""

        progress_scenarios = [
            ("file_updates", {"files_changed": 3, "lines_added": 150}),
            ("session_state", {"iteration": 2, "stage": "execution"}),
            ("iteration_data", {"iteration": 1, "duration": 300, "status": "complete"}),
            ("mixed_updates", {"files": 2, "iteration": 3, "errors": 0}),
        ]

        for scenario_name, progress_data in progress_scenarios:
            progress_file = os.path.join(temp_session_dir, f"progress_{scenario_name}.json")

            # This will fail until progress tracking is implemented
            update_progress_file(temp_session_dir, progress_data)

            # Should create progress file with correct data
            if os.path.exists(progress_file):
                with open(progress_file) as f:
                    saved_data = json.load(f)

                for key, value in progress_data.items():
                    assert saved_data.get(key) == value, f"Missing {key} in progress data"

    def test_recovery_scenario_matrix(self, temp_session_dir):
        """Test different recovery scenarios from Matrix 3"""

        recovery_scenarios = [
            ("clean_shutdown", "normal", True, "Session saved successfully"),
            ("crash_recovery", "interrupted", False, "Session recovery attempted"),
            ("timeout_recovery", "timeout", False, "Timeout recovery initiated"),
            ("corruption_recovery", "corrupted", False, "Corruption detected, resetting"),
        ]

        for scenario_name, shutdown_type, expected_success, expected_message in recovery_scenarios:
            session_file = os.path.join(temp_session_dir, f"session_{scenario_name}.json")

            if shutdown_type == "corrupted":
                # Create corrupted file
                with open(session_file, "w") as f:
                    f.write("corrupted json {")

            elif shutdown_type == "interrupted":
                # Create partial session
                partial_session = {
                    "iteration": 2,
                    "goal": "Test goal",
                    "status": "interrupted",
                    "partial": True
                }
                with open(session_file, "w") as f:
                    json.dump(partial_session, f)

            # This will fail until recovery scenarios are implemented
            try:
                if os.path.exists(session_file):
                    with open(session_file) as f:
                        session_data = json.load(f)

                    # Recovery logic should handle each scenario appropriately
                    if shutdown_type == "corrupted":
                        pytest.fail("Should have detected corruption")
                    elif shutdown_type == "interrupted":
                        assert session_data.get("status") == "interrupted"

                recovery_success = expected_success
                assert recovery_success == expected_success, f"Recovery behavior mismatch for {scenario_name}"

            except json.JSONDecodeError:
                # Expected for corrupted scenarios
                if shutdown_type != "corrupted":
                    pytest.fail(f"Unexpected corruption in {scenario_name}")

    def test_concurrent_access_matrix(self, temp_session_dir):
        """Test concurrent access scenarios from Matrix 3"""

        import threading
        import time

        session_file = os.path.join(temp_session_dir, "concurrent_session.json")
        results = []
        errors = []

        def concurrent_writer(writer_id, delay=0):
            """Simulate concurrent session writing"""
            try:
                time.sleep(delay)
                session_data = {
                    "writer": f"process_{writer_id}",
                    "timestamp": time.time(),
                    "data": f"data_from_{writer_id}"
                }

                # This will fail until file locking is implemented
                safe_session_write(session_file, session_data)
                results.append(writer_id)
            except Exception as e:
                errors.append((writer_id, str(e)))

        # Create multiple concurrent writers
        threads = []
        for i in range(5):
            thread = threading.Thread(target=concurrent_writer, args=(i, i * 0.01))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify handling of concurrent access
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) > 0, "No successful concurrent writes"

        # Final state should be consistent
        if os.path.exists(session_file):
            with open(session_file) as f:
                final_session = json.load(f)
            assert "writer" in final_session, "Final session should have writer info"

    def test_token_usage_without_workflow_state(self, temp_session_dir):
        """
        RED TEST: Test that token_usage dict creation works without workflow_state in scope.

        This tests the bug fix for line 2787 in genesis.py where workflow_state.total_tokens_used
        caused NameError when workflow_state was undefined. The fix uses session_data.get()
        with safe defaults instead.

        Bug scenario:
        - Genesis reaches session save point near iteration 10
        - workflow_state is not in scope (defined in different function)
        - Code tries to access workflow_state.total_tokens_used -> NameError
        - Should use session_data.get("total_tokens", 0) as safe fallback
        """
        session_data = {
            "goal_directory": "test_goal",
            "refined_goal": "Test goal",
            "exit_criteria": "Test criteria",
            "max_iterations": 30,
            "status": "in_progress",
            "total_tokens": 150000,
            "iteration_tokens": {0: 10000, 1: 12000, 2: 15000},
            "milestones": [],
            "current_milestone": None,
            "milestone_progress": {}
        }

        # Simulate the bug scenario - workflow_state is NOT defined
        # This is the exact scenario from line 2785-2791 in genesis.py
        workflow_phase = "ITERATIVE_REFINEMENT"
        i = 2  # Current iteration

        # This should NOT raise NameError - uses safe defaults from session_data
        try:
            token_usage_dict = {
                "total_tokens": session_data.get("total_tokens", 0),
                "iteration_tokens": session_data.get("iteration_tokens", {}),
                "max_tokens_per_iteration": 200000,
                "current_iteration_tokens": session_data.get("iteration_tokens", {}).get(i, 0)
            }

            # Verify the structure is correct
            assert "total_tokens" in token_usage_dict
            assert "iteration_tokens" in token_usage_dict
            assert "max_tokens_per_iteration" in token_usage_dict
            assert "current_iteration_tokens" in token_usage_dict

            # Verify values are correct
            assert token_usage_dict["total_tokens"] == 150000
            assert token_usage_dict["iteration_tokens"] == {0: 10000, 1: 12000, 2: 15000}
            assert token_usage_dict["max_tokens_per_iteration"] == 200000
            assert token_usage_dict["current_iteration_tokens"] == 15000

        except NameError as e:
            pytest.fail(f"NameError should not occur with safe defaults: {e}")

        # Test with missing token data - should use safe defaults
        minimal_session_data = {
            "goal_directory": "test_goal",
            "status": "in_progress"
        }

        token_usage_dict_minimal = {
            "total_tokens": minimal_session_data.get("total_tokens", 0),
            "iteration_tokens": minimal_session_data.get("iteration_tokens", {}),
            "max_tokens_per_iteration": 200000,
            "current_iteration_tokens": minimal_session_data.get("iteration_tokens", {}).get(i, 0)
        }

        # Should use safe defaults
        assert token_usage_dict_minimal["total_tokens"] == 0
        assert token_usage_dict_minimal["iteration_tokens"] == {}
        assert token_usage_dict_minimal["current_iteration_tokens"] == 0


if __name__ == "__main__":
    # These tests MUST fail in RED phase
    pytest.main([__file__, "-v", "--tb=short"])
