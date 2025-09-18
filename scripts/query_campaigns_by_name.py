#!/usr/bin/env python3
"""
Query Campaigns by Name - Find campaigns with exact name match for a specific user

This script queries Firestore to find all campaigns with an exact name match
for a specific user and outputs the campaign IDs.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add mvp_site to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

import firestore_service
from custom_types import UserId


def query_campaigns_by_name(user_id: str, campaign_name: str) -> List[Dict[str, Any]]:
    """
    Query campaigns for a user with exact name match.
    
    Args:
        user_id: Firebase user ID (email)
        campaign_name: Exact campaign name to match
        
    Returns:
        List of campaign dictionaries with matching name
    """
    print(f"🔍 Querying campaigns for user: {user_id}")
    print(f"📝 Looking for campaigns named: '{campaign_name}'")
    
    # Get all campaigns for the user
    all_campaigns = firestore_service.get_campaigns_for_user(user_id)
    
    print(f"📊 Found {len(all_campaigns)} total campaigns for user")
    
    # Filter campaigns with exact name match
    matching_campaigns = []
    for campaign in all_campaigns:
        # Check if campaign has a title field that matches exactly
        campaign_title = campaign.get('title', '')
        if campaign_title == campaign_name:
            matching_campaigns.append(campaign)
            print(f"✅ Found matching campaign: {campaign['id']}")
    
    print(f"🎯 Found {len(matching_campaigns)} campaigns with exact name match")
    
    return matching_campaigns


def main():
    """Main function to execute the campaign query."""
    if len(sys.argv) != 3:
        print("Usage: python3 query_campaigns_by_name.py <user_id> <campaign_name>")
        print("Example: python3 query_campaigns_by_name.py jleechan@gmail.com 'My Epic Adventure'")
        sys.exit(1)
    
    user_id = sys.argv[1]
    campaign_name = sys.argv[2]
    
    try:
        # Query campaigns
        matching_campaigns = query_campaigns_by_name(user_id, campaign_name)
        
        # Prepare results
        results = {
            "query_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "campaign_name": campaign_name,
            "total_matches": len(matching_campaigns),
            "campaign_ids": [campaign['id'] for campaign in matching_campaigns],
            "full_campaign_data": matching_campaigns
        }
        
        # Output results as JSON
        print("\n📋 QUERY RESULTS:")
        print("=" * 50)
        print(json.dumps(results, indent=2))
        
        return results
        
    except Exception as e:
        print(f"❌ Error querying campaigns: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()