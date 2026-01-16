#!/usr/bin/env python3
"""
Centralized CLI Validation Library

Provides two-phase validation for CLI tools:
- Phase 1: --help check (cheap sanity check)
- Phase 2: Execution test with file output (2+2 test, saves to /tmp)

All CLIs use consistent validation logic with CLI-specific adaptations.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

# Test prompt used for CLI validation (simple math question to verify CLI can execute and write output)
CLI_VALIDATION_TEST_PROMPT = "What is 2+2? Write only the number."

# Timeout constants for CLI validation subprocess runs
CLI_VALIDATION_TIMEOUT_SECONDS = 10
OAUTH_CLI_VALIDATION_TIMEOUT_SECONDS = 15
HELP_CHECK_TIMEOUT_SECONDS = 5


class ValidationResult:
    """Result of CLI validation."""
    
    def __init__(
        self,
        success: bool,
        phase: str,  # "help", "execution", or "unknown"
        message: str,
        output_file: Optional[Path] = None,
    ):
        self.success = success
        self.phase = phase
        self.message = message
        self.output_file = output_file  # Path to validation output file (if Phase 2 succeeded)
    
    def __bool__(self) -> bool:
        return self.success
    
    def __str__(self) -> str:
        return f"ValidationResult(success={self.success}, phase={self.phase}, message={self.message})"


def validate_cli_help(
    cli_name: str,
    cli_path: str,
    help_args: list[str],
    env: Optional[dict[str, str]] = None,
    timeout: int = HELP_CHECK_TIMEOUT_SECONDS,
) -> ValidationResult:
    """
    Phase 1: Validate CLI by running --help (or equivalent).
    
    Args:
        cli_name: Name of CLI (e.g., "gemini", "codex")
        cli_path: Path to CLI binary
        help_args: Arguments to pass for help check (e.g., ["--help"] or ["exec", "--help"])
        env: Environment variables (defaults to os.environ)
        timeout: Timeout in seconds
    
    Returns:
        ValidationResult with success=True if help check passes
    """
    if env is None:
        env = dict(os.environ)
    
    try:
        cmd = [cli_path] + help_args
        result = subprocess.run(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            env=env,
        )
        
        # Check for help/version output in either stdout or stderr
        combined_output = f"{result.stdout or ''}\n{result.stderr or ''}"
        
        # Success if exit code is 0 or if we see help/version indicators
        if result.returncode == 0:
            return ValidationResult(
                success=True,
                phase="help",
                message=f"{cli_name} help check passed (exit code 0)",
            )
        
        # Check for help/version keywords as fallback
        help_patterns = [
            r"\bUsage:\s*",
            r"\bhelp\b",
            r"\bversion\b",
            r"\boptions\b",
            r"\bcommands\b",
        ]
        for pattern in help_patterns:
            if re.search(pattern, combined_output, re.IGNORECASE):
                return ValidationResult(
                    success=True,
                    phase="help",
                    message=f"{cli_name} help check passed (help/version detected)",
                )
        
        return ValidationResult(
            success=False,
            phase="help",
            message=f"{cli_name} help check failed (exit code {result.returncode}, no help output)",
        )
    
    except subprocess.TimeoutExpired:
        return ValidationResult(
            success=True,  # Timeout = slow but might work
            phase="help",
            message=f"{cli_name} help check timed out (will try execution phase)",
        )
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            phase="help",
            message=f"{cli_name} binary not found: {cli_path}",
        )
    except Exception as e:
        return ValidationResult(
            success=True,  # Unknown error = assume available
            phase="help",
            message=f"{cli_name} help check error: {e} (will try execution phase)",
        )


def validate_cli_execution(
    cli_name: str,
    cli_path: str,
    execution_cmd: list[str],
    test_prompt: str = CLI_VALIDATION_TEST_PROMPT,
    env: Optional[dict[str, str]] = None,
    timeout: int = CLI_VALIDATION_TIMEOUT_SECONDS,
    output_dir: Optional[Path] = None,
    retain_output: bool = False,
    prompt_file_needed: bool = False,
) -> ValidationResult:
    """
    Phase 2: Validate CLI by running execution test (2+2) and verifying file output.
    
    Args:
        cli_name: Name of CLI (e.g., "gemini", "codex")
        cli_path: Path to CLI binary
        execution_cmd: Command to run (e.g., ["-m", "gemini-2.0-flash-exp", "--yolo"])
        test_prompt: Prompt to send to CLI
        env: Environment variables (defaults to os.environ)
        timeout: Timeout in seconds
        output_dir: Directory to save output file (defaults to /tmp/cli_validation_<cli_name>_<timestamp>)
        retain_output: If True, don't delete output directory after validation
    
    Returns:
        ValidationResult with success=True if execution test passes and writes output file
    """
    if env is None:
        env = dict(os.environ)
    
    # Create output directory (deterministic path for debugging)
    validation_dir = None
    try:
        if output_dir:
            validation_dir = Path(output_dir)
            validation_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(validation_dir, 0o700)
        else:
            # Use deterministic /tmp path: /tmp/cli_validation_<cli_name>_<pid>_<timestamp>
            timestamp = int(time.time())
            pid = os.getpid()
            validation_dir = Path(f"/tmp/cli_validation_{cli_name}_{pid}_{timestamp}")
            validation_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(validation_dir, 0o700)
    except Exception as dir_error:
        return ValidationResult(
            success=False,
            phase="execution",
            message=f"{cli_name} failed to create validation directory: {dir_error}",
        )
    
    validation_output_file = validation_dir / "validation_output.txt"
    
    try:
        # Handle prompt file for OAuth CLIs (Claude/Cursor)
        if prompt_file_needed:
            prompt_file = validation_dir / "test_prompt.txt"
            prompt_file.write_text(test_prompt)
            # Replace @PROMPT_FILE marker with actual prompt file path, preserving @ prefix
            # OAuth CLIs use -p @path syntax, so we need to keep the @
            execution_cmd = [arg.replace("@PROMPT_FILE", f"@{prompt_file}") if "@PROMPT_FILE" in arg else arg for arg in execution_cmd]
            stdin_input = None  # OAuth CLIs use prompt file, not stdin
        else:
            stdin_input = test_prompt  # API key CLIs use stdin
        
        # Build full command
        cmd = [cli_path] + execution_cmd
        
        # Run CLI and redirect output to file
        with open(validation_output_file, "w") as f:
            result = subprocess.run(
                cmd,
                input=stdin_input,
                stdin=subprocess.DEVNULL if stdin_input is None else None,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                env=env,
            )
        
        stderr_output = result.stderr or ""
        
        # Check output file
        if validation_output_file.exists() and validation_output_file.stat().st_size > 0:
            output_content = validation_output_file.read_text()
            
            # Success: file exists, has content, and exit code is 0
            if result.returncode == 0 and len(output_content.strip()) > 0:
                return ValidationResult(
                    success=True,
                    phase="execution",
                    message=f"{cli_name} execution test passed (output written to {validation_output_file})",
                    output_file=validation_output_file,
                )
        
        # Check for quota/rate limit errors in stderr or stdout
        combined_output = f"{stderr_output}\n{validation_output_file.read_text() if validation_output_file.exists() else ''}"
        quota_phrases = [
            "exhausted your capacity",
            "exhausted your daily quota",
            "rate limit",
            "quota exceeded",
            "resource_exhausted",
        ]
        if any(phrase in combined_output.lower() for phrase in quota_phrases):
            return ValidationResult(
                success=False,
                phase="execution",
                message=f"{cli_name} quota/rate limit detected",
            )
        
        # Check for auth/permission errors for OAuth CLIs (Claude/Cursor)
        # DESIGN DECISION: Auth errors are treated as "available" (success=True) for OAuth CLIs.
        # Rationale: OAuth CLIs require interactive login that may not be available during preflight.
        # Runtime will handle auth (user may be logged in, or CLI will prompt interactively).
        # Tradeoff: A CLI needing interactive login in non-interactive runs could "validate" but
        # hang/fail at runtime. This is acceptable because OAuth CLIs are fallback options.
        if prompt_file_needed:  # OAuth CLIs use prompt files
            auth_patterns = [
                r"\bauth\b",
                r"\bpermission\b",
                r"\bauthenticate\b",
                r"\bnot authenticated\b",
                r"\bnot authorized\b",
            ]
            if any(re.search(pattern, combined_output, re.IGNORECASE) for pattern in auth_patterns):
                return ValidationResult(
                    success=True,
                    phase="execution",
                    message=f"{cli_name} execution test detected auth issue (will try anyway, runtime will handle)",
                    output_file=validation_output_file if validation_output_file.exists() else None,
                )
        
        # Check for help/version output as fallback (for CLIs that emit help on error)
        help_patterns = [
            r"\bUsage:\s*",
            r"\bversion\b",
        ]
        for pattern in help_patterns:
            if re.search(pattern, combined_output, re.IGNORECASE):
                return ValidationResult(
                    success=True,
                    phase="execution",
                    message=f"{cli_name} execution test passed (help/version detected as fallback)",
                    output_file=validation_output_file if validation_output_file.exists() else None,
                )
        
        return ValidationResult(
            success=False,
            phase="execution",
            message=f"{cli_name} execution test failed (exit code {result.returncode}, output file exists={validation_output_file.exists()})",
        )
    
    except subprocess.TimeoutExpired:
        # DESIGN DECISION: Timeouts are treated as "available" (success=True) to allow runtime fallback.
        # Rationale: A slow CLI may still work at runtime; preflight validation is meant to catch
        # definitive failures (quota exhaustion, binary not found), not to block on slow responses.
        # Tradeoff: A hung CLI could be selected, but runtime will catch actual failures.
        return ValidationResult(
            success=True,  # Timeout = slow but might work
            phase="execution",
            message=f"{cli_name} execution test timed out (will try anyway)",
        )
    except FileNotFoundError:
        return ValidationResult(
            success=False,
            phase="execution",
            message=f"{cli_name} binary not found: {cli_path}",
        )
    except Exception as e:
        # DESIGN DECISION: Unknown exceptions are treated as "available" (success=True) to allow runtime fallback.
        # Rationale: Preflight validation should catch definitive failures (quota, binary not found),
        # not block on unexpected errors that might be transient or environment-specific.
        # Tradeoff: Real breakage (permission errors, network issues) could be masked, but runtime
        # will catch actual failures and fallback to next CLI in chain.
        return ValidationResult(
            success=True,  # Unknown error = assume available
            phase="execution",
            message=f"{cli_name} execution test error: {e} (will try anyway)",
        )
    finally:
        # Clean up validation directory unless retain_output is True
        if not retain_output and validation_dir and validation_dir.exists():
            try:
                shutil.rmtree(validation_dir)
            except Exception as cleanup_error:
                # Log but don't fail validation
                import logging
                logging.debug(f"Cleanup error during CLI validation for {cli_name}: {cleanup_error}")


def validate_cli_two_phase(
    cli_name: str,
    cli_path: str,
    help_args: list[str],
    execution_cmd: list[str],
    env: Optional[dict[str, str]] = None,
    execution_timeout: int = CLI_VALIDATION_TIMEOUT_SECONDS,
    output_dir: Optional[Path] = None,
    retain_output: bool = False,
    skip_help: bool = False,
    agent_name: Optional[str] = None,
) -> ValidationResult:
    """
    Two-phase validation: --help check first, then execution test.
    
    Args:
        cli_name: Name of CLI
        cli_path: Path to CLI binary
        help_args: Arguments for help check (e.g., ["--help"])
        execution_cmd: Command for execution test (e.g., ["-m", "model", "--yolo"])
        env: Environment variables
        execution_timeout: Timeout for execution phase
        output_dir: Directory to save output file
        retain_output: If True, don't delete output directory
        skip_help: If True, skip Phase 1 and go straight to execution
    
    Returns:
        ValidationResult from Phase 2 (execution), or Phase 1 if skip_help=False and Phase 1 fails hard
    """
    # Phase 1: Help check (unless skipped)
    if not skip_help:
        help_result = validate_cli_help(cli_name, cli_path, help_args, env=env)
        if not help_result.success and help_result.phase == "help":
            # Hard failure (binary not found, etc.) - don't proceed to execution
            if "not found" in help_result.message.lower():
                if agent_name:
                    print(f"   ⚠️ {cli_name.capitalize()} CLI binary not found for {agent_name}: {cli_path}")
                return help_result
    
    # Phase 2: Execution test
    # Check if execution command needs prompt file (OAuth CLIs)
    prompt_file_needed = any("@PROMPT_FILE" in arg for arg in execution_cmd)
    
    execution_result = validate_cli_execution(
        cli_name,
        cli_path,
        execution_cmd,
        env=env,
        timeout=execution_timeout,
        output_dir=output_dir,
        retain_output=retain_output,
        prompt_file_needed=prompt_file_needed,
    )
    
    # Add agent_name to messages if provided
    if agent_name and execution_result.message:
        if execution_result.success:
            print(f"   ✅ {execution_result.message} (agent: {agent_name})")
        else:
            print(f"   ⚠️ {execution_result.message} (agent: {agent_name})")
    
    return execution_result
