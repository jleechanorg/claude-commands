#!/usr/bin/env python3
"""
Collect narrative samples from WorldArchitect.AI for desync analysis.

This script simulates narrative generation scenarios to collect samples
where desynchronization errors might occur, particularly focusing on:
- Party member presence tracking
- Character state consistency
- Location-based entity manifests
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any
import random

# Add parent directory to path to import game modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_sample_game_state() -> Dict[str, Any]:
    """Create a sample game state with multiple party members."""
    return {
        "game_id": f"sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "player_character": {
            "id": "gideon_001",
            "name": "Gideon",
            "hp": 45,
            "max_hp": 50,
            "status": ["conscious", "armed"]
        },
        "party_members": [
            {
                "id": "rowan_001",
                "name": "Rowan",
                "hp": 30,
                "max_hp": 35,
                "status": ["conscious", "healing"]
            },
            {
                "id": "kira_001", 
                "name": "Kira",
                "hp": 25,
                "max_hp": 40,
                "status": ["conscious", "scouting"]
            }
        ],
        "current_location": "Forest Clearing",
        "timestamp": datetime.now().isoformat()
    }

def create_desync_scenarios() -> List[Dict[str, Any]]:
    """Create various scenarios that might cause desync."""
    scenarios = []
    
    # Scenario 1: Party member temporarily absent
    state1 = create_sample_game_state()
    state1["party_members"][0]["status"].append("hidden")
    scenarios.append({
        "name": "Hidden Party Member",
        "description": "Rowan is hidden but should still be tracked",
        "game_state": state1,
        "expected_entities": ["Gideon", "Rowan", "Kira"],
        "common_error": "Hidden character omitted from narrative"
    })
    
    # Scenario 2: Unconscious party member
    state2 = create_sample_game_state()
    state2["party_members"][1]["status"] = ["unconscious"]
    state2["party_members"][1]["hp"] = 0
    scenarios.append({
        "name": "Unconscious Party Member",
        "description": "Kira is unconscious and should be mentioned",
        "game_state": state2,
        "expected_entities": ["Gideon", "Rowan", "Kira"],
        "common_error": "Unconscious character ignored in scene description"
    })
    
    # Scenario 3: Combat with multiple NPCs
    state3 = create_sample_game_state()
    state3["combat_state"] = {
        "active": True,
        "enemies": [
            {"id": "bandit_001", "name": "Bandit Leader", "hp": 20},
            {"id": "bandit_002", "name": "Bandit Archer", "hp": 15}
        ]
    }
    scenarios.append({
        "name": "Combat Scene",
        "description": "Combat with enemies and all party members",
        "game_state": state3,
        "expected_entities": ["Gideon", "Rowan", "Kira", "Bandit Leader", "Bandit Archer"],
        "common_error": "Missing combatants in action descriptions"
    })
    
    # Scenario 4: Location transition
    state4 = create_sample_game_state()
    state4["previous_location"] = "Village Inn"
    state4["current_location"] = "Forest Path"
    state4["transition_context"] = "The party left the inn at dawn"
    scenarios.append({
        "name": "Location Transition",
        "description": "Party moving between locations",
        "game_state": state4,
        "expected_entities": ["Gideon", "Rowan", "Kira"],
        "common_error": "Party members lost during location transitions"
    })
    
    # Scenario 5: Split party
    state5 = create_sample_game_state()
    state5["party_members"][0]["current_location"] = "Village Market"
    state5["party_members"][0]["status"].append("shopping")
    scenarios.append({
        "name": "Split Party",
        "description": "Rowan is at a different location",
        "game_state": state5,
        "expected_entities": ["Gideon", "Kira"],  # Rowan should NOT be in main scene
        "expected_absent": ["Rowan"],
        "common_error": "Including absent party members in scene"
    })
    
    return scenarios

def simulate_narrative_generation(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate what a narrative generation might produce."""
    # This simulates various types of narrative outputs that might occur
    narrative_variations = [
        # Correct narrative mentioning all entities
        lambda s: f"In the {s['game_state']['current_location']}, " + 
                  " stands ready while ".join([e for e in s['expected_entities']]) + 
                  " prepare for what's ahead.",
        
        # Missing entity narrative (simulated error)
        lambda s: f"In the {s['game_state']['current_location']}, " +
                  f"{s['expected_entities'][0]} surveys the area.",
        
        # Partial mention narrative
        lambda s: f"{s['expected_entities'][0]} and {s['expected_entities'][1]} " +
                  f"move through the {s['game_state']['current_location']}.",
        
        # Incorrect entity state narrative
        lambda s: (f"Everyone is alert and ready in the {s['game_state']['current_location']}."
                  if 'unconscious' in str(s['game_state']) else
                  f"The party gathers in the {s['game_state']['current_location']}.")
    ]
    
    # Randomly select a narrative style to simulate various outputs
    narrative = random.choice(narrative_variations)(scenario)
    
    # Check which entities were mentioned
    mentioned_entities = []
    for entity in scenario["expected_entities"]:
        if entity.lower() in narrative.lower():
            mentioned_entities.append(entity)
    
    missing_entities = [e for e in scenario["expected_entities"] if e not in mentioned_entities]
    
    return {
        "scenario_name": scenario["name"],
        "narrative": narrative,
        "mentioned_entities": mentioned_entities,
        "missing_entities": missing_entities,
        "desync_detected": len(missing_entities) > 0,
        "timestamp": datetime.now().isoformat()
    }

