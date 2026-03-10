"""
Command Composition Hook for Claude Code CLI.
Uses Claude's LLM to interpret command compositions naturally.
"""
import json
import os

def is_composition_command(command_line):
    """
    Detect if command line contains composition syntax.
    
    Args:
        command_line (str): User input like "/debug /test src/"
        
    Returns:
        bool: True if multiple commands detected
    """
    if not command_line.strip():
        return False
        
    # Simple detection: multiple slash commands
    return command_line.count('/') > 1

def get_available_commands():
    """
    Get context about available commands for Claude interpretation.
    
    Returns:
        dict: Command context for Claude
    """
    return {
        "protocol_commands": [
            "/test", "/testui", "/deploy", "/coverage", "/arch", 
            "/execute", "/plan", "/learn", "/replicate", "/pr"
        ],
        "natural_modifiers": [
            "/debug", "/paranoid", "/minimal", "/complete", "/think", 
            "/verbose", "/thorough", "/clean", "/performance"
        ],
        "command_descriptions": {
            "/test": "Run tests on specified directory/files",
            "/testui": "Run UI tests with browser automation", 
            "/deploy": "Deploy to specified environment",
            "/coverage": "Analyze test coverage",
            "/debug": "Enable verbose debug output",
            "/paranoid": "Add strict validation and checks",
            "/minimal": "Quick execution with reduced scope",
            "/think": "Enable analytical/thinking mode"
        }
    }

def interpret_composition_with_claude(command_line):
    """
    Use Claude to interpret command composition naturally.
    
    Args:
        command_line (str): Like "/debug /paranoid /test src/"
        
    Returns:
        dict: {
            'protocol_command': '/test',
            'arguments': ['src/'],
            'context_flags': {'debug': True, 'paranoid': True},
            'execution_plan': 'Run comprehensive tests on src/ with debug output and paranoid validation',
            'success': True
        }
    """
    commands_context = get_available_commands()
    
    # Create prompt for Claude
    prompt = f"""Interpret this command composition for Claude Code CLI:

Command: "{command_line}"

Available Commands Context:
{json.dumps(commands_context, indent=2)}

Please respond with a JSON object containing:
- protocol_command: The main action command (like "/test", "/deploy")  
- arguments: List of non-command arguments (like ["src/", "production"])
- context_flags: Dict of boolean flags based on modifiers (like {{"debug": true, "paranoid": true}})
- execution_plan: Human-readable description of what will be executed
- success: true if interpretation successful, false if unclear

Example:
Input: "/debug /paranoid /test $PROJECT_ROOT/"
Output: {{
  "protocol_command": "/test",
  "arguments": ["$PROJECT_ROOT/"],
  "context_flags": {{"debug": true, "paranoid": true, "verbose": true, "strict": true}},
  "execution_plan": "Run comprehensive tests on $PROJECT_ROOT/ with debug verbose output and paranoid validation checks",
  "success": true
}}

Respond with only the JSON object, no other text."""

    # In real implementation, this would call Claude API
    # For now, return a structured simulation
    return simulate_claude_interpretation(command_line, commands_context)

def simulate_claude_interpretation(command_line, commands_context):
    """
    Simulate Claude's interpretation for testing.
    In production, this would be replaced with actual Claude API call.
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
        elif token in natural_modifiers:
            # Map natural modifiers to flags
            if token == "/debug":
                context_flags.update({"debug": True, "verbose": True})
            elif token == "/paranoid":
                context_flags.update({"paranoid": True, "strict": True})
            elif token == "/minimal":
                context_flags.update({"minimal": True, "quick": True})
            elif token == "/think":
                context_flags.update({"thinking": True, "analytical": True})
        elif not token.startswith('/'):
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
        "/debug /paranoid /minimal /test $PROJECT_ROOT/", # Multiple modifiers
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