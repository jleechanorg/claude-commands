"""
Command Composition Hook for Claude Code CLI.
Uses Claude's LLM to interpret command compositions naturally.
"""
import json
import os

def is_composition_command(command_line):
    """
    Detect if command line should use natural language interpretation.

    Args:
        command_line (str): User input like "/debug /test src/" or "/please run tests carefully"

    Returns:
        bool: True if should use Claude interpretation (natural language default)
    """
    if not command_line.strip():
        return False

    # Check if it starts with / (any slash command gets Claude interpretation)
    if command_line.strip().startswith('/'):
        return True

    # For now, only handle slash-based commands
    # Future: could handle pure natural language like "run tests carefully"
    return False

def get_available_commands():
    """
    Get context about available commands for Claude interpretation.
    Based on comprehensive analysis of all user-defined commands.

    Returns:
        dict: Command context for Claude
    """
    return {
        "protocol_commands": [
            # Core Actions (DO things)
            "/test", "/testui", "/testuif", "/testhttp", "/testhttpf",
            "/testi", "/teste", "/tester", "/testerc", "/testserver",
            "/coverage", "/execute", "/e", "/plan",

            # Analysis & Review
            "/arch", "/archreview", "/review", "/reviewdeep", "/replicate",

            # Development Workflow
            "/pr", "/push", "/pushlite", "/integrate", "/newbranch", "/nb",

            # Documentation & Planning
            "/learn", "/scratchpad", "/roadmap", "/r", "/milestones", "/handoff",

            # Multi-agent & Orchestration
            "/orchestrate", "/orch", "/copilot",

            # Search & Research
            "/perp",

            # Comment Management
            "/commentr", "/commentreply",

            # Utilities & Tools
            "/list", "/header", "/usage", "/context", "/con", "/bclean",
            "/localserver", "/puppeteer", "/optimize", "/experiment",
            "/ghfixtests", "/4layer", "/tdd", "/rg", "/newb"
        ],
        "natural_modifiers": [
            # Thinking & Analysis Modifiers
            "/think", "/thinku", "/debug",

            # Quality & Thoroughness Modifiers
            "/paranoid", "/minimal", "/complete", "/thorough", "/clean",

            # Style & Approach Modifiers
            "/verbose", "/performance", "/combinations", "/combo-help",

            # Action Modifiers (virtual commands that modify how things are done)
            "/deploy",

            # Enhanced Execution Modifiers
            "/execute-enhanced", "/ENHANCED_ALIASES", "/LEARN_ENHANCEMENT_SUMMARY",
            "/MEMORY_INTEGRATION"
        ],
        "command_descriptions": {
            # Protocol Commands (Actions)
            "/test": "Run full test suite and check GitHub CI status",
            "/testui": "Run REAL browser tests with mock APIs using Puppeteer MCP",
            "/testuif": "Run REAL browser tests with REAL APIs (costs money!)",
            "/testhttp": "Run HTTP request tests with mock APIs",
            "/testhttpf": "Run HTTP request tests with REAL APIs (costs money!)",
            "/coverage": "Run Python test coverage analysis and identify gaps",
            "/execute": "Execute tasks immediately using available tools",
            "/plan": "Same as execute but requires user approval first",
            "/arch": "Conduct comprehensive architecture and design reviews",
            "/pr": "Complete development lifecycle from thinking through to PR review",
            "/push": "Pre-push review, validation, PR update, and test server startup",
            "/learn": "Capture and document learnings with Memory MCP integration",
            "/orchestrate": "Multi-agent orchestration for complex development tasks",
            "/copilot": "Make PR mergeable by resolving ALL comments and fixing tests",
            "/integrate": "Create fresh branch from main and cleanup test servers",
            "/newbranch": "Create new branch from latest main",
            "/review": "Process ALL PR comments systematically with tracking",
            "/replicate": "Analyze and replicate functionality from other PRs",
            "/perp": "Multi-engine search across Claude, DuckDuckGo, and Perplexity with synthesized results",
            "/commentr": "Systematically address all GitHub PR comments with replies",
            "/commentreply": "Systematically address all GitHub PR comments with inline replies",
            "/context": "Show context usage percentage and breakdown",
            "/deploy": "Deploy to specified environment",

            # Natural Modifiers (How to do things)
            "/debug": "Enable verbose debug output and detailed analysis",
            "/think": "Enable analytical/thinking mode with sequential reasoning",
            "/paranoid": "Add strict validation, safety checks, and verification",
            "/minimal": "Quick execution with reduced scope and essentials only",
            "/complete": "Thorough comprehensive execution covering all aspects",
            "/thorough": "Detailed methodical approach with full coverage",
            "/clean": "Focus on code quality, organization, and cleanliness",
            "/verbose": "Detailed explanatory output with extra information",
            "/performance": "Optimize for speed, efficiency, and performance"
        }
    }

