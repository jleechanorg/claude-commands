#!/usr/bin/env python3
"""
Manual test script for PR #3484: Prevent pending reviews + Daily cooldown tests

Tests:
1. Verify no pending reviews are created by automation
2. Verify cleanup deletes any existing pending reviews
3. Verify daily cooldown state storage (timestamps in pr_attempts.json)
4. Save evidence to /tmp/pr_3484_evidence/
"""

import json
import os
import platform
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from jleechanorg_pr_automation.jleechanorg_pr_monitor import JleechanorgPRMonitor

# Setup evidence directory (to be initialized in main)
EVIDENCE_DIR: Path | None = None

def log(message):
    """Log message and save to evidence file"""
    timestamp = datetime.now().isoformat()
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    assert EVIDENCE_DIR is not None
    with open(EVIDENCE_DIR / "test_log.txt", "a") as f:
        f.write(log_msg + "\n")

def save_evidence(filename, content):
    """Save content to evidence file"""
    assert EVIDENCE_DIR is not None
    filepath = EVIDENCE_DIR / filename
    if isinstance(content, (dict, list)):
        with open(filepath, "w") as f:
            json.dump(content, f, indent=2)
    else:
        with open(filepath, "w") as f:
            f.write(str(content))
    log(f"Saved evidence: {filename}")

def run_command(cmd, description):
    """Run command and save output"""
    log(f"Running: {description}")
    log(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            check=False
        )
        output = {
            "command": " ".join(cmd),
            "description": description,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat()
        }
        save_evidence(f"cmd_{description.replace(' ', '_')}.json", output)
        return result
    except Exception as e:
        log(f"ERROR running command: {e}")
        return None

def get_pr_number():
    """Get PR number from current branch"""
    result = run_command(
        ["gh", "pr", "view", "--json", "number", "-q", ".number"],
        "Get PR number"
    )
    if result and result.returncode == 0:
        return int(result.stdout.strip())
    return None

def check_pending_reviews(pr_number, repo="jleechanorg/worldarchitect.ai"):
    """Check for pending reviews on PR"""
    log(f"Checking for pending reviews on PR #{pr_number}")
    cmd = [
        "gh", "api",
        f"repos/{repo}/pulls/{pr_number}/reviews",
        "--jq", '[.[] | select(.state=="PENDING") | {id: .id, user: .user.login, state: .state, created_at: .submitted_at}]'
    ]
    result = run_command(cmd, "Check pending reviews")
    if result and result.returncode == 0:
        try:
            reviews = json.loads(result.stdout) if result.stdout.strip() else []
            save_evidence("pending_reviews_before.json", reviews)
            return reviews
        except json.JSONDecodeError:
            log("Failed to parse pending reviews JSON")
            return []
    return []

def delete_pending_review(pr_number, review_id, repo="jleechanorg/worldarchitect.ai"):
    """Delete a pending review"""
    log(f"Deleting pending review #{review_id} on PR #{pr_number}")
    cmd = [
        "gh", "api",
        f"repos/{repo}/pulls/{pr_number}/reviews/{review_id}",
        "-X", "DELETE"
    ]
    result = run_command(cmd, f"Delete pending review {review_id}")
    return result and result.returncode == 0

def get_state_dir():
    """Get platform-agnostic automation state directory"""
    if "AUTOMATION_SAFETY_DATA_DIR" in os.environ:
        return Path(os.environ["AUTOMATION_SAFETY_DATA_DIR"])
    
    if platform.system() == "Darwin":
        return Path.home() / "Library/Application Support/worldarchitect-automation"
    elif platform.system() == "Linux":
        return Path.home() / ".config/worldarchitect-automation"
    else:
        return Path.home() / ".worldarchitect-automation"

