#!/usr/bin/env python3
"""
Dice Roll Audit Script

Audits dice rolls from a specific campaign by ID using collection group queries.
Extracts dice roll data from story entries and provides statistical analysis.

Usage:
    python scripts/audit_dice_rolls.py <campaign_id>

Example:
    python scripts/audit_dice_rolls.py tAE30bFvyfO0rUd9cgyv
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from statistics import mean, stdev

# Apply clock skew patch BEFORE importing firebase_admin
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials, firestore


def initialize_firebase():
    """Initialize Firebase connection."""
    if not firebase_admin._apps:
        try:
            # Try WORLDAI_GOOGLE_APPLICATION_CREDENTIALS first
            cred_path = os.environ.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
            if not cred_path:
                # Fallback to ~/serviceAccountKey.json
                cred_path = os.path.expanduser("~/serviceAccountKey.json")

            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                print(f"Firebase initialized with: {cred_path}")
            else:
                firebase_admin.initialize_app()
                print("Firebase initialized with default credentials")
        except Exception as e:
            print(f"Failed to initialize Firebase: {e}")
            raise

    return firestore.client()


def find_campaign_by_id(db, campaign_id: str):
    """Find a campaign across all users using collection group query."""
    print(f"\nSearching for campaign: {campaign_id}")

    campaigns_group = db.collection_group("campaigns")

    for campaign_doc in campaigns_group.stream():
        if campaign_doc.id == campaign_id:
            # Extract user ID from path: users/{user_id}/campaigns/{campaign_id}
            path_parts = campaign_doc.reference.path.split("/")
            if len(path_parts) >= 4 and path_parts[0] == "users":
                user_id = path_parts[1]
                return user_id, campaign_doc.to_dict()

    return None, None


def get_story_entries(db, user_id: str, campaign_id: str):
    """Get all story entries for a campaign."""
    story_ref = (
        db.collection("users")
        .document(user_id)
        .collection("campaigns")
        .document(campaign_id)
        .collection("story")
        .order_by("timestamp")
    )

    entries = []
    for doc in story_ref.stream():
        entry = doc.to_dict()
        entry["doc_id"] = doc.id
        entries.append(entry)

    return entries


def extract_dice_rolls_from_text(text: str):
    """Extract dice roll patterns from narrative text."""
    rolls = []

    # Pattern: "rolls a d20" or "rolled a 15" or "d20 roll: 15"
    d20_pattern = r'd20[^0-9]*(?:roll[^\d]*)?(\d+)'
    # Pattern: "1d6" or "2d8" style
    dice_pattern = r'(\d+)d(\d+)[^0-9]*(?:roll[^\d]*)?(\d+)?'
    # Pattern: "rolled 15" or "result: 15"
    result_pattern = r'(?:roll(?:ed)?|result)[^\d]*(\d+)'

    # Look for explicit dice notation with results
    for match in re.finditer(dice_pattern, text, re.IGNORECASE):
        num_dice = int(match.group(1))
        die_type = int(match.group(2))
        result = int(match.group(3)) if match.group(3) else None
        rolls.append({
            "notation": f"{num_dice}d{die_type}",
            "num_dice": num_dice,
            "die_type": die_type,
            "result": result,
            "source": "text_pattern"
        })

    return rolls


def extract_dice_from_structured_fields(entry: dict):
    """Extract dice roll data from structured fields in story entries."""
    rolls = []

    # Check for structured_fields containing dice data
    structured = entry.get("structured_fields", {})
    if not structured:
        structured = {}

    # Check for dice_rolls field
    dice_rolls = structured.get("dice_rolls", [])
    if isinstance(dice_rolls, list):
        for roll in dice_rolls:
            rolls.append({
                "notation": roll.get("notation", "unknown"),
                "result": roll.get("result"),
                "purpose": roll.get("purpose", ""),
                "source": "structured_fields"
            })

    # Check for combat-related dice
    combat = structured.get("combat", {})
    if isinstance(combat, dict):
        attack_rolls = combat.get("attack_rolls", [])
        if isinstance(attack_rolls, list):
            for roll in attack_rolls:
                rolls.append({
                    "notation": "d20",
                    "result": roll.get("roll"),
                    "purpose": f"attack by {roll.get('attacker', 'unknown')}",
                    "source": "combat_attack"
                })

        damage_rolls = combat.get("damage_rolls", [])
        if isinstance(damage_rolls, list):
            for roll in damage_rolls:
                rolls.append({
                    "notation": roll.get("dice", "unknown"),
                    "result": roll.get("total"),
                    "purpose": f"damage by {roll.get('source', 'unknown')}",
                    "source": "combat_damage"
                })

    # Check for tool_calls that might contain dice results
    tool_calls = entry.get("tool_calls", [])
    if isinstance(tool_calls, list):
        for tool in tool_calls:
            if isinstance(tool, dict):
                name = tool.get("name", "")
                if "dice" in name.lower() or "roll" in name.lower():
                    result = tool.get("result", {})
                    if isinstance(result, dict):
                        rolls.append({
                            "notation": result.get("notation", "unknown"),
                            "result": result.get("total") or result.get("result"),
                            "individual_rolls": result.get("rolls", []),
                            "purpose": tool.get("purpose", ""),
                            "source": "tool_call"
                        })

    return rolls


def analyze_dice_distribution(rolls: list, die_type: int):
    """Analyze the distribution of dice rolls for a specific die type."""
    results = [r["result"] for r in rolls if r.get("result") is not None]

    if not results:
        return None

    # Expected mean for fair die
    expected_mean = (1 + die_type) / 2

    analysis = {
        "die_type": f"d{die_type}",
        "total_rolls": len(results),
        "results": results,
        "min": min(results),
        "max": max(results),
        "mean": mean(results),
        "expected_mean": expected_mean,
        "deviation_from_expected": mean(results) - expected_mean,
    }

    if len(results) > 1:
        analysis["stdev"] = stdev(results)

    # Count distribution
    distribution = defaultdict(int)
    for r in results:
        distribution[r] += 1
    analysis["distribution"] = dict(sorted(distribution.items()))

    # Check for suspicious patterns
    analysis["warnings"] = []

    # Too many high/low rolls
    high_threshold = die_type * 0.8
    low_threshold = die_type * 0.2
    high_count = sum(1 for r in results if r >= high_threshold)
    low_count = sum(1 for r in results if r <= low_threshold)

    if len(results) >= 10:
        if high_count / len(results) > 0.4:
            analysis["warnings"].append(f"High proportion of high rolls: {high_count}/{len(results)}")
        if low_count / len(results) > 0.4:
            analysis["warnings"].append(f"High proportion of low rolls: {low_count}/{len(results)}")

    # Check for impossible values
    impossible = [r for r in results if r < 1 or r > die_type]
    if impossible:
        analysis["warnings"].append(f"Impossible values detected: {impossible}")

    return analysis


def audit_campaign_dice(campaign_id: str):
    """Main function to audit dice rolls for a campaign."""
    db = initialize_firebase()

    # Find campaign
    user_id, campaign_data = find_campaign_by_id(db, campaign_id)

    if not user_id:
        print(f"Campaign not found: {campaign_id}")
        return

    print(f"\n{'='*60}")
    print(f"CAMPAIGN DICE ROLL AUDIT")
    print(f"{'='*60}")
    print(f"Campaign ID: {campaign_id}")
    print(f"Campaign Title: {campaign_data.get('title', 'Untitled')}")
    print(f"User ID: {user_id}")
    print(f"Created: {campaign_data.get('created_at', 'Unknown')}")
    print(f"{'='*60}")

    # Get story entries
    entries = get_story_entries(db, user_id, campaign_id)
    print(f"\nTotal story entries: {len(entries)}")

    # Extract all dice rolls
    all_rolls = []
    entries_with_dice = 0

    for entry in entries:
        entry_rolls = []

        # Extract from structured fields
        structured_rolls = extract_dice_from_structured_fields(entry)
        entry_rolls.extend(structured_rolls)

        # Extract from text (if AI response)
        if entry.get("actor") == "gemini":
            text = entry.get("text", "")
            text_rolls = extract_dice_rolls_from_text(text)
            entry_rolls.extend(text_rolls)

        if entry_rolls:
            entries_with_dice += 1
            for roll in entry_rolls:
                roll["timestamp"] = entry.get("timestamp")
                roll["sequence_id"] = entry.get("sequence_id")
            all_rolls.extend(entry_rolls)

    print(f"Entries with dice rolls: {entries_with_dice}")
    print(f"Total dice rolls found: {len(all_rolls)}")

    if not all_rolls:
        print("\n No dice rolls found in this campaign.")
        print("This might mean:")
        print("  - Dice rolls are not being logged in structured_fields")
        print("  - The campaign doesn't use dice mechanics")
        print("  - Dice data is stored in a different format")

        # Show sample entry structure
        if entries:
            print("\n Sample entry structure (first AI response):")
            for entry in entries[:10]:
                if entry.get("actor") == "gemini":
                    print(json.dumps({
                        "actor": entry.get("actor"),
                        "keys": list(entry.keys()),
                        "has_structured_fields": "structured_fields" in entry,
                        "has_tool_calls": "tool_calls" in entry,
                        "text_preview": entry.get("text", "")[:200] + "..."
                    }, indent=2))
                    break
        return

    # Analyze by die type
    print(f"\n{'='*60}")
    print("DICE ROLL ANALYSIS")
    print(f"{'='*60}")

    # Group by die type
    by_die_type = defaultdict(list)
    for roll in all_rolls:
        notation = roll.get("notation", "unknown")
        # Extract die type from notation like "1d20", "2d6", etc.
        match = re.search(r'd(\d+)', notation)
        if match:
            die_type = int(match.group(1))
            by_die_type[die_type].append(roll)
        else:
            by_die_type["unknown"].append(roll)

    for die_type, rolls in sorted(by_die_type.items(), key=lambda x: str(x[0])):
        if isinstance(die_type, int):
            analysis = analyze_dice_distribution(rolls, die_type)
            if analysis:
                print(f"\n--- d{die_type} Analysis ---")
                print(f"Total rolls: {analysis['total_rolls']}")
                print(f"Range: {analysis['min']} - {analysis['max']}")
                print(f"Mean: {analysis['mean']:.2f} (expected: {analysis['expected_mean']:.2f})")
                print(f"Deviation: {analysis['deviation_from_expected']:+.2f}")
                if "stdev" in analysis:
                    print(f"Std Dev: {analysis['stdev']:.2f}")
                print(f"Distribution: {analysis['distribution']}")

                if analysis["warnings"]:
                    print("\n WARNINGS:")
                    for w in analysis["warnings"]:
                        print(f"  - {w}")
        else:
            print(f"\n--- Unknown notation rolls: {len(rolls)} ---")

    # Show recent rolls
    print(f"\n{'='*60}")
    print("RECENT DICE ROLLS (last 20)")
    print(f"{'='*60}")

    recent = sorted(all_rolls, key=lambda x: x.get("timestamp", ""), reverse=True)[:20]
    for roll in recent:
        print(f"  {roll.get('notation', '?'):>8} = {roll.get('result', '?'):>3} | {roll.get('purpose', 'N/A')[:40]} | {roll.get('source', 'N/A')}")

    # Summary
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print(f"{'='*60}")

    total_with_results = len([r for r in all_rolls if r.get("result") is not None])
    print(f"Total rolls with results: {total_with_results}/{len(all_rolls)}")

    by_source = defaultdict(int)
    for roll in all_rolls:
        by_source[roll.get("source", "unknown")] += 1
    print(f"By source: {dict(by_source)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audit_dice_rolls.py <campaign_id>")
        print("Example: python audit_dice_rolls.py tAE30bFvyfO0rUd9cgyv")
        sys.exit(1)

    campaign_id = sys.argv[1]
    audit_campaign_dice(campaign_id)
