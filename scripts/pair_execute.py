#!/usr/bin/env python3
"""
Pair Execute - Orchestrated Dual-Agent Pair Programming

Launches two agents for pair programming: one for coding, one for verification.
Defaults to Claude (coder) + Codex (verifier), but supports any agent combination.

Usage:
    python3 scripts/pair_execute.py "Task description"
    python3 scripts/pair_execute.py --coder-cli gemini --verifier-cli claude "Task"
    python3 scripts/pair_execute.py --coder-cli claude --verifier-cli claude "Task"  # Claude + Claude
    python3 scripts/pair_execute.py --brainstorm "Task description"
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import random
import subprocess  # nosec
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

# Constants
BEADS_FILE = ".beads/beads.left.jsonl"
SESSION_DIR = Path(tempfile.gettempdir()) / "pair_sessions"
# Use resolved absolute paths to work correctly from any directory
ORCHESTRATE_SCRIPT = str(
    Path(__file__).resolve().parent.parent / "orchestration" / "orchestrate_unified.py"
)
MONITOR_SCRIPT = str(Path(__file__).resolve().parent / "pair_monitor.py")

# Supported CLI options
SUPPORTED_CLIS = ["claude", "codex", "gemini", "cursor"]

# Default settings
DEFAULT_CODER_CLI = "claude"
DEFAULT_VERIFIER_CLI = "codex"
DEFAULT_MAX_ITERATIONS = 10
DEFAULT_MONITOR_INTERVAL = 60


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now(UTC).isoformat()
    print(f"[{timestamp}] {message}", flush=True)


def generate_session_id() -> str:
    """Generate unique session ID with randomness to prevent collisions."""
    return f"pair-{int(time.time())}-{random.randint(10000, 99999)}"


def create_session_directory(session_id: str) -> Path:
    """Create session directory for artifacts."""
    session_dir = Path(SESSION_DIR) / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def create_bead_entry(bead_id: str, task_description: str) -> bool:
    """Create bead entry for state tracking with fcntl locking."""
    try:
        beads_path = Path(BEADS_FILE)
        beads_path.parent.mkdir(parents=True, exist_ok=True)
        
        title = f"Pair Session: {task_description[:50]}"
        if len(task_description) > 50:
            title += "..."

        timestamp = datetime.now(UTC).isoformat()
        bead = {
            "id": bead_id,
            "title": title,
            "description": f"Dual-agent pair programming session for: {task_description}",
            "status": "in_progress",
            "priority": 1,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        with open(beads_path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(json.dumps(bead) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"Created bead: {bead_id}")
        return True

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error creating bead: {e}")
        return False
    except Exception as e:
        log(f"Unexpected error creating bead: {e}")
        return False


def update_bead_status(bead_id: str, status: str) -> bool:
    """Update bead status in beads file with fcntl locking."""
    try:
        beads_path = Path(BEADS_FILE)
        if not beads_path.exists():
            log(f"Beads file not found: {beads_path}")
            return False

        with open(beads_path, "r+", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                
                # Read all beads
                lines = f.readlines()
                beads = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line:
                        beads.append(json.loads(stripped_line))

                # Update matching bead
                updated = False
                for bead in beads:
                    if bead.get("id") == bead_id:
                        bead["status"] = status
                        bead["updated_at"] = datetime.now(UTC).isoformat()
                        updated = True
                        break

                if not updated:
                    log(f"Bead {bead_id} not found")
                    return False

                # Write back
                f.seek(0)
                f.truncate()
                for bead in beads:
                    f.write(json.dumps(bead) + "\n")
                f.flush()
                os.fsync(f.fileno())
                
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"Bead {bead_id} updated to status: {status}")
        return True

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error updating bead: {e}")
        return False
    except Exception as e:
        log(f"Unexpected error updating bead: {e}")
        return False


def create_tdd_paired_beads(session_id: str, task_description: str) -> dict | None:
    """Create TDD paired beads for tests, implementation, and verification.

    Returns dict with bead IDs or None if creation failed.
    """
    try:
        timestamp = datetime.now(UTC).isoformat()

        # Bead IDs following pattern: session-id-suffix
        tests_bead_id = f"{session_id}-tests"
        impl_bead_id = f"{session_id}-impl"
        verification_bead_id = f"{session_id}-verification"

        log("Creating TDD paired beads...")

        # Create tests bead
        tests_bead = {
            "id": tests_bead_id,
            "title": f"[TESTS] {task_description[:40]}...",
            "description": f"Write tests for: {task_description}",
            "status": "todo",
            "priority": 1,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Create implementation bead
        impl_bead = {
            "id": impl_bead_id,
            "title": f"[IMPL] {task_description[:40]}...",
            "description": f"Implement: {task_description}",
            "status": "todo",
            "priority": 2,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        # Create verification bead
        verification_bead = {
            "id": verification_bead_id,
            "title": f"[VERIFY] {task_description[:40]}...",
            "description": f"Verify implementation for: {task_description}",
            "status": "todo",
            "priority": 3,
            "issue_type": "task",
            "created_at": timestamp,
            "updated_at": timestamp,
        }

        beads_path = Path(BEADS_FILE)
        beads_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(beads_path, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(json.dumps(tests_bead) + "\n")
                f.write(json.dumps(impl_bead) + "\n")
                f.write(json.dumps(verification_bead) + "\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

        log(f"✅ Created tests bead: {tests_bead_id}")
        log(f"✅ Created implementation bead: {impl_bead_id}")
        log(f"✅ Created verification bead: {verification_bead_id}")

        return {
            "tests_bead_id": tests_bead_id,
            "impl_bead_id": impl_bead_id,
            "verification_bead_id": verification_bead_id,
        }

    except (OSError, json.JSONDecodeError) as e:
        log(f"Error creating TDD paired beads: {e}")
        return None
    except Exception as e:
        log(f"Unexpected error creating TDD paired beads: {e}")
        return None


def generate_default_instructions(
    task_description: str, session_dir: Path, tdd_beads: dict | None = None
) -> dict | None:
    """Generate default task instructions without brainstorming.

    Args:
        task_description: The task to be implemented
        session_dir: Directory for session artifacts
        tdd_beads: Optional dict with tests_bead_id, impl_bead_id, verification_bead_id
    """
    # Build TDD bead instructions if beads were created
    tdd_bead_instructions = ""
    verification_bead_instructions = ""

    if tdd_beads:
        tdd_bead_instructions = f"""
