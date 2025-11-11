#!/usr/bin/env python3
"""
Proto Genesis - Interactive Goal Refinement System
Executes goal refinement using claude -p based on pre-defined goals from /goal command
"""

import fcntl
import json
import os
import re
import select
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .common_cli import (
    GenesisArguments,
    GenesisHelpRequested,
    GenesisUsageError,
    extract_model_preference,
    parse_genesis_cli,
)
from .common_cli import (
    print_usage as print_cli_usage,
)

GENESIS_USE_CODEX: bool | None = None

# Token burn prevention constants (centralized to avoid duplication)
MAX_TOKENS_PER_ITERATION = 50_000  # Hard limit per iteration
MAX_PROMPT_LENGTH = 100_000  # Context overflow prevention
MAX_FIELD_SIZE = 50_000  # Session field size limit


def is_codex_enabled(argv: list[str] | None = None) -> bool:
    """Determine whether Codex should be used (Codex default)."""
    global GENESIS_USE_CODEX

    if GENESIS_USE_CODEX is not None:
        return GENESIS_USE_CODEX

    args = list(sys.argv) if argv is None else list(argv)
    if "--claude" in args and "--codex" in args:
        raise GenesisUsageError("Cannot specify both --codex and --claude")

    preference = extract_model_preference(args)
    use_codex = True if preference is None else preference
    GENESIS_USE_CODEX = use_codex
    return use_codex

# SlashCommand import removed to comply with mandatory import patterns
# Code review integration disabled to prevent import violations


