#!/usr/bin/env python3
"""
Comprehensive Command Frequency Analysis for Agents 3-10
Processes conversation data to extract and analyze slash commands
"""

import json
import os
import re
import glob
from collections import defaultdict, Counter
from datetime import datetime

def is_valid_slash_command(text):
    """
    Determine if a slash command is a valid command vs file path or other artifact
    """
    # Skip obvious file paths
    if text.count('/') > 2:  # Multiple slashes indicate file paths
        return False

    # Skip common file extensions
    if any(text.lower().endswith(ext) for ext in ['.py', '.js', '.md', '.json', '.txt', '.sh', '.yml', '.yaml']):
        return False

    # Skip paths starting with common directories
    if any(text.lower().startswith(path) for path in ['/users/', '/home/', '/var/', '/tmp/', '/usr/', '/etc/', '/opt/']):
        return False

    # Skip version strings and URLs
    if re.match(r'/(v\d+|http)', text.lower()):
        return False

    # Valid commands are typically short single words after /
    command_part = text.split()[0] if text.split() else text
    if len(command_part) > 20:  # Too long to be a command
        return False

    # Must start with / and have alphanumeric characters
    if not re.match(r'^/[a-zA-Z][a-zA-Z0-9_-]*', command_part):
        return False

    return True

def extract_slash_commands(raw_prompt):
    """
    Extract slash commands from a raw prompt string
    """
    if not raw_prompt or not isinstance(raw_prompt, str):
        return []

    commands = []

    # Look for patterns that start with / and are followed by word characters
    # This pattern captures /command with optional arguments
    pattern = r'(?:^|[\s>])/([a-zA-Z][a-zA-Z0-9_-]*)'

    matches = re.findall(pattern, raw_prompt)

    for match in matches:
        full_command = f"/{match}"
        if is_valid_slash_command(full_command):
            commands.append(full_command)

    return commands

def process_agent_directory(agent_dir):
    """
    Process all progress files in an agent directory
    """
    agent_id = os.path.basename(agent_dir)
    print(f"Processing {agent_id}...")

    command_counts = Counter()
    command_examples = defaultdict(list)
    total_prompts = 0
    processed_files = 0

    # Find all progress files
    progress_files = glob.glob(os.path.join(agent_dir, "progress_*.json"))
    progress_files.sort()

    for progress_file in progress_files:
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            processed_files += 1

            if 'prompts' in data:
                for prompt_data in data['prompts']:
                    total_prompts += 1
                    raw_prompt = prompt_data.get('raw_prompt', '')

                    # Extract commands from this prompt
                    commands = extract_slash_commands(raw_prompt)

                    for command in commands:
                        command_counts[command] += 1

                        # Store example (limit to avoid memory issues)
                        if len(command_examples[command]) < 10:
                            # Clean the example for storage
                            clean_prompt = raw_prompt.replace('\n', ' ').strip()
                            if len(clean_prompt) > 200:
                                clean_prompt = clean_prompt[:200] + "..."

                            command_examples[command].append({
                                'prompt_id': prompt_data.get('prompt_id', 'unknown'),
                                'raw_prompt': clean_prompt,
                                'timestamp': prompt_data.get('timestamp', 'unknown')
                            })

        except Exception as e:
            print(f"Error processing {progress_file}: {e}")
            continue

    return {
        'agent_id': agent_id,
        'total_prompts': total_prompts,
        'processed_files': processed_files,
        'command_frequencies': dict(command_counts),
        'command_examples': dict(command_examples),
        'top_commands': command_counts.most_common(20)
    }

def main():
    """
    Main execution function for processing agents 3-10
    """
    base_dir = "/Users/jleechan/projects/worktree_genesis/docs/genesis/processing"
    output_dir = "/Users/jleechan/projects/worktree_genesis/roadmap"

    # Process agents 3-10
    agents_to_process = [f"agent_{i:03d}" for i in range(3, 11)]

    all_results = {}
    combined_command_counts = Counter()
    combined_examples = defaultdict(list)

    print("Starting comprehensive command frequency analysis...")
    print(f"Processing agents: {', '.join(agents_to_process)}")

    for agent_id in agents_to_process:
        agent_dir = os.path.join(base_dir, agent_id)

        if os.path.exists(agent_dir):
            result = process_agent_directory(agent_dir)
            all_results[agent_id] = result

            # Add to combined results
            for command, count in result['command_frequencies'].items():
                combined_command_counts[command] += count

            for command, examples in result['command_examples'].items():
                combined_examples[command].extend(examples[:3])  # Limit examples

            # Save individual agent result
            output_file = os.path.join(output_dir, f"{agent_id}_command_frequency.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"✅ {agent_id}: {result['total_prompts']} prompts, {len(result['command_frequencies'])} unique commands")

        else:
            print(f"❌ {agent_id}: Directory not found at {agent_dir}")

    # Create combined analysis
    combined_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'agents_processed': list(agents_to_process),
        'total_agents': len(agents_to_process),
        'combined_command_frequencies': dict(combined_command_counts),
        'top_commands_overall': combined_command_counts.most_common(30),
        'combined_examples': dict(combined_examples),
        'summary_statistics': {
            'total_prompts_analyzed': sum(r['total_prompts'] for r in all_results.values()),
            'unique_commands_found': len(combined_command_counts),
            'total_command_occurrences': sum(combined_command_counts.values())
        }
    }

    # Save combined analysis
    combined_output_file = os.path.join(output_dir, "agents_3_10_combined_command_frequency.json")
    with open(combined_output_file, 'w', encoding='utf-8') as f:
        json.dump(combined_analysis, f, indent=2, ensure_ascii=False)

    print("\n=== ANALYSIS COMPLETE ===")
    print(f"Processed {len(all_results)} agents successfully")
    print(f"Total prompts analyzed: {combined_analysis['summary_statistics']['total_prompts_analyzed']}")
    print(f"Unique commands found: {combined_analysis['summary_statistics']['unique_commands_found']}")
    print(f"Total command occurrences: {combined_analysis['summary_statistics']['total_command_occurrences']}")

    print("\nTop 15 commands across agents 3-10:")
    for i, (command, count) in enumerate(combined_command_counts.most_common(15), 1):
        print(f"{i:2d}. {command}: {count} occurrences")

    return combined_analysis

if __name__ == "__main__":
    main()
