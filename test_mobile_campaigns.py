#!/usr/bin/env python3
"""
Test script to reproduce mobile campaign list issue.
Simulates a mobile user agent request to /api/campaigns endpoint.
"""

import sys
import os
import asyncio
import json
from urllib.parse import urlencode

# Set up paths
sys.path.insert(0, os.path.abspath('.'))

# Mock environment
os.environ['WORLDAI_DEV_MODE'] = 'true'
os.environ['WORLDAI_GOOGLE_APPLICATION_CREDENTIALS'] = os.path.expanduser('~/serviceAccountKey.json')

# Import app modules
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

from mvp_site import world_logic

# Define the user and campaign
uid = 'vnLp2G3m21PJL6kxcuAqmWSOtm73'
target_campaign_id = 'bs27jWsO0jJa0MyOTQgI'

async def test_campaign_fetch():
    """Test fetching campaigns as the API endpoint would."""
    print("=" * 80)
    print("MOBILE CAMPAIGN LIST REPRODUCTION TEST")
    print("=" * 80)
    
    # Simulate the exact request that frontend makes
    # Frontend calls: fetchApi('/api/campaigns') with no parameters
    request_data = {
        "user_id": uid,
        "limit": None,  # No limit parameter passed
        "sort_by": "last_played"  # Default sort
    }
    
    print(f"\n📱 Simulating mobile request:")
    print(f"   User ID: {uid}")
    print(f"   Limit: {request_data['limit']}")
    print(f"   Sort By: {request_data['sort_by']}")
    print(f"   Target Campaign: {target_campaign_id}")
    
    result = await world_logic.get_campaigns_list_unified(request_data)
    
    if not result.get("success"):
        print(f"\n❌ ERROR: {result.get('error')}")
        return
    
    campaigns = result.get("campaigns", [])
    print(f"\n✅ API Response:")
    print(f"   Total campaigns returned: {len(campaigns)}")
    
    # Check if target campaign is present
    found_index = None
    for i, c in enumerate(campaigns):
        if c.get("id") == target_campaign_id:
            found_index = i
            break
    
    if found_index is not None:
        print(f"\n✅ TARGET CAMPAIGN FOUND at index {found_index}")
        campaign = campaigns[found_index]
        print(f"   Title: {campaign.get('title')}")
        print(f"   Last Played: {campaign.get('last_played')}")
        print(f"   Created At: {campaign.get('created_at')}")
    else:
        print(f"\n❌ TARGET CAMPAIGN NOT FOUND in response!")
        print(f"   This indicates a backend filtering/pagination issue")
    
    # Show first 10 campaigns to verify sorting
    print(f"\n📋 First 10 Campaigns (sorted by last_played DESC):")
    for i, c in enumerate(campaigns[:10], 1):
        marker = "🎯" if c.get("id") == target_campaign_id else "  "
        print(f"   {marker} {i:2d}. {c.get('last_played', 'N/A')[:19]} | {c.get('title', 'N/A')[:50]} ({c.get('id')})")
    
    # Check if there's a limit being applied somewhere
    if len(campaigns) < 232:
        print(f"\n⚠️  WARNING: Only {len(campaigns)} campaigns returned, but user has 232 total!")
        print(f"   This suggests a limit is being applied somewhere.")
    
    # Test with explicit limit 100 (common default)
    print(f"\n" + "=" * 80)
    print("TESTING WITH LIMIT=100 (Common Default)")
    print("=" * 80)
    request_data["limit"] = 100
    result_limited = await world_logic.get_campaigns_list_unified(request_data)
    if result_limited.get("success"):
        campaigns_limited = result_limited.get("campaigns", [])
        found_limited = any(c.get("id") == target_campaign_id for c in campaigns_limited)
        print(f"   With limit=100: {len(campaigns_limited)} campaigns, target found: {found_limited}")

if __name__ == "__main__":
    asyncio.run(test_campaign_fetch())
