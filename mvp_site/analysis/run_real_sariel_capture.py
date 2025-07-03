#!/usr/bin/env python3
"""
Capture actual LLM responses by calling the main project environment.
Uses subprocess to run tests in the proper environment where Flask is available.
"""

import subprocess
import json
import os
import sys
from datetime import datetime

def run_sariel_capture_in_main_project():
    """Run the Sariel capture in the main project where dependencies exist"""
    
    print("🎯 Running Sariel LLM capture in main project environment...")
    
    # Path to the main project mvp_site (where Flask dependencies exist)
    main_project_path = "/home/jleechan/projects/worldarchitect.ai/mvp_site"
    
    # Check if main project exists
    if not os.path.exists(main_project_path):
        print(f"❌ Main project not found at {main_project_path}")
        return None
    
    # Create a script in the main project to run our capture
    capture_script = '''
import unittest
import os
import json
import sys
from datetime import datetime

# Add project root to path
project_root = os.path.abspath('.')
sys.path.insert(0, project_root)

# Import Flask app components
from main import create_app
from integration_test_lib import IntegrationTestSetup, setup_integration_test_environment

def capture_responses():
    # Set up test environment
    test_setup = setup_integration_test_environment(project_root)
    temp_prompts_dir = test_setup.create_test_prompts_directory()
    
    original_cwd = os.getcwd()
    os.chdir(temp_prompts_dir)
    
    import gemini_service
    
    try:
        # Create Flask app
        app = create_app()
        app.config['TESTING'] = True
        client = app.test_client()
        user_id = 'test-llm-capture'
        
        # Sariel prompts (minimal first few)
        interactions = [
            {
                "input": "continue",
                "context": {"location": "Throne Room", "expected_entities": ["Sariel"]}
            },
            {
                "input": "ask for forgiveness. tell cassian i was scared and helpless",
                "context": {"location": "Throne Room", "expected_entities": ["Sariel", "Cassian"]},
                "metadata": {"is_cassian_problem": True}
            },
            {
                "input": "2",
                "context": {"location": "Valerius's Study", "expected_entities": ["Sariel", "Valerius"]}
            }
        ]
        
        # Create campaign
        create_response = client.post(
            '/api/campaigns',
            headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': user_id},
            data=json.dumps({
                'prompt': 'Start a campaign with Sariel in a throne room',
                'title': 'Sariel Response Capture',
                'selected_prompts': ['narrative', 'mechanics']
            })
        )
        
        if create_response.status_code != 201:
            print(f"Campaign creation failed: {create_response.status_code}")
            return None
            
        campaign_info = create_response.get_json()
        campaign_id = campaign_info['campaign_id']
        print(f"Created campaign: {campaign_id}")
        
        captured = []
        
        for i, interaction in enumerate(interactions):
            print(f"Running interaction {i+1}: {interaction['input'][:30]}...")
            
            response = client.post(
                f'/api/campaigns/{campaign_id}/interaction',
                headers={'Content-Type': 'application/json', 'X-Test-Bypass-Auth': 'true', 'X-Test-User-ID': user_id},
                data=json.dumps({'input': interaction['input'], 'mode': 'character'})
            )
            
            if response.status_code == 200:
                data = response.get_json()
                narrative = data.get('response', '')
                
                result = {
                    'interaction': i + 1,
                    'input': interaction['input'],
                    'location': interaction['context']['location'],
                    'expected_entities': interaction['context']['expected_entities'],
                    'narrative': narrative,
                    'length': len(narrative),
                    'is_cassian_problem': interaction.get('metadata', {}).get('is_cassian_problem', False)
                }
                captured.append(result)
                
                print(f"  Response ({len(narrative)} chars): {narrative[:50]}...")
                
                if result['is_cassian_problem']:
                    cassian_found = 'cassian' in narrative.lower()
                    print(f"  CASSIAN PROBLEM: {'RESOLVED' if cassian_found else 'STILL FAILING'}")
            else:
                print(f"  Failed: {response.status_code}")
                break
        
        # Save results
        output = {
            'capture_date': datetime.now().isoformat(),
            'campaign_id': campaign_id,
            'total_interactions': len(captured),
            'responses': captured
        }
        
        with open('sariel_real_responses.json', 'w') as f:
            json.dump(output, f, indent=2)
            
        print(f"Saved {len(captured)} responses to sariel_real_responses.json")
        return output
        
    finally:
        os.chdir(original_cwd)
        test_setup.cleanup()

if __name__ == "__main__":
    result = capture_responses()
    if result:
        print("SUCCESS: Captured real LLM responses")
    else:
        print("FAILED: Could not capture responses")
'''
    
    # Write the script to main project
    script_path = os.path.join(main_project_path, "temp_capture_script.py")
    with open(script_path, 'w') as f:
        f.write(capture_script)
    
    try:
        # Run the script in the main project environment
        print("📝 Created capture script in main project")
        print("🚀 Running capture in main project environment...")
        
        result = subprocess.run(
            ["python3", "temp_capture_script.py"],
            cwd=main_project_path,
            capture_output=True,
            text=True,
            env={**os.environ, "TESTING": "true"}
        )
        
        print("📊 Capture script output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Errors:")
            print(result.stderr)
        
        # Check if results file was created
        results_path = os.path.join(main_project_path, "sariel_real_responses.json")
        if os.path.exists(results_path):
            # Copy results to our working directory
            with open(results_path, 'r') as f:
                data = json.load(f)
            
            local_path = "sariel_real_responses_captured.json"
            with open(local_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Copied results to {local_path}")
            
            # Create summary
            summary = f"""# Real Sariel LLM Responses - {datetime.now().strftime('%Y-%m-%d')}

**Campaign ID**: {data['campaign_id']}
**Total Interactions**: {data['total_interactions']}
**Capture Date**: {data['capture_date']}

## Complete AI Responses

"""
            
            for response in data['responses']:
                summary += f"""### Interaction {response['interaction']}
**Player Input**: {response['input']}
**Location**: {response['location']}
**Expected Entities**: {', '.join(response['expected_entities'])}
**Response Length**: {response['length']} characters

**Complete LLM Response**:
```
{response['narrative']}
```

"""
                if response['is_cassian_problem']:
                    cassian_found = 'cassian' in response['narrative'].lower()
                    summary += f"🚨 **THE CASSIAN PROBLEM**: {'RESOLVED' if cassian_found else 'STILL FAILING'}\\n\\n"
            
            with open("sariel_real_responses_summary.md", 'w') as f:
                f.write(summary)
            
            print("📄 Created detailed summary")
            return data
        else:
            print("❌ No results file created")
            return None
            
    except Exception as e:
        print(f"💥 Error running capture: {e}")
        return None
    
    finally:
        # Clean up script
        if os.path.exists(script_path):
            os.remove(script_path)

if __name__ == "__main__":
    try:
        result = run_sariel_capture_in_main_project()
        if result:
            print("\\n🎉 Successfully captured real LLM responses!")
            print(f"📊 Captured {result['total_interactions']} interactions")
        else:
            print("\\n❌ Failed to capture LLM responses")
            sys.exit(1)
    except Exception as e:
        print(f"\\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)