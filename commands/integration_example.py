"""
Example: How to integrate hook + LLM command composition with existing Claude Code CLI.

This shows the minimal changes needed to add natural composition support using Claude's LLM.
"""


# Example 1: Existing test command (before)
def test_command_old(target_directory):
    """Original test command - single argument, no context"""
    print(f"Running tests in {target_directory}")
    # ... existing test logic
    return True


# Example 2: Enhanced test command (after)
def test_command_new(target_directory, debug=False, paranoid=False, minimal=False):
    """Enhanced test command - same functionality + context flags"""

    # Basic functionality (unchanged)
    print(f"Running tests in {target_directory}")

    # Enhanced behavior based on context flags
    if debug:
        print("🐛 DEBUG MODE: Verbose test execution")
        print("   - Analyzing test files...")
        print("   - Checking test dependencies...")
        print("   - Setting up test environment...")

    if paranoid:
        print("🔍 PARANOID MODE: Additional validation checks")
        print("   - Verifying test integrity...")
        print("   - Checking for test conflicts...")
        print("   - Validating test data...")

    if minimal:
        print("⚡ MINIMAL MODE: Reduced test scope")
        print("   - Running essential tests only...")
    else:
        print("📊 Running comprehensive test suite...")

    # ... existing test logic (unchanged)
    return True


# Example 3: Enhanced deploy command
def deploy_command_new(environment, paranoid=False, verbose=False):
    """Enhanced deploy command with context flags"""

    print(f"Deploying to {environment}")

    if paranoid:
        print("🔍 PARANOID MODE: Strict deployment validation")
        print("   - Verifying deployment target...")
        print("   - Checking environment health...")
        print("   - Validating configuration...")

    if verbose:
        print("📝 VERBOSE MODE: Detailed deployment output")
        print("   - Deployment progress details...")

    print("🚀 Deployment completed")
    return True


# Example 4: Claude Code CLI integration with hook + LLM approach
def claude_cli_parser_with_hook(command_line):
    """Enhanced CLI parser using hook + LLM interpretation"""

    # Import our composition hook
    from composition_hook import handle_composition_command

    # Try composition interpretation first
    composition_result = handle_composition_command(command_line)

    if composition_result:
        # Execute based on Claude's interpretation
        execute_command_with_context(
            composition_result["protocol_command"],
            composition_result["arguments"],
            **composition_result["context_flags"],
        )
    else:
        # Use existing single command parsing
        execute_single_command(command_line)


def execute_command_with_context(protocol_command, arguments, **context_flags):
    """Execute a protocol command with context flags"""

    if protocol_command == "/test":
        # Call enhanced test command with flags
        test_command_new(
            arguments[0] if arguments else ".",
            debug=context_flags.get("debug", False),
            paranoid=context_flags.get("paranoid", False),
            minimal=context_flags.get("minimal", False),
        )
    elif protocol_command == "/deploy":
        # Call enhanced deploy command with flags
        deploy_command_new(
            arguments[0] if arguments else "staging",
            paranoid=context_flags.get("paranoid", False),
            verbose=context_flags.get("verbose", False),
        )
    # ... add more commands as needed


def execute_single_command(command_line):
    """Handle single commands with existing CLI logic"""
    print(f"Executing single command: {command_line}")
    # ... existing single command logic


# Example 5: Testing the integration
def test_integration():
    """Test the simple composition integration"""

    test_cases = [
        "/test src/",  # Basic test
        "/debug /test src/",  # Debug test
        "/paranoid /test integration/",  # Paranoid test
        "/debug /paranoid /test mvp_site/",  # Combined modes
        "/minimal /test unit/",  # Minimal test
    ]

    print("=== Testing Simple Command Composition Integration ===")

    for command in test_cases:
        print(f"\n--- Command: {command} ---")
        claude_cli_parser_with_hook(command)


if __name__ == "__main__":
    test_integration()
