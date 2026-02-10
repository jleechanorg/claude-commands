#!/usr/bin/env python3
"""
tmux Live Mode - Interactive AI CLI Wrapper

Start claude or codex CLI in an interactive tmux session for direct user interaction.
Beyond slash commands, this provides a persistent terminal interface to AI assistants.
"""

# ruff: noqa: E402

# Allow direct script execution - add parent directory to sys.path
import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import argparse
import contextlib
import io
import json
import shlex
import shutil
import subprocess
import time
from importlib import metadata as importlib_metadata
from typing import Optional

# Use absolute imports with package name for __main__ compatibility
from orchestration.orchestrate_unified import UnifiedOrchestration
from orchestration.task_dispatcher import CLI_PROFILES
from orchestration.task_dispatcher import TaskDispatcher


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

    def _get_version() -> str:
        package_name = "jleechanorg-orchestration"
        try:
            return importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            return "unknown"

    def _normalize_cli_chain(cli_value: Optional[str]):
        if cli_value is None:
            return None, False
        cli_parts = [part.strip().lower() for part in cli_value.split(",") if part.strip()]
        if not cli_parts:
            raise ValueError("Agent CLI chain cannot be empty")
        invalid = [cli for cli in cli_parts if cli not in CLI_PROFILES]
        if invalid:
            raise ValueError(f"Invalid agent CLI(s): {', '.join(invalid)}")
        return ",".join(cli_parts), True

    def _json_dumps_safe(payload: object) -> str:
        try:
            return json.dumps(payload, indent=2)
        except TypeError:
            return json.dumps(payload, indent=2, default=str)

    def _run_unified(args) -> int:
        try:
            agent_cli, cli_provided = _normalize_cli_chain(args.agent_cli)
        except ValueError as exc:
            print(f"❌ {exc}. Valid options: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        if agent_cli is None:
            agent_cli = "gemini"

        task = " ".join(args.task).strip()
        if not task:
            print("❌ Task description is required.")
            return 2

        options = {
            "context": args.context,
            "branch": args.branch,
            "pr": args.pr,
            "mcp_agent": args.mcp_agent,
            "bead": args.bead,
            "validate": args.validate,
            "no_new_pr": args.no_new_pr,
            "no_new_branch": args.no_new_branch,
            "agent_cli": agent_cli,
            "agent_cli_provided": cli_provided,
            "model": args.model,
        }

        try:
            orchestration = UnifiedOrchestration()
            orchestration.orchestrate(task, options=options)
            return 0
        except KeyboardInterrupt:
            print("\n👋 Orchestration interrupted.")
            return 130
        except Exception as exc:
            print(f"❌ Orchestration failed: {exc}")
            return 1

    def _dispatcher_analyze(args) -> int:
        try:
            agent_cli, _ = _normalize_cli_chain(args.agent_cli)
        except ValueError as exc:
            print(f"❌ {exc}. Valid options: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        task = " ".join(args.task).strip()
        try:
            if args.output_json:
                captured_stdout = io.StringIO()
                with contextlib.redirect_stdout(captured_stdout):
                    dispatcher = TaskDispatcher()
                    specs = dispatcher.analyze_task_and_create_agents(task, forced_cli=agent_cli)
                dispatcher_logs = captured_stdout.getvalue().strip()
                if dispatcher_logs:
                    print(dispatcher_logs, file=sys.stderr)
                print(_json_dumps_safe(specs))
            else:
                dispatcher = TaskDispatcher()
                specs = dispatcher.analyze_task_and_create_agents(task, forced_cli=agent_cli)
                print(f"Planned {len(specs)} agent(s):")
                for idx, spec in enumerate(specs, start=1):
                    print(f"{idx}. {spec.get('name')} ({spec.get('cli', 'default')})")
            return 0
        except KeyboardInterrupt:
            print("\n👋 Dispatcher analysis interrupted.")
            return 130
        except Exception as exc:
            print(f"❌ Dispatcher analyze failed: {exc}")
            return 1

    def _dispatcher_create(args) -> int:
        try:
            agent_cli, _ = _normalize_cli_chain(args.agent_cli)
        except ValueError as exc:
            print(f"❌ {exc}. Valid options: {', '.join(sorted(CLI_PROFILES.keys()))}")
            return 2

        try:
            dispatcher = TaskDispatcher()
            task = " ".join(args.task).strip()
            specs = dispatcher.analyze_task_and_create_agents(task, forced_cli=agent_cli)

            if args.model:
                for spec in specs:
                    spec["model"] = args.model

            if args.dry_run:
                print(_json_dumps_safe(specs))
                return 0

            success_count = 0
            for spec in specs:
                print(f"Creating agent: {spec.get('name')}")
                if dispatcher.create_dynamic_agent(spec):
                    success_count += 1
                    print(f"✅ Created: {spec.get('name')}")
                else:
                    print(f"❌ Failed: {spec.get('name')}")

            if success_count != len(specs):
                print(f"❌ Created {success_count}/{len(specs)} agents.")
                return 1
            return 0
        except KeyboardInterrupt:
            print("\n👋 Dispatcher create interrupted.")
            return 130
        except Exception as exc:
            print(f"❌ Dispatcher create failed: {exc}")
            return 1

    parser = argparse.ArgumentParser(
        description="AI Orchestration CLI (unified runtime + task dispatcher)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Unified orchestration (default mode)
  ai_orch run --agent-cli gemini,claude "Fix failing tests"
  ai_orch --agent-cli claude "Implement feature X"

  # TaskDispatcher helpers
  ai_orch dispatcher analyze --agent-cli codex "Refactor API handlers"
  ai_orch dispatcher create --agent-cli gemini "Fix PR #123 conflicts"

  # Legacy interactive tmux mode
  ai_orch live --cli codex
        """,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {_get_version()}",
    )

    commands = {"run", "dispatcher", "live", "list", "attach", "kill"}
    live_only_flags = {"--cli", "--name", "--dir", "--detached", "--model"}
    argv = sys.argv[1:]
    if argv and not argv[0].startswith("-") and argv[0] not in commands:
        argv = ["run"] + argv
    elif argv and argv[0].startswith("-") and argv[0] not in {"--version", "--help", "-h"}:
        if any(arg in live_only_flags for arg in argv):
            argv = ["live"] + argv
        else:
            argv = ["run"] + argv

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Unified orchestration command
    run_parser = subparsers.add_parser("run", help="Run unified orchestration (orchestrate_unified interface)")
    run_parser.add_argument("task", nargs="+", help="Task description for the orchestration system")
    run_parser.add_argument("--context", type=str, default=None, help="Path to markdown context file")
    run_parser.add_argument("--branch", type=str, default=None, help="Force checkout of specific branch")
    run_parser.add_argument("--pr", type=int, default=None, help="Existing PR number to update")
    run_parser.add_argument("--mcp-agent", type=str, default=None, help="Pre-fill agent name for MCP Mail")
    run_parser.add_argument("--bead", type=str, default=None, help="Pre-fill bead ID for tracking")
    run_parser.add_argument("--validate", type=str, default=None, help="Validation command to run after completion")
    run_parser.add_argument("--no-new-pr", action="store_true", help="Block new PR creation")
    run_parser.add_argument("--no-new-branch", action="store_true", help="Block new branch creation")
    run_parser.add_argument(
        "--agent-cli",
        type=str,
        default=None,
        help="Agent CLI to use (supports fallback chain, e.g. gemini,claude)",
    )
    run_parser.add_argument("--model", type=str, default=None, help="Model override for supported CLIs")

    # TaskDispatcher command
    dispatcher_parser = subparsers.add_parser("dispatcher", help="Direct TaskDispatcher utilities")
    dispatcher_subparsers = dispatcher_parser.add_subparsers(dest="dispatcher_command", required=True)

    analyze_parser = dispatcher_subparsers.add_parser("analyze", help="Analyze task and print planned agent specs")
    analyze_parser.add_argument("task", nargs="+", help="Task description to analyze")
    analyze_parser.add_argument("--agent-cli", type=str, default=None, help="Force a specific CLI")
    analyze_parser.add_argument("--json", action="store_true", dest="output_json", help="Print JSON output")

    create_parser = dispatcher_subparsers.add_parser(
        "create", help="Analyze task and create dynamic agents via TaskDispatcher"
    )
    create_parser.add_argument("task", nargs="+", help="Task description")
    create_parser.add_argument("--agent-cli", type=str, default=None, help="Force a specific CLI")
    create_parser.add_argument("--model", type=str, default=None, help="Model override")
    create_parser.add_argument("--dry-run", action="store_true", help="Print planned specs without creating agents")

    # Legacy live command
    live_parser = subparsers.add_parser("live", help="(Legacy) Start interactive AI CLI session")
    live_parser.add_argument(
        "--cli", choices=list(CLI_PROFILES.keys()), default="claude", help="AI CLI to use (default: claude)"
    )
    live_parser.add_argument("--name", help="Custom session name")
    live_parser.add_argument("--dir", help="Working directory (default: current directory)")
    live_parser.add_argument("--model", help="Model to use (default: sonnet for claude)")
    live_parser.add_argument(
        "--detached", action="store_true", help="Start in detached mode (don't attach immediately)"
    )

    # Legacy list/attach/kill commands
    subparsers.add_parser("list", help="(Legacy) List active tmux sessions")
    attach_parser = subparsers.add_parser("attach", help="(Legacy) Attach to existing session")
    attach_parser.add_argument("session", help="Session name to attach to")
    kill_parser = subparsers.add_parser("kill", help="(Legacy) Kill a session")
    kill_parser.add_argument("session", help="Session name to kill")

    args = parser.parse_args(argv)

    if args.command == "run":
        return _run_unified(args)

    if args.command == "dispatcher":
        if args.dispatcher_command == "analyze":
            return _dispatcher_analyze(args)
        if args.dispatcher_command == "create":
            return _dispatcher_create(args)
        return 2

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
