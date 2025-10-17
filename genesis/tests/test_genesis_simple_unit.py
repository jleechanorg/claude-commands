import json
from pathlib import Path

import pytest

from genesis import genesis_simple


@pytest.mark.parametrize(
    "text, expected",
    [
        ("All tasks complete. genesis completion achieved!", True),
        ("Objective achieved in this run", True),
        ("final assessment pending", True),
        ("No conclusion yet", False),
    ],
)
def test_detect_completion(text, expected):
    assert genesis_simple.detect_completion(text) is expected


def test_build_prompt_includes_context():
    prompt = genesis_simple.build_prompt(
        refined_goal="Ship MVP",
        exit_criteria="All tests passing",
        iteration=2,
        max_iterations=5,
        previous_summary="Finished setup",
        skip_initial_generation=False,
    )

    assert "Iteration: 2/5" in prompt
    assert "Ship MVP" in prompt
    assert "All tests passing" in prompt
    assert "Finished setup" in prompt
    assert "Plan + execute" in prompt


def test_build_prompt_iterative_mode_message():
    prompt = genesis_simple.build_prompt(
        refined_goal="Improve docs",
        exit_criteria="",
        iteration=1,
        max_iterations=3,
        previous_summary="",
        skip_initial_generation=True,
    )

    assert "Initial planning is skipped" in prompt
    assert "(no explicit exit criteria provided)" in prompt
    assert "No previous work" in prompt


def test_load_session_handles_missing_file(tmp_path):
    path = tmp_path / "session.json"
    assert genesis_simple.load_session(path) == {}


def test_load_session_invalid_json_warns(tmp_path, capsys):
    path = tmp_path / "session.json"
    path.write_text("not json", encoding="utf-8")

    data = genesis_simple.load_session(path)
    assert data == {}

    captured = capsys.readouterr()
    assert "not valid JSON" in captured.err


def test_save_session_round_trip(tmp_path):
    path = tmp_path / "session.json"
    session = {"current_iteration": 3, "latest_summary": "Done"}

    genesis_simple.save_session(path, session)

    assert path.exists()
    reloaded = json.loads(path.read_text(encoding="utf-8"))
    assert reloaded == session


def test_ensure_goal_context_sets_default():
    session = {}
    genesis_simple.ensure_goal_context("goals/test", session)

    assert session["goal_directory"] == "goals/test"

    genesis_simple.ensure_goal_context("goals/test", session)
    assert session["goal_directory"] == "goals/test"


def test_summarize_output_limits_lines():
    lines = [f"line {i}" for i in range(60)]
    output = "\n".join(lines)

    summary = genesis_simple.summarize_output(output)

    expected = "\n".join(lines[-genesis_simple.MAX_SUMMARY_LINES :])
    assert summary == expected