TDD PAIRED BEADS (CRITICAL):
This task has 3 beads that MUST be updated in order:

1. TESTS BEAD: {tdd_beads['tests_bead_id']}
   - Write tests FIRST (TDD approach)
   - Update status: todo -> in_progress -> done
   - Mark done ONLY when tests are written and failing (RED phase)

2. IMPLEMENTATION BEAD: {tdd_beads['impl_bead_id']}
   - Implement code to make tests pass
   - Update status: todo -> in_progress -> done
   - Mark done ONLY when all tests pass (GREEN phase)

3. VERIFICATION BEAD: {tdd_beads['verification_bead_id']}
   - VERIFIER ONLY can update this bead
   - DO NOT mark this bead as done - only the verifier can
   - This tracks the verifier's review and approval

Update beads using: mcp__beads__update --id <bead-id> --status <status>
"""
        verification_bead_instructions = f"""
VERIFICATION BEAD RESPONSIBILITY (CRITICAL):
YOU are the ONLY agent who can mark the verification bead as done.

Verification Bead: {tdd_beads['verification_bead_id']}
- Update status: todo -> in_progress (when you start review)
- Update status: in_progress -> done (ONLY when ALL verification passes)
- Update status: in_progress -> blocked (if major issues found)

The coder has completed the tests and impl beads. Your job is to verify their work.
"""

    # MCP setup instructions
    mcp_setup_instructions = """
MCP SETUP (Required for Pair Programming):

This session requires two MCP servers for coordination:

