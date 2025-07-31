#!/usr/bin/env python3
"""
Debug script to test slash command processing.
Simulates the GitHub Actions workflow steps to identify where the prompt is getting lost.
"""

import json
import subprocess
import urllib.parse

import requests


def simulate_github_event():
    """Simulate a GitHub event payload for /claude hello!"""
    return {
        "slash_command": {
            "args": {
                "all": "hello!"
            }
        },
        "github": {
            "payload": {
                "comment": {
                    "id": "12345"
                }
            }
        }
    }

def test_jq_extraction(event_data):
    """Test the jq command used in GitHub Actions"""
    # Write event to temp file like GitHub does
    with open('/tmp/test_event.json', 'w') as f:
        json.dump(event_data, f)

    try:
        # Simulate the jq command
        result = subprocess.run([
            'jq', '-r', '.slash_command.args.all', '/tmp/test_event.json'
        ], check=False, capture_output=True, text=True)

        prompt = result.stdout.strip()
        print(f"jq extraction result: '{prompt}'")
        print(f"jq stderr: {result.stderr}")
        return prompt
    except Exception as e:
        print(f"jq command failed: {e}")
        return None

def test_curl_encoding(prompt):
    """Test the curl command used in GitHub Actions"""
    if not prompt:
        print("Cannot test curl with empty prompt")
        return

    # Simulate the curl command
    encoded_data = urllib.parse.urlencode({'prompt': prompt})
    print(f"URL encoded data: {encoded_data}")

    # Test if the encoding looks correct
    if 'prompt=' in encoded_data and prompt in encoded_data:
        print("✅ Curl encoding looks correct")
    else:
        print("❌ Curl encoding might be incorrect")

def test_local_claude_server(prompt):
    """Test the local Claude server if running"""
    try:
        response = requests.post(
            'http://127.0.0.1:8000/claude',
            data={'prompt': prompt},
            timeout=5
        )
        print(f"Server response status: {response.status_code}")
        print(f"Server response: {response.text[:200]}...")
    except Exception as e:
        print(f"Local server test failed: {e}")

if __name__ == '__main__':
    print("🔍 Debug: Slash command processing")
    print("=" * 50)

    # Simulate the GitHub event
    event = simulate_github_event()
    print(f"Simulated event: {json.dumps(event, indent=2)}")
    print()

    # Test jq extraction
    prompt = test_jq_extraction(event)
    print()

    # Test curl encoding
    test_curl_encoding(prompt)
    print()

    # Test local server if available
    if prompt:
        test_local_claude_server(prompt)
