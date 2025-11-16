#!/usr/bin/env python3
"""Launch asynchronous Python linting after Claude Write operations.

This hook watches for Write tool invocations that create or edit Python files
and launches the project's pre-commit lint suite in the background. It mirrors
our presubmit checks (import ordering, linting, type checks, security scans)
so issues are surfaced immediately while keeping the main session responsive.
"""

from __future__ import annotations

import datetime
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Sequence


def _safe_print(message: str) -> None:
    """Print helper that tolerates encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("utf-8", errors="replace").decode("utf-8"))


def _load_payload() -> dict | None:
    # Avoid blocking if no payload is piped (stdin is a TTY or closed)
    if sys.stdin is None or sys.stdin.closed:
        return None
    try:
        is_tty = sys.stdin.isatty()
    except (AttributeError, ValueError):
        is_tty = False
    if is_tty:
        return None

    raw_input = sys.stdin.read()
    if not raw_input.strip():
        return None
    try:
        return json.loads(raw_input)
    except json.JSONDecodeError:
        _safe_print("python_async_lint: received non-JSON payload; skipping")
        return None


def _get_repo_root() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return completed.stdout.strip() or os.getcwd()
    except subprocess.CalledProcessError:
        return os.getcwd()


def _is_python_file(path: str) -> bool:
    return path.endswith(".py")


def _is_safe_path(path: str, root: str) -> bool:
    """Return True if *path* stays within *root* after normalization."""

    if not path or any(ch in path for ch in "\n\r\t"):
        return False

    root_abs = os.path.abspath(root)
    # Reject absolute paths outright so they cannot escape the repository root.
    if os.path.isabs(path):
        return False

    normalized = os.path.normpath(path)

    # Paths that backtrack beyond the repository ("../") are disallowed.
    if normalized.startswith(".."):
        return False

    candidate = os.path.abspath(os.path.join(root_abs, normalized))
    try:
        common = os.path.commonpath([root_abs, candidate])
    except ValueError:
        return False
    return common == root_abs


def _build_commands(root: str, rel_path: str) -> list[list[str]]:
    pre_commit = shutil.which("pre-commit")
    commands: list[list[str]] = []

    if pre_commit:
        commands.append([pre_commit, "run", "--files", rel_path])
        return commands

    ruff = shutil.which("ruff")
    isort = shutil.which("isort")
    mypy = shutil.which("mypy")
    bandit = shutil.which("bandit")

    if ruff:
        commands.append([ruff, "check", rel_path])
        commands.append([ruff, "format", "--check", rel_path])
    if isort:
        commands.append([isort, rel_path, "--check-only", "--diff"])
    if mypy:
        commands.append([mypy, rel_path])
    if bandit:
        # Use repository-level configuration if present
        config_path = os.path.join(root, "pyproject.toml")
        if os.path.exists(config_path):
            commands.append([bandit, "-c", config_path, "-r", rel_path])
        else:
            commands.append([bandit, "-r", rel_path])

    return commands


def _log_write(handle, text: str) -> None:
    handle.write(text.encode("utf-8", errors="replace"))


def _run_worker(payload_path: str) -> int:
    try:
        with open(payload_path, encoding="utf-8") as payload_handle:
            payload = json.load(payload_handle)
    except (OSError, json.JSONDecodeError) as exc:
        _safe_print(f"python_async_lint worker: failed to load payload: {exc}")
        return 1
    finally:
        try:
            os.unlink(payload_path)
        except OSError:
            pass

    root = payload.get("root")
    commands = payload.get("commands") or []
    log_file = payload.get("log_file")
    if not root or not log_file:
        _safe_print("python_async_lint worker: missing root or log_file")
        return 1

    root = os.path.abspath(root)
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    exit_code = 0
    with open(log_file, "ab", buffering=0) as log_handle:
        start_msg = (
            f"=== Async Python lint started {datetime.datetime.now().isoformat()} ===\n"
        )
        _log_write(log_handle, start_msg)

        for raw_command in commands:
            if not isinstance(raw_command, list) or not raw_command:
                continue
            command = [str(part) for part in raw_command]
            display = "$ " + shlex.join(command) + "\n"
            _log_write(log_handle, display)
            completed = subprocess.run(
                command,
                check=False, cwd=root,
                stdout=log_handle,
                stderr=log_handle,
            )
            result_line = f"[exit code {completed.returncode}]\n"
            _log_write(log_handle, result_line)
            if completed.returncode != 0 and exit_code == 0:
                exit_code = completed.returncode

        finish_status = (
            "succeeded" if exit_code == 0 else "finished with errors"
        )
        end_msg = (
            f"=== Async Python lint {finish_status} at "
            f"{datetime.datetime.now().isoformat()} ===\n"
        )
        _log_write(log_handle, end_msg)

    return exit_code


def _launch_async(commands: Sequence[Sequence[str]], root: str, log_file: str) -> None:
    payload = {
        "root": root,
        "commands": commands,
        "log_file": log_file,
    }

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as temp:
        json.dump(payload, temp)
        payload_path = temp.name

    python_executable = sys.executable or shutil.which("python3") or "python3"

    try:
        subprocess.Popen(  # noqa: PLW1510 - we intentionally detach the process
            [python_executable, os.path.abspath(__file__), "--worker", payload_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError as exc:
        _safe_print(f"python_async_lint: failed to launch async worker: {exc}")
        try:
            os.unlink(payload_path)
        except OSError:
            pass


def main() -> int:
    payload = _load_payload()
    if not payload:
        return 0

    if payload.get("tool_name") != "Write":
        return 0

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0

    if not _is_python_file(file_path):
        return 0

    root = os.path.abspath(_get_repo_root())

    if not _is_safe_path(file_path, root):
        _safe_print(f"python_async_lint: unsafe path '{file_path}' - skipping")
        return 0

    normalized_rel = os.path.normpath(file_path)
    abs_path = os.path.abspath(os.path.join(root, normalized_rel))
    try:
        common = os.path.commonpath([root, abs_path])
    except ValueError:
        _safe_print(
            f"python_async_lint: resolved path outside repository ({abs_path}) - skipping"
        )
        return 0
    if common != root:
        _safe_print(
            f"python_async_lint: resolved path outside repository ({abs_path}) - skipping"
        )
        return 0

    if not os.path.exists(abs_path):
        # Nothing to lint yet (file may have been deleted)
        return 0

    rel_path = os.path.relpath(abs_path, root)
    commands = _build_commands(root, rel_path)
    if not commands:
        _safe_print(
            "python_async_lint: no lint commands available (install pre-commit or Python linters)"
        )
        return 0

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = os.path.join(root, ".claude", "logs", f"python_lint_{timestamp}.log")
    _launch_async(commands, root, log_file)
    _safe_print(
        f"python_async_lint: launched async lint for {rel_path}. Logs: {os.path.relpath(log_file, root)}"
    )
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        if len(sys.argv) != 3:
            sys.exit(1)
        sys.exit(_run_worker(sys.argv[2]))
    sys.exit(main())
