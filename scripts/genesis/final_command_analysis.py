#!/usr/bin/env python3
"""
Create a refined analysis focusing on actual user slash commands
"""
import json

def is_real_user_command(cmd, count):
    """Determine if this is likely a real user command vs noise"""

    # Real commands we know are used by users
    known_commands = {
        '/execute', '/copilot', '/tdd', '/redgreen', '/arch', '/pr', '/orch', '/orchestrate',
        '/think', '/debug', '/research', '/plan', '/guidelines', '/cons', '/consensus',
        '/reviewdeep', '/commentreply', '/commentfetch', '/commentcheck', '/fixpr',
        '/testllm', '/deploy', '/converge', '/pushl', '/review', '/help', '/newbranch',
        '/newb', '/fake3', '/checkpoint', '/context', '/lint', '/test', '/integrate',
        '/clear', '/perp', '/learn', '/cereb', '/cerebras', '/localserver'
    }

    # If it's a known command, include it
    if cmd in known_commands:
        return True

    # Filter out obvious non-commands
    non_commands = {
        # Branch/PR specific
        '/main', '/pull', '/status', '/repo', '/token',
        # URLs/APIs
        '/chat', '/completions', '/responses', '/openai', '/google',
        # File paths/configs
        '/run_tests', '/run_ui_tests', '/run_local_server', '/test_file',
        '/constants', '/model', '/output', '/campaigns', '/limits',
        # Project-specific identifiers
        '/gstatus', '/start_mcp_server', '/mcp', '/rg',
        # Error codes and statuses
        '/failure', '/errors', '/NO', '/CI', '/CD', '/PR'
    }

    if cmd in non_commands:
        return False

    # Include if it has significant usage (>= 10 occurrences) and looks like a command
    if count >= 10 and not any(x in cmd.lower() for x in ['_', '-', 'server', 'test', 'run']):
        return True

    return False

def main():
    # Read the full analysis
    with open('/Users/jleechan/projects/worktree_genesis/roadmap/agent_001_command_frequency.json', 'r') as f:
        data = json.load(f)

    # Filter to real user commands
    filtered_commands = {}

    for cmd, cmd_data in data['command_frequencies'].items():
        if is_real_user_command(cmd, cmd_data['count']):
            filtered_commands[cmd] = cmd_data

    # Create refined output
    refined_analysis = {
        "agent_id": "001",
        "chunk_range": "1-994",
        "total_prompts_analyzed": data['total_prompts_analyzed'],
        "files_processed": data['files_processed'],
        "total_commands_found": len(data['command_frequencies']),
        "real_user_commands_filtered": len(filtered_commands),
        "command_frequencies": dict(sorted(filtered_commands.items(),
                                         key=lambda x: x[1]['count'], reverse=True)),
        "methodology_notes": [
            "Filtered out file paths, URLs, and system artifacts",
            "Focused on actual user-issued slash commands",
            "Commands with <10 occurrences excluded unless known user commands",
            "Examples truncated to first 200 characters for readability"
        ]
    }

    # Save refined analysis
    with open('/Users/jleechan/projects/worktree_genesis/roadmap/agent_001_command_frequency_refined.json', 'w') as f:
        json.dump(refined_analysis, f, indent=2, ensure_ascii=False)

    # Print summary
    print("=== REFINED COMMAND FREQUENCY ANALYSIS ===")
    print(f"Agent: {refined_analysis['agent_id']}")
    print(f"Chunk Range: {refined_analysis['chunk_range']}")
    print(f"Total Prompts: {refined_analysis['total_prompts_analyzed']}")
    print(f"Raw Commands Found: {refined_analysis['total_commands_found']}")
    print(f"Real User Commands: {refined_analysis['real_user_commands_filtered']}")
    print()
    print("TOP 20 USER COMMANDS:")

    for i, (cmd, data) in enumerate(list(refined_analysis['command_frequencies'].items())[:20]):
        print(f"{i+1:2d}. {cmd:15s} : {data['count']:3d} occurrences")

    print(f"\nFull results saved to: roadmap/agent_001_command_frequency_refined.json")

if __name__ == "__main__":
    main()
