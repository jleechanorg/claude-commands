#!/usr/bin/env python3
"""
Comprehensive command frequency analysis for agent_001 data chunk (prompts 1-994)
"""
import json
import re
from collections import defaultdict
from pathlib import Path


def extract_slash_commands(text):
    """Extract actual slash commands from text, filtering out file paths"""
    # Pattern to match slash commands - starts with /, followed by word characters
    pattern = r'/[a-zA-Z][a-zA-Z0-9_-]*'
    all_matches = re.findall(pattern, text)

    # Filter out common file path patterns and system paths
    excluded_patterns = {
        # System paths
        '/Users', '/tmp', '/dev', '/null', '/api', '/src', '/lib', '/bin', '/etc',
        '/var', '/usr', '/opt', '/home', '/root', '/proc', '/sys', '/boot',
        # Common project paths
        '/projects', '/backend', '/frontend', '/tests', '/docs', '/scripts',
        '/config', '/utils', '/services', '/agents', '/models', '/tools',
        '/hooks', '/commands', '/github', '/mvp_site', '/site-packages',
        # URLs and web paths
        '/localhost', '/www', '/auth', '/oauth2', '/repos', '/pulls', '/issues',
        '/community', '/stackoverflow', '/questions', '/blog', '/favicon',
        # Version/build paths
        '/v1', '/v2', '/venv', '/python3', '/json',
        # Project specific paths that are clearly directories
        '/jleechan', '/jleechanorg', '/worktree_main2', '/worktree_worker5',
        '/ai_universe', '/project_ai_universe', '/projects_other', '/worldarchitect',
        '/firebase_admin', '/claude_llm_proxy', '/frontend_v2',
        # File extensions and formats
        '/MultiEdit', '/ConfigManager', '/SecondOpinionAgent', '/CostCalculator',
        '/RuntimeConfigService',
        # System hooks (not user commands)
        '/user-prompt-submit-hook'
    }

    # Additional filters for patterns that are clearly file paths
    def is_likely_command(cmd):
        # Skip if it's a known path pattern
        if cmd in excluded_patterns:
            return False

        # Skip if it looks like a file path (contains common path segments)
        path_indicators = ['_main', '_worker', '_v2', '_admin', '_proxy', 'Manager', 'Agent', 'Service', 'Calculator']
        if any(indicator in cmd for indicator in path_indicators):
            return False

        # Skip if it's all caps (likely constants or error codes)
        if cmd[1:].isupper() and len(cmd) > 3:
            return False

        # Skip single letters or very short commands that are likely paths
        if len(cmd) <= 2:
            return False

        return True

    # Filter to only actual commands
    commands = [cmd for cmd in all_matches if is_likely_command(cmd)]
    return commands

def analyze_agent_001_commands():
    """Analyze all progress files in agent_001 directory"""

    base_dir = Path("/Users/jleechan/projects/worktree_genesis/docs/genesis/processing/agent_001")

    # Dictionary to store command frequencies and examples
    command_data = defaultdict(lambda: {"count": 0, "examples": []})
    total_prompts = 0
    processed_files = 0

    # Process all progress files
    progress_files = sorted([f for f in base_dir.glob("progress_*.json")])

    print(f"Found {len(progress_files)} progress files to analyze...")

    for progress_file in progress_files:
        print(f"Processing {progress_file.name}...")

        try:
            with open(progress_file, encoding='utf-8') as f:
                data = json.load(f)

            processed_files += 1

            # Process each prompt in the file
            for prompt_obj in data:
                if isinstance(prompt_obj, dict) and 'raw_prompt' in prompt_obj:
                    total_prompts += 1
                    raw_prompt = prompt_obj['raw_prompt']

                    # Extract slash commands from this prompt
                    commands = extract_slash_commands(raw_prompt)

                    # Count each command and store examples
                    for cmd in commands:
                        command_data[cmd]["count"] += 1

                        # Store example if we don't have enough yet
                        if len(command_data[cmd]["examples"]) < 10:
                            # Store first 200 chars of prompt as example
                            example = raw_prompt[:200].replace('\n', ' ').replace('\r', ' ')
                            if example not in command_data[cmd]["examples"]:
                                command_data[cmd]["examples"].append(example)

        except Exception as e:
            print(f"Error processing {progress_file}: {e}")
            continue

    print(f"Processed {processed_files} files with {total_prompts} total prompts")

    # Convert defaultdict to regular dict for JSON serialization
    result = {
        "agent_id": "001",
        "chunk_range": "1-994",
        "total_prompts_analyzed": total_prompts,
        "files_processed": processed_files,
        "command_frequencies": {}
    }

    # Sort commands by frequency (highest first)
    sorted_commands = sorted(command_data.items(), key=lambda x: x[1]["count"], reverse=True)

    for cmd, data in sorted_commands:
        result["command_frequencies"][cmd] = {
            "count": data["count"],
            "examples": data["examples"][:5]  # Keep top 5 examples
        }

    print(f"\nFound {len(command_data)} unique slash commands:")
    for cmd, data in sorted_commands:
        print(f"  {cmd}: {data['count']} occurrences")

    return result

if __name__ == "__main__":
    results = analyze_agent_001_commands()

    # Create output directory if it doesn't exist
    output_dir = Path("/Users/jleechan/projects/worktree_genesis/roadmap")
    output_dir.mkdir(exist_ok=True)

    # Save results
    output_file = output_dir / "agent_001_command_frequency.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults saved to: {output_file}")
    print(f"Total commands found: {len(results['command_frequencies'])}")
