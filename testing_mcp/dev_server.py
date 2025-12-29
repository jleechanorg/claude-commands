#!/usr/bin/env python3
"""
Centralized Development Server Detection for testing_mcp tests.

This module detects running servers and provides the correct BASE_URL.
It does NOT start servers - use run_local_server.sh for that.

Usage in tests:
    from testing_mcp.dev_server import ensure_server_running, get_base_url

    # At test start - checks for running server
    ensure_server_running()
    base_url = get_base_url()

Features:
- Detects running servers on common ports (8001, 8080, 8087, etc.)
- Worktree-specific port computation for isolation
- Falls back to common ports if worktree port not available
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import requests

# Configuration
DEFAULT_HOST = "localhost"
COMMON_PORTS = [8001, 8080, 8081, 8000]  # Common dev server ports to check
PORT_RANGE_START = 8001
PORT_RANGE_END = 8099

# Paths
PROJECT_ROOT = Path(__file__).parent.parent


def _get_repo_name() -> str:
    """Get the git repository name."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
        # Extract repo name from URL (handles both HTTPS and SSH)
        # e.g., "https://github.com/user/repo.git" -> "repo"
        # e.g., "git@github.com:user/repo.git" -> "repo"
        name = remote_url.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name
    except Exception:
        return PROJECT_ROOT.name


def _get_branch_name() -> str:
    """Get the current git branch name."""
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).strip()
    except Exception:
        return "main"


def _compute_port_for_worktree() -> int:
    """
    Compute a deterministic port based on repo name and branch name.

    This ensures:
    - Same repo+branch always gets the same port (across machines)
    - Different branches get different ports
    - Port is in range 8001-8099
    """
    repo_name = _get_repo_name()
    branch_name = _get_branch_name()
    identifier = f"{repo_name}:{branch_name}"

    hash_bytes = hashlib.md5(identifier.encode()).digest()
    hash_int = int.from_bytes(hash_bytes[:4], byteorder='big')
    return PORT_RANGE_START + (hash_int % (PORT_RANGE_END - PORT_RANGE_START + 1))


# Worktree-specific port
WORKTREE_PORT = _compute_port_for_worktree()


def is_server_healthy(port: int, host: str = DEFAULT_HOST, timeout: float = 2.0) -> bool:
    """Check if server is running and healthy on given port."""
    try:
        resp = requests.get(f"http://{host}:{port}/health", timeout=timeout)
        return resp.status_code == 200 and resp.json().get("status") == "healthy"
    except Exception:
        return False


def find_running_server() -> Optional[int]:
    """
    Find a running server, checking worktree port first, then common ports.

    Returns:
        Port number if found, None otherwise
    """
    # Check worktree-specific port first
    if is_server_healthy(WORKTREE_PORT):
        return WORKTREE_PORT

    # Check common ports
    for port in COMMON_PORTS:
        if port != WORKTREE_PORT and is_server_healthy(port):
            return port

    return None


def get_base_url(port: Optional[int] = None) -> str:
    """
    Get the base URL for the test server.

    Priority:
    1. BASE_URL environment variable
    2. Provided port parameter
    3. Detected running server
    4. Worktree-specific port (even if not running)
    """
    # Environment variable takes precedence
    if os.getenv("BASE_URL"):
        return os.getenv("BASE_URL")

    # Use provided port
    if port:
        return f"http://{DEFAULT_HOST}:{port}"

    # Try to find running server
    running_port = find_running_server()
    if running_port:
        return f"http://{DEFAULT_HOST}:{running_port}"

    # Default to worktree port
    return f"http://{DEFAULT_HOST}:{WORKTREE_PORT}"


def ensure_server_running(port: Optional[int] = None, check_code_changes: bool = True) -> int:
    """
    Ensure a server is running and accessible.

    This function does NOT start servers. If no server is found, it prints
    instructions to start one using run_local_server.sh.

    Args:
        port: Specific port to check (optional)
        check_code_changes: Ignored (kept for API compatibility)

    Returns:
        Port number of running server, or 0 if not found
    """
    # Check if BASE_URL points to external server
    base_url = os.getenv("BASE_URL", "")
    if base_url and "localhost" not in base_url and "127.0.0.1" not in base_url:
        print(f"ℹ️  Using external server: {base_url}")
        return 0

    # Check specific port if provided
    if port and is_server_healthy(port):
        print(f"✅ Server running on port {port}")
        return port

    # Find any running server
    running_port = find_running_server()
    if running_port:
        print(f"✅ Server running on port {running_port}")
        return running_port

    # No server found - print instructions
    print("⚠️  No running server detected")
    print(f"   Checked ports: {WORKTREE_PORT} (worktree), {COMMON_PORTS}")
    print("")
    print("   To start the server, run:")
    print("   ./run_local_server.sh")
    print("")
    print("   Or for API-only testing:")
    print(f"   source venv/bin/activate && gunicorn -w 1 -b 0.0.0.0:{WORKTREE_PORT} --reload mvp_site.main:app")
    print("")

    return 0


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Development server detection")
    parser.add_argument("action", choices=["status", "port", "url"], nargs="?", default="status")

    args = parser.parse_args()

    if args.action == "status":
        port = ensure_server_running()
        if port:
            print(f"\nBase URL: {get_base_url(port)}")
        else:
            sys.exit(1)
    elif args.action == "port":
        print(WORKTREE_PORT)
    elif args.action == "url":
        print(get_base_url())
