import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_unified_installer(product: str, extra_args=None):
    """Run the unified MCP installer for testing"""
    script_path = PROJECT_ROOT / "scripts" / "install_mcp_servers.sh"
    args = [str(script_path)]
    if extra_args:
        args.extend(extra_args)
    args.append(product)

    result = subprocess.run(
        args,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        check=False,
    )
    return result


def test_codex_installer_exits_cleanly():
    """Test that Codex installer runs in test mode without errors"""
    result = run_unified_installer("codex", ["--test"])
    assert result.returncode == 0
    assert "Codex MCP Server Installer" in result.stdout


def test_claude_installer_exits_cleanly():
    """Test that Claude installer runs in test mode without errors"""
    result = run_unified_installer("claude", ["--test"])
    assert result.returncode == 0
    assert "Claude MCP Server Installer" in result.stdout
    assert "requires bash 4.0" not in result.stdout