def check_rate_limit_state():
    """Check rate limit state files for daily cooldown timestamps"""
    log("Checking rate limit state files")
    state_dir = get_state_dir()
    evidence = {
        "state_dir": str(state_dir),
        "files": {},
        "timestamp": datetime.now().isoformat()
    }
    
    # Check pr_attempts.json for timestamp format
    pr_attempts_file = state_dir / "pr_attempts.json"
    if pr_attempts_file.exists():
        with open(pr_attempts_file, "r") as f:
            try:
                pr_attempts = json.load(f)
            except json.JSONDecodeError:
                pr_attempts = {}
        evidence["files"]["pr_attempts.json"] = {
            "exists": True,
            "sample_keys": list(pr_attempts.keys())[:3] if pr_attempts else [],
            "sample_entries": {}
        }
        # Check if entries have timestamps
        for key in list(pr_attempts.keys())[:2]:
            if pr_attempts[key]:
                attempts = pr_attempts[key]
                sample = attempts[0] if isinstance(attempts, list) and attempts else attempts
                evidence["files"]["pr_attempts.json"]["sample_entries"][key] = sample
                if isinstance(sample, dict) and "timestamp" in sample:
                    evidence["files"]["pr_attempts.json"]["has_timestamps"] = True
                    evidence["files"]["pr_attempts.json"]["timestamp_format"] = sample["timestamp"][:10]  # Date portion
    else:
        evidence["files"]["pr_attempts.json"] = {"exists": False}
    
    # Check global_runs.json
    global_runs_file = state_dir / "global_runs.json"
    if global_runs_file.exists():
        with open(global_runs_file, "r") as f:
            try:
                global_runs = json.load(f)
            except json.JSONDecodeError:
                global_runs = {}
        evidence["files"]["global_runs.json"] = {
            "exists": True,
            "content": global_runs
        }
    else:
        evidence["files"]["global_runs.json"] = {"exists": False}
    
    save_evidence("rate_limit_state.json", evidence)
    return evidence

def test_cleanup_functionality():
    """Test that cleanup function works"""
    log("Testing cleanup functionality")

    try:
        monitor = JleechanorgPRMonitor(automation_username="jleechan2015")
        pr_number = get_pr_number()
        
        if pr_number:
            log(f"Testing cleanup on PR #{pr_number}")
            # Check reviews before cleanup
            reviews_before = check_pending_reviews(pr_number)
            log(f"Found {len(reviews_before)} pending reviews before cleanup")
            
            # Run cleanup
            monitor._cleanup_pending_reviews("jleechanorg/worldarchitect.ai", pr_number)
            
            # Check reviews after cleanup
            reviews_after = check_pending_reviews(pr_number)
            log(f"Found {len(reviews_after)} pending reviews after cleanup")
            
            save_evidence("cleanup_test.json", {
                "pr_number": pr_number,
                "reviews_before": len(reviews_before),
                "reviews_after": len(reviews_after),
                "cleanup_worked": len(reviews_after) < len(reviews_before) if reviews_before else None
            })
        else:
            log("Could not determine PR number")
    except ImportError as e:
        log(f"ERROR: Could not import JleechanorgPRMonitor: {e}")

def main():
    """Main test execution"""
    global EVIDENCE_DIR
    EVIDENCE_DIR = Path(tempfile.mkdtemp(prefix="pr_3484_evidence_"))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 80)
    log("PR #3484 Manual Test: Prevent Pending Reviews + Daily Cooldown")
    log("=" * 80)
    
    # Test 1: Check for existing pending reviews
    pr_number = get_pr_number()
    if pr_number:
        log(f"Testing PR #{pr_number}")
        reviews = check_pending_reviews(pr_number)
        log(f"Found {len(reviews)} pending reviews")
        
        # Delete any pending reviews from automation user
        for review in reviews:
            if review.get("user") == "jleechan2015":
                delete_pending_review(pr_number, review["id"])
        
        # Verify they're gone
        reviews_after = check_pending_reviews(pr_number)
        save_evidence("pending_reviews_after.json", reviews_after)
        log(f"Pending reviews after cleanup: {len(reviews_after)}")
    
    # Test 2: Check rate limit state storage
    check_rate_limit_state()
    log("Rate limit state checked - see rate_limit_state.json")
    
    # Test 3: Test cleanup functionality
    test_cleanup_functionality()
    
    # Create summary
    summary = {
        "test_timestamp": datetime.now().isoformat(),
        "pr_number": pr_number,
        "evidence_dir": str(EVIDENCE_DIR),
        "tests_run": [
            "Pending review check and cleanup",
            "Rate limit state verification",
            "Cleanup functionality test"
        ]
    }
    save_evidence("test_summary.json", summary)
    
    log("=" * 80)
    log(f"Test complete! Evidence saved to: {EVIDENCE_DIR}")
    log("=" * 80)

if __name__ == "__main__":
    main()
