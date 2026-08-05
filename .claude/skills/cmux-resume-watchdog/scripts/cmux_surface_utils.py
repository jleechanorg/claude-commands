"""Shared cmux surface enumeration utility.

Both the cmux-codex-autoapprove daemon and the cmux-resume-watchdog use this
to enumerate terminal surfaces via a single ``cmux rpc debug.terminals`` call
(one socket round-trip, ~0.3-0.5s for 85 surfaces) instead of the old N+M
pattern (list-workspaces -> per-workspace list-panes -> per-pane
list-pane-surfaces = dozens of subprocess spawns that saturated cmux's IPC
socket and caused periodic UI freezes).

Fails open on any error — callers must never block on enumeration failure.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections.abc import Iterator


def debug_terminals(timeout: int = 10, socket_path: str | None = None) -> list[dict]:
    """Return the raw terminal list from ``cmux rpc debug.terminals``.

    Returns an empty list on any error (never raises).
    """
    try:
        env = dict(os.environ)
        if socket_path:
            env["CMUX_SOCKET_PATH"] = socket_path
            env["CMUX_SOCKET"] = socket_path
        proc = subprocess.run(
            ["cmux", "rpc", "debug.terminals"],
            capture_output=True, text=True, timeout=timeout, env=env,
        )
        if proc.returncode != 0:
            return []
        data = json.loads(proc.stdout)
        terms = data.get("terminals", data) if isinstance(data, dict) else data
        return terms if isinstance(terms, list) else []
    except Exception:
        return []


def iter_terminal_surfaces(
    timeout: int = 10,
    skip_dead_dirs: bool = True,
    skip_teardown: bool = True,
    socket_path: str | None = None,
) -> Iterator[tuple[str, str, str]]:
    """Yield (workspace_ref, surface_ref, title) for every live terminal surface.

    Uses one ``cmux rpc debug.terminals`` call (single socket round-trip).
    Optionally filters out surfaces whose working directory no longer exists
    on disk (orphaned worktrees) and surfaces with teardown_requested.

    Yields nothing on any error — never blocks the caller.
    """
    terms = debug_terminals(timeout=timeout, socket_path=socket_path)
    for term in terms:
        if skip_teardown and term.get("teardown_requested"):
            continue
        cwd = term.get("current_directory") or term.get("requested_working_directory")
        if skip_dead_dirs and cwd and not os.path.isdir(cwd):
            continue
        ws_ref = term.get("workspace_ref", "")
        surface_ref = term.get("surface_ref", "")
        title = term.get("surface_title") or term.get("title") or ""
        if ws_ref and surface_ref:
            yield ws_ref, surface_ref, title


def dead_directory_surface_refs(timeout: int = 10, socket_path: str | None = None) -> set[str]:
    """Return surface_refs whose working directory no longer exists.

    Convenience wrapper for callers that only need the dead-dir filter
    (mirrors the original ``dead_directory_surfaces()`` in the auto-approve
    daemon).  Fails open (returns empty set) on any error.
    """
    dead: set[str] = set()
    for term in debug_terminals(timeout=timeout, socket_path=socket_path):
        cwd = term.get("current_directory") or term.get("requested_working_directory")
        surface_ref = term.get("surface_ref")
        if cwd and surface_ref and not os.path.isdir(cwd):
            dead.add(surface_ref)
    return dead
