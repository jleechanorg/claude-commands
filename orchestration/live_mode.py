#!/usr/bin/env python3
"""
tmux Live Mode - Interactive AI CLI Wrapper

Start claude or codex CLI in an interactive tmux session for direct user interaction.
Beyond slash commands, this provides a persistent terminal interface to AI assistants.
"""

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import argparse
import shlex
import shutil
import subprocess
import time
from typing import Optional

# Use absolute imports with package name for __main__ compatibility
from orchestration.task_dispatcher import CLI_PROFILES


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


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="AI Orchestration - tmux Live Mode",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive Claude session
  ai_orch live

  # Start interactive Codex session
  ai_orch live --cli codex

  # Start with custom session name
  ai_orch live --name my-session

  # Start in specific directory
  ai_orch live --dir ~/my-project

  # List all active sessions
  ai_orch list

  # Attach to existing session
  ai_orch attach my-session

  # Kill a session
  ai_orch kill my-session
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Live command
    live_parser = subparsers.add_parser("live", help="Start interactive AI CLI session")
    live_parser.add_argument(
        "--cli", choices=list(CLI_PROFILES.keys()), default="claude", help="AI CLI to use (default: claude)"
    )
    live_parser.add_argument("--name", help="Custom session name")
    live_parser.add_argument("--dir", help="Working directory (default: current directory)")
    live_parser.add_argument("--model", help="Model to use (default: sonnet for claude)")
    live_parser.add_argument(
        "--detached", action="store_true", help="Start in detached mode (don't attach immediately)"
    )

    # List command
    subparsers.add_parser("list", help="List active sessions")

    # Attach command
    attach_parser = subparsers.add_parser("attach", help="Attach to existing session")
    attach_parser.add_argument("session", help="Session name to attach to")

    # Kill command
    kill_parser = subparsers.add_parser("kill", help="Kill a session")
    kill_parser.add_argument("session", help="Session name to kill")

    args = parser.parse_args()

    # Default to live command if no command specified
    if args.command is None:
        args.command = "live"
        args.cli = "claude"
        args.name = None
        args.dir = None
        args.model = None
        args.detached = False

    # Execute command
    if args.command == "live":
        live_mode = LiveMode(cli_name=args.cli)
        live_mode.start_interactive_session(
            session_name=args.name, working_dir=args.dir, model=args.model, attach=not args.detached
        )

    elif args.command == "list":
        # List sessions for all CLIs
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

    elif args.command == "attach":
        # Try to find session across all CLIs
        session_name = args.session
        found = False

        for cli_name in CLI_PROFILES.keys():
            live_mode = LiveMode(cli_name=cli_name)
            # Normalize session name before checking (add prefix if missing)
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
            sys.exit(1)

    elif args.command == "kill":
        # Try to find and kill session across all CLIs
        session_name = args.session
        found = False

        for cli_name in CLI_PROFILES.keys():
            live_mode = LiveMode(cli_name=cli_name)
            # Normalize session name before checking (add prefix if missing)
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
            sys.exit(1)


if __name__ == "__main__":
    main()
