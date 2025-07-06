#!/usr/bin/env python3
"""
Direct test of the combat bug - simulate the exact error condition
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

from game_state import GameState, StateHelper

def test_combat_bug_scenario():
    """Test the exact scenario that causes the AttributeError"""
    
    print("="*70)
    print("🐛 TESTING COMBAT BUG DIRECTLY")
    print("="*70)
    
    # Scenario 1: NPCs as a list (incorrect)
    print("\nScenario 1: Testing with NPCs as a LIST (bug scenario)")
    
    state_dict = {
        'version': 1,
        'entities': {
            'NPCs': ['Dragon', 'Goblin']  # This is a LIST!
        },
        'narrative': {
            'current_scene': 'A warrior faces enemies'
        }
    }
    
    print(f"Initial state: {state_dict}")
    
    # Try to process this state
    try:
        # This is likely where the bug occurs
        game_state = GameState.from_dict(state_dict)
        print("✅ GameState.from_dict() succeeded")
        
        # Try to access NPCs
        npcs = game_state.entities.get('NPCs', {})
        print(f"NPCs type: {type(npcs)}")
        
        # Try to iterate like a dict (this will fail if it's a list)
        if hasattr(npcs, 'items'):
            print("✅ NPCs has .items() method")
            for npc_id, npc_data in npcs.items():
                print(f"  NPC: {npc_id} = {npc_data}")
        else:
            print("❌ NPCs does NOT have .items() method!")
            print(f"❌ NPCs is a {type(npcs).__name__}, not a dict!")
            
            # This is likely the bug!
            try:
                # This will cause AttributeError
                for key, value in npcs.items():
                    pass
            except AttributeError as e:
                print(f"\n🐛 COMBAT BUG REPRODUCED!")
                print(f"❌ AttributeError: {e}")
                print("This confirms PR #314's finding!")
                
    except Exception as e:
        print(f"❌ Error during state processing: {e}")
        import traceback
        traceback.print_exc()
    
    # Scenario 2: NPCs as a dict (correct)
    print("\n" + "-"*50)
    print("\nScenario 2: Testing with NPCs as a DICT (correct)")
    
    correct_state = {
        'version': 1,
        'entities': {
            'NPCs': {  # This is a DICT!
                'dragon_001': {'name': 'Dragon', 'HP': 100},
                'goblin_001': {'name': 'Goblin', 'HP': 20}
            }
        },
        'narrative': {
            'current_scene': 'A warrior faces enemies'
        }
    }
    
    try:
        game_state = GameState.from_dict(correct_state)
        npcs = game_state.entities.get('NPCs', {})
        
        if hasattr(npcs, 'items'):
            print("✅ NPCs has .items() method")
            for npc_id, npc_data in npcs.items():
                print(f"  ✅ NPC: {npc_id} = {npc_data}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Check where this might happen in combat
    print("\n" + "-"*50)
    print("\nLikely bug location:")
    print("When AI returns NPCs as a list instead of dict in state updates")
    print("The code expects NPCs.items() but gets a list")
    
    # Test the state helper
    print("\n" + "-"*50)
    print("\nTesting StateHelper methods...")
    
    buggy_update = {
        'entities': {
            'NPCs': ['New Dragon']  # AI might return this
        }
    }
    
    try:
        # This might be where it fails
        result = StateHelper.deep_merge(state_dict, buggy_update)
        print(f"Deep merge result: {result}")
    except Exception as e:
        print(f"❌ Error in deep_merge: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_combat_bug_scenario()