import logging
import os
import threading
from unittest.mock import patch

import pytest

from mvp_site import logging_util


def _restore_root_logger(original_handlers, original_level):
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        if handler not in original_handlers:
            handler.close()
    for handler in original_handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(original_level)


def _reset_logging_state():
    logging_util._logging_initialized = False
    logging_util._configured_service_name = None
    logging_util._configured_log_file = None


def test_get_repo_name_parses_https_remote():
    with patch("mvp_site.logging_util.subprocess.check_output") as mock_check_output:
        mock_check_output.return_value = "https://github.com/user/worldarchitect.ai.git\n"

        assert logging_util.LoggingUtil.get_repo_name() == "worldarchitect.ai"
        assert mock_check_output.call_args.kwargs["timeout"] == 30


def test_get_repo_name_parses_ssh_remote():
    with patch("mvp_site.logging_util.subprocess.check_output") as mock_check_output:
        mock_check_output.return_value = "git@github.com:user/worldarchitect.ai.git\n"

        assert logging_util.LoggingUtil.get_repo_name() == "worldarchitect.ai"
        assert mock_check_output.call_args.kwargs["timeout"] == 30


def test_get_repo_name_falls_back_to_git_root():
    with patch("mvp_site.logging_util.subprocess.check_output") as mock_check_output:
        mock_check_output.side_effect = [
            logging_util.subprocess.CalledProcessError(1, "git"),
            "/path/to/worldarchitect.ai\n",
        ]

        assert logging_util.LoggingUtil.get_repo_name() == "worldarchitect.ai"
        assert mock_check_output.call_args.kwargs["timeout"] == 30


def test_get_branch_name_returns_branch():
    with patch("mvp_site.logging_util.subprocess.check_output") as mock_check_output:
        mock_check_output.return_value = "feature/logging\n"

        assert logging_util.LoggingUtil.get_branch_name() == "feature/logging"
        assert mock_check_output.call_args.kwargs["timeout"] == 30


def test_get_branch_name_returns_unknown_on_failure():
    with patch("mvp_site.logging_util.subprocess.check_output") as mock_check_output:
        mock_check_output.side_effect = logging_util.subprocess.CalledProcessError(
            1, "git"
        )

        assert logging_util.LoggingUtil.get_branch_name() == "unknown"


def test_setup_unified_logging_reuses_initial_service_name():
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    _reset_logging_state()

    try:
        with (
            patch.object(logging_util.LoggingUtil, "get_repo_name", return_value="repo"),
            patch.object(
                logging_util.LoggingUtil, "get_branch_name", return_value="branch"
            ),
        ):
            first_path = logging_util.setup_unified_logging("flask-server")
            second_path = logging_util.setup_unified_logging("mcp-server")

        assert first_path == second_path
        assert logging_util._configured_service_name == "flask-server"
    finally:
        _restore_root_logger(original_handlers, original_level)
        _reset_logging_state()


def test_setup_unified_logging_is_thread_safe_and_idempotent():
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level
    _reset_logging_state()
    results = []

    try:
        with (
            patch.object(logging_util.LoggingUtil, "get_repo_name", return_value="repo"),
            patch.object(
                logging_util.LoggingUtil, "get_branch_name", return_value="branch"
            ),
        ):
            def _call_setup():
                results.append(logging_util.setup_unified_logging("worker"))

            threads = [threading.Thread(target=_call_setup) for _ in range(5)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        assert logging_util.is_logging_initialized()
        assert len(set(results)) == 1

        file_handlers = [
            handler
            for handler in logging.getLogger().handlers
            if isinstance(handler, logging.FileHandler)
            and handler.baseFilename.endswith(
                os.path.join("/tmp", "repo", "branch", "worker.log")
            )
        ]
        assert len(file_handlers) == 1
    finally:
        _restore_root_logger(original_handlers, original_level)
        _reset_logging_state()
