#!/usr/bin/env python3
"""
Refined command frequency analysis for agent_002 conversation data chunk.
Focuses specifically on legitimate slash commands with strict filtering.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def extract_legitimate_slash_commands(text):
    """Extract only legitimate slash commands, strictly filtering file paths."""

    # Definitive list of legitimate slash commands
    legitimate_commands = {
        'execute', 'tdd', 'redgreen', 'copilot', 'cons', 'reviewdeep', 'arch', 'pr',
        'orch', 'think', 'debug', 'research', 'guidelines', 'plan', 'fixpr',
        'consensus', 'commentreply', 'commentfetch', 'commentcheck', 'fake3',
        'hooks', 'git-header', 'logging', 'pre_creation_blocker', 'auto_fix_placement',
        'manual_fix_placement', 'compose-commands', 'settings', 'reviewe',
        'cerebras', 'testmcp', 'testllm', 'run_mcp_tests', 'test', 'deploy',
        'build', 'lint', 'format', 'check', 'validate', 'inspect', 'analyze',
        'create', 'delete', 'update', 'modify', 'edit', 'review', 'merge',
        'commit', 'push', 'pull', 'fetch', 'status', 'diff', 'log', 'branch',
        'checkout', 'switch', 'reset', 'revert', 'cherry-pick', 'rebase',
        'stash', 'tag', 'remote', 'clone', 'init', 'add', 'remove', 'mv',
        'clean', 'config', 'help', 'version', 'info', 'show', 'describe',
        'pushl', 'pushlite', 'header', 'context', 'checkpoint'
    }

    # Pattern to match slash commands
    slash_pattern = r'/([a-zA-Z][a-zA-Z0-9_-]*)'
    matches = re.findall(slash_pattern, text)

    # Return only commands that are in our legitimate list
    valid_commands = []
    for match in matches:
        if match.lower() in legitimate_commands:
            valid_commands.append(f"/{match}")

    return valid_commands

def extract_direct_user_commands(raw_prompt):
    """Extract commands from prompts that are direct user commands."""
    # Look for lines that start with slash commands directly
    lines = raw_prompt.split('\n')
    user_commands = []

    for line in lines:
        stripped = line.strip()
        # Check for direct slash command usage
        if stripped.startswith('/') and len(stripped.split()) == 1:
            # This looks like a direct command
            cmd = stripped.split()[0]
            if len(cmd) <= 20 and cmd.count('/') == 1:  # Simple slash command
                user_commands.append(stripped)
        # Also check for lines that start with '>' (quoted user input)
        elif stripped.startswith('>'):
            user_content = stripped[1:].strip()
            if user_content.startswith('/') and len(user_content.split()) == 1:
                user_commands.append(user_content)

    return user_commands

def analyze_agent_002_refined():
    """Refined analysis focusing only on legitimate slash commands."""

    agent_dir = Path("/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/agent_002")

    if not agent_dir.exists():
        print(f"Directory not found: {agent_dir}")
        return

    command_counter = Counter()
    command_examples = defaultdict(list)
    total_prompts = 0
    processed_files = 0

    progress_files = sorted([f for f in agent_dir.glob("progress_*.json")])
    print(f"Found {len(progress_files)} progress files to analyze")

    for file_path in progress_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            processed_files += 1

            for record in data:
                if not isinstance(record, dict):
                    continue

                total_prompts += 1
                raw_prompt = record.get('raw_prompt', '')

                # Extract direct user commands
                direct_commands = extract_direct_user_commands(raw_prompt)

                # Extract all legitimate commands from the entire prompt
                all_commands = extract_legitimate_slash_commands(raw_prompt)

                # Process all found commands
                for command in set(direct_commands + all_commands):
                    # Clean up the command
                    cmd = command.strip()
                    if cmd.startswith('/'):
                        command_counter[cmd] += 1

                        # Store examples
                        if len(command_examples[cmd]) < 5:
                            # Try to get meaningful context
                            context = raw_prompt[:300] + "..." if len(raw_prompt) > 300 else raw_prompt
                            # Remove user-prompt-submit-hook wrapper if present
                            context = re.sub(r'<user-prompt-submit-hook>(.*?)</user-prompt-submit-hook>', r'\1', context, flags=re.DOTALL)
                            example = {
                                "prompt": context.strip(),
                                "prompt_id": record.get('prompt_id', 'unknown')
                            }
                            command_examples[cmd].append(example)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Prepare final results - only include commands with meaningful frequency
    result = {
        "agent_id": "002",
        "chunk_range": "995-1988",
        "total_prompts_analyzed": total_prompts,
        "files_processed": processed_files,
        "command_frequencies": {}
    }

    # Sort commands by frequency and filter for meaningful ones
    for command, count in command_counter.most_common():
        # Only include commands that appear multiple times or are known important commands
        if count >= 1:
            examples_list = []
            for example in command_examples[command][:5]:
                examples_list.append(example["prompt"])

            result["command_frequencies"][command] = {
                "count": count,
                "examples": examples_list
            }

    # Save results
    output_path = "/Users/jleechan/projects/worktree_genesis/roadmap/agent_002_command_frequency_refined.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nRefined analysis complete!")
    print(f"Total prompts analyzed: {total_prompts}")
    print(f"Files processed: {processed_files}")
    print(f"Legitimate slash commands found: {len(command_counter)}")
    print(f"Results saved to: {output_path}")

    # Print all commands found
    print("\nAll legitimate commands found:")
    for command, count in command_counter.most_common():
        print(f"  {command}: {count}")

if __name__ == "__main__":
    analyze_agent_002_refined()
