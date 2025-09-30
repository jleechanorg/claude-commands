"""
jleechanorg-pr-automation: GitHub PR automation system with safety limits and actionable counting.

This package provides comprehensive PR monitoring and automation capabilities with built-in
safety features, intelligent filtering, and cross-process synchronization.
"""

from .jleechanorg_pr_monitor import JleechanorgPRMonitor
from .automation_safety_manager import AutomationSafetyManager
from .utils import (
    SafeJSONManager,
    setup_logging,
    get_email_config,
    validate_email_config,
    get_automation_limits,
    json_manager,
)

__version__ = "0.1.0"
__author__ = "jleechan"
__email__ = "jlee@jleechan.org"

__all__ = [
    "JleechanorgPRMonitor",
    "AutomationSafetyManager",
    "SafeJSONManager",
    "setup_logging",
    "get_email_config",
    "validate_email_config",
    "get_automation_limits",
    "json_manager",
]
