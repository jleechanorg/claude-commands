#!/usr/bin/env python3
"""Launch the MCP server in stdio-only mode.

This wrapper resolves the project root so it works from both the repository's
`.claude/scripts` directory and exported copies under `~/.claude/scripts`.
"""
from __future__ import annotations

import os
import sys


def resolve_project_root(script_dir: str) -> str | None:
    """Attempt to locate the project root containing mcp_api.py."""

    # First, honour explicit overrides
    env_root = os.environ.get("WORLDARCHITECT_PROJECT_ROOT")
    if env_root:
        candidate = os.path.join(env_root, "mvp_site", "mcp_api.py")
        if os.path.isfile(candidate):
            return env_root

    # Walk up the directory tree looking for the repo markers
    search_dir = script_dir
    while True:
        parent = os.path.dirname(search_dir)
        if parent == search_dir:
            break
        mcp_path = os.path.join(parent, "mvp_site", "mcp_api.py")
        if os.path.isfile(mcp_path):
            return parent
        search_dir = parent

    return None


def find_mcp_server(project_root: str) -> str | None:
    """Return the first existing MCP server path under the project root."""

    candidates = [
        os.path.join(project_root, "mvp_site", "mcp_api.py"),
        os.path.join(project_root, "src", "mcp_api.py"),
        os.path.join(project_root, "mcp_api.py"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return None


def main() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = resolve_project_root(script_dir)
    if not project_root:
        print(
            "ERROR: Unable to locate project root containing mvp_site/mcp_api.py. "
            "Set WORLDARCHITECT_PROJECT_ROOT to override.",
            file=sys.stderr,
        )
        sys.exit(1)

    mcp_server_path = find_mcp_server(project_root)
    if not mcp_server_path:
        print(
            f"ERROR: MCP server not found under {project_root}. Expected mvp_site/mcp_api.py",
            file=sys.stderr,
        )
        sys.exit(1)

    os.execv(sys.executable, [sys.executable, mcp_server_path, "--stdio"])


if __name__ == "__main__":
    main()
