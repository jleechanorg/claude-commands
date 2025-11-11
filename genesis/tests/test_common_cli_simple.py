from collections.abc import Sequence

import pytest

from genesis.common_cli import (
    DEFAULT_MAX_ITERATIONS,
    DEFAULT_POOL_SIZE,
    USAGE_MESSAGE,
    GenesisHelpRequested,
    GenesisUsageError,
    extract_model_preference,
    parse_genesis_cli,
    print_usage,
)


def run_parse(argv: Sequence[str]):
    """Helper to invoke parse_genesis_cli with a custom argv sequence."""
    return parse_genesis_cli(list(argv))


def test_parse_goal_mode_with_defaults():
    args = run_parse(["genesis.py", "goals/example-goal"])

    assert args.mode == "goal"
    assert args.goal_directory == "goals/example-goal"
    assert args.max_iterations == DEFAULT_MAX_ITERATIONS
    assert args.skip_initial_generation is False
    assert args.interactive is False
    assert args.use_codex is True
    assert args.pool_size == DEFAULT_POOL_SIZE


def test_parse_refine_mode_with_flags():
    args = run_parse(
        [
            "genesis.py",
            "--refine",
            "build an api",
            "7",
            "--iterate",
            "--interactive",
            "--claude",
            "--pool-size",
            "9",
        ]
    )

    assert args.mode == "refine"
    assert args.goal_directory is None
    assert args.refine_goal == "build an api"
    assert args.max_iterations == 7
    assert args.skip_initial_generation is True
    assert args.interactive is True
    assert args.use_codex is False
    assert args.pool_size == 9


def test_parse_goal_mode_invalid_max_iterations():
    with pytest.raises(GenesisUsageError) as excinfo:
        run_parse(["genesis.py", "goals/example-goal", "not-a-number"])

    message = str(excinfo.value)
    assert "Invalid max_iterations value" in message
    assert USAGE_MESSAGE.strip() in message


def test_parse_rejects_conflicting_model_flags():
    with pytest.raises(GenesisUsageError, match="Cannot specify both --codex and --claude"):
        run_parse(["genesis.py", "--refine", "goal", "--codex", "--claude"])


def test_parse_rejects_unknown_arguments():
    with pytest.raises(GenesisUsageError) as excinfo:
        run_parse(["genesis.py", "goals/x", "--unknown"])

    assert "Unexpected arguments" in str(excinfo.value)


@pytest.mark.parametrize("flag", ["--help", "-h"])
def test_parse_help_requests_exit(flag):
    with pytest.raises(GenesisHelpRequested):
        run_parse(["genesis.py", flag])


def test_parse_help_takes_precedence_over_unknown_arguments():
    with pytest.raises(GenesisHelpRequested):
        run_parse(["genesis.py", "--help", "--unknown"])


@pytest.mark.parametrize(
    "argv, expected",
    [
        ([], None),
        (["script.py", "--claude"], False),
        (["script.py", "--codex"], True),
        (["script.py", "--claude", "--codex"], True),
    ],
)
def test_extract_model_preference(argv, expected):
    assert extract_model_preference(argv) is expected


@pytest.mark.parametrize(
    "argv",
    [
        ["genesis.py", "goals/example-goal", "0"],
        ["genesis.py", "--refine", "goal", "0"],
        ["genesis.py", "goals/example-goal", "-1"],
        ["genesis.py", "--refine", "goal", "-3"],
    ],
)
def test_parse_rejects_non_positive_max_iterations(argv):
    with pytest.raises(GenesisUsageError, match="positive integer"):
        run_parse(argv)


@pytest.mark.parametrize("value", ["0", "-5"])
def test_parse_rejects_non_positive_pool_size(value):
    with pytest.raises(GenesisUsageError, match="pool size must be a positive integer"):
        run_parse(["genesis.py", "goals/example-goal", "--pool-size", value])


def test_print_usage_stdout(capsys):
    print_usage()
    captured = capsys.readouterr()

    assert USAGE_MESSAGE.strip() in captured.out
    assert captured.err == ""


def test_print_usage_with_error_message(capsys):
    print_usage("Some problem occurred")
    captured = capsys.readouterr()

    assert "Some problem occurred" in captured.err
    assert USAGE_MESSAGE.strip() in captured.err
    assert captured.out == ""
