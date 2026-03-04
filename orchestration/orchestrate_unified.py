#!/usr/bin/env python3
"""
orchestrate_unified - stub retained for backwards compatibility with tests.

The orchestration logic has moved to runner.py (passthrough + AsyncRunner).
"""

import os
import re
import subprocess
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from orchestration.task_dispatcher import CLI_PROFILES, TaskDispatcher  # noqa: F401


def main() -> int:
    """Stub main - orchestration entry point moved to runner.main()."""
    print("Use 'ai_orch' (runner) for passthrough or async modes.", file=sys.stderr)
    return 1


class UnifiedOrchestration:
    """Stub - kept so existing imports don't break. No longer used by ai_orch."""

    def _check_dependencies(self) -> bool:
        """Minimal dependency check for test compatibility."""
        for cmd in ("tmux", "git", "gh"):
            try:
                r = subprocess.run(["which", cmd], shell=False, check=False, capture_output=True, timeout=5)
                if r.returncode != 0:
                    return False
            except Exception:
                return False
        return True

    def orchestrate(self, task_description: str, options: dict = None) -> int:
        if not self._check_dependencies():
            return 0
        raise NotImplementedError(
            "UnifiedOrchestration.orchestrate() has been removed. "
            "Use 'ai_orch' (passthrough) or 'ai_orch --async' instead."
        )

    @staticmethod
    def _is_safe_branch_name(branch_name: str) -> bool:
        """Validate branch name against safe pattern. Retained for test compatibility."""
        return bool(re.match(r"^[A-Za-z0-9._/-]+$", branch_name))
