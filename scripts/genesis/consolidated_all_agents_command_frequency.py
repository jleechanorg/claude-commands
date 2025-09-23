#!/usr/bin/env python3
"""
Consolidated Command Frequency Analysis Across All 10 Agents
Combines results from agents 1-2 (refined) and agents 3-10 (refined) for complete dataset analysis
"""

import json
import os
from collections import defaultdict, Counter
from datetime import datetime

def load_agent_data():
    """
    Load data from all processed agents
    """
    roadmap_dir = "/Users/jleechan/projects/worktree_genesis/roadmap"

    # Load agents 1-2 refined data
    agent_001_file = os.path.join(roadmap_dir, "agent_001_command_frequency_refined.json")
    agent_002_file = os.path.join(roadmap_dir, "agent_002_command_frequency_refined.json")
    agents_3_10_file = os.path.join(roadmap_dir, "agents_3_10_refined_command_frequency.json")

    agents_data = {}

    # Load agent 1
    if os.path.exists(agent_001_file):
        with open(agent_001_file, 'r', encoding='utf-8') as f:
            agent_001_data = json.load(f)
            # Handle agent 1 structure: command_frequencies[cmd]['count']
            commands_dict = {}
            for cmd, data in agent_001_data['command_frequencies'].items():
                if isinstance(data, dict) and 'count' in data:
                    commands_dict[cmd] = data['count']
                else:
                    commands_dict[cmd] = data

            agents_data['agent_001'] = {
                'prompts': agent_001_data['total_prompts_analyzed'],
                'commands': commands_dict
            }

    # Load agent 2
    if os.path.exists(agent_002_file):
        with open(agent_002_file, 'r', encoding='utf-8') as f:
            agent_002_data = json.load(f)
            # Handle agent 2 structure: command_frequencies[cmd]['count']
            commands_dict = {}
            for cmd, data in agent_002_data['command_frequencies'].items():
                if isinstance(data, dict) and 'count' in data:
                    commands_dict[cmd] = data['count']
                else:
                    commands_dict[cmd] = data

            agents_data['agent_002'] = {
                'prompts': agent_002_data['total_prompts_analyzed'],
                'commands': commands_dict
            }

    # Load agents 3-10 combined
    if os.path.exists(agents_3_10_file):
        with open(agents_3_10_file, 'r', encoding='utf-8') as f:
            agents_3_10_data = json.load(f)
            agents_data['agents_3_10'] = {
                'prompts': agents_3_10_data['original_summary']['total_prompts_analyzed'],
                'commands': agents_3_10_data['refined_command_frequencies']
            }

    return agents_data

def consolidate_all_agents():
    """
    Create consolidated analysis across all agents
    """
    print("=== CONSOLIDATED COMMAND FREQUENCY ANALYSIS ===")
    print("Loading data from all 10 agents...")

    agents_data = load_agent_data()

    if not agents_data:
        print("❌ No agent data found")
        return None

    # Consolidate command frequencies
    consolidated_commands = Counter()
    total_prompts = 0
    agent_summaries = {}

    for agent_id, data in agents_data.items():
        total_prompts += data['prompts']
        agent_summaries[agent_id] = {
            'prompts': data['prompts'],
            'unique_commands': len(data['commands']),
            'total_command_occurrences': sum(data['commands'].values())
        }

        for command, count in data['commands'].items():
            consolidated_commands[command] += count

    # Create comprehensive analysis
    consolidated_analysis = {
        'analysis_timestamp': datetime.now().isoformat(),
        'analysis_scope': 'all_agents_1_to_10',
        'dataset_info': {
            'total_prompts_analyzed': total_prompts,
            'expected_total_prompts': 9936,
            'coverage_percentage': f"{(total_prompts / 9936) * 100:.1f}%",
            'agents_processed': list(agents_data.keys())
        },
        'agent_summaries': agent_summaries,
        'consolidated_command_frequencies': dict(consolidated_commands),
        'top_commands_overall': consolidated_commands.most_common(50),
        'summary_statistics': {
            'unique_commands_total': len(consolidated_commands),
            'total_command_occurrences': sum(consolidated_commands.values()),
            'average_commands_per_prompt': f"{sum(consolidated_commands.values()) / total_prompts:.2f}",
            'command_usage_percentage': f"{(sum(consolidated_commands.values()) / total_prompts) * 100:.1f}%"
        },
        'command_tier_analysis': analyze_command_tiers(consolidated_commands),
        'comparison_with_priorities': compare_with_priorities(consolidated_commands)
    }

    return consolidated_analysis

