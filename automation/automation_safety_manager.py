#!/usr/bin/env python3
"""
Automation Safety Manager - GREEN Phase Implementation

Minimal implementation to pass the RED phase tests with:
- PR attempt limits (max 5 per PR)
- Global run limits (max 50 total)
- Manual approval system
- Thread-safe operations
- Email notifications
"""

import argparse
import json
import os
import threading
import smtplib
import tempfile
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional


class AutomationSafetyManager:
    """Thread-safe automation safety manager with configurable limits"""

    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.lock = threading.RLock()  # Use RLock to prevent deadlock

        # Configurable limits via environment
        self.pr_limit = int(os.environ.get('AUTOMATION_PR_LIMIT', '5'))
        self.global_limit = int(os.environ.get('AUTOMATION_GLOBAL_LIMIT', '50'))

        # File paths
        self.pr_attempts_file = os.path.join(data_dir, "pr_attempts.json")
        self.global_runs_file = os.path.join(data_dir, "global_runs.json")
        self.approval_file = os.path.join(data_dir, "manual_approval.json")

        # In-memory counters for thread safety
        self._pr_attempts_cache = {}
        self._global_runs_cache = 0

        # Initialize files if they don't exist
        self._ensure_files_exist()

        # Load initial state from files
        self._load_state_from_files()

    def _ensure_files_exist(self):
        """Initialize tracking files if they don't exist"""
        os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.pr_attempts_file):
            self._write_json_file(self.pr_attempts_file, {})

        if not os.path.exists(self.global_runs_file):
            self._write_json_file(self.global_runs_file, {
                "total_runs": 0,
                "start_date": datetime.now().isoformat()
            })

        if not os.path.exists(self.approval_file):
            self._write_json_file(self.approval_file, {
                "approved": False,
                "approval_date": None
            })

    def _load_state_from_files(self):
        """Load state from files into memory cache"""
        with self.lock:
            # Load PR attempts - keep all string keys as-is
            pr_data = self._read_json_file(self.pr_attempts_file)
            self._pr_attempts_cache = pr_data.copy()

            # Load global runs
            global_data = self._read_json_file(self.global_runs_file)
            self._global_runs_cache = global_data.get("total_runs", 0)

    def _sync_state_to_files(self):
        """Sync in-memory state to files"""
        with self.lock:
            # Sync PR attempts - keys are already strings
            self._write_json_file(self.pr_attempts_file, self._pr_attempts_cache)

            # Sync global runs
            global_data = self._read_json_file(self.global_runs_file)
            global_data["total_runs"] = self._global_runs_cache
            self._write_json_file(self.global_runs_file, global_data)

    def _make_pr_key(self, pr_number: int, repo: str = None, branch: str = None) -> str:
        """Create a standardized key for PR attempts tracking"""
        if repo and branch:
            return f"{repo}-{pr_number}-{branch}"
        elif isinstance(pr_number, int):
            # For backward compatibility and simple testing
            return str(pr_number)
        else:
            return str(pr_number)

    def _read_json_file(self, file_path: str) -> dict:
        """Safely read JSON file with file locking"""
        import fcntl
        try:
            with open(file_path, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock for reading
                data = json.load(f)
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_json_file(self, file_path: str, data: dict):
        """Atomically write JSON file with file locking to prevent corruption"""
        import fcntl
        # Use temporary file with atomic rename for safety
        dir_path = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)

        # Create temporary file in same directory to ensure atomic rename works
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=dir_path,
            prefix=f".{file_name}.",
            suffix=".tmp",
            delete=False
        ) as temp_file:
            fcntl.flock(temp_file.fileno(), fcntl.LOCK_EX)  # Exclusive lock for writing
            json.dump(data, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Force write to disk
            fcntl.flock(temp_file.fileno(), fcntl.LOCK_UN)  # Unlock
            temp_path = temp_file.name

        # Atomic rename - this operation is atomic on POSIX systems
        os.rename(temp_path, file_path)

    def can_process_pr(self, pr_number: int, repo: str = None, branch: str = None) -> bool:
        """Check if PR can be processed (under attempt limit)"""
        with self.lock:
            attempts = self.get_pr_attempts(pr_number, repo, branch)
            return attempts < self.pr_limit

    def try_process_pr(self, pr_number: int, repo: str = None, branch: str = None) -> bool:
        """Atomically check if PR can be processed and increment failure counter if so"""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)
            current_attempts = self._pr_attempts_cache.get(pr_key, 0)

            if current_attempts < self.pr_limit:
                # Atomically increment the failure counter in memory
                self._pr_attempts_cache[pr_key] = current_attempts + 1
                # Sync to file immediately for persistence
                self._sync_state_to_files()
                return True
            return False

    def get_pr_attempts(self, pr_number: int, repo: str = None, branch: str = None) -> int:
        """Get number of attempts for a specific PR"""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)
            return self._pr_attempts_cache.get(pr_key, 0)

    def record_pr_attempt(self, pr_number: int, result: str, repo: str = None, branch: str = None):
        """Record a PR attempt (success or failure)"""
        with self.lock:
            pr_key = self._make_pr_key(pr_number, repo, branch)

            if result == "success":
                # Reset counter on success
                if pr_key in self._pr_attempts_cache:
                    del self._pr_attempts_cache[pr_key]
            else:
                # Increment counter on failure
                self._pr_attempts_cache[pr_key] = self._pr_attempts_cache.get(pr_key, 0) + 1

            # Sync to file for persistence
            self._sync_state_to_files()

    def can_start_global_run(self) -> bool:
        """Check if a global run can be started"""
        with self.lock:
            runs = self.get_global_runs()
            if runs < self.global_limit:
                return True

            # Check if we have valid manual approval for beyond limit
            return self.has_manual_approval()

    def get_global_runs(self) -> int:
        """Get total number of global runs"""
        with self.lock:
            data = self._read_json_file(self.global_runs_file)
            return data.get("total_runs", 0)

    def record_global_run(self):
        """Record a global automation run"""
        with self.lock:
            data = self._read_json_file(self.global_runs_file)
            data["total_runs"] = data.get("total_runs", 0) + 1
            data["last_run"] = datetime.now().isoformat()
            self._write_json_file(self.global_runs_file, data)

    def requires_manual_approval(self) -> bool:
        """Check if manual approval is required"""
        return self.get_global_runs() >= self.global_limit

    def has_manual_approval(self) -> bool:
        """Check if valid manual approval exists"""
        with self.lock:
            data = self._read_json_file(self.approval_file)

            if not data.get("approved", False):
                return False

            # Check if approval has expired (24 hours)
            approval_date_str = data.get("approval_date")
            if not approval_date_str:
                return False

            approval_date = datetime.fromisoformat(approval_date_str)
            expiry = approval_date + timedelta(hours=24)

            return datetime.now() < expiry

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

    def check_and_notify_limits(self):
        """Check limits and send notifications if needed"""
        # Check PR limits
        pr_data = self._read_json_file(self.pr_attempts_file)

        for pr_number, attempts in pr_data.items():
            if attempts >= self.pr_limit:
                self._send_notification(
                    f"PR #{pr_number} Limit Reached",
                    f"PR #{pr_number} has reached {attempts} attempts (limit: {self.pr_limit})"
                )

        # Check global limits
        if self.requires_manual_approval() and not self.has_manual_approval():
            self._send_notification(
                "Global Automation Limit Reached",
                f"Automation has reached {self.get_global_runs()} runs (limit: {self.global_limit}). Manual approval required."
            )

    def _send_notification(self, subject: str, message: str):
        """Send email notification"""
        try:
            # Load email configuration
            smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.environ.get('SMTP_PORT', '587'))
            username = os.environ.get('SMTP_USERNAME')
            password = os.environ.get('SMTP_PASSWORD')
            from_email = os.environ.get('MEMORY_EMAIL_FROM')
            to_email = os.environ.get('MEMORY_EMAIL_TO')

            if not all([username, password, from_email, to_email]):
                # Skip email if configuration is missing
                return

            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = f"[WorldArchitect Automation] {subject}"

            body = f"""
{message}

Time: {datetime.now().isoformat()}
System: PR Automation Safety Manager

This is an automated notification from the WorldArchitect.AI automation system.
"""

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()

        except Exception as e:
            # Log error but don't fail automation
            print(f"Failed to send notification: {e}")


