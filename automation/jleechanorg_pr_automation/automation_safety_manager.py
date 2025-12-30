#!/usr/bin/env python3
"""
Automation Safety Manager - GREEN Phase Implementation

Minimal implementation to pass the RED phase tests with:
- PR attempt limits (max 10 per PR)
- Global run limits (max 50 per day with automatic midnight reset)
- Manual approval system
- Thread-safe operations
- Email notifications
"""

import argparse
import importlib.util
import json
import os
import smtplib
import sys
import threading
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional, Union

REAL_DATETIME = datetime

# Number of characters in the ISO 8601 date prefix ("YYYY-MM-DD").
ISO_DATE_PREFIX_LENGTH = len("YYYY-MM-DD")

# Optional keyring import for email functionality
_keyring_spec = importlib.util.find_spec("keyring")
if _keyring_spec:
    import keyring  # type: ignore
    HAS_KEYRING = True
else:
    keyring = None  # type: ignore
    HAS_KEYRING = False

# Import shared utilities
from .utils import (
    get_automation_limits,
    json_manager,
    setup_logging,
)


class AutomationSafetyManager:
    """Thread-safe automation safety manager with configurable limits"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.lock = threading.RLock()  # Use RLock to prevent deadlock
        self.logger = setup_logging(__name__)

        # Get limits from shared utility
        limits = get_automation_limits()
        self.pr_limit = limits["pr_limit"]
        self.global_limit = limits["global_limit"]

        # File paths
        self.pr_attempts_file = os.path.join(data_dir, "pr_attempts.json")
        self.global_runs_file = os.path.join(data_dir, "global_runs.json")
        self.approval_file = os.path.join(data_dir, "manual_approval.json")
        self.config_file = os.path.join(data_dir, "automation_safety_config.json")
        self.inflight_file = os.path.join(data_dir, "pr_inflight.json")  # NEW: Persist inflight cache

        # In-memory counters for thread safety
        self._pr_attempts_cache = {}
        self._global_runs_cache = 0
        self._pr_inflight_cache: Dict[str, int] = {}

        # Initialize files if they don't exist
        self._ensure_files_exist()

        # Load configuration from file if it exists
        self._load_config_if_exists()

        # Load initial state from files
        self._load_state_from_files()

    def _ensure_files_exist(self):
        """Initialize tracking files if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.pr_attempts_file):
            self._write_json_file(self.pr_attempts_file, {})

        if not os.path.exists(self.global_runs_file):
            now = datetime.now()
            today = now.date().isoformat()
            self._write_json_file(self.global_runs_file, {
                "total_runs": 0,
                "start_date": now.isoformat(),
                "current_date": today,
                "last_run": None,
                "last_reset": now.isoformat(),
            })

        if not os.path.exists(self.approval_file):
            self._write_json_file(self.approval_file, {
                "approved": False,
                "approval_date": None
            })

        if not os.path.exists(self.inflight_file):
            self._write_json_file(self.inflight_file, {})

    def _load_config_if_exists(self):
        """Load configuration from file if it exists, create default if not"""
        if os.path.exists(self.config_file):
            # Load existing config
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                    # Update limits from config
                    if "pr_limit" in config:
                        self.pr_limit = config["pr_limit"]
                    if "global_limit" in config:
                        self.global_limit = config["global_limit"]
            except (FileNotFoundError, json.JSONDecodeError):
                pass  # Use defaults
        else:
            # Create default config
            default_config = {
                "global_limit": self.global_limit,
                "pr_limit": self.pr_limit,
            }
            self._write_json_file(self.config_file, default_config)

    def _load_state_from_files(self):
        """Load state from files into memory cache"""
        with self.lock:
            pr_data = self._read_json_file(self.pr_attempts_file)
            self._pr_attempts_cache = self._normalize_pr_attempt_keys(pr_data)

            # Load global runs
            global_data = self._read_json_file(self.global_runs_file)
            self._global_runs_cache = global_data.get("total_runs", 0)

            # Load inflight cache
            inflight_data = self._read_json_file(self.inflight_file)
            self._pr_inflight_cache = {k: int(v) for k, v in inflight_data.items()}

    def _sync_state_to_files(self):
        """Sync in-memory state to files"""
        with self.lock:
            # Sync PR attempts - keys already normalized
            self._write_json_file(self.pr_attempts_file, self._pr_attempts_cache)

            # Sync inflight cache to prevent concurrent processing
            self._write_json_file(self.inflight_file, self._pr_inflight_cache)

    def _make_pr_key(
        self,
        pr_number: Union[int, str],
        repo: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> str:
        """Create a labeled key for PR attempt tracking."""

        repo_part = f"r={repo or ''}"
        pr_part = f"p={pr_number!s}"
        branch_part = f"b={branch or ''}"
        return "||".join((repo_part, pr_part, branch_part))

    def _normalize_pr_attempt_keys(self, raw_data: Dict) -> Dict[str, list]:
        """Normalize legacy PR attempt keys to the labeled format."""

        normalized: Dict[str, list] = {}

        for key, value in (raw_data or {}).items():
            if not isinstance(value, list):
                # Older versions stored counts; coerce to list of failures
                try:
                    count = int(value)
                    value = [{"result": "failure"}] * count
                except (TypeError, ValueError):
                    value = []

            if isinstance(key, str) and "||p=" in key:
                normalized[key] = value
                continue

            repo = None
            branch = None
            pr_number: Union[str, int] = ""

            if isinstance(key, str):
                parts = key.split("::")
                if len(parts) == 1:
                    pr_number = parts[0]
                elif len(parts) == 2:
                    repo, pr_number = parts
                elif len(parts) >= 3:
                    repo, pr_number, branch = parts[0], parts[1], parts[2]
                else:
                    pr_number = key
            else:
                pr_number = key

            normalized_key = self._make_pr_key(pr_number, repo, branch)
            normalized[normalized_key] = value

        return normalized

    def _read_json_file(self, file_path: str) -> dict:
        """Safely read JSON file using shared utility"""
        return json_manager.read_json(file_path, {})

    def _write_json_file(self, file_path: str, data: dict):
        """Atomically write JSON file using shared utility"""
        try:
            if not json_manager.write_json(file_path, data):
                self.logger.error(f"Failed to write safety data file {file_path}")
        except Exception as e:
            self.logger.error(f"Exception writing safety data file {file_path}: {e}")

    def _normalize_global_run_payload(
        self,
        payload: Optional[dict],
        *,
        now: Optional[datetime] = None,
    ) -> tuple[dict, int, bool]:
        """Normalize persisted global run data and determine if it is stale."""

        current_time = now or datetime.now()
        today = current_time.date().isoformat()

        if isinstance(payload, dict):
            data = dict(payload)
        else:
            data = {}

        # Ensure start_date is always present and well-formed
        start_date = data.get("start_date")
        if isinstance(start_date, str):
            try:
                REAL_DATETIME.fromisoformat(start_date)
            except ValueError:
                data["start_date"] = current_time.isoformat()
        else:
            data["start_date"] = current_time.isoformat()

        stored_date = data.get("current_date")
        normalized_date: Optional[str] = None
        if isinstance(stored_date, str):
            try:
                normalized_date = REAL_DATETIME.fromisoformat(stored_date).date().isoformat()
            except ValueError:
                # Support legacy data that stored raw dates without full ISO format
                if len(stored_date) >= ISO_DATE_PREFIX_LENGTH:
                    candidate = stored_date[:ISO_DATE_PREFIX_LENGTH]
                    try:
                        normalized_date = REAL_DATETIME.fromisoformat(candidate).date().isoformat()
                    except ValueError:
                        normalized_date = None
                else:
                    normalized_date = None

        if normalized_date is None:
            try:
                normalized_date = REAL_DATETIME.fromisoformat(data["start_date"]).date().isoformat()
            except ValueError:
                normalized_date = None

        is_stale = normalized_date != today

        if is_stale:
            normalized_date = today
            data["total_runs"] = 0
            data["last_reset"] = current_time.isoformat()

        data["current_date"] = normalized_date or today

        raw_total = data.get("total_runs", 0)
        try:
            total_runs = int(raw_total)
        except (TypeError, ValueError):
            total_runs = 0

        total_runs = max(total_runs, 0)

        data["total_runs"] = total_runs

        last_run = data.get("last_run")
        if last_run is not None:
            if not isinstance(last_run, str):
                data.pop("last_run", None)
            else:
                try:
                    REAL_DATETIME.fromisoformat(last_run)
                except ValueError:
                    data.pop("last_run", None)

        last_reset = data.get("last_reset")
        if last_reset is not None:
            if not isinstance(last_reset, str):
                data.pop("last_reset", None)
            else:
                try:
                    REAL_DATETIME.fromisoformat(last_reset)
                except ValueError:
                    data.pop("last_reset", None)

        if "last_reset" not in data:
            data["last_reset"] = data["start_date"]

        return data, total_runs, is_stale

    def can_process_pr(self, pr_number: Union[int, str], repo: str = None, branch: str = None) -> bool:
        """Check if PR can be processed (under attempt limit)"""
        with self.lock:
            raw_data = self._read_json_file(self.pr_attempts_file)
            self._pr_attempts_cache = self._normalize_pr_attempt_keys(raw_data)

            pr_key = self._make_pr_key(pr_number, repo, branch)
            attempts = list(self._pr_attempts_cache.get(pr_key, []))

            # Check total attempts limit first
            if len(attempts) >= self.pr_limit:
                return False

            # Count consecutive failures from latest attempts
            consecutive_failures = 0
            for attempt in reversed(attempts):
                if attempt.get("result") == "failure":
                    consecutive_failures += 1
                else:
                    break

            # Also block if too many consecutive failures (earlier than total limit)
            return consecutive_failures < self.pr_limit

    def try_process_pr(self, pr_number: Union[int, str], repo: str = None, branch: str = None) -> bool:
        """Atomically reserve a processing slot for PR."""
        with self.lock:
            # Check consecutive failure limit first
            if not self.can_process_pr(pr_number, repo, branch):
                return False

            pr_key = self._make_pr_key(pr_number, repo, branch)
            inflight = self._pr_inflight_cache.get(pr_key, 0)

            # Check if we're at the concurrent processing limit for this PR
            if inflight >= self.pr_limit:
                return False

            # Reserve a processing slot
            self._pr_inflight_cache[pr_key] = inflight + 1

            # Persist immediately to prevent race conditions with concurrent cron jobs
            self._write_json_file(self.inflight_file, self._pr_inflight_cache)

            return True

    def release_pr_slot(self, pr_number: Union[int, str], repo: str = None, branch: str = None):
        """Release a processing slot for PR (call in finally block)"""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)
            inflight = self._pr_inflight_cache.get(pr_key, 0)
            if inflight > 0:
                self._pr_inflight_cache[pr_key] = inflight - 1
                # Persist immediately to prevent race conditions
                self._write_json_file(self.inflight_file, self._pr_inflight_cache)

    def get_pr_attempts(self, pr_number: Union[int, str], repo: str = None, branch: str = None):
        """Get count of consecutive failures for a specific PR."""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)
            attempts = list(self._pr_attempts_cache.get(pr_key, []))

            failure_count = 0
            for attempt in reversed(attempts):
                if attempt.get("result") == "failure":
                    failure_count += 1
                else:
                    break
            return failure_count

    def get_pr_attempt_list(self, pr_number: Union[int, str], repo: str = None, branch: str = None):
        """Get list of attempts for a specific PR (for detailed analysis)"""
        with self.lock:
            # Reload from disk to ensure consistency across multiple managers
            raw_data = self._read_json_file(self.pr_attempts_file)
            self._pr_attempts_cache = self._normalize_pr_attempt_keys(raw_data)
            pr_key = self._make_pr_key(pr_number, repo, branch)
            return self._pr_attempts_cache.get(pr_key, [])

    def record_pr_attempt(self, pr_number: Union[int, str], result: str, repo: str = None, branch: str = None):
        """Record a PR attempt (success or failure)"""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)

            # Create attempt record
            attempt_record = {
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "pr_number": pr_number,
                "repo": repo,
                "branch": branch
            }

            # Get existing attempts list and append new attempt
            attempts = self._pr_attempts_cache.get(pr_key, [])
            attempts.append(attempt_record)
            self._pr_attempts_cache[pr_key] = attempts

            # Update inflight cache
            inflight = self._pr_inflight_cache.get(pr_key, 0)
            if inflight > 0:
                if inflight == 1:
                    self._pr_inflight_cache.pop(pr_key, None)
                else:
                    self._pr_inflight_cache[pr_key] = inflight - 1

            # Sync to file for persistence
            self._sync_state_to_files()

    def can_start_global_run(self) -> bool:
        """Check if a global run can be started"""
        with self.lock:
            # Always refresh from file to detect external resets
            runs = self.get_global_runs()

            if runs < self.global_limit:
                return True

            # Manual override allows limited additional runs (max 2x limit)
            # Never allow unlimited runs even with override
            if self.has_manual_approval() and runs < (self.global_limit * 2):
                return True

            # Hard stop at 2x limit regardless of approval status
            return False

    def get_global_runs(self) -> int:
        """Get total number of global runs (resets daily)"""
        with self.lock:
            normalized_total = 0

            def _refresh(payload: Optional[dict]):
                nonlocal normalized_total
                normalized, total, _ = self._normalize_global_run_payload(payload)
                normalized_total = normalized["total_runs"]
                return normalized

            if not json_manager.update_json(self.global_runs_file, _refresh):
                self.logger.warning(
                    "Falling back to manual refresh for global run counter"
                )
                payload = self._read_json_file(self.global_runs_file)
                normalized, total, _ = self._normalize_global_run_payload(payload)
                normalized_total = total
                self._write_json_file(self.global_runs_file, normalized)

            self._global_runs_cache = normalized_total
            return normalized_total

    def record_global_run(self):
        """Record a global automation run atomically"""
        with self.lock:
            new_total = 0
            current_time = datetime.now()

            def _increment(payload: Optional[dict]):
                nonlocal new_total
                normalized, total, _ = self._normalize_global_run_payload(payload, now=current_time)
                total += 1
                normalized["total_runs"] = total
                normalized["current_date"] = current_time.date().isoformat()
                normalized["last_run"] = current_time.isoformat()
                new_total = total
                return normalized

            if not json_manager.update_json(self.global_runs_file, _increment):
                self.logger.warning(
                    "Falling back to manual increment for global run counter"
                )
                payload = self._read_json_file(self.global_runs_file)
                normalized, total, _ = self._normalize_global_run_payload(payload, now=current_time)
                total += 1
                normalized["total_runs"] = total
                normalized["current_date"] = current_time.date().isoformat()
                normalized["last_run"] = current_time.isoformat()
                new_total = total
                self._write_json_file(self.global_runs_file, normalized)

            self._global_runs_cache = new_total

    def requires_manual_approval(self) -> bool:
        """Check if manual approval is required"""
        return self.get_global_runs() >= self.global_limit

    def has_manual_approval(self) -> bool:
        """Check if valid manual approval exists"""
        with self.lock:
            data = self._read_json_file(self.approval_file)

            if not data.get("approved", False):
                return False

            # Check if approval has expired (configurable hours)
            approval_date_str = data.get("approval_date")
            if not approval_date_str:
                return False

            try:
                approval_date = REAL_DATETIME.fromisoformat(approval_date_str)
            except (TypeError, ValueError):
                return False
            approval_hours = get_automation_limits()["approval_hours"]
            expiry = approval_date + timedelta(hours=approval_hours)

            return datetime.now() < expiry

    def check_and_notify_limits(self):
        """Check limits and send email notifications if thresholds are reached"""
        notifications_sent = []

        with self.lock:
            # Check for PR limits reached
            for pr_key, attempts in self._pr_attempts_cache.items():
                if len(attempts) >= self.pr_limit:
                    self._send_limit_notification(
                        "PR Automation Limit Reached",
                        f"PR {pr_key} has reached the maximum attempt limit of {self.pr_limit}."
                    )
                    notifications_sent.append(f"PR {pr_key}")

            # Check for global limit reached
            if self._global_runs_cache >= self.global_limit:
                self._send_limit_notification(
                    "Global Automation Limit Reached",
                    f"Global automation runs have reached the maximum limit of {self.global_limit}."
                )
                notifications_sent.append("Global limit")

        return notifications_sent

    def _send_limit_notification(self, subject: str, message: str):
        """Send email notification for limit reached"""
        try:
            # Try to use the more complete email notification method
            self._send_notification(subject, message)
        except Exception as e:
            # If email fails, just log it - don't break automation
            self.logger.error("Failed to send email notification: %s", e)
            self.logger.debug("Notification subject: %s", subject)
            self.logger.debug("Notification body: %s", message)

    def grant_manual_approval(self, approver_email: str, approval_time: Optional[datetime] = None):
        """Grant manual approval for continued automation"""
        with self.lock:
            approval_time = approval_time or datetime.now()

            data = {
                "approved": True,
                "approval_date": approval_time.isoformat(),
                "approver": approver_email
            }

            self._write_json_file(self.approval_file, data)

    def _get_smtp_credentials(self):
        """Get SMTP credentials securely from keyring or environment fallback"""
        username = None
        password = None

        if HAS_KEYRING:
            try:
                username = keyring.get_password("worldarchitect-automation", "smtp_username")
                password = keyring.get_password("worldarchitect-automation", "smtp_password")
            except Exception:
                self.logger.debug("Keyring lookup failed for SMTP credentials", exc_info=True)
                username = None
                password = None

        if username is None:
            username = os.environ.get("SMTP_USERNAME") or os.environ.get("EMAIL_USER")
        if password is None:
            password = os.environ.get("SMTP_PASSWORD") or os.environ.get("EMAIL_PASS")

        return username, password

    def _send_notification(self, subject: str, message: str) -> bool:
        """Send email notification with secure credential handling"""
        try:
            # Load email configuration
            smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            username, password = self._get_smtp_credentials()
            to_email = os.environ.get("EMAIL_TO")
            from_email = os.environ.get("EMAIL_FROM") or username

            if not (username and password and to_email and from_email):
                self.logger.info("Email configuration incomplete - skipping notification")
                return False

            msg = MIMEMultipart()
            msg["From"] = from_email
            msg["To"] = to_email
            msg["Subject"] = f"[WorldArchitect Automation] {subject}"

            body = f"""
{message}

Time: {datetime.now().isoformat()}
System: PR Automation Safety Manager

This is an automated notification from the WorldArchitect.AI automation system.
"""

            msg.attach(MIMEText(body, "plain"))

            # Connect and send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            try:
                server.ehlo()
                server.starttls()
                server.ehlo()
                if username and password:
                    server.login(username, password)
                server.send_message(msg)
            finally:
                server.quit()
                self.logger.info("Email notification sent successfully: %s", subject)
            return True

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed - check credentials: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            self.logger.error(f"Email recipients refused: {e}")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error sending notification: {e}")
            return False
        except OSError as e:
            self.logger.error(f"Network error sending notification: {e}")
            return False
        except Exception as e:
            # Log error but don't fail automation
            self.logger.error(f"Unexpected error sending notification: {e}")
            return False

    def _clear_global_runs(self):
        """Clear global runs counter (for testing)"""
        with self.lock:
            self._global_runs_cache = 0
            data = self._read_json_file(self.global_runs_file)
            data["total_runs"] = 0
            data["last_run"] = None
            now = datetime.now()
            data["current_date"] = now.date().isoformat()
            data["last_reset"] = now.isoformat()
            self._write_json_file(self.global_runs_file, data)

    def _clear_pr_attempts(self):
        """Clear PR attempts cache (for testing)"""
        with self.lock:
            self._pr_attempts_cache.clear()
            self._write_json_file(self.pr_attempts_file, {})

    def load_config(self, config_file: str) -> dict:
        """Load configuration from file"""
        try:
            with open(config_file) as f:
                config = json.load(f)
                # Update limits from config
                if "pr_limit" in config:
                    self.pr_limit = config["pr_limit"]
                if "global_limit" in config:
                    self.global_limit = config["global_limit"]
                return config
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_config(self, config_file: str, config: dict):
        """Save configuration to file"""
        self._write_json_file(config_file, config)

    def has_email_config(self) -> bool:
        """Check if email configuration is available"""
        try:
            smtp_server = os.environ.get("SMTP_SERVER")
            username, password = self._get_smtp_credentials()
            return bool(smtp_server and username and password)
        except Exception:
            return False

    def send_notification(self, subject: str, message: str) -> bool:
        """Send email notification - wrapper for _send_notification"""
        try:
            return self._send_notification(subject, message)
        except Exception:
            return False

    def _is_email_configured(self) -> bool:
        """Check if email configuration is complete"""
        try:
            smtp_server = os.environ.get("SMTP_SERVER")
            smtp_port = os.environ.get("SMTP_PORT")
            email_to = os.environ.get("EMAIL_TO")
            username, password = self._get_smtp_credentials()
            return bool(smtp_server and smtp_port and email_to and username and password)
        except Exception:
            return False


