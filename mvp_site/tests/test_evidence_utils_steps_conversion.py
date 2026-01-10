"""
Unit tests for evidence_utils.py steps-to-scenarios conversion.

Validates that steps dict format is correctly converted to scenarios list
without duplication or data loss.
"""

import sys
from pathlib import Path
from typing import Any

# Add testing_mcp to path for imports
testing_mcp_path = Path(__file__).parent.parent.parent / "testing_mcp"
sys.path.insert(0, str(testing_mcp_path))

from testing_mcp.lib.evidence_utils import create_evidence_bundle


def test_steps_to_scenarios_no_duplicates():
    """Verify steps dict conversion doesn't create duplicate scenario entries."""
    # Simulate test results with "steps" dict format (not "scenarios" list)
    test_results = {
        "test_name": "example_test",
        "steps": {
            "step_1": {"success": True},
            "step_2": {"success": True},
            "step_3": {"success": False, "error": "Step 3 failed"},
        },
    }

    # Create minimal evidence bundle
    evidence_dir = Path("/tmp/test_evidence_steps_conversion")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    files = create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name="example_test",
        provenance={"git_head": "abc123", "git_branch": "test"},
        results=test_results,
    )
    bundle_path = evidence_dir / "iteration_001"

    # Read evidence.md to verify scenario counts
    evidence_md = (bundle_path / "evidence.md").read_text()

    # Verify: Should show 3 scenarios (not 6 due to duplicates)
    assert "Total Scenarios:** 3" in evidence_md, (
        f"Expected 3 scenarios, evidence.md shows different count:\n{evidence_md}"
    )

    # Verify: Should show 2 passed, 1 failed
    assert "Passed:** 2" in evidence_md, "Expected 2 passed scenarios"
    assert "Failed:** 1" in evidence_md, "Expected 1 failed scenario"

    # Verify: Each step name appears exactly once
    assert evidence_md.count("### step_1") == 1, "step_1 should appear once"
    assert evidence_md.count("### step_2") == 1, "step_2 should appear once"
    assert evidence_md.count("### step_3") == 1, "step_3 should appear once"


def test_steps_to_scenarios_with_error_details():
    """Verify error details are preserved during conversion."""
    test_results = {
        "test_name": "error_detail_test",
        "steps": {
            "validation_step": {
                "success": False,
                "error": "Validation failed: missing required field",
            },
            "success_step": {"success": True},
        },
    }

    evidence_dir = Path("/tmp/test_evidence_error_details")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    files = create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name="error_detail_test",
        provenance={"git_head": "def456", "git_branch": "test"},
        results=test_results,
    )
    bundle_path = evidence_dir / "iteration_001"

    evidence_md = (bundle_path / "evidence.md").read_text()

    # Verify error message is captured
    assert "Validation failed: missing required field" in evidence_md, (
        "Error message should be preserved in evidence"
    )


def test_steps_invalid_data_type():
    """Verify invalid step data type is handled gracefully."""
    test_results = {
        "test_name": "invalid_type_test",
        "steps": {
            "valid_step": {"success": True},
            "invalid_step": "this_is_a_string_not_a_dict",  # Invalid type
        },
    }

    evidence_dir = Path("/tmp/test_evidence_invalid_type")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    files = create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name="invalid_type_test",
        provenance={"git_head": "ghi789", "git_branch": "test"},
        results=test_results,
    )
    bundle_path = evidence_dir / "iteration_001"

    evidence_md = (bundle_path / "evidence.md").read_text()

    # Verify invalid type is reported as error
    assert "Invalid step data type" in evidence_md, (
        "Invalid step data should be reported"
    )
    # Should still show 2 scenarios (not 4 due to duplicates)
    assert "Total Scenarios:** 2" in evidence_md, "Expected 2 scenarios"


def test_scenarios_list_format_unchanged():
    """Verify scenarios list format passes through unchanged."""
    test_results = {
        "test_name": "scenarios_list_test",
        "scenarios": [
            {"name": "scenario_1", "errors": []},
            {"name": "scenario_2", "errors": ["Failed"]},
        ],
    }

    evidence_dir = Path("/tmp/test_evidence_scenarios_list")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    files = create_evidence_bundle(
        evidence_dir=evidence_dir,
        test_name="scenarios_list_test",
        provenance={"git_head": "jkl012", "git_branch": "test"},
        results=test_results,
    )
    bundle_path = evidence_dir / "iteration_001"

    evidence_md = (bundle_path / "evidence.md").read_text()

    # Verify scenarios list format works correctly (no conversion needed)
    assert "Total Scenarios:** 2" in evidence_md, "Expected 2 scenarios"
    assert "Passed:** 1" in evidence_md, "Expected 1 passed"
    assert "Failed:** 1" in evidence_md, "Expected 1 failed"
