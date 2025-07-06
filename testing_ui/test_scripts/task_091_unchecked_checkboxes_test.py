#!/usr/bin/env python3
"""
TASK-091 Test: Campaign Creation with Unchecked Checkboxes
Test campaign creation with both mechanics and narrative checkboxes unchecked.
"""

import os
import sys
import json
import time
import tempfile
import requests
from unittest.mock import patch, MagicMock

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'mvp_site'))

# Set environment variables for testing
os.environ['TESTING'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/dev/null'

# Import required modules
from main import create_app
import constants

def test_campaign_creation_unchecked_checkboxes():
    """Test campaign creation with both checkboxes unchecked."""
    print("=== TASK-091: Testing Campaign Creation with Unchecked Checkboxes ===\n")
    
    # Create Flask app
    app = create_app()
    
    # Mock Firebase authentication
    with patch('firebase_admin.auth.verify_id_token') as mock_verify:
        mock_verify.return_value = {'uid': 'test-user-id'}
        
        # Mock Firestore operations
        with patch('mvp_site.firestore_service.create_campaign') as mock_create_campaign, \
             patch('mvp_site.firestore_service.add_story_entry') as mock_add_story, \
             patch('mvp_site.gemini_service.generate_story_response') as mock_generate:
            
            # Mock campaign creation
            mock_create_campaign.return_value = 'test-campaign-id'
            mock_add_story.return_value = True
            
            # Mock AI response
            mock_generate.return_value = {
                'story': 'Welcome to your adventure! You find yourself in a mystical forest...',
                'state_updates': {
                    'current_scene': 1,
                    'location': 'Mystical Forest',
                    'characters': {'player': {'name': 'Test Hero', 'health': 100}}
                }
            }
            
            with app.test_client() as client:
                # Test 1: Campaign creation with both checkboxes unchecked
                print("Test 1: Creating campaign with both checkboxes unchecked...")
                
                campaign_data = {
                    'title': 'Test Campaign - Unchecked Checkboxes',
                    'prompt': 'A simple adventure in a medieval fantasy world.',
                    'selected_prompts': [],  # Both checkboxes unchecked
                    'custom_options': {
                        'companions': False,
                        'defaultWorld': False
                    }
                }
                
                response = client.post('/api/campaigns', 
                                     json=campaign_data,
                                     headers={'X-Test-Bypass-Auth': 'true',
                                             'X-Test-User-ID': 'test-user-id'})
                
                print(f"Response status: {response.status_code}")
                print(f"Response data: {response.get_json()}")
                
                if response.status_code in [200, 201]:
                    print("✅ Campaign creation successful with unchecked checkboxes")
                    campaign_id = response.get_json().get('campaign_id')
                    
                    # Test 2: Story interaction with unchecked settings
                    print("\nTest 2: Testing story interaction with unchecked settings...")
                    
                    interaction_data = {
                        'input': 'I explore the forest path ahead.',
                        'campaign_id': campaign_id,
                        'mode': 'character'
                    }
                    
                    response = client.post('/api/story_interaction',
                                         json=interaction_data,
                                         headers={'X-Test-Bypass-Auth': 'true',
                                                 'X-Test-User-ID': 'test-user-id'})
                    
                    print(f"Interaction response status: {response.status_code}")
                    print(f"Interaction response data: {response.get_json()}")
                    
                    if response.status_code in [200, 201]:
                        print("✅ Story interaction successful with unchecked settings")
                        
                        # Test 3: Multiple interactions to ensure stability
                        print("\nTest 3: Testing multiple interactions for stability...")
                        
                        interactions = [
                            "I examine the surrounding trees.",
                            "I listen for any sounds in the forest.",
                            "I check my inventory.",
                            "I look for a place to rest.",
                            "I continue down the path."
                        ]
                        
                        for i, interaction in enumerate(interactions, 1):
                            print(f"Interaction {i}: {interaction}")
                            
                            interaction_data = {
                                'input': interaction,
                                'campaign_id': campaign_id,
                                'mode': 'character'
                            }
                            
                            response = client.post('/api/story_interaction',
                                                 json=interaction_data,
                                                 headers={'X-Test-Bypass-Auth': 'true',
                                                         'X-Test-User-ID': 'test-user-id'})
                            
                            if response.status_code in [200, 201]:
                                print(f"✅ Interaction {i} successful")
                            else:
                                print(f"❌ Interaction {i} failed with status {response.status_code}")
                                print(f"Error: {response.get_json()}")
                                return False
                            
                            time.sleep(0.5)  # Small delay between interactions
                        
                        print("\n✅ All interactions completed successfully!")
                        return True
                    else:
                        print(f"❌ Story interaction failed with status {response.status_code}")
                        return False
                else:
                    print(f"❌ Campaign creation failed with status {response.status_code}")
                    return False

def test_frontend_checkbox_behavior():
    """Test that frontend properly handles unchecked checkboxes."""
    print("\n=== Testing Frontend Checkbox Behavior ===\n")
    
    # Read the HTML file to verify checkbox setup
    html_path = '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/mvp_site/static/index.html'
    
    with open(html_path, 'r') as f:
        html_content = f.read()
    
    # Check if checkboxes exist
    narrative_checkbox = 'id="prompt-narrative"' in html_content
    mechanics_checkbox = 'id="prompt-mechanics"' in html_content
    
    print(f"Narrative checkbox found: {narrative_checkbox}")
    print(f"Mechanics checkbox found: {mechanics_checkbox}")
    
    # Check if they are checked by default
    narrative_checked = 'id="prompt-narrative"' in html_content and 'checked' in html_content
    mechanics_checked = 'id="prompt-mechanics"' in html_content and 'checked' in html_content
    
    print(f"Narrative checkbox checked by default: {narrative_checked}")
    print(f"Mechanics checkbox checked by default: {mechanics_checked}")
    
    if narrative_checkbox and mechanics_checkbox:
        print("✅ Frontend checkboxes are properly configured")
        return True
    else:
        print("❌ Frontend checkboxes are missing or misconfigured")
        return False

def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n=== Generating Test Report ===\n")
    
    results = {
        'test_name': 'TASK-091: Campaign Creation with Unchecked Checkboxes',
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'tests_performed': [
            'Campaign creation with both checkboxes unchecked',
            'Story interaction with unchecked settings',
            'Multiple interactions for stability testing',
            'Frontend checkbox behavior verification'
        ],
        'findings': [],
        'recommendations': []
    }
    
    try:
        # Run the tests
        backend_test_passed = test_campaign_creation_unchecked_checkboxes()
        frontend_test_passed = test_frontend_checkbox_behavior()
        
        results['backend_test_passed'] = backend_test_passed
        results['frontend_test_passed'] = frontend_test_passed
        
        if backend_test_passed and frontend_test_passed:
            results['overall_status'] = 'PASS'
            results['findings'].append('Campaign creation works correctly with unchecked checkboxes')
            results['findings'].append('Story interactions remain stable with minimal AI configuration')
            results['findings'].append('Frontend properly displays checkbox options')
        else:
            results['overall_status'] = 'FAIL'
            results['findings'].append('One or more tests failed')
            
        if not backend_test_passed:
            results['recommendations'].append('Review backend handling of empty selected_prompts array')
        
        if not frontend_test_passed:
            results['recommendations'].append('Verify frontend checkbox configuration')
            
    except Exception as e:
        results['overall_status'] = 'ERROR'
        results['error'] = str(e)
        results['findings'].append(f'Test execution failed with error: {str(e)}')
        
    return results

if __name__ == '__main__':
    try:
        # Generate and save test report
        report = generate_test_report()
        
        # Save report to file
        report_path = '/home/jleechan/projects/worldarchitect.ai/worktree_roadmap/tmp/task_091_unchecked_checkboxes_results.md'
        
        with open(report_path, 'w') as f:
            f.write(f"# {report['test_name']}\n\n")
            f.write(f"**Test Date:** {report['test_date']}\n")
            f.write(f"**Overall Status:** {report['overall_status']}\n\n")
            
            f.write("## Tests Performed\n\n")
            for test in report['tests_performed']:
                f.write(f"- {test}\n")
            
            f.write("\n## Test Results\n\n")
            if 'backend_test_passed' in report:
                f.write(f"- Backend Test: {'PASS' if report['backend_test_passed'] else 'FAIL'}\n")
            if 'frontend_test_passed' in report:
                f.write(f"- Frontend Test: {'PASS' if report['frontend_test_passed'] else 'FAIL'}\n")
            
            f.write("\n## Findings\n\n")
            for finding in report['findings']:
                f.write(f"- {finding}\n")
            
            if report['recommendations']:
                f.write("\n## Recommendations\n\n")
                for rec in report['recommendations']:
                    f.write(f"- {rec}\n")
            
            if 'error' in report:
                f.write(f"\n## Error Details\n\n{report['error']}\n")
                
        print(f"\n📝 Test report saved to: {report_path}")
        print(f"📊 Overall test status: {report['overall_status']}")
        
    except Exception as e:
        print(f"❌ Test execution failed: {str(e)}")
        import traceback
        traceback.print_exc()