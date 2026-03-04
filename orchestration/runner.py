#!/usr/bin/env python3
"""
ai_orch - AI CLI runner: passthrough and async tmux modes.

  ai_orch "task"                         # run directly, stream output
  ai_orch --agent-cli codex "task"       # use codex
  ai_orch --async "task"                 # detached tmux, return immediately
  ai_orch --async --resume "task"        # resume existing session for this dir
  ai_orch --async --worktree "task"      # create git worktree, then async
"""

# ruff: noqa: E402
import hashlib
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import argparse
import json
import shlex
import shutil
import subprocess
import time
from importlib import metadata as importlib_metadata
from typing import Optional

from orchestration.cli_args import add_agent_cli_and_model_arguments
from orchestration.cli_args import add_live_cli_arguments
from orchestration.cli_args import add_named_session_argument
from orchestration.cli_args import add_task_argument
from orchestration.live_mode import LiveMode
from orchestration.task_dispatcher import apply_minimax_auth_env
from orchestration.task_dispatcher import CLI_PROFILES
from orchestration.task_dispatcher import GEMINI_MODEL


class AsyncRunner:
    """Spawn detached tmux sessions; track by CWD+CLI for resume."""

    SESSIONS_FILE = os.path.expanduser("~/.ai_orch_sessions.json")

    def _load_sessions(self) -> dict:
        try:
            with open(self.SESSIONS_FILE) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save_sessions(self, sessions: dict) -> None:
        with open(self.SESSIONS_FILE, "w") as f:
            json.dump(sessions, f, indent=2)

    def session_alive(self, session_name: str) -> bool:
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                shell=False, capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def find_existing_session(self, cwd: str, cli: str) -> Optional[str]:
        session = self._load_sessions().get(cwd, {}).get(cli)
        if session and self.session_alive(session):
            return session
        return None

    def _register_session(self, cwd: str, cli: str, session_name: str) -> None:
        sessions = self._load_sessions()
        sessions.setdefault(cwd, {})[cli] = session_name
        self._save_sessions(sessions)

    def _make_session_name(self, cli: str, cwd: str) -> str:
        cwd_hash = hashlib.md5(cwd.encode()).hexdigest()[:6]
        return f"ai-{cli}-{cwd_hash}"

    def _build_shell_cmd(self, cli: str, model: Optional[str], task: str, resume: bool) -> str:
        """Return a shell-safe command string for tmux to execute."""
        profile = CLI_PROFILES[cli]
        binary = shlex.quote(profile["binary"])

        if cli == "claude":
            parts = [binary]
            if model:
                parts += ["--model", shlex.quote(model)]
            if resume:
                parts.append("--continue")
            parts += ["-p", shlex.quote(task)]
            return " ".join(parts)

        if cli == "codex":
            parts = [binary, "exec", "--yolo", "--skip-git-repo-check"]
            if model:
                parts += ["--model", shlex.quote(model)]
            return f"printf '%s' {shlex.quote(task)} | {' '.join(parts)}"

        if cli == "gemini":
            m = shlex.quote(model or GEMINI_MODEL)
            return f"printf '%s' {shlex.quote(task)} | {binary} -m {m} --yolo"

        if cli == "minimax":
            # MiniMax uses claude binary with environment variable overrides
            env_cmds = []
            # Unset conflicting environment variables
            for var in profile.get("env_unset", []):
                env_cmds.append(f"unset {var}")
            # Set MiniMax-specific environment variables
            for key, value in profile.get("env_set", {}).items():
                env_cmds.append(f"export {key}={shlex.quote(str(value))}")
            # Apply MiniMax authentication
            auth_env = apply_minimax_auth_env({})
            for key, value in auth_env.items():
                env_cmds.append(f"export {key}={shlex.quote(str(value))}")
            
            # Build claude command (minimax uses claude binary)
            parts = ["claude"]
            if model:
                parts += ["--model", shlex.quote(model)]
            if resume:
                parts.append("--continue")
            parts += ["-p", shlex.quote(task)]
            
            # Combine environment setup and command
            return "; ".join(env_cmds + [" ".join(parts)])

        # generic fallback
        parts = [binary]
        if model:
            parts += ["--model", shlex.quote(model)]
        parts.append(shlex.quote(task))
        return " ".join(parts)

    def create_worktree(self, cwd: str) -> Optional[str]:
        branch = f"ai-orch-{int(time.time()) % 100000}"
        worktree_path = f"/tmp/ai-orch-worktrees/{branch}"
        os.makedirs("/tmp/ai-orch-worktrees", exist_ok=True)
        try:
            subprocess.run(
                ["git", "worktree", "add", "-b", branch, worktree_path],
                shell=False, check=True, cwd=cwd,
                capture_output=True, timeout=30,
            )
            print(f"🧩 Worktree: {worktree_path} (branch: {branch})")
            return worktree_path
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode() if e.stderr else str(e)
            print(f"❌ Failed to create worktree: {stderr}")
            return None

    def run(
        self,
        task: str,
        cli: str,
        model: Optional[str] = None,
        resume: bool = False,
        worktree: bool = False,
        cwd: Optional[str] = None,
    ) -> int:
        if cwd is None:
            cwd = os.getcwd()

        profile = CLI_PROFILES.get(cli)
        if not profile:
            print(f"❌ Unknown CLI: {cli}. Valid: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        if not shutil.which("tmux"):
            print("❌ tmux not found. Install: brew install tmux")
            return 1

        if not shutil.which(profile["binary"]):
            print(f"❌ {profile['binary']} not found in PATH")
            return 1

        work_dir = cwd
        if worktree:
            work_dir = self.create_worktree(cwd)
            if work_dir is None:
                return 1

        existing = self.find_existing_session(cwd, cli) if resume else None
        shell_cmd = self._build_shell_cmd(cli, model, task, resume=(existing is not None))

        if existing:
            try:
                subprocess.run(
                    ["tmux", "send-keys", "-t", existing, shell_cmd, "Enter"],
                    shell=False, check=True, timeout=10,
                )
                print(f"📨 Sent to existing session: {existing}")
                print(f"📺 Attach: tmux attach -t {existing}")
                return 0
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Could not send to {existing}: {e}. Creating new session.")

        session_name = self._make_session_name(cli, cwd)
        if self.session_alive(session_name):
            session_name = f"{session_name}-{int(time.time()) % 10000}"

        try:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session_name, "-c", work_dir, shell_cmd],
                shell=False, check=True, timeout=15,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start session: {e}")
            return 1

        self._register_session(cwd, cli, session_name)
        print(f"🚀 Async session: {session_name}")
        print(f"📺 Attach: tmux attach -t {session_name}")
        print(f"💓 Alive?: tmux has-session -t {session_name} && echo alive")
        return 0


