"""
Global test performance configuration for fast test execution.

This module provides aggressive mocking of expensive operations to speed up tests.
Import this module in tests that need fast execution with minimal overhead.
"""

import os
from unittest.mock import MagicMock, patch

# Performance mode configuration
FAST_MODE = os.environ.get('FAST_TESTS', '0') == '1'
CI_MODE = os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS')

def setup_fast_mode_mocks():
    """Set up aggressive mocking for fast test execution."""
    if not FAST_MODE:
        return []

    # Mock expensive file operations with absolute paths
    file_cache_patch = patch('mvp_site.file_cache.load_file_cached')
    world_loader_patch = patch('mvp_site.world_loader.load_world_content')

    # Mock Gemini service operations with absolute paths
    gemini_continue_patch = patch('mvp_site.gemini_service.continue_story')
    gemini_client_patch = patch('mvp_site.gemini_service.get_client')

    # Start patches
    patches = [
        file_cache_patch,
        world_loader_patch,
        gemini_continue_patch,
        gemini_client_patch
    ]

    mock_configs = {
        file_cache_patch: "Mock file content",
        world_loader_patch: "Mock world content",
        gemini_continue_patch: {
            "narrative": "Mock story response",
            "state_updates": {},
            "entities_mentioned": []
        },
        gemini_client_patch: MagicMock()
    }

    mocks = {}
    for patch_obj in patches:
        mock = patch_obj.start()
        if patch_obj in mock_configs:
            mock.return_value = mock_configs[patch_obj]
        mocks[str(patch_obj)] = mock

    return patches

def cleanup_fast_mode_mocks(patches):
    """Clean up fast mode mocks."""
    for patch_obj in patches:
        patch_obj.stop()

def setup_ci_fast_mode():
    """Set up fast mode for CI environment."""
    if CI_MODE and not os.environ.get('FAST_TESTS'):
        os.environ['FAST_TESTS'] = '1'
        global FAST_MODE
        FAST_MODE = True

# Don't automatically call on import - let tests decide
# setup_ci_fast_mode()

# Performance diagnostic
def print_performance_config():
    """Print current performance configuration."""
    print("🚀 Test Performance Config:")
    print(f"   FAST_TESTS: {os.environ.get('FAST_TESTS', 'not set')}")
    print(f"   CI_MODE: {CI_MODE}")
    print(f"   ENABLE_BROWSER_TESTS: {os.environ.get('ENABLE_BROWSER_TESTS', 'not set')}")
    print(f"   ENABLE_BUILD_TESTS: {os.environ.get('ENABLE_BUILD_TESTS', 'not set')}")
