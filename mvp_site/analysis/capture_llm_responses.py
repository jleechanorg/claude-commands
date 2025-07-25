#!/usr/bin/env python3
"""
Capture actual LLM responses from Sariel campaign replay for documentation.
This runs a single test and saves the complete narrative responses.
"""

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List

from main import create_app
from test_integration.integration_test_lib import (
    IntegrationTestSetup,
    setup_integration_test_environment,
)

# Ensure we're in the project root
project_root = os.path.abspath(os.path.dirname(__file__))
os.chdir(project_root)

# Add mvp_site to path
sys.path.insert(0, os.path.join(project_root, 'mvp_site'))

def capture_sariel_responses():
    """Run Sariel campaign and capture actual LLM responses"""
    print("🎯 Starting Sariel campaign replay with response capture...")

    # Import test modules



    # Set up environment
    test_setup = setup_integration_test_environment(project_root)

    # Create Flask app
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()
    user_id = 'test-llm-capture-user'

    # Load Sariel campaign prompts
    prompts_path = os.path.join('mvp_site', 'tests', 'data', 'sariel_campaign_prompts.json')
    with open(prompts_path, 'r') as f:
        sariel_data = json.load(f)

    prompts = sariel_data['prompts']
    initial_prompt = prompts[0]
    interaction_prompts = prompts[1:6]  # First 5 interactions to start

    print(f"🔍 Will replay {len(interaction_prompts)} interactions")

    # Step 1: Create campaign
    print("📝 Creating campaign...")
    campaign_data = {
        'prompt': initial_prompt['input'],
        'title': 'Sariel LLM Response Capture',
        'selected_prompts': ['narrative', 'mechanics']
    }

    create_response = client.post(
        '/api/campaigns',
        headers=IntegrationTestSetup.create_test_headers(user_id),
        data=json.dumps(campaign_data)
    )

    if create_response.status_code != 201:
        print(f"❌ Failed to create campaign: {create_response.status_code}")
        print(f"Response: {create_response.get_data()}")
        return None

    campaign_info = create_response.get_json()
    campaign_id = campaign_info['campaign_id']
    print(f"✅ Created campaign: {campaign_id}")

    # Step 2: Capture responses for each interaction
    captured_responses = []

    for i, prompt_data in enumerate(interaction_prompts):
        interaction_num = i + 1
        print(f"\n--- Interaction {interaction_num}: {prompt_data['input'][:50]}... ---")

        # Send interaction
        interaction_data = {
            'input': prompt_data['input'],
            'mode': 'character'
        }

        start_time = time.time()
        interaction_response = client.post(
            f'/api/campaigns/{campaign_id}/interaction',
            headers={
                'Content-Type': 'application/json',
                'X-Test-Bypass-Auth': 'true',
                'X-Test-User-ID': user_id
            },
            data=json.dumps(interaction_data)
        )

        duration = time.time() - start_time

        if interaction_response.status_code != 200:
            print(f"❌ Interaction {interaction_num} failed: {interaction_response.status_code}")
            response_data = interaction_response.get_json()
            print(f"Error: {response_data}")
            break

        response_data = interaction_response.get_json()
        narrative = response_data.get('response', '')

        print(f"✅ Received response ({len(narrative)} chars) in {duration:.1f}s")
        print(f"📄 Preview: {narrative[:100]}...")

        # Capture complete response data
        captured_response = {
            'interaction': interaction_num,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'input': {
                'text': prompt_data['input'],
                'location': prompt_data['context']['location'],
                'expected_entities': prompt_data['context']['expected_entities']
            },
            'output': {
                'narrative': narrative,
                'full_response': response_data,
                'character_count': len(narrative),
                'word_count': len(narrative.split())
            },
            'metadata': {
                'is_cassian_problem': prompt_data['metadata'].get('is_cassian_problem', False),
                'campaign_id': campaign_id
            }
        }

        captured_responses.append(captured_response)

        # Brief pause between interactions
        time.sleep(1)

    # Step 3: Save captured responses
    output_data = {
        'capture_date': datetime.now().isoformat(),
        'campaign_id': campaign_id,
        'total_interactions': len(captured_responses),
        'purpose': 'Document actual LLM responses for GitHub plan update',
        'responses': captured_responses
    }

    output_path = os.path.join('mvp_site', 'tests', 'data', 'sariel_llm_responses_captured.json')
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"\n✅ Captured {len(captured_responses)} LLM responses")
    print(f"📁 Saved to: {output_path}")

    # Step 4: Create summary for GitHub
    summary_lines = [
        f"# Sariel Campaign LLM Responses - {datetime.now().strftime('%Y-%m-%d')}",
        "",
        f"**Campaign ID**: {campaign_id}",
        f"**Total Interactions**: {len(captured_responses)}",
        f"**Capture Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Interaction Summary",
        ""
    ]

    for response in captured_responses:
        summary_lines.extend([
            f"### Interaction {response['interaction']}",
            f"**Player Input**: {response['input']['text']}",
            f"**Location**: {response['input']['location']}",
            f"**Expected Entities**: {', '.join(response['input']['expected_entities'])}",
            f"**Response Length**: {response['output']['character_count']} chars, {response['output']['word_count']} words",
            f"**Duration**: {response['duration_seconds']}s",
            "",
            "**LLM Response**:",
            "```",
            response['output']['narrative'],
            "```",
            ""
        ])

        if response['metadata']['is_cassian_problem']:
            summary_lines.insert(-2, "🚨 **THE CASSIAN PROBLEM** - Player references Cassian directly")
            summary_lines.insert(-2, "")

    summary_path = os.path.join('mvp_site', 'tests', 'data', 'sariel_llm_responses_summary.md')
    with open(summary_path, 'w') as f:
        f.write('\n'.join(summary_lines))

    print(f"📄 Summary saved to: {summary_path}")

    return output_data

if __name__ == "__main__":
    try:
        result = capture_sariel_responses()
        if result:
            print("\n🎉 LLM response capture completed successfully!")
        else:
            print("\n❌ LLM response capture failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Error during capture: {e}")

        traceback.print_exc()
        sys.exit(1)