def _run_passthrough(task: str, cli_name: str, model: Optional[str], resume: bool = False) -> int:
    """Invoke CLI directly, stream output to stdout."""
    profile = CLI_PROFILES.get(cli_name)
    if not profile:
        print(f"❌ Unknown CLI: {cli_name}. Valid: {', '.join(sorted(CLI_PROFILES.keys()))}")
        return 2

    if not shutil.which(profile["binary"]):
        print(f"❌ {profile['binary']} not found in PATH")
        return 1

    binary = profile["binary"]
    try:
        if cli_name == "claude":
            cmd = [binary]
            if model:
                cmd.extend(["--model", model])
            if resume:
                cmd.append("--continue")
            cmd.extend(["-p", task])
            return subprocess.run(cmd, shell=False).returncode

        if cli_name == "codex":
            cmd = [binary, "exec", "--yolo", "--skip-git-repo-check"]
            if model:
                cmd.extend(["--model", model])
            return subprocess.run(cmd, input=task, text=True, shell=False).returncode

        if cli_name == "gemini":
            cmd = [binary, "-m", model or GEMINI_MODEL, "--yolo"]
            return subprocess.run(cmd, input=task, text=True, shell=False).returncode

        if cli_name == "minimax":
            cmd = ["claude"]
            if model is not None:
                cmd.extend(["--model", model])
            if resume:
                cmd.append("--continue")
            cmd.extend(["-p", task])
            env = dict(os.environ)
            for var in profile.get("env_unset", []):
                env.pop(var, None)
            env.update({k: str(v) for k, v in profile.get("env_set", {}).items()})
            env = apply_minimax_auth_env(env)
            return subprocess.run(cmd, shell=False, env=env).returncode

        # generic fallback
        cmd = [binary]
        if model:
            cmd.extend(["--model", model])
        cmd.append(task)
        return subprocess.run(cmd, shell=False).returncode

    except KeyboardInterrupt:
        return 130


