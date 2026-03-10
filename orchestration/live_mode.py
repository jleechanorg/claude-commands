#!/usr/bin/env python3
"""
ai_orch - AI CLI runner with passthrough and async tmux modes.

Modes:
  passthrough (default): run CLI directly, stream output
  async (--async):       spawn detached tmux session, return immediately
"""

# ruff: noqa: E402

# Allow direct script execution - add parent directory to sys.path
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

# Use absolute imports with package name for __main__ compatibility
from orchestration.cli_args import add_agent_cli_and_model_arguments
from orchestration.cli_args import add_live_cli_arguments
from orchestration.cli_args import add_named_session_argument
from orchestration.cli_args import add_task_argument
from orchestration.task_dispatcher import apply_minimax_auth_env
from orchestration.task_dispatcher import CLI_PROFILES
from orchestration.task_dispatcher import GEMINI_MODEL


class LiveMode:
    """Manages interactive tmux sessions for AI CLI tools."""

    def __init__(self, cli_name: str = "claude", session_prefix: str = "ai-live"):
        """
        Initialize live mode manager.

        Args:
            cli_name: Name of CLI to use (claude or codex)
            session_prefix: Prefix for tmux session names
        """
        self.cli_name = cli_name
        self.session_prefix = session_prefix
        self.cli_profile = CLI_PROFILES.get(cli_name)

        if not self.cli_profile:
            raise ValueError(f"Unknown CLI: {cli_name}. Available: {list(CLI_PROFILES.keys())}")

    def _check_dependencies(self) -> bool:
        """Check if required binaries are available."""
        # Check tmux (cross-platform using shutil.which)
        if not shutil.which("tmux"):
            print("❌ Error: tmux not found. Please install tmux:")
            print("   Ubuntu/Debian: sudo apt-get install tmux")
            print("   macOS: brew install tmux")
            return False

        # Check CLI binary
        cli_binary = self.cli_profile["binary"]
        if not shutil.which(cli_binary):
            print(f"❌ Error: {cli_binary} CLI not found.")
            print(f"   Please install {self.cli_profile['display_name']} CLI first.")
            return False

        return True

    def _generate_session_name(self) -> str:
        """Generate unique session name."""
        timestamp = int(time.time() * 1000) % 100000000  # 8 digits
        return f"{self.session_prefix}-{self.cli_name}-{timestamp}"

    def _session_exists(self, session_name: str) -> bool:
        """Check if tmux session exists."""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name], shell=False, capture_output=True, timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            # If tmux hangs, assume session doesn't exist
            return False

    def list_sessions(self) -> list[str]:
        """List all active ai-live sessions."""
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                shell=False,
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                return []

            # Handle empty stdout (no sessions)
            output = result.stdout.strip()
            if not output:
                return []

            sessions = output.split("\n")
            return [s for s in sessions if s.startswith(self.session_prefix)]
        except subprocess.TimeoutExpired:
            # If tmux hangs, return empty list
            return []

    def start_interactive_session(
        self,
        session_name: Optional[str] = None,
        working_dir: Optional[str] = None,
        model: Optional[str] = None,
        attach: bool = True,
    ) -> str:
        """
        Start an interactive tmux session with the AI CLI.

        Args:
            session_name: Custom session name (auto-generated if None)
            working_dir: Working directory for the session (current dir if None)
            model: Model to use (default from CLI profile if None)
            attach: Whether to attach to session immediately

        Returns:
            Session name
        """
        if not self._check_dependencies():
            sys.exit(1)

        # Generate or validate session name
        if session_name is None:
            session_name = self._generate_session_name()
        elif not session_name.startswith(self.session_prefix):
            session_name = f"{self.session_prefix}-{session_name}"

        # Check if session already exists
        if self._session_exists(session_name):
            print(f"📌 Session '{session_name}' already exists.")
            if attach:
                print("🔗 Attaching to existing session...")
                self.attach_to_session(session_name)
            else:
                print(f"   Use 'ai_orch attach {session_name}' to attach.")
            return session_name

        # Set working directory
        if working_dir is None:
            working_dir = os.getcwd()
        working_dir = os.path.abspath(os.path.expanduser(working_dir))

        # Build CLI command (properly escaped to prevent shell injection)
        cli_binary = self.cli_profile["binary"]

        if self.cli_name == "claude":
            # Claude interactive mode
            cmd_parts = [cli_binary]
            if model:
                cmd_parts.extend(["--model", model])
            else:
                cmd_parts.extend(["--model", "sonnet"])
            # Interactive mode - no prompt file
            # Use shlex.quote to prevent shell injection via model parameter
            cmd = " ".join(shlex.quote(part) for part in cmd_parts)
        elif self.cli_name == "codex":
            # Codex interactive mode
            cmd = f"{shlex.quote(cli_binary)} exec"
        else:
            # Generic CLI
            cmd = shlex.quote(cli_binary)

        # Create tmux session
        print(f"🚀 Starting {self.cli_profile['display_name']} in tmux session: {session_name}")
        print(f"📁 Working directory: {working_dir}")
        print(f"💬 Command: {cmd}")
        print()
        print("📝 Tmux commands:")
        print("   - Detach: Ctrl+b, then d")
        print("   - Reattach: ai_orch attach <session-name>")
        print("   - List sessions: ai_orch list")
        print("   - Kill session: tmux kill-session -t <session-name>")
        print()

        try:
            # Create new tmux session
            # NOTE: We pass the command as a shell-quoted string to tmux.
            # Flow: subprocess (shell=False) → tmux → tmux's shell → our command
            # - shell=False: subprocess executes tmux directly (no shell for tmux)
            # - tmux executes our command via $SHELL -c "command"
            # - shlex.quote() ensures the command is safe for shell execution
            # This is the correct and secure way to pass commands to tmux.
            tmux_cmd = ["tmux", "new-session", "-s", session_name, "-c", working_dir]

            if not attach:
                tmux_cmd.insert(2, "-d")  # Detached mode

            # Add the shell-quoted command string for tmux to execute
            tmux_cmd.append(cmd)

            # Add timeout only for detached mode (attached mode blocks until user exits)
            run_kwargs = {"shell": False, "check": True}
            if not attach:
                run_kwargs["timeout"] = 30  # Detached mode should return quickly

            subprocess.run(tmux_cmd, **run_kwargs)

            if not attach:
                print(f"✅ Session '{session_name}' created in detached mode.")
                print(f"   Attach with: ai_orch attach {session_name}")

            return session_name

        except subprocess.TimeoutExpired:
            print("❌ Error: tmux session creation timed out after 30 seconds.")
            print("   This may indicate tmux is unresponsive. Please check tmux status.")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error creating tmux session: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 Session creation cancelled.")
            sys.exit(0)

    def attach_to_session(self, session_name: str):
        """Attach to an existing tmux session."""
        if not session_name.startswith(self.session_prefix):
            session_name = f"{self.session_prefix}-{session_name}"

        if not self._session_exists(session_name):
            print(f"❌ Error: Session '{session_name}' does not exist.")
            print("\n📋 Available sessions:")
            sessions = self.list_sessions()
            if sessions:
                for s in sessions:
                    print(f"   - {s}")
            else:
                print("   (no active sessions)")
            sys.exit(1)

        print(f"🔗 Attaching to session: {session_name}")
        print("   (Detach with: Ctrl+b, then d)")

        try:
            subprocess.run(["tmux", "attach-session", "-t", session_name], shell=False, check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error attaching to session: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            print("\n👋 Detached from session.")

    def kill_session(self, session_name: str):
        """Kill a tmux session."""
        if not session_name.startswith(self.session_prefix):
            session_name = f"{self.session_prefix}-{session_name}"

        if not self._session_exists(session_name):
            print(f"❌ Error: Session '{session_name}' does not exist.")
            sys.exit(1)

        try:
            subprocess.run(["tmux", "kill-session", "-t", session_name], shell=False, check=True, timeout=10)
            print(f"✅ Session '{session_name}' killed.")
        except subprocess.TimeoutExpired:
            print("❌ Error: Killing session timed out after 10 seconds.")
            print("   The session may still be running. Please check tmux status.")
            sys.exit(1)
        except subprocess.CalledProcessError as e:
            print(f"❌ Error killing session: {e}")
            sys.exit(1)


class AsyncRunner:
    """Spawn detached tmux sessions for CLI tasks; track by CWD for resume."""

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
        """Check if a tmux session exists."""
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", session_name],
                shell=False, capture_output=True, timeout=5,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def find_existing_session(self, cwd: str, cli: str) -> Optional[str]:
        """Return session name if one is alive for this cwd+cli, else None."""
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
        """Return a shell command string suitable for tmux to execute."""
        profile = CLI_PROFILES[cli]
        binary = shlex.quote(profile["binary"])

        if cli == "claude":
            parts = [binary]
            if model:
                parts += ["--model", shlex.quote(model)]
            else:
                parts += ["--model", "sonnet"]
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

        # generic fallback: task as positional arg
        parts = [binary]
        if model:
            parts += ["--model", shlex.quote(model)]
        parts.append(shlex.quote(task))
        return " ".join(parts)

    def create_worktree(self, cwd: str) -> Optional[str]:
        """Create a git worktree under /tmp and return its path, or None on failure."""
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
        """Spawn a detached tmux session and return immediately."""
        if cwd is None:
            cwd = os.getcwd()

        profile = CLI_PROFILES.get(cli)
        if not profile:
            print(f"❌ Unknown CLI: {cli}. Valid: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        if not shutil.which("tmux"):
            print("❌ tmux not found. Install with: brew install tmux")
            return 1

        binary = profile["binary"]
        if not shutil.which(binary):
            print(f"❌ {binary} not found in PATH")
            return 1

        work_dir = cwd
        if worktree:
            work_dir = self.create_worktree(cwd)
            if work_dir is None:
                return 1

        # Find or create session name
        session_name = self._make_session_name(cli, cwd)
        existing = self.find_existing_session(cwd, cli) if resume else None

        shell_cmd = self._build_shell_cmd(cli, model, task, resume=(existing is not None))

        if existing:
            # Resume: send task to the live session
            try:
                subprocess.run(
                    ["tmux", "send-keys", "-t", existing, shell_cmd, "Enter"],
                    shell=False, check=True, timeout=10,
                )
                print(f"📨 Sent to existing session: {existing}")
                print(f"📺 Attach: tmux attach -t {existing}")
                return 0
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Could not send to session {existing}: {e}. Creating new session.")

        # Unique name if already taken
        if self.session_alive(session_name):
            session_name = f"{session_name}-{int(time.time()) % 10000}"

        try:
            subprocess.run(
                ["tmux", "new-session", "-d", "-s", session_name, "-c", work_dir, shell_cmd],
                shell=False, check=True, timeout=15,
            )
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start tmux session: {e}")
            return 1

        self._register_session(cwd, cli, session_name)
        print(f"🚀 Async session: {session_name}")
        print(f"📺 Attach: tmux attach -t {session_name}")
        print(f"💓 Alive?: tmux has-session -t {session_name} && echo alive")
        return 0


def main():
    """Main CLI entry point."""

    def _get_version() -> str:
        package_name = "jleechanorg-orchestration"
        try:
            return importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            return "unknown"

    def _run_passthrough(task: str, cli_name: str, model: Optional[str], resume: bool = False) -> int:
        """Invoke the CLI directly and stream output to stdout."""
        profile = CLI_PROFILES.get(cli_name)
        if not profile:
            print(f"❌ Unknown CLI: {cli_name}. Valid: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        binary = profile["binary"]
        if not shutil.which(binary):
            print(f"❌ {binary} not found in PATH")
            return 1

        try:
            if cli_name == "claude":
                cmd = [binary]
                if model:
                    cmd.extend(["--model", model])
                else:
                    cmd.extend(["--model", "sonnet"])
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

            # Generic fallback
            cmd = [binary]
            if model:
                cmd.extend(["--model", model])
            cmd.append(task)
            return subprocess.run(cmd, shell=False).returncode

        except KeyboardInterrupt:
            return 130

    def _run(args) -> int:
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
                task=task,
                cli=cli,
                model=args.model,
                resume=args.resume,
                worktree=args.worktree,
            )

        return _run_passthrough(task, cli, args.model, resume=args.resume)

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

    # run command
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

    # live command
    live_parser = subparsers.add_parser("live", help="Start interactive AI CLI session in tmux")
    add_live_cli_arguments(live_parser, include_model=True, include_detached=True)

    # list/attach/kill commands
    subparsers.add_parser("list", help="List active tmux sessions")
    attach_parser = subparsers.add_parser("attach", help="Attach to existing session")
    add_named_session_argument(attach_parser, help_text="Session name to attach to")
    kill_parser = subparsers.add_parser("kill", help="Kill a session")
    add_named_session_argument(kill_parser, help_text="Session name to kill")

    if argv == ["--help"] or argv == ["-h"]:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    if args.command == "run":
        return _run(args)

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
