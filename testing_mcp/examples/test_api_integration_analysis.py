#!/usr/bin/env python3
"""
Unified API Integration Analysis

Static analysis of Flask and MCP server integration with world_logic.py
to verify consistency, duplication, and integration completeness.
"""

import os
import re


class UnifiedAPIIntegrationAnalyzer:
    """Analyzes unified API integration across Flask and MCP interfaces."""

    def __init__(self):
        self.mvp_site_path = os.path.join(os.path.dirname(__file__), 'mvp_site')
        self.results = {}

    def analyze_world_logic_structure(self) -> dict:
        """Analyze world_logic.py structure and available functions."""
        print("=== Analyzing Unified API Structure ===")

        world_logic_path = os.path.join(self.mvp_site_path, 'world_logic.py')

        if not os.path.exists(world_logic_path):
            return {"error": "world_logic.py not found"}

        with open(world_logic_path) as f:
            content = f.read()

        # Find async function definitions
        async_functions = re.findall(r'async def (\w+)\(', content)
        regular_functions = re.findall(r'^def (\w+)\(', content, re.MULTILINE)

        # Filter out private functions
        public_functions = [f for f in async_functions + regular_functions if not f.startswith('_')]

        print(f"✅ Found {len(public_functions)} public functions in world_logic.py:")
        for func in sorted(public_functions):
            print(f"   - {func}")

        return {
            "public_functions": public_functions,
            "async_functions": async_functions,
            "regular_functions": regular_functions,
            "total_lines": len(content.split('\n'))
        }

    def analyze_flask_integration(self) -> dict:
        """Analyze Flask routes integration with world_logic."""
        print("\n=== Analyzing Flask Integration ===")

        main_py_path = os.path.join(self.mvp_site_path, 'main.py')

        if not os.path.exists(main_py_path):
            return {"error": "main.py not found"}

        with open(main_py_path) as f:
            content = f.read()

        # Check for world_logic import
        has_import = 'import world_logic' in content

        # Find world_logic function calls
        unified_calls = re.findall(r'world_logic\.(\w+)\(', content)
        unique_calls = list(set(unified_calls))

        # Count Flask routes
        routes = re.findall(r'@app\.route\([\'"]([^\'"]+)[\'"]', content)

        print(f"✅ world_logic import: {has_import}")
        print(f"✅ Found {len(unique_calls)} unique world_logic calls:")
        for call in sorted(unique_calls):
            count = unified_calls.count(call)
            print(f"   - world_logic.{call}() [{count} times]")

        print(f"✅ Found {len(routes)} Flask routes")

        return {
            "has_unified_import": has_import,
            "unified_calls": unique_calls,
            "call_counts": {call: unified_calls.count(call) for call in unique_calls},
            "routes_count": len(routes),
            "routes": routes
        }

    def analyze_mcp_integration(self) -> dict:
        """Analyze MCP server integration with world_logic."""
        print("\n=== Analyzing MCP Server Integration ===")

        world_logic_path = os.path.join(self.mvp_site_path, 'world_logic.py')

        if not os.path.exists(world_logic_path):
            return {"error": "world_logic.py not found"}

        with open(world_logic_path) as f:
            content = f.read()

        # Check for world_logic import
        has_import = 'import world_logic' in content or 'from world_logic' in content

        # Find world_logic function calls
        unified_calls = re.findall(r'world_logic\.(\w+)\(', content)
        unique_calls = list(set(unified_calls))

        # Find MCP tool functions
        tool_functions = re.findall(r'async def (_\w+_tool)\(', content)

        # Find regular async functions
        async_functions = re.findall(r'async def (\w+)\(', content)

        print(f"❌ world_logic import: {has_import}")
        print(f"❌ Found {len(unique_calls)} world_logic calls:")
        if unique_calls:
            for call in sorted(unique_calls):
                count = unified_calls.count(call)
                print(f"   - world_logic.{call}() [{count} times]")
        else:
            print("   - No world_logic calls found")

        print(f"✅ Found {len(tool_functions)} MCP tool functions:")
        for tool in sorted(tool_functions):
            print(f"   - {tool}")

        return {
            "has_unified_import": has_import,
            "unified_calls": unique_calls,
            "call_counts": {call: unified_calls.count(call) for call in unique_calls},
            "tool_functions": tool_functions,
            "async_functions": async_functions
        }

    def analyze_business_logic_duplication(self) -> dict:
        """Analyze business logic duplication between Flask and MCP."""
        print("\n=== Analyzing Business Logic Duplication ===")

        main_py_path = os.path.join(self.mvp_site_path, 'main.py')
        world_logic_path = os.path.join(self.mvp_site_path, 'world_logic.py')
        world_logic_path = os.path.join(self.mvp_site_path, 'world_logic.py')

        files_content = {}
        for name, path in [("main.py", main_py_path), ("world_logic.py", world_logic_path), ("world_logic.py", world_logic_path)]:
            if os.path.exists(path):
                with open(path) as f:
                    files_content[name] = f.read()

        # Business logic patterns to check for duplication
        patterns = [
            '_prepare_game_state',
            '_cleanup_legacy_state',
            '_build_campaign_prompt',
            '_handle_debug_mode_command',
            'gemini_service.get_initial_story',
            'gemini_service.continue_story',
            'firestore_service.create_campaign',
            'firestore_service.update_campaign_game_state',
            'GameState.from_dict',
            'process_story_for_display',
            'get_user_settings',
            'update_user_settings'
        ]

        duplications = {}
        for pattern in patterns:
            locations = []
            for file_name, content in files_content.items():
                if pattern in content:
                    locations.append(file_name)

            if len(locations) > 1:
                duplications[pattern] = locations
                print(f"❌ DUPLICATE: {pattern} found in {', '.join(locations)}")
            elif len(locations) == 1:
                print(f"✅ {pattern} found only in {locations[0]}")
            else:
                print(f"⚠️  {pattern} not found in any file")

        print(f"\n📊 Summary: {len(duplications)} patterns duplicated across files")

        return {
            "duplicated_patterns": duplications,
            "patterns_checked": patterns,
            "files_analyzed": list(files_content.keys())
        }

    def analyze_json_response_consistency(self) -> dict:
        """Analyze JSON response format consistency."""
        print("\n=== Analyzing JSON Response Consistency ===")

        world_logic_path = os.path.join(self.mvp_site_path, 'world_logic.py')

        if not os.path.exists(world_logic_path):
            return {"error": "world_logic.py not found"}

        with open(world_logic_path) as f:
            content = f.read()

        # Check for standard response patterns
        success_patterns = [
            'KEY_SUCCESS',
            '"success": True',
            '"success": true',
            'create_success_response'
        ]

        error_patterns = [
            'KEY_ERROR',
            '"error":',
            '"success": False',
            '"success": false',
            'create_error_response'
        ]

        success_found = [p for p in success_patterns if p in content]
        error_found = [p for p in error_patterns if p in content]

        print(f"✅ Success response patterns found: {len(success_found)}")
        for pattern in success_found:
            print(f"   - {pattern}")

        print(f"✅ Error response patterns found: {len(error_found)}")
        for pattern in error_found:
            print(f"   - {pattern}")

        # Check for response helper functions
        has_helper_functions = 'create_error_response' in content and 'create_success_response' in content
        print(f"✅ Response helper functions: {has_helper_functions}")

        return {
            "success_patterns": success_found,
            "error_patterns": error_found,
            "has_helper_functions": has_helper_functions
        }

    def run_complete_analysis(self) -> dict:
        """Run complete analysis and provide integration assessment."""
        print("=" * 70)
        print("UNIFIED API INTEGRATION ANALYSIS")
        print("=" * 70)

        results = {}

        # Run all analyses
        results["world_logic"] = self.analyze_world_logic_structure()
        results["flask"] = self.analyze_flask_integration()
        results["mcp"] = self.analyze_mcp_integration()
        results["duplication"] = self.analyze_business_logic_duplication()
        results["json_consistency"] = self.analyze_json_response_consistency()

        # Generate integration assessment
        print("\n" + "=" * 70)
        print("INTEGRATION ASSESSMENT")
        print("=" * 70)

        flask_integrated = results["flask"].get("has_unified_import", False) and len(results["flask"].get("unified_calls", [])) > 0
        mcp_integrated = results["mcp"].get("has_unified_import", False) and len(results["mcp"].get("unified_calls", [])) > 0

        print(f"✅ Flask Integration Status: {'COMPLETE' if flask_integrated else 'INCOMPLETE'}")
        print(f"❌ MCP Integration Status: {'COMPLETE' if mcp_integrated else 'INCOMPLETE'}")

        duplication_count = len(results["duplication"].get("duplicated_patterns", {}))
        print(f"{'❌' if duplication_count > 0 else '✅'} Business Logic Duplication: {duplication_count} patterns duplicated")

        has_consistent_responses = results["json_consistency"].get("has_helper_functions", False)
        print(f"✅ JSON Response Consistency: {'STANDARDIZED' if has_consistent_responses else 'NEEDS_WORK'}")

        # Overall assessment
        print("\n📊 OVERALL STATUS:")
        if flask_integrated and mcp_integrated and duplication_count == 0:
            print("✅ FULLY INTEGRATED - Both Flask and MCP use unified API with no duplication")
        elif flask_integrated and not mcp_integrated:
            print("⚠️  PARTIALLY INTEGRATED - Flask uses unified API, MCP needs integration")
        elif not flask_integrated and mcp_integrated:
            print("⚠️  PARTIALLY INTEGRATED - MCP uses unified API, Flask needs integration")
        else:
            print("❌ NOT INTEGRATED - Neither Flask nor MCP properly use unified API")

        results["assessment"] = {
            "flask_integrated": flask_integrated,
            "mcp_integrated": mcp_integrated,
            "duplication_count": duplication_count,
            "has_consistent_responses": has_consistent_responses
        }

        return results


def main():
    """Run the unified API integration analysis."""
    analyzer = UnifiedAPIIntegrationAnalyzer()
    results = analyzer.run_complete_analysis()

    # Generate recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)

    assessment = results["assessment"]

    if not assessment["mcp_integrated"]:
        print("1. ❌ CRITICAL: Update world_logic.py to use world_logic functions")
        print("   - Add: import world_logic")
        print("   - Replace MCP tool business logic with world_logic calls")
        print("   - Remove duplicate business logic from world_logic.py")

    if assessment["duplication_count"] > 0:
        print("2. ❌ CRITICAL: Remove business logic duplication")
        print("   - Move all business logic to world_logic.py")
        print("   - Update both Flask and MCP to call unified functions")

    if assessment["flask_integrated"] and not assessment["mcp_integrated"]:
        print("3. ✅ GOOD: Flask integration is complete")
        print("4. ❌ TODO: Complete MCP integration to match Flask")

    print("\nNext Steps:")
    print("- Update world_logic.py MCP tools to call world_logic functions")
    print("- Test that Flask and MCP return identical JSON responses")
    print("- Verify no business logic duplication remains")


if __name__ == "__main__":
    main()
