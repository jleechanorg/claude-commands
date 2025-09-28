#!/usr/bin/env python3
"""
Shared utilities for automation system

Consolidates common patterns:
- JSON file operations with thread safety
- Logging configuration setup
- Environment variable handling
- Email configuration management
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class SafeJSONManager:
    """Thread-safe JSON file operations with consistent error handling"""

    def __init__(self):
        self._locks = {}
        self._locks_lock = threading.Lock()

    def _get_lock(self, file_path: str) -> threading.RLock:
        """Get or create a lock for a specific file"""
        with self._locks_lock:
            if file_path not in self._locks:
                self._locks[file_path] = threading.RLock()
            return self._locks[file_path]

    def read_json(self, file_path: str, default: Any = None) -> Any:
        """Thread-safe JSON file reading with default fallback"""
        lock = self._get_lock(file_path)
        with lock:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        return json.load(f)
                else:
                    return default if default is not None else {}
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Failed to read JSON from {file_path}: {e}")
                return default if default is not None else {}

    def write_json(self, file_path: str, data: Any) -> bool:
        """Thread-safe JSON file writing with error handling"""
        lock = self._get_lock(file_path)
        with lock:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # Write with atomic operation using temp file
                temp_path = f"{file_path}.tmp"
                with open(temp_path, 'w') as f:
                    json.dump(data, f, indent=2, default=str)

                # Atomic move
                os.rename(temp_path, file_path)
                return True
            except (IOError, OSError) as e:
                logging.error(f"Failed to write JSON to {file_path}: {e}")
                return False

    def update_json(self, file_path: str, update_func) -> bool:
        """Thread-safe JSON file update with callback function"""
        lock = self._get_lock(file_path)
        with lock:
            data = self.read_json(file_path, {})
            updated_data = update_func(data)
            return self.write_json(file_path, updated_data)


# Global instance for shared use
json_manager = SafeJSONManager()


def setup_logging(name: str, level: int = logging.INFO,
                 log_file: Optional[str] = None) -> logging.Logger:
    """Standardized logging setup for automation components"""
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


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
        'smtp_server': os.getenv('SMTP_SERVER', 'localhost'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'email_user': os.getenv('EMAIL_USER', ''),
        'email_pass': os.getenv('EMAIL_PASS', ''),
        'email_to': os.getenv('EMAIL_TO', ''),
        'email_from': os.getenv('EMAIL_FROM', os.getenv('EMAIL_USER', ''))
    }
    return email_config


def validate_email_config(config: Dict[str, str]) -> bool:
    """Validate that required email configuration is present"""
    required_fields = ['smtp_server', 'email_user', 'email_pass', 'email_to']
    return all(config.get(field) for field in required_fields)


def get_automation_limits() -> Dict[str, int]:
    """Get automation safety limits from environment or defaults"""
    return {
        'pr_limit': int(os.getenv('AUTOMATION_PR_LIMIT', '5')),
        'global_limit': int(os.getenv('AUTOMATION_GLOBAL_LIMIT', '50')),
        'approval_hours': int(os.getenv('AUTOMATION_APPROVAL_HOURS', '24'))
    }


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
        'SMTP_SERVER': 'smtp.example.com',
        'SMTP_PORT': '587',
        'EMAIL_USER': 'test@example.com',
        'EMAIL_PASS': 'testpass',
        'EMAIL_TO': 'admin@example.com'
    }
