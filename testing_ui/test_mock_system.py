#!/usr/bin/env python3
"""
Test the mock Gemini system for UI testing
Validates that mock responses work correctly for both campaign types
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

from mock_data.gemini_mock_service import MockGeminiService, mock_gemini_get_initial_story

def test_mock_service():
    """Test the mock Gemini service directly"""
    print("🧪 Testing Mock Gemini Service")
    print("=" * 40)
    
    mock_service = MockGeminiService()
    
    # Test Dragon Knight campaign
    print("\n🐲 Testing Dragon Knight Campaign:")
    dragon_knight_data = {
        'campaign_type': 'dragon-knight',
        'character': 'Ser Arion',
        'setting': 'World of Assiah'
    }
    
    dk_response = mock_service.get_initial_story(dragon_knight_data)
    print(f"   Success: {dk_response.get('success', False)}")
    print(f"   Response length: {len(dk_response.get('response', ''))}")
    print(f"   Preview: {dk_response.get('response', '')[:100]}...")
    print(f"   Has planning block: {'planning_block' in dk_response}")
    
    # Test Custom campaign
    print("\n✨ Testing Custom Campaign:")
    custom_data = {
        'campaign_type': 'custom',
        'character': 'Astarion who ascended',
        'setting': "Baldur's Gate"
    }
    
    custom_response = mock_service.get_initial_story(custom_data)
    print(f"   Success: {custom_response.get('success', False)}")
    print(f"   Response length: {len(custom_response.get('response', ''))}")
    print(f"   Preview: {custom_response.get('response', '')[:100]}...")
    print(f"   Has planning block: {'planning_block' in custom_response}")
    
    # Test monkey patch function
    print("\n🔧 Testing Monkey Patch Function:")
    
    # Dragon Knight prompt (what backend generates)
    dk_prompt = """You are Ser Arion, a 16 year old honorable knight on your first mission, sworn to protect the vast Celestial Imperium. For decades, the Empire has been ruled by the iron-willed Empress Sariel, a ruthless tyrant who uses psychic power to crush dissent. While her methods are terrifying, her reign has brought undeniable benefits: the roads are safe, commerce thrives, and the Imperium has never been stronger. But dark whispers speak of the Dragon Knights - an ancient order that once served the realm before mysteriously vanishing. As you journey through this morally complex world, you must decide: will you serve the tyrant who brings order, or seek a different path?"""
    
    dk_mock_response = mock_gemini_get_initial_story(dk_prompt)
    print(f"   Dragon Knight mock success: {dk_mock_response.get('success', False)}")
    
    # Custom prompt (what backend generates)
    custom_prompt = "Character: Astarion who ascended\nSetting: Baldur's Gate"
    custom_mock_response = mock_gemini_get_initial_story(custom_prompt)
    print(f"   Custom mock success: {custom_mock_response.get('success', False)}")
    
    return dk_response.get('success', False) and custom_response.get('success', False)

def test_with_real_backend():
    """Test that we can patch the real backend to use mocks"""
    print("\n🔗 Testing Backend Integration:")
    
    try:
        # Import the real gemini service
        import gemini_service
        
        # Store original function
        original_get_initial_story = gemini_service.get_initial_story
        
        # Patch with mock
        gemini_service.get_initial_story = mock_gemini_get_initial_story
        print("   ✅ Successfully patched gemini_service.get_initial_story")
        
        # Test the patched function
        test_response = gemini_service.get_initial_story("Character: Test\nSetting: Test World")
        print(f"   ✅ Patched function works: {test_response.get('success', False)}")
        
        # Restore original function
        gemini_service.get_initial_story = original_get_initial_story
        print("   ✅ Restored original function")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Backend integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Mock Gemini System Test")
    print("=" * 50)
    
    # Test mock service
    service_success = test_mock_service()
    
    # Test backend integration
    backend_success = test_with_real_backend()
    
    print("\n📊 Test Results:")
    print(f"   Mock Service: {'✅ PASS' if service_success else '❌ FAIL'}")
    print(f"   Backend Integration: {'✅ PASS' if backend_success else '❌ FAIL'}")
    
    if service_success and backend_success:
        print("\n🎉 Mock system is ready for UI testing!")
        print("💡 Use USE_MOCKS=true to enable mock responses")
    else:
        print("\n💥 Mock system needs fixes before use")
    
    sys.exit(0 if (service_success and backend_success) else 1)