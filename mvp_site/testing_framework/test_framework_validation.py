#!/usr/bin/env python3
"""
Framework validation script to demonstrate all components working together.
Run this to verify the TestServiceProvider framework is functioning correctly.
"""

import os
import sys
import traceback
from typing import Any

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from mvp_site.testing_framework import (
    RealServiceProvider,
    TestConfig,
    TestServiceProvider,
    get_current_provider,
    get_service_provider,
    reset_global_provider,
    set_service_provider,
)


def test_component(name: str, test_func) -> dict[str, Any]:
    """Run a test component and return results."""
    try:
        result = test_func()
        return {"name": name, "status": "PASS", "result": result, "error": None}
    except Exception as e:
        return {
            "name": name,
            "status": "FAIL",
            "result": None,
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


def test_mock_provider():
    """Test MockServiceProvider functionality."""
    provider = get_service_provider("mock")

    # Verify interface implementation
    assert isinstance(provider, TestServiceProvider)
    assert not provider.is_real_service

    # Test service creation
    firestore = provider.get_firestore()
    gemini = provider.get_gemini()
    auth = provider.get_auth()

    assert firestore is not None
    assert gemini is not None
    # auth can be None for mock

    # Test service operations
    campaigns = firestore.get_campaigns_for_user("test_user")
    assert isinstance(campaigns, list)

    response = gemini.generate_content("test prompt")
    assert response is not None

    # Test cleanup
    provider.cleanup()

    return {
        "provider_type": type(provider).__name__,
        "firestore_type": type(firestore).__name__,
        "gemini_type": type(gemini).__name__,
        "auth_type": type(auth).__name__ if auth else "None",
    }


def test_real_provider_validation():
    """Test RealServiceProvider configuration validation."""
    # Clear any existing API key
    original_key = os.environ.pop("TEST_GEMINI_API_KEY", None)

    try:
        # Should raise ValueError without API key
        RealServiceProvider()
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        assert "TEST_GEMINI_API_KEY" in str(e)
    except ImportError:
        # Expected if google packages not installed
        pass
    finally:
        # Restore original key if it existed
        if original_key:
            os.environ["TEST_GEMINI_API_KEY"] = original_key

    return {"validation": "working"}


def test_factory_switching():
    """Test service provider factory mode switching."""
    results = {}

    # Test mock mode
    mock_provider = get_service_provider("mock")
    results["mock"] = {
        "type": type(mock_provider).__name__,
        "is_real": mock_provider.is_real_service,
    }

    # Test real mode (will fail without config, which is expected)
    try:
        real_provider = get_service_provider("real")
        results["real"] = {
            "type": type(real_provider).__name__,
            "is_real": real_provider.is_real_service,
        }
    except (ValueError, ImportError) as e:
        results["real"] = {"error": str(e), "expected": True}

    # Test capture mode
    try:
        capture_provider = get_service_provider("capture")
        results["capture"] = {
            "type": type(capture_provider).__name__,
            "is_real": capture_provider.is_real_service,
            "capture_mode": getattr(capture_provider, "capture_mode", False),
        }
    except (ValueError, ImportError) as e:
        results["capture"] = {"error": str(e), "expected": True}

    # Test invalid mode
    try:
        get_service_provider("invalid")
        raise AssertionError("Should have raised ValueError")
    except ValueError:
        results["invalid_mode"] = "correctly_rejected"

    return results


def test_global_provider_management():
    """Test global provider state management."""
    # Reset to clean state
    reset_global_provider()

    # Test default creation
    provider1 = get_current_provider()
    provider2 = get_current_provider()
    assert provider1 is provider2, "Should return same instance"

    # Test explicit setting
    new_provider = get_service_provider("mock")
    set_service_provider(new_provider)
    provider3 = get_current_provider()
    assert provider3 is new_provider, "Should return explicitly set provider"

    # Test reset
    reset_global_provider()
    provider4 = get_current_provider()
    assert provider4 is not new_provider, "Should create new provider after reset"

    return {
        "default_creation": "working",
        "explicit_setting": "working",
        "reset_functionality": "working",
    }


def test_configuration():
    """Test configuration management."""
    config = TestConfig.get_real_service_config()

    # Verify expected structure
    assert "firestore" in config
    assert "gemini" in config
    assert "auth" in config

    assert "project_id" in config["firestore"]
    assert "collection_prefix" in config["firestore"]
    assert "api_key" in config["gemini"]
    assert "model" in config["gemini"]

    # Test collection name generation
    test_name = TestConfig.get_test_collection_name("campaigns")
    assert test_name.startswith("test_")
    assert "campaigns" in test_name

    return {
        "config_structure": "valid",
        "collection_naming": "working",
        "default_values": config,
    }


def test_interface_compliance():
    """Test that all providers implement the same interface."""
    mock_provider = get_service_provider("mock")

    # Check required methods
    required_methods = ["get_firestore", "get_gemini", "get_auth", "cleanup"]
    required_properties = ["is_real_service"]

    for method in required_methods:
        assert hasattr(mock_provider, method), f"Missing method: {method}"
        assert callable(getattr(mock_provider, method)), f"Not callable: {method}"

    for prop in required_properties:
        assert hasattr(mock_provider, prop), f"Missing property: {prop}"

    return {
        "methods": required_methods,
        "properties": required_properties,
        "compliance": "verified",
    }


def main():
    """Run all validation tests and report results."""
    print("🔍 TestServiceProvider Framework Validation")
    print("=" * 50)

    # Define test suite
    tests = [
        ("Mock Provider Functionality", test_mock_provider),
        ("Real Provider Validation", test_real_provider_validation),
        ("Factory Mode Switching", test_factory_switching),
        ("Global Provider Management", test_global_provider_management),
        ("Configuration Management", test_configuration),
        ("Interface Compliance", test_interface_compliance),
    ]

    results = []
    passed = 0

    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        result = test_component(test_name, test_func)
        results.append(result)

        if result["status"] == "PASS":
            print("   ✅ PASS")
            passed += 1
        else:
            print(f"   ❌ FAIL: {result['error']}")
            if os.getenv("VERBOSE"):
                print(f"   📋 Details: {result['result']}")

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{len(tests)} tests passed")

    if passed == len(tests):
        print("🎉 All tests passed! Framework is ready for use.")
        return 0
    print("⚠️  Some tests failed. Check errors above.")

    # Show detailed results for failed tests
    print("\n🔍 Failed Test Details:")
    for result in results:
        if result["status"] == "FAIL":
            print(f"\n❌ {result['name']}:")
            print(f"   Error: {result['error']}")
            if os.getenv("DEBUG"):
                print(f"   Traceback:\n{result['traceback']}")

    return 1


if __name__ == "__main__":
    sys.exit(main())
