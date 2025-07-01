#!/usr/bin/env python3
"""
Show a summary of what the Sariel campaign integration test validates
"""
import json

# Load the prompts
with open('sariel_campaign_prompts.json', 'r') as f:
    data = json.load(f)

print("=== SARIEL CAMPAIGN INTEGRATION TEST SUMMARY ===")
print()
print(f"Total prompts to test: {data['total_prompts']}")
print()

# Show what fields would be checked
print("FIELDS VALIDATED PER INTERACTION:")
print()

print("1. Game State Top-Level Fields (7 fields):")
state_fields = [
    'game_state_version', 'player_character_data', 'world_data', 
    'npc_data', 'custom_campaign_state', 'combat_state', 
    'last_state_update_timestamp'
]
for field in state_fields:
    print(f"   - {field}")

print("\n2. Player Character Fields (up to 20+ fields):")
pc_fields = [
    'name', 'class', 'level', 'race', 'hp_current', 'hp_max',
    'stats (STR, DEX, CON, INT, WIS, CHA)', 'inventory', 'equipment', 
    'skills', 'spells', 'conditions', 'gold', 'experience', 'backstory'
]
for field in pc_fields:
    print(f"   - {field}")

print("\n3. NPC Fields (per NPC, up to 8+ fields each):")
npc_fields = [
    'name', 'hp_current', 'hp_max', 'location', 'status', 
    'relationship', 'faction', 'type'
]
for field in npc_fields:
    print(f"   - {field}")

print("\n4. Entity Tracking Fields (7 per interaction):")
tracking_fields = [
    'interaction number', 'player input', 'location',
    'expected entities', 'found entities', 'missing entities', 'success status'
]
for field in tracking_fields:
    print(f"   - {field}")

print("\n=== ESTIMATED TOTAL FIELDS ===")
print()

# Calculate estimates
interactions = 10
avg_npcs_per_interaction = 3
fields_per_npc = len(npc_fields)
pc_fields_count = 20  # Including nested stats
state_fields_count = len(state_fields)
tracking_fields_count = len(tracking_fields)

total_per_interaction = (
    state_fields_count +  # State validation
    pc_fields_count +     # Player character
    (avg_npcs_per_interaction * fields_per_npc) +  # NPCs
    tracking_fields_count  # Entity tracking
)

print(f"Per interaction: ~{total_per_interaction} fields")
print(f"Total across {interactions} interactions: ~{total_per_interaction * interactions} fields")
print()

print("KEY TEST SCENARIOS:")
print("1. Initial campaign setup - validates proper initialization")
print("2. The 'Cassian Problem' (interaction #2) - tests entity reference handling")
print("3. Location changes - validates entity presence based on context")
print("4. NPC interactions - ensures all mentioned NPCs are tracked")
print()

# Show the actual prompts being tested
print("PROMPTS BEING TESTED:")
for i, prompt in enumerate(data['prompts'][:5]):  # Show first 5
    print(f"\n[{i}] {prompt['prompt_id']} ({prompt['mode']} mode)")
    if len(prompt['input']) > 100:
        print(f"Input: {prompt['input'][:100]}...")
    else:
        print(f"Input: {prompt['input']}")
    if 'context' in prompt and 'location' in prompt['context']:
        print(f"Location: {prompt['context']['location']}")

print("\n... and 6 more interactions")
print()
print("This comprehensive test ensures the game state remains consistent")
print("and all entities are properly tracked throughout a real campaign.")