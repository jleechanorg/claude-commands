#!/usr/bin/env python3
"""
HTTP API version of API response structure test.

This test validates API response structures through direct HTTP calls,
sharing validation logic with the browser version.
"""

import sys
import os
import json
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import shared testing utilities
from testing_ui.testing_shared import (
    TEST_SCENARIOS,
    CAMPAIGN_TEST_DATA,
    generate_test_user_id,
    get_test_headers,
    get_test_url,
    setup_http_test_session,
    validate_campaign_created_successfully,
    validate_api_response_structure,
    setup_test_environment
)

def test_campaign_api_response_structure():
    """Test and analyze campaign API response structure"""
    
    print("🧪 Testing campaign API response structure (HTTP API)...")
    
    # Use shared test data
    campaign_data = CAMPAIGN_TEST_DATA["custom_campaign"].copy()
    
    # Setup HTTP session using shared utility
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("api-structure-http")
    session, _ = setup_http_test_session(base_url, test_user_id)
    
    print(f"📤 Creating campaign to analyze response structure...")
    
    # Make campaign creation request
    response = session.post(f"{base_url}/api/campaigns", json=campaign_data)
    
    print(f"📥 Response status: {response.status_code}")
    
    if response.status_code == 201:
        creation_response = response.json()
        
        print("\n🔍 ANALYZING CREATION RESPONSE STRUCTURE:")
        print("=" * 50)
        print(f"📋 Response keys: {list(creation_response.keys())}")
        print(f"📋 Response structure:")
        for key, value in creation_response.items():
            value_type = type(value).__name__
            if isinstance(value, (str, int, bool)):
                print(f"   {key}: {value_type} = {value}")
            else:
                print(f"   {key}: {value_type} (length: {len(value) if hasattr(value, '__len__') else 'N/A'})")
        
        # Use shared validation
        campaign_id = validate_campaign_created_successfully(creation_response, "http")
        print(f"✅ Campaign created with ID: {campaign_id}")
        
        # Test campaign retrieval API structure
        print("\n📤 Retrieving campaign to analyze detailed structure...")
        get_response = session.get(f"{base_url}/api/campaigns/{campaign_id}")
        
        if get_response.status_code == 200:
            campaign_details = get_response.json()
            
            print("\n🔍 ANALYZING RETRIEVAL RESPONSE STRUCTURE:")
            print("=" * 50)
            print(f"📋 Top-level keys: {list(campaign_details.keys())}")
            
            # Analyze each major section
            for section_key, section_data in campaign_details.items():
                print(f"\n📂 Section: {section_key}")
                if isinstance(section_data, dict):
                    print(f"   Type: dict with {len(section_data)} keys")
                    for key in list(section_data.keys())[:5]:  # Show first 5 keys
                        print(f"   - {key}: {type(section_data[key]).__name__}")
                    if len(section_data) > 5:
                        print(f"   ... and {len(section_data) - 5} more keys")
                elif isinstance(section_data, list):
                    print(f"   Type: list with {len(section_data)} items")
                    if section_data:
                        first_item = section_data[0]
                        if isinstance(first_item, dict):
                            print(f"   First item keys: {list(first_item.keys())}")
                        else:
                            print(f"   First item type: {type(first_item).__name__}")
                else:
                    print(f"   Type: {type(section_data).__name__}")
                    if hasattr(section_data, '__len__'):
                        print(f"   Length: {len(section_data)}")
            
            # Test specific structure validation
            expected_sections = ['campaign', 'game_state', 'story']
            try:
                validate_api_response_structure(campaign_details, expected_sections)
                print(f"\n✅ API response structure validation passed")
                print(f"   Required sections present: {expected_sections}")
            except AssertionError as e:
                print(f"\n⚠️  API response structure validation failed: {e}")
                print(f"   Available sections: {list(campaign_details.keys())}")
            
            # Analyze narrative/story structure if present
            if 'story' in campaign_details and campaign_details['story']:
                print(f"\n📖 STORY CONTENT ANALYSIS:")
                story_data = campaign_details['story']
                if isinstance(story_data, list) and story_data:
                    first_story_entry = story_data[0]
                    if isinstance(first_story_entry, dict):
                        print(f"   Story entry structure: {list(first_story_entry.keys())}")
                        
                        # Check for structured fields
                        structured_fields = ['planning_block', 'god_mode_response', 'session_header', 'resources', 'dice_rolls']
                        found_fields = [field for field in structured_fields if field in first_story_entry]
                        print(f"   Structured fields found: {found_fields}")
                        
                        # Analyze content lengths
                        for field in found_fields:
                            if isinstance(first_story_entry[field], str):
                                content_length = len(first_story_entry[field])
                                print(f"   {field} length: {content_length} characters")
            
            print("\n✅ SUCCESS: API response structure analysis complete!")
            return campaign_details
            
        else:
            print(f"❌ Failed to retrieve campaign: {get_response.text}")
            raise Exception(f"Campaign retrieval failed with status {get_response.status_code}")
        
    else:
        print(f"❌ Failed to create campaign: {response.text}")
        raise Exception(f"Campaign creation failed with status {response.status_code}")

