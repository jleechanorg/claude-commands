#!/usr/bin/env python3
"""
Tests for SKILL.md /pair integration documentation completeness.

Per TDD paired beads protocol, these tests verify that the SKILL.md
documentation update meets all requirements from /tmp/codex-skill-pair-task.md.

This is the TESTS BEAD (pair-1770929716-81372-tests) - must be written and failing
before implementation begins.
"""

import re
from pathlib import Path


def read_skill_md():
    """Read the SKILL.md file."""
    skill_md_path = Path(__file__).parent.parent / "SKILL.md"
    return skill_md_path.read_text()


def test_phase_35_section_exists():
    """Verify Phase 3.5 section exists and is comprehensive."""
    content = read_skill_md()

    # Check for Phase 3.5 section header
    assert "## Phase 3.5: Pair Programming Integration" in content, \
        "Missing Phase 3.5 section header"

    # Check for comprehensive guide subtitle
    assert "COMPREHENSIVE GUIDE" in content, \
        "Missing COMPREHENSIVE GUIDE subtitle in Phase 3.5"


def test_configuration_constants_documented():
    """Verify all COPILOT_PAIR_* constants are documented."""
    content = read_skill_md()

    required_constants = [
        "COPILOT_USE_PAIR",
        "COPILOT_PAIR_MIN_SEVERITY",
        "COPILOT_PAIR_IMPORTANT",
        "COPILOT_PAIR_CODER",
        "COPILOT_PAIR_VERIFIER",
        "COPILOT_PAIR_TIMEOUT"
    ]

    for constant in required_constants:
        assert constant in content, \
            f"Missing configuration constant: {constant}"


def test_python_code_examples_present():
    """Verify Python code examples are present for key functions."""
    content = read_skill_md()

    # Check for Python code blocks
    python_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)
    assert len(python_blocks) >= 10, \
        f"Expected at least 10 Python code examples, found {len(python_blocks)}"

    # Check for key function examples
    required_functions = [
        "should_trigger_pair",
        "generate_pair_task_spec",
        "collect_pair_results",
        "enhance_response_with_pair_data"
    ]

    for func in required_functions:
        assert func in content, \
            f"Missing Python code example for function: {func}"


def test_error_handling_documented():
    """Verify error handling for /pair failures is documented."""
    content = read_skill_md()

    # Check for error handling keywords
    assert "try:" in content and "except" in content, \
        "Missing try/except error handling examples"

    assert "TimeoutExpired" in content or "timeout" in content.lower(), \
        "Missing timeout handling documentation"

    assert "Error Handling:" in content or "error" in content.lower(), \
        "Missing error handling section"


def test_codex_verifier_role_documented():
    """Verify Codex verifier role and responsibilities are documented."""
    content = read_skill_md()

    # Check for verifier role section
    assert "Codex as Verifier" in content or "VERIFIER" in content, \
        "Missing Codex verifier role documentation"

    # Check for verifier responsibilities
    verifier_keywords = [
        "IMPLEMENTATION_READY",
        "VERIFICATION_COMPLETE",
        "VERIFICATION_FAILED",
        "code review",
        "run tests"
    ]

    for keyword in verifier_keywords:
        assert keyword in content, \
            f"Missing verifier responsibility keyword: {keyword}"


def test_mcp_mail_protocol_documented():
    """Verify MCP Mail communication protocol is documented."""
    content = read_skill_md()

    # Check for MCP Mail keywords
    mcp_keywords = [
        "MCP Mail",
        "send_message",
        "check_inbox",
        "poll"
    ]

    for keyword in mcp_keywords:
        assert keyword in content, \
            f"Missing MCP Mail keyword: {keyword}"

    # Check for message structure examples
    assert '"session_id"' in content, \
        "Missing session_id in message examples"
    assert '"files_changed"' in content or '"files_modified"' in content, \
        "Missing files_changed/files_modified in message examples"


def test_workflow_examples_present():
    """Verify concrete workflow examples are present."""
    content = read_skill_md()

    # Check for example sections
    example_patterns = [
        r"Example \d+:",
        r"\*\*Scenario\*\*:",
        r"\*\*Flow:\*\*"
    ]

    example_count = sum(len(re.findall(pattern, content))
                        for pattern in example_patterns)

    assert example_count >= 3, \
        f"Expected at least 3 workflow examples, found {example_count}"

    # Check for specific scenarios
    assert "CRITICAL" in content and "Comment" in content, \
        "Missing CRITICAL comment example"
    assert "BLOCKING" in content or "iteration" in content.lower(), \
        "Missing iteration/blocking example"
    assert "timeout" in content.lower() or "TIMEOUT" in content, \
        "Missing timeout fallback example"


