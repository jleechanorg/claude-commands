#!/usr/bin/env python3
"""
Campaign Analyzer for Milestone 0.4
Extracts campaign data and detects desync patterns
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prototype.validators.narrative_sync_validator import NarrativeSyncValidator


class DesyncPattern:
    """Represents a detected desync pattern"""

    def __init__(
        self,
        session: int,
        turn: int,
        pattern_type: str,
        expected: list[str],
        found: list[str],
        missing: list[str],
        narrative_excerpt: str,
    ):
        self.session = session
        self.turn = turn
        self.pattern_type = pattern_type
        self.expected = expected
        self.found = found
        self.missing = missing
        self.narrative_excerpt = narrative_excerpt
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "turn": self.turn,
            "pattern_type": self.pattern_type,
            "expected_entities": self.expected,
            "found_entities": self.found,
            "missing_entities": self.missing,
            "narrative_excerpt": self.narrative_excerpt[:200] + "..."
            if len(self.narrative_excerpt) > 200
            else self.narrative_excerpt,
            "timestamp": self.timestamp,
        }


class CampaignAnalyzer:
    """Analyzes campaigns for desync patterns and generates reports"""

    def __init__(self):
        self.validator = NarrativeSyncValidator()
        self.desync_patterns = []
        self.metrics = {
            "total_turns": 0,
            "desync_turns": 0,
            "entities_tracked": set(),
            "pattern_counts": defaultdict(int),
            "processing_time": 0,
        }

    def analyze_campaign(self, campaign_data: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze a campaign for desync patterns

        Args:
            campaign_data: Campaign data with sessions and narratives

        Returns:
            Analysis report with desync patterns and metrics
        """
        start_time = time.time()

        campaign_id = campaign_data.get("campaign_id", "unknown")
        campaign_name = campaign_data.get("campaign_name", "Unknown Campaign")

        print(f"\nAnalyzing campaign: {campaign_name} ({campaign_id})")

        # Process each session
        sessions = campaign_data.get("sessions", [])
        for session_data in sessions:
            self._analyze_session(session_data)

        # Calculate metrics
        self.metrics["processing_time"] = time.time() - start_time
        self.metrics["desync_rate"] = (
            self.metrics["desync_turns"] / self.metrics["total_turns"]
            if self.metrics["total_turns"] > 0
            else 0
        )

        # Generate report
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_sessions": len(sessions),
                "total_turns": self.metrics["total_turns"],
                "desync_turns": self.metrics["desync_turns"],
                "desync_rate": self.metrics["desync_rate"],
                "unique_entities": len(self.metrics["entities_tracked"]),
                "processing_time_seconds": self.metrics["processing_time"],
            },
            "pattern_breakdown": dict(self.metrics["pattern_counts"]),
            "desync_patterns": [p.to_dict() for p in self.desync_patterns],
            "entity_list": sorted(self.metrics["entities_tracked"]),
        }


    def _analyze_session(self, session_data: dict[str, Any]):
        """Analyze a single session for desyncs"""
        session_num = session_data.get("session_number", 0)
        turns = session_data.get("turns", [])

        print(f"  Analyzing session {session_num} with {len(turns)} turns...")

        for turn_data in turns:
            self._analyze_turn(session_num, turn_data)

    def _analyze_turn(self, session_num: int, turn_data: dict[str, Any]):
        """Analyze a single turn for desyncs"""
        turn_num = turn_data.get("turn_number", 0)
        narrative = turn_data.get("narrative", "")
        game_state = turn_data.get("game_state", {})

        self.metrics["total_turns"] += 1

        # Extract expected entities from game state
        expected_entities = self._extract_expected_entities(game_state)

        # Track all entities
        self.metrics["entities_tracked"].update(expected_entities)

        if not expected_entities:
            return

        # Validate narrative
        validation_result = self.validator.validate(
            narrative_text=narrative,
            expected_entities=expected_entities,
            location=game_state.get("location"),
        )

        # Check for desyncs
        if validation_result.entities_missing:
            self.metrics["desync_turns"] += 1

            # Determine pattern type
            pattern_type = self._classify_desync_pattern(
                game_state, validation_result, narrative
            )

            self.metrics["pattern_counts"][pattern_type] += 1

            # Record desync
            desync = DesyncPattern(
                session=session_num,
                turn=turn_num,
                pattern_type=pattern_type,
                expected=expected_entities,
                found=validation_result.entities_found,
                missing=validation_result.entities_missing,
                narrative_excerpt=narrative,
            )

            self.desync_patterns.append(desync)

    def _extract_expected_entities(self, game_state: dict[str, Any]) -> list[str]:
        """Extract entities that should be mentioned from game state"""
        entities = []

        # Player character
        pc_data = game_state.get("player_character_data", {})
        if pc_data.get("name"):
            entities.append(pc_data["name"])

        # NPCs
        npc_data = game_state.get("npc_data", {})
        for npc_name, npc_info in npc_data.items():
            # Only include present NPCs
            if npc_info.get("present", True) and npc_info.get("conscious", True):
                entities.append(npc_name)

        # Combat participants
        combat_state = game_state.get("combat_state", {})
        if combat_state.get("in_combat"):
            participants = combat_state.get("participants", [])
            entities.extend(p for p in participants if p not in entities)

        return entities

    def _classify_desync_pattern(
        self, game_state: dict[str, Any], validation_result: Any, narrative: str
    ) -> str:
        """Classify the type of desync pattern"""

        # Check for combat desync
        if game_state.get("combat_state", {}).get("in_combat"):
            return "combat_entity_missing"

        # Check for split party
        locations = set()
        for npc_info in game_state.get("npc_data", {}).values():
            if loc := npc_info.get("location"):
                locations.add(loc)

        if len(locations) > 1:
            return "split_party_confusion"

        # Check for status effects
        missing_entities = validation_result.entities_missing
        for entity in missing_entities:
            npc_info = game_state.get("npc_data", {}).get(entity, {})
            if not npc_info.get("conscious", True):
                return "unconscious_omission"
            if npc_info.get("hidden", False):
                return "hidden_character"

        # Check for presence ambiguity
        if hasattr(validation_result, "metadata"):
            ambiguous = validation_result.metadata.get("ambiguous", [])
            if ambiguous:
                return "presence_ambiguity"

        # Default
        return "general_entity_omission"

    def export_campaign_snapshot(self, campaign_data: dict[str, Any], output_path: str):
        """Export campaign data in efficient format"""
        # Create minimal snapshot focusing on turns with desyncs
        snapshot = {
            "campaign_id": campaign_data.get("campaign_id"),
            "campaign_name": campaign_data.get("campaign_name"),
            "metadata": {
                "players": campaign_data.get("players", []),
                "total_sessions": len(campaign_data.get("sessions", [])),
                "date_range": {
                    "start": campaign_data.get("start_date"),
                    "end": campaign_data.get("last_updated"),
                },
            },
            "desync_turns": [],
        }

        # Only include turns with desyncs
        for pattern in self.desync_patterns:

            # Find the original turn data
            for session in campaign_data.get("sessions", []):
                if session.get("session_number") == pattern.session:
                    for turn in session.get("turns", []):
                        if turn.get("turn_number") == pattern.turn:
                            snapshot["desync_turns"].append(
                                {
                                    "session": pattern.session,
                                    "turn": pattern.turn,
                                    "game_state": turn.get("game_state"),
                                    "narrative": turn.get("narrative"),
                                    "desync_info": pattern.to_dict(),
                                }
                            )
                            break

        # Write snapshot
        with open(output_path, "w") as f:
            json.dump(snapshot, f, indent=2)

        print(f"Exported campaign snapshot to {output_path}")
        return output_path


