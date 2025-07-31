#!/usr/bin/env python3
"""
Centralized Test Configuration for WorldArchitect.AI

Single source of truth for all test server and testing configuration.
Replaces scattered configuration across multiple test files.
"""

import os
import time
from dataclasses import dataclass
from enum import Enum


class TestMode(Enum):
    """Test execution modes"""

    MOCK = "mock"  # Use mock APIs (free)
    REAL = "real"  # Use real APIs (costs money)
    INTEGRATION = "integration"  # Mixed mock/real for integration tests


class TestType(Enum):
    """Types of tests that need server configuration"""

    BROWSER = "browser"  # Playwright/Puppeteer browser automation
    HTTP = "http"  # Direct HTTP API testing
    INTEGRATION = "integration"  # End-to-end integration tests
    DEVELOPMENT = "dev"  # Local development server


@dataclass
class ServerConfig:
    """Configuration for a test server instance"""

    base_port: int
    port_range: tuple[int, int]  # (min, max) for dynamic allocation
    host: str = "localhost"
    protocol: str = "http"

    def get_base_url(self, port: int | None = None) -> str:
        """Get base URL for server"""
        actual_port = port or self.base_port
        return f"{self.protocol}://{self.host}:{actual_port}"

    def get_test_url(self, port: int | None = None, **params) -> str:
        """Get test URL with parameters"""
        base_url = self.get_base_url(port)
        if not params:
            return base_url

        # Build query string
        query_parts = []
        for key, value in params.items():
            query_parts.append(f"{key}={value}")
        query_string = "&".join(query_parts)

        return f"{base_url}?{query_string}"


class TestConfig:
    """Centralized test configuration manager"""

    # Server configurations by test type
    SERVERS: dict[TestType, ServerConfig] = {
        TestType.BROWSER: ServerConfig(base_port=8081, port_range=(8080, 8090)),
        TestType.HTTP: ServerConfig(base_port=8086, port_range=(8085, 8095)),
        TestType.INTEGRATION: ServerConfig(base_port=8088, port_range=(8087, 8097)),
        TestType.DEVELOPMENT: ServerConfig(base_port=5005, port_range=(5000, 5010)),
    }

    # Common test parameters
    DEFAULT_TEST_USER_ID = "test-user-123"
    DEFAULT_TIMEOUT_MS = 10000  # 10 seconds
    SHORT_TIMEOUT_MS = 5000  # 5 seconds
    LONG_TIMEOUT_MS = 30000  # 30 seconds

    # Test mode parameters
    TEST_MODE_PARAMS = {"test_mode": "true", "test_user_id": DEFAULT_TEST_USER_ID}

    # Mock API control
    MOCK_ENV_VARS = {
        "USE_MOCK_FIREBASE": "true",
        "USE_MOCK_GEMINI": "true",
        "TESTING": "true",
    }

    # Directory paths
    SCREENSHOT_DIR = "/tmp/worldarchitectai/browser"
    LOGS_DIR = "/tmp/worldarchitectai_logs"
    TEMP_DIR = "/tmp/worldarchitectai"

    @classmethod
    def get_server_config(cls, test_type: TestType) -> ServerConfig:
        """Get server configuration for test type"""
        return cls.SERVERS[test_type]

    @classmethod
    def get_base_url(cls, test_type: TestType, port: int | None = None) -> str:
        """Get base URL for test type"""
        server_config = cls.get_server_config(test_type)
        return server_config.get_base_url(port)

    @classmethod
    def get_test_url(
        cls,
        test_type: TestType,
        port: int | None = None,
        with_test_params: bool = True,
        **extra_params,
    ) -> str:
        """Get test URL with standard test parameters"""
        server_config = cls.get_server_config(test_type)

        params = {}
        if with_test_params:
            params.update(cls.TEST_MODE_PARAMS)
        params.update(extra_params)

        return server_config.get_test_url(port, **params)

    @classmethod
    def setup_mock_environment(cls) -> None:
        """Set up environment variables for mock testing"""
        for key, value in cls.MOCK_ENV_VARS.items():
            os.environ[key] = value

    @classmethod
    def get_port_from_env(cls, test_type: TestType) -> int:
        """Get port from environment variable or use default"""
        env_var = f"TEST_PORT_{test_type.value.upper()}"
        env_port = os.environ.get(env_var)
        if env_port:
            return int(env_port)
        return cls.get_server_config(test_type).base_port

    @classmethod
    def generate_test_user_id(cls, prefix: str = "test") -> str:
        """Generate unique test user ID"""
        timestamp = int(time.time())
        return f"{prefix}-user-{timestamp}"


# Convenience functions for backward compatibility
def get_browser_base_url(port: int | None = None) -> str:
    """Get browser test base URL"""
    return TestConfig.get_base_url(TestType.BROWSER, port)


def get_http_base_url(port: int | None = None) -> str:
    """Get HTTP test base URL"""
    return TestConfig.get_base_url(TestType.HTTP, port)


def get_browser_test_url(port: int | None = None, **params) -> str:
    """Get browser test URL with test mode parameters"""
    return TestConfig.get_test_url(TestType.BROWSER, port, **params)


def get_http_test_url(port: int | None = None, **params) -> str:
    """Get HTTP test URL"""
    return TestConfig.get_test_url(
        TestType.HTTP, port, with_test_params=False, **params
    )


def setup_test_environment(test_mode: TestMode = TestMode.MOCK) -> None:
    """Set up test environment"""
    if test_mode == TestMode.MOCK:
        TestConfig.setup_mock_environment()
    # Add real API setup if needed


# Export key constants for easy access
BROWSER_PORT = TestConfig.get_server_config(TestType.BROWSER).base_port
HTTP_PORT = TestConfig.get_server_config(TestType.HTTP).base_port
DEFAULT_TIMEOUT = TestConfig.DEFAULT_TIMEOUT_MS
SCREENSHOT_DIR = TestConfig.SCREENSHOT_DIR
