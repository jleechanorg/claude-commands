#!/usr/bin/env python3
"""
Working test for structured fields - uses test mode to bypass auth.
"""

import json
import os
import signal
import subprocess
import time

import requests


def test_structured_fields():
    # Start server
    print("Starting test server...")
    env = os.environ.copy()
    env["TESTING"] = "true"
    env["PORT"] = "8090"

    server = subprocess.Popen(
        ["python", "mvp_site/main.py", "serve"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for server and check it's running
    time.sleep(5)

    try:
        # First, let's test that the server is running
        print("\nTesting server health...")
        try:
            response = requests.get("http://localhost:8090/")
            print(f"Server is running: {response.status_code}")
        except Exception as e:
            print(f"Server not responding: {e}")
            # Print server output
            stdout, stderr = server.communicate(timeout=1)
            print(f"Server stdout: {stdout.decode()}")
            print(f"Server stderr: {stderr.decode()}")
            return

        # Now let's make a direct API call with test headers
        print("\nMaking API call with test headers...")

        # Create campaign
        response = requests.post(
            "http://localhost:8090/api/campaigns",
            headers={
                "Content-Type": "application/json",
                "X-Test-Mode": "true",
                "X-Test-User-Id": "test-user-123",
            },
            json={
                "title": "Structured Fields Test",
                "prompt": "Test campaign",
                "campaign_type": "custom",
            },
        )

        print(f"Campaign creation status: {response.status_code}")
        if response.status_code != 200:
            print(f"Campaign creation failed: {response.text}")
            return

        campaign_data = response.json()
        campaign_id = campaign_data.get("campaign_id")
        print(f"Created campaign: {campaign_id}")

        # Test interaction
        response = requests.post(
            f"http://localhost:8090/api/campaigns/{campaign_id}/interaction",
            headers={
                "Content-Type": "application/json",
                "X-Test-Mode": "true",
                "X-Test-User-Id": "test-user-123",
            },
            json={
                "input_text": "I attack the goblin with my sword!",
                "mode": "character",
                "debug_mode": True,
            },
        )

        print(f"\nInteraction status: {response.status_code}")
        if response.status_code != 200:
            print(f"Interaction failed: {response.text}")
            return

        data = response.json()

        # Analyze response
        print("\n=== RESPONSE ANALYSIS ===")
        print(f"Top-level keys: {sorted(data.keys())}")

        # Check for structured fields at top level
        print("\n=== TOP LEVEL FIELDS ===")
        for field in ["dice_rolls", "resources", "planning_block", "session_header"]:
            if field in data:
                print(
                    f"✓ {field}: {type(data[field]).__name__} = {repr(data[field])[:100]}"
                )
            else:
                print(f"✗ {field}: not found")

        # Check debug_info
        if "debug_info" in data:
            print("\n=== DEBUG_INFO CONTENTS ===")
            print(f"debug_info keys: {list(data['debug_info'].keys())}")
            for field in ["dice_rolls", "resources", "dm_notes", "state_rationale"]:
                if field in data["debug_info"]:
                    print(f"✓ {field}: {type(data['debug_info'][field]).__name__}")
                else:
                    print(f"✗ {field}: not found")

        # Show the actual response
        print("\n=== FULL RESPONSE ===")
        print(json.dumps(data, indent=2))

    finally:
        # Cleanup
        print("\nCleaning up...")
        os.kill(server.pid, signal.SIGTERM)
        server.wait()


if __name__ == "__main__":
    test_structured_fields()