1. Beads MCP (steveyegge/beads) - Task tracking
   - Check if available: Try calling mcp__beads__list
   - If not installed: Follow setup at https://github.com/steveyegge/beads
   - Configuration: Add to ~/.claude/mcp.json (server named "beads")

2. Agent Mail MCP (jleechanorg/mcp_mail) - Inter-agent messaging
   - Check if available: Try calling mcp__agentmail__check_inbox
   - If not installed:
     ```bash
     # Clone and install mcp_mail
     git clone https://github.com/jleechanorg/mcp_mail.git ~/mcp_mail
     cd ~/mcp_mail && npm install && npm run build
     ```
   - Configuration: Add to ~/.claude/mcp.json:
     ```json
     {
       "agentmail": {
         "command": "node",
         "args": ["/path/to/mcp_mail/build/index.js"],
         "env": {}
       }
     }
     ```
   - Verify: Check inbox with mcp__agentmail__check_inbox

If either MCP is unavailable, STOP and request setup before continuing.
Both are critical for pair programming coordination.
"""

    brainstorm_result = {
        "task": task_description,
        "coder_instructions": f"""IMPLEMENTATION TASK: {task_description}

Your role is IMPLEMENTATION. You are the coding agent in a pair programming session.

IMPORTANT: This is an ITERATIVE session. You will continue to run and communicate with
the Verifier agent until BOTH of you agree the work is complete and meets all requirements.

{mcp_setup_instructions}
{tdd_bead_instructions}
Instructions:
1. Write tests FIRST (update tests bead to in_progress, then done when tests written)
2. Implement the requested feature/fix following best practices (update impl bead)
3. Ensure code passes all existing tests
4. Commit your changes with descriptive messages
5. Send IMPLEMENTATION_READY message via MCP Mail when complete

Quality Requirements:
- Follow existing code patterns in the codebase
- Include proper error handling
- Add docstrings/comments for complex logic
- Ensure test coverage for new code

Beads MCP Integration:
- Update bead status as you progress (use Beads MCP if available: mcp__beads__update)
- Track your work in the bead system for visibility
- TDD workflow: tests (todo->done) -> impl (todo->done) -> verification (VERIFIER ONLY)

Iterative Coordination Protocol (INDEPENDENT POLLING):
- YOU are a long-running process - do NOT exit until VERIFICATION_COMPLETE
- Send IMPLEMENTATION_READY to Verifier via MCP Mail (mcp__agentmail__send_message)
- Poll inbox in a loop to wait for Verifier response (check every 30 seconds)
- Example polling pattern: while True: check_inbox, if messages: break, sleep(30)
- If VERIFICATION_FAILED: Review feedback, fix issues, re-send IMPLEMENTATION_READY, resume polling
- If VERIFICATION_COMPLETE: Update beads, create PR, EXIT successfully
- You may iterate multiple times - this is expected and encouraged for quality
- MCP Mail is REQUIRED - if mcp__agentmail__* tools fail, exit with error

MCP Mail Communication:
- Use mcp__agentmail__send_message to send messages to Verifier
- Use mcp__agentmail__check_inbox to poll for Verifier responses (every 30s)
- Message body should include: files_changed (list), test_result (pass/fail), test_summary (string)
- Include detailed context in message bodies (files changed, test results, etc.)
""",
        "verifier_instructions": f"""VERIFICATION TASK: Verify implementation for {task_description}

Your role is VERIFICATION. You are the testing agent in a pair programming session.

IMPORTANT: This is an ITERATIVE session. You will continue to run and communicate with
the Coder agent until BOTH of you agree the work is complete and meets all requirements.

{mcp_setup_instructions}
{tdd_bead_instructions}
{verification_bead_instructions}
Instructions:
1. Check MCP Mail for IMPLEMENTATION_READY message from Coder agent
2. Verify tests bead is marked done (tests were written first - TDD)
3. Verify impl bead is marked done (implementation complete)
4. Review the implementation files listed in the message
5. Run all tests: TESTING=true vpython -m pytest
6. Verify code quality and test coverage
7. Check for common issues:
   - Missing edge cases
   - Security vulnerabilities
   - Performance concerns
   - Documentation gaps