class WorkflowStatus(Enum):
    """Enumeration for workflow status states"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class TestStatus(Enum):
    """Enumeration for test execution status"""
    NOT_RUN = "not_run"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowState:
    """Structured workflow state with comprehensive validation and progress tracking"""

    # Core Status Fields
    goal_complete: bool = False
    tests_passing: bool = False
    implementation_gaps: str | None = None
    current_phase: str = "B1"
    error_message: str | None = None

    # Enhanced Tracking Fields
    phase_history: list[str] = field(default_factory=list)
    iteration_count: int = 0
    max_iterations: int = 20
    start_timestamp: float | None = None
    end_timestamp: float | None = None

    # Validation State
    validation_errors: list[str] = field(default_factory=list)
    test_failures: list[str] = field(default_factory=list)
    integration_status: str | None = None

    # Progress Metrics
    completion_percentage: float = 0.0
    phase_durations: dict[str, float] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3

    # Token Usage Tracking (prevent infinite burn)
    total_tokens_used: int = 0
    iteration_tokens: dict[int, int] = field(default_factory=dict)
    max_tokens_per_iteration: int = field(default_factory=lambda: MAX_TOKENS_PER_ITERATION)

    def __post_init__(self) -> None:
        """Initialize state with proper defaults and validation"""
        if self.start_timestamp is None:
            import time
            self.start_timestamp = time.time()

        # Ensure phase history tracks current phase
        if self.current_phase not in self.phase_history:
            self.phase_history.append(self.current_phase)

    @property
    def is_complete(self) -> bool:
        """Workflow is complete when both goal and tests are satisfied"""
        return self.goal_complete and self.tests_passing and not self.validation_errors

    @property
    def is_failed(self) -> bool:
        """Workflow has failed if max iterations/retries exceeded or critical errors"""
        return (
            self.iteration_count >= self.max_iterations or
            self.retry_count >= self.max_retries or
            bool(self.error_message and "critical" in self.error_message.lower())
        )

    @property
    def duration(self) -> float | None:
        """Calculate total workflow duration if completed"""
        if self.start_timestamp and self.end_timestamp:
            return self.end_timestamp - self.start_timestamp
        if self.start_timestamp:
            import time
            return time.time() - self.start_timestamp
        return None

    @property
    def current_status(self) -> WorkflowStatus:
        """Determine current workflow status"""
        if self.is_complete:
            return WorkflowStatus.COMPLETED
        if self.is_failed:
            return WorkflowStatus.FAILED
        return WorkflowStatus.IN_PROGRESS

    def advance_phase(self, new_phase: str) -> None:
        """Advance to new phase with proper tracking"""
        import time
        current_time = time.time()

        # Record duration of previous phase
        if self.phase_history and self.start_timestamp:
            previous_phase = self.phase_history[-1]
            if previous_phase not in self.phase_durations:
                phase_start = self.start_timestamp + sum(self.phase_durations.values())
                self.phase_durations[previous_phase] = current_time - phase_start

        # Update to new phase
        self.current_phase = new_phase
        if new_phase not in self.phase_history:
            self.phase_history.append(new_phase)

        self.iteration_count += 1

    def add_validation_error(self, error: str) -> None:
        """Add validation error with deduplication"""
        if error not in self.validation_errors:
            self.validation_errors.append(error)

    def add_test_failure(self, failure: str) -> None:
        """Add test failure with deduplication"""
        if failure not in self.test_failures:
            self.test_failures.append(failure)

    def clear_validation_errors(self) -> None:
        """Clear all validation errors"""
        self.validation_errors.clear()

    def clear_test_failures(self) -> None:
        """Clear all test failures"""
        self.test_failures.clear()

    def increment_retry(self) -> bool:
        """Increment retry count and return if more retries available"""
        self.retry_count += 1
        return self.retry_count < self.max_retries

    def add_token_usage(self, tokens: int, iteration: int) -> bool:
        """Track token usage and prevent burn. Returns False if limit exceeded."""
        self.total_tokens_used += tokens

        # Track per-iteration tokens
        if iteration in self.iteration_tokens:
            self.iteration_tokens[iteration] += tokens
        else:
            self.iteration_tokens[iteration] = tokens

        # Check if this iteration exceeds limit
        if self.iteration_tokens[iteration] > self.max_tokens_per_iteration:
            print(f"🛑 TOKEN BURN PREVENTION: Iteration {iteration} used {self.iteration_tokens[iteration]} tokens")
            print(f"    Maximum per iteration: {self.max_tokens_per_iteration}")
            return False

        # Log current usage
        print(f"📊 TOKEN TRACKING: Iteration {iteration}: {self.iteration_tokens[iteration]} tokens, Total: {self.total_tokens_used}")
        return True

    def calculate_completion_percentage(self) -> float:
        """Calculate completion percentage based on goals and tests"""
        total_criteria = 4  # goal_complete, tests_passing, no_validation_errors, no_test_failures
        completed_criteria = 0

        if self.goal_complete:
            completed_criteria += 1
        if self.tests_passing:
            completed_criteria += 1
        if not self.validation_errors:
            completed_criteria += 1
        if not self.test_failures:
            completed_criteria += 1

        self.completion_percentage = (completed_criteria / total_criteria) * 100.0
        return self.completion_percentage

    def finalize(self) -> None:
        """Mark workflow as finished and record end timestamp"""
        import time
        self.end_timestamp = time.time()
        self.calculate_completion_percentage()

        # Record final phase duration
        if self.phase_history and self.start_timestamp:
            final_phase = self.phase_history[-1]
            if final_phase not in self.phase_durations:
                phase_start = self.start_timestamp + sum(self.phase_durations.values())
                self.phase_durations[final_phase] = self.end_timestamp - phase_start

    def update_from_response(self, response: str, phase: str) -> None:
        """Update state from AI response with reliable parsing"""
        response_lower = response.lower()

        # Update current phase if different
        if phase != self.current_phase:
            self.advance_phase(phase)

        # Check for goal completion indicators
        goal_indicators = [
            "goal fully implemented",
            "implementation complete",
            "objective achieved",
            "requirements satisfied",
            "100% complete",
            "fully functional",
            "successfully implemented"
        ]
        self.goal_complete = any(indicator in response_lower for indicator in goal_indicators)

        # Check for test passing indicators
        test_indicators = [
            "all tests pass",
            "tests passed",
            "no test failures",
            "test execution successful",
            "100% test success",
            "tests are passing"
        ]
        self.tests_passing = any(indicator in response_lower for indicator in test_indicators)

        # Extract test failures
        if "test fail" in response_lower or "failed test" in response_lower:
            failure_lines = [
                line.strip() for line in response.split('\n')
                if any(term in line.lower() for term in ["fail", "error", "exception"])
            ]
            for failure in failure_lines:
                self.add_test_failure(failure)

        # Check for implementation gaps
        gap_indicators = [
            "implementation gaps",
            "missing functionality",
            "incomplete features",
            "pending implementation",
            "not yet implemented",
            "todo",
            "placeholder"
        ]
        if any(indicator in response_lower for indicator in gap_indicators):
            # Extract the gap description
            for line in response.split('\n'):
                if any(indicator in line.lower() for indicator in gap_indicators):
                    self.implementation_gaps = line.strip()
                    break

        # Extract error messages
        error_indicators = ["error:", "exception:", "critical:", "fatal:"]
        for line in response.split('\n'):
            if any(indicator in line.lower() for indicator in error_indicators):
                self.error_message = line.strip()
                break

        # Update completion percentage
        self.calculate_completion_percentage()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'goal_complete': self.goal_complete,
            'tests_passing': self.tests_passing,
            'implementation_gaps': self.implementation_gaps,
            'current_phase': self.current_phase,
            'error_message': self.error_message,
            'phase_history': self.phase_history,
            'iteration_count': self.iteration_count,
            'max_iterations': self.max_iterations,
            'start_timestamp': self.start_timestamp,
            'end_timestamp': self.end_timestamp,
            'validation_errors': self.validation_errors,
            'test_failures': self.test_failures,
            'integration_status': self.integration_status,
            'completion_percentage': self.completion_percentage,
            'phase_durations': self.phase_durations,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'current_status': self.current_status.value,
            'duration': self.duration
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'WorkflowState':
        """Create WorkflowState from dictionary"""
        # Handle optional fields with defaults
        instance = cls(
            goal_complete=data.get('goal_complete', False),
            tests_passing=data.get('tests_passing', False),
            implementation_gaps=data.get('implementation_gaps'),
            current_phase=data.get('current_phase', 'B1'),
            error_message=data.get('error_message'),
            phase_history=data.get('phase_history', []),
            iteration_count=data.get('iteration_count', 0),
            max_iterations=data.get('max_iterations', 20),
            start_timestamp=data.get('start_timestamp'),
            end_timestamp=data.get('end_timestamp'),
            validation_errors=data.get('validation_errors', []),
            test_failures=data.get('test_failures', []),
            integration_status=data.get('integration_status'),
            completion_percentage=data.get('completion_percentage', 0.0),
            phase_durations=data.get('phase_durations', {}),
            retry_count=data.get('retry_count', 0),
            max_retries=data.get('max_retries', 3)
        )
        return instance


class SecureFileHandler:
    """Secure file operations with locking to prevent race conditions"""

    @staticmethod
    def write_with_lock(filepath: str, content: str) -> None:
        """Write to file with exclusive lock to prevent race conditions"""
        try:
            dir_path = os.path.dirname(filepath)
            if dir_path:  # Only create if directory path is not empty
                os.makedirs(dir_path, exist_ok=True)

            with open(filepath, 'w') as f:
                # Try file locking if available (Unix systems)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    f.write(content)
                    f.flush()
                    os.fsync(f.fileno())  # Force write to disk
                except (AttributeError, OSError, TypeError):
                    # Fall back to basic write without locking
                    f.write(content)
                    f.flush()
        except Exception as e:
            # Fall back to basic file write if locking fails
            print(f"Warning: File locking failed for {filepath}, using basic write: {e}")
            try:
                with open(filepath, 'w') as f:
                    f.write(content)
            except Exception as write_error:
                print(f"Error: Failed to write file {filepath}: {write_error}")
                raise

    @staticmethod
    def read_with_lock(filepath: str) -> str:
        """Read from file with shared lock"""
        if not os.path.exists(filepath):
            return ""

        try:
            with open(filepath) as f:
                # Try file locking if available (Unix systems)
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                    return f.read()
                except (AttributeError, OSError, TypeError):
                    # Fall back to basic read without locking
                    return f.read()
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
            return ""


class SubagentPool:
    """Genesis-inspired subagent pool manager (configurable concurrent limit)"""
    def __init__(self, max_subagents=5):
        self.semaphore = threading.Semaphore(max_subagents)
        self.active_count = 0
        self.lock = threading.Lock()

    def execute_with_limit(self, prompt, timeout=600, use_codex=False):
        """Execute claude -p with subagent limit enforcement"""
        with self.semaphore:
            with self.lock:
                self.active_count += 1
                print(f"  🤖 Claude -p call {self.active_count} active")

            try:
                return execute_claude_command(prompt, timeout, use_codex)
            finally:
                with self.lock:
                    self.active_count -= 1

# Global subagent pool (Genesis pattern: configurable concurrent limit, default 5)
SUBAGENT_POOL = SubagentPool(max_subagents=5)  # Default 5, can be overridden

def cerebras_call(prompt):
    """Simple wrapper for Cerebras API call"""
    return execute_claude_command(prompt, use_cerebras=True)

def execute_codex_command(prompt):
    """Execute command using Codex API"""
    return execute_claude_command(prompt, use_codex=True)

def smart_model_call(prompt):
    """Smart model wrapper - Codex by default, Claude if override flag."""
    use_codex = is_codex_enabled()  # Global flag affects all calls within single Genesis instance
    if use_codex:
        return execute_codex_command(prompt)
    return execute_claude_command(prompt, use_cerebras=False)

def execute_claude_command(prompt, timeout=600, use_codex=False, use_cerebras=False, iteration_token_count=None, workflow_state=None):
    """Execute claude, codex, or cerebras command with prompt and return output."""
    import time

    # TOKEN BURN PREVENTION: Use centralized constants
    # Check token budget if provided
    if iteration_token_count is not None and iteration_token_count > MAX_TOKENS_PER_ITERATION:
        print(f"🛑 TOKEN LIMIT EXCEEDED: {iteration_token_count} > {MAX_TOKENS_PER_ITERATION}")
        print("    Preventing infinite token burn - operation cancelled")
        return None

    # Check prompt length for context overflow
    if len(prompt) > MAX_PROMPT_LENGTH:
        print(f"🛑 CONTEXT OVERFLOW PREVENTION: Prompt length {len(prompt)} > {MAX_PROMPT_LENGTH}")
        print("    Truncating prompt to prevent context overflow...")
        prompt = prompt[:MAX_PROMPT_LENGTH] + "\n\n[PROMPT TRUNCATED DUE TO LENGTH - PROVIDE CONCISE RESPONSE]"

    # Log token usage and track in workflow_state if available
    estimated_tokens = len(prompt) // 4  # Rough token estimation
    current_iteration = 0
    if workflow_state is not None:
        current_iteration = getattr(workflow_state, 'iteration_count', 0)
        # Track token usage and enforce limit
        if not workflow_state.add_token_usage(estimated_tokens, current_iteration):
            print("🛑 TOKEN BUDGET EXCEEDED via workflow_state tracking")
            print("    Preventing infinite token burn - operation cancelled")
            return None
    print(f"📊 TOKEN USAGE: Estimated {estimated_tokens} input tokens, iteration total: {iteration_token_count or 0}")

    # Increase timeout for large prompts to prevent hanging
    if len(prompt) > 500:
        timeout = max(timeout, 1800)  # Minimum 30 minutes for large prompts
    if len(prompt) > 2000:
        timeout = max(timeout, 3600)  # Minimum 1 hour for very large prompts

    start_time = time.time()

    # Default to enhanced observability mode for better debugging
    verbose_mode = True
    debug_mode = True

    try:
        if use_codex:
            command = ["codex", "exec", "--yolo", "--skip-git-repo-check"]
            # Add maximum verbosity config overrides for codex
            if verbose_mode:
                command.extend(["-c", "verbose=true"])
                print("    🔊 CODEX: Maximum verbosity enabled", flush=True)
            if debug_mode:
                command.extend(["-c", "debug=true"])
                print("    🐛 CODEX: Debug mode enabled", flush=True)
            tool_name = "codex"
            input_method = "stdin"
        elif use_cerebras:
            # Use cerebras_direct.sh for fast generation
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".claude", "commands", "cerebras", "cerebras_direct.sh")
            if os.path.exists(script_path):
                command = ["bash", script_path, prompt]
                tool_name = "cerebras"
                input_method = "arg"
            else:
                # Fallback to claude if cerebras script not found
                # Use codex by default (controlled by is_codex_enabled())
                if is_codex_enabled():
                    command = ["codex", "exec", "--yolo"]
                    tool_name = "codex"
                    if verbose_mode:
                        print("    🔊 CODEX: Using Codex CLI (larger context)", flush=True)
                else:
                    command = ["claude", "-p", "--dangerously-skip-permissions", "--model", "sonnet"]
                    tool_name = "claude"
                    if verbose_mode:
                        command.extend(["--verbose"])
                        print("    🔊 CLAUDE: Maximum verbosity enabled (no streaming to prevent hangs)", flush=True)
                    if debug_mode:
                        command.extend(["--debug", "api,hooks,mcp"])
                        print("    🐛 CLAUDE: Full debug mode enabled (api,hooks,mcp)", flush=True)
                input_method = "stdin"
        # Use codex by default (controlled by is_codex_enabled())
        elif is_codex_enabled():
            command = ["codex", "exec", "--yolo"]
            tool_name = "codex"
            input_method = "stdin"
            if verbose_mode:
                print("    🔊 CODEX: Using Codex CLI (larger context)", flush=True)
        else:
            # Pass model flag and value as separate args so CLI parses it correctly
            command = ["claude", "-p", "--dangerously-skip-permissions", "--model", "sonnet"]
            if verbose_mode:
                command.extend(["--verbose"])
                print("    🔊 CLAUDE: Maximum verbosity enabled (no streaming to prevent hangs)", flush=True)
            if debug_mode:
                command.extend(["--debug", "api,hooks,mcp"])
                print("    🐛 CLAUDE: Full debug mode enabled (api,hooks,mcp)", flush=True)
            tool_name = "claude"
            input_method = "stdin"

        print(f"    🚀 EXECUTING {tool_name.upper()} COMMAND:")
        print(f"    └─ Command: {' '.join(command[:2])}...")
        print(f"    └─ Timeout: {timeout}s")
        print(f"    └─ Input method: {input_method}")

        # Setup environment for codex with proxy
        env = os.environ.copy()
        if use_codex:
            env['OPENAI_BASE_URL'] = 'http://localhost:10000'
            print(f"    └─ Using codex proxy: {env['OPENAI_BASE_URL']}")

        # Use streaming subprocess for real-time output in tmux
        print(f"🚀 EXECUTING: {' '.join(command)}", flush=True)
        print(f"📝 PROMPT LENGTH: {len(prompt)} characters", flush=True)
        print("═" * 60, flush=True)

        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE if input_method == "stdin" else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified streaming
            text=True,
            shell=False,
            env=env,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        output_lines = []

        # Send input if using stdin method
        if input_method == "stdin" and prompt:
            try:
                process.stdin.write(prompt)
                process.stdin.close()
            except Exception as e:
                print(f"❌ Error writing to stdin: {e}", flush=True)

        # Stream output in real-time with timeout and completion detection
        try:

            # Track streaming state
            last_output_time = time.time()
            stall_timeout = 300  # 5 minutes with no output = stall
            completion_keywords = ["CONVERGED", "OBJECTIVE ACHIEVED", "GENESIS COMPLETION", "FINAL ASSESSMENT"]
            lines_after_completion = -1  # -1 means no completion signal seen yet
            max_lines_after_completion = 20  # Allow 20 lines after completion signal

            while True:
                # Check overall timeout
                current_time = time.time()
                if current_time - start_time > timeout:
                    print(f"⚠️ TIMEOUT: Process exceeded {timeout}s limit, terminating...", flush=True)
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        print("⚠️ Force killing process...", flush=True)
                        process.kill()
                        process.wait()
                    break

                # Check for stalled streaming (no output for 5 minutes)
                if current_time - last_output_time > stall_timeout:
                    print(f"⚠️ STALL DETECTED: No output for {stall_timeout}s, terminating streaming...", flush=True)
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        print("⚠️ Force killing stalled process...", flush=True)
                        process.kill()
                        process.wait()
                    break

                # Use select to check if data is available (Unix/Linux/macOS)
                try:
                    ready, _, _ = select.select([process.stdout], [], [], 1.0)  # 1 second timeout
                    if not ready:
                        continue  # No data available, check timeouts again
                except (OSError, ValueError):
                    # select not available or process closed, fallback to blocking read
                    pass

                line = process.stdout.readline()
                if not line:
                    break

                last_output_time = current_time

                # Print line immediately for tmux visibility with proper escaping
                clean_line = line.rstrip().replace('\\n', '\n').replace('\\t', '\t')
                # Remove ANSI escape sequences for cleaner tmux output
                import re
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', clean_line)
                print(clean_line, flush=True)
                output_lines.append(line)

                # Check for completion keywords
                for keyword in completion_keywords:
                    if keyword in clean_line:
                        print(f"🎯 COMPLETION SIGNAL DETECTED: {keyword}", flush=True)
                        lines_after_completion = 0  # Reset counter
                        break

                # Count lines after completion signal
                if lines_after_completion >= 0:  # We've seen a completion signal
                    lines_after_completion += 1
                    if lines_after_completion > max_lines_after_completion:
                        print(f"🛑 TERMINATING: {max_lines_after_completion} lines after completion signal", flush=True)
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                        break

        except Exception as e:
            print(f"❌ Error reading output: {e}", flush=True)
            print(f"❌ Exception type: {type(e).__name__}", flush=True)
            import traceback
            print(f"❌ Full traceback: {traceback.format_exc()}", flush=True)

        # Wait for process completion with timeout
        try:
            return_code = process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            print("⚠️ Process did not terminate cleanly, force killing...", flush=True)
            process.kill()
            return_code = process.wait()

        # Create a result object that matches subprocess.run interface
        class StreamingResult:
            def __init__(self, returncode, stdout, stderr=""):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        result = StreamingResult(
            returncode=return_code,
            stdout=''.join(output_lines),
            stderr=""  # We merged stderr into stdout
        )

        end_time = time.time()
        duration = end_time - start_time

        print("    ⏱️  EXECUTION COMPLETED:")
        print(f"    └─ Duration: {duration:.2f}s")
        print(f"    └─ Return code: {result.returncode}")

        if result.returncode == 0:
            output = result.stdout.strip()
            print(f"    └─ Output size: {len(output)} characters")

            # Add output size limit to prevent runaway generation
            MAX_OUTPUT_SIZE = 100000  # 100KB limit
            if len(output) > MAX_OUTPUT_SIZE:
                print(f"    ⚠️  OUTPUT TRUNCATED: Response too large ({len(output)} chars > {MAX_OUTPUT_SIZE} limit)")
                output = output[:MAX_OUTPUT_SIZE] + "\n\n[TRUNCATED - Response exceeded 100KB limit]"
                print(f"    └─ Truncated to: {len(output)} characters")

            return output
        # Enhanced error diagnostics for codex failures
        full_output = result.stdout.strip()
        error_output = full_output if full_output else "No output captured"

        print(f"    └─ Error: {error_output}")
        print(f"    └─ Full stdout: {repr(full_output)}")

        # Specific codex error pattern detection
        if use_codex:
            print("    🔍 CODEX ERROR ANALYSIS:")
            if "Broken pipe" in full_output:
                print("    └─ Issue: Broken pipe - codex process terminated unexpectedly")
                print("    └─ Check: Is codex proxy running on localhost:10000?")
            elif "Not inside a trusted directory" in full_output:
                print("    └─ Issue: Git trust directory error")
                print("    └─ Solution: Using --skip-git-repo-check flag")
            elif "permission" in full_output.lower():
                print("    └─ Issue: Permission error")
            elif "connection" in full_output.lower() or "refused" in full_output.lower():
                print("    └─ Issue: Connection error to codex proxy")
                print("    └─ Check: curl http://localhost:10000/health")
            else:
                print("    └─ Issue: Unknown codex error - see full output above")

        print(f"Error running {tool_name}: {error_output}")
        return None
    except subprocess.TimeoutExpired:
        end_time = time.time()
        duration = end_time - start_time
        print("    ⏱️  EXECUTION TIMED OUT:")
        print(f"    └─ Duration: {duration:.2f}s (exceeded {timeout}s limit)")
        print(f"{tool_name.title()} command timed out")
        return None
    except FileNotFoundError:
        print(
            f"Error: '{tool_name}' command not found. Please install {tool_name.title()} CLI."
        )
        sys.exit(1)
    except Exception as e:
        print(f"Error running {tool_name}: {e}")
        return None

# Remove duplicate - using original execute_claude_command

def set_subagent_pool_size(size):
    """Update global subagent pool size"""
    global SUBAGENT_POOL
    SUBAGENT_POOL = SubagentPool(max_subagents=size)


def detect_goal_ambiguities(refined_goal, exit_criteria):
    """Light-touch ambiguity detection for Genesis goals (Spec Kit integration).

    Returns warning message if ambiguities detected, None otherwise.
    """
    # Ambiguity patterns that indicate unclear requirements
    ambiguity_patterns = [
        "implement something",
        "add feature",
        "make it work",
        "TODO",
        "placeholder",
        "FIXME",
        "TBD",
        "to be determined",
        "needs clarification",
        "[NEEDS CLARIFICATION",
        "figure out",
        "somehow",
        "maybe",
        "possibly",
        "some kind of",
        "etc.",
        "and so on",
        "various",
        "different",
        "appropriate",
        "proper",
        "correct",
        "good",
        "better",
        "optimal",
        "efficient",
        "fast",
        "secure",
        "scalable",
        "robust"
    ]

    combined_text = f"{refined_goal} {exit_criteria}".lower()

    detected_ambiguities = []
    for pattern in ambiguity_patterns:
        if pattern.lower() in combined_text:
            detected_ambiguities.append(pattern)

    # Check for missing concrete specifications
    if not any(keyword in combined_text for keyword in ["must", "shall", "will", "specific", "exactly"]):
        detected_ambiguities.append("missing concrete specifications")

    # Check for vague success criteria
    if "success" in combined_text and not any(metric in combined_text for metric in ["test", "pass", "fail", "measure", "verify", "validate"]):
        detected_ambiguities.append("vague success criteria")

    if detected_ambiguities:
        return f"AMBIGUITY WARNING: Detected unclear requirements: {', '.join(detected_ambiguities[:5])}. Consider running /clarify command for better results."

    return None


def load_goal_from_directory(goal_dir):
    """Load goal specification from goal directory structure."""
    print(f"📂 LOADING GOAL FROM DIRECTORY: {goal_dir}", flush=True)

    if goal_dir is None:
        print("❌ Error: Goal directory is None", flush=True)
        return None, None

    # Validate goal directory path length before attempting filesystem operations
    if len(goal_dir) > 200:
        print(f"❌ Error: Goal directory path too long ({len(goal_dir)} chars > 200 limit)", flush=True)
        print("💡 Hint: Use --refine mode for long descriptions:", flush=True)
        print("   python genesis/genesis.py --refine 'short description' [iterations]", flush=True)
        print("💡 Or create a proper goal directory with short name:", flush=True)
        print("   mkdir goals/2025-09-22-debug-codex && populate with goal files", flush=True)
        return None, None

    goal_path = Path(goal_dir)

    try:
        if not goal_path.exists():
            print(f"❌ Error: Goal directory not found: {goal_dir}", flush=True)
            return None, None
    except OSError as e:
        if e.errno == 63:  # File name too long
            print("❌ Error: Goal directory name too long for filesystem", flush=True)
            print("💡 Use --refine mode: python genesis/genesis.py --refine 'description' [iterations]", flush=True)
            return None, None
        print(f"❌ Error accessing goal directory: {e}", flush=True)
        return None, None

    print("✅ Goal directory exists, checking files...", flush=True)

    # Load goal definition
    goal_def_file = goal_path / "00-goal-definition.md"
    criteria_file = goal_path / "01-success-criteria.md"

    print(f"📄 Goal definition file: {goal_def_file} (exists: {goal_def_file.exists()})", flush=True)
    print(f"📄 Success criteria file: {criteria_file} (exists: {criteria_file.exists()})", flush=True)

    refined_goal = ""
    exit_criteria = ""

    try:
        if goal_def_file.exists():
            print("📖 Reading goal definition file...", flush=True)
            with open(goal_def_file) as f:
                content = f.read()
                print(f"📊 Goal definition content length: {len(content)} characters", flush=True)
                # Extract refined goal from markdown
                lines = content.split("\n")
                print(f"📝 Processing {len(lines)} lines to find refined goal...", flush=True)
                for i, line in enumerate(lines):
                    if (
                        "refined goal" in line.lower()
                        or "specification" in line.lower()
                    ):
                        print(f"🎯 Found goal section at line {i}: {line[:50]}...", flush=True)
                        # Take next few lines as the goal
                        goal_lines = []
                        for j in range(i + 1, min(i + 10, len(lines))):
                            if lines[j].strip() and not lines[j].startswith("#"):
                                goal_lines.append(lines[j].strip())
                        refined_goal = " ".join(goal_lines)
                        print(f"✅ Extracted refined goal: {len(refined_goal)} characters", flush=True)
                        break

                if not refined_goal:
                    print("⚠️  No 'refined goal' section found, using fallback...", flush=True)
                    # Fallback: take first meaningful paragraph
                    for line in lines:
                        if len(line.strip()) > 20 and not line.startswith("#"):
                            refined_goal = line.strip()
                            print(f"📝 Using fallback goal: {refined_goal[:100]}...", flush=True)
                            break

        if criteria_file.exists():
            print("📖 Reading success criteria file...", flush=True)
            with open(criteria_file) as f:
                exit_criteria = f.read()
                print(f"📊 Success criteria content length: {len(exit_criteria)} characters", flush=True)

        print(f"✅ Goal loading complete. Goal: {len(refined_goal)} chars, Criteria: {len(exit_criteria)} chars", flush=True)

        # Light-touch ambiguity detection (Spec Kit integration)
        ambiguity_result = detect_goal_ambiguities(refined_goal, exit_criteria)
        if ambiguity_result:
            print(f"⚠️  {ambiguity_result}", flush=True)

        return refined_goal, exit_criteria

    except Exception as e:
        print(f"❌ Error loading goal files: {e}", flush=True)
        return None, None


def generate_goal_files_fast(goal_description, goal_dir):
    """Use cerebras_direct.sh to generate all goal files at once (fast generation)"""
    prompt = f"""Generate complete goal directory structure for: {goal_description}

