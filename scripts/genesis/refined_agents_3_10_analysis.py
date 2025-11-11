#!/usr/bin/env python3
"""
Refined Command Frequency Analysis for Agents 3-10
Enhanced filtering to remove filesystem artifacts and focus on genuine slash commands
"""

import json
import os
import re
from datetime import datetime


def is_genuine_slash_command(command):
    """
    Enhanced filtering to identify genuine slash commands vs filesystem artifacts
    """
    command = command.lower()

    # Definitive file system patterns to exclude
    filesystem_patterns = [
        r'^/dev',       # Device files
        r'^/tmp',       # Temporary files
        r'^/var',       # Variable files
        r'^/usr',       # User system resources
        r'^/etc',       # Configuration files
        r'^/opt',       # Optional software
        r'^/bin',       # Binary files
        r'^/lib',       # Library files
        r'^/home',      # Home directories
        r'^/users',     # User directories
        r'^/system',    # System directories
        r'^/volumes',   # Mounted volumes
        r'^/private',   # Private directories
        r'^/applications', # Applications
        r'^/library',   # Library directories
        r'^/mnt',       # Mount points
        r'^/proc',      # Process information
        r'^/sys',       # System information
        r'^/root',      # Root directory
        r'^/boot',      # Boot files
        r'^/run',       # Runtime files
        r'^/srv',       # Service data
        r'^/media',     # Media mount points
    ]

    # Check against filesystem patterns
    for pattern in filesystem_patterns:
        if re.match(pattern, command):
            return False

    # Exclude obvious file extensions and versioning
    exclusion_patterns = [
        r'/v\d+',       # Version numbers like /v1, /v2
        r'/\d+',        # Pure numbers
        r'^/[a-z]$',    # Single letters
        r'\.(py|js|md|json|txt|sh|yml|yaml|html|css|jsx|ts|tsx)$',  # File extensions
        r'/http',       # URL protocols
        r'/https',      # URL protocols
        r'/ftp',        # URL protocols
        r'/file',       # File protocol
        r'/path',       # Generic path references
        r'/url',        # URL references
        r'/api/v',      # API versioning
        r'/.*\.(.*)',   # Anything with file extensions
    ]

    for pattern in exclusion_patterns:
        if re.search(pattern, command):
            return False

    # Must be a reasonable command length
    if len(command) < 2 or len(command) > 20:
        return False

    # Must start with / and contain only valid command characters
    if not re.match(r'^/[a-z][a-z0-9_-]*$', command):
        return False

    # Whitelist of known valid commands (based on agents 1-2 analysis)
    known_valid_commands = {
        '/execute', '/copilot', '/reviewdeep', '/fixpr', '/consensus', '/commentreply',
        '/arch', '/guidelines', '/testllm', '/comments', '/commentfetch', '/cons',
        '/tdd', '/plan', '/commentcheck', '/pull', '/hooks', '/think', '/redgreen',
        '/design', '/debug', '/test', '/build', '/deploy', '/help', '/status',
        '/check', '/validate', '/analyze', '/review', '/merge', '/push', '/commit',
        '/branch', '/checkout', '/rebase', '/reset', '/log', '/diff', '/blame',
        '/research', '/cerebras', '/cereb', '/memory', '/context', '/checkpoint',
        '/header', '/pr', '/issue', '/milestone', '/project', '/team', '/user',
        '/config', '/settings', '/preferences', '/profile', '/account', '/login',
        '/logout', '/auth', '/token', '/key', '/secret', '/env', '/var'
    }

    # If it matches a known command, it's definitely valid
    if command in known_valid_commands:
        return True

    # Additional heuristics for unknown commands
    # Command should be meaningful English-like words
    valid_prefixes = ['/', '/get', '/set', '/create', '/delete', '/update', '/list',
                      '/show', '/hide', '/enable', '/disable', '/start', '/stop',
                      '/run', '/exec', '/call', '/invoke', '/trigger', '/fire']

    # Check if it starts with valid command prefixes
    for prefix in valid_prefixes:
        if command.startswith(prefix) and len(command) > len(prefix):
            return True

    # If we reach here, it's likely a genuine command but unknown
    # Allow it but flag for manual review
    return True

