"""Run the unit + (optional) live integration tests for cross-cli Stop hook."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

CMD = [
    sys.executable,
    "-m",
    "unittest",
    "-v",
    "tests.test_cross_cli_status",
]
if os.environ.get("CROSS_CLI_LIVE") == "1":
    CMD.append("tests.integration.test_cross_cli_live_tmux")

print("$", " ".join(CMD))
res = subprocess.run(CMD, cwd=str(REPO_ROOT), env=os.environ.copy(), timeout=600)
sys.exit(res.returncode)