def test_testing_instructions_present():
    """Verify testing instructions for validation are present."""
    content = read_skill_md()

    # Check for testing section
    assert "Testing Instructions" in content or "Test Scenario" in content, \
        "Missing testing instructions section"

    # Check for test commands
    assert "pytest" in content or "python3" in content, \
        "Missing test execution commands"


def test_backward_compatibility_documented():
    """Verify backward compatibility notes are present."""
    content = read_skill_md()

    # Check for backward compatibility section
    assert "Backward Compatibility" in content, \
        "Missing Backward Compatibility section"

    # Check for COPILOT_USE_PAIR=false mention
    assert 'COPILOT_USE_PAIR=false' in content or \
           'COPILOT_USE_PAIR": "false"' in content, \
        "Missing backward compatibility with COPILOT_USE_PAIR=false"


def test_step_by_step_execution_guide():
    """Verify step-by-step execution guide exists."""
    content = read_skill_md()

    # Check for numbered steps in Phase 3.5
    step_pattern = r'#### Step \d+:'
    steps = re.findall(step_pattern, content)

    assert len(steps) >= 5, \
        f"Expected at least 5 execution steps, found {len(steps)}"

    # Verify key steps are present
    assert "Step 1" in content and "Trigger Detection" in content, \
        "Missing Step 1: Trigger Detection"
    assert "Step 2" in content and "Task Spec Generation" in content, \
        "Missing Step 2: Task Spec Generation"
    assert "Step 3" in content and "Launch" in content, \
        "Missing Step 3: Launch /pair Session"


def test_verification_checklist_present():
    """Verify verification checklist for Codex is present."""
    content = read_skill_md()

    # Check for checklist markers
    checklist_items = re.findall(r'- \[ \]', content)

    assert len(checklist_items) >= 5, \
        f"Expected at least 5 checklist items, found {len(checklist_items)}"

    # Check for specific checklist content
    assert "Requirements met" in content or "requirements" in content.lower(), \
        "Missing requirements verification in checklist"
    assert "Tests pass" in content or "test" in content.lower(), \
        "Missing test execution in checklist"


def test_constructive_feedback_guidance():
    """Verify guidance for providing constructive feedback is present."""
    content = read_skill_md()

    # Check for feedback guidance
    feedback_keywords = [
        "feedback",
        "VERIFICATION_FAILED",
        "issues_found",
        "suggestions"
    ]

    for keyword in feedback_keywords:
        assert keyword in content, \
            f"Missing feedback keyword: {keyword}"


def test_pair_metadata_structure_documented():
    """Verify pair_metadata structure is documented."""
    content = read_skill_md()

    # Check for pair_metadata documentation
    assert "pair_metadata" in content, \
        "Missing pair_metadata documentation"

    # Check for pair_metadata fields
    metadata_fields = [
        "session_id",
        "status",
        "duration_seconds",
        "test_results"
    ]

    for field in metadata_fields:
        assert field in content, \
            f"Missing pair_metadata field: {field}"


def test_timeout_value_documented():
    """Verify COPILOT_PAIR_TIMEOUT=600 (10 minutes) is explicitly documented."""
    content = read_skill_md()

    # Check for 600 seconds timeout
    assert "600" in content, \
        "Missing COPILOT_PAIR_TIMEOUT=600 value"

    # Check for 10 minutes mention
    assert "10 min" in content or "10-minute" in content or "600s" in content, \
        "Missing 10-minute timeout documentation"


if __name__ == "__main__":
    """Run all tests and report results."""
    import sys

    test_functions = [
        test_phase_35_section_exists,
        test_configuration_constants_documented,
        test_python_code_examples_present,
        test_error_handling_documented,
        test_codex_verifier_role_documented,
        test_mcp_mail_protocol_documented,
        test_workflow_examples_present,
        test_testing_instructions_present,
        test_backward_compatibility_documented,
        test_step_by_step_execution_guide,
        test_verification_checklist_present,
        test_constructive_feedback_guidance,
        test_pair_metadata_structure_documented,
        test_timeout_value_documented
    ]

    print("Running SKILL.md /pair integration tests...")
    print("=" * 70)

    passed = 0
    failed = 0

    for test_func in test_functions:
        test_name = test_func.__name__
        try:
            test_func()
            print(f"✅ PASS: {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"❌ FAIL: {test_name}")
            print(f"   {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {test_name}")
            print(f"   {str(e)}")
            failed += 1

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)
