#!/usr/bin/env python3
"""
Command frequency analysis for agent_002 conversation data chunk.
Extracts slash commands from user prompts and counts their frequencies.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path


def extract_slash_commands(text):
    """Extract slash commands from text, filtering out file paths and URLs."""
    # Known slash commands to focus on
    known_commands = {
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
        'clean', 'config', 'help', 'version', 'info', 'show', 'describe'
    }

    # Pattern to match slash commands that start with / followed by alphanumeric characters
    slash_pattern = r'/([a-zA-Z][a-zA-Z0-9_-]*)'

    # Find all potential slash commands
    matches = re.findall(slash_pattern, text)

    # Filter out common false positives
    false_positives = {
        'Users', 'home', 'tmp', 'var', 'etc', 'usr', 'bin', 'lib', 'opt', 'srv',
        'dev', 'proc', 'sys', 'boot', 'root', 'mnt', 'media', 'run', 'snap',
        'Applications', 'Library', 'System', 'volumes', 'private', 'Network',
        'projects', 'src', 'app', 'api', 'web', 'docs', 'test', 'tests',
        'config', 'configs', 'data', 'logs', 'cache', 'temp', 'backup',
        'node_modules', 'dist', 'build', 'target', 'out', 'output',
        'http', 'https', 'ftp', 'ftps', 'ssh', 'git', 'svn', 'hg',
        'py', 'js', 'ts', 'html', 'css', 'json', 'xml', 'yaml', 'yml',
        'md', 'txt', 'log', 'csv', 'pdf', 'zip', 'tar', 'gz', 'bz2',
        'user', 'worldarchitect', 'main', 'mvp_site', 'null', 'ai', 'claude',
        'github', 'repo', 'branch', 'commit', 'pull', 'merge', 'fix',
        'feature', 'bugfix', 'hotfix', 'release', 'version', 'stable',
        'prod', 'production', 'staging', 'development', 'local', 'remote'
    }

    # Extract valid slash commands
    valid_commands = []
    for match in matches:
        # Skip if it's a known false positive
        if match.lower() in false_positives:
            continue

        # Skip if it contains common file extensions or path separators
        if any(ext in match.lower() for ext in ['.', '_test', '_spec', 'test_', 'spec_']):
            continue

        # Skip if it's too long (likely a path)
        if len(match) > 20:
            continue

        # Prioritize known commands but also include others that look like commands
        command = f"/{match}"
        if match.lower() in known_commands or len(match) <= 15:
            valid_commands.append(command)

    return valid_commands

def extract_user_prompts(raw_prompt):
    """Extract lines that start with '>' which indicate user prompts."""
    lines = raw_prompt.split('\n')
    user_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith('>'):
            # Remove the '>' prefix and any additional whitespace
            user_content = stripped[1:].strip()
            if user_content:  # Only add non-empty lines
                user_lines.append(user_content)

    return user_lines

def analyze_agent_002():
    """Analyze agent_002 directory for slash command frequencies."""

    agent_dir = Path("/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/agent_002")

    if not agent_dir.exists():
        print(f"Directory not found: {agent_dir}")
        return

    command_counter = Counter()
    command_examples = defaultdict(list)
    total_prompts = 0
    processed_files = 0

    # Process all progress files
    progress_files = sorted([f for f in agent_dir.glob("progress_*.json")])

    print(f"Found {len(progress_files)} progress files to analyze")

    for file_path in progress_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                data = json.load(f)

            processed_files += 1

            # Each file contains a list of prompt records
            for record in data:
                if not isinstance(record, dict):
                    continue

                total_prompts += 1
                raw_prompt = record.get('raw_prompt', '')

                # Extract user prompts (lines starting with '>')
                user_prompts = extract_user_prompts(raw_prompt)

                # If no user prompts found with '>', check the entire raw_prompt
                # for slash commands as it might be a direct user input
                if not user_prompts:
                    # Check if this looks like a direct user command
                    if raw_prompt.strip().startswith('/'):
                        user_prompts = [raw_prompt.strip()]
                    else:
                        # Also extract from the raw prompt directly for any slash commands
                        user_prompts = [raw_prompt]

                # Also check command_history in context_analysis if available
                context_analysis = record.get('context_analysis', {})
                technical_context = context_analysis.get('technical_context', {})
                command_history = technical_context.get('command_history', [])

                # Add command history as additional user prompts
                for cmd in command_history:
                    if isinstance(cmd, str) and cmd.startswith('/'):
                        user_prompts.append(cmd)

                # Extract slash commands from user prompts
                for user_prompt in user_prompts:
                    commands = extract_slash_commands(user_prompt)

                    for command in commands:
                        command_counter[command] += 1

                        # Store examples (limit to avoid memory issues)
                        if len(command_examples[command]) < 10:
                            # Store the full user prompt as context
                            example = {
                                "prompt": user_prompt[:200] + "..." if len(user_prompt) > 200 else user_prompt,
                                "prompt_id": record.get('prompt_id', 'unknown')
                            }
                            command_examples[command].append(example)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Prepare final results
    result = {
        "agent_id": "002",
        "chunk_range": "995-1988",
        "total_prompts_analyzed": total_prompts,
        "files_processed": processed_files,
        "command_frequencies": {}
    }

    # Sort commands by frequency (most common first)
    for command, count in command_counter.most_common():
        examples_list = []
        for example in command_examples[command][:5]:  # Limit to 5 examples
            examples_list.append(example["prompt"])

        result["command_frequencies"][command] = {
            "count": count,
            "examples": examples_list
        }

    # Save results
    output_path = "/Users/jleechan/projects/worktree_genesis/roadmap/agent_002_command_frequency.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\nAnalysis complete!")
    print(f"Total prompts analyzed: {total_prompts}")
    print(f"Files processed: {processed_files}")
    print(f"Unique slash commands found: {len(command_counter)}")
    print(f"Results saved to: {output_path}")

    # Print top commands for preview
    print("\nTop 10 most frequent commands:")
    for command, count in command_counter.most_common(10):
        print(f"  {command}: {count}")

if __name__ == "__main__":
    analyze_agent_002()
