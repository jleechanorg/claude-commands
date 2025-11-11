#!/usr/bin/env python3
"""
Header compliance checker with Memory MCP integration
Detects if previous response was missing mandatory branch header
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path


class HeaderComplianceChecker:
    """Check for missing headers and save violations to Memory MCP"""

    # Regex pattern for valid header
    HEADER_PATTERN = r"\[Local:\s+[^\]]+\|\s+Remote:\s+[^\]]+\|\s+PR:\s+[^\]]+\]"

    def __init__(self):
        self.violation_detected = False
        self.previous_response = None

    def check_previous_response(self, response_text: str) -> bool:
        """Check if response has the mandatory header at the end"""
        if not response_text:
            return True  # No response to check

        # Truncate very long responses for performance
        check_text = response_text[-500:]  # Check last 500 chars

        # Look for header pattern
        return bool(re.search(self.HEADER_PATTERN, check_text))

    def save_violation_to_memory_mcp(self) -> dict:
        """Save header violation to Memory MCP"""
        timestamp = datetime.now().isoformat()
        entity_name = f"header_violation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # This is where we would call the actual Memory MCP function
        # For now, we'll print what would be saved
        entity_data = {
            "entities": [
                {
                    "name": entity_name,
                    "entityType": "compliance_violation",
                    "observations": [
                        "Violation type: MANDATORY_HEADER missing",
                        "Severity: CRITICAL",
                        "Rule: Every response must end with branch header format",
                        f"Detected at: {timestamp}",
                        "Pattern: [Local: <branch> | Remote: <upstream> | PR: <info>]",
                        "Action taken: User invoked /header command to fix",
                        "Learning: Automatic header generation prevents this violation",
                    ],
                }
            ]
        }

        # Save to Memory MCP
        try:
            # Import this at runtime to check if MCP is available

            # Try to use MCP through Claude's interface
            # This would work if called from within Claude with MCP access
            # For standalone script, we'll need to implement differently

            # Log to a JSON file that could be read by MCP later
            mcp_queue_file = (
                Path.home() / ".cache" / "claude-learning" / "mcp_queue.json"
            )
            mcp_queue_file.parent.mkdir(parents=True, exist_ok=True)

            # Read existing queue
            queue = []
            if mcp_queue_file.exists():
                with open(mcp_queue_file, "r") as f:
                    queue = json.load(f)

            # Add our entity
            queue.append(entity_data)

            # Write back
            with open(mcp_queue_file, "w") as f:
                json.dump(queue, f, indent=2)

            print(f"📁 Queued for Memory MCP: {mcp_queue_file}")

        except Exception as e:
            print(f"⚠️ Could not queue for Memory MCP: {e}")

        return entity_data

    def report_violation(self):
        """Report the violation detection"""
        print("🚨 HEADER VIOLATION DETECTED!")
        print("Your previous response was missing the mandatory branch header.")
        print("✅ Saving violation to Memory MCP for learning...")

        # Save to Memory MCP
        entity = self.save_violation_to_memory_mcp()

        print(f"📝 Saved as: {entity['entities'][0]['name']}")
        print("\n💡 Remember: Every response must end with the branch header!")
        print("   Format: [Local: branch | Remote: upstream | PR: info]\n")


def main():
    """Main entry point for header checking"""
    checker = HeaderComplianceChecker()

    # Get response text from command line argument for validation

    # Check if we have a test response passed as argument
    if len(sys.argv) > 1:
        previous_response = sys.argv[1]
    else:
        # Simulate checking - would need actual conversation context
        previous_response = ""

    # Check for header
    has_header = checker.check_previous_response(previous_response)

    if not has_header:
        checker.report_violation()
        sys.exit(1)  # Exit with error code to indicate violation
    else:
        print("✅ Previous response had proper header - no violation detected.")
        sys.exit(0)  # Exit successfully


if __name__ == "__main__":
    main()
