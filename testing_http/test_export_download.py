#!/usr/bin/env python3
"""
Test export/download functionality.
"""

import os
import sys

import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_config import BASE_URL, get_test_session

# Using BASE_URL from test_config
SESSION = get_test_session()


def test_export_download():
    """Test exporting campaigns in different formats."""
    print("📥 TEST: Export/Download Functionality")
    print("=" * 50)

    # First create a campaign with some content
    print("\n1️⃣ Creating campaign with content...")
    campaign_data = {
        "prompt": "A detective mystery in Victorian London",
        "enableNarrative": True,
        "enableMechanics": False,
    }

    response = SESSION.post(f"{BASE_URL}/api/campaigns", json=campaign_data)
    if response.status_code not in [200, 201]:
        print(f"❌ Campaign creation failed: {response.status_code}")
        return False

    campaign = response.json()
    campaign_id = campaign.get("campaign_id")
    print(f"✅ Campaign created: {campaign_id}")

    # Add some content
    print("\n2️⃣ Adding story content...")
    story_entries = [
        "I examine the crime scene carefully",
        "I interview the butler about last night",
        "I search for clues in the library",
    ]

    for entry in story_entries:
        story_data = {"campaignId": campaign_id, "input": entry, "mode": "character"}
        response = SESSION.post(
            f"{BASE_URL}/api/campaigns/{campaign_id}/interaction", json=story_data
        )
        if response.status_code == 200:
            print(f"  ✅ Added: '{entry}'")

    # Test export formats
    print("\n3️⃣ Testing export formats...")
    export_formats = ["txt", "pdf", "docx"]
    results = {}

    for format_type in export_formats:
        print(f"\n  Testing {format_type.upper()} export...")

        # Request export
        response = SESSION.get(
            f"{BASE_URL}/api/campaigns/{campaign_id}/export",
            params={"format": format_type},
        )

        if response.status_code == 200:
            # Check response headers
            content_type = response.headers.get("Content-Type", "")
            content_disp = response.headers.get("Content-Disposition", "")
            content_length = len(response.content)

            print("    ✅ Export successful")
            print(f"    📄 Content-Type: {content_type}")
            print(f"    📏 Size: {content_length} bytes")

            # Verify content type
            expected_types = {
                "txt": "text/plain",
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats",
            }

            correct_type = any(
                t in content_type for t in [expected_types.get(format_type, "")]
            )
            if correct_type:
                print("    ✅ Correct content type")
            else:
                print("    ❌ Wrong content type")

            # Check filename
            if f".{format_type}" in content_disp:
                print("    ✅ Correct file extension")

            results[format_type] = response.status_code == 200
        else:
            print(f"    ❌ Export failed: {response.status_code}")
            results[format_type] = False

    # Summary
    print("\n4️⃣ Export Summary:")
    for fmt, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {fmt.upper()} export")

    return all(results.values())


if __name__ == "__main__":
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Server running at {BASE_URL}\n")

        success = test_export_download()
        print(f"\n{'✅ TEST PASSED' if success else '❌ TEST FAILED'}")

    except Exception as e:
        print(f"❌ Error: {e}")
