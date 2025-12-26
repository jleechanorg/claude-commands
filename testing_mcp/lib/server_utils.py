"""Local MCP server utilities for testing."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent
DEFAULT_EVIDENCE_DIR = Path(__file__).parent.parent / "evidence"


@dataclass
class LocalServer:
    """Handle for a locally-started MCP server process."""

    proc: subprocess.Popen[bytes]
    base_url: str
    log_path: Path
    _log_file: Any | None = None

    def stop(self) -> None:
        """Stop the local server process."""
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        if self._log_file:
            self._log_file.close()
            self._log_file = None


def _which(name: str) -> str | None:
    """Find executable in PATH."""
    for d in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(d) / name
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def pick_free_port() -> int:
    """Find an available port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


# Keep old name for backwards compatibility
_pick_free_port = pick_free_port


def _load_secret(env: dict[str, str], *, secret_name: str, env_var: str) -> None:
    """Load a secret from GCP Secret Manager if not already set."""
    if env.get(env_var):
        return
    if not _which("gcloud"):
        return

    project = (
        env.get("GCP_PROJECT")
        or env.get("GOOGLE_CLOUD_PROJECT")
        or "worldarchitecture-ai"
    )
    try:
        value = (
            subprocess.check_output(
                [
                    "gcloud",
                    "secrets",
                    "versions",
                    "access",
                    "latest",
                    "--secret",
                    secret_name,
                    "--project",
                    project,
                ],
                stderr=subprocess.DEVNULL,
            )
            .decode("utf-8")
            .strip()
        )
        if value:
            env[env_var] = value
    except (subprocess.CalledProcessError, OSError):
        return


def start_local_mcp_server(
    port: int,
    *,
    env_overrides: dict[str, str] | None = None,
    log_dir: Path | None = None,
) -> LocalServer:
    """Start an HTTP-only MCP server (env overrides control mock/production behavior).

    Args:
        port: Port to listen on.
        env_overrides: Environment variables to override (e.g., MOCK_SERVICES_MODE).
        log_dir: Directory to write server logs. Defaults to evidence dir.

    Returns:
        LocalServer handle for managing the server process.
    """
    python_bin = PROJECT_ROOT / "venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    if env_overrides:
        env.update(env_overrides)

    # Some environments set WORLDAI_GOOGLE_APPLICATION_CREDENTIALS globally.
    # When present, the app requires an explicit dev-mode acknowledgement.
    if env.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") and not env.get(
        "WORLDAI_DEV_MODE"
    ):
        env["WORLDAI_DEV_MODE"] = "true"

    # Load provider keys from Secret Manager if possible.
    _load_secret(env, secret_name="gemini-api-key", env_var="GEMINI_API_KEY")
    _load_secret(env, secret_name="cerebras-api-key", env_var="CEREBRAS_API_KEY")
    _load_secret(env, secret_name="openrouter-api-key", env_var="OPENROUTER_API_KEY")

    log_root = log_dir or DEFAULT_EVIDENCE_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"local_mcp_{port}.log"
    log_f = open(log_path, "wb")  # noqa: SIM115

    proc = subprocess.Popen(
        [
            str(python_bin),
            "-m",
            "mvp_site.mcp_api",
            "--http-only",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )

    return LocalServer(
        proc=proc,
        base_url=f"http://127.0.0.1:{port}",
        log_path=log_path,
        _log_file=log_f,
    )
