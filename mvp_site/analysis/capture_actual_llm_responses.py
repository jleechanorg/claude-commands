#!/usr/bin/env python3
"""
Capture actual LLM responses from Sariel campaign using the working integration test pattern.
Based on mvp_site/tests/test_integration.py approach.
"""

import json
import os
import sys
import traceback
from datetime import datetime

from integration_test_lib import (
    IntegrationTestSetup,
    setup_integration_test_environment,
)
from main import create_app

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "mvp_site"))
sys.path.insert(0, project_root)

# Handle missing dependencies gracefully
try:
    # Set up the integration test environment
    test_setup = setup_integration_test_environment(project_root)
    temp_prompts_dir = test_setup.create_test_prompts_directory()
    DEPS_AVAILABLE = True
except ImportError as e:
    print(f"Integration test dependencies not available: {e}")
    DEPS_AVAILABLE = False


def capture_sariel_llm_responses():
    """Capture actual LLM responses using the working integration pattern"""
    if not DEPS_AVAILABLE:
        print("❌ Dependencies not available - cannot run LLM capture")
        return None

    print("🎯 Starting LLM response capture using working integration pattern...")

    # Initialize test configuration
    original_cwd = os.getcwd()
    os.chdir(temp_prompts_dir)

    # Get test configuration
    TEST_SELECTED_PROMPTS = IntegrationTestSetup.TEST_SELECTED_PROMPTS

    # Create Flask app using working pattern
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    user_id = "test-llm-capture-user"

    try:
        # Load Sariel campaign prompts
        prompts_path = os.path.join(
            os.path.dirname(__file__),
            "mvp_site",
            "tests",
            "data",
            "sariel_campaign_prompts.json",
        )
        with open(prompts_path) as f:
            sariel_data = json.load(f)

        prompts = sariel_data["prompts"]
        initial_prompt = prompts[0]
        interaction_prompts = prompts[1:6]  # First 5 interactions

        print(f"📋 Loaded {len(interaction_prompts)} interactions to replay")

        # Step 1: Create campaign using working pattern
        create_response = client.post(
            "/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Bypass-Auth": "true",
                "X-Test-User-ID": user_id,
            },
            data=json.dumps(
                {
                    "prompt": initial_prompt["input"],
                    "title": "Sariel LLM Response Capture",
                    "selected_prompts": TEST_SELECTED_PROMPTS,
                }
            ),
        )

        if create_response.status_code != 201:
            print(f"❌ Failed to create campaign: {create_response.status_code}")
            return None

        campaign_info = create_response.get_json()
        campaign_id = campaign_info["campaign_id"]
        print(f"✅ Created campaign: {campaign_id}")

        # Step 2: Capture responses for each interaction
        captured_responses = []

        for i, prompt_data in enumerate(interaction_prompts):
            interaction_num = i + 1
            print(
                f"\n--- Interaction {interaction_num}: {prompt_data['input'][:50]}... ---"
            )

            # Send interaction using working pattern
            interaction_response = client.post(
                f"/api/campaigns/{campaign_id}/interaction",
                headers={
                    "Content-Type": "application/json",
                    "X-Test-Bypass-Auth": "true",
                    "X-Test-User-ID": user_id,
                },
                data=json.dumps({"input": prompt_data["input"], "mode": "character"}),
            )

            if interaction_response.status_code != 200:
                print(
                    f"❌ Interaction {interaction_num} failed: {interaction_response.status_code}"
                )
                response_data = interaction_response.get_json()
                print(f"Error: {response_data}")
                break

            response_data = interaction_response.get_json()
            narrative = response_data.get("response", "")

            print(f"✅ Received response ({len(narrative)} chars)")
            print(f"📄 Preview: {narrative[:100]}...")

            # Capture complete response
            captured_response = {
                "interaction": interaction_num,
                "timestamp": datetime.now().isoformat(),
                "input": {
                    "text": prompt_data["input"],
                    "location": prompt_data["context"]["location"],
                    "expected_entities": prompt_data["context"]["expected_entities"],
                },
                "output": {
                    "narrative": narrative,
                    "full_response": response_data,
                    "character_count": len(narrative),
                    "word_count": len(narrative.split()),
                },
                "metadata": {
                    "is_cassian_problem": prompt_data["metadata"].get(
                        "is_cassian_problem", False
                    ),
                    "campaign_id": campaign_id,
                },
            }

            captured_responses.append(captured_response)

            # Check for The Cassian Problem specifically
            if prompt_data["metadata"].get("is_cassian_problem"):
                cassian_mentioned = "cassian" in narrative.lower()
                print(
                    f"🚨 CASSIAN PROBLEM CHECK: {'✅ RESOLVED' if cassian_mentioned else '❌ STILL FAILING'}"
                )

        # Step 3: Save captured responses
        output_data = {
            "capture_date": datetime.now().isoformat(),
            "campaign_id": campaign_id,
            "total_interactions": len(captured_responses),
            "purpose": "Document actual LLM responses with working integration pattern",
            "responses": captured_responses,
        }

        output_path = os.path.join(
            "mvp_site", "tests", "data", "sariel_actual_llm_responses.json"
        )
        with open(output_path, "w") as f:
            json.dump(output_data, f, indent=2)

        print(
            f"\n✅ Successfully captured {len(captured_responses)} actual LLM responses"
        )
        print(f"📁 Saved to: {output_path}")

        # Step 4: Create detailed summary
        summary_lines = [
            f"# Actual Sariel Campaign LLM Responses - {datetime.now().strftime('%Y-%m-%d')}",
            "",
            f"**Campaign ID**: {campaign_id}",
            f"**Total Interactions**: {len(captured_responses)}",
            "**Capture Method**: Working integration test pattern",
            f"**Capture Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Complete LLM Responses",
            "",
        ]

        for response in captured_responses:
            summary_lines.extend(
                [
                    f"### Interaction {response['interaction']}",
                    f"**Player Input**: {response['input']['text']}",
                    f"**Location**: {response['input']['location']}",
                    f"**Expected Entities**: {', '.join(response['input']['expected_entities'])}",
                    f"**Response Length**: {response['output']['character_count']} chars, {response['output']['word_count']} words",
                    "",
                    "**Complete LLM Response**:",
                    "```",
                    response["output"]["narrative"],
                    "```",
                    "",
                ]
            )

            if response["metadata"]["is_cassian_problem"]:
                cassian_mentioned = "cassian" in response["output"]["narrative"].lower()
                summary_lines.insert(
                    -2,
                    f"🚨 **THE CASSIAN PROBLEM**: {'RESOLVED' if cassian_mentioned else 'STILL FAILING'}",
                )
                summary_lines.insert(-2, "")

        summary_path = os.path.join(
            "mvp_site", "tests", "data", "sariel_actual_responses_summary.md"
        )
        with open(summary_path, "w") as f:
            f.write("\n".join(summary_lines))

        print(f"📄 Detailed summary saved to: {summary_path}")

        return output_data

    except Exception as e:
        print(f"💥 Error during capture: {e}")

        traceback.print_exc()
        return None

    finally:
        # Restore original directory
        os.chdir(original_cwd)
        # Cleanup
        test_setup.cleanup()


if __name__ == "__main__":
    try:
        result = capture_sariel_llm_responses()
        if result:
            print("\n🎉 Actual LLM response capture completed successfully!")
            print("📊 Now we have the real responses to document")
        else:
            print("\n❌ LLM response capture failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

        traceback.print_exc()
        sys.exit(1)
