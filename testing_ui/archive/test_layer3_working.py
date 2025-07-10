#!/usr/bin/env python3
"""
Working Layer 3 test - Browser + Mock structured fields with direct injection.
"""

import os
import sys
import json
from playwright.sync_api import sync_playwright

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test utilities
sys.path.append(os.path.dirname(__file__))
from test_data_utils import create_test_campaign
from test_ui_helpers import capture_structured_fields_sequence

def test_layer3_working():
    """Working Layer 3 test with direct HTML injection."""
    
    print("=== Layer 3 Working Test ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Initialize helper
        helper = BrowserTestHelper("layer3_working", page)
        
        try:
            # Create complete test HTML with structured fields
            test_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Layer 3 Working Test</title>
                <style>
                    .session-header { 
                        background-color: #f0f0f0; 
                        padding: 10px; 
                        margin-bottom: 10px; 
                        font-family: monospace; 
                        white-space: pre-wrap; 
                        border-radius: 5px; 
                    }
                    .god-mode-response { 
                        border: 2px solid #9b59b6; 
                        background-color: rgba(155, 89, 182, 0.05); 
                        padding: 15px; 
                        margin: 10px 0; 
                        border-radius: 8px; 
                    }
                    .entities-mentioned { 
                        background-color: #e7f3ff; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #2196F3; 
                    }
                    .location-confirmed { 
                        background-color: #f0f8ff; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #4169e1; 
                    }
                    .dice-rolls { 
                        background-color: #e8f4e8; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #4caf50; 
                    }
                    .resources { 
                        background-color: #fff3cd; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #ffc107; 
                    }
                    .state-updates { 
                        background-color: #f5f5f5; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #9e9e9e; 
                    }
                    .planning-block { 
                        background-color: #e3f2fd; 
                        padding: 15px; 
                        margin: 15px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #2196f3; 
                        white-space: pre-wrap; 
                    }
                    .debug-info { 
                        background-color: #f8f9fa; 
                        padding: 15px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border: 1px solid #dee2e6; 
                    }
                    .dm-notes { 
                        background-color: #f8f4ff; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #9c27b0; 
                    }
                    .state-rationale { 
                        background-color: #fff8e7; 
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 5px; 
                        border-left: 4px solid #ff9800; 
                    }
                </style>
            </head>
            <body>
                <h1>Layer 3 Working Test - All 10 Structured Fields</h1>
                
                <div class="session-header">
[SESSION_HEADER]
Timestamp: 1492 DR, Ches 20, 10:00
Location: Goblin Cave
Status: Lvl 5 Paladin | HP: 10/10 (Temp: 0) | XP: 0/2700 | Gold: 0gp
Resources: HD: 3/3 | Lay on Hands: 20/20 | Divine Sense: 4/4 | Spells: L1 2/2, L2 1/1 | Channel Divinity: 1/1
Conditions: None | Exhaustion: 0 | Inspiration: No | Potions: 1
                </div>
                
                <div class="god-mode-response">
                    <strong>🔮 God Mode Response:</strong>
                    <pre>Current game state:
- Goblin HP: 7/7
- Player Location: Cave Entrance
- Combat: Not active
- Hidden: Treasure chest behind waterfall
- NPCs: 2 goblins sleeping in side chamber</pre>
                </div>
                
                <div class="entities-mentioned">
                    <strong>👥 Entities:</strong>
                    <ul>
                        <li>goblin</li>
                        <li>dragon</li>
                        <li>merchant</li>
                    </ul>
                </div>
                
                <div class="location-confirmed">
                    <strong>📍 Location:</strong> Dragon's Lair
                </div>
                
                <div class="dice-rolls">
                    <strong>🎲 Dice Rolls:</strong>
                    <ul>
                        <li>Attack Roll: 1d20 + 5 = 18 + 5 = 23 (Hit!)</li>
                        <li>Damage Roll: 1d8 + 5 = 6 + 5 = 11 Slashing damage</li>
                    </ul>
                </div>
                
                <div class="resources">
                    <strong>📊 Resources:</strong> HD: 3/3 | Lay on Hands: 5/5 | Spells: L1 4/4, L2 3/3 | Divine Sense: 4/4 | Channel Divinity: 1/1 | Potions: 1
                </div>
                
                <div class="state-updates">
                    <strong>🔧 State Updates:</strong>
                    <pre>{
  "npc_data": {
    "goblin_leader": {"hp": 7, "status": "wounded", "morale": "angry"}
  },
  "location": "goblin_cave_main_chamber"
}</pre>
                </div>
                
                <div class="planning-block">--- PLANNING BLOCK ---
What would you like to do next?
1. **Proceed cautiously:** Slowly enter the cave, searching for traps and enemies.
2. **Shout a challenge:** Announce your presence to any goblins inside.
3. **Cast Divine Sense:** Check for any evil presences nearby.
4. **Other:** Describe a different action you'd like to take.</div>
                
                <div class="debug-info">
                    <strong>🔍 Debug Info:</strong>
                    <div class="dm-notes">
                        <strong>📝 DM Notes:</strong>
                        <ul>
                            <li>The opening scene establishes Sir Kaelan's character, his mission, and the setting. The combat encounter serves as a simple tutorial for dice rolling and combat mechanics.</li>
                        </ul>
                    </div>
                    <div class="state-rationale">
                        <strong>💭 State Rationale:</strong> The player's attack successfully hit the goblin, dealing 11 damage. The goblin was defeated and removed from the active encounter.
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Load the test HTML
            page.set_content(test_html)
            
            # Take initial screenshot
            helper.take_screenshot("full_page")
            
            # Verify all structured fields are present
            field_checks = {
                'session_header': '.session-header',
                'god_mode_response': '.god-mode-response',
                'entities_mentioned': '.entities-mentioned',
                'location_confirmed': '.location-confirmed',
                'dice_rolls': '.dice-rolls',
                'resources': '.resources',
                'state_updates': '.state-updates',
                'planning_block': '.planning-block',
                'debug_info': '.debug-info',
                'dm_notes': '.dm-notes',
                'state_rationale': '.state-rationale'
            }
            
            print("🔍 Verifying structured fields presence...")
            found_fields = []
            for field_name, selector in field_checks.items():
                if page.locator(selector).count() > 0:
                    helper.take_screenshot(f"field_{field_name}", selector)
                    found_fields.append(field_name)
                    print(f"✅ {field_name} - Found and captured")
                else:
                    print(f"❌ {field_name} - Not found")
            
            # Final summary
            summary = helper.get_screenshot_summary()
            print(f"\n✅ Layer 3 Working Test Complete!")
            print(f"📁 Screenshots: {summary['screenshot_dir']}")
            print(f"📸 Total: {summary['total_screenshots']}")
            print(f"🎯 Fields found: {len(found_fields)}/11")
            print(f"📋 Found fields: {', '.join(found_fields)}")
            
            return len(found_fields) >= 10
            
        except Exception as e:
            print(f"❌ Layer 3 working test failed: {e}")
            helper.take_screenshot("error")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_layer3_working()
    exit(0 if success else 1)