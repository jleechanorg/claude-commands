#!/usr/bin/env python3
"""
Testing Utilities Package for WorldArchitect.AI

Centralized test configuration and server management utilities.
"""

from .test_server_manager import (
    ServerInstance,
    TestServerManager,
    get_server_instance,
    start_browser_server,
    start_http_server,
    start_test_server,
    stop_test_server,
    test_server,
)
from .testing_config import (
    BROWSER_PORT,
    DEFAULT_TIMEOUT,
    HTTP_PORT,
    SCREENSHOT_DIR,
    TestConfig,
    TestMode,
    TestType,
    get_browser_base_url,
    get_browser_test_url,
    get_http_base_url,
    get_http_test_url,
    setup_test_environment,
)

__all__ = [
    # Configuration
    "TestConfig",
    "TestType",
    "TestMode",
    "get_browser_base_url",
    "get_http_base_url",
    "get_browser_test_url",
    "get_http_test_url",
    "setup_test_environment",
    "BROWSER_PORT",
    "HTTP_PORT",
    "DEFAULT_TIMEOUT",
    "SCREENSHOT_DIR",
    # Server Management
    "TestServerManager",
    "ServerInstance",
    "start_test_server",
    "stop_test_server",
    "get_server_instance",
    "test_server",
    "start_browser_server",
    "start_http_server",
]