def main():
    """CLI interface for safety manager"""

    parser = argparse.ArgumentParser(description="Automation Safety Manager")
    parser.add_argument("--data-dir", default="/tmp/automation_safety",
                        help="Directory for safety data files")
    parser.add_argument("--check-pr", type=int, metavar="PR_NUMBER",
                        help="Check if PR can be processed")
    parser.add_argument("--record-pr", nargs=2, metavar=("PR_NUMBER", "RESULT"),
                        help="Record PR attempt (result: success|failure)")
    parser.add_argument("--repo", type=str,
                        help="Repository name (owner/repo) for PR attempt operations")
    parser.add_argument("--branch", type=str,
                        help="Branch name for PR attempt tracking")
    parser.add_argument("--check-global", action="store_true",
                        help="Check if global run can start")
    parser.add_argument("--record-global", action="store_true",
                        help="Record global run")
    parser.add_argument("--manual_override", type=str, metavar="EMAIL",
                        help="Grant manual override (emergency use only)")
    parser.add_argument("--status", action="store_true",
                        help="Show current status")

    args = parser.parse_args()

    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)

    manager = AutomationSafetyManager(args.data_dir)

    if args.check_pr:
        can_process = manager.can_process_pr(args.check_pr, repo=args.repo, branch=args.branch)
        attempts = manager.get_pr_attempts(args.check_pr, repo=args.repo, branch=args.branch)
        repo_label = f" ({args.repo})" if args.repo else ""
        branch_label = f" [{args.branch}]" if args.branch else ""
        print(
            f"PR #{args.check_pr}{repo_label}{branch_label}: "
            f"{'ALLOWED' if can_process else 'BLOCKED'} ({attempts}/{manager.pr_limit} attempts)"
        )
        sys.exit(0 if can_process else 1)

    elif args.record_pr:
        pr_number, result = args.record_pr
        manager.record_pr_attempt(int(pr_number), result, repo=args.repo, branch=args.branch)
        print(
            f"Recorded {result} for PR #{pr_number}"
            f"{' in ' + args.repo if args.repo else ''}"
            f"{' [' + args.branch + ']' if args.branch else ''}"
        )

    elif args.check_global:
        can_start = manager.can_start_global_run()
        runs = manager.get_global_runs()
        print(f"Global runs: {'ALLOWED' if can_start else 'BLOCKED'} ({runs}/{manager.global_limit} runs)")
        sys.exit(0 if can_start else 1)

    elif args.record_global:
        manager.record_global_run()
        runs = manager.get_global_runs()
        print(f"Recorded global run #{runs}")

    elif args.manual_override:
        manager.grant_manual_approval(args.manual_override)
        print(f"Manual override granted by {args.manual_override}")

    elif args.status:
        runs = manager.get_global_runs()
        has_approval = manager.has_manual_approval()
        requires_approval = manager.requires_manual_approval()

        print(f"Global runs: {runs}/{manager.global_limit}")
        print(f"Requires approval: {requires_approval}")
        print(f"Has approval: {has_approval}")

        pr_data = manager._read_json_file(manager.pr_attempts_file)

        if pr_data:
            print("PR attempts:")
            for pr_key, attempts in pr_data.items():
                count = len(attempts) if isinstance(attempts, list) else int(attempts or 0)
                status = "BLOCKED" if count >= manager.pr_limit else "OK"

                repo_label = ""
                branch_label = ""
                pr_label = pr_key

                if "||" in pr_key:
                    segments = {}
                    for segment in pr_key.split("||"):
                        if "=" in segment:
                            k, v = segment.split("=", 1)
                            segments[k] = v
                    repo_label = segments.get("r", "")
                    pr_label = segments.get("p", pr_label)
                    branch_label = segments.get("b", "")

                display = f"PR #{pr_label}"
                if repo_label:
                    display += f" ({repo_label})"
                if branch_label:
                    display += f" [{branch_label}]"

                print(f"  {display}: {count}/{manager.pr_limit} ({status})")
        else:
            print("No PR attempts recorded")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
