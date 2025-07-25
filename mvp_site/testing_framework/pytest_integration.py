"""
Pytest integration for the Real-Mode Testing Framework.
Provides pytest-specific fixtures, markers, and utilities.
"""

import os
import time
from collections.abc import Generator
from typing import Any

import pytest

from .factory import get_service_provider, reset_global_provider
from .service_provider import TestServiceProvider

# ============================================================================
# PYTEST FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def test_mode() -> str:
    """Get current test mode from environment."""
    return os.getenv("TEST_MODE", "mock")


@pytest.fixture(scope="function")
def service_provider(test_mode: str) -> Generator[TestServiceProvider, None, None]:
    """Provide appropriate service provider based on TEST_MODE.

    This is the main fixture that most tests should use.
    """
    provider = get_service_provider(test_mode)
    try:
        yield provider
    finally:
        provider.cleanup()


@pytest.fixture(scope="function")
def isolated_service_provider(
    test_mode: str,
) -> Generator[TestServiceProvider, None, None]:
    """Provide isolated service provider with fresh state.

    Use when test isolation is critical.
    """
    reset_global_provider()
    provider = get_service_provider(test_mode)
    try:
        yield provider
    finally:
        provider.cleanup()
        reset_global_provider()


@pytest.fixture(scope="function")
def firestore_client(service_provider: TestServiceProvider):
    """Provide Firestore client (mock or real) based on TEST_MODE."""
    return service_provider.get_firestore()


@pytest.fixture(scope="function")
def gemini_client(service_provider: TestServiceProvider):
    """Provide Gemini client (mock or real) based on TEST_MODE."""
    return service_provider.get_gemini()


@pytest.fixture(scope="function")
def auth_service(service_provider: TestServiceProvider):
    """Provide auth service (mock or real) based on TEST_MODE."""
    return service_provider.get_auth()


@pytest.fixture(scope="function")
def is_real_service(service_provider: TestServiceProvider) -> bool:
    """Check if using real services."""
    return service_provider.is_real_service


@pytest.fixture(scope="function")
def test_services(service_provider: TestServiceProvider) -> dict[str, Any]:
    """Provide all services as a dictionary for convenience."""
    return {
        "provider": service_provider,
        "firestore": service_provider.get_firestore(),
        "gemini": service_provider.get_gemini(),
        "auth": service_provider.get_auth(),
        "is_real": service_provider.is_real_service,
    }


# ============================================================================
# PYTEST MARKERS
# ============================================================================

# Define custom markers for test filtering
pytest_markers = [
    pytest.mark.mock_only,  # Test only runs in mock mode
    pytest.mark.real_only,  # Test only runs in real mode
    pytest.mark.expensive,  # Test is expensive in real mode
    pytest.mark.integration,  # Integration test
    pytest.mark.unit,  # Unit test
]


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker in pytest_markers:
        config.addinivalue_line("markers", f"{marker.name}: {marker.name} test")


def pytest_runtest_setup(item):
    """Setup hook to skip tests based on mode and markers."""
    test_mode = os.getenv("TEST_MODE", "mock")

    # Skip mock-only tests in real mode
    if test_mode in ["real", "capture"] and item.get_closest_marker("mock_only"):
        pytest.skip("Skipped in real mode (mock_only marker)")

    # Skip real-only tests in mock mode
    if test_mode == "mock" and item.get_closest_marker("real_only"):
        pytest.skip("Skipped in mock mode (real_only marker)")


# ============================================================================
# PARAMETRIZED FIXTURES FOR MODE TESTING
# ============================================================================


@pytest.fixture(params=["mock", "real"], ids=["mock-mode", "real-mode"])
def all_modes_service_provider(request) -> Generator[TestServiceProvider, None, None]:
    """Parametrized fixture that runs tests in both mock and real modes.

    Usage:
        def test_works_in_both_modes(all_modes_service_provider):
            firestore = all_modes_service_provider.get_firestore()
            # Test runs twice: once with mock, once with real
    """
    # Skip real mode if no API keys are configured
    if request.param == "real" and not _has_real_service_config():
        pytest.skip("Real mode requires API keys")

    provider = get_service_provider(request.param)
    try:
        yield provider
    finally:
        provider.cleanup()


