#!/usr/bin/env python3
"""
Automation Safety Wrapper for launchd

This wrapper enforces safety limits before running PR automation:
- Max 10 attempts per PR
- Max 50 total automation runs before requiring manual approval
- Email notifications when limits are reached
"""

import logging
import os
import subprocess
import sys
from pathlib import Path

from .automation_safety_manager import AutomationSafetyManager


def setup_logging() -> logging.Logger:
    """Set up logging for automation wrapper"""
    log_dir = Path.home() / "Library" / "Logs" / "worldarchitect-automation"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "automation_safety.log"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def main() -> int:
    """Main wrapper function with safety checks"""
    logger = setup_logging()
    logger.info("🛡️  Starting automation safety wrapper")

    # Data directory for safety tracking
    data_dir = Path.home() / "Library" / "Application Support" / "worldarchitect-automation"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize safety manager
    manager = AutomationSafetyManager(str(data_dir))

    try:
        # Check global run limits
        if not manager.can_start_global_run():
            logger.warning(f"🚫 Global automation limit reached ({manager.get_global_runs()}/{manager.global_limit} runs)")

            if manager.requires_manual_approval() and not manager.has_manual_approval():
                logger.error("❌ Manual approval required to continue automation")
                logger.info("💡 To grant approval: automation-safety-cli --manual_override user@example.com")

                # Send notification
                manager.check_and_notify_limits()
                return 1

        logger.info(
            f"📊 Global runs before execution: {manager.get_global_runs()}"
            f"/{manager.global_limit}"
        )

        logger.info("🚀 Executing PR automation monitor: jleechanorg_pr_automation.jleechanorg_pr_monitor")

        # Execute with environment variables for safety integration
        env = os.environ.copy()
        env["AUTOMATION_SAFETY_DATA_DIR"] = str(data_dir)
        env["AUTOMATION_SAFETY_WRAPPER"] = "1"

        # Record the global run *before* launching the monitor so the attempt
        # is counted even if the subprocess fails to start or exits early.
        manager.record_global_run()
        logger.info(
            f"📊 Recorded global run {manager.get_global_runs()}/"
            f"{manager.global_limit} prior to monitor execution"
        )

        result = subprocess.run(
            [sys.executable, "-m", "jleechanorg_pr_automation.jleechanorg_pr_monitor"],
            check=False, env=env,
            capture_output=True,
            text=True,
            timeout=3600,
            shell=False,
        )  # 1 hour timeout

        global_runs_after = manager.get_global_runs()
        logger.info(f"📊 Global runs after execution: {global_runs_after}/{manager.global_limit}")

        # Log results
        if result.returncode == 0:
            logger.info("✅ Automation completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"❌ Automation failed with exit code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr.strip()}")

        return result.returncode

    except subprocess.TimeoutExpired:
        logger.error("⏰ Automation timed out after 1 hour")
        return 124
    except Exception as e:
        logger.error(f"💥 Unexpected error in safety wrapper: {e}")
        return 1
    finally:
        # Check and notify about any limit violations
        manager.check_and_notify_limits()


if __name__ == "__main__":
    sys.exit(main())
