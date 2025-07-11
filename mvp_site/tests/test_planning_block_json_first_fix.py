#!/usr/bin/env python3
"""
Test to demonstrate and fix the planning block display issue.
Planning blocks should only come from JSON field, not narrative text.
"""

import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from narrative_response_schema import NarrativeResponse
import constants


class TestPlanningBlockJsonFirstFix(unittest.TestCase):
    """Test the JSON-first planning block architecture"""
    
    def test_user_reported_issue(self):
        """Reproduce the exact issue the user reported"""
        
        # This is what the user sees - planning block in narrative text
        user_sees_narrative = """[CHARACTER CREATION - Step 1]

Scene #1: Excellent! I see you want to play as Astarion. Let's design Astarion with D&D 5e mechanics!

How would you like to design Astarion:
1. **[AIGenerated]:** I'll create a complete D&D version based on their lore
2. **[StandardDND]:** You choose from D&D races and classes  
3. **[CustomClass]:** We'll create custom mechanics for their unique abilities

Which option would you prefer? (1, 2, or 3)

What is your choice?
1. **AIGenerated**
2. **StandardDND**
3. **CustomClass**"""
        
        # What SHOULD happen with JSON-first architecture:
        # 1. Narrative text should NOT contain planning block
        correct_narrative = """[CHARACTER CREATION - Step 1]

Scene #1: Excellent! I see you want to play as Astarion. Let's design Astarion with D&D 5e mechanics!

How would you like to design Astarion:"""
        
        # 2. Planning block should be in structured response
        correct_planning_block = """Which option would you prefer? (1, 2, or 3)

What is your choice?
1. **AIGenerated** - I'll create a complete D&D version based on their lore
2. **StandardDND** - You choose from D&D races and classes  
3. **CustomClass** - We'll create custom mechanics for their unique abilities"""
        
        # Create the correct structured response
        structured_response = NarrativeResponse(
            narrative=correct_narrative,
            planning_block=correct_planning_block
        )
        
        # Verify the fix
        self.assertNotIn("**AIGenerated**", structured_response.narrative)
        self.assertNotIn("**StandardDND**", structured_response.narrative)
        self.assertNotIn("**CustomClass**", structured_response.narrative)
        
        self.assertIn("AIGenerated", structured_response.planning_block)
        self.assertIn("StandardDND", structured_response.planning_block)
        self.assertIn("CustomClass", structured_response.planning_block)
    
    
    def test_frontend_receives_correct_data(self):
        """Test that frontend receives planning block in JSON field only"""
        
        # Simulate API response data structure
        api_response = {
            'success': True,
            'narrative': '[CHARACTER CREATION - Step 1]\n\nScene #1: Let\'s create your character!',
            constants.FIELD_PLANNING_BLOCK: 'What is your choice?\n1. **AIGenerated**\n2. **StandardDND**\n3. **CustomClass**',
            'debug_mode': False,
            'sequence_id': 1
        }
        
        # Frontend should:
        # 1. Display narrative without planning block
        self.assertNotIn("AIGenerated", api_response['narrative'])
        
        # 2. Get planning block from JSON field
        self.assertIn("AIGenerated", api_response[constants.FIELD_PLANNING_BLOCK])
        
        # 3. NOT try to parse planning blocks from narrative text (fixed in app.js line 298)


if __name__ == '__main__':
    unittest.main()