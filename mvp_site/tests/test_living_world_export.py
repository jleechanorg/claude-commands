"""Test comprehensive debug events in campaign exports."""

import unittest
from mvp_site.document_generator import _format_debug_events, format_story_entry


class TestDebugEventsExport(unittest.TestCase):
    """Test that all debug events are properly included in exports."""

    def test_format_debug_events_with_background_events(self):
        """Test formatting background_events from debug_info."""
        debug_info = {
            "background_events": [
                {
                    "actor": "City Guard Captain",
                    "action": "Doubled patrols in the market district",
                    "event_type": "immediate",
                    "status": "pending",
                },
                {
                    "actor": "Zhentarim Inner Circle",
                    "action": "Replaced regional commander",
                    "event_type": "long_term",
                    "status": "discovered",
                },
            ]
        }

        result = _format_debug_events(debug_info)

        self.assertIn("🌍 Living World Updates", result)
        self.assertIn("📜 Background Events:", result)
        self.assertIn("City Guard Captain", result)
        self.assertIn("Doubled patrols", result)
        self.assertIn("immediate", result)
        self.assertIn("pending", result)
        self.assertIn("Zhentarim Inner Circle", result)
        self.assertIn("long_term", result)

    def test_format_debug_events_comprehensive(self):
        """Test formatting all types of debug events."""
        debug_info = {
            "world_events": {
                "background_events": [
                    {
                        "actor": "Merchant Caravan",
                        "action": "Arrived with news",
                        "event_type": "immediate",
                        "status": "resolved",
                    }
                ],
                "faction_updates": {
                    "Zhentarim": {
                        "current_objective": "Control trade routes",
                        "progress": "50% complete",
                        "resource_change": "+500 gold"
                    }
                },
                "rumors": [
                    {
                        "content": "The Archdevils are mobilizing",
                        "accuracy": "true"
                    }
                ],
                "scene_event": {
                    "type": "companion_request",
                    "actor": "Shadowheart",
                    "description": "Asks for help with a personal quest"
                },
                "complications": {
                    "type": "information_leak",
                    "severity": "regional",
                    "description": "Your plans were discovered"
                }
            }
        }

        result = _format_debug_events(debug_info)

        # Check all sections are present
        self.assertIn("🌍 Living World Updates", result)
        self.assertIn("📜 Background Events:", result)
        self.assertIn("🏛️ Faction Updates:", result)
        self.assertIn("💬 Rumors:", result)
        self.assertIn("🎭 Scene Event:", result)
        self.assertIn("⚠️ Complications:", result)

        # Check specific content
        self.assertIn("Merchant Caravan", result)
        self.assertIn("Zhentarim", result)
        self.assertIn("Control trade routes", result)
        self.assertIn("The Archdevils are mobilizing", result)
        self.assertIn("Shadowheart", result)
        self.assertIn("information_leak", result)

    def test_format_debug_events_with_string_events(self):
        """Test formatting background_events that are strings."""
        debug_info = {
            "background_events": [
                "A mysterious figure was spotted in the shadows",
                {
                    "actor": "City Guard",
                    "action": "Increased patrols",
                    "event_type": "immediate",
                    "status": "pending",
                },
                "Strange lights appeared in the sky"
            ]
        }

        result = _format_debug_events(debug_info)

        self.assertIn("🌍 Living World Updates", result)
        self.assertIn("📜 Background Events:", result)
        # Check string events are formatted with ⏳ icon
        self.assertIn("⏳ A mysterious figure was spotted in the shadows", result)
        self.assertIn("⏳ Strange lights appeared in the sky", result)
        # Check dict event is also present
        self.assertIn("City Guard", result)
        self.assertIn("Increased patrols", result)

    def test_format_debug_events_empty(self):
        """Test that empty debug_info returns empty string."""
        self.assertEqual(_format_debug_events({}), "")
        self.assertEqual(_format_debug_events(None), "")

    def test_format_debug_events_empty_background_events(self):
        """Test that debug_info with empty background_events returns empty string."""
        debug_info = {
            "background_events": [],
            "world_events": {
                "background_events": []
            }
        }
        result = _format_debug_events(debug_info)
        self.assertEqual(result, "")

    def test_format_story_entry_with_comprehensive_debug(self):
        """Test that format_story_entry includes all debug events."""
        entry = {
            "actor": "gemini",
            "text": "The city buzzes with activity.",
            "user_scene_number": 3,
            "debug_info": {
                "background_events": [
                    {
                        "actor": "The remaining Archdevils",
                        "action": "Initiated a defensive mobilization",
                        "event_type": "immediate",
                        "status": "pending",
                    }
                ],
                "world_events": {
                    "rumors": [
                        {"content": "War is coming", "accuracy": "partial"}
                    ]
                }
            },
        }

        result = format_story_entry(entry, include_scene=True)

        self.assertIn("SCENE 3", result)
        self.assertIn("🌍 Living World Updates", result)
        self.assertIn("The remaining Archdevils", result)
        self.assertIn("defensive mobilization", result)
        self.assertIn("💬 Rumors:", result)
        self.assertIn("War is coming", result)

    def test_format_story_entry_without_debug_info(self):
        """Test that format_story_entry works without debug_info."""
        entry = {
            "actor": "gemini",
            "text": "You enter the tavern.",
            "user_scene_number": 1,
        }

        result = format_story_entry(entry, include_scene=True)

        self.assertIn("SCENE 1", result)
        self.assertIn("You enter the tavern", result)
        self.assertNotIn("🌍 Living World Updates", result)


if __name__ == "__main__":
    unittest.main()