def interpret_composition_with_claude(command_line):
    """
    Use Claude to interpret command composition naturally - REAL API INTEGRATION.

    Args:
        command_line (str): Like "/debug /paranoid /test src/" or "/please run tests carefully on mvp_site"

    Returns:
        dict: {
            'protocol_command': '/test',
            'arguments': ['src/'],
            'context_flags': {'debug': True, 'paranoid': True},
            'execution_plan': 'Run comprehensive tests on src/ with debug output and paranoid validation',
            'success': True
        }
    """
    import subprocess
    import tempfile

    commands_context = get_available_commands()

    # Create prompt for Claude - supports ANYTHING, not just predefined commands
    prompt = f"""Interpret this command for Claude Code CLI. Support ANY natural language, not just predefined commands:

Command: "{command_line}"

Available Commands Context:
{json.dumps(commands_context, indent=2)}

Rules:
1. ANY text starting with / can be a natural modifier, even if not in the list
2. Support natural language like "/please run tests carefully"
3. If you see unknown /commands, interpret them contextually
4. Natural language is the DEFAULT - be flexible and intelligent

Please respond with a JSON object containing:
- protocol_command: The main action command (like "/test", "/deploy")
- arguments: List of non-command arguments (like ["src/", "production"])
- context_flags: Dict of boolean flags based on modifiers (like {{"debug": true, "paranoid": true, "careful": true}})
- execution_plan: Human-readable description of what will be executed
- success: true if interpretation successful, false if unclear

Examples:
Input: "/debug /paranoid /test mvp_site/"
Output: {{"protocol_command": "/test", "arguments": ["mvp_site/"], "context_flags": {{"debug": true, "paranoid": true}}, "execution_plan": "Run comprehensive tests on mvp_site/ with debug output and paranoid validation", "success": true}}

Input: "/please /carefully /test the integration folder"
Output: {{"protocol_command": "/test", "arguments": ["integration"], "context_flags": {{"careful": true, "thorough": true}}, "execution_plan": "Run careful comprehensive tests on integration folder", "success": true}}

Respond with only the JSON object, no other text."""

    try:
        # Use Claude API through the existing claude command
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(prompt)
            temp_file = f.name

        # Call Claude CLI directly for real interpretation
        # Use a direct prompt rather than file to ensure JSON response
        result = subprocess.run([
            'claude', '-p', prompt,
            '--output-format', 'json'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            try:
                # Parse Claude's JSON response - extract the actual result
                claude_response = json.loads(result.stdout.strip())

                # Check if this is the CLI metadata format
                if 'result' in claude_response and isinstance(claude_response['result'], str):
                    # Try to extract JSON from the result field
                    result_text = claude_response['result']
                    start = result_text.find('{')
                    end = result_text.rfind('}') + 1
                    if start >= 0 and end > start:
                        try:
                            actual_result = json.loads(result_text[start:end])
                            return actual_result
                        except json.JSONDecodeError:
                            pass
                    # If no JSON found in result, it's likely not a composition interpretation
                    print(f"⚠️ Claude returned non-JSON result: {result_text}")
                elif isinstance(claude_response, dict) and 'protocol_command' in claude_response:
                    # Direct JSON response format
                    return claude_response

            except json.JSONDecodeError:
                # If Claude didn't return valid JSON, try to extract JSON from the response
                response_text = result.stdout.strip()
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start >= 0 and end > start:
                    try:
                        return json.loads(response_text[start:end])
                    except json.JSONDecodeError:
                        pass

        # Fallback to local interpretation if Claude API fails
        print("⚠️ Claude API failed, using local interpretation")
        fallback_result = fallback_interpretation(command_line, commands_context)
        # Ensure fallback result has success key
        if 'success' not in fallback_result:
            fallback_result['success'] = True
        return fallback_result

    except Exception as e:
        print(f"⚠️ Claude API error: {e}, using local interpretation")
        fallback_result = fallback_interpretation(command_line, commands_context)
        # Ensure fallback result has success key
        if 'success' not in fallback_result:
            fallback_result['success'] = True
        return fallback_result
    finally:
        # Clean up temp file
        try:
            import os
            os.unlink(temp_file)
        except:
            pass

def fallback_interpretation(command_line, commands_context):
    """
    Fallback interpretation when Claude API is unavailable.
    Handles basic parsing with support for ANY natural language modifiers.
    """
    tokens = command_line.strip().split()

    # Find protocol command
    protocol_commands = set(commands_context["protocol_commands"])
    natural_modifiers = set(commands_context["natural_modifiers"])

    protocol_command = None
    context_flags = {}
    arguments = []

    for token in tokens:
        if token in protocol_commands:
            protocol_command = token
        elif token.startswith('/'):
            # ANY /command that's not a protocol command is treated as natural modifier
            # Handle known modifiers with specific flags
            if token == "/debug":
                context_flags.update({"debug": True, "verbose": True})
            elif token == "/paranoid":
                context_flags.update({"paranoid": True, "strict": True})
            elif token == "/minimal":
                context_flags.update({"minimal": True, "quick": True})
            elif token == "/think":
                context_flags.update({"thinking": True, "analytical": True})
            else:
                # Unknown /command gets interpreted as natural language
                # Remove the / and use the word as a flag
                flag_name = token[1:]  # Remove /
                context_flags[flag_name] = True
                # Try to infer related flags
                if any(word in flag_name.lower() for word in ['careful', 'thorough', 'complete']):
                    context_flags['thorough'] = True
                if any(word in flag_name.lower() for word in ['quick', 'fast', 'rapid']):
                    context_flags['quick'] = True
                if any(word in flag_name.lower() for word in ['verbose', 'detail', 'explain']):
                    context_flags['verbose'] = True
        else:
            arguments.append(token)

    if not protocol_command:
        return {
            "protocol_command": None,
            "arguments": arguments,
            "context_flags": context_flags,
            "execution_plan": "No clear protocol command found",
            "success": False
        }

    # Generate execution plan
    plan_parts = [f"Execute {protocol_command}"]
    if arguments:
        plan_parts.append(f"on {' '.join(arguments)}")

    modifiers = []
    if context_flags.get("debug"):
        modifiers.append("debug verbose output")
    if context_flags.get("paranoid"):
        modifiers.append("paranoid validation checks")
    if context_flags.get("minimal"):
        modifiers.append("minimal quick execution")
    if context_flags.get("thinking"):
        modifiers.append("analytical thinking mode")

    if modifiers:
        plan_parts.append(f"with {' and '.join(modifiers)}")

    execution_plan = ' '.join(plan_parts)

    return {
        "protocol_command": protocol_command,
        "arguments": arguments,
        "context_flags": context_flags,
        "execution_plan": execution_plan,
        "success": True
    }

def handle_composition_command(command_line):
    """
    Main entry point for handling command compositions.

    Args:
        command_line (str): User input

    Returns:
        dict: Interpretation result or None for single commands
    """
    if not is_composition_command(command_line):
        return None  # Let normal CLI handle single commands

    print(f"🧠 Interpreting composition: {command_line}")
    result = interpret_composition_with_claude(command_line)

    if result['success']:
        print(f"📋 Plan: {result['execution_plan']}")
        return result
    else:
        print(f"❌ Could not interpret: {result['execution_plan']}")
        return None

# Example usage and testing
if __name__ == "__main__":
    test_cases = [
        "/test src/",                              # Single command (should return None)
        "/debug /test src/",                       # Debug test
        "/paranoid /deploy production",            # Paranoid deploy
        "/debug /paranoid /minimal /test mvp_site/", # Multiple modifiers
        "/think /arch codebase",                   # Thinking architecture review
        "/complete /coverage integration/"         # Thorough coverage
    ]

    print("=== Command Composition Hook Test ===\n")

    for test in test_cases:
        print(f"Input: {test}")
        result = handle_composition_command(test)

        if result is None:
            print("→ Single command, handled by normal CLI\n")
        else:
            print(f"→ Protocol: {result['protocol_command']}")
            print(f"→ Flags: {result['context_flags']}")
            print(f"→ Args: {result['arguments']}")
            print(f"→ Plan: {result['execution_plan']}\n")
