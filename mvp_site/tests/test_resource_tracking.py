#!/usr/bin/env python3
"""
Test resource tracking in debug output for PR changes
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Mock the types module with necessary attributes
class MockTypes:
    class SafetySetting:
        def __init__(self, **kwargs):
            pass
    
    class HarmCategory:
        HARM_CATEGORY_HATE_SPEECH = "hate_speech"
        HARM_CATEGORY_HARASSMENT = "harassment"  
        HARM_CATEGORY_SEXUALLY_EXPLICIT = "sexually_explicit"
        HARM_CATEGORY_DANGEROUS_CONTENT = "dangerous_content"
    
    class HarmBlockThreshold:
        BLOCK_NONE = "block_none"
    
    class Part:
        def __init__(self, text=""):
            self.text = text
    
    class Content:
        def __init__(self, role="", parts=None):
            self.role = role
            self.parts = parts or []
    
    class GenerateContentConfig:
        def __init__(self, **kwargs):
            pass

sys.modules['google.genai'].types = MockTypes()

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
    def mock_call(prompt_contents, model_name, current_prompt_text_for_logging=None, system_instruction_text=None, use_json_mode=False):
        capture_box['instruction'] = system_instruction_text
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
    
    # Test 2: AI always gets debug instructions (backend strips for display)
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
    # AI always gets debug instructions - backend strips them for user display
    assert '[DEBUG_RESOURCES_START]' in captured_instruction, "DEBUG_RESOURCES_START should be in instructions for AI"
    assert '[DEBUG_RESOURCES_END]' in captured_instruction, "DEBUG_RESOURCES_END should be in instructions for AI"
    print("✓ AI always receives debug instructions (backend handles display filtering)")
    
    # Restore original functions
    gemini_service._load_instruction_file = original_load
    gemini_service._call_gemini_api = original_call
    
    print("\n=== Resource Tracking Tests Passed! ===")
    
except Exception as e:
    print(f"✗ Resource tracking test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)