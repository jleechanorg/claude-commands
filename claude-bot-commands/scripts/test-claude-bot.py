#!/usr/bin/env python3
"""
Test script for the Claude bot server.
Verifies that the server can accept requests and process them.
"""

import requests
import json
import time
import sys

def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get('http://127.0.0.1:5001/health', timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed:", response.text)
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_form_encoded_request():
    """Test a form-encoded POST request."""
    try:
        data = {'prompt': 'Hello Claude, this is a test prompt. Please respond with "Test successful".'}
        response = requests.post('http://127.0.0.1:5001/claude', data=data, timeout=30)

        if response.status_code == 200:
            print("✅ Form-encoded request successful")
            print(f"Response: {response.text[:200]}...")
            return True
        else:
            print(f"❌ Form-encoded request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Form-encoded request failed: {e}")
        return False

def test_json_request():
    """Test a JSON POST request."""
    try:
        data = {'prompt': 'Hello Claude, this is a JSON test. Please respond with "JSON test successful".'}
        headers = {'Content-Type': 'application/json'}
        response = requests.post('http://127.0.0.1:5001/claude',
                               json=data, headers=headers, timeout=30)

        if response.status_code == 200:
            print("✅ JSON request successful")
            print(f"Response: {response.text[:200]}...")
            return True
        else:
            print(f"❌ JSON request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ JSON request failed: {e}")
        return False

def main():
    print("Testing Claude Bot Server...")
    print("=" * 50)

    # Test health check
    print("1. Testing health check...")
    if not test_health_check():
        print("❌ Server appears to be down. Start it with: ./start-claude-bot.sh")
        sys.exit(1)

    print()

    # Test form-encoded request
    print("2. Testing form-encoded request...")
    test_form_encoded_request()

    print()

    # Test JSON request
    print("3. Testing JSON request...")
    test_json_request()

    print()
    print("=" * 50)
    print("✅ All tests completed!")
    print()
    print("Next steps:")
    print("1. Set up a self-hosted GitHub runner with 'claude' label")
    print("2. Configure GitHub secrets: REPO_ACCESS_TOKEN and CLAUDE_ENDPOINT")
    print("3. Test with '/claude <prompt>' in a PR comment")

if __name__ == '__main__':
    main()
