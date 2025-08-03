#!/usr/bin/env python3
"""
MCP Integration Demonstration

This test demonstrates how MCP server tools should be integrated with world_logic
and provides example integration code for world_logic.py.
"""

import asyncio
import json


# Mock the world_logic calls for demonstration
class MockUnifiedAPI:
    """Mock unified API for demonstration purposes."""

    @staticmethod
    async def create_campaign_unified(request_data):
        """Mock create campaign."""
        return {
            "success": True,
            "campaign_id": "mock-campaign-123",
            "title": request_data.get("title"),
            "opening_story": "Mock opening story...",
            "game_state": {"mock": "state"},
            "attribute_system": "dnd",
        }

    @staticmethod
    async def process_action_unified(request_data):
        """Mock process action."""
        return {
            "success": True,
            "story": [{"story": "Mock story response..."}],
            "game_state": {"mock": "updated_state"},
            "state_changes": {"mock": "changes"},
            "mode": request_data.get("mode", "character"),
            "user_input": request_data.get("user_input"),
        }

    @staticmethod
    async def get_campaign_state_unified(request_data):
        """Mock get campaign state."""
        return {
            "success": True,
            "campaign": {"title": "Mock Campaign"},
            "game_state": {"mock": "state"},
            "state_cleaned": False,
            "entries_cleaned": 0,
        }


async def demonstrate_current_mcp_approach(args):
    """Demonstrate current MCP tool approach (with duplicated business logic)."""
    print("=== Current MCP Approach (Before Integration) ===")

    # This simulates current world_logic.py approach
    args["user_id"]
    title = args["title"]
    character = args.get("character", "")
    setting = args.get("setting", "")
    description = args.get("description", "")

    # DUPLICATE business logic (same as in world_logic.py)
    if not title:
        return {"error": "Title is required"}

    # Build prompt (DUPLICATE logic)
    prompt_parts = []
    if character:
        prompt_parts.append(f"Character: {character}")
    if setting:
        prompt_parts.append(f"Setting: {setting}")
    if description:
        prompt_parts.append(f"Description: {description}")
    prompt = " | ".join(prompt_parts) if prompt_parts else ""

    # Create campaign (DUPLICATE service calls)
    result = {
        "campaign_id": "current-approach-123",
        "title": title,
        "prompt": prompt,
        "approach": "current_duplicate_logic",
    }

    print(f"📊 Current Result: {json.dumps(result, indent=2)}")
    return result


async def demonstrate_integrated_mcp_approach(args):
    """Demonstrate integrated MCP tool approach (using world_logic)."""
    print("\n=== Integrated MCP Approach (After Integration) ===")

    # This simulates how world_logic.py SHOULD work after integration
    try:
        # Simply call unified API - no duplicate business logic
        result = await MockUnifiedAPI.create_campaign_unified(args)

        # MCP tool just handles MCP-specific formatting
        mcp_result = {
            "success": result["success"],
            "campaign_id": result["campaign_id"],
            "title": result["title"],
            "opening_story": result["opening_story"],
            "game_state": result["game_state"],
            "approach": "integrated_world_logic",
        }

        print(f"📊 Integrated Result: {json.dumps(mcp_result, indent=2)}")
        return mcp_result

    except Exception as e:
        return {"error": f"Failed to create campaign: {str(e)}"}


def demonstrate_response_format_consistency():
    """Demonstrate JSON response format consistency."""
    print("\n=== Response Format Consistency Test ===")

    # Unified API standard response formats
    success_response = {
        "success": True,
        "campaign_id": "test-123",
        "title": "Test Campaign",
        "data": "...",
    }

    error_response = {
        "success": False,
        "error": "Test error message",
        "status_code": 400,
    }

    print("✅ Standard Success Response:")
    print(json.dumps(success_response, indent=2))

    print("\n✅ Standard Error Response:")
    print(json.dumps(error_response, indent=2))

    print("\n✅ Both Flask and MCP should return identical JSON structures")


