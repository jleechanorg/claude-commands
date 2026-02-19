#!/usr/bin/env python3
"""
Response Format Validator for Copilot Command
Validates responses.json format compatibility with commentreply.py
"""

import os
import sys
import json


def validate_response_format():
    """
    Validate the RESPONSES_FILE format for comment reply compatibility
    Returns: 0 for success, 1 for failure
    """
    responses_file = os.environ.get("RESPONSES_FILE", "")
    if not responses_file:
        print("❌ RESPONSES_FILE environment variable not set")
        return 1

    try:
        with open(responses_file, "r") as f:
            data = json.load(f)

        # Validate required structure
        if "responses" not in data:
            print("❌ CRITICAL: Missing responses array")
            return 1

        for i, response in enumerate(data["responses"]):
            if "comment_id" not in response:
                print(f"❌ CRITICAL: Missing comment_id in response {i}")
                return 1
            if "reply_text" not in response:
                print(f"❌ CRITICAL: Missing reply_text in response {i}")
                return 1

        print("✅ Response format validated")
        return 0

    except FileNotFoundError:
        print(f"❌ CRITICAL: Response file not found: {responses_file}")
        return 1
    except json.JSONDecodeError as e:
        print(f"❌ CRITICAL: Invalid JSON format: {e}")
        return 1
    except Exception as e:
        print(f"❌ CRITICAL: Response validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(validate_response_format())