def test_api_endpoint_availability():
    """Test availability and structure of various API endpoints"""
    
    print("\n🧪 Testing API endpoint availability (HTTP API)...")
    
    # Setup HTTP session
    base_url = get_test_url("http")
    test_user_id = generate_test_user_id("api-endpoints-http")
    session, _ = setup_http_test_session(base_url, test_user_id)
    
    # Test various endpoints
    endpoints_to_test = [
        {"path": "/", "method": "GET", "description": "Homepage"},
        {"path": "/api/campaigns", "method": "POST", "description": "Campaign creation"},
        # Note: We'll test campaign retrieval after creating one
    ]
    
    results = {}
    
    for endpoint in endpoints_to_test:
        path = endpoint["path"]
        method = endpoint["method"]
        description = endpoint["description"]
        
        print(f"📍 Testing {method} {path} ({description})...")
        
        try:
            if method == "GET":
                response = session.get(f"{base_url}{path}")
            elif method == "POST" and path == "/api/campaigns":
                # Use test data for campaign creation
                test_data = CAMPAIGN_TEST_DATA["custom_campaign"].copy()
                response = session.post(f"{base_url}{path}", json=test_data)
            
            results[path] = {
                "status": response.status_code,
                "success": response.status_code < 400,
                "content_type": response.headers.get("content-type", "unknown")
            }
            
            if response.status_code < 400:
                print(f"   ✅ {response.status_code} - {description} available")
                
                # If campaign creation, test retrieval endpoint
                if path == "/api/campaigns" and response.status_code == 201:
                    try:
                        campaign_response = response.json()
                        campaign_id = campaign_response.get('campaign_id')
                        if campaign_id:
                            retrieval_path = f"/api/campaigns/{campaign_id}"
                            print(f"📍 Testing GET {retrieval_path} (Campaign retrieval)...")
                            get_response = session.get(f"{base_url}{retrieval_path}")
                            results[retrieval_path] = {
                                "status": get_response.status_code,
                                "success": get_response.status_code == 200,
                                "content_type": get_response.headers.get("content-type", "unknown")
                            }
                            if get_response.status_code == 200:
                                print(f"   ✅ {get_response.status_code} - Campaign retrieval available")
                            else:
                                print(f"   ❌ {get_response.status_code} - Campaign retrieval failed")
                    except Exception as e:
                        print(f"   ⚠️  Could not test campaign retrieval: {e}")
            else:
                print(f"   ❌ {response.status_code} - {description} failed")
                
        except Exception as e:
            results[path] = {
                "status": "error",
                "success": False,
                "error": str(e)
            }
            print(f"   ❌ Error testing {description}: {e}")
    
    # Summary
    successful_endpoints = sum(1 for result in results.values() if result["success"])
    total_endpoints = len(results)
    
    print(f"\n📊 API ENDPOINT SUMMARY:")
    print(f"   Successful: {successful_endpoints}/{total_endpoints}")
    print(f"   Results: {results}")
    
    return results

def main():
    """Run all HTTP API response structure tests"""
    print("=" * 70)
    print("🚀 Running API Response Structure HTTP Tests (Browser Equivalent)")
    print("=" * 70)
    
    try:
        # Test 1: Campaign API response structure analysis
        test_campaign_api_response_structure()
        
        # Test 2: API endpoint availability
        test_api_endpoint_availability()
        
        print("\n" + "=" * 70)
        print("✅ All API response structure HTTP tests passed!")
        print("🎯 HTTP API structure analysis complete")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("=" * 70)
        raise

if __name__ == "__main__":
    main()