def collect_samples(num_samples: int = 100) -> List[Dict[str, Any]]:
    """Collect narrative samples with various desync scenarios."""
    scenarios = create_desync_scenarios()
    samples = []
    
    for i in range(num_samples):
        # Rotate through scenarios
        scenario = scenarios[i % len(scenarios)]
        
        # Generate a narrative sample
        sample = simulate_narrative_generation(scenario)
        sample["sample_id"] = f"sample_{i:04d}"
        sample["scenario_data"] = scenario
        
        samples.append(sample)
    
    return samples

def save_samples(samples: List[Dict[str, Any]], output_dir: str = "data"):
    """Save collected samples to JSON file."""
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"narrative_samples_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Create summary statistics
    total_samples = len(samples)
    desync_count = sum(1 for s in samples if s["desync_detected"])
    desync_rate = (desync_count / total_samples) * 100 if total_samples > 0 else 0
    
    output_data = {
        "metadata": {
            "collection_date": datetime.now().isoformat(),
            "total_samples": total_samples,
            "desync_count": desync_count,
            "desync_rate": f"{desync_rate:.2f}%",
            "scenarios": list(set(s["scenario_name"] for s in samples))
        },
        "samples": samples
    }
    
    with open(filepath, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Collected {total_samples} narrative samples")
    print(f"Desync rate: {desync_rate:.2f}%")
    print(f"Saved to: {filepath}")
    
    # Also create a simplified CSV for quick analysis
    csv_filepath = filepath.replace('.json', '_summary.csv')
    with open(csv_filepath, 'w') as f:
        f.write("sample_id,scenario,desync_detected,missing_count,entities_expected,entities_found\n")
        for s in samples:
            f.write(f"{s['sample_id']},{s['scenario_name']},{s['desync_detected']},"
                   f"{len(s['missing_entities'])},{len(s['scenario_data']['expected_entities'])},"
                   f"{len(s['mentioned_entities'])}\n")
    
    print(f"Summary saved to: {csv_filepath}")

def main():
    """Main execution function."""
    print("WorldArchitect.AI Narrative Sample Collector")
    print("=" * 50)
    
    # Collect samples
    samples = collect_samples(num_samples=100)
    
    # Save samples
    save_samples(samples)
    
    # Print analysis preview
    print("\nSample Analysis Preview:")
    print("-" * 30)
    
    scenario_stats = {}
    for sample in samples:
        scenario = sample["scenario_name"]
        if scenario not in scenario_stats:
            scenario_stats[scenario] = {"total": 0, "desync": 0}
        scenario_stats[scenario]["total"] += 1
        if sample["desync_detected"]:
            scenario_stats[scenario]["desync"] += 1
    
    for scenario, stats in scenario_stats.items():
        rate = (stats["desync"] / stats["total"]) * 100
        print(f"{scenario}: {rate:.1f}% desync rate ({stats['desync']}/{stats['total']})")

if __name__ == "__main__":
    main()