Create these files for proto_genesis workflow:

1. 00-goal-definition.md - Goal definition with refined goal analysis
2. 01-success-criteria.md - Clear success criteria and exit conditions
3. 02-implementation-notes.md - Technical approach and considerations
4. 03-testing-strategy.md - How to validate the implementation

Each file should be complete and detailed. Format as:

=== 00-goal-definition.md ===
[Complete markdown content]

=== 01-success-criteria.md ===
[Complete markdown content]

=== 02-implementation-notes.md ===
[Complete markdown content]

=== 03-testing-strategy.md ===
[Complete markdown content]

Generate all files now:"""

    try:
        # Use cerebras_direct.sh for fast generation
        output = execute_claude_command(prompt, timeout=60, use_cerebras=True)

        if output:
            # Parse and write files
            os.makedirs(goal_dir, exist_ok=True)

            # Split by file markers and write each file
            sections = output.split("=== ")
            for section in sections[1:]:  # Skip first empty section
                if " ===" in section:
                    filename, content = section.split(" ===", 1)
                    filepath = os.path.join(goal_dir, filename.strip())
                    with open(filepath, "w") as f:
                        f.write(content.strip())
                    print(f"✅ Generated: {filename.strip()}")

            return True
        print("❌ Fast generation failed")
        return False

    except Exception as e:
        print(f"❌ Fast generation error: {e}")
        return False


def refine_goal_interactive(original_goal, use_codex=False):
    """Interactive goal refinement (only used with --refine flag)."""
    print("🎯 STARTING GOAL REFINEMENT...", flush=True)
    print(f"📊 Goal length: {len(original_goal)} characters", flush=True)
    print(f"🔧 Using codex: {use_codex}", flush=True)

    prompt = f"""Please refine this goal into a clear, specific technical specification for a coder to implement:

Original Goal: "{original_goal}"

Please provide:
1. Refined Goal: A specific, technical description of what needs to be built
2. Exit Criteria: Clear, measurable conditions that define when this goal is complete (at least 3 criteria)

Format your response as:
REFINED GOAL: [specific technical description]

EXIT CRITERIA:
- [criterion 1]
- [criterion 2]
- [criterion 3]
"""

    print(f"📝 Prompt length: {len(prompt)} characters", flush=True)
    print("🚀 Executing refinement with Cerebras...", flush=True)

    result = execute_claude_command(prompt, use_codex=use_codex, use_cerebras=True)

    print(f"✅ Refinement completed. Result length: {len(result) if result else 0} characters", flush=True)
    return result


def parse_refinement(response):
    """Parse the goal refinement response - handles both Claude and Cerebras formats."""
    if not response:
        return None, None

    refined_goal = None
    exit_criteria = None

    # Clean up Cerebras performance metrics and file paths
    # Remove lines starting with 🚀, "Output saved to:", and markdown timestamp headers
    clean_lines = []
    for line in response.split('\n'):
        line = line.strip()
        if (line.startswith('🚀') or
            line.startswith('Output saved to:') or
            line.startswith('## Assistant (') or
            line.startswith('<Claude.') or
            line.startswith('</Claude.')):
            continue
        clean_lines.append(line)

    cleaned_response = '\n'.join(clean_lines).strip()

    # Multiple parsing strategies for different response formats

    # Strategy 1: Look for explicit "REFINED GOAL:" format
    goal_match = re.search(
        r"^\s*REFINED\s+GOAL\s*:\s*(.+)", cleaned_response, re.IGNORECASE | re.MULTILINE
    )
    if goal_match:
        refined_goal = goal_match.group(1).strip()

    # Strategy 2: If no explicit format, use the entire cleaned response as refined goal
    # This handles cases where Cerebras returns the refined goal directly without headers
    if not refined_goal and cleaned_response:
        # Filter out empty lines and very short lines
        substantial_lines = [line for line in clean_lines if line.strip() and len(line.strip()) > 10]
        if substantial_lines:
            # Use the first substantial content as the refined goal
            refined_goal = '\n'.join(substantial_lines).strip()

    # Strategy 3: Fallback - if still no goal, extract from any meaningful content
    if not refined_goal and response:
        # Last resort: clean the original response more aggressively
        fallback_lines = []
        for line in response.split('\n'):
            line = line.strip()
            if (line and
                not line.startswith('🚀') and
                not line.startswith('Output saved to:') and
                not line.startswith('## Assistant') and
                not line.startswith('#') and
                len(line) > 20):
                fallback_lines.append(line)

        if fallback_lines:
            refined_goal = '\n'.join(fallback_lines[:5]).strip()  # Take first 5 meaningful lines

    # Find exit criteria section
    criteria_match = re.search(
        r"^\s*EXIT\s+CRITERIA\s*:\s*(.+)",
        cleaned_response,
        re.IGNORECASE | re.MULTILINE | re.DOTALL,
    )
    if criteria_match:
        # Get everything from the match start to end of response
        start_pos = criteria_match.start()
        exit_criteria = cleaned_response[start_pos:].strip()

    return refined_goal, exit_criteria


def summarize_for_next_stage(stage_name, stage_output, goal, iteration_num, use_codex=False):
    """Genesis pattern: Detailed summary with 2000 token max (enhanced context)"""
    prompt = f"""GENESIS CONTEXT ENHANCEMENT - FULL STATUS SUMMARY

STAGE: {stage_name} | ITERATION: {iteration_num}
GOAL: {goal}

OUTPUT TO SUMMARIZE:
{stage_output}

CLEARLY SUMMARIZE THE FULL STATUS (TARGET ~2000 TOKENS; USE ALL AVAILABLE DETAILS):
KEY DECISIONS: [critical decisions only]
ESSENTIAL FINDINGS: [key discoveries only]
NEXT FOCUS: [single priority item]
CONTEXT: [minimal essential only]

GENESIS RULE: Expand the status summary to the fullest extent possible up to 2000 tokens. Note if content is insufficient to reach the target length.
"""

    return execute_claude_command(prompt, timeout=600, use_codex=use_codex)


def update_plan_document(goal_dir, learnings, iteration_num, use_codex=False):
    """Genesis pattern: Maintain living @fix_plan.md with priority scoring"""
    from pathlib import Path

    if goal_dir is None:
        return ""  # Return empty string if no goal directory available

    plan_file = Path(goal_dir) / "fix_plan.md"
    existing_plan = ""

    if plan_file.exists():
        try:
            with open(plan_file) as f:
                existing_plan = f.read()
        except Exception:
            existing_plan = ""

    prompt = f"""GENESIS PLAN MAINTENANCE - PRIORITY SCORING

ITERATION: {iteration_num}
CURRENT PLAN:
{existing_plan}

NEW LEARNINGS:
{learnings}

GENESIS REQUIREMENTS:
1. Remove completed items (✅ status)
2. Add newly discovered tasks
3. PRIORITY SCORE each item (1-10, 10=critical)
4. Reorder by priority score (highest first)
5. Mark dependencies and blockers
6. Keep actionable (no vague items)

FORMAT:
## Priority 10 (Critical)
- [ ] Specific task description

## Priority 9 (High)
- [ ] Another task

Return updated fix_plan.md:
"""

    updated_plan = execute_claude_command(prompt, timeout=600, use_codex=use_codex)

    if updated_plan and plan_file.parent.exists():
        try:
            with open(plan_file, "w") as f:
                f.write(updated_plan)
        except Exception as e:
            print(f"Warning: Could not update fix_plan.md: {e}")

    return updated_plan


def validate_single_task_focus(strategy_text):
    """Genesis enforcement: Validate strategy focuses on ONE task only"""
    multi_task_indicators = [
        "and also", "additionally", "next we", "then do", "while doing",
        "simultaneously", "in parallel", "at the same time", "multiple"
    ]

    for indicator in multi_task_indicators:
        if indicator.lower() in strategy_text.lower():
            return False, f"REJECTED: Multi-task detected ({indicator}). Genesis requires ONE task per loop."

    # Check for numbered lists with multiple items
    lines = strategy_text.split('\n')
    task_lines = [line for line in lines if re.match(r'^\s*[0-9]+\.|^\s*[-*]', line)]
    if len(task_lines) > 1:
        return False, "REJECTED: Multiple numbered/bulleted tasks detected. Genesis requires ONE task per loop."

    return True, "APPROVED: Single task focus validated"

def generate_execution_strategy(
    refined_goal, iteration_num, previous_summary="", plan_context="", use_codex=False
):
    """Genesis pattern: Generate single-focus strategy with validation using user simulation"""

    # Load jleechan simulation prompt for authentic command prediction - but skip for Cerebras and Codex
    simulation_prompt = ""
    # Switch from Cerebras to claude -p user mimicry after iteration 2 (TDD phase)
    use_cerebras = iteration_num <= 2

    if not use_cerebras and not use_codex:  # Only load user simulation for Claude (non-Cerebras, non-Codex)
        try:
            simulation_file = Path(__file__).parent / "jleechan_simulation_prompt.md"
            if simulation_file.exists():
                simulation_prompt = simulation_file.read_text()
                print(f"  📋 Loaded detailed user simulation prompt: {len(simulation_prompt)} characters")
            else:
                print(f"  ⚠️  User simulation prompt not found at {simulation_file}")
        except Exception as e:
            print(f"  ⚠️  Error loading simulation prompt: {e}")
    elif use_codex:
        print("  🔧 Skipping user simulation prompt for Codex (direct instruction mode)")
    else:
        print("  🚀 Skipping user simulation prompt for Cerebras (fast generation mode)")

    # Use different prompt structure for Cerebras vs Claude vs Codex
    if use_cerebras:
        prompt_header = "GENESIS PRIMARY SCHEDULER - FAST CEREBRAS GENERATION"
    elif use_codex:
        prompt_header = "GENESIS PRIMARY SCHEDULER - DIRECT CODEX EXECUTION"
    else:
        prompt_header = "GENESIS PRIMARY SCHEDULER - SINGLE TASK ENFORCEMENT WITH USER SIMULATION"

    # Build dynamic prompt based on agent type
    if use_codex:
        # Codex-specific prompt - no jleechan simulation, no slash commands
        prompt = f"""{prompt_header}

CODEX EXECUTION PRINCIPLES:
- ONE ITEM PER LOOP: Choose exactly ONE specific task (validation enforced)
- DIRECT IMPLEMENTATION: Write code directly, no command delegation
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens
- NO PLACEHOLDERS: Full implementations only
- AUTONOMOUS BREAKDOWN: Intelligently decompose complex goals into manageable tasks

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}
PREVIOUS SUMMARY: {previous_summary}

🎯 LARGE GOAL BREAKDOWN STRATEGY:
When facing complex/comprehensive goals (like "comprehensive testing"):
1. IDENTIFY core components of the goal
2. PRIORITIZE the most fundamental component first
3. SELECT ONE specific, implementable task from that component
4. ENSURE the task can be completed in a single iteration

SCHEDULER REQUIREMENTS:
1. SELECT ONE SPECIFIC ITEM from plan context (if available)
2. REJECT multi-tasking (will be validated)
3. PROVIDE direct implementation approach
4. DEMAND full implementation (no TODOs)
5. BREAK DOWN large goals into incremental progress

EXECUTION STRATEGY FORMAT:
SINGLE FOCUS: [ONE specific task only - if goal is large, pick first logical component]
EXECUTION PLAN: [direct implementation approach]
SUCCESS CRITERIA: [clear completion criteria]
NO PLACEHOLDERS: [enforcement approach]
INCREMENTAL PROGRESS: [how this task contributes to larger goal]

GENESIS VALIDATION: Strategy will be rejected if multiple tasks detected.
AUTONOMOUS GUIDANCE: For large goals, start with foundation/setup tasks first.

OUTPUT REQUIREMENTS: Keep response to 2-3 sentences maximum. Be direct and specific about what code to write or task to complete.
"""
    else:
        # Claude-specific prompt - includes jleechan simulation and slash commands
        prompt = f"""{simulation_prompt}

{prompt_header}

GENESIS PRINCIPLES FOR AUTONOMOUS DEVELOPMENT:
- ONE ITEM PER LOOP: Choose exactly ONE specific task (validation enforced)
- DIRECT EXECUTION: Use claude -p directly for all work
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens
- NO PLACEHOLDERS: Full implementations only
- AUTONOMOUS BREAKDOWN: Intelligently decompose complex goals into manageable tasks

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}
PREVIOUS SUMMARY: {previous_summary}

