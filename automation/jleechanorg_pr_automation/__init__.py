"""
jleechanorg-pr-automation: GitHub PR automation system with safety limits and actionable counting.

This package provides comprehensive PR monitoring and automation capabilities with built-in
safety features, intelligent filtering, and cross-process synchronization.
"""

from .automation_safety_manager import AutomationSafetyManager
from .jleechanorg_pr_monitor import JleechanorgPRMonitor
from .utils import (
    SafeJSONManager,
    get_automation_limits,
    get_email_config,
    json_manager,
    setup_logging,
    validate_email_config,
)

__version__ = "0.2.27"
__author__ = "jleechan"
__email__ = "jlee@jleechan.org"

__all__ = [
    "AutomationSafetyManager",
    "JleechanorgPRMonitor",
    "SafeJSONManager",
    "get_automation_limits",
    "get_email_config",
    "json_manager",
    "setup_logging",
    "validate_email_config",
]
