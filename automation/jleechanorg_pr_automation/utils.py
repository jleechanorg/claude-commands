#!/usr/bin/env python3
"""
Shared utilities for automation system

Consolidates common patterns:
- JSON file operations with thread safety
- Logging configuration setup
- Environment variable handling
- Email configuration management
"""

import fcntl
import json
import logging
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from .logging_utils import setup_logging  # noqa: F401


class SafeJSONManager:
    """Thread-safe and cross-process safe JSON file operations with file locking"""

    def __init__(self):
        self._locks = {}
        self._locks_lock = threading.Lock()

    def _get_lock(self, file_path: str) -> threading.RLock:
        """Get or create a lock for a specific file"""
        # Normalize path to prevent duplicate locks for same file
        norm_path = os.path.abspath(file_path)
        with self._locks_lock:
            if norm_path not in self._locks:
                self._locks[norm_path] = threading.RLock()
            return self._locks[norm_path]

    def _get_file_lock_path(self, file_path: str) -> str:
        """Get file lock path for cross-process safety"""
        return f"{file_path}.lock"

    def read_json(self, file_path: str, default: Any = None) -> Any:
        """Cross-process safe JSON file reading with default fallback"""
        lock = self._get_lock(file_path)
        with lock:
            try:
                if os.path.exists(file_path):
                    with open(file_path) as f:
                        # Add file lock for cross-process safety
                        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                        try:
                            return json.load(f)
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                else:
                    return default if default is not None else {}
            except (OSError, json.JSONDecodeError) as e:
                logging.warning(f"Failed to read JSON from {file_path}: {e}")
                return default if default is not None else {}

    def write_json(self, file_path: str, data: Any) -> bool:
        """Cross-process safe JSON file writing with atomic operations"""
        lock = self._get_lock(file_path)
        with lock:
            try:
                # Ensure directory exists (guard against empty dirname for root files)
                directory = os.path.dirname(file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                # Create temp file in same directory for atomic replace
                dir_path = directory or "."
                fd, temp_path = tempfile.mkstemp(
                    dir=dir_path,
                    prefix=os.path.basename(file_path),
                    suffix=".tmp"
                )

                try:
                    with os.fdopen(fd, "w") as f:
                        # Add exclusive file lock for cross-process safety
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        try:
                            json.dump(data, f, indent=2, default=str)
                            f.flush()
                            os.fsync(f.fileno())
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                    # Atomic replace
                    os.replace(temp_path, file_path)
                    return True
                finally:
                    # Clean up temp file if replace failed
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except OSError:
                            pass

            except OSError as e:
                logging.exception(f"Failed to write JSON to {file_path}: {e}")
                return False

    def update_json(self, file_path: str, update_func, lock_timeout: int = 10) -> bool:
        """Cross-process safe JSON file update with callback function"""
        lock = self._get_lock(file_path)
        with lock:
            try:
                data = self.read_json(file_path, {})
                updated_data = update_func(data)
                return self.write_json(file_path, updated_data)
            except Exception as e:
                logging.exception(f"Failed to update JSON {file_path}: {e}")
                return False

    def atomic_update(self, file_path: str, update_func, default: Any = None) -> bool:
        """
        ATOMIC read-modify-write with file lock held across entire operation.

        This fixes the race condition where separate read_json() and write_json()
        calls release the file lock between operations, allowing other processes
        to interleave and corrupt the update.

        Args:
            file_path: Path to JSON file
            update_func: Callback that takes current data dict and returns updated dict
            default: Default value if file doesn't exist (default: {})

        Returns:
            bool: True if update succeeded, False otherwise
        """
        lock = self._get_lock(file_path)
        default_val = default if default is not None else {}

        with lock:
            try:
                # Ensure directory exists
                directory = os.path.dirname(file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                # FIX: Use single code path to avoid TOCTOU race condition
                # 'a+' mode creates file if missing, doesn't truncate if exists
                # Lock is acquired BEFORE any truncation happens
                with open(file_path, 'a+') as f:
                    # Acquire EXCLUSIVE lock for entire read-modify-write
                    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    try:
                        # Read current data (seek to start for 'a+' mode)
                        f.seek(0)
                        try:
                            content = f.read()
                            data = json.loads(content) if content.strip() else default_val
                        except (json.JSONDecodeError, ValueError):
                            data = default_val

                        # Apply update function
                        updated_data = update_func(data)

                        # Write updated data atomically (truncate AFTER lock acquired)
                        f.seek(0)
                        f.truncate()
                        json.dump(updated_data, f, indent=2, default=str)
                        f.flush()
                        os.fsync(f.fileno())

                        return True
                    finally:
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

            except Exception as e:
                logging.exception(f"Failed atomic update of {file_path}: {e}")
                return False


# Global instance for shared use
json_manager = SafeJSONManager()


def get_env_config(prefix: str = "AUTOMATION_") -> Dict[str, str]:
    """Get all environment variables with specified prefix"""
    config = {}
    for key, value in os.environ.items():
        if key.startswith(prefix):
            # Remove prefix and convert to lowercase
            config_key = key[len(prefix):].lower()
            config[config_key] = value
    return config


def get_email_config() -> Dict[str, str]:
    """Get email configuration from environment variables"""
    email_config = {
        "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "email_user": os.getenv("EMAIL_USER", ""),
        "email_pass": os.getenv("EMAIL_PASS", ""),
        "email_to": os.getenv("EMAIL_TO", ""),
        "email_from": os.getenv("EMAIL_FROM", os.getenv("EMAIL_USER", ""))
    }
    return email_config


def validate_email_config(config: Dict[str, str]) -> bool:
    """Validate that required email configuration is present"""
    required_fields = ["smtp_server", "email_user", "email_pass", "email_to"]
    return all(config.get(field) for field in required_fields)


def get_automation_limits() -> Dict[str, int]:
    """Get automation safety limits from defaults with optional overrides.

    Supports workflow-specific limits:
    - pr_automation: Default PR monitoring workflow (posts codex comments)
    - fix_comment: Fix-comment workflow (addresses review comments)
    - codex_update: Codex update workflow (browser automation)
    - fixpr: FixPR workflow (resolves conflicts/failing checks)
    """
    return get_automation_limits_with_overrides()


def coerce_positive_int(value: Any, *, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def get_automation_limits_with_overrides(overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, int]:
    """Internal helper to keep defaults centralized and overrides explicit.

    New limit structure:
    - pr_limit: 50 total attempts across ALL workflows for a PR
    - workflow limits: 10 attempts per workflow (counts ALL attempts, not just failures)
    """
    # Global PR limit: 50 total attempts across all workflows
    pr_limit_default = 50
    pr_limit = coerce_positive_int(os.getenv("AUTOMATION_PR_LIMIT"), default=pr_limit_default)

    # Per-workflow limit: 10 attempts per workflow
    workflow_limit_default = 10

    defaults: Dict[str, int] = {
        # Global PR limit: counts ALL attempts across ALL workflows
        "pr_limit": pr_limit,
        "global_limit": coerce_positive_int(os.getenv("AUTOMATION_GLOBAL_LIMIT"), default=100),
        "approval_hours": 24,
        "subprocess_timeout": 300,
        # Workflow-specific limits: 10 attempts per workflow (counts ALL attempts)
        "pr_automation_limit": coerce_positive_int(
            os.getenv("AUTOMATION_PR_AUTOMATION_LIMIT"), default=workflow_limit_default
        ),
        "fix_comment_limit": coerce_positive_int(
            os.getenv("AUTOMATION_FIX_COMMENT_LIMIT"), default=workflow_limit_default
        ),
        "codex_update_limit": coerce_positive_int(
            os.getenv("AUTOMATION_CODEX_UPDATE_LIMIT"), default=workflow_limit_default
        ),
        "fixpr_limit": coerce_positive_int(os.getenv("AUTOMATION_FIXPR_LIMIT"), default=workflow_limit_default),
    }

    if not overrides:
        return dict(defaults)

    limits = dict(defaults)
    for key in list(defaults.keys()):
        if key in overrides:
            limits[key] = coerce_positive_int(overrides.get(key), default=defaults[key])

    return limits


def ensure_directory(file_path: str) -> None:
    """Ensure directory exists for given file path"""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def get_project_root() -> str:
    """Get project root directory"""
    current_dir = Path(__file__).resolve()
    # Look for CLAUDE.md to identify project root
    for parent in current_dir.parents:
        if (parent / "CLAUDE.md").exists():
            return str(parent)
    # Fallback to parent of automation directory
    return str(current_dir.parent.parent)


def format_timestamp(dt: datetime = None) -> str:
    """Format datetime as ISO string"""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string to datetime"""
    return datetime.fromisoformat(timestamp_str)


def get_test_email_config() -> Dict[str, str]:
    """Get standardized test email configuration"""
    return {
        "SMTP_SERVER": "smtp.example.com",
        "SMTP_PORT": "587",
        "EMAIL_USER": "test@example.com",
        "EMAIL_PASS": "testpass",
        "EMAIL_TO": "admin@example.com"
    }
