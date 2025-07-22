#!/usr/bin/env python3
"""
Testing Utilities Package for WorldArchitect.AI

Centralized test configuration and server management utilities.
"""

from .testing_config import (
    TestConfig, TestType, TestMode, 
    get_browser_base_url, get_http_base_url,
    get_browser_test_url, get_http_test_url,
    setup_test_environment,
    BROWSER_PORT, HTTP_PORT, DEFAULT_TIMEOUT, SCREENSHOT_DIR
)

from .test_server_manager import (
    TestServerManager, ServerInstance,
    start_test_server, stop_test_server, get_server_instance,
    test_server, start_browser_server, start_http_server
)

__all__ = [
    # Configuration
    'TestConfig', 'TestType', 'TestMode',
    'get_browser_base_url', 'get_http_base_url',
    'get_browser_test_url', 'get_http_test_url',
    'setup_test_environment',
    'BROWSER_PORT', 'HTTP_PORT', 'DEFAULT_TIMEOUT', 'SCREENSHOT_DIR',
    
    # Server Management  
    'TestServerManager', 'ServerInstance',
    'start_test_server', 'stop_test_server', 'get_server_instance',
    'test_server', 'start_browser_server', 'start_http_server'
]