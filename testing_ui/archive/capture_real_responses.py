#!/usr/bin/env python3
"""
Capture real Gemini API responses for key test scenarios
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime

import requests

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def capture_campaign_response(campaign_data, test_name, max_wait=60):
    """Capture real campaign creation and initial story response"""
    print(f"\n🎯 Capturing: {test_name}")
    print(f"   Campaign Type: {campaign_data.get('campaign_type', 'none')}")

    headers = {
        "Content-Type": "application/json",
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": f"capture-{test_name.lower().replace(' ', '-')}",
    }

    try:
        # Create campaign with real Gemini
        print("   📤 Creating campaign with real Gemini API...")
        response = requests.post(
            "http://localhost:6007/api/campaigns",
            json=campaign_data,
            headers=headers,
            timeout=90,  # Give Gemini time to generate
        )

        if response.status_code != 201:
            print(f"   ❌ Campaign creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None

        result = response.json()
        campaign_id = result.get("campaign_id")
        print(f"   ✅ Campaign created: {campaign_id}")

        # Wait for and fetch the generated story
        print("   ⏳ Waiting for Gemini story generation...")
        for attempt in range(max_wait):
            time.sleep(1)

            # Get campaign data
            campaign_response = requests.get(
                f"http://localhost:6007/api/campaigns/{campaign_id}",
                headers=headers,
                timeout=30,
            )

            if campaign_response.status_code != 200:
                continue

            campaign_data_resp = campaign_response.json()
            story = campaign_data_resp.get("data", {}).get("story", [])

            if story and len(story) > 0:
                first_entry = story[0]
                narrative_text = first_entry.get("text", "")

                if narrative_text.strip():
                    print(f"   ✅ Story generated after {attempt + 1} seconds")
                    print(f"   📝 Preview: {narrative_text[:100]}...")

                    # Create capture data
                    return {
                        "test_name": test_name,
                        "campaign_input": campaign_data,
                        "creation_response": result,
                        "story_response": first_entry,
                        "full_campaign_data": campaign_data_resp.get("data", {}),
                        "captured_at": datetime.now().isoformat(),
                        "capture_duration_seconds": attempt + 1,
                    }


        print(f"   ⚠️  Timeout: No story generated after {max_wait} seconds")
        return None

    except Exception as e:
        print(f"   💥 Error: {e}")
        return None


def main():
    """Capture responses for key test scenarios"""
    print("🎬 WorldArchitect.AI - Real Gemini Response Capture")
    print("=" * 55)
    print("💰 WARNING: This uses real Gemini API and costs money!")
    print("📋 Capturing responses for 5 core test scenarios...")
    print("=" * 55)

    # Key test scenarios to capture
    test_scenarios = [
        {
            "name": "Dragon Knight Campaign",
            "data": {
                "title": "Ser Arion's First Mission",
                "character": "Ser Arion",
                "setting": "World of Assiah",
                "campaign_type": "dragon-knight",
                "selected_prompts": ["narrative", "mechanics"],
                "custom_options": ["defaultWorld"],
            },
        },
        {
            "name": "Custom Campaign - Astarion",
            "data": {
                "title": "Astarion's Ascension",
                "character": "Astarion who ascended in BG3",
                "setting": "Baldur's Gate",
                "campaign_type": "custom",
                "selected_prompts": ["narrative", "mechanics"],
                "custom_options": ["companions"],
            },
        },
        {
            "name": "Custom Campaign - Minimal",
            "data": {
                "title": "Random Adventure",
                "character": "",
                "setting": "",
                "campaign_type": "custom",
                "selected_prompts": ["narrative"],
                "custom_options": [],
            },
        },
    ]

    captured_responses = []

    # Start server with real Gemini
    print("🚀 Starting server with real Gemini API...")
    os.system("pkill -f 'mvp_site/main.py serve' 2>/dev/null || true")
    time.sleep(2)

    # Start server in background with real APIs

    env = os.environ.copy()
    env["TESTING"] = "true"
    env["USE_MOCKS"] = "false"
    env["PORT"] = "6007"

    server_process = subprocess.Popen(
        ["python3", "mvp_site/main.py", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )

    # Wait for server startup
    print("⏳ Waiting for server startup...")
    time.sleep(5)

    # Test server
    try:
        test_response = requests.get("http://localhost:6007", timeout=10)
        if test_response.status_code != 200:
            print("❌ Server not responding")
            server_process.terminate()
            return
        print("✅ Server ready for capture")
    except:
        print("❌ Server failed to start")
        server_process.terminate()
        return

    try:
        # Capture each scenario
        for scenario in test_scenarios:
            capture_data = capture_campaign_response(
                scenario["data"], scenario["name"], max_wait=90
            )

            if capture_data:
                captured_responses.append(capture_data)
                print(f"   💾 Captured: {scenario['name']}")
            else:
                print(f"   💥 Failed: {scenario['name']}")

    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        server_process.terminate()
        server_process.wait(timeout=10)

    # Save all captured data
    if captured_responses:
        output_file = "testing_ui/mock_data/real_gemini_captures.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "captured_at": datetime.now().isoformat(),
                    "total_captures": len(captured_responses),
                    "scenarios": captured_responses,
                },
                f,
                indent=2,
            )

        print(f"\n✅ SUCCESS: {len(captured_responses)} scenarios captured")
        print(f"💾 Saved to: {output_file}")

        # Show summary
        print("\n📊 Capture Summary:")
        for capture in captured_responses:
            test_name = capture["test_name"]
            duration = capture["capture_duration_seconds"]
            preview = capture["story_response"]["text"][:80] + "..."
            print(f"   • {test_name}: {duration}s - {preview}")

    else:
        print("\n❌ No responses captured - check server logs for errors")


if __name__ == "__main__":
    main()
