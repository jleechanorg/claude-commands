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
from typing import Iterable, List


def _safe_print(message: str) -> None:
    """Print helper that tolerates encoding issues."""
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("utf-8", errors="replace").decode("utf-8"))


def _load_payload() -> dict | None:
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


def _is_safe_path(path: str) -> bool:
    return not (path.startswith("/") or ".." in path or any(ch in path for ch in "\n\r\t"))


def _build_commands(root: str, rel_path: str) -> List[str]:
    pre_commit = shutil.which("pre-commit")
    quoted_rel = shlex.quote(rel_path)
    commands: List[str] = []

    if pre_commit:
        commands.append(f"{shlex.quote(pre_commit)} run --files {quoted_rel}")
        return commands

    ruff = shutil.which("ruff")
    isort = shutil.which("isort")
    mypy = shutil.which("mypy")
    bandit = shutil.which("bandit")

    if ruff:
        commands.append(f"{shlex.quote(ruff)} check {quoted_rel}")
        commands.append(f"{shlex.quote(ruff)} format --check {quoted_rel}")
    if isort:
        commands.append(f"{shlex.quote(isort)} {quoted_rel} --check-only --diff")
    if mypy:
        commands.append(f"{shlex.quote(mypy)} {quoted_rel}")
    if bandit:
        # Use repository-level configuration if present
        config_path = os.path.join(root, "pyproject.toml")
        if os.path.exists(config_path):
            commands.append(
                f"{shlex.quote(bandit)} -c {shlex.quote(config_path)} -r {quoted_rel}"
            )
        else:
            commands.append(f"{shlex.quote(bandit)} -r {quoted_rel}")

    return commands


def _launch_async(commands: Iterable[str], root: str, log_file: str) -> None:
    script_lines = ["set -e", f"cd {shlex.quote(root)}"]
    script_lines.extend(commands)
    script_content = "\n".join(script_lines)

    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    header = (
        f"=== Async Python lint started {datetime.datetime.now().isoformat()} ===\n"
    )
    with open(log_file, "ab", buffering=0) as log_handle:
        log_handle.write(header.encode("utf-8"))
        subprocess.Popen(  # noqa: PLW1510 - we intentionally detach the process
            ["bash", "-lc", script_content],
            stdout=log_handle,
            stderr=log_handle,
            cwd=root,
            start_new_session=True,
        )


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

    if not _is_safe_path(file_path):
        _safe_print(f"python_async_lint: unsafe path '{file_path}' - skipping")
        return 0

    if not _is_python_file(file_path):
        return 0

    root = _get_repo_root()
    abs_path = os.path.abspath(os.path.join(root, file_path))
    if not abs_path.startswith(root):
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
    sys.exit(main())
