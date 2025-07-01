#!/usr/bin/env python3
"""
Test resource tracking in debug output for PR changes
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n=== Testing Resource Tracking in Debug Output ===")

# Mock the necessary imports
class MockClient:
    class models:
        @staticmethod
        def generate_content(**kwargs):
            class Response:
                text = "Test response"
            return Response()

sys.modules['google'] = type(sys)('google')
sys.modules['google.genai'] = type(sys)('genai')
sys.modules['google.genai'].Client = lambda **kwargs: MockClient()
sys.modules['google.genai'].types = type(sys)('types')

# Set dummy API key
os.environ['GEMINI_API_KEY'] = 'dummy_key'

try:
    # Now we can import gemini_service
    import gemini_service
    from game_state import GameState
    
    # Clear cache
    gemini_service._loaded_instructions_cache.clear()
    
    # Mock load instruction file
    original_load = gemini_service._load_instruction_file
    def mock_load(instruction_type):
        return f"Mock content for {instruction_type}"
    
    gemini_service._load_instruction_file = mock_load
    
    # Test 1: Debug mode includes resource tracking
    gs = GameState(debug_mode=True)
    
    # Capture the system instruction by mocking _call_gemini_api
    capture_box = {'instruction': None}
    original_call = gemini_service._call_gemini_api
    def mock_call(system_instruction, model, contents, **kwargs):
        capture_box['instruction'] = system_instruction
        class Response:
            text = "Test response"
        return Response()
    
    gemini_service._call_gemini_api = mock_call
    
    # Call continue_story
    gemini_service.continue_story(
        "test input",
        "character",
        [],
        gs,
        ['narrative']
    )
    
    # Check for resource tracking in captured instruction
    captured_instruction = capture_box['instruction']
    assert captured_instruction is not None, "System instruction not captured"
    assert '[DEBUG_RESOURCES_START]' in captured_instruction, "Missing DEBUG_RESOURCES_START tag"
    assert '[DEBUG_RESOURCES_END]' in captured_instruction, "Missing DEBUG_RESOURCES_END tag"
    assert 'EP used' in captured_instruction, "Missing EP resource tracking"
    assert 'spell slot' in captured_instruction, "Missing spell slot tracking"
    assert 'short rest' in captured_instruction, "Missing short rest tracking"
    print("✓ Debug mode includes resource tracking tags and examples")
    
    # Test 2: Non-debug mode excludes resource tracking
    capture_box['instruction'] = None
    gs_no_debug = GameState(debug_mode=False)
    
    gemini_service.continue_story(
        "test input",
        "character", 
        [],
        gs_no_debug,
        ['narrative']
    )
    
    captured_instruction = capture_box['instruction']
    assert captured_instruction is not None, "System instruction not captured"
    assert '[DEBUG_RESOURCES_START]' not in captured_instruction, "DEBUG_RESOURCES_START should not be in non-debug mode"
    assert '[DEBUG_RESOURCES_END]' not in captured_instruction, "DEBUG_RESOURCES_END should not be in non-debug mode"
    print("✓ Non-debug mode excludes resource tracking")
    
    # Restore original functions
    gemini_service._load_instruction_file = original_load
    gemini_service._call_gemini_api = original_call
    
    print("\n=== Resource Tracking Tests Passed! ===")
    
except Exception as e:
    print(f"✗ Resource tracking test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)