🎯 LARGE GOAL BREAKDOWN STRATEGY:
When facing complex/comprehensive goals (like "comprehensive testing"):
1. IDENTIFY core components of the goal
2. PRIORITIZE the most fundamental component first
3. SELECT ONE specific, implementable task from that component
4. ENSURE the task can be completed in a single iteration

Example breakdown approach:
- Large Goal: "Comprehensive testing framework with 12 criteria"
- Iteration 1: "Set up basic proxy connectivity testing"
- Iteration 2: "Implement agent invocation testing"
- Iteration 3: "Add performance metrics collection"
- Continue until all components addressed...

SCHEDULER REQUIREMENTS:
1. SELECT ONE SPECIFIC ITEM from plan context (if available)
2. REJECT multi-tasking (will be validated)
3. SPECIFY how to use claude -p subagents (max 5)
4. DEMAND full implementation (no TODOs)
5. BREAK DOWN large goals into incremental progress

SUBAGENT DELEGATION PATTERN:
- Code generation → claude -p subagent
- Testing/validation → claude -p subagent
- File operations → claude -p subagent
- Keep primary context as scheduler only

EXECUTION STRATEGY FORMAT:
SINGLE FOCUS: [ONE specific task only - if goal is large, pick first logical component]
EXECUTION PLAN: [how to use claude -p directly]
SUCCESS CRITERIA: [clear completion criteria]
NO PLACEHOLDERS: [enforcement approach]
INCREMENTAL PROGRESS: [how this task contributes to larger goal]

GENESIS VALIDATION: Strategy will be rejected if multiple tasks detected.
AUTONOMOUS GUIDANCE: For large goals, start with foundation/setup tasks first.

OUTPUT REQUIREMENTS: Keep response to 2-3 sentences maximum. Use slash commands (like /execute, /fixpr) when appropriate for the predicted task. Be direct and actionable like jleechan's typical commands.
"""

    print("  📤 SENDING PROMPT TO CLAUDE:")
    print(f"  └─ Prompt length: {len(prompt)} characters")
    print(f"  └─ Using codex: {use_codex}")
    print("  └─ Timeout: 600s")

    # Log execution plan to human-readable log
    if 'human_logger' in globals():
        human_logger.log_execution_plan(
            f"Generating strategy via user simulation ({len(prompt)} chars)",
            prompt[:500]  # First 500 chars of prompt
        )

    strategy = execute_claude_command(prompt, use_codex=use_codex, use_cerebras=True)

    print("  📥 CLAUDE RESPONSE RECEIVED:")
    if strategy:
        print(f"  └─ Response length: {len(strategy)} characters")
        print(f"  └─ First 200 chars: {strategy[:200]}...")

        is_valid, validation_msg = validate_single_task_focus(strategy)
        print(f"  🎯 Task Focus Validation: {validation_msg}")

        if not is_valid:
            print("  🔄 Regenerating strategy with stricter single-task enforcement...")
            print("  📤 SENDING STRICTER PROMPT TO CLAUDE:")
            # Retry with stricter prompt
            strict_prompt = f"""{prompt}

STRICT ENFORCEMENT: Previous strategy rejected for multi-tasking.
MUST focus on EXACTLY ONE TASK. No exceptions.
"""
            print(f"  └─ Stricter prompt length: {len(strict_prompt)} characters")
            strategy = execute_claude_command(strict_prompt, use_codex=use_codex, use_cerebras=True)

            if strategy:
                print("  📥 CLAUDE RETRY RESPONSE RECEIVED:")
                print(f"  └─ Retry response length: {len(strategy)} characters")
    else:
        print("  ❌ No response received from Claude")

    return strategy


def validate_task_necessity(task_description, goal_dir):
    """Genesis pattern: Search-first approach - verify gap exists before building"""
    search_prompt = f"""GENESIS SEARCH-FIRST VALIDATION

TASK TO VALIDATE: {task_description}
GOAL DIRECTORY: {goal_dir}

SEARCH REQUIREMENTS:
1. Check for existing implementations
2. Look for TODO/placeholder patterns
3. Verify gap actually exists
4. Check for similar functionality

SEARCH PATTERN:
- Use find/grep to search codebase
- Check relevant files and directories
- Look for partial implementations

RETURN:
GAP EXISTS: [true/false]
EVIDENCE: [what was found/not found]
RECOMMENDATION: [proceed/skip/modify task]
"""

    return execute_claude_command(search_prompt, timeout=600)

def validate_implementation_quality(work_output):
    """Genesis pattern: Track TODOs for later completion instead of rejecting"""
    placeholder_patterns = {
        'TODO': r'TODO',
        'FIXME': r'FIXME',
        'PLACEHOLDER': r'PLACEHOLDER',
        'XXX': r'XXX',
        'HACK': r'HACK',
        'NotImplemented': r'NotImplemented',
        'pass_comment': r'pass\s*#',
        'NotImplementedError': r'raise NotImplementedError',
        'comment_todo': r'// TODO|// FIXME|/\* TODO|<!-- TODO',
        'empty_function_python': r'def\s+\w+\([^)]*\):\s*pass\s*$',
        'empty_function_js': r'function\s+\w+\([^)]*\)\s*{\s*}',
    }

    detected_todos = []
    for name, pattern in placeholder_patterns.items():
        matches = re.finditer(pattern, work_output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            # Get line number and context
            line_num = work_output[:match.start()].count('\n') + 1
            line_start = work_output.rfind('\n', 0, match.start()) + 1
            line_end = work_output.find('\n', match.end())
            if line_end == -1:
                line_end = len(work_output)
            line_content = work_output[line_start:line_end].strip()

            detected_todos.append({
                'type': name,
                'line': line_num,
                'content': line_content[:100]  # First 100 chars
            })

    if detected_todos:
        return True, f"APPROVED with {len(detected_todos)} TODO(s) tracked for later completion", detected_todos

    return True, "APPROVED: No TODOs detected", []

def make_progress(
    refined_goal,
    iteration_num,
    execution_strategy,
    plan_context="",
    use_codex=False,
    session_data=None,
):
    """Genesis pattern: Execute with search-first validation and subagent delegation"""

    # Genesis principle: Search first before assuming implementation needed
    print("  🔍 Genesis Search-First Validation...")
    task_validation = validate_task_necessity(execution_strategy, plan_context)

    # Build dynamic prompt based on agent type
    if use_codex:
        prompt = f"""GENESIS EXECUTION - SEARCH-FIRST DIRECT IMPLEMENTATION

CORE CODEX PRINCIPLES:
- ONE ITEM PER LOOP: Execute exactly one task (enforced)
- DIRECT IMPLEMENTATION: Write code directly, no delegation
- SEARCH FIRST: Validate before building (see validation below)
- NO PLACEHOLDERS: Full implementations only
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}

SEARCH VALIDATION RESULT:
{task_validation}

EXECUTION STRATEGY:
{execution_strategy}

CODEX EXECUTION REQUIREMENTS:
1. Honor search validation result above
2. Implement code directly without delegation
3. Write complete, working implementations
4. NO TODO/placeholder comments allowed
5. Full implementation or nothing

STRUCTURED OUTPUT:
SEARCH VALIDATION: [honored/ignored and why]
WORK COMPLETED: [specific accomplishments]
CODE WRITTEN: [what code was implemented directly]
FULL IMPLEMENTATION: [confirm no placeholders]
DISCOVERIES: [codebase learnings]
COMPLETION STATUS: [percentage for this iteration's focus]
NEXT PRIORITY: [single next focus item]

Execute using Codex principles now.
"""
    else:
        prompt = f"""GENESIS EXECUTION - SEARCH-FIRST WITH SUBAGENTS

CORE GENESIS PRINCIPLES:
- ONE ITEM PER LOOP: Execute exactly one task (enforced)
- SUBAGENT DELEGATION: Use claude -p for expensive work (max 5)
- SEARCH FIRST: Validate before building (see validation below)
- NO PLACEHOLDERS: Full implementations only
- CONTEXT ENHANCEMENT: Detailed context within 2000 tokens

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}

SEARCH VALIDATION RESULT:
{task_validation}

EXECUTION STRATEGY:
{execution_strategy}

GENESIS EXECUTION REQUIREMENTS:
1. Honor search validation result above
2. Use claude -p subagents for expensive work:
   - Code generation → claude -p subagent
   - Testing/validation → claude -p subagent
   - File operations → claude -p subagent
3. Primary context = scheduler only
4. NO TODO/placeholder comments allowed
5. Full implementation or nothing