def generate_integration_code_example():
    """Generate example code showing how to integrate MCP tools with world_logic."""
    print("\n=== Integration Code Example ===")

    integration_example = """
# BEFORE: world_logic.py with duplicate business logic
async def _create_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    user_id = args["user_id"]
    title = args["title"]
    # ... 50+ lines of duplicate business logic ...
    # Duplicate: prompt building, validation, Gemini calls, Firestore calls
    result = {...}
    return [TextContent(type="text", text=json.dumps(result))]

# AFTER: world_logic.py integrated with world_logic
async def _create_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    try:
        # Use unified API - no duplicate business logic!
        result = await world_logic.create_campaign_unified(args)

        # MCP tool just handles MCP-specific response formatting
        return [TextContent(type="text", text=json.dumps(result, default=json_default_serializer))]

    except Exception as e:
        error_response = world_logic.create_error_response(f"Failed to create campaign: {str(e)}")
        return [TextContent(type="text", text=json.dumps(error_response))]

# Benefits of integration:
# ✅ No business logic duplication
# ✅ Consistent JSON responses between Flask and MCP
# ✅ Single source of truth for game logic
# ✅ Easier testing and maintenance
# ✅ Bug fixes apply to both Flask and MCP automatically
"""

    print(integration_example)


async def run_comparison_tests():
    """Run comparison tests between current and integrated approaches."""
    print("=" * 80)
    print("MCP INTEGRATION DEMONSTRATION")
    print("=" * 80)

    # Test data
    test_args = {
        "user_id": "test-user-123",
        "title": "Test Campaign",
        "character": "A brave knight",
        "setting": "Medieval fantasy",
        "description": "An epic adventure",
    }

    # Test current approach
    await demonstrate_current_mcp_approach(test_args)

    # Test integrated approach
    await demonstrate_integrated_mcp_approach(test_args)

    # Compare results
    print("\n=== Comparison Analysis ===")

    print("🔍 Business Logic Location:")
    print("   Current: Duplicated in world_logic.py AND world_logic.py")
    print("   Integrated: Only in world_logic.py (single source of truth)")

    print("\n🔍 Maintenance Burden:")
    print("   Current: Bug fixes need to be applied in multiple places")
    print("   Integrated: Bug fixes automatically apply to both Flask and MCP")

    print("\n🔍 Response Consistency:")
    print("   Current: Flask and MCP may return different JSON structures")
    print("   Integrated: Flask and MCP return identical JSON structures")

    print("\n🔍 Code Lines:")
    print("   Current: ~100+ lines per MCP tool (business logic + MCP formatting)")
    print("   Integrated: ~10 lines per MCP tool (just MCP formatting)")

    # Format consistency demo
    demonstrate_response_format_consistency()

    # Code example
    generate_integration_code_example()


def main():
    """Run the MCP integration demonstration."""
    asyncio.run(run_comparison_tests())

    print("\n" + "=" * 80)
    print("INTEGRATION RECOMMENDATIONS")
    print("=" * 80)

    print(
        "1. ❌ CRITICAL: world_logic.py currently has 12 duplicated business logic patterns"
    )
    print("2. ❌ CRITICAL: MCP tools do NOT use world_logic functions")
    print("3. ✅ SOLUTION: Update all MCP tools to call world_logic functions")
    print("4. ✅ BENEFIT: Eliminate business logic duplication")
    print("5. ✅ BENEFIT: Ensure Flask and MCP return identical JSON responses")

    print("\nIMPLEMENTATION STEPS:")
    print("1. Add 'import world_logic' to world_logic.py")
    print("2. Replace MCP tool business logic with world_logic calls")
    print("3. Remove duplicate helper functions from world_logic.py")
    print("4. Test that Flask and MCP return identical JSON responses")
    print("5. Verify no business logic duplication remains")

    print("\nTEST VERIFICATION:")
    print("- Run test_api_integration_analysis.py to verify integration")
    print("- Ensure 'MCP Integration Status: COMPLETE'")
    print("- Ensure 'Business Logic Duplication: 0 patterns duplicated'")


if __name__ == "__main__":
    main()