def load_campaign_data(campaign_path: str) -> dict[str, Any]:
    """Load campaign data from file or mock data"""
    if os.path.exists(campaign_path):
        with open(campaign_path) as f:
            return json.load(f)
    else:
        # Return mock campaign data for testing
        return create_mock_campaign_data()


def create_mock_campaign_data() -> dict[str, Any]:
    """Create mock campaign data for testing"""
    return {
        "campaign_id": "sariel_v2_001",
        "campaign_name": "Sariel v2: The Awakening",
        "players": ["Player1", "Player2", "Player3", "Player4"],
        "start_date": "2024-01-15",
        "last_updated": "2024-03-20",
        "sessions": [
            {
                "session_number": 1,
                "date": "2024-01-15",
                "turns": [
                    {
                        "turn_number": 1,
                        "game_state": {
                            "player_character_data": {"name": "Sariel"},
                            "npc_data": {
                                "Cassian": {"present": True},
                                "Valerius": {"present": True},
                            },
                            "location": "Throne Room",
                        },
                        "narrative": "Sariel stood before the throne as Valerius approached.",
                        # Missing Cassian
                    },
                    {
                        "turn_number": 2,
                        "game_state": {
                            "player_character_data": {"name": "Sariel"},
                            "npc_data": {
                                "Cassian": {"present": True, "location": "throne"},
                                "Valerius": {"present": True, "location": "entrance"},
                                "Guard": {"present": True},
                            },
                            "combat_state": {
                                "in_combat": True,
                                "participants": ["Sariel", "Cassian", "Guard"],
                            },
                        },
                        "narrative": "The guard attacked! Sariel dodged while engaging in combat.",
                        # Missing Cassian in combat
                    },
                ],
            }
        ],
    }


def main():
    """Main execution function"""
    analyzer = CampaignAnalyzer()

    # Test with mock campaign
    campaign_data = create_mock_campaign_data()

    # Analyze campaign
    report = analyzer.analyze_campaign(campaign_data)

    # Save analysis report
    report_path = "analysis/campaign_analysis_sariel_v2.json"
    os.makedirs("analysis", exist_ok=True)

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\nAnalysis complete! Report saved to {report_path}")

    # Export snapshot
    snapshot_path = "analysis/campaign_snapshot_sariel_v2.json"
    analyzer.export_campaign_snapshot(campaign_data, snapshot_path)

    # Print summary
    print("\nDesync Summary:")
    print(f"  Total turns: {report['summary']['total_turns']}")
    print(f"  Desync turns: {report['summary']['desync_turns']}")
    print(f"  Desync rate: {report['summary']['desync_rate']:.2%}")
    print("\nPattern breakdown:")
    for pattern, count in report["pattern_breakdown"].items():
        print(f"  {pattern}: {count}")


if __name__ == "__main__":
    main()
