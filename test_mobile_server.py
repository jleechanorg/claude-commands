#!/usr/bin/env python3
"""
Start a local server with auth bypass to test mobile campaign list.
"""

import subprocess
import sys
import os
import time
import requests
from urllib.parse import urljoin

# Mobile user agent strings
MOBILE_USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]

DESKTOP_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

def test_campaigns_endpoint(base_url, user_id, user_agent, label):
    """Test /api/campaigns endpoint with given user agent."""
    url = urljoin(base_url, "/api/campaigns")
    headers = {
        "User-Agent": user_agent,
        "X-Test-Bypass-Auth": "true",
        "X-Test-User-ID": user_id,
        "Content-Type": "application/json",
    }
    
    print(f"\n{'='*80}")
    print(f"Testing {label}")
    print(f"{'='*80}")
    print(f"User-Agent: {user_agent[:80]}...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            campaigns = data.get("campaigns", data if isinstance(data, list) else [])
            print(f"✅ Success: {len(campaigns)} campaigns returned")
            
            # Check for target campaign
            target_id = "bs27jWsO0jJa0MyOTQgI"
            found = any(c.get("id") == target_id for c in campaigns)
            if found:
                print(f"✅ Target campaign '{target_id}' FOUND")
            else:
                print(f"❌ Target campaign '{target_id}' NOT FOUND")
            
            # Show first 5 campaigns
            print(f"\nFirst 5 campaigns:")
            for i, c in enumerate(campaigns[:5], 1):
                marker = "🎯" if c.get("id") == target_id else "  "
                print(f"  {marker} {i}. {c.get('title', 'N/A')[:50]} ({c.get('id', 'N/A')})")
            
            return len(campaigns), found
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return 0, False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return 0, False

def main():
    user_id = "vnLp2G3m21PJL6kxcuAqmWSOtm73"
    base_url = "http://localhost:8005"
    
    print("="*80)
    print("MOBILE CAMPAIGN LIST TEST")
    print("="*80)
    print(f"\nMake sure server is running with:")
    print(f"  TESTING_AUTH_BYPASS=true ./run_local_server.sh")
    print(f"\nWaiting 5 seconds for you to start server...")
    time.sleep(5)
    
    # Test desktop
    desktop_count, desktop_found = test_campaigns_endpoint(
        base_url, user_id, DESKTOP_USER_AGENT, "DESKTOP"
    )
    
    # Test mobile
    mobile_count, mobile_found = test_campaigns_endpoint(
        base_url, user_id, MOBILE_USER_AGENTS[0], "MOBILE (iPhone)"
    )
    
    # Compare results
    print(f"\n{'='*80}")
    print("COMPARISON")
    print(f"{'='*80}")
    print(f"Desktop: {desktop_count} campaigns, target found: {desktop_found}")
    print(f"Mobile:  {mobile_count} campaigns, target found: {mobile_found}")
    
    if desktop_count != mobile_count:
        print(f"\n⚠️  DIFFERENCE DETECTED: Desktop has {desktop_count} campaigns, Mobile has {mobile_count}")
    if desktop_found != mobile_found:
        print(f"\n⚠️  TARGET CAMPAIGN DIFFERENCE: Desktop found={desktop_found}, Mobile found={mobile_found}")

if __name__ == "__main__":
    main()