Verification Checklist:
- [ ] Tests bead is marked done
- [ ] Implementation bead is marked done
- [ ] All tests pass
- [ ] New code has test coverage
- [ ] No regressions introduced
- [ ] Code follows project conventions
- [ ] Implementation fully addresses the task requirements

Beads MCP Integration:
- Update verification bead status as you progress (mcp__beads__update)
- YOU ALONE control the verification bead
- Status flow: todo -> in_progress -> done (or blocked if issues)
- Mark done ONLY when you're fully confident in the implementation

Iterative Coordination Protocol (INDEPENDENT POLLING):
- YOU are a long-running process - do NOT exit until you send VERIFICATION_COMPLETE
- Poll inbox in a loop to wait for IMPLEMENTATION_READY from Coder (check every 30 seconds)
- Example polling pattern: while True: check_inbox, filter for IMPLEMENTATION_READY, if found: break, sleep(30)
- Receive IMPLEMENTATION_READY → run thorough verification checks
- If issues found: Send VERIFICATION_FAILED with detailed feedback, resume polling for next attempt
- If all checks pass: Send VERIFICATION_COMPLETE, mark verification bead done, EXIT successfully
- You may request fixes multiple times - this is expected and encouraged for quality
- Be thorough and demand excellence - you are the quality gatekeeper
- MCP Mail is REQUIRED - if mcp__agentmail__* tools fail, exit with error

MCP Mail Communication:
- Use mcp__agentmail__check_inbox to poll for messages from Coder (every 30s)
- Use mcp__agentmail__send_message to send responses to Coder
- Message body should include: feedback (string), files (list), test_result (pass/fail)
- Include detailed feedback in VERIFICATION_FAILED messages (specific files, line numbers, issues)

Response Protocol:
- VERIFICATION_COMPLETE: Only send when ALL criteria met and you're confident
- VERIFICATION_FAILED: Include specific actionable feedback for Coder to address
- After sending FAILED: Resume polling for updated IMPLEMENTATION_READY messages
- When sending VERIFICATION_COMPLETE: ALSO mark verification bead as done, then EXIT
""",
        "success_criteria": [
            "All tests pass",
            "Code implements requested functionality",
            "No regressions introduced",
            "Test coverage meets standards",
        ],
    }

    # Save brainstorm results
    brainstorm_file = session_dir / "brainstorm_results.json"
    try:
        with open(brainstorm_file, "w", encoding="utf-8") as f:
            json.dump(brainstorm_result, f, indent=2)
        log(f"Task plan saved to: {brainstorm_file}")
    except OSError as exc:
        log(
            "Warning: Failed to save task plan to disk; "
            f"continuing with in-memory plan only ({exc})."
        )
    return brainstorm_result


def brainstorm_task(
    task_description: str, session_dir: Path, tdd_beads: dict | None = None
) -> dict | None:
    """Use Superpowers to brainstorm the task (placeholder for actual implementation)."""
    # This would integrate with Chrome Superpowers MCP for actual brainstorming
    # For now, generate a structured plan
    log("Generating task plan via brainstorm...")
    return generate_default_instructions(task_description, session_dir, tdd_beads)


def launch_coder_agent(
    session_id: str,
    bead_id: str,
    instructions: str,
    cli: str = DEFAULT_CODER_CLI,
    verifier_agent_name: str | None = None,
    session_dir: Path | None = None,
) -> tuple[bool, str]:
    """Launch coder agent for implementation."""
    agent_name = f"{cli}-coder-{session_id}"
    verifier_name = verifier_agent_name or f"{DEFAULT_VERIFIER_CLI}-verifier-{session_id}"

    # Build the full prompt
    full_prompt = f"""{instructions}

