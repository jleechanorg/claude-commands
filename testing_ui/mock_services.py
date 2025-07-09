#!/usr/bin/env python3
"""
Mock service helpers for Layer 3 browser testing.
Provides controlled API responses for structured fields testing.
"""

import json
from typing import Dict, Any

# Mock API responses for structured fields testing
MOCK_STRUCTURED_FIELDS_RESPONSE = {
    "success": True,
    "response": "The larger goblin, witnessing his underling's demise, lets out a guttural roar.",
    "narrative": "The larger goblin, witnessing his underling's demise, lets out a guttural roar.",
    "session_header": "[SESSION_HEADER]\nTimestamp: 1492 DR, Ches 20, 10:00\nLocation: Goblin Cave\nStatus: Lvl 5 Paladin | HP: 10/10 (Temp: 0) | XP: 0/2700 | Gold: 0gp\nResources: HD: 3/3 | Lay on Hands: 20/20 | Divine Sense: 4/4 | Spells: L1 2/2, L2 1/1 | Channel Divinity: 1/1\nConditions: None | Exhaustion: 0 | Inspiration: No | Potions: 1",
    "entities_mentioned": ["goblin", "underling", "cave entrance"],
    "location_confirmed": "Goblin Cave - Main Chamber",
    "dice_rolls": [
        "Attack Roll: 1d20 + 5 = 18 + 5 = 23 (Hit!)",
        "Damage Roll: 1d8 + 5 = 6 + 5 = 11 Slashing damage"
    ],
    "resources": "HD: 3/3 | Lay on Hands: 5/5 | Spells: L1 4/4, L2 3/3 | Divine Sense: 4/4 | Channel Divinity: 1/1 | Potions: 1",
    "state_updates": {
        "npc_data": {
            "goblin_leader": {"hp": 7, "status": "wounded", "morale": "angry"}
        },
        "location": "goblin_cave_main_chamber"
    },
    "planning_block": "--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **Proceed cautiously:** Slowly enter the cave, searching for traps and enemies.\n2. **Shout a challenge:** Announce your presence to any goblins inside.\n3. **Cast Divine Sense:** Check for any evil presences nearby.\n4. **Other:** Describe a different action you'd like to take.",
    "debug_info": {
        "dm_notes": [
            "The opening scene establishes Sir Kaelan's character, his mission, and the setting. The combat encounter serves as a simple tutorial for dice rolling and combat mechanics."
        ],
        "state_rationale": "The player's attack successfully hit the goblin, dealing 11 damage. The goblin was defeated and removed from the active encounter. The larger goblin now enters combat mode."
    },
    "debug_mode": True,
    "user_scene_number": 2
}

MOCK_GOD_MODE_RESPONSE = {
    "success": True,
    "response": "",
    "narrative": "",
    "god_mode_response": "Current game state:\n- Goblin Leader HP: 7/7\n- Player Location: Cave Entrance\n- Combat: Not active\n- Hidden: Treasure chest behind waterfall\n- NPCs: 2 goblins sleeping in side chamber",
    "entities_mentioned": ["goblin_leader", "treasure_chest", "sleeping_goblins"],
    "location_confirmed": "Cave Entrance",
    "debug_mode": True,
    "user_scene_number": 3
}

def create_mock_api_server():
    """Create a simple mock API server for Layer 3 testing."""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    import urllib.parse
    
    class MockAPIHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if '/api/campaigns/' in self.path and '/interaction' in self.path:
                # Parse request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                request_data = json.loads(post_data.decode('utf-8'))
                
                # Determine response based on mode
                if request_data.get('mode') == 'god':
                    response_data = MOCK_GOD_MODE_RESPONSE
                else:
                    response_data = MOCK_STRUCTURED_FIELDS_RESPONSE
                
                # Send response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode('utf-8'))
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_GET(self):
            if '/api/campaigns' in self.path and '/interaction' not in self.path:
                if self.path == '/api/campaigns':
                    # Mock campaign list
                    campaign_list = {
                        "success": True,
                        "data": [
                            {
                                "id": "test-campaign-id",
                                "title": "Layer 3 Test Campaign",
                                "last_played": "2025-07-09T18:00:00Z",
                                "initial_prompt": "Test campaign for Layer 3 mock testing..."
                            }
                        ]
                    }
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json') 
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(campaign_list).encode('utf-8'))
                elif '/api/campaigns/' in self.path:
                    # Mock individual campaign data
                    campaign_data = {
                        "success": True,
                        "data": {
                            "campaign": {"title": "Layer 3 Test Campaign"},
                            "story": [
                                {
                                    "actor": "gemini",
                                    "text": "Welcome to the test campaign.",
                                    "mode": None,
                                    "user_scene_number": 1,
                                    **MOCK_STRUCTURED_FIELDS_RESPONSE
                                }
                            ],
                            "game_state": {"debug_mode": True}
                        }
                    }
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json') 
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps(campaign_data).encode('utf-8'))
                else:
                    self.send_response(404)
                    self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # Suppress log messages
    
    return MockAPIHandler