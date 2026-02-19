import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

# Ensure repository root is importable
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import automation.jleechanorg_pr_automation.orchestrated_pr_runner as runner

def test_get_automation_user_from_env_actor(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTOR", "test-actor")
    monkeypatch.setenv("AUTOMATION_USERNAME", "other-user")
    assert runner.get_automation_user() == "test-actor"

def test_get_automation_user_from_env_automation_username(monkeypatch):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.setenv("AUTOMATION_USERNAME", "test-automation-user")
    assert runner.get_automation_user() == "test-automation-user"

def test_get_automation_user_from_gh_cli_success(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("AUTOMATION_USERNAME", raising=False)
    
    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        if cmd == ["gh", "api", "user", "--jq", ".login"]:
            return SimpleNamespace(returncode=0, stdout="gh-user\n")
        return SimpleNamespace(returncode=1, stdout="", stderr="")
        
    monkeypatch.setattr(subprocess, "run", fake_run)
    
    assert runner.get_automation_user() == "gh-user"
    captured = capsys.readouterr().out
    assert "Auto-detected automation user from gh CLI: gh-user" in captured

def test_get_automation_user_from_gh_cli_invalid_format(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("AUTOMATION_USERNAME", raising=False)
    
    def fake_run(cmd, capture_output=True, text=True, timeout=5, check=False):
        return SimpleNamespace(returncode=0, stdout="invalid user!\n")
        
    monkeypatch.setattr(subprocess, "run", fake_run)
    
    assert runner.get_automation_user() is None
    captured = capsys.readouterr().out
    assert "Invalid username format from gh CLI: 'invalid user!'" in captured

def test_get_automation_user_from_gh_cli_timeout(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("AUTOMATION_USERNAME", raising=False)
    
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], 5)
        
    monkeypatch.setattr(subprocess, "run", fake_run)
    
    assert runner.get_automation_user() is None
    captured = capsys.readouterr().out
    assert "Timeout while auto-detecting automation user from gh CLI" in captured

def test_get_automation_user_from_gh_cli_error(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("AUTOMATION_USERNAME", raising=False)
    
    def fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(1, args[0])
        
    monkeypatch.setattr(subprocess, "run", fake_run)
    
    assert runner.get_automation_user() is None
    captured = capsys.readouterr().out
    assert "gh CLI error while auto-detecting automation user" in captured

def test_get_automation_user_from_gh_cli_general_exception(monkeypatch, capsys):
    monkeypatch.delenv("GITHUB_ACTOR", raising=False)
    monkeypatch.delenv("AUTOMATION_USERNAME", raising=False)
    
    def fake_run(*args, **kwargs):
        raise RuntimeError("Something went wrong")
        
    monkeypatch.setattr(subprocess, "run", fake_run)
    
    assert runner.get_automation_user() is None
    captured = capsys.readouterr().out
    assert "Failed to auto-detect automation user: RuntimeError: Something went wrong" in captured
