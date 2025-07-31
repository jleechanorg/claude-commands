#!/usr/bin/env python3
"""
Campaign selector for Milestone 0.4 testing.
Finds real campaigns with historical desync issues.
"""

import json
import os

# Add parent directory to path
import sys
from collections import defaultdict
from datetime import datetime

mvp_site_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mvp_site"
)
sys.path.insert(0, mvp_site_path)

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase if not already done
if not firebase_admin._apps:
    cred_path = os.path.expanduser(
        "~/.firebase/worldarchitect-ai-firebase-adminsdk.json"
    )
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)


def is_test_campaign(campaign_name: str) -> bool:
    """Check if campaign is a test campaign to exclude."""
    test_patterns = [
        "my epic adventure",
        "test campaign",
        "demo campaign",
        "tutorial",
        "test-",
    ]
    name_lower = campaign_name.lower()
    return any(pattern in name_lower for pattern in test_patterns)


def analyze_narrative_for_desync(narrative: str, game_state: dict) -> list[dict]:
    """Analyze a narrative for potential desync issues."""
    issues = []

    # Extract expected entities from game state
    expected_entities = set()

    # Get player characters
    if "player_character_data" in game_state:
        for name, data in game_state["player_character_data"].items():
            if isinstance(data, dict):
                expected_entities.add(name)

    # Get NPCs in scene
    if "npc_data" in game_state:
        for npc_id, npc_data in game_state["npc_data"].items():
            if isinstance(npc_data, dict):
                name = npc_data.get("name", npc_id)
                # Check if NPC is in current location
                if npc_data.get("location") == game_state.get("world_data", {}).get(
                    "current_location"
                ):
                    expected_entities.add(name)

    # Check for missing entities
    narrative_lower = narrative.lower()
    for entity in expected_entities:
        # Simple check - can be enhanced
        if entity.lower() not in narrative_lower:
            issues.append(
                {
                    "type": "missing_entity",
                    "entity": entity,
                    "expected": True,
                    "found": False,
                }
            )

    # Check for combat desyncs
    if game_state.get("combat_state", {}).get("in_combat"):
        combat_participants = game_state.get("combat_state", {}).get("participants", [])
        for participant in combat_participants:
            if isinstance(participant, dict):
                name = participant.get("name", "")
                if name and name.lower() not in narrative_lower:
                    issues.append(
                        {
                            "type": "missing_combat_participant",
                            "entity": name,
                            "combat_active": True,
                        }
                    )

    # Check for location mismatches
    current_location = game_state.get("world_data", {}).get("current_location", "")
    if current_location:
        # Simple location check
        location_words = current_location.lower().split()
        location_mentioned = any(
            word in narrative_lower for word in location_words if len(word) > 3
        )
        if not location_mentioned and len(narrative) > 100:
            issues.append(
                {
                    "type": "location_mismatch",
                    "expected_location": current_location,
                    "narrative_length": len(narrative),
                }
            )

    return issues


def analyze_campaign(
    campaign_id: str, campaign_data: dict, user_id: str, limit: int = 50
) -> dict:
    """Analyze a campaign for desync patterns."""
    analysis = {
        "campaign_id": campaign_id,
        "campaign_name": campaign_data.get("name", "Unknown"),
        "total_sessions": 0,
        "total_turns": 0,
        "desync_incidents": [],
        "desync_rate": 0.0,
        "player_count": len(campaign_data.get("players", [])),
        "created_at": campaign_data.get("created_at"),
        "last_played": campaign_data.get("last_played"),
        "common_issues": defaultdict(int),
    }

    # Get game states for this campaign
    db = firestore.client()
    # Game states are stored under users/{user_id}/campaigns/{campaign_id}/game_state
    (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("game_state")
    )

    # Actually, let's get the campaign doc which contains story
    campaign_doc = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .get()
    )

    if campaign_doc.exists:
        campaign_full_data = campaign_doc.to_dict()
        story_entries = campaign_full_data.get("story", [])

        for i, entry in enumerate(story_entries):
            if analysis["total_turns"] >= limit:
                break

            # Skip non-AI entries
            if not isinstance(entry, dict) or entry.get("actor") != "ai":
                continue

            analysis["total_turns"] += 1

            # Get narrative text
            narrative = entry.get("text", "")
            if not narrative or len(narrative) < 50:
                continue

            # Try to get game state at this point
            # Note: This is approximate as we don't have exact state for each turn
            game_state = campaign_full_data.get("game_state", {})

            # Analyze for desyncs
            issues = analyze_narrative_for_desync(narrative, game_state)

            if issues:
                analysis["desync_incidents"].append(
                    {
                        "turn": i,
                        "issues": issues,
                        "narrative_preview": narrative[:200] + "..."
                        if len(narrative) > 200
                        else narrative,
                    }
                )

                # Track common issue types
                for issue in issues:
                    analysis["common_issues"][issue["type"]] += 1

    # Calculate desync rate
    if analysis["total_turns"] > 0:
        analysis["desync_rate"] = (
            len(analysis["desync_incidents"]) / analysis["total_turns"]
        )

    # Estimate session count
    analysis["total_sessions"] = analysis["total_turns"] // 20  # Rough estimate

    return analysis