def main() -> int:
    def _get_version() -> str:
        try:
            return importlib_metadata.version("jleechanorg-orchestration")
        except importlib_metadata.PackageNotFoundError:
            return "unknown"

    parser = argparse.ArgumentParser(
        description="ai_orch - run AI CLI tasks (passthrough or async tmux)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai_orch "explain this code"                       # passthrough (default)
  ai_orch --agent-cli codex "print 1"               # codex passthrough
  ai_orch --async "implement feature X"             # detached tmux session
  ai_orch --async --resume "add error handling"     # resume existing session
  ai_orch --async --worktree "refactor auth"        # new git worktree + tmux
  ai_orch live --cli codex                          # interactive session
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_get_version()}")

    commands = {"run", "live", "list", "attach", "kill"}
    live_only_flags = {"--cli", "--name", "--dir", "--detached"}
    argv = sys.argv[1:]
    if argv and not argv[0].startswith("-") and argv[0] not in commands:
        argv = ["run"] + argv
    elif argv and argv[0].startswith("-") and argv[0] not in {"--version", "--help", "-h"}:
        if any(arg in live_only_flags for arg in argv):
            argv = ["live"] + argv
        else:
            argv = ["run"] + argv

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    run_parser = subparsers.add_parser("run", help="Run a task (passthrough or async)")
    add_task_argument(run_parser, help_text="Task to send to the CLI")
    add_agent_cli_and_model_arguments(run_parser, model_default=None)
    run_parser.add_argument(
        "--async", dest="async_mode", action="store_true", default=False,
        help="Spawn a detached tmux session and return immediately",
    )
    run_parser.add_argument(
        "--resume", "--continue", dest="resume", action="store_true", default=False,
        help="Resume existing session for this directory (or add --continue for claude)",
    )
    run_parser.add_argument(
        "--worktree", dest="worktree", action="store_true", default=False,
        help="Create a git worktree before running (only applies with --async)",
    )

    live_parser = subparsers.add_parser("live", help="Start interactive AI CLI session in tmux")
    add_live_cli_arguments(live_parser, include_model=True, include_detached=True)

    subparsers.add_parser("list", help="List active tmux sessions")
    attach_parser = subparsers.add_parser("attach", help="Attach to existing session")
    add_named_session_argument(attach_parser, help_text="Session name to attach to")
    kill_parser = subparsers.add_parser("kill", help="Kill a session")
    add_named_session_argument(kill_parser, help_text="Session name to kill")

    if argv in (["--help"], ["-h"]):
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.command == "run":
        cli = (args.agent_cli or "claude").strip().lower()
        if cli not in CLI_PROFILES:
            print(f"❌ Unknown CLI: {cli}. Valid: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2
        task = " ".join(args.task).strip()
        if not task:
            print("❌ Task is required.")
            return 2
        if args.worktree and not args.async_mode:
            print("❌ --worktree requires --async.")
            return 2

        if args.async_mode:
            return AsyncRunner().run(
                task=task, cli=cli, model=args.model,
                resume=args.resume, worktree=args.worktree,
            )
        return _run_passthrough(task, cli, args.model, resume=args.resume)

    if args.command == "live":
        live_mode = LiveMode(cli_name=args.cli)
        live_mode.start_interactive_session(
            session_name=args.name, working_dir=args.dir, model=args.model, attach=not args.detached
        )
        return 0

    if args.command == "list":
        all_sessions = []
        for cli_name in CLI_PROFILES.keys():
            live_mode = LiveMode(cli_name=cli_name)
            all_sessions.extend(live_mode.list_sessions())

        if all_sessions:
            print("📋 Active AI sessions:")
            for session in all_sessions:
                print(f"   - {session}")
        else:
            print("📋 No active AI sessions.")
        return 0

    if args.command == "attach":
        session_name = args.session
        found = False

        for cli_name in CLI_PROFILES.keys():
            live_mode = LiveMode(cli_name=cli_name)
            normalized_name = (
                session_name
                if session_name.startswith(live_mode.session_prefix)
                else f"{live_mode.session_prefix}-{session_name}"
            )
            if live_mode._session_exists(normalized_name):
                live_mode.attach_to_session(session_name)
                found = True
                break

        if not found:
            print(f"❌ Error: Session '{session_name}' not found.")
            print("\n📋 Available sessions:")
            for cli_name in CLI_PROFILES.keys():
                live_mode = LiveMode(cli_name=cli_name)
                sessions = live_mode.list_sessions()
                for s in sessions:
                    print(f"   - {s}")
            return 1
        return 0

    if args.command == "kill":
        session_name = args.session
        found = False

        for cli_name in CLI_PROFILES.keys():
            live_mode = LiveMode(cli_name=cli_name)
            normalized_name = (
                session_name
                if session_name.startswith(live_mode.session_prefix)
                else f"{live_mode.session_prefix}-{session_name}"
            )
            if live_mode._session_exists(normalized_name):
                live_mode.kill_session(session_name)
                found = True
                break

        if not found:
            print(f"❌ Error: Session '{session_name}' not found.")
            return 1
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
