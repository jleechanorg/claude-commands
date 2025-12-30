"""Centralized evidence capture utilities for evidence bundles."""

import json
import os
import subprocess
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict


def _run_cmd(cmd: list[str]) -> tuple[int, str]:
    """Run a command and return (returncode, stdout)."""
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return result.returncode, result.stdout.strip()


def capture_git_provenance(fetch_origin: bool = True) -> Dict[str, Any]:
    """Collect git provenance details for the current repository."""

    if fetch_origin:
        subprocess.run(["git", "fetch", "origin"], check=False, capture_output=True)

    provenance: Dict[str, Any] = {}

    _, head = _run_cmd(["git", "rev-parse", "HEAD"])
    _, branch = _run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, origin_main = _run_cmd(["git", "rev-parse", "origin/main"])
    _, merge_base = _run_cmd(["git", "merge-base", "HEAD", "origin/main"])

    provenance.update(
        {
            "working_directory": os.getcwd(),
            "git_head": head or None,
            "git_branch": branch or None,
            "origin_main": origin_main or None,
            "merge_base": merge_base or None,
        }
    )

    ahead_rc, ahead_out = _run_cmd(["git", "rev-list", "--left-right", "--count", "origin/main...HEAD"])
    if ahead_rc == 0 and ahead_out:
        parts = ahead_out.split()
        if len(parts) >= 2:
            provenance["commits_ahead_of_main"] = parts[1]
            provenance["commits_behind_main"] = parts[0]

    return provenance


def capture_server_runtime(port: int) -> Dict[str, Any]:
    """Capture runtime metadata for a local server listening on `port`."""

    runtime: Dict[str, Any] = {"port": port}

    proc = subprocess.run(
        ["lsof", "-i", f":{port}", "-sTCP:LISTEN", "-Pn"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.stdout:
        runtime["lsof"] = proc.stdout.strip()

    env_vars = {key: os.environ.get(key) for key in ["WORLDAI_DEV_MODE", "PYTHONPATH", "VIRTUAL_ENV"] if key in os.environ}
    if env_vars:
        runtime["env"] = env_vars

    return runtime


def capture_server_health(server_url: str) -> Dict[str, Any]:
    """Placeholder health check hook for server endpoints."""

    return {"server_url": server_url, "status": "unknown"}


def capture_full_provenance(port: int, server_url: str) -> Dict[str, Any]:
    """Combine git, server runtime, and health provenance."""

    git_info = capture_git_provenance(fetch_origin=False)
    server_info = capture_server_runtime(port)
    health = capture_server_health(server_url)

    return {"git": git_info, "server": server_info, "health": health}


def write_with_checksum(path: Path | str, data: Any) -> Dict[str, str]:
    """Write data to path and persist checksum."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    payload = data
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, indent=2)
    elif not isinstance(data, (str, bytes)):
        payload = str(data)

    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
        file_path.write_text(payload, encoding="utf-8")
    else:
        payload_bytes = payload
        file_path.write_bytes(payload_bytes)

    checksum = sha256(payload_bytes).hexdigest()
    checksum_path = file_path.with_suffix(file_path.suffix + ".sha256")
    checksum_path.write_text(checksum, encoding="utf-8")

    return {"path": str(file_path), "checksum": checksum}
