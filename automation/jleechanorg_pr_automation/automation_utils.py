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
import logging
import os
import smtplib
import subprocess
import tempfile
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False


class AutomationUtils:
    """Shared utilities for automation components"""

    # Default configuration
    DEFAULT_CONFIG = {
        "SMTP_SERVER": "smtp.gmail.com",
        "SMTP_PORT": 587,
        "LOG_DIR": "~/Library/Logs/worldarchitect-automation",
        "DATA_DIR": "~/Library/Application Support/worldarchitect-automation",
        "MAX_SUBPROCESS_TIMEOUT": int(os.getenv("AUTOMATION_SUBPROCESS_TIMEOUT", "300")),  # 5 minutes (configurable)
        "EMAIL_SUBJECT_PREFIX": "[WorldArchitect Automation]"
    }

    @classmethod
    def setup_logging(cls, name: str, log_filename: str = None) -> logging.Logger:
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

        # Set up logging with consistent format
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / log_filename),
                logging.StreamHandler()
            ]
        )

        logger = logging.getLogger(name)
        logger.info(f"🛠️  Logging initialized - logs: {log_dir / log_filename}")
        return logger

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
                username = keyring.get_password("worldarchitect-automation", "smtp_username")
                password = keyring.get_password("worldarchitect-automation", "smtp_password")
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
System: WorldArchitect Automation

This is an automated notification from the WorldArchitect.AI automation system."""

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
                                      check: bool = True) -> subprocess.CompletedProcess:
        """Execute subprocess with standardized timeout and error handling

        Args:
            command: Command to execute as list
            timeout: Timeout in seconds (uses default if None)
            cwd: Working directory
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise CalledProcessError on non-zero exit (default True)

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.TimeoutExpired: If command times out
            subprocess.CalledProcessError: If command fails and check=True
        """
        if timeout is None:
            timeout = cls.get_config_value("MAX_SUBPROCESS_TIMEOUT")

        # Ensure shell=False for security, check parameter controls error handling
        result = subprocess.run(
            command,
            timeout=timeout,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            shell=False,
            check=check
        )

        return result

    @classmethod
    def safe_read_json(cls, file_path: Path) -> dict:
        """Safely read JSON file with file locking"""
        try:
            with open(file_path) as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @classmethod
    def safe_write_json(cls, file_path: Path, data: dict):
        """Atomically write JSON file with file locking"""
        # Use system temp directory for better security
        temp_path = None
        try:
            # Create temporary file securely
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".tmp",
                delete=False
            ) as temp_file:
                fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
                json.dump(data, temp_file, indent=2)
                temp_file.flush()
                os.fsync(temp_file.fileno())  # Force write to disk
                fcntl.flock(temp_file.fileno(), fcntl.LOCK_UN)  # Unlock
                temp_path = temp_file.name

            # Set restrictive permissions before moving
            os.chmod(temp_path, 0o600)  # Owner read/write only

            # Atomic rename - this operation is atomic on POSIX systems
            os.rename(temp_path, file_path)
            temp_path = None  # Successful, don't clean up

        except (OSError, json.JSONEncodeError) as e:
            # Clean up temp file on error
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass  # Best effort cleanup
            raise RuntimeError(f"Failed to write JSON file {file_path}: {e}") from e

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
def setup_logging(name: str, log_filename: str = None) -> logging.Logger:
    """Convenience function for setup_logging"""
    return AutomationUtils.setup_logging(name, log_filename)


def send_email_notification(subject: str, message: str, to_email: str = None, from_email: str = None) -> bool:
    """Convenience function for send_email_notification"""
    return AutomationUtils.send_email_notification(subject, message, to_email, from_email)


def execute_subprocess_with_timeout(command: list, timeout: int = None,
                                  cwd: str = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Convenience function for execute_subprocess_with_timeout"""
    return AutomationUtils.execute_subprocess_with_timeout(command, timeout, cwd, capture_output)
