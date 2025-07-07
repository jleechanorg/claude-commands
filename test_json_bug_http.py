#!/usr/bin/env python3
"""
HTTP-based test to reproduce the JSON display bug.
This avoids browser authentication issues and focuses on the API behavior.
"""

import os
import sys
import json
import time
import requests
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration
BASE_URL = "http://localhost:8080"
TEST_USER_ID = "json-bug-test-user"

class JSONBugHTTPTest:
    """Test to reproduce JSON display bug via HTTP requests."""
    
    def __init__(self):
        self.server_process = None
        self.session = requests.Session()
        
    def start_server(self):
        """Start the Flask server in test mode."""
        print("🚀 Starting Flask server in test mode...")
        env = os.environ.copy()
        env['TESTING'] = 'true'
        
        # Kill any existing servers
        subprocess.run(['pkill', '-f', 'main.py serve'], capture_output=True)
        time.sleep(1)
        
        # Start server
        self.server_process = subprocess.Popen(
            ['python3', 'mvp_site/main.py', 'serve'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for server to start
        for i in range(30):
            try:
                r = requests.get(f"{BASE_URL}/health", timeout=1)
                if r.status_code == 200:
                    print("✅ Server started successfully")
                    return True
            except:
                pass
            time.sleep(1)
        
        print("❌ Server failed to start")
        return False
    
    def stop_server(self):
        """Stop the Flask server."""
        if self.server_process:
            print("🛑 Stopping Flask server...")
            self.server_process.terminate()
            self.server_process.wait()
    
    def create_campaign(self, name, prompt):
        """Create a campaign via API."""
        print(f"\n📝 Creating campaign: {name}")
        
        # Use test mode headers
        headers = {
            'X-Test-Mode': 'true',
            'X-Test-User-Id': TEST_USER_ID,
            'Content-Type': 'application/json'
        }
        
        data = {
            'name': name,
            'prompt': prompt,
            'user_id': TEST_USER_ID
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/campaigns",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Campaign created: {result.get('campaign_id')}")
                return result.get('campaign_id')
            else:
                print(f"❌ Failed to create campaign: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating campaign: {e}")
            return None
    
    def get_campaign_story(self, campaign_id):
        """Get the campaign story via API."""
        headers = {
            'X-Test-Mode': 'true',
            'X-Test-User-Id': TEST_USER_ID
        }
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/campaigns/{campaign_id}/story",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get story: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error getting story: {e}")
            return None
    
    def submit_action(self, campaign_id, action):
        """Submit a player action via API."""
        headers = {
            'X-Test-Mode': 'true',
            'X-Test-User-Id': TEST_USER_ID,
            'Content-Type': 'application/json'
        }
        
        data = {
            'campaign_id': campaign_id,
            'action': action,
            'user_id': TEST_USER_ID
        }
        
        try:
            response = self.session.post(
                f"{BASE_URL}/api/story/continue",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to submit action: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error submitting action: {e}")
            return None
    
    def check_for_json_artifacts(self, text, context=""):
        """Check text for raw JSON artifacts."""
        json_indicators = [
            'Scene #',
            '"narrative":',
            '"god_mode_response":',
            '"entities_mentioned":',
            '"scene_number":',
            '"location":'
        ]
        
        found_artifacts = []
        for indicator in json_indicators:
            if indicator in text:
                found_artifacts.append(indicator)
        
        if found_artifacts:
            print(f"\n❌ JSON ARTIFACTS DETECTED in {context}!")
            print(f"   Found: {', '.join(found_artifacts)}")
            print(f"   Text preview: {text[:500]}...")
            return True
        
        return False
    
    def run_test(self):
        """Run the JSON bug reproduction test."""
        print("\n=== JSON Bug Reproduction Test (HTTP) ===")
        
        # Skip server start - assume it's already running
        print("✅ Using existing server on port 8080")
        
        try:
            # Create campaign with the exact prompt that triggered the bug
            campaign_id = self.create_campaign(
                "Invincible Test Campaign",
                "Play as Nolan's son. He's offering you to join him. TV show invincible"
            )
            
            if not campaign_id:
                print("❌ Failed to create campaign")
                return False
            
            # Wait a moment for story generation
            time.sleep(3)
            
            # Get initial story
            print("\n📖 Checking opening story for JSON artifacts...")
            story_data = self.get_campaign_story(campaign_id)
            
            if story_data and 'entries' in story_data:
                for i, entry in enumerate(story_data['entries']):
                    story_text = entry.get('story', '')
                    if self.check_for_json_artifacts(story_text, f"opening story entry {i+1}"):
                        print("\n🎯 BUG CONFIRMED: Raw JSON in opening story!")
            
            # Continue the story with responses
            responses = [
                "I look at my father with confusion. 'Join you? What are you talking about, Dad?'",
                "I take a step back, shocked. 'You're... you're a Viltrumite? All this time?'",
                "I feel anger rising. 'How could you lie to me? To Mom? Was any of it real?'",
                "I clench my fists. 'I won't help you conquer Earth. These are my people!'",
                "'You're not my father anymore. You're just another alien invader.'"
            ]
            
            for i, response in enumerate(responses, 1):
                print(f"\n📤 Turn {i}: Submitting action...")
                result = self.submit_action(campaign_id, response)
                
                if result and 'story' in result:
                    if self.check_for_json_artifacts(result['story'], f"turn {i} response"):
                        print(f"\n🎯 BUG CONFIRMED: Raw JSON in turn {i}!")
                        
                        # Check for the specific Scene pattern
                        if "Scene #" in result['story'] and "{" in result['story']:
                            print("   🔴 EXACT BUG PATTERN FOUND: 'Scene #X: {' pattern detected!")
                
                # Small delay between turns
                time.sleep(2)
            
            # Final check - get complete story
            print("\n📊 Final check of complete story...")
            final_story = self.get_campaign_story(campaign_id)
            
            if final_story and 'entries' in final_story:
                json_count = 0
                scene_count = 0
                
                for entry in final_story['entries']:
                    story_text = entry.get('story', '')
                    json_count += story_text.count('"narrative":')
                    scene_count += story_text.count('Scene #')
                
                print(f"\n   JSON artifact counts across all entries:")
                print(f"   - 'narrative' occurrences: {json_count}")
                print(f"   - 'Scene #' occurrences: {scene_count}")
                
                if json_count > 0 or scene_count > 0:
                    print(f"\n❌ JSON BUG CONFIRMED: Raw JSON is being returned in API responses")
                    print(f"\n📋 NEXT STEP: Check server logs for JSON_BUG entries to trace the issue")
                    return False
                else:
                    print(f"\n✅ No JSON bugs detected in this test run")
                    return True
            
        finally:
            pass  # Don't stop server since we didn't start it
        
        return False


if __name__ == "__main__":
    test = JSONBugHTTPTest()
    success = test.run_test()
    
    # Check server logs
    print("\n📋 Checking server logs for JSON_BUG entries...")
    try:
        # Get the server output
        if test.server_process and test.server_process.stderr:
            stderr_output = test.server_process.stderr.read().decode('utf-8')
            stdout_output = test.server_process.stdout.read().decode('utf-8') if test.server_process.stdout else ""
            
            # Look for JSON_BUG entries
            bug_entries = []
            for line in (stderr_output + stdout_output).split('\n'):
                if 'JSON_BUG' in line:
                    bug_entries.append(line)
            
            if bug_entries:
                print(f"\n🔍 Found {len(bug_entries)} JSON_BUG log entries:")
                for entry in bug_entries[:10]:  # Show first 10
                    print(f"   {entry}")
            else:
                print("   No JSON_BUG entries found in logs")
    except Exception as e:
        print(f"   Error reading logs: {e}")
    
    sys.exit(0 if success else 1)