def main():
    """CLI interface for safety manager"""

    parser = argparse.ArgumentParser(description='Automation Safety Manager')
    parser.add_argument('--data-dir', default='/tmp/automation_safety',
                        help='Directory for safety data files')
    parser.add_argument('--check-pr', type=int, metavar='PR_NUMBER',
                        help='Check if PR can be processed')
    parser.add_argument('--record-pr', nargs=2, metavar=('PR_NUMBER', 'RESULT'),
                        help='Record PR attempt (result: success|failure)')
    parser.add_argument('--check-global', action='store_true',
                        help='Check if global run can start')
    parser.add_argument('--record-global', action='store_true',
                        help='Record global run')
    parser.add_argument('--approve', type=str, metavar='EMAIL',
                        help='Grant manual approval')
    parser.add_argument('--status', action='store_true',
                        help='Show current status')

    args = parser.parse_args()

    # Ensure data directory exists
    os.makedirs(args.data_dir, exist_ok=True)

    manager = AutomationSafetyManager(args.data_dir)

    if args.check_pr:
        can_process = manager.can_process_pr(args.check_pr)
        attempts = manager.get_pr_attempts(args.check_pr)
        print(f"PR #{args.check_pr}: {'ALLOWED' if can_process else 'BLOCKED'} ({attempts}/{manager.pr_limit} attempts)")
        exit(0 if can_process else 1)

    elif args.record_pr:
        pr_number, result = args.record_pr
        manager.record_pr_attempt(int(pr_number), result)
        print(f"Recorded {result} for PR #{pr_number}")

    elif args.check_global:
        can_start = manager.can_start_global_run()
        runs = manager.get_global_runs()
        print(f"Global runs: {'ALLOWED' if can_start else 'BLOCKED'} ({runs}/{manager.global_limit} runs)")
        exit(0 if can_start else 1)

    elif args.record_global:
        manager.record_global_run()
        runs = manager.get_global_runs()
        print(f"Recorded global run #{runs}")

    elif args.approve:
        manager.grant_manual_approval(args.approve)
        print(f"Manual approval granted by {args.approve}")

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
            for pr_number, attempts in pr_data.items():
                status = "BLOCKED" if attempts >= manager.pr_limit else "OK"
                print(f"  PR #{pr_number}: {attempts}/{manager.pr_limit} ({status})")
        else:
            print("No PR attempts recorded")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