def get_all_campaigns():
    """Get all campaigns from Firestore."""
    db = firestore.client()
    campaigns = []

    # Get all users
    users_ref = db.collection("users")
    for user_doc in users_ref.stream():
        user_id = user_doc.id

        # Get campaigns for this user
        campaigns_ref = user_doc.reference.collection("campaigns")
        for campaign_doc in campaigns_ref.stream():
            campaign_data = campaign_doc.to_dict()
            if campaign_data:
                campaign_data["user_id"] = user_id
                campaign_data["campaign_id"] = campaign_doc.id
                campaigns.append(campaign_data)

    return campaigns


def select_campaigns_for_testing():
    """Select campaigns for Milestone 0.4 testing."""
    print("Selecting campaigns for Milestone 0.4 testing...")

    # Get all campaigns
    all_campaigns = get_all_campaigns()
    print(f"Found {len(all_campaigns)} total campaigns")

    # Filter out test campaigns
    real_campaigns = []
    for campaign_data in all_campaigns:
        if not isinstance(campaign_data, dict):
            continue

        name = campaign_data.get("name", "") or campaign_data.get("title", "")
        if is_test_campaign(name):
            continue

        # Check player count - for now, any campaign with a story is valid
        story = campaign_data.get("story", [])
        if len(story) < 10:  # At least 10 story entries
            continue

        real_campaigns.append(campaign_data)

    print(f"Found {len(real_campaigns)} real campaigns after filtering")

    # Analyze campaigns for desync patterns
    analyzed_campaigns = []

    # Always include Sariel v2 if it exists
    sariel_found = False
    for campaign_data in real_campaigns:
        name = campaign_data.get("name", "") or campaign_data.get("title", "")
        if "sariel" in name.lower() and "v2" in name.lower():
            print("\nAnalyzing Sariel v2 (required)...")
            analysis = analyze_campaign(
                campaign_data["campaign_id"], campaign_data, campaign_data["user_id"]
            )
            analyzed_campaigns.append(analysis)
            sariel_found = True
            break

    # Analyze other campaigns
    for campaign_data in real_campaigns:
        if len(analyzed_campaigns) >= 10:  # Get top 10 for selection
            break

        # Skip if already analyzed
        if any(
            a["campaign_id"] == campaign_data["campaign_id"] for a in analyzed_campaigns
        ):
            continue

        name = campaign_data.get("name", "") or campaign_data.get("title", "")
        print(f"\nAnalyzing campaign: {name}")

        analysis = analyze_campaign(
            campaign_data["campaign_id"],
            campaign_data,
            campaign_data["user_id"],
            limit=30,
        )

        # Only include if it has meaningful data
        if analysis["total_turns"] >= 5 and analysis["desync_rate"] > 0.05:
            analyzed_campaigns.append(analysis)

    # Sort by desync rate
    analyzed_campaigns.sort(key=lambda x: x["desync_rate"], reverse=True)

    # Generate report
    report = {
        "analysis_date": datetime.now().isoformat(),
        "total_campaigns_analyzed": len(analyzed_campaigns),
        "sariel_v2_found": sariel_found,
        "top_campaigns": analyzed_campaigns[:5],
    }

    # Save analysis
    output_path = "analysis/campaign_selection_0.4.json"
    os.makedirs("analysis", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\nAnalysis saved to {output_path}")

    # Generate markdown report
    generate_markdown_report(report)

    return report


def generate_markdown_report(report: dict):
    """Generate markdown report for campaign selection."""
    md_content = f"""# Campaign Selection for Milestone 0.4 Testing

Generated: {report["analysis_date"]}

## Summary
- Total campaigns analyzed: {report["total_campaigns_analyzed"]}
- Sariel v2 found: {"Yes" if report["sariel_v2_found"] else "No - Manual selection needed"}

## Recommended Campaigns

"""

    for i, campaign in enumerate(report["top_campaigns"], 1):
        desync_examples = []
        for incident in campaign["desync_incidents"][:3]:  # First 3 examples
            for issue in incident["issues"]:
                if issue["type"] == "missing_entity":
                    desync_examples.append(
                        f"- Turn {incident['turn']}: Missing {issue['entity']} from narrative"
                    )
                elif issue["type"] == "missing_combat_participant":
                    desync_examples.append(
                        f"- Turn {incident['turn']}: Combat participant {issue['entity']} not mentioned"
                    )
                elif issue["type"] == "location_mismatch":
                    desync_examples.append(
                        f"- Turn {incident['turn']}: Location '{issue['expected_location']}' not referenced"
                    )

        md_content += f"""### {i}. {campaign["campaign_name"]}
- **Campaign ID**: {campaign["campaign_id"]}
- **Players**: {campaign["player_count"]}
- **Estimated Sessions**: {campaign["total_sessions"]}
- **Desync Rate**: {campaign["desync_rate"] * 100:.1f}% ({len(campaign["desync_incidents"])} incidents in {campaign["total_turns"]} turns)
- **Common Issues**: {", ".join(f"{k}: {v}" for k, v in campaign["common_issues"].items())}
- **Example Desyncs**:
{chr(10).join(desync_examples[:3])}

"""

    # Save markdown report
    output_path = "analysis/campaign_selection_0.4.md"
    with open(output_path, "w") as f:
        f.write(md_content)

    print(f"Markdown report saved to {output_path}")


if __name__ == "__main__":
    select_campaigns_for_testing()
