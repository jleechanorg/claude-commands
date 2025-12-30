"""Centralized evidence capture utilities for testing_mcp tests.

This module provides evidence capture functions that comply with
.claude/skills/evidence-standards.md requirements.

Usage in tests:
    from lib.evidence_utils import (
        capture_git_provenance,
        capture_server_runtime,
        capture_server_health,
        write_with_checksum,
    )

    # At test start
    provenance = capture_git_provenance()
    server_info = capture_server_runtime(port=8082)

    # When writing evidence
    write_with_checksum(Path("evidence.json"), json.dumps(data, indent=2))
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import urllib.request

PROJECT_ROOT = Path(__file__).parent.parent.parent


def get_evidence_dir(work_name: str, timestamp: str | None = None) -> Path:
    """Get evidence directory per evidence-standards.md pattern.

    Pattern: /tmp/<repo>/<branch>/<work>/<timestamp>/

    Args:
        work_name: Name of the work/test (e.g., "god_mode_validation").
        timestamp: Optional timestamp string. If None, uses current time.

    Returns:
        Path to evidence directory (created if it doesn't exist).
    """
    import subprocess

    # Get repo name from git
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10,
        )
        if result.returncode == 0:
            repo_name = Path(result.stdout.strip()).name
        else:
            repo_name = "unknown_repo"
    except Exception:
        repo_name = "unknown_repo"

    # Get branch name
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            branch = result.stdout.strip()
        else:
            branch = "unknown_branch"
    except Exception:
        branch = "unknown_branch"

    # Generate timestamp if not provided
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Build path: /tmp/<repo>/<branch>/<work>/<timestamp>/
    evidence_dir = Path("/tmp") / repo_name / branch / work_name / timestamp
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "artifacts").mkdir(exist_ok=True)

    return evidence_dir


def capture_git_provenance(*, fetch_origin: bool = True) -> dict[str, Any]:
    """Capture git provenance per evidence-standards.md requirements.

    This captures all mandatory git provenance fields:
    - git_head: Current commit SHA
    - git_branch: Current branch name
    - merge_base: Common ancestor with origin/main
    - commits_ahead_of_main: Number of commits ahead
    - diff_stat_vs_main: Summary of changed files
    - changed_files: List of changed file paths

    Args:
        fetch_origin: If True, fetch origin/main first to ensure it's current.

    Returns:
        Dict with git provenance data.
    """
    provenance: dict[str, Any] = {
        "capture_timestamp": datetime.now(timezone.utc).isoformat(),
        "working_directory": str(PROJECT_ROOT),
    }

    def run_git(args: list[str], timeout: int = 10) -> tuple[str, int]:
        """Run git command and return (output, returncode)."""
        try:
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=PROJECT_ROOT,
                timeout=timeout,
            )
            return result.stdout.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "ERROR: timeout", -1
        except Exception as e:
            return f"ERROR: {e}", -1

    # Optionally fetch origin/main to ensure it's current
    if fetch_origin:
        run_git(["fetch", "origin", "main"], timeout=30)

    # Core git state (MANDATORY per evidence-standards.md)
    git_head, rc = run_git(["rev-parse", "HEAD"])
    provenance["git_head"] = git_head if rc == 0 else f"ERROR: {git_head}"

    git_branch, rc = run_git(["branch", "--show-current"])
    provenance["git_branch"] = git_branch if rc == 0 else f"ERROR: {git_branch}"

    merge_base, rc = run_git(["merge-base", "HEAD", "origin/main"])
    provenance["merge_base"] = merge_base if rc == 0 else f"ERROR: {merge_base}"

    commits_ahead, rc = run_git(["rev-list", "--count", "origin/main..HEAD"])
    provenance["commits_ahead_of_main"] = (
        int(commits_ahead) if rc == 0 and commits_ahead.isdigit() else 0
    )

    diff_stat, rc = run_git(["diff", "--stat", "origin/main...HEAD"])
    provenance["diff_stat_vs_main"] = diff_stat if rc == 0 else f"ERROR: {diff_stat}"

    # Changed files list
    changed_files, rc = run_git(["diff", "--name-only", "origin/main...HEAD"])
    if rc == 0 and changed_files:
        provenance["changed_files"] = [f for f in changed_files.split("\n") if f]
    else:
        provenance["changed_files"] = []

    # Also capture origin/main commit for reference
    origin_main, rc = run_git(["rev-parse", "origin/main"])
    provenance["origin_main"] = origin_main if rc == 0 else f"ERROR: {origin_main}"

    return provenance


def capture_server_runtime(
    port: int,
    *,
    host: str = "localhost",
    env_vars: list[str] | None = None,
) -> dict[str, Any]:
    """Capture server runtime info per evidence-standards.md requirements.

    This captures all mandatory server runtime fields:
    - server.pid: Process ID of server
    - server.port: Port number
    - server.process_cmdline: Full command line
    - server.env_vars: Environment variables

    Args:
        port: Server port to check.
        host: Server host (default localhost).
        env_vars: List of env var names to capture (default: standard set).

    Returns:
        Dict with server runtime info.
    """
    if env_vars is None:
        env_vars = [
            "WORLDAI_DEV_MODE",
            "TESTING",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GEMINI_API_KEY",
            "FIREBASE_PROJECT_ID",
        ]

    server_info: dict[str, Any] = {
        "capture_timestamp": datetime.now(timezone.utc).isoformat(),
        "port": port,
        "host": host,
    }

    # Get PIDs listening on port
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            server_info["pid"] = pids[0] if pids else None

            # Get process command line
            if server_info["pid"]:
                cmd_result = subprocess.run(
                    ["ps", "-p", server_info["pid"], "-o", "command="],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if cmd_result.returncode == 0:
                    server_info["process_cmdline"] = cmd_result.stdout.strip()
                else:
                    server_info["process_cmdline"] = None
        else:
            server_info["pid"] = None
            server_info["process_cmdline"] = None
    except Exception as e:
        server_info["pid"] = f"ERROR: {e}"
        server_info["process_cmdline"] = None

    # Capture environment variables (sanitized - only show if set)
    server_info["env_vars"] = {}
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "CREDENTIALS" in var:
                server_info["env_vars"][var] = f"[SET - {len(value)} chars]"
            else:
                server_info["env_vars"][var] = value
        else:
            server_info["env_vars"][var] = None

    return server_info


def capture_server_health(server_url: str, *, timeout: int = 10) -> dict[str, Any]:
    """Capture server health endpoint for version/build info.

    Args:
        server_url: Base URL of the server.
        timeout: Request timeout in seconds.

    Returns:
        Dict with server health data.
    """
    health_url = f"{server_url.rstrip('/')}/health"
    health_info: dict[str, Any] = {
        "capture_timestamp": datetime.now(timezone.utc).isoformat(),
        "url": health_url,
    }

    try:
        req = urllib.request.Request(health_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            health_info["status_code"] = response.status
            content = response.read().decode("utf-8")
            try:
                health_info["data"] = json.loads(content)
            except json.JSONDecodeError:
                health_info["data"] = content
    except Exception as e:
        health_info["status_code"] = None
        health_info["error"] = str(e)

    return health_info


def write_with_checksum(filepath: Path, content: str) -> str:
    """Write file and create SHA256 checksum file.

    Per evidence-standards.md, all evidence files should have checksums.
    The .sha256 file uses the basename format for portability.

    Args:
        filepath: Path to write content to.
        content: String content to write.

    Returns:
        The SHA256 hash of the content.
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content)

    sha256_hash = hashlib.sha256(content.encode()).hexdigest()
    checksum_file = Path(str(filepath) + ".sha256")
    # Use basename only for portability (evidence-standards.md requirement)
    checksum_file.write_text(f"{sha256_hash}  {filepath.name}\n")

    return sha256_hash


def capture_full_provenance(
    port: int,
    server_url: str,
    *,
    fetch_origin: bool = True,
) -> dict[str, Any]:
    """Capture complete provenance for evidence bundle.

    This is a convenience function that captures all required provenance:
    - Git provenance
    - Server runtime info
    - Server health

    Args:
        port: Server port.
        server_url: Server base URL.
        fetch_origin: If True, fetch origin/main first.

    Returns:
        Dict with all provenance data.
    """
    return {
        "git": capture_git_provenance(fetch_origin=fetch_origin),
        "server": capture_server_runtime(port),
        "health": capture_server_health(server_url),
    }
