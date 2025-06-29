#!/usr/bin/env python3
"""
API Integration Validation Script
Tests all existing API endpoints to ensure frontend modernization won't break compatibility
Part of Phase 0: Risk Assessment & Preparation
"""

import requests
import json
import sys
import os
from datetime import datetime

# Base URL for local testing
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

class APIValidator:
    def __init__(self):
        self.results = []
        self.test_user_id = "test-validation-user"
        self.test_campaign_id = None
        
    def log_result(self, endpoint, method, status, details=""):
        result = {
            "endpoint": endpoint,
            "method": method,
            "status": "PASS" if status else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        status_symbol = "✅" if status else "❌"
        print(f"{status_symbol} {method} {endpoint} - {details}")
    
    def test_health_check(self):
        """Test basic server connectivity"""
        try:
            response = requests.get(BASE_URL, timeout=10)
            success = response.status_code == 200
            self.log_result("/", "GET", success, f"Status: {response.status_code}")
            return success
        except Exception as e:
            self.log_result("/", "GET", False, f"Connection error: {str(e)}")
            return False
    
    def test_campaign_creation(self):
        """Test POST /api/campaigns"""
        endpoint = "/api/campaigns"
        headers = {
            'Content-Type': 'application/json',
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id
        }
        
        # Test campaign data matching current form structure
        campaign_data = {
            "campaign_name": "API Validation Test Campaign",
            "setting": "fantasy",
            "tone": "balanced",
            "prompt": "A test campaign for API validation",
            "companions": []
        }
        
        try:
            response = requests.post(f"{API_BASE}{endpoint}", 
                                   json=campaign_data, 
                                   headers=headers, 
                                   timeout=30)
            
            success = response.status_code == 200
            if success:
                response_data = response.json()
                if response_data.get('success') and response_data.get('campaign_id'):
                    self.test_campaign_id = response_data['campaign_id']
                    self.log_result(endpoint, "POST", True, f"Campaign created: {self.test_campaign_id}")
                else:
                    self.log_result(endpoint, "POST", False, f"Invalid response format: {response_data}")
                    success = False
            else:
                self.log_result(endpoint, "POST", False, f"Status: {response.status_code}, Response: {response.text}")
            
            return success
        except Exception as e:
            self.log_result(endpoint, "POST", False, f"Error: {str(e)}")
            return False
    
    def test_campaign_listing(self):
        """Test GET /api/campaigns"""
        endpoint = "/api/campaigns"
        headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id
        }
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                campaigns = response.json()
                if isinstance(campaigns, list):
                    self.log_result(endpoint, "GET", True, f"Retrieved {len(campaigns)} campaigns")
                else:
                    self.log_result(endpoint, "GET", False, f"Expected list, got: {type(campaigns)}")
                    success = False
            else:
                self.log_result(endpoint, "GET", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_result(endpoint, "GET", False, f"Error: {str(e)}")
            return False
    
    def test_campaign_details(self):
        """Test GET /api/campaigns/{id}"""
        if not self.test_campaign_id:
            self.log_result("/api/campaigns/{id}", "GET", False, "No test campaign ID available")
            return False
        
        endpoint = f"/api/campaigns/{self.test_campaign_id}"
        headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id
        }
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}", headers=headers, timeout=10)
            success = response.status_code == 200
            
            if success:
                campaign = response.json()
                if campaign.get('campaign_id') == self.test_campaign_id:
                    self.log_result(endpoint, "GET", True, "Campaign details retrieved successfully")
                else:
                    self.log_result(endpoint, "GET", False, f"Campaign ID mismatch: {campaign.get('campaign_id')}")
                    success = False
            else:
                self.log_result(endpoint, "GET", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_result(endpoint, "GET", False, f"Error: {str(e)}")
            return False
    
    def test_campaign_update(self):
        """Test PATCH /api/campaigns/{id}"""
        if not self.test_campaign_id:
            self.log_result("/api/campaigns/{id}", "PATCH", False, "No test campaign ID available")
            return False
        
        endpoint = f"/api/campaigns/{self.test_campaign_id}"
        headers = {
            'Content-Type': 'application/json',
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id
        }
        
        update_data = {
            "last_played": datetime.now().isoformat(),
            "notes": "Updated during API validation"
        }
        
        try:
            response = requests.patch(f"{API_BASE}{endpoint}", 
                                    json=update_data, 
                                    headers=headers, 
                                    timeout=10)
            
            success = response.status_code == 200
            if success:
                self.log_result(endpoint, "PATCH", True, "Campaign updated successfully")
            else:
                self.log_result(endpoint, "PATCH", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_result(endpoint, "PATCH", False, f"Error: {str(e)}")
            return False
    
    def test_story_interaction(self):
        """Test POST /api/campaigns/{id}/interaction"""
        if not self.test_campaign_id:
            self.log_result("/api/campaigns/{id}/interaction", "POST", False, "No test campaign ID available")
            return False
        
        endpoint = f"/api/campaigns/{self.test_campaign_id}/interaction"
        headers = {
            'Content-Type': 'application/json',
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': self.test_user_id
        }
        
        interaction_data = {
            "input": "I look around the starting area."
        }
        
        try:
            # Use shorter timeout for AI interactions
            response = requests.post(f"{API_BASE}{endpoint}", 
                                   json=interaction_data, 
                                   headers=headers, 
                                   timeout=60)
            
            success = response.status_code == 200
            if success:
                response_data = response.json()
                if response_data.get('response'):
                    self.log_result(endpoint, "POST", True, "Story interaction successful")
                else:
                    self.log_result(endpoint, "POST", False, f"No response content: {response_data}")
                    success = False
            else:
                self.log_result(endpoint, "POST", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_result(endpoint, "POST", False, f"Error: {str(e)}")
            return False
    
    def test_file_export(self):
        """Test GET /api/campaigns/{id}/export"""
        if not self.test_campaign_id:
            self.log_result("/api/campaigns/{id}/export", "GET", False, "No test campaign ID available")
            return False
        
        # Test each export format
        formats = ['pdf', 'docx', 'txt']
        all_success = True
        
        for format_type in formats:
            endpoint = f"/api/campaigns/{self.test_campaign_id}/export"
            headers = {
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': self.test_user_id
            }
            params = {'format': format_type}
            
            try:
                response = requests.get(f"{API_BASE}{endpoint}", 
                                      headers=headers, 
                                      params=params, 
                                      timeout=30)
                
                success = response.status_code == 200
                if success:
                    # Check if we got file content
                    content_length = len(response.content)
                    if content_length > 0:
                        self.log_result(f"{endpoint}?format={format_type}", "GET", True, 
                                      f"Export successful ({content_length} bytes)")
                    else:
                        self.log_result(f"{endpoint}?format={format_type}", "GET", False, "Empty file content")
                        success = False
                else:
                    self.log_result(f"{endpoint}?format={format_type}", "GET", False, 
                                  f"Status: {response.status_code}")
                
                if not success:
                    all_success = False
                    
            except Exception as e:
                self.log_result(f"{endpoint}?format={format_type}", "GET", False, f"Error: {str(e)}")
                all_success = False
        
        return all_success
    
    def run_validation(self):
        """Run complete API validation suite"""
        print("🚀 Starting API Integration Validation")
        print("=" * 50)
        
        # Test server connectivity first
        if not self.test_health_check():
            print("\n❌ Server not accessible. Make sure the application is running:")
            print("   cd mvp_site && vpython main.py")
            return False
        
        print("\n📋 Testing Core API Endpoints:")
        print("-" * 30)
        
        # Run all tests in sequence
        tests = [
            ("Campaign Creation", self.test_campaign_creation),
            ("Campaign Listing", self.test_campaign_listing),
            ("Campaign Details", self.test_campaign_details),
            ("Campaign Update", self.test_campaign_update),
            ("Story Interaction", self.test_story_interaction),
            ("File Export", self.test_file_export)
        ]
        
        total_tests = len(tests)
        passed_tests = 0
        
        for test_name, test_func in tests:
            print(f"\n🔍 Running {test_name} test...")
            if test_func():
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 All API endpoints validated successfully!")
            print("✅ Frontend modernization can proceed safely")
        else:
            print(f"⚠️  {total_tests - passed_tests} test(s) failed")
            print("🛑 Address API issues before frontend modernization")
        
        # Save detailed results
        results_file = "api_validation_results.json"
        with open(results_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "detailed_results": self.results
            }, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
        
        return passed_tests == total_tests

def main():
    """Main execution function"""
    print("WorldArchitect.AI - API Integration Validation")
    print("Part of Frontend Modernization Phase 0: Risk Assessment")
    print()
    
    # Check if we're in the right directory
    if not os.path.exists("mvp_site"):
        print("❌ Error: Run this script from the project root directory")
        print("   Expected to find 'mvp_site' directory")
        sys.exit(1)
    
    validator = APIValidator()
    success = validator.run_validation()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()