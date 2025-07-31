#!/usr/bin/env python3
"""
Real campaign selector for Milestone 0.4 testing.
Connects to actual Firebase DB to find campaigns with desync issues.
"""

import json
import os
import sys
from datetime import datetime

# Add mvp_site to path
mvp_site_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mvp_site"
)
sys.path.insert(0, mvp_site_path)

import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
if not firebase_admin._apps:
    try:
        # Try to use default credentials (from environment or compute engine)
        firebase_admin.initialize_app()
    except:
        # Try to use local credentials file
        cred_path = os.path.expanduser(
            "~/.config/gcloud/application_default_credentials.json"
        )
        if os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        else:
            print("Error: Could not find Firebase credentials")
            sys.exit(1)


def is_test_campaign(campaign_name):
    """Check if this is a test campaign."""
    if not campaign_name:
        return True
    test_patterns = ["my epic adventure", "test campaign", "demo campaign", "tutorial"]
    return any(pattern in campaign_name.lower() for pattern in test_patterns)


def analyze_campaign_stories(campaign_data):
    """Analyze campaign story for desync patterns."""
    story = campaign_data.get("story", [])
    game_state = campaign_data.get("game_state", {})

    desync_incidents = []
    total_ai_turns = 0

    # Get expected entities from game state
    expected_entities = set()

    # Player characters
    pc_data = game_state.get("player_character_data", {})
    if isinstance(pc_data, dict):
        expected_entities.update(pc_data.keys())

    # NPCs in current location
    game_state.get("world_data", {}).get("current_location", "")
    game_state.get("npc_data", {})

    # Combat participants
    combat_state = game_state.get("combat_state", {})
    if combat_state.get("in_combat"):
        participants = combat_state.get("participants", [])
        for p in participants:
            if isinstance(p, dict):
                name = p.get("name")
                if name:
                    expected_entities.add(name)

    # Analyze story entries
    for i, entry in enumerate(story[-50:]):  # Last 50 entries
        if not isinstance(entry, dict):
            continue

        if entry.get("actor") != "ai":
            continue

        total_ai_turns += 1
        narrative = entry.get("text", "")

        if len(narrative) < 50:
            continue

        # Check for missing entities
        narrative_lower = narrative.lower()
        missing = []

        for entity in expected_entities:
            if entity.lower() not in narrative_lower:
                missing.append(entity)

        if missing:
            desync_incidents.append(
                {
                    "turn": i,
                    "missing_entities": missing,
                    "narrative_preview": narrative[:150] + "...",
                }
            )

    desync_rate = len(desync_incidents) / total_ai_turns if total_ai_turns > 0 else 0

    return {
        "total_turns": total_ai_turns,
        "desync_incidents": desync_incidents,
        "desync_rate": desync_rate,
    }


def get_real_campaigns():
    """Get real campaigns from Firebase."""
    print("Connecting to Firebase...")
    db = firestore.client()

    campaigns_found = []

    # Get all users
    users_ref = db.collection("users")
    user_count = 0

    for user_doc in users_ref.stream():
        user_count += 1
        if user_count > 50:  # Limit to first 50 users
            break

        user_id = user_doc.id

        # Get campaigns for this user
        campaigns_ref = user_doc.reference.collection("campaigns")

        for campaign_doc in campaigns_ref.stream():
            campaign_data = campaign_doc.to_dict()
            if not campaign_data:
                continue

            name = campaign_data.get("name", "") or campaign_data.get("title", "")

            # Skip test campaigns
            if is_test_campaign(name):
                continue

            # Must have meaningful story
            story = campaign_data.get("story", [])
            if len(story) < 20:
                continue

            # Add metadata
            campaign_data["user_id"] = user_id
            campaign_data["campaign_id"] = campaign_doc.id
            campaign_data["story_length"] = len(story)

            campaigns_found.append(
                {
                    "campaign_id": campaign_doc.id,
                    "user_id": user_id,
                    "name": name,
                    "story_length": len(story),
                    "data": campaign_data,
                }
            )

            print(f"Found campaign: {name} ({len(story)} story entries)")

    return campaigns_found


def main():
    """Main function to select campaigns."""
    # Get real campaigns
    real_campaigns = get_real_campaigns()
    print(f"\nFound {len(real_campaigns)} real campaigns")

    # Analyze for desync patterns
    analyzed = []
    sariel_found = False

    for campaign in real_campaigns[:20]:  # Analyze first 20
        name = campaign["name"]

        # Check for Sariel v2
        if "sariel" in name.lower() and (
            "v2" in name.lower() or "awakening" in name.lower()
        ):
            sariel_found = True
            print(f"\n✓ Found Sariel campaign: {name}")

        print(f"\nAnalyzing: {name}")

        analysis = analyze_campaign_stories(campaign["data"])

        if analysis["desync_rate"] > 0.05 and analysis["total_turns"] > 5:
            analyzed.append(
                {
                    "campaign_id": campaign["campaign_id"],
                    "user_id": campaign["user_id"],
                    "name": name,
                    "desync_rate": analysis["desync_rate"],
                    "total_turns": analysis["total_turns"],
                    "incident_count": len(analysis["desync_incidents"]),
                    "example_incidents": analysis["desync_incidents"][:3],
                }
            )

    # Sort by desync rate
    analyzed.sort(key=lambda x: x["desync_rate"], reverse=True)

    # Take top 3
    top_real = analyzed[:3]

    # Generate report
    report = {
        "analysis_date": datetime.now().isoformat(),
        "real_campaigns_found": len(real_campaigns),
        "real_campaigns_analyzed": len(analyzed),
        "sariel_found": sariel_found,
        "top_real_campaigns": top_real,
    }

    # Save report
    os.makedirs("analysis", exist_ok=True)
    with open("analysis/real_campaigns_0.4.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Generate markdown
    generate_markdown_report(report)

    print(f"\n✓ Found {len(top_real)} real campaigns with desync issues")
    print("✓ Report saved to analysis/real_campaigns_0.4.md")


def generate_markdown_report(report):
    """Generate markdown report for real campaigns."""
    md = f"""# Real Campaigns for Milestone 0.4 Testing

Generated: {report["analysis_date"]}

## Summary
- Real campaigns found: {report["real_campaigns_found"]}
- Campaigns analyzed: {report["real_campaigns_analyzed"]}
- Sariel v2 found: {"Yes ✓" if report["sariel_found"] else "No ❌"}

## Top 3 Real Campaigns with Desync Issues

"""

    for i, campaign in enumerate(report["top_real_campaigns"], 1):
        md += f"""### {i}. {campaign["name"]}
- **Campaign ID**: `{campaign["campaign_id"]}`
- **Desync Rate**: **{campaign["desync_rate"] * 100:.1f}%**
- **Total AI Turns**: {campaign["total_turns"]}
- **Desync Incidents**: {campaign["incident_count"]}

**Example Issues:**
"""

        for incident in campaign["example_incidents"]:
            missing = ", ".join(incident["missing_entities"])
            md += f"- Turn {incident['turn']}: Missing entities: {missing}\n"
            md += f'  - Preview: "{incident["narrative_preview"]}"\n'

        md += "\n---\n\n"

    # Save markdown
    with open("analysis/real_campaigns_0.4.md", "w") as f:
        f.write(md)


if __name__ == "__main__":
    main()