---
PAIR SESSION CONFIGURATION:
- Session ID: {session_id}
- Agent Role: IMPLEMENTATION ({cli.upper()})
- Partner Agent: {verifier_name}
- Bead ID: {bead_id}
- MCP Mail Protocol: Send IMPLEMENTATION_READY when done

COMMUNICATION:
When implementation is complete, send this MCP mail message:
Subject: IMPLEMENTATION_READY
To: {verifier_name}
Body: {{
  "session_id": "{session_id}",
  "files_changed": ["<list of modified files>"],
  "tests_added": ["<list of test files>"],
  "summary": "<brief description of changes>"
}}
"""

    log(f"Launching {cli.upper()} coder agent: {agent_name}")

    # Use orchestration to create the agent
    # Run in background with nohup to ensure agent persists
    cmd = [
        sys.executable,
        ORCHESTRATE_SCRIPT,
        "--agent-cli",
        cli,
        "--bead",
        bead_id,
        "--mcp-agent",
        agent_name,
        full_prompt,
    ]

    try:
        # Launch orchestration in background - don't wait for it
        log_file = (
            session_dir / f"{agent_name}.log"
            if session_dir
            else Path(tempfile.gettempdir()) / f"{agent_name}.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
            )

        # Give it a moment to start
        time.sleep(1)

        # Check if process is still running (good sign)
        if process.poll() is None:
            log(f"{cli.upper()} coder agent launched successfully: {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name
        log(f"Failed to launch {cli.upper()} coder agent (process exited)")
        return False, agent_name

    except Exception as e:
        log(f"Error launching {cli.upper()} coder agent: {e}")
        return False, agent_name


def launch_verifier_agent(
    session_id: str,
    bead_id: str,
    instructions: str,
    cli: str = DEFAULT_VERIFIER_CLI,
    coder_agent_name: str | None = None,
    session_dir: Path | None = None,
) -> tuple[bool, str]:
    """Launch verifier agent for test verification."""
    agent_name = f"{cli}-verifier-{session_id}"
    coder_name = coder_agent_name or f"{DEFAULT_CODER_CLI}-coder-{session_id}"

    # Build the full prompt
    full_prompt = f"""{instructions}

---
PAIR SESSION CONFIGURATION:
- Session ID: {session_id}
- Agent Role: VERIFICATION ({cli.upper()})
- Partner Agent: {coder_name}
- Bead ID: {bead_id}
- MCP Mail Protocol: Poll for IMPLEMENTATION_READY, send VERIFICATION_COMPLETE/FAILED

COMMUNICATION:
1. Poll for IMPLEMENTATION_READY from {coder_name}
2. After verification, send one of:

   SUCCESS - Subject: VERIFICATION_COMPLETE
   Body: {{
     "session_id": "{session_id}",
     "test_results": "all_pass",
     "coverage": "<percentage>",
     "summary": "<verification summary>"
   }}

   FAILURE - Subject: VERIFICATION_FAILED
   Body: {{
     "session_id": "{session_id}",
     "failures": ["<list of issues>"],
     "suggestions": ["<recommended fixes>"]
   }}