def analyze_command_tiers(commands):
    """
    Analyze commands by usage tiers
    """
    sorted_commands = commands.most_common()
    total_occurrences = sum(commands.values())

    tiers = {
        'tier_1_heavy_use': [],     # >100 occurrences
        'tier_2_frequent_use': [],  # 50-100 occurrences
        'tier_3_moderate_use': [],  # 20-49 occurrences
        'tier_4_light_use': [],     # 5-19 occurrences
        'tier_5_rare_use': []       # 1-4 occurrences
    }

    for command, count in sorted_commands:
        percentage = (count / total_occurrences) * 100

        if count >= 100:
            tiers['tier_1_heavy_use'].append((command, count, f"{percentage:.1f}%"))
        elif count >= 50:
            tiers['tier_2_frequent_use'].append((command, count, f"{percentage:.1f}%"))
        elif count >= 20:
            tiers['tier_3_moderate_use'].append((command, count, f"{percentage:.1f}%"))
        elif count >= 5:
            tiers['tier_4_light_use'].append((command, count, f"{percentage:.1f}%"))
        else:
            tiers['tier_5_rare_use'].append((command, count, f"{percentage:.1f}%"))

    return tiers

def compare_with_priorities(commands):
    """
    Compare findings with priority commands identified in user request
    """
    priority_commands = [
        '/execute', '/copilot', '/reviewdeep', '/fixpr', '/consensus', '/commentreply',
        '/arch', '/guidelines', '/testllm', '/comments', '/commentfetch', '/cons',
        '/tdd', '/plan', '/commentcheck', '/pull', '/hooks', '/think', '/redgreen'
    ]

    found_priorities = {}
    missing_priorities = []

    for priority in priority_commands:
        if priority in commands:
            found_priorities[priority] = commands[priority]
        else:
            missing_priorities.append(priority)

    return {
        'priority_commands_analyzed': priority_commands,
        'found_in_dataset': found_priorities,
        'missing_from_dataset': missing_priorities,
        'priority_command_rankings': [(cmd, commands[cmd]) for cmd in priority_commands if cmd in commands]
    }

def main():
    """
    Execute consolidated analysis
    """
    consolidated_results = consolidate_all_agents()

    if consolidated_results:
        # Save consolidated results
        output_file = "/Users/jleechan/projects/worktree_genesis/roadmap/consolidated_all_agents_command_frequency.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(consolidated_results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Consolidated analysis complete: {output_file}")

        # Display key results
        dataset_info = consolidated_results['dataset_info']
        print(f"\n📊 DATASET OVERVIEW:")
        print(f"   Total prompts analyzed: {dataset_info['total_prompts_analyzed']:,}")
        print(f"   Expected total prompts: {dataset_info['expected_total_prompts']:,}")
        print(f"   Dataset coverage: {dataset_info['coverage_percentage']}")

        stats = consolidated_results['summary_statistics']
        print(f"\n📈 COMMAND STATISTICS:")
        print(f"   Unique commands found: {stats['unique_commands_total']}")
        print(f"   Total command occurrences: {stats['total_command_occurrences']:,}")
        print(f"   Average commands per prompt: {stats['average_commands_per_prompt']}")
        print(f"   Command usage percentage: {stats['command_usage_percentage']}")

        print(f"\n🏆 TOP 20 COMMANDS ACROSS ALL 9,936 PROMPTS:")
        for i, (command, count) in enumerate(consolidated_results['top_commands_overall'][:20], 1):
            percentage = (count / int(stats['total_command_occurrences'])) * 100
            print(f"   {i:2d}. {command}: {count:,} occurrences ({percentage:.1f}%)")

        print(f"\n🎯 PRIORITY COMMAND ANALYSIS:")
        priority_data = consolidated_results['comparison_with_priorities']
        found_priorities = sorted(priority_data['found_in_dataset'].items(), key=lambda x: x[1], reverse=True)
        print(f"   Found {len(found_priorities)} of {len(priority_data['priority_commands_analyzed'])} priority commands")
        for command, count in found_priorities[:10]:
            percentage = (count / int(stats['total_command_occurrences'])) * 100
            print(f"   {command}: {count:,} occurrences ({percentage:.1f}%)")

        print(f"\n📊 USAGE TIER ANALYSIS:")
        tiers = consolidated_results['command_tier_analysis']
        for tier_name, tier_commands in tiers.items():
            if tier_commands:
                print(f"   {tier_name.upper().replace('_', ' ')}: {len(tier_commands)} commands")
                for command, count, percentage in tier_commands[:3]:  # Show top 3 in each tier
                    print(f"      {command}: {count:,} ({percentage})")

        return consolidated_results

    else:
        print("❌ Consolidated analysis failed")
        return None

if __name__ == "__main__":
    main()
