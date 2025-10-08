import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_launcher(script_name: str):
    script_path = PROJECT_ROOT / script_name
    result = subprocess.run(
        [str(script_path), "--test"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result


def test_codex_launcher_exits_cleanly():
    result = run_launcher("codex_mcp.sh")
    assert result.returncode == 0
    assert "📝 Logging to: /tmp/codex_mcp" in result.stdout


def test_claude_launcher_reexecs_to_newer_bash():
    result = run_launcher("claude_mcp.sh")
    assert result.returncode == 0
    assert "📝 Logging to: /tmp/claude_mcp" in result.stdout
    assert "requires bash 4.0" not in result.stdout