"""

    log(f"Launching {cli.upper()} verifier agent: {agent_name}")

    # Use orchestration to create the agent
    # Run in background with nohup to ensure agent persists
    cmd = [
        sys.executable,
        ORCHESTRATE_SCRIPT,
        "--agent-cli",
        cli,
        "--bead",
        bead_id,
        "--mcp-agent",
        agent_name,
        full_prompt,
    ]

    try:
        # Launch orchestration in background - don't wait for it
        log_file = (
            session_dir / f"{agent_name}.log"
            if session_dir
            else Path(tempfile.gettempdir()) / f"{agent_name}.log"
        )
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, "w", encoding="utf-8") as f:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=f,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
            )

        # Give it a moment to start
        time.sleep(1)

        # Check if process is still running (good sign)
        if process.poll() is None:
            log(f"{cli.upper()} verifier agent launched successfully: {agent_name}")
            log(f"  Agent log: {log_file}")
            return True, agent_name
        log(f"Failed to launch {cli.upper()} verifier agent (process exited)")
        return False, agent_name

    except Exception as e:
        log(f"Error launching {cli.upper()} verifier agent: {e}")
        return False, agent_name


def start_background_monitor(
    session_id: str,
    coder_agent: str,
    verifier_agent: str,
    bead_id: str,
    session_dir: Path,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
    interval: int = DEFAULT_MONITOR_INTERVAL,
) -> int | None:
    """Start background monitor process."""
    log("Starting background monitor...")

    monitor_log = session_dir / "monitor.log"
    pid_file = session_dir / "monitor.pid"

    cmd = [
        sys.executable,
        MONITOR_SCRIPT,
        "--session-id",
        session_id,
        "--coder-agent",
        coder_agent,
        "--verifier-agent",
        verifier_agent,
        "--bead-id",
        bead_id,
        "--max-iterations",
        str(max_iterations),
        "--interval",
        str(interval),
    ]

    try:
        # Start monitor as background process
        with open(monitor_log, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(  # noqa: S603 # nosec
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # Detach from parent
            )

        # Give it a moment to start
        time.sleep(1)

        # Check if process is still running (good sign)
        if process.poll() is not None:
            log("Failed to start monitor (process exited immediately)")
            return None

        # Write PID
        with open(pid_file, "w", encoding="utf-8") as f:
            f.write(str(process.pid))

        log(f"Monitor started (PID: {process.pid})")
        log(f"Monitor log: {monitor_log}")
        return process.pid

    except Exception as e:
        log(f"Error starting monitor: {e}")
        return None


def main():  # noqa: PLR0915
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Launch dual-agent pair programming session (default: Claude + Codex)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    # Default: Claude coder + Codex verifier
    python3 scripts/pair_execute.py "Add user authentication with JWT"

    # Custom: Gemini coder + Claude verifier
    python3 scripts/pair_execute.py --coder-cli gemini --verifier-cli claude "Task"

    # Same CLI for both: Claude + Claude
    python3 scripts/pair_execute.py --coder-cli claude --verifier-cli claude "Task"

    # With brainstorm phase
    python3 scripts/pair_execute.py --brainstorm "Implement dark mode toggle"

    # Custom iterations
    python3 scripts/pair_execute.py --max-iterations 5 --interval 30 "Fix bug"

Supported CLIs: {", ".join(SUPPORTED_CLIS)}
        """,
    )

    parser.add_argument("task", help="Task description")
    parser.add_argument(
        "--coder-cli",
        choices=SUPPORTED_CLIS,
        default=DEFAULT_CODER_CLI,
        help=f"CLI for coder agent (default: {DEFAULT_CODER_CLI})",
    )
    parser.add_argument(
        "--verifier-cli",
        choices=SUPPORTED_CLIS,
        default=DEFAULT_VERIFIER_CLI,
        help=f"CLI for verifier agent (default: {DEFAULT_VERIFIER_CLI})",
    )
    parser.add_argument(
        "--brainstorm",
        action="store_true",
        help="Run brainstorm phase before launching agents",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=DEFAULT_MAX_ITERATIONS,
        help=f"Maximum monitor iterations (default: {DEFAULT_MAX_ITERATIONS})",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_MONITOR_INTERVAL,
        help=f"Monitor check interval in seconds (default: {DEFAULT_MONITOR_INTERVAL})",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Skip background monitor (agents only)",
    )

    args = parser.parse_args()

    # Initialize session
    log("=" * 60)
    log("PAIR PROGRAMMING SESSION")
    log("=" * 60)

    session_id = generate_session_id()
    session_dir = create_session_directory(session_id)
    bead_id = session_id

    log(f"Session ID: {session_id}")
    log(f"Task: {args.task}")
    log(f"Session Dir: {session_dir}")

    # Phase 1: Create TDD paired beads
    log("")
    log("Phase 1: Creating TDD paired beads (tests, impl, verification)...")
    tdd_beads = create_tdd_paired_beads(session_id, args.task)
    if not tdd_beads:
        log("Warning: Failed to create TDD paired beads, continuing anyway")

    # Also create session tracking bead
    log("")
    log("Phase 1b: Creating session tracking bead...")
    if not create_bead_entry(bead_id, args.task):
        log("Warning: Failed to create session bead entry, continuing anyway")

    # Phase 2: Brainstorm (if requested)
    brainstorm_result = None
    if args.brainstorm:
        log("")
        log("Phase 2: Brainstorming task...")
        brainstorm_result = brainstorm_task(args.task, session_dir, tdd_beads)
    else:
        # Generate default instructions without brainstorming
        log("")
        log("Phase 2: Generating default task plan...")
        brainstorm_result = generate_default_instructions(args.task, session_dir, tdd_beads)

    if not brainstorm_result:
        log("Failed to generate task plan")
        sys.exit(1)

    # Build agent names based on CLI selection
    verifier_agent_name = f"{args.verifier_cli}-verifier-{session_id}"

    # Phase 3: Launch coder agent
    log("")
    log(f"Phase 3: Launching {args.coder_cli.upper()} coder agent (Implementation)...")
    coder_success, coder_agent = launch_coder_agent(
        session_id,
        bead_id,
        brainstorm_result["coder_instructions"],
        cli=args.coder_cli,
        verifier_agent_name=verifier_agent_name,
        session_dir=session_dir,
    )

    if not coder_success:
        log(f"Failed to launch {args.coder_cli.upper()} coder agent")
        update_bead_status(bead_id, "failed")
        sys.exit(1)

    # Brief delay to stagger agent launches
    time.sleep(2)

    # Phase 4: Launch verifier agent
    log("")
    log(
        f"Phase 4: Launching {args.verifier_cli.upper()} verifier agent (Verification)..."
    )
    verifier_success, verifier_agent = launch_verifier_agent(
        session_id,
        bead_id,
        brainstorm_result["verifier_instructions"],
        cli=args.verifier_cli,
        coder_agent_name=coder_agent,
        session_dir=session_dir,
    )

    if not verifier_success:
        log(f"Failed to launch {args.verifier_cli.upper()} verifier agent")
        # Update bead status to partial-failure
        update_bead_status(bead_id, "partial-failure")
        log(f"⚠️  PARTIAL SESSION: Only {args.coder_cli.upper()} coder agent is running")
        log("⚠️  Background monitor will NOT start (requires both agents)")
        # Set monitor_pid to None since we're not starting the monitor
        monitor_pid = None
        sys.exit(1)
    else:
        # Phase 5: Start background monitor (only if both agents are running)
        monitor_pid = None
        if not args.no_monitor:
            log("")
            log("Phase 5: Starting background monitor...")
            monitor_pid = start_background_monitor(
                session_id,
                coder_agent,
                verifier_agent,
                bead_id,
                session_dir,
                max_iterations=args.max_iterations,
                interval=args.interval,
            )

    # Summary
    log("")
    log("=" * 60)
    log("PAIR SESSION LAUNCHED")
    log("=" * 60)
    log(f"Session ID: {session_id}")
    log(f"Coder Agent ({args.coder_cli.upper()}): {coder_agent}")
    log(f"Verifier Agent ({args.verifier_cli.upper()}): {verifier_agent}")
    log(f"Bead ID: {bead_id}")
    log(f"Monitor PID: {monitor_pid or 'N/A'}")
    log("")
    log("Monitoring Commands:")
    log(f"  tmux attach -t {coder_agent}  # View coder agent")
    log(f"  tmux attach -t {verifier_agent}   # View verifier agent")
    log(f"  tail -f {session_dir}/monitor.log  # View monitor log")
    log("")
    log("Stop Session:")
    if monitor_pid:
        log(f"  kill {monitor_pid}  # Stop monitor")
    else:
        log("  # Monitor not running")
    log(f"  tmux kill-session -t {coder_agent}")
    log(f"  tmux kill-session -t {verifier_agent}")
    log("=" * 60)


if __name__ == "__main__":
    main()
