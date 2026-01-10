#!/usr/bin/env python3
"""
Shared Automation Utilities Module

Consolidates common functionality used across automation components:
- Logging setup and configuration
- Configuration management (SMTP, paths, environment)
- Email notification system
- Subprocess execution with timeout and error handling
- File and directory management utilities
"""

import fcntl
import json
import os
import smtplib
import subprocess
import tempfile
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional, Sequence, Tuple

import keyring

KEYRING_AVAILABLE = True

from .utils import json_manager, setup_logging as shared_setup_logging


class AutomationUtils:
    """Shared utilities for automation components"""

    # Default configuration
    DEFAULT_CONFIG = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": 587,
        "LOG_DIR": "~/Library/Logs/project-automation",
        "DATA_DIR": "~/Library/Application Support/project-automation",
        "MAX_SUBPROCESS_TIMEOUT": int(os.getenv("AUTOMATION_SUBPROCESS_TIMEOUT", "300")),  # 5 minutes (configurable)
        "EMAIL_SUBJECT_PREFIX": f"[{os.getenv('PROJECT_NAME', 'Project')} Automation]"
    }

    @classmethod
    def setup_logging(cls, name: str, log_filename: str = None) -> Any:
        """Unified logging setup for all automation components

        Args:
            name: Logger name (typically __name__)
            log_filename: Optional specific log filename, defaults to component name

        Returns:
            Configured logger instance
        """
        if log_filename is None:
            log_filename = f"{name.split('.')[-1]}.log"

        # Create log directory
        log_dir = Path(cls.DEFAULT_CONFIG["LOG_DIR"]).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)
        
        return shared_setup_logging(name, log_file=str(log_dir / log_filename))

    @classmethod
    def get_config_value(cls, key: str, default: Any = None) -> Any:
        """Get configuration value from environment or defaults"""
        env_value = os.environ.get(key)
        if env_value is not None:
            # Try to convert to appropriate type
            if isinstance(default, bool):
                return env_value.lower() in ("true", "1", "yes", "on")
            if isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    pass
            return env_value
        return cls.DEFAULT_CONFIG.get(key, default)

    @classmethod
    def get_data_directory(cls, subdir: str = None) -> Path:
        """Get standardized data directory path"""
        data_dir = Path(cls.DEFAULT_CONFIG["DATA_DIR"]).expanduser()
        if subdir:
            data_dir = data_dir / subdir
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    @classmethod
    def get_smtp_credentials(cls) -> Tuple[Optional[str], Optional[str]]:
        """Securely get SMTP credentials from keyring or environment"""
        username = None
        password = None

        if KEYRING_AVAILABLE:
            try:
                service_name = os.environ.get("AUTOMATION_KEYRING_SERVICE", "project-automation")
                username = keyring.get_password(service_name, "smtp_username")
                password = keyring.get_password(service_name, "smtp_password")
            except Exception:
                pass  # Fall back to environment variables

        # Fallback to environment variables if keyring fails or unavailable
        if not username:
            username = os.environ.get("SMTP_USERNAME")
        if not password:
            password = os.environ.get("SMTP_PASSWORD")

        return username, password

    @classmethod
    def send_email_notification(cls, subject: str, message: str,
                              to_email: str = None, from_email: str = None) -> bool:
        """Send email notification with unified error handling

        Args:
            subject: Email subject line
            message: Email body content
            to_email: Override recipient email
            from_email: Override sender email

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Get SMTP configuration
            smtp_server = cls.get_config_value("SMTP_SERVER")
            smtp_port = cls.get_config_value("SMTP_PORT")
            username, password = cls.get_smtp_credentials()

            # Get email addresses
            from_email = from_email or os.environ.get("MEMORY_EMAIL_FROM")
            to_email = to_email or os.environ.get("MEMORY_EMAIL_TO")

            if not all([username, password, from_email, to_email]):
                print("Email configuration incomplete - skipping notification")
                return False

            # Build email message
            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = f"{cls.DEFAULT_CONFIG['EMAIL_SUBJECT_PREFIX']} {subject}"

            # Add timestamp to message
            full_message = f"""{message}

Time: {datetime.now().isoformat()}
System: Project Automation