def _has_real_service_config() -> bool:
    """Check if real service configuration is available."""
    # Check for required environment variables
    required_vars = ["GOOGLE_APPLICATION_CREDENTIALS", "GEMINI_API_KEY"]
    return any(os.getenv(var) for var in required_vars)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def skip_if_real_mode(reason="Test not suitable for real services"):
    """Pytest marker function to skip tests in real mode."""
    test_mode = os.getenv("TEST_MODE", "mock")
    return pytest.mark.skipif(test_mode in ["real", "capture"], reason=reason)


def skip_if_mock_mode(reason="Test requires real services"):
    """Pytest marker function to skip tests in mock mode."""
    test_mode = os.getenv("TEST_MODE", "mock")
    return pytest.mark.skipif(test_mode == "mock", reason=reason)


def requires_real_services(test_func):
    """Decorator that marks test as requiring real services."""
    return pytest.mark.real_only(test_func)


def mock_only(test_func):
    """Decorator that marks test as mock-only."""
    return pytest.mark.mock_only(test_func)


def expensive_test(test_func):
    """Decorator that marks test as expensive (for real mode filtering)."""
    return pytest.mark.expensive(test_func)


# ============================================================================
# PYTEST PLUGINS
# ============================================================================


@pytest.fixture(autouse=True)
def test_mode_info(test_mode: str, request):
    """Auto-use fixture that prints test mode information."""
    if hasattr(request.config.option, "verbose") and request.config.option.verbose:
        print(f"\n🔧 Running {request.node.name} in {test_mode.upper()} mode")


@pytest.fixture(scope="session", autouse=True)
def validate_test_environment():
    """Validate test environment at session start."""
    try:
        provider = get_service_provider()
        provider.cleanup()  # Test basic functionality
        print("✅ Test environment validation passed")
    except Exception as e:
        pytest.exit(f"❌ Test environment validation failed: {e}")


# ============================================================================
# CONFIGURATION HELPERS
# ============================================================================


def configure_pytest_ini():
    """Generate pytest.ini configuration for the framework.

    Call this to create a pytest.ini file with appropriate settings.
    """
    ini_content = """[tool:pytest]
# Real-Mode Testing Framework Configuration

# Test discovery
testpaths = mvp_site
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Custom markers
markers =
    mock_only: Test only runs in mock mode
    real_only: Test only runs in real mode
    expensive: Test is expensive in real mode
    integration: Integration test
    unit: Unit test

# Output formatting
addopts =
    -v
    --tb=short
    --strict-markers

# Test mode filtering examples:
# Run only mock tests: pytest -m "not real_only"
# Run only real tests: pytest -m "not mock_only"
# Skip expensive tests: pytest -m "not expensive"
"""

    with open("pytest.ini", "w") as f:
        f.write(ini_content)

    print("Created pytest.ini with Real-Mode Testing Framework configuration")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================


def example_test_functions():
    """Example test functions showing different patterns."""

    # Basic service provider usage
    def test_basic_usage(service_provider):
        firestore = service_provider.get_firestore()
        doc = firestore.collection("test").document("example")
        doc.set({"test": True})
        result = doc.get()
        assert result.exists

    # Mode-specific testing
    @mock_only
    def test_mock_specific_behavior(firestore_client):
        # This test only runs in mock mode
        # Can test mock-specific behaviors
        pass

    @requires_real_services
    def test_real_integration(gemini_client):
        # This test only runs with real services
        # Tests actual API integration
        pass

    # Parametrized testing across modes
    def test_cross_mode_compatibility(all_modes_service_provider):
        # This test runs in both mock and real modes
        provider = all_modes_service_provider
        services = {
            "firestore": provider.get_firestore(),
            "gemini": provider.get_gemini(),
            "auth": provider.get_auth(),
        }

        # Test logic that should work in both modes
        assert all(service is not None for service in services.values())

    # Resource management
    def test_with_cleanup(test_services):
        firestore = test_services["firestore"]
        is_real = test_services["is_real"]

        if is_real:
            # Use unique collection name in real mode

            collection_name = f"test_{int(time.time())}"
        else:
            # Use simple name in mock mode
            collection_name = "test"

        # Test operations...
        # Cleanup happens automatically via fixture

    return [
        test_basic_usage,
        test_mock_specific_behavior,
        test_real_integration,
        test_cross_mode_compatibility,
        test_with_cleanup,
    ]
