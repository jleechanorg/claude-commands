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
# Use worldarchitect.ai venv if it exists (has dependencies), otherwise use local venv
WORLDARCH_VENV = Path("/Users/jleechan/projects/worldarchitect.ai/venv/bin/python")
# Server logs go to /tmp per evidence-standards.md
DEFAULT_LOG_DIR = Path("/tmp/mcp_server_logs")

# Default MCP server port and URL for testing
DEFAULT_MCP_PORT = 8081
DEFAULT_MCP_BASE_URL = f"http://localhost:{DEFAULT_MCP_PORT}"

# Evidence capture settings per evidence-standards.md
# Note: CAPTURE_RAW_LLM defaults to true in the server (llm_service.py)
# These overrides are for tests that need custom limits
DEFAULT_EVIDENCE_ENV = {
    "CAPTURE_RAW_LLM": "true",  # Server default, included for explicitness
    "CAPTURE_RAW_LLM_MAX_CHARS": "50000",  # Test override (server default: 20000)
    "CAPTURE_SYSTEM_INSTRUCTION_MAX_CHARS": "120000",
}


@dataclass
class LocalServer:
    """Handle for a locally-started MCP server process."""

    proc: subprocess.Popen[bytes]
    base_url: str
    log_path: Path
    env: dict[str, str] | None = None
    _log_file: Any | None = None

    @property
    def pid(self) -> int | None:
        """Return the server process PID when available."""
        return self.proc.pid if self.proc else None

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
                timeout=30,  # Prevent indefinite hang if gcloud is unresponsive
            )
            .decode("utf-8")
            .strip()
        )
        if value:
            env[env_var] = value
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        # Silent failure is intentional - secret loading is optional
        return


def start_local_mcp_server(
    port: int,
    *,
    env_overrides: dict[str, str] | None = None,
    log_dir: Path | None = None,
) -> LocalServer:
    """Start an HTTP-only MCP server (real services only).

    Uses shared production environment setup from scripts/setup_production_env.sh
    for consistency with run_local_server.sh.

    Args:
        port: Port to listen on.
        env_overrides: Environment variables to override (real mode enforced).
        log_dir: Directory to write server logs. Defaults to evidence dir.

    Returns:
        LocalServer handle for managing the server process.
    """
    # Prefer worldarchitect.ai venv (has dependencies), fallback to local venv, then sys.executable
    python_bin = None
    if WORLDARCH_VENV.exists():
        python_bin = WORLDARCH_VENV
    elif (PROJECT_ROOT / "venv" / "bin" / "python").exists():
        python_bin = PROJECT_ROOT / "venv" / "bin" / "python"
    else:
        python_bin = Path(sys.executable)

    env = dict(os.environ)
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    # Apply default evidence capture settings (can be overridden)
    for key, value in DEFAULT_EVIDENCE_ENV.items():
        env.setdefault(key, value)

    if env_overrides:
        env.update(env_overrides)

    # Use shared production environment setup (same as run_local_server.sh)
    # Replicate logic from scripts/setup_production_env.sh for consistency
    # This ensures test servers use the same environment as development servers
    
    # Clear any testing/mock environment variables (same as setup_production_env.sh)
    # Note: Don't unset TESTING - it may be needed for some server initialization
    env.pop("MOCK_SERVICES_MODE", None)
    env.pop("MOCK_MODE", None)
    
    # Ensure production mode is explicit (same as setup_production_env.sh)
    env["PRODUCTION_MODE"] = "true"
    
    # Enforce real mode: mock services are never allowed
    env["MOCK_SERVICES_MODE"] = "false"
    # Don't set TESTING=false - let server handle it (may break initialization)

    # Some environments set WORLDAI_GOOGLE_APPLICATION_CREDENTIALS globally.
    # When present, the app requires an explicit dev-mode acknowledgement.
    if env.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS") and not env.get(
        "WORLDAI_DEV_MODE"
    ):
        env["WORLDAI_DEV_MODE"] = "true"

    # Load provider keys from Secret Manager if possible (fallback if not in env)
    _load_secret(env, secret_name="gemini-api-key", env_var="GEMINI_API_KEY")
    _load_secret(env, secret_name="cerebras-api-key", env_var="CEREBRAS_API_KEY")
    _load_secret(env, secret_name="openrouter-api-key", env_var="OPENROUTER_API_KEY")

    log_root = log_dir or DEFAULT_LOG_DIR
    log_root.mkdir(parents=True, exist_ok=True)
    log_path = log_root / f"local_mcp_{port}.log"
    log_f = open(log_path, "wb")  # noqa: SIM115

    # Use same command pattern as start_mcp_production.sh but with --http-only for tests
    proc = subprocess.Popen(
        [
            str(python_bin),
            "-m",
            "mvp_site.mcp_api",
            "--http-only",  # Tests use HTTP-only, not dual transport
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
        env=env,
        _log_file=log_f,
    )
