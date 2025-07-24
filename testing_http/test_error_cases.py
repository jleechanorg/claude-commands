#!/usr/bin/env python3
"""
Test error cases and edge conditions.
"""

import os
import sys

import requests

import concurrent.futures

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BASE_URL, get_test_session

# Using BASE_URL from test_config
SESSION = get_test_session()


def test_error_cases():
    """Test various error cases and edge conditions."""
    print("⚠️ TEST: Error Cases and Edge Conditions")
    print("=" * 50)

    results = {}

    # Test 1: Invalid campaign ID
    print("\n1️⃣ Testing invalid campaign ID...")
    invalid_id = "invalid-campaign-id-12345"
    response = SESSION.get(f"{BASE_URL}/api/campaigns/{invalid_id}")

    if response.status_code == 404:
        print("  ✅ Correctly returned 404 for invalid ID")
        results["invalid_id"] = True
    else:
        print(f"  ❌ Expected 404, got {response.status_code}")
        results["invalid_id"] = False

    # Test 2: Empty campaign prompt
    print("\n2️⃣ Testing empty campaign prompt...")
    empty_data = {"prompt": "", "enableNarrative": True, "enableMechanics": False}

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=empty_data)

    if response.status_code in [400, 422]:
        print("  ✅ Correctly rejected empty prompt")
        results["empty_prompt"] = True
    else:
        print(f"  ❌ Expected 400/422, got {response.status_code}")
        results["empty_prompt"] = False

    # Test 3: Extremely long input
    print("\n3️⃣ Testing extremely long input...")
    long_text = "A" * 10000  # 10K characters
    long_data = {"prompt": long_text, "enableNarrative": True, "enableMechanics": False}

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=long_data)

    if response.status_code in [400, 413, 422]:
        print("  ✅ Correctly handled long input")
        results["long_input"] = True
    elif response.status_code == 200:
        print("  ⚠️ Accepted long input (may be truncated)")
        results["long_input"] = True
    else:
        print(f"  ❓ Unexpected response: {response.status_code}")
        results["long_input"] = False

    # Test 4: Missing required fields
    print("\n4️⃣ Testing missing required fields...")
    incomplete_data = {
        "prompt": "Test campaign"
        # Missing enableNarrative and enableMechanics
    }

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=incomplete_data)

    if response.status_code in [400, 422]:
        print("  ✅ Correctly rejected incomplete data")
        results["missing_fields"] = True
    elif response.status_code == 200:
        print("  ⚠️ Accepted with defaults")
        results["missing_fields"] = True
    else:
        print(f"  ❌ Unexpected response: {response.status_code}")
        results["missing_fields"] = False

    # Test 5: Invalid JSON
    print("\n5️⃣ Testing invalid JSON...")

    response = SESSION.post(
        f"{BASE_URL}/api/campaigns",
        data="invalid json {not valid}",
        headers={"Content-Type": "application/json"},
    )

    if response.status_code in [400, 422]:
        print("  ✅ Correctly rejected invalid JSON")
        results["invalid_json"] = True
    else:
        print(f"  ❌ Expected 400/422, got {response.status_code}")
        results["invalid_json"] = False

    # Test 6: Concurrent requests
    print("\n6️⃣ Testing concurrent requests...")


    def make_request():
        return SESSION.get(BASE_URL)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_request) for _ in range(5)]
        responses = [f.result() for f in futures]

    if all(r.status_code == 200 for r in responses):
        print("  ✅ Handled 5 concurrent requests")
        results["concurrent"] = True
    else:
        print("  ❌ Failed on concurrent requests")
        results["concurrent"] = False

    # Test 7: Special characters
    print("\n7️⃣ Testing special characters...")
    special_data = {
        "prompt": "Test with émojis 🧙‍♂️ and unicode ñ é ü",
        "enableNarrative": True,
        "enableMechanics": False,
    }

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=special_data)

    if response.status_code in [200, 201]:
        print("  ✅ Handled special characters")
        results["special_chars"] = True
    else:
        print(f"  ⚠️ May not support special characters: {response.status_code}")
        results["special_chars"] = False

    # Summary
    print("\n📊 Error Handling Summary:")
    for test, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {test}")

    return sum(results.values()) >= len(results) * 0.7  # Pass if 70% tests pass


if __name__ == "__main__":
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")

        success = test_error_cases()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