STRUCTURED OUTPUT:
SEARCH VALIDATION: [honored/ignored and why]
WORK COMPLETED: [specific accomplishments]
CLAUDE CALLS: [what was executed with claude -p]
FULL IMPLEMENTATION: [confirm no placeholders]
DISCOVERIES: [codebase learnings]
COMPLETION STATUS: [percentage for this iteration's focus]
NEXT PRIORITY: [single next focus item]

Execute using Genesis principles now.
"""

    print("  📤 SENDING EXECUTION PROMPT TO CLAUDE:")
    print(f"  └─ Execution prompt length: {len(prompt)} characters")
    print(f"  └─ Goal: {refined_goal[:100]}...")
    print(f"  └─ Iteration: {iteration_num}")
    print(f"  └─ Using codex: {use_codex}")

    result = execute_claude_command(prompt, timeout=600, use_codex=use_codex)

    print("  📥 CLAUDE EXECUTION RESPONSE:")
    if result:
        print(f"  └─ Response length: {len(result)} characters")
        print(f"  └─ First 300 chars: {result[:300]}...")

        # Validate result quality and track TODOs
        is_quality, quality_msg, detected_todos = validate_implementation_quality(result)
        print(f"  🛡️ Implementation Quality: {quality_msg}")

        # Track TODOs for later completion instead of rejecting
        if detected_todos:
            print(f"  📝 Tracked {len(detected_todos)} TODO(s) for later completion:")
            for todo in detected_todos[:5]:  # Show first 5
                print(f"     └─ Line {todo['line']}: {todo['type']} - {todo['content'][:60]}...")

            # Store TODOs in session for later resolution
            if session_data is not None:
                if 'tracked_todos' not in session_data:
                    session_data['tracked_todos'] = []
                session_data['tracked_todos'].extend(detected_todos)

        # Continue with result (no longer blocking on TODOs)
    else:
        print("  ❌ No response received from Claude execution")

    return result


def check_consensus(refined_goal, exit_criteria, iteration_summary, plan_context="", use_codex=False):
    """Genesis-inspired consensus validation using subagent for focused assessment."""
    prompt = f"""You are a validation subagent in a Genesis-inspired system.

GENESIS VALIDATION PRINCIPLES:
- FOCUSED ASSESSMENT: Evaluate only this iteration's progress
- NO ASSUMPTION: Search/verify before concluding anything is missing
- EVIDENCE-BASED: Base assessment on concrete evidence
- CONTEXT ENHANCEMENT: Provide detailed evaluation within limits

GOAL: {refined_goal}

EXIT CRITERIA:
{exit_criteria}

THIS ITERATION'S WORK:
{iteration_summary}

CURRENT PLAN CONTEXT:
{plan_context}

VALIDATION REQUIREMENTS:
1. Use /goal --validate command to check against criteria
2. Assess ONLY this iteration's contribution to the overall goal
3. Identify concrete evidence of progress made with actual artifacts
4. Check if any exit criteria can now be marked as completed with proof
5. Determine if goal is complete or identify the single most important next step

🚨 COMPLETION ASSESSMENT (Genesis Self-Determination):
- If ALL exit criteria are satisfied with evidence: State "ALL EXIT CRITERIA SATISFIED"
- If implementation is 100% complete and functional: State "IMPLEMENTATION COMPLETE"
- If goal is achieved with end-to-end validation: State "OBJECTIVE ACHIEVED"
- If no critical gaps remain and everything works: State "NO CRITICAL GAPS REMAINING"

CONSENSUS ASSESSMENT:
ITERATION COMPLETION: [X% for this iteration's specific task]
OVERALL PROGRESS: [X% toward complete goal - if 100%, state "FULLY COMPLETE"]
CRITERIA VALIDATED: [which exit criteria are now satisfied - if all, state "ALL CRITERIA MET"]
EVIDENCE FOUND: [concrete proof of progress with file paths, test results, benchmarks]
CRITICAL GAPS: [specific remaining issues - if none, state "NONE - IMPLEMENTATION COMPLETE"]
END-TO-END STATUS: [full workflow validation status]
NEXT FOCUS: [specific next item, or "GENESIS COMPLETION - NO FURTHER WORK NEEDED"]

Use /goal --validate and provide evidence-based assessment.
"""

    return execute_claude_command(prompt, timeout=600, use_codex=use_codex)


def check_goal_completion(consensus_response, exit_criteria):
    """
    Genesis Self-Determination: Analyze consensus response for completion signals.

    Returns True if Genesis determines the goal is complete based on:
    1. Explicit completion statements in consensus
    2. High overall progress (>=95%)
    3. All critical exit criteria satisfied
    4. No critical gaps identified
    """
    if not consensus_response or not isinstance(consensus_response, str):
        return False

    # Limit input size to prevent regex performance issues
    if len(consensus_response) > 50000:  # 50KB limit
        consensus_response = consensus_response[:50000]

    response_lower = consensus_response.lower()

    # 🚨 ANTI-MOCK VALIDATION - Check for mock patterns first
    mock_indicators = [
        "mock execution result", "mock response", "placeholder implementation",
        "todo", "fixme", "not implemented", "hardcoded", "fake", "stub",
        "return mock_", "mock_data", "demo response", "sample output",
        "test response", "dummy", "example only", "for demonstration"
    ]

    if any(mock in response_lower for mock in mock_indicators):
        print("🚨 MOCK IMPLEMENTATION DETECTED - Goal NOT complete")
        print(f"   └─ Mock indicators found: {[mock for mock in mock_indicators if mock in response_lower]}")
        return False

    # Check for explicit completion indicators
    completion_signals = [
        "goal completed", "100% complete", "fully implemented",
        "all criteria satisfied", "implementation complete",
        "objective achieved", "requirements met", "task accomplished",
        "fully operational", "production ready", "fully functional"
    ]

    if any(signal in response_lower for signal in completion_signals):
        print("🔍 Completion signal detected in consensus response")
        # Additional validation - must also have evidence of real work
        if "working code" in response_lower or "functional implementation" in response_lower:
            return True
        print("⚠️ Completion claimed but no working code evidence - requiring more validation")
        return False

    # Parse progress percentages with robust error handling
    progress_patterns = [
        r"overall progress[:\s]+(\d+)%",       # "Overall progress: 98%"
        r"(\d+)%.*?toward.*?complet",          # "95% progress toward completion" (flexible)
        r"progress[:\s]+(\d+)%"                # "Progress: 95%"
    ]

    for pattern in progress_patterns:
        try:
            matches = re.findall(pattern, response_lower)
            if matches:
                for match in matches:
                    try:
                        progress = int(match)
                        if progress >= 95:  # Consistent threshold
                            print(f"🔍 High progress detected: {progress}%")
                            return True
                    except (ValueError, TypeError):
                        continue  # Skip invalid numeric conversions
        except re.error:
            continue  # Skip invalid regex patterns

    # Check for critical gaps - if none mentioned, likely complete
    if "critical gaps: none" in response_lower or "no critical gaps" in response_lower:
        print("🔍 No critical gaps remaining")
        return True

    # Check if consensus explicitly says all exit criteria are met
    if "all exit criteria" in response_lower and ("satisfied" in response_lower or "met" in response_lower):
        print("🔍 All exit criteria satisfied")
        return True

    return False


def append_genesis_learning(goal_dir, iteration_num, learning_note):
    """Append fallback learning entry to GENESIS.md when automation fails."""
    from pathlib import Path

    if goal_dir is None:
        return  # Skip if no goal directory available

    genesis_file = Path(goal_dir) / "GENESIS.md"
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    header = "# Genesis Learnings\n\n" if not genesis_file.exists() else ""
    entry_header = f"### Iteration {iteration_num} - {timestamp}\n"
    entry_body = f"- {learning_note}\n"

    try:
        if not genesis_file.parent.exists():
            genesis_file.parent.mkdir(parents=True, exist_ok=True)

        with open(genesis_file, "a") as f:
            if header:
                f.write(header)
            f.write(entry_header)
            f.write(entry_body)
    except Exception as e:
        print(f"Warning: Could not append to GENESIS.md: {e}")


def update_genesis_instructions(goal_dir, learnings, use_codex=False, iteration_num=None):
    """Genesis pattern: Update GENESIS.md with self-improvement learnings"""
    from pathlib import Path

    if goal_dir is None:
        return None  # Skip if no goal directory available

    genesis_file = Path(goal_dir) / "GENESIS.md"
    existing_instructions = ""

    if genesis_file.exists():
        try:
            with open(genesis_file) as f:
                existing_instructions = f.read()
        except Exception:
            existing_instructions = ""

    prompt = f"""GENESIS SELF-IMPROVEMENT - UPDATE GENESIS.md

CURRENT GENESIS INSTRUCTIONS:
{existing_instructions}

NEW LEARNINGS FROM ITERATION:
{learnings}

UPDATE GENESIS.md WITH:
1. Successful claude -p command patterns that worked
2. Failure modes to avoid (what caused loops/blocks)
3. Better approaches discovered during execution
4. Specific subagent delegation patterns that were effective
5. Context optimization techniques learned
6. Genesis principle applications that succeeded/failed

FORMAT:
## Successful Patterns
- [specific commands/approaches that worked]

## Avoid These Patterns
- [what causes failures/loops]

## Genesis Optimizations
- [context conservation techniques]
- [subagent delegation improvements]

KEEP BRIEF and actionable. Focus on improving future iterations.

Return updated GENESIS.md content:
"""

    updated_instructions = execute_claude_command(prompt, timeout=600, use_codex=use_codex)

    if updated_instructions and genesis_file.parent.exists():
        try:
            with open(genesis_file, "w") as f:
                f.write(updated_instructions)
        except Exception as e:
            print(f"Warning: Could not update GENESIS.md: {e}")
    elif genesis_file.parent.exists() and iteration_num is not None:
        append_genesis_learning(
            goal_dir,
            iteration_num,
            "Automation failed to refresh GENESIS.md; captured learnings manually.",
        )

    return updated_instructions

def detect_loop_back_opportunities(consensus_response, goal_dir):
    """Genesis pattern: Create loop-back when failures detected"""
    loop_back_triggers = [
        "build fail", "test fail", "error", "exception", "timeout",
        "not found", "missing", "incomplete", "broken", "stuck"
    ]

    needs_loop_back = any(trigger in consensus_response.lower() for trigger in loop_back_triggers)

    if needs_loop_back:
        loop_back_prompt = f"""GENESIS LOOP-BACK RECOVERY

FAILURE DETECTED IN: {consensus_response}
GOAL DIRECTORY: {goal_dir}

LOOP-BACK OPPORTUNITIES:
1. Add additional logging for debugging
2. Compile and examine build output
3. Run tests and analyze failure patterns
4. Check dependencies and environment
5. Examine error logs and stack traces

CREATE RECOVERY STRATEGY:
- What specific logging to add
- What compilation/build commands to run
- What tests to examine
- How to get more diagnostic information

Return concrete loop-back actions to take:
"""

        return execute_claude_command(loop_back_prompt, timeout=600)

    return None

def generate_tdd_implementation(
    refined_goal, iteration_num, execution_strategy, plan_context="", use_codex=False, session_data=None
):
    """Genesis pattern: Generate comprehensive TDD tests and implementation using Cerebras direct."""

    prompt = f"""GENESIS TDD GENERATION - COMPREHENSIVE TESTS AND IMPLEMENTATION

CORE GENESIS PRINCIPLES:
- COMPREHENSIVE TESTING: Generate complete test suite covering all edge cases
- FULL IMPLEMENTATION: Provide complete, working implementation (no placeholders)
- TDD METHODOLOGY: Tests drive implementation design and validation
- PRODUCTION READY: Code should be deployable and maintainable

GOAL: {refined_goal}
ITERATION: {iteration_num}
PLAN CONTEXT: {plan_context}

EXECUTION STRATEGY:
{execution_strategy}

TDD GENERATION REQUIREMENTS:
1. COMPREHENSIVE TEST SUITE:
   - Unit tests for all core functionality
   - Integration tests for system interactions
   - Edge case and error condition tests
   - Performance and security tests where applicable
   - Mock/stub external dependencies appropriately

2. COMPLETE IMPLEMENTATION:
   - Full working code that passes all generated tests
   - Proper error handling and edge case management
   - Clean, maintainable code following best practices
   - Documentation and type hints where applicable
   - Integration with existing codebase patterns

3. STRUCTURED OUTPUT FORMAT:
   ```
   # TDD TEST SUITE
   [Complete test code here]

   # IMPLEMENTATION
   [Complete implementation code here]

   # INTEGRATION NOTES
   [How to integrate with existing codebase]

   # VALIDATION CHECKLIST
   [Steps to verify implementation works]
   ```

GENESIS TDD METHODOLOGY:
- Write comprehensive tests first that define expected behavior
- Implement code that makes all tests pass
- Ensure no TODO or placeholder comments
- Include proper error handling and logging
- Follow existing codebase patterns and conventions

Generate the complete TDD test suite and implementation now:
"""

    print("  📋 SENDING TDD GENERATION PROMPT TO CEREBRAS:")
    print(f"  └─ Prompt length: {len(prompt)} characters")
    print(f"  └─ Goal: {refined_goal[:100] if refined_goal else 'None'}...")
    print(f"  └─ Iteration: {iteration_num}")
    print("  └─ Using Cerebras direct for high-speed generation")

    # Log TDD generation to human-readable log
    if 'human_logger' in globals():
        human_logger.log_execution_plan(
            f"Generating TDD suite via Cerebras ({len(prompt)} chars)",
            prompt[:500]  # First 500 chars of prompt
        )

    # Use Cerebras for fast TDD generation
    tdd_response = execute_claude_command(prompt, use_codex=use_codex, use_cerebras=True, timeout=1200)

    print("  📤 CEREBRAS TDD RESPONSE RECEIVED:")
    if tdd_response:
        print(f"  └─ Response length: {len(tdd_response)} characters")
        print(f"  └─ First 200 chars: {tdd_response[:200]}...")

        # Validate TDD response quality and track TODOs
        is_quality, quality_msg, detected_todos = validate_implementation_quality(tdd_response)
        print(f"  🛡️ TDD Quality Validation: {quality_msg}")

        # Track TODOs for later completion instead of rejecting
        if detected_todos:
            print(f"  📝 Tracked {len(detected_todos)} TODO(s) in TDD for later completion:")
            for todo in detected_todos[:5]:  # Show first 5
                print(f"     └─ Line {todo['line']}: {todo['type']} - {todo['content'][:60]}...")

            # Store TODOs in session for later resolution
            if session_data is not None:
                if 'tracked_todos' not in session_data:
                    session_data['tracked_todos'] = []
                for todo in detected_todos:
                    todo['source'] = 'TDD'
                session_data['tracked_todos'].extend(detected_todos)

        # Continue with TDD response (no longer blocking on TODOs)
    else:
        print("  ❌ No TDD response received from Cerebras")

    return tdd_response

def resolve_tracked_todos(session_data, use_codex=True):
    """Resolve accumulated TODOs from previous iterations"""
    tracked_todos = session_data.get('tracked_todos', [])

    if not tracked_todos:
        print("  ✅ No tracked TODOs to resolve")
        return True

    print(f"\n{'='*80}")
    print("📝 TODO RESOLUTION PHASE")
    print(f"{'='*80}")
    print(f"  Found {len(tracked_todos)} tracked TODO(s) from previous iterations")

    # Group TODOs by type for batch resolution
    todos_by_type = {}
    for todo in tracked_todos:
        todo_type = todo.get('type', 'unknown')
        if todo_type not in todos_by_type:
            todos_by_type[todo_type] = []
        todos_by_type[todo_type].append(todo)

    print("\n  📊 TODO Breakdown:")
    for todo_type, todos in todos_by_type.items():
        print(f"     └─ {todo_type}: {len(todos)} items")

    # Create resolution prompt
    todo_summary = "\n".join([
        f"- Line {todo['line']}: {todo['type']} - {todo['content']}"
        for todo in tracked_todos[:20]  # Show first 20
    ])

    if len(tracked_todos) > 20:
        todo_summary += f"\n... and {len(tracked_todos) - 20} more"

    resolution_prompt = f"""TODO RESOLUTION REQUEST

You have {len(tracked_todos)} tracked TODO(s) that need completion:

{todo_summary}

TASK: Resolve these TODOs by:
1. Finding each TODO in the codebase
2. Implementing the complete functionality
3. Removing the TODO comment after implementation

REQUIREMENTS:
- Complete implementations only (no new TODOs)
- Maintain existing code structure
- Add tests if needed
- Document what you resolved

Execute using claude -p for each resolution.
"""

    print("\n  📤 SENDING TODO RESOLUTION PROMPT:")
    print(f"  └─ Prompt length: {len(resolution_prompt)} characters")
    print(f"  └─ TODOs to resolve: {len(tracked_todos)}")

    result = execute_claude_command(resolution_prompt, timeout=600, use_codex=use_codex)

    if result:
        print("  📥 TODO RESOLUTION RESPONSE:")
        print(f"  └─ Response length: {len(result)} characters")

        # Validate that TODOs were actually resolved
        is_quality, quality_msg, new_todos = validate_implementation_quality(result)

        if new_todos:
            print(f"  ⚠️  Resolution created {len(new_todos)} new TODO(s)")
            # Add new TODOs to tracking
            session_data['tracked_todos'] = new_todos
        else:
            print("  ✅ All TODOs resolved successfully")
            session_data['tracked_todos'] = []

        return True
    print("  ❌ No resolution response received")
    return False

def integrate_git_workflow(goal_dir, iteration_summary, use_codex=False):
    """Genesis pattern: Auto-commit when tests pass"""
    git_prompt = f"""GENESIS GIT WORKFLOW INTEGRATION

GOAL DIRECTORY: {goal_dir}
ITERATION SUMMARY: {iteration_summary}

GIT WORKFLOW REQUIREMENTS:
1. Check if tests are passing (look for test results in summary)
2. If tests pass, prepare for git operations:
   - git add -A
   - git commit with descriptive message
   - git push origin HEAD
   - create/increment git tag (0.0.1, 0.0.2, etc.)

DETECT TEST STATUS:
- Look for "tests pass", "all tests passed", "✅", "success" indicators
- Look for "test fail", "❌", "error", "failure" indicators

If tests are passing, return git commands to execute.
If tests failing or unclear, return "SKIP: Tests not confirmed passing"

Return git workflow actions:
"""

    return execute_claude_command(git_prompt, timeout=600, use_codex=use_codex)


def update_progress_file(goal_dir, iteration_data):
    """Update the progress tracking file in goal directory."""
    if goal_dir is None:
        return  # Skip if no goal directory available

    goal_path = Path(goal_dir)
    progress_file = goal_path / "02-progress-tracking.md"

    try:
        # Append iteration data to progress file
        with open(progress_file, "a") as f:
            f.write(f"\n## Iteration {iteration_data['iteration']}\n")
            f.write(
                f"**Work Completed**: {iteration_data.get('work_completed', 'N/A')}\n"
            )
            f.write(f"**Challenges**: {iteration_data.get('challenges', 'N/A')}\n")
            f.write(f"**Progress**: {iteration_data.get('progress', 'N/A')}\n")
            f.write(f"**Next Steps**: {iteration_data.get('next_steps', 'N/A')}\n")
            f.write(f"**Consensus**: {iteration_data.get('consensus', 'N/A')}\n\n")
    except Exception as e:
        print(f"Warning: Could not update progress file: {e}")



def detect_workflow_phase(iteration_num, total_iterations, skip_initial_generation=False):
    """
    Detect workflow phase based on iteration number.

    Stage A (BULK_GENERATION): Iterations 1-2
    - A1: Enhanced goal generation with milestones
    - A2: Comprehensive TDD + implementation generation

    Stage B (ITERATIVE_REFINEMENT): Iterations 3+
    - B1-B6: Milestone-driven development with test validation

    Args:
        iteration_num: Current iteration (1-based)
        total_iterations: Total planned iterations
        skip_initial_generation: If True, skip bulk generation phase (--iterate flag)

    Returns:
        str: "BULK_GENERATION" or "ITERATIVE_REFINEMENT"
    """
    if skip_initial_generation:
        return "ITERATIVE_REFINEMENT"
    if iteration_num <= 2:
        return "BULK_GENERATION"
    return "ITERATIVE_REFINEMENT"


def define_milestones_from_failures(test_results, refined_goal, session_data):
    """
    Define milestones based on test failures and current goal state.

    Args:
        test_results: Results from test execution
        refined_goal: Current refined goal
        session_data: Current session data

    Returns:
        list: List of milestone dictionaries
    """
    # Generate milestones based on test failures and goal analysis
    milestones = []

    # Placeholder for milestone generation logic
    # In real implementation, this would analyze test failures and create
    # specific milestones with success criteria
    milestone = {
        "id": f"milestone_{len(session_data.get('milestones', [])) + 1}",
        "description": "Fix failing tests and implement missing functionality",
        "success_criteria": ["All tests pass", "Code review approval"],
        "test_requirements": ["Unit tests", "Integration tests"],
        "completion_status": "in_progress",
        "attempts": 0,
        "last_review": None
    }
    milestones.append(milestone)

    return milestones

def main():
    """Main goal refinement execution."""

    global GENESIS_USE_CODEX
    GENESIS_USE_CODEX = None

    # Set up logging to /tmp/repo_name/branch_name/
    try:
        import subprocess
        repo_name = os.path.basename(os.getcwd())
        branch_result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                     check=False, capture_output=True, text=True, cwd=os.getcwd())
        branch_name = branch_result.stdout.strip() if branch_result.returncode == 0 else 'unknown'

        log_dir = f"/tmp/{repo_name}/{branch_name}"
        os.makedirs(log_dir, exist_ok=True)

        # Create session-specific log file
        session_id = int(time.time())
        log_file = f"{log_dir}/genesis_{session_id}.log"

        # Set up logging with both file and stdout
        import logging

        # Create a custom logger
        logger = logging.getLogger('genesis')
        logger.setLevel(logging.INFO)

        # Create formatters
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Redirect print statements to both file and console
        class TeeLogger:
            def __init__(self, log_file_path):
                self.log_file = open(log_file_path, 'a', encoding='utf-8')
                self.stdout = sys.stdout

            def write(self, message):
                if message.strip():  # Only log non-empty messages
                    self.log_file.write(message)
                    self.log_file.flush()
                self.stdout.write(message)
                self.stdout.flush()

            def flush(self):
                self.log_file.flush()
                self.stdout.flush()

            def close(self):
                if hasattr(self, 'log_file') and self.log_file:
                    self.log_file.close()

            def __del__(self):
                self.close()

        # Set up the tee logger
        sys.stdout = TeeLogger(log_file)

        # Create human-readable log file
        human_log_file = f"{log_dir}/genesis_{session_id}_human.log"

        class HumanReadableLogger:
            """Simple, structured logger for human-readable Genesis progress"""
            def __init__(self, log_file_path):
                self.log_file = open(log_file_path, 'w', encoding='utf-8')
                self.current_iteration = 0
                self.current_stage = ""
                self.write_header()

            def write_header(self):
                self.log_file.write("=" * 80 + "\n")
                self.log_file.write("GENESIS HUMAN-READABLE LOG\n")
                self.log_file.write(f"Session: {session_id}\n")
                self.log_file.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.log_file.write("=" * 80 + "\n\n")
                self.log_file.flush()

            def start_iteration(self, iteration_num, max_iterations):
                self.current_iteration = iteration_num
                self.log_file.write(f"\n{'='*60}\n")
                self.log_file.write(f"ITERATION {iteration_num}/{max_iterations}\n")
                self.log_file.write(f"Time: {time.strftime('%H:%M:%S')}\n")
                self.log_file.write(f"{'='*60}\n\n")
                self.log_file.flush()

            def log_stage(self, stage_name, details=""):
                self.current_stage = stage_name
                self.log_file.write(f"\n[{stage_name}] {time.strftime('%H:%M:%S')}\n")
                if details:
                    self.log_file.write(f"  {details}\n")
                self.log_file.flush()

            def log_execution_plan(self, plan_summary, prompt_preview=""):
                self.log_file.write("\n📋 EXECUTION PLAN:\n")
                self.log_file.write(f"  Summary: {plan_summary}\n")
                if prompt_preview:
                    self.log_file.write("  Prompt Preview (first 500 chars):\n")
                    self.log_file.write("  " + "-" * 50 + "\n")
                    preview = prompt_preview[:500].replace('\n', '\n    ')
                    self.log_file.write(f"    {preview}...\n")
                    self.log_file.write("  " + "-" * 50 + "\n")
                self.log_file.flush()

            def log_execution(self, action, result="pending"):
                self.log_file.write("\n⚡ EXECUTION:\n")
                self.log_file.write(f"  Action: {action}\n")
                self.log_file.write(f"  Status: {result}\n")
                self.log_file.flush()

            def log_validation(self, validation_type, result, details=""):
                symbol = "✅" if result else "❌"
                self.log_file.write(f"\n{symbol} VALIDATION [{validation_type}]:\n")
                self.log_file.write(f"  Result: {'PASSED' if result else 'FAILED'}\n")
                if details:
                    self.log_file.write(f"  Details: {details}\n")
                self.log_file.flush()

            def log_completion(self, status, summary=""):
                self.log_file.write(f"\n{'='*60}\n")
                self.log_file.write(f"ITERATION {self.current_iteration} COMPLETE\n")
                self.log_file.write(f"Status: {status}\n")
                if summary:
                    self.log_file.write(f"Summary: {summary}\n")
                self.log_file.write(f"{'='*60}\n")
                self.log_file.flush()

            def close(self):
                self.log_file.write(f"\n\nSession ended: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.log_file.close()

            def __del__(self):
                if hasattr(self, 'log_file') and not self.log_file.closed:
                    self.close()

        # Initialize human-readable logger as global
        global human_logger
        human_logger = HumanReadableLogger(human_log_file)

        print(f"📝 Logging to: {log_file}", flush=True)
        print(f"📝 Human-readable log: {human_log_file}", flush=True)
        print("📝 All output will be logged to both terminal and file", flush=True)

    except Exception as e:
        print(f"⚠️ Could not set up logging: {e}", flush=True)
        log_file = None

    print("🚀 PROTO GENESIS STARTING...", flush=True)
    print(f"📍 Working Directory: {os.getcwd()}", flush=True)
    print(f"🧠 Arguments: {sys.argv}", flush=True)

    # Parse arguments using the shared CLI utilities
    try:
        cli_args: GenesisArguments = parse_genesis_cli(sys.argv)
    except GenesisHelpRequested:
        print_cli_usage()
        sys.exit(0)
    except GenesisUsageError as exc:
        print_cli_usage(str(exc))
        sys.exit(1)

    GENESIS_USE_CODEX = cli_args.use_codex

    # Check model selection flags - Codex by default
    original_args = list(sys.argv)
    use_codex = cli_args.use_codex

    if use_codex:
        if "--codex" in original_args:
            print("🔧 Using codex (explicit flag)", flush=True)
        else:
            print("🔧 Using codex (default)", flush=True)
    else:
        print("🔧 Using claude (override: --claude)", flush=True)

    # Check for --iterate flag to skip initial cerebras generation
    skip_initial_generation = cli_args.skip_initial_generation
    if skip_initial_generation:
        print("🔄 Using --iterate flag: Skipping initial Cerebras generation phase", flush=True)
    else:
        print("🚀 Standard mode: Will perform initial Cerebras generation", flush=True)

    # Apply configured pool size (idempotent)
    pool_size = cli_args.pool_size
    set_subagent_pool_size(pool_size)
    if any(arg.startswith("--pool-size") for arg in original_args):
        print(f"🤖 Setting subagent pool size to: {pool_size}")

    # Handle --refine mode (interactive goal refinement)
    if cli_args.mode == "refine":
        print("🔄 REFINE MODE DETECTED", flush=True)
        original_goal = cli_args.refine_goal or ""
        max_iterations = cli_args.max_iterations
        print(f"📝 Goal: {original_goal[:100]}...", flush=True)
        print(f"🔢 Max Iterations: {max_iterations}", flush=True)

        print("=" * 60)
        print("PROTO GENESIS - Interactive Goal Refinement (--refine mode)")
        print("=" * 60)
        print(f"Original Goal: {original_goal}")
        print()

        # Interactive goal refinement
        print("STEP 1: Goal Refinement")
        print("-" * 30)

        refined_goal = None
        exit_criteria = None

        while True:
            print("Refining goal...")
            response = refine_goal_interactive(original_goal, use_codex)

            if response:
                print("🔍 PARSING REFINEMENT RESPONSE...", flush=True)
                refined_goal, exit_criteria = parse_refinement(response)

                print("\nProposed Refinement:")
                print(f"Refined Goal: {refined_goal}")
                print(f"Exit Criteria:\n{exit_criteria}")
                print()

                print("🔐 CHECKING INTERACTIVE MODE...", flush=True)
                is_tty = sys.stdin.isatty()
                print(f"📺 stdin.isatty(): {is_tty}", flush=True)

                # Auto-approve by default to skip refinement approval
                print("🚀 AUTO-APPROVING REFINEMENT (default behavior)", flush=True)
                approval = "y"

                # Optional: Only ask for approval if --interactive flag is provided
                if cli_args.interactive and is_tty:
                    try:
                        approval = (
                            input("Do you approve this refinement? (y/n): ").lower().strip()
                        )
                    except EOFError:
                        print("Auto-approving refinement (stdin closed)")
                        approval = "y"
                if approval in ["y", "yes"]:
                    break
                if approval in ["n", "no"]:
                    print("Let's refine again...\n")
                    continue
                print("Please enter 'y' or 'n'")
            else:
                print("Error refining goal. Please try again.")
                return

        # Generate goal directory using refined goal
        print("\n📋 STEP 2: Creating Goal Directory from Refined Goal")
        print("-" * 50)

        # Create goal directory with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        goal_slug = "-".join(original_goal.lower().split()[:4])  # First 4 words
        goal_dir = f"goals/{timestamp}-{goal_slug}"

        print(f"🎯 Creating goal directory: {goal_dir}")
        success = generate_goal_files_fast(f"REFINED GOAL: {refined_goal}\n\nEXIT CRITERIA:\n{exit_criteria}", goal_dir)

        if not success:
            print("\n❌ Goal directory generation failed, falling back to session mode")
            goal_dir = None  # Fall back to session mode
            session_file = "proto_genesis_session.json"
        else:
            print(f"\n✅ Goal directory created: {goal_dir}")
            session_file = os.path.join(goal_dir, "proto_genesis_session.json")
            print(f"📁 Session file: {session_file}")

        if goal_dir is None:
            # Fallback to session mode if goal directory creation failed
            session_file = "proto_genesis_session.json"

    else:
        # Standard mode: use goal directory
        goal_dir = cli_args.goal_directory
        max_iterations = cli_args.max_iterations

        print("📁 ENTERING GOAL DIRECTORY MODE", flush=True)
        print(f"📂 Goal Directory: {goal_dir}", flush=True)

        print("=" * 60)
        print("PROTO GENESIS - Goal Refinement Execution")
        print("=" * 60)
        print(f"Goal Directory: {goal_dir}")
        print(f"Max Iterations: {max_iterations}")
        print()

        # Load goal from directory
        refined_goal, exit_criteria = load_goal_from_directory(goal_dir)

        if not refined_goal:
            print("Error: Could not load goal from directory")
            return

        print("Loaded Goal:")
        print(f"Refined Goal: {refined_goal}")
        print(
            f"Exit Criteria: {exit_criteria[:200]}..."
            if len(exit_criteria) > 200
            else exit_criteria
        )
        print()

        session_file = os.path.join(goal_dir, "proto_genesis_session.json")

    # Genesis-inspired iteration loop with stage summarization
    print("STARTING GENESIS-INSPIRED ITERATIONS")
    print("=" * 30)
    print("Genesis Principles: One item per loop | Direct claude -p execution | Enhanced context: 2000 tokens | No placeholders")
    print()

    # Genesis-style context variables (minimal)
    previous_summary = ""
    plan_context = ""
    start_iteration = 0

    # Support resuming progress from previous runs when session file exists
    if os.path.exists(session_file):
        try:
            with open(session_file) as f:
                saved_session = json.load(f)

            matches_goal = False
            if "goal_dir" in locals():
                matches_goal = saved_session.get("goal_directory") == goal_dir
            else:
                matches_goal = saved_session.get("goal_directory") == "refine_mode"

            if matches_goal:
                start_iteration = saved_session.get("current_iteration", 0)
                previous_summary = saved_session.get("latest_summary", "") or ""
                print(
                    f"🔁 Resuming Genesis session from iteration {start_iteration + 1}"
                )
                print("Loaded previous summary context for continuity.")
                print()
            else:
                print(
                    "⚠️ Existing session file does not match current goal. Starting fresh iterations."
                )
        except Exception as e:
            print(f"Warning: Could not load session file for resume: {e}")

    if start_iteration >= max_iterations:
        print(
            "✅ Stored session indicates all requested iterations were completed. Increase max iterations to continue."
        )
        print(f"Session saved to: {session_file}")
        return

    for i in range(start_iteration, max_iterations):
        print(f"🎯 GENESIS ITERATION {i + 1}/{max_iterations}")
        print("-" * 40)

        # Initialize session data for this iteration
        session_data = {
            "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
            "refined_goal": refined_goal,
            "exit_criteria": exit_criteria,
            "max_iterations": max_iterations,
            "current_iteration": i,
            "latest_summary": previous_summary,
            "latest_consensus": None,
            "genesis_principles": "One item per loop | Direct execution | Enhanced context",
        }

        # ENHANCED WORKFLOW: Detect workflow phase based on iteration
        workflow_phase = detect_workflow_phase(i + 1, max_iterations, skip_initial_generation)
        print(f"📊 WORKFLOW PHASE: {workflow_phase}")
        if skip_initial_generation:
            print("🔄 --iterate flag active: Skipping Cerebras bulk generation, starting with iterative refinement")

        # Initialize milestone tracking in session if Stage B
        if workflow_phase == "ITERATIVE_REFINEMENT":
            if "milestones" not in session_data:
                session_data["milestones"] = []
                session_data["current_milestone"] = None
                session_data["milestone_progress"] = {}

        # Log to human-readable file
        if 'human_logger' in globals():
            human_logger.start_iteration(i + 1, max_iterations)

        # Load current plan context if available
        plan_context = ""
        if "goal_dir" in locals() and goal_dir is not None:
            try:
                plan_file = Path(goal_dir) / "fix_plan.md"
                if plan_file.exists():
                    with open(plan_file) as f:
                        plan_context = f.read()
            except Exception:
                plan_context = ""

        # ENHANCED WORKFLOW: Execute appropriate phase
        if workflow_phase == "BULK_GENERATION":
            # STAGE A: Bulk Generation Phase
            if i + 1 == 1:
                # A1: Enhanced Goal Generation with Milestones
                print("🎯 STAGE A1: Enhanced Goal Generation (Cerebras)")
                if 'human_logger' in globals():
                    human_logger.log_stage("Enhanced Goal Generation", "Cerebras generating comprehensive goal with milestones")

                execution_strategy = generate_execution_strategy(
                    refined_goal, i + 1, previous_summary, plan_context, use_codex
                )

            elif i + 1 == 2:
                # A2: Comprehensive TDD + Implementation Generation
                print("🧪 STAGE A2: Comprehensive TDD + Implementation (Cerebras)")
                if 'human_logger' in globals():
                    human_logger.log_stage("Comprehensive TDD Generation", "Cerebras generating complete test suite and implementation")

                # Reuse existing function but enhance for comprehensive generation
                execution_strategy = generate_execution_strategy(
                    refined_goal, i + 1, previous_summary, plan_context, use_codex
                )
        else:
            # STAGE B: Iterative Refinement Phase
            print("🔄 STAGE B: Iterative Refinement (Milestone-Driven)")
            if 'human_logger' in globals():
                human_logger.log_stage("Iterative Refinement", "Milestone-driven development with test validation")

            execution_strategy = generate_execution_strategy(
                refined_goal, i + 1, previous_summary, plan_context, use_codex
            )

        if execution_strategy:
            print("Execution Strategy Generated:")
            print(execution_strategy[:300] + "..." if len(execution_strategy) > 300 else execution_strategy)
            print()

            # Summarize planning stage for execution stage
            planning_summary = summarize_for_next_stage(
                "PLANNING", execution_strategy, refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Failed to generate execution strategy")
            if "goal_dir" in locals():
                append_genesis_learning(
                    goal_dir,
                    i + 1,
                    "Scheduler stage failed to produce a strategy; review prompt content and constraints.",
                )
            # Increment iteration counter before backtracking to prevent infinite loops
            session_data = {
                "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
                "refined_goal": refined_goal,
                "exit_criteria": exit_criteria,
                "max_iterations": max_iterations,
                "current_iteration": i + 1,
                "latest_summary": previous_summary,
                "latest_consensus": None,
                "genesis_principles": "One item per loop | Direct execution | Enhanced context",
            }
            safe_session_write(session_file, session_data)
            continue

        # TDD Generation - Enhanced for workflow phases
        if workflow_phase == "BULK_GENERATION" and i + 1 == 2:
            # A2: Comprehensive TDD + Implementation Generation
            print("🧪 STAGE A2 TDD: Comprehensive Test Suite Generation (Cerebras)")
            if 'human_logger' in globals():
                human_logger.log_stage("Comprehensive TDD Generation", "Cerebras generating complete test framework and initial implementation")
        else:
            # Standard TDD or Stage B TDD
            print("🧪 STAGE 2: TDD Generation (Genesis Cerebras)")
            if 'human_logger' in globals():
                human_logger.log_stage("TDD Generation", "Genesis TDD with Cerebras generating tests and implementation")

        tdd_response = generate_tdd_implementation(
            refined_goal, i + 1, execution_strategy, plan_context, use_codex
        )

        if tdd_response:
            print("TDD Suite Generated:")
            print(tdd_response[:300] + "..." if len(tdd_response) > 300 else tdd_response)
            print()

            # Summarize TDD stage for execution stage
            tdd_summary = summarize_for_next_stage(
                "TDD_GENERATION", tdd_response, refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Failed to generate TDD suite")
            if "goal_dir" in locals():
                append_genesis_learning(
                    goal_dir,
                    i + 1,
                    "TDD generation stage failed; review Cerebras integration and prompt effectiveness.",
                )
            tdd_summary = planning_summary or previous_summary
            # Increment iteration counter before backtracking to prevent infinite loops
            session_data = {
                "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
                "refined_goal": refined_goal,
                "exit_criteria": exit_criteria,
                "max_iterations": max_iterations,
                "current_iteration": i + 1,
                "latest_summary": tdd_summary,
                "latest_consensus": None,
                "genesis_principles": "One item per loop | TDD with Cerebras | Enhanced context",
            }
            safe_session_write(session_file, session_data)
            continue

        # STAGE 3: Enhanced Execution - Phase-specific logic
        if workflow_phase == "BULK_GENERATION":
            # Stage A: Standard execution with test/fix focus
            print("⚡ STAGE A3: Execution (Genesis Test/Fix/Adapt)")

            test_fix_strategy = f"""EXECUTION FOCUS: Test, Fix, and Adapt Generated Code

GENERATED TDD CONTENT:
{tdd_response[:1000]}{'...' if len(tdd_response) > 1000 else ''}

EXECUTION TASKS:
1. Implement the generated tests in the codebase
2. Run the tests and identify any failures
3. Fix the implementation to make all tests pass
4. Integrate the code with existing codebase patterns
5. Verify end-to-end functionality

ORIGINAL STRATEGY CONTEXT:
{execution_strategy}
"""

            progress_response = make_progress(
                refined_goal, i + 1, test_fix_strategy, plan_context, use_codex
            )

        else:
            # Stage B: Milestone-driven iterative refinement
            print("🎯 STAGE B: Milestone-Driven Execution")

            # B1: Test execution & debug
            print("🔧 B1: Test Execution & Debug Analysis")
            test_results = make_progress(
                f"Run all tests and analyze failures for: {refined_goal}",
                i + 1, execution_strategy, plan_context, use_codex
            )

            # B2: Define milestones if tests are failing
            if test_results and ("FAIL" in test_results or "ERROR" in test_results):
                print("📋 B2: Defining Milestones from Test Failures")
                session_data.setdefault("milestones", [])
                new_milestones = define_milestones_from_failures(test_results, refined_goal, session_data)
                session_data["milestones"].extend(new_milestones)

                # B3-B6: Milestone execution loop
                for milestone in session_data["milestones"]:
                    if milestone["completion_status"] != "complete":
                        print(f"🎯 B3-B6: Processing Milestone: {milestone['description']}")

                        # B3.1: Generate execution strategy for milestone
                        milestone_strategy = generate_execution_strategy(
                            f"Milestone: {milestone['description']}\nOriginal Goal: {refined_goal}",
                            i + 1, previous_summary, plan_context, use_codex
                        )

                        # B3.2: Cerebras code generation for milestone
                        milestone_code = generate_tdd_implementation(
                            f"Milestone: {milestone['description']}",
                            i + 1, milestone_strategy, plan_context, use_codex
                        )

                        # B4: Code review with /cons
                        print("👥 B4: Code Review Integration")
                        # Code review integration disabled to comply with mandatory import patterns
                        print("⚠️ Code review integration disabled - import validation compliance")
                        review_result = "Review skipped - import validation compliance"

                        # B5: Test validation
                        print("✅ B5: Test Validation")
                        milestone_tests = make_progress(
                            f"Run tests specifically for milestone: {milestone['description']}",
                            i + 1, milestone_strategy, plan_context, use_codex
                        )

                        # B6: Milestone completion check
                        if milestone_tests and "PASS" in milestone_tests:
                            milestone["completion_status"] = "complete"
                            print(f"✅ Milestone completed: {milestone['description']}")
                        else:
                            milestone["attempts"] += 1
                            print(f"🔄 Milestone retry needed: {milestone['description']} (attempt {milestone['attempts']})")
                            if milestone["attempts"] >= 3:
                                print(f"⚠️ Milestone max attempts reached: {milestone['description']}")
                                milestone["completion_status"] = "blocked"

                        break  # Process one milestone per iteration

                progress_response = test_results
            else:
                # Tests passing, continue with standard execution
                progress_response = make_progress(
                    refined_goal, i + 1, execution_strategy, plan_context, use_codex
                )

        if progress_response:
            print("Progress Made:")
            print(progress_response[:300] + "..." if len(progress_response) > 300 else progress_response)
            print()

            # Summarize execution stage for validation stage (now includes TDD context)
            execution_summary = summarize_for_next_stage(
                "EXECUTION", f"TDD Generated:\n{tdd_summary}\n\nExecution Results:\n{progress_response}", refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Failed to make progress")
            if "goal_dir" in locals():
                append_genesis_learning(
                    goal_dir,
                    i + 1,
                    "Execution stage produced no tangible updates; investigate failing subagent outputs.",
                )
            previous_summary = tdd_summary if 'tdd_summary' in locals() else planning_summary or previous_summary
            # Increment iteration counter before backtracking to prevent infinite loops
            session_data = {
                "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
                "refined_goal": refined_goal,
                "exit_criteria": exit_criteria,
                "max_iterations": max_iterations,
                "current_iteration": i + 1,
                "latest_summary": previous_summary,
                "latest_consensus": None,
                "genesis_principles": "One item per loop | Direct execution | Enhanced context",
            }
            safe_session_write(session_file, session_data)
            continue

        # STAGE 4: Validation with focused assessment
        print("✅ STAGE 4: Validation (Genesis Consensus)")
        consensus_response = check_consensus(
            refined_goal, exit_criteria, execution_summary, plan_context, use_codex
        )

        if consensus_response:
            print("Consensus Assessment:")
            print(consensus_response[:300] + "..." if len(consensus_response) > 300 else consensus_response)
            print()

            # STAGE 4.5: TODO Resolution Phase (DISABLED - causing analysis paralysis)
            # print("📝 STAGE 4.5: TODO Resolution Phase")
            # if 'session_data' not in locals():
            #     session_data = {}
            # resolve_tracked_todos(session_data, use_codex)

            # 🚨 GENESIS SELF-DETERMINATION: Check for completion
            if check_goal_completion(consensus_response, exit_criteria):
                print("🎉 GENESIS SELF-DETERMINATION: GOAL COMPLETED!")
                print("✅ All exit criteria satisfied based on consensus assessment")
                try:
                    if goal_dir is None:
                        # Handle fallback case where goal_dir is None
                        goal_dir = "refine_mode_completion"
                    completion_file = Path(goal_dir) / "GENESIS_COMPLETE.md"
                except (NameError, TypeError):
                    # Handle refine mode where goal_dir may not be defined or is None
                    goal_dir = "refine_mode_completion"
                    completion_file = Path(goal_dir) / "GENESIS_COMPLETE.md"
                    # Ensure directory exists
                    Path(goal_dir).mkdir(parents=True, exist_ok=True)

                if goal_dir and goal_dir != "unknown":
                    with open(completion_file, 'w') as f:
                        f.write("# Genesis Completion Report\n\n")
                        f.write(f"**Completion Time**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"**Final Iteration**: {i + 1}/{max_iterations}\n\n")
                        f.write(f"## Final Assessment\n{consensus_response}\n\n")
                        f.write(f"## Goal Achieved\n{refined_goal}\n\n")
                        f.write(f"## Exit Criteria Met\n{exit_criteria}\n")
                    print(f"📄 Completion report saved: {completion_file}")

                # Save final session state
                session_data = {
                    "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
                    "refined_goal": refined_goal,
                    "exit_criteria": exit_criteria,
                    "max_iterations": max_iterations,
                    "completed_iteration": i + 1,
                    "status": "COMPLETED",
                    "final_assessment": consensus_response,
                    "completion_time": time.strftime('%Y-%m-%d %H:%M:%S'),
                    "genesis_principles": "Self-determined completion based on exit criteria"
                }
                safe_session_write(session_file, session_data)
                print("🏁 Genesis session completed successfully")
                return  # Exit the iteration loop

            # Update plan document (Genesis living plan maintenance)
            if "goal_dir" in locals() and goal_dir is not None:
                updated_plan = update_plan_document(
                    goal_dir, f"{execution_summary}\n{consensus_response}", i + 1, use_codex
                )

                # Update genesis instructions (Genesis self-improvement)
                update_genesis_instructions(
                    goal_dir,
                    f"Iteration {i+1} learnings:\n{progress_response}",
                    use_codex,
                    iteration_num=i + 1,
                )

            # Prepare summary for next iteration (context conservation)
            previous_summary = summarize_for_next_stage(
                "VALIDATION", consensus_response, refined_goal, i + 1, use_codex
            )
        else:
            print("❌ Consensus validation failed to produce output")
            if "goal_dir" in locals():
                append_genesis_learning(
                    goal_dir,
                    i + 1,
                    "Consensus stage returned no assessment; tighten validation prompts or inspect logs.",
                )
            previous_summary = execution_summary if 'execution_summary' in locals() else tdd_summary if 'tdd_summary' in locals() else previous_summary

            # Increment iteration counter before backtracking to prevent infinite loops
            session_data = {
                "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
                "refined_goal": refined_goal,
                "exit_criteria": exit_criteria,
                "max_iterations": max_iterations,
                "current_iteration": i + 1,
                "latest_summary": previous_summary,
                "latest_consensus": None,
                "genesis_principles": "One item per loop | Direct execution | Enhanced context",
            }
            safe_session_write(session_file, session_data)
            continue

        # Save enhanced session data (Genesis context conservation + workflow state)
        session_data = {
            "goal_directory": goal_dir if "goal_dir" in locals() else "refine_mode",
            "refined_goal": refined_goal,
            "exit_criteria": exit_criteria,
            "max_iterations": max_iterations,
            "current_iteration": i + 1,
            "latest_summary": previous_summary,  # Only keep latest summary, not all work
            "latest_consensus": consensus_response,
            "genesis_principles": "Enhanced workflow | Stage A: Bulk generation | Stage B: Milestone-driven",
            # Enhanced workflow state
            "workflow_phase": workflow_phase,
            "milestones": session_data.get("milestones", []),
            # TOKEN BURN PREVENTION: Pull live token data from workflow_state when available
            "token_usage": {
                "total_tokens": getattr(workflow_state, 'total_tokens_used', 0) if 'workflow_state' in locals() and workflow_state is not None else session_data.get("total_tokens", 0),
                "iteration_tokens": getattr(workflow_state, 'iteration_tokens', {}) if 'workflow_state' in locals() and workflow_state is not None else session_data.get("iteration_tokens", {}),
                "max_tokens_per_iteration": MAX_TOKENS_PER_ITERATION,
                "current_iteration_tokens": getattr(workflow_state, 'iteration_tokens', {}).get(i, 0) if 'workflow_state' in locals() and workflow_state is not None else session_data.get("iteration_tokens", {}).get(i, 0)
            },
            "current_milestone": session_data.get("current_milestone"),
            "milestone_progress": session_data.get("milestone_progress", {})
        }

        # Update progress in goal directory if available
        if "goal_dir" in locals():
            iteration_data = {
                "iteration": i + 1,
                "work_completed": "See GENESIS.md and fix_plan.md for details",
                "genesis_approach": "Single focus with direct execution",
                "progress": "See consensus assessment",
                "next_steps": "See fix_plan.md priorities",
                "consensus": consensus_response.split("\n")[0] if consensus_response else "N/A",
            }
            update_progress_file(goal_dir, iteration_data)

        safe_session_write(session_file, session_data)

        # Check if goal achieved (enhanced Genesis completion detection)
        if consensus_response:
            # Look for OVERALL PROGRESS: XX% pattern (Genesis-specific)
            overall_match = re.search(
                r"OVERALL\s+PROGRESS\s*:\s*(\d+)%",
                consensus_response,
                re.IGNORECASE,
            )
            if overall_match:
                completion_percentage = int(overall_match.group(1))
                if completion_percentage >= 95:  # Genesis allows 95% as "close enough"
                    print("🎉 GENESIS GOAL ACHIEVED! 🎉")
                    print("Genesis principle: 95%+ completion with working implementation is success")
                    break

        # Genesis-style continuation (trust the process)
        if i < max_iterations - 1:
            print("📈 Progress made this iteration. Genesis continues...")
            print("Genesis principle: Trust the process, focus on next single task")
            print()

        print("=" * 60 + "\n")

    print("Goal refinement execution complete!")
    print(f"Session saved to: {session_file}")


def safe_session_write(session_file, session_data):
    """Write session data with size limits to prevent runaway files"""
    try:
        # Truncate large fields to prevent multi-GB files
        MAX_FIELD_SIZE = 50000  # 50KB per field

        # Create a copy to modify
        safe_data = session_data.copy()

        # Truncate large string fields
        for key, value in safe_data.items():
            if isinstance(value, str) and len(value) > MAX_FIELD_SIZE:
                print(f"    ⚠️  TRUNCATING SESSION FIELD '{key}': {len(value)} chars > {MAX_FIELD_SIZE} limit")
                safe_data[key] = value[:MAX_FIELD_SIZE] + f"\n\n[TRUNCATED - Field exceeded {MAX_FIELD_SIZE} char limit]"

        with open(session_file, "w") as f:
            json.dump(safe_data, f, indent=2)

    except Exception as e:
        print(f"Warning: Could not write session file: {e}")


# Helper functions for structured status parsing
def _parse_test_status(output: str) -> TestStatus:
    """Parse test output to determine status using reliable patterns."""
    output_lower = output.lower()

    # Clear passing indicators
    if any(phrase in output_lower for phrase in [
        "all tests pass", "tests passed", "test suite passed",
        "✅ all tests", "0 failed", "success: all tests"
    ]):
        return TestStatus.PASSED

    # Clear failing indicators
    if any(phrase in output_lower for phrase in [
        "test failed", "tests failed", "failure", "error",
        "❌ test", "failed:", "assertion error"
    ]):
        return TestStatus.FAILED

    # Default to not run if unclear
    return TestStatus.NOT_RUN


def _parse_goal_status(output: str) -> WorkflowStatus:
    """Parse goal validation output to determine completion status."""
    output_lower = output.lower()

    # Clear completion indicators
    if any(phrase in output_lower for phrase in [
        "goal fully implemented", "implementation complete", "objective achieved",
        "requirements met", "✅ goal", "100% complete", "fully functional"
    ]):
        return WorkflowStatus.COMPLETED

    # Clear in-progress indicators
    if any(phrase in output_lower for phrase in [
        "implementation gaps", "partially complete", "in progress",
        "needs work", "missing", "todo", "incomplete"
    ]):
        return WorkflowStatus.IN_PROGRESS

    # Default to pending if unclear
    return WorkflowStatus.PENDING


def _extract_implementation_gaps(output: str) -> str | None:
    """Extract specific implementation gaps from goal validation output."""
    # Look for gap patterns in the output
    gap_patterns = [
        r"gaps?:\s*([^\n]+)",
        r"missing:\s*([^\n]+)",
        r"todo:\s*([^\n]+)",
        r"incomplete:\s*([^\n]+)"
    ]

    for pattern in gap_patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    # Fallback: look for bullet points or numbered lists indicating gaps
    lines = output.split('\n')
    gaps = []
    for line in lines:
        line = line.strip()
        if line.startswith(('- ', '* ', '1. ', '2. ', '3. ')) and any(
            word in line.lower() for word in ['missing', 'need', 'todo', 'gap', 'incomplete']
        ):
            gaps.append(line)

    if gaps:
        return '; '.join(gaps)

    return None


def _extract_test_errors(output: str) -> str:
    """Extract specific test error messages from test output."""
    # Look for error patterns
    error_patterns = [
        r"error:\s*([^\n]+)",
        r"failed:\s*([^\n]+)",
        r"assertion error:\s*([^\n]+)",
        r"❌\s*([^\n]+)"
    ]

    errors = []
    for pattern in error_patterns:
        matches = re.findall(pattern, output, re.IGNORECASE)
        errors.extend(matches)

    if errors:
        return '; '.join(errors[:3])  # Limit to first 3 errors

    return "Unknown test failures"


def enhanced_genesis_workflow(goal, iteration_num, previous_output=None):
    """Minimal orchestration using /tmp file-based data flow"""
    import os
    import subprocess

    # Setup /tmp paths
    repo_name = os.path.basename(os.getcwd())
    try:
        branch_name = subprocess.check_output(
            ['git', 'branch', '--show-current'],
            timeout=10,
            stderr=subprocess.DEVNULL
        ).decode().strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Warning: Could not determine git branch: {e}")
        branch_name = "unknown"
    tmp_path = f"/tmp/{repo_name}/{branch_name}"
    os.makedirs(tmp_path, exist_ok=True)

    if iteration_num == 1:
        # A1: Enhanced Goal (Cerebras)
        prompt = f"Enhanced Goal Generation: Take this goal and expand it into a comprehensive specification with clear milestones: {goal}"
        return cerebras_call(prompt)

    if iteration_num == 2:
        # A2: Comprehensive TDD (Cerebras)
        prompt = f"Comprehensive TDD Implementation: Create complete test suite and initial implementation for: {previous_output}"
        return cerebras_call(prompt)

    # Stage B: Use detailed design workflow (B1-B5) with /tmp file data flow
    current_suite = previous_output

    # Detailed workflow implementation follows B1-B5 design specification
    return execute_detailed_b1_to_b5_workflow(current_suite, goal, tmp_path)


def execute_detailed_b1_to_b5_workflow(current_suite, goal, tmp_path):
    """Execute the detailed B1-B5 workflow with /tmp file-based data flow and structured status."""

    # Initialize structured workflow state
    workflow_state = WorkflowState()
    max_iterations = 20  # Prevent infinite loops

    for iteration in range(max_iterations):
        print(f"\n🔄 B-Stage Iteration {iteration + 1}/{max_iterations}")
        workflow_state.current_phase = f"B{iteration + 1}"

        # TOKEN BURN PREVENTION: Log iteration start with token tracking
        print("📊 ITERATION STATS:")
        print(f"  └─ Total tokens used: {workflow_state.total_tokens_used}")
        print(f"  └─ Iteration {iteration + 1} tokens: {workflow_state.iteration_tokens.get(iteration, 0)}")
        print(f"  └─ Token budget remaining: {workflow_state.max_tokens_per_iteration - workflow_state.iteration_tokens.get(iteration, 0)}")
        print(f"  └─ Tests passing: {workflow_state.tests_passing}")
        print(f"  └─ Goal complete: {workflow_state.goal_complete}")
        print("═" * 50)

        # B1: Integration & Testing (Smart Model)
        b1_prompt = f"Integration & Testing: Run all relevant tests and integrate changes for goal '{goal}': {current_suite}"
        b1_output = smart_model_call(b1_prompt)

        # Parse B1 results using structured status
        workflow_state.tests_passing = _parse_test_status(b1_output) == TestStatus.PASSED

        # Write integration status to file with secure handling
        SecureFileHandler.write_with_lock(
            f"{tmp_path}/genesis_integration_status.txt",
            b1_output
        )

        # B2: Goal Validation & Verification (Smart Model)
        integration_status = SecureFileHandler.read_with_lock(
            f"{tmp_path}/genesis_integration_status.txt"
        )

        b2_prompt = f"Goal Validation: Verify that the implementation satisfies the original goal '{goal}' and enhanced spec: {integration_status}"
        b2_output = smart_model_call(b2_prompt)

        # Parse B2 results using structured status
        workflow_state.goal_complete = _parse_goal_status(b2_output) == WorkflowStatus.COMPLETED
        if not workflow_state.goal_complete:
            workflow_state.implementation_gaps = _extract_implementation_gaps(b2_output)

        # Write goal validation to file with secure handling
        SecureFileHandler.write_with_lock(
            f"{tmp_path}/genesis_goal_validation.txt",
            b2_output
        )

        # Check dual termination condition using structured status
        if workflow_state.goal_complete and workflow_state.tests_passing:
            print("✅ Workflow complete: Both goal validation and tests satisfied")
            workflow_state.current_phase = "COMPLETE"
            return current_suite  # Workflow complete
        if workflow_state.goal_complete:
            print(f"🟡 Goal complete but tests failing - will retry (iteration {iteration + 1}/{max_iterations})")
        elif workflow_state.tests_passing:
            print(f"🟡 Tests passing but goal not complete - will retry (iteration {iteration + 1}/{max_iterations})")
        else:
            print(f"🔴 Both goal and tests incomplete - will retry (iteration {iteration + 1}/{max_iterations})")

        # B3: Milestone Planning (Smart Model) - only if goal not complete
        if not workflow_state.goal_complete:
            validation_results = SecureFileHandler.read_with_lock(
                f"{tmp_path}/genesis_goal_validation.txt"
            )

            gap_context = f" (Gaps: {workflow_state.implementation_gaps})" if workflow_state.implementation_gaps else ""
            b3_prompt = f"Milestone Planning: Based on implementation gaps{gap_context} and overall goal '{goal}', create prioritized milestones: {validation_results}"
            b3_output = smart_model_call(b3_prompt)

            # Write milestones to file with secure handling
            SecureFileHandler.write_with_lock(
                f"{tmp_path}/genesis_milestones.txt",
                b3_output
            )

            # B4: Two-Phase Code Generation with retry logic
            max_retries = 3
            retry_count = 0
            workflow_state.current_phase = "B4"

            while retry_count < max_retries:
                # B4.1: Execution Planning (Smart Model)
                milestones = SecureFileHandler.read_with_lock(
                    f"{tmp_path}/genesis_milestones.txt"
                )

                use_codex = is_codex_enabled()
                if not use_codex:  # Claude path
                    b41_prompt = f"Generate execution plan for goal '{goal}' milestones using jleechan_simulation_prompt.md: {milestones}"
                else:  # Codex path
                    b41_prompt = f"Generate execution plan for goal '{goal}' milestones: {milestones}"

                b41_output = smart_model_call(b41_prompt)

                # Write execution plan to file with secure handling
                SecureFileHandler.write_with_lock(
                    f"{tmp_path}/genesis_execution_plan.txt",
                    b41_output
                )

                # B4.2: TDD Code Generation (Cerebras)
                execution_plan = SecureFileHandler.read_with_lock(
                    f"{tmp_path}/genesis_execution_plan.txt"
                )
                milestones = SecureFileHandler.read_with_lock(
                    f"{tmp_path}/genesis_milestones.txt"
                )

                b42_prompt = f"TDD Code Generation: Using execution plan and milestones for goal '{goal}': Plan: {execution_plan} Milestones: {milestones}"
                b42_output = cerebras_call(b42_prompt)

                # B4.3: Test Validation (Smart Model) with structured status
                b43_prompt = f"Test Validation: Run all relevant tests and analyze results for goal '{goal}'"
                b43_output = smart_model_call(b43_prompt)

                # Parse test results using structured status
                test_status = _parse_test_status(b43_output)
                workflow_state.tests_passing = (test_status == TestStatus.PASSED)

                # Write test results to file with secure handling
                SecureFileHandler.write_with_lock(
                    f"{tmp_path}/genesis_test_results.txt",
                    b43_output
                )

                # Check if tests pass using structured status
                if test_status == TestStatus.PASSED:
                    print("✅ B4.3 Test validation passed")
                    workflow_state.error_message = None
                    break
                retry_count += 1
                print(f"⚠️  B4.3 Test validation failed (attempt {retry_count}/{max_retries}), retrying...")
                workflow_state.error_message = f"Test failures in B4.3: {_extract_test_errors(b43_output)}"

                # Write failure details for next iteration with secure handling
                SecureFileHandler.write_with_lock(
                    f"{tmp_path}/genesis_failure_details.txt",
                    f"Test Failures: {workflow_state.error_message}"
                )

            # B5: Code Review (Model-Specific)
            workflow_state.current_phase = "B5"
            use_codex = is_codex_enabled()
            if not use_codex:  # Claude path - simulate /cons command
                b5_prompt = f"Code Review: Review current implementation using /cons methodology for goal '{goal}'"
            else:  # Codex path
                b5_prompt = f"Code Review: Review current implementation for goal '{goal}'"

            b5_output = smart_model_call(b5_prompt)

            # Update current suite with B5 feedback for next iteration
            current_suite = b5_output

        else:
            print(f"🔄 Goal complete but tests not passing, continuing iteration {iteration + 1}")

    # Maximum iterations reached
    print(f"⚠️  Maximum B-stage iterations ({max_iterations}) reached")
    workflow_state.error_message = f"Maximum iterations ({max_iterations}) reached without completion"
    return current_suite


if __name__ == "__main__":
    main()