This is an automated notification from the automation system."""

            msg.attach(MIMEText(full_message, "plain"))

            # Send email with timeout and proper error handling
            with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)

            print(f"✅ Email notification sent: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP authentication failed: {e}")
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ Email recipients refused: {e}")
        except smtplib.SMTPException as e:
            print(f"❌ SMTP error: {e}")
        except OSError as e:
            print(f"❌ Network error: {e}")
        except Exception as e:
            print(f"❌ Unexpected email error: {e}")

        return False

    @classmethod
    def execute_subprocess_with_timeout(cls, command: list, timeout: int = None,
                                      cwd: str = None, capture_output: bool = True,
                                      check: bool = True,
                                      retry_attempts: int = 1,
                                      retry_backoff_seconds: float = 1.0,
                                      retry_backoff_multiplier: float = 2.0,
                                      retry_on_stderr_substrings: Optional[Sequence[str]] = None) -> subprocess.CompletedProcess:
        """Execute subprocess with standardized timeout and error handling

        Args:
            command: Command to execute as list
            timeout: Timeout in seconds (uses default if None)
            cwd: Working directory
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise CalledProcessError on non-zero exit (default True)
            retry_attempts: Total attempts for retryable failures (default 1 = no retries)
            retry_backoff_seconds: Initial backoff between retries
            retry_backoff_multiplier: Backoff multiplier per attempt
            retry_on_stderr_substrings: If provided, only retry when stderr/stdout contains one of these substrings

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails and check=True
        """
        if timeout is None:
            timeout = cls.get_config_value("MAX_SUBPROCESS_TIMEOUT")

        try:
            retry_attempts_int = max(int(retry_attempts), 1)
        except (TypeError, ValueError):
            retry_attempts_int = 1

        try:
            backoff_seconds = max(float(retry_backoff_seconds), 0.0)
        except (TypeError, ValueError):
            backoff_seconds = 1.0

        try:
            backoff_multiplier = max(float(retry_backoff_multiplier), 1.0)
        except (TypeError, ValueError):
            backoff_multiplier = 2.0

        if retry_on_stderr_substrings and not capture_output:
            raise ValueError("retry_on_stderr_substrings requires capture_output=True")

        attempt = 1
        while True:
            try:
                # Ensure shell=False for security, check parameter controls error handling
                return subprocess.run(
                    command,
                    timeout=timeout,
                    cwd=cwd,
                    capture_output=capture_output,
                    text=True,
                    shell=False,
                    check=check,
                )
            except subprocess.CalledProcessError as exc:
                if attempt >= retry_attempts_int:
                    raise

                if retry_on_stderr_substrings:
                    stderr = (exc.stderr or "") + "\n" + (exc.stdout or "")
                    if not any(token in stderr for token in retry_on_stderr_substrings):
                        raise

                delay = backoff_seconds * (backoff_multiplier ** (attempt - 1))
                delay = max(0.0, min(delay, 60.0))
                time.sleep(delay)
                attempt += 1

    @classmethod
    def safe_read_json(cls, file_path: Path) -> dict:
        """Safely read JSON file with file locking (delegates to json_manager)"""
        return json_manager.read_json(str(file_path), {})

    @classmethod
    def safe_write_json(cls, file_path: Path, data: dict) -> None:
        """Atomically write JSON file with file locking (delegates to json_manager)"""
        if not json_manager.write_json(str(file_path), data):
            raise RuntimeError(f"Failed to write JSON file {file_path}")

    @classmethod
    def get_memory_config(cls) -> Dict[str, str]:
        """Load memory email configuration (for backward compatibility)"""
        config = {}
        config_file = Path.home() / ".memory_email_config"

        if config_file.exists():
            try:
                # Source the bash config file by running it and capturing environment
                result = cls.execute_subprocess_with_timeout(
                    ["bash", "-c", f"source {config_file} && env"],
                    timeout=10
                )

                for line in result.stdout.splitlines():
                    if "=" in line:
                        key, value = line.split("=", 1)
                        config[key] = value

            except Exception as e:
                print(f"Warning: Could not load memory config: {e}")

        return config


# Convenience functions for backward compatibility
def setup_logging(name: str, log_filename: str = None) -> Any:
    """Convenience function for setup_logging"""
    return AutomationUtils.setup_logging(name, log_filename)


def send_email_notification(subject: str, message: str, to_email: str = None, from_email: str = None) -> bool:
    """Convenience function for send_email_notification"""
    return AutomationUtils.send_email_notification(subject, message, to_email, from_email)


def execute_subprocess_with_timeout(command: list, timeout: int = None,
                                  cwd: str = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Convenience function for execute_subprocess_with_timeout"""
    return AutomationUtils.execute_subprocess_with_timeout(command, timeout, cwd, capture_output)