def process_combined_results():
    """
    Process the combined results from the initial analysis and apply refined filtering
    """
    combined_file = "/Users/jleechan/projects/worktree_genesis/roadmap/agents_3_10_combined_command_frequency.json"

    if not os.path.exists(combined_file):
        print("❌ Combined results file not found")
        return None

    with open(combined_file, encoding='utf-8') as f:
        data = json.load(f)

    print("Applying refined filtering to combined results...")

    original_commands = data['combined_command_frequencies']
    refined_commands = {}
    filtered_out = {}

    for command, count in original_commands.items():
        if is_genuine_slash_command(command):
            refined_commands[command] = count
        else:
            filtered_out[command] = count

    # Sort by frequency
    refined_sorted = sorted(refined_commands.items(), key=lambda x: x[1], reverse=True)

    refined_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_type': 'refined_filtering',
        'agents_processed': data['agents_processed'],
        'original_summary': data['summary_statistics'],
        'filtering_results': {
            'original_unique_commands': len(original_commands),
            'refined_unique_commands': len(refined_commands),
            'commands_filtered_out': len(filtered_out),
            'filtering_efficiency': f"{(len(filtered_out) / len(original_commands)) * 100:.1f}%"
        },
        'refined_command_frequencies': refined_commands,
        'top_commands_refined': refined_sorted[:30],
        'filtered_out_commands': dict(sorted(filtered_out.items(), key=lambda x: x[1], reverse=True)[:20]),
        'command_categories': categorize_commands(refined_commands),
    }

    return refined_analysis

def categorize_commands(commands):
    """
    Categorize commands by their likely purpose
    """
    categories = {
        'execution': ['execute', 'run', 'exec', 'call', 'invoke', 'trigger'],
        'collaboration': ['copilot', 'consensus', 'commentreply', 'comments', 'commentfetch', 'commentcheck'],
        'development': ['tdd', 'redgreen', 'test', 'build', 'debug', 'analyze'],
        'git_workflow': ['fixpr', 'pull', 'push', 'commit', 'branch', 'merge', 'rebase'],
        'architecture': ['arch', 'design', 'plan', 'review', 'reviewdeep'],
        'research': ['research', 'testllm', 'cerebras', 'cereb'],
        'project_management': ['guidelines', 'hooks', 'think', 'status', 'check'],
        'system': ['config', 'settings', 'env', 'memory', 'context', 'checkpoint']
    }

    categorized = {cat: {} for cat in categories}
    categorized['uncategorized'] = {}

    for command, count in commands.items():
        command_name = command.lstrip('/')
        categorized_flag = False

        for category, keywords in categories.items():
            if any(keyword in command_name.lower() for keyword in keywords):
                categorized[category][command] = count
                categorized_flag = True
                break

        if not categorized_flag:
            categorized['uncategorized'][command] = count

    # Sort each category by frequency
    for category in categorized:
        categorized[category] = dict(sorted(categorized[category].items(), key=lambda x: x[1], reverse=True))

    return categorized

def main():
    """
    Main execution for refined analysis
    """
    print("=== REFINED COMMAND FREQUENCY ANALYSIS ===")
    print("Processing agents 3-10 with enhanced filtering...")

    refined_results = process_combined_results()

    if refined_results:
        # Save refined results
        output_file = "/Users/jleechan/projects/worktree_genesis/roadmap/agents_3_10_refined_command_frequency.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(refined_results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Refined analysis complete: {output_file}")

        # Display key results
        print("\n📊 FILTERING RESULTS:")
        print(f"   Original commands: {refined_results['filtering_results']['original_unique_commands']}")
        print(f"   Refined commands: {refined_results['filtering_results']['refined_unique_commands']}")
        print(f"   Filtered out: {refined_results['filtering_results']['commands_filtered_out']}")
        print(f"   Filtering efficiency: {refined_results['filtering_results']['filtering_efficiency']}")

        print("\n🏆 TOP 15 REFINED COMMANDS:")
        for i, (command, count) in enumerate(refined_results['top_commands_refined'][:15], 1):
            print(f"   {i:2d}. {command}: {count} occurrences")

        print("\n🗑️  TOP 10 FILTERED OUT (FILESYSTEM ARTIFACTS):")
        for i, (command, count) in enumerate(list(refined_results['filtered_out_commands'].items())[:10], 1):
            print(f"   {i:2d}. {command}: {count} occurrences")

        print("\n📂 COMMAND CATEGORIES:")
        for category, commands in refined_results['command_categories'].items():
            if commands:
                total_in_category = sum(commands.values())
                print(f"   {category.upper()}: {len(commands)} commands, {total_in_category} total occurrences")
                top_3 = list(commands.items())[:3]
                for cmd, count in top_3:
                    print(f"      {cmd}: {count}")

        return refined_results

    print("❌ Refined analysis failed")
    return None

if __name__ == "__main__":
    main()
