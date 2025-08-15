"""
Subprocess utilities for safe command execution.

This module provides utilities for secure subprocess execution with:
- Timeout handling
- Safe command execution with security validation
- Content sanitization for logging
"""

import logging
import re
import subprocess
import shlex
from typing import List, Union, Optional


logger = logging.getLogger(__name__)


def run_cmd_safe(
    cmd: Union[List[str], str], 
    timeout: int = 120,
    capture_output: bool = True,
    text: bool = True,
    check: bool = False,
    cwd: Optional[str] = None,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Execute a command safely with timeout and security validation.
    
    Args:
        cmd: Command to execute (list of strings or string)
        timeout: Maximum execution time in seconds
        capture_output: Whether to capture stdout/stderr
        text: Whether to return text output
        check: Whether to raise on non-zero exit
        cwd: Working directory for command
        **kwargs: Additional subprocess arguments
        
    Returns:
        CompletedProcess with stdout, stderr, and returncode
        
    Raises:
        subprocess.TimeoutExpired: If command times out
        subprocess.CalledProcessError: If check=True and command fails
        ValueError: If command fails security validation
    """
    # Validate and prepare command
    if isinstance(cmd, str):
        # Basic validation for string commands
        if any(char in cmd for char in ['&', '|', ';', '`', '$(']):
            logger.warning("Command contains shell metacharacters, consider using list form")
        cmd_list = shlex.split(cmd)
    else:
        cmd_list = list(cmd)
    
    # Basic command validation
    if not cmd_list:
        raise ValueError("Empty command")
    
    # Log command execution (sanitized/redacted)
    cmd_str = ' '.join(shlex.quote(arg) for arg in cmd_list)
    sanitized_cmd_str = cmd_str
    redaction_patterns = [
        (r'(?i)(--(?:token|auth|password|pass|secret|api[-_]?key)\s+)\S+', r'\1[REDACTED]'),
        (r'(?i)(-p\s+)\S+', r'\1[REDACTED]'),  # common short password flag
        (r'(?i)(Authorization:\s*Bearer\s+)\S+', r'\1[REDACTED]'),
        (r'(?i)(\bGITHUB_TOKEN=)\S+', r'\1[REDACTED]'),  # Added capture group
    ]
    for pat, repl in redaction_patterns:
        sanitized_cmd_str = re.sub(pat, repl, sanitized_cmd_str)
    logger.debug(f"Executing command: {sanitized_cmd_str}")
    
    try:
        result = subprocess.run(
            cmd_list,
            timeout=timeout,
            capture_output=capture_output,
            text=text,
            check=check,
            cwd=cwd,
            **kwargs
        )
        
        logger.debug(f"Command completed with return code: {result.returncode}")
        if capture_output:
            if result.stdout:
                logger.debug(f"STDOUT: {sanitize_log_content(result.stdout)}")
            if result.stderr:
                logger.debug(f"STDERR: {sanitize_log_content(result.stderr)}")
        return result
        
    except subprocess.TimeoutExpired as e:
        logger.error(f"Command timed out after {timeout} seconds: {sanitized_cmd_str}")
        try:
            out = getattr(e, "output", "") or ""
            err = getattr(e, "stderr", "") or ""
            if out:
                logger.debug(f"STDOUT (partial): {sanitize_log_content(out)}")
            if err:
                logger.debug(f"STDERR (partial): {sanitize_log_content(err)}")
        except Exception:
            pass
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with return code {e.returncode}: {sanitized_cmd_str}")
        try:
            if getattr(e, "stdout", None):
                logger.debug(f"STDOUT: {sanitize_log_content(e.stdout)}")
            if getattr(e, "stderr", None):
                logger.debug(f"STDERR: {sanitize_log_content(e.stderr)}")
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error(f"Unexpected error executing command: {e}")
        raise


def sanitize_log_content(content: str, max_length: int = 1000) -> str:
    """
    Sanitize content for safe logging by removing sensitive information.
    
    Args:
        content: Content to sanitize
        max_length: Maximum length of returned content
        
    Returns:
        Sanitized content safe for logging
    """
    if not content:
        return ""
    
    # Remove common sensitive patterns
    sanitized = content
    
    # Remove potential API keys, tokens, and secrets
    patterns = [
        # key/value style credentials
        r'(?i)(api[_-]?key|token|secret|password)["\s]*[:=]["\s]*[A-Za-z0-9._\-+/=]{20,}',
        r'(?i)\b(bearer)\s+[A-Za-z0-9._\-+/=]{20,}',
        r'(?i)\bauthorization["\s]*:\s*[A-Za-z]+\s+[A-Za-z0-9._\-+/=]{20,}',
        # JWTs (three base64url segments with minimum length requirements)
        # Must have header.payload.signature format with substantial length
        r'\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\b',
        # Provider-specific token prefixes
        r'\bghp_[A-Za-z0-9]{30,}\b',              # GitHub classic tokens
        r'\bgithub_pat_[A-Za-z0-9_]{30,}\b',      # GitHub fine-grained tokens
        r'\bglpat-[A-Za-z0-9_\-]{20,}\b',         # GitLab tokens
        r'\bxox[baprs]-[A-Za-z0-9\-]{20,}\b',     # Slack tokens
        r'\bsk-[A-Za-z0-9]{20,}\b',               # OpenAI-style
        r'\bAIza[0-9A-Za-z\-_]{20,}\b',           # Google API keys
    ]
    
    for pattern in patterns:
        sanitized = re.sub(pattern, '[REDACTED_CREDENTIAL]', sanitized)
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "... [TRUNCATED]"
    
    return sanitized


def validate_tmux_session_name(session_name: str) -> bool:
    """
    Validate tmux session name for security.
    
    Args:
        session_name: Session name to validate
        
    Returns:
        True if session name is safe to use
    """
    if not session_name:
        return False
    
    # Validate: 1-64 chars, no leading '-', allow alnum, dot, underscore, hyphen (no colon)
    if not re.fullmatch(r"(?=.{1,64}$)(?!-)[A-Za-z0-9._-]+", session_name):
        return False
    
    return True