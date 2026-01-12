#!/usr/bin/env python3
"""
Campaign Issue Diagnostic Tool

Comprehensive diagnostic script for debugging campaign-related issues, particularly
useful for investigating mobile vs desktop discrepancies, missing campaigns, and
data consistency problems.

Usage:
    # Basic campaign check
    WORLDAI_DEV_MODE=true python scripts/diagnose_campaign_issues.py \
        --user jleechan@gmail.com \
        --campaign-id bs27jWsO0jJa0MyOTQgI

    # Full diagnostic with API simulation
    WORLDAI_DEV_MODE=true python scripts/diagnose_campaign_issues.py \
        --user jleechan@gmail.com \
        --campaign-id bs27jWsO0jJa0MyOTQgI \
        --full

    # Test API endpoint (requires running server)
    WORLDAI_DEV_MODE=true python scripts/diagnose_campaign_issues.py \
        --user jleechan@gmail.com \
        --api-test \
        --base-url http://localhost:8005

    # Compare mobile vs desktop user agents
    WORLDAI_DEV_MODE=true python scripts/diagnose_campaign_issues.py \
        --user jleechan@gmail.com \
        --user-agent-test \
        --base-url http://localhost:8005
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from typing import Any

import requests

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Apply clock skew patch BEFORE importing Firebase
os.environ.setdefault('WORLDAI_DEV_MODE', 'true')
from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, credentials, firestore

from mvp_site import world_logic


class CampaignDiagnostic:
    """Comprehensive campaign diagnostic tool."""

    def __init__(self):
        """Initialize Firebase and diagnostic tools."""
        self._init_firebase()

    def _init_firebase(self):
        """Initialize Firebase Admin SDK."""
        if not firebase_admin._apps:
            creds_path = os.environ.get('WORLDAI_GOOGLE_APPLICATION_CREDENTIALS')
            if creds_path:
                creds_path = os.path.expanduser(creds_path)
                if os.path.exists(creds_path):
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                    print(f"✅ Firebase initialized with: {creds_path}")
                else:
                    firebase_admin.initialize_app()
            else:
                firebase_admin.initialize_app()

        self.db = firestore.client()

    def find_user_by_email(self, email: str) -> dict[str, Any]:
        """Find Firebase user by email and return user info."""
        try:
            user_record = auth.get_user_by_email(email)
            return {
                'email': user_record.email,
                'uid': user_record.uid,
                'email_verified': user_record.email_verified,
                'creation_timestamp': user_record.user_metadata.creation_timestamp,
                'last_sign_in_timestamp': user_record.user_metadata.last_sign_in_timestamp,
            }
        except auth.UserNotFoundError:
            return None

    def check_campaign_exists(self, user_id: str, campaign_id: str) -> dict[str, Any]:
        """Check if a specific campaign exists in Firestore."""
        print(f"\n{'='*80}")
        print(f"CHECKING CAMPAIGN EXISTENCE")
        print(f"{'='*80}")
        print(f"User ID: {user_id}")
        print(f"Campaign ID: {campaign_id}")

        doc_ref = (
            self.db.collection('users')
            .document(user_id)
            .collection('campaigns')
            .document(campaign_id)
        )

        try:
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                print(f"✅ Campaign EXISTS in Firestore")
                print(f"   Title: {data.get('title', 'N/A')}")
                print(f"   Created: {data.get('created_at', 'N/A')}")
                print(f"   Last Played: {data.get('last_played', 'N/A')}")
                return {'exists': True, 'data': data}
            else:
                print(f"❌ Campaign DOES NOT EXIST in Firestore")
                return {'exists': False, 'data': None}
        except Exception as e:
            print(f"❌ Error checking campaign: {e}")
            return {'exists': False, 'error': str(e)}

    def count_user_campaigns(self, user_id: str) -> int:
        """Count total campaigns for a user."""
        campaigns_ref = (
            self.db.collection('users').document(user_id).collection('campaigns')
        )
        count = len(list(campaigns_ref.stream()))
        return count

    async def test_backend_api_simulation(
        self, user_id: str, campaign_id: str = None
    ) -> dict[str, Any]:
        """Simulate backend API call to get campaigns list."""
        print(f"\n{'='*80}")
        print(f"TESTING BACKEND API SIMULATION")
        print(f"{'='*80}")
        print(f"User ID: {user_id}")

        request_data = {
            'user_id': user_id,
            'limit': None,
            'sort_by': 'last_played',
        }

        try:
            result = await world_logic.get_campaigns_list_unified(request_data)

            if not result.get('success'):
                print(f"❌ API Simulation FAILED: {result.get('error')}")
                return result

            campaigns = result.get('campaigns', [])
            print(f"✅ API Simulation SUCCESS")
            print(f"   Total campaigns returned: {len(campaigns)}")

            # Check if target campaign is present
            if campaign_id:
                found_index = None
                for i, c in enumerate(campaigns):
                    if c.get('id') == campaign_id:
                        found_index = i
                        break

                if found_index is not None:
                    print(f"✅ Target campaign '{campaign_id}' FOUND at index {found_index}")
                    campaign = campaigns[found_index]
                    print(f"   Title: {campaign.get('title')}")
                    print(f"   Last Played: {campaign.get('last_played')}")
                else:
                    print(f"❌ Target campaign '{campaign_id}' NOT FOUND in response")

            # Show first 10 campaigns
            print(f"\n📋 First 10 Campaigns (sorted by last_played DESC):")
            for i, c in enumerate(campaigns[:10], 1):
                marker = '🎯' if campaign_id and c.get('id') == campaign_id else '  '
                last_played = c.get('last_played', 'N/A')[:19] if c.get('last_played') else 'N/A'
                title = c.get('title', 'N/A')[:50]
                cid = c.get('id', 'N/A')
                print(f"   {marker} {i:2d}. {last_played} | {title} ({cid})")

            return {
                'success': True,
                'total_campaigns': len(campaigns),
                'target_found': campaign_id in [c.get('id') for c in campaigns] if campaign_id else None,
                'campaigns': campaigns[:10],  # Return first 10 for inspection
            }
        except Exception as e:
            print(f"❌ API Simulation ERROR: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}

    def test_api_endpoint(
        self,
        base_url: str,
        user_id: str,
        user_agent: str = None,
        campaign_id: str = None,
    ) -> dict[str, Any]:
        """Test actual API endpoint (requires running server)."""
        print(f"\n{'='*80}")
        print(f"TESTING API ENDPOINT")
        print(f"{'='*80}")
        print(f"Base URL: {base_url}")
        print(f"User ID: {user_id}")
        if user_agent:
            print(f"User-Agent: {user_agent[:80]}...")

        url = f"{base_url.rstrip('/')}/api/campaigns"
        headers = {
            'X-Test-Bypass-Auth': 'true',
            'X-Test-User-ID': user_id,
            'Content-Type': 'application/json',
        }

        if user_agent:
            headers['User-Agent'] = user_agent

        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                campaigns = data.get('campaigns', data if isinstance(data, list) else [])
                print(f"✅ API Request SUCCESS")
                print(f"   Total campaigns returned: {len(campaigns)}")

                if campaign_id:
                    found = any(c.get('id') == campaign_id for c in campaigns)
                    if found:
                        print(f"✅ Target campaign '{campaign_id}' FOUND")
                    else:
                        print(f"❌ Target campaign '{campaign_id}' NOT FOUND")

                # Show first 5 campaigns
                print(f"\n📋 First 5 Campaigns:")
                for i, c in enumerate(campaigns[:5], 1):
                    marker = '🎯' if campaign_id and c.get('id') == campaign_id else '  '
                    title = c.get('title', 'N/A')[:50]
                    cid = c.get('id', 'N/A')
                    print(f"   {marker} {i}. {title} ({cid})")

                return {
                    'success': True,
                    'status_code': response.status_code,
                    'total_campaigns': len(campaigns),
                    'target_found': campaign_id in [c.get('id') for c in campaigns] if campaign_id else None,
                }
            else:
                print(f"❌ API Request FAILED: {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response.text[:500],
                }
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error: Could not connect to {base_url}")
            print(f"   Make sure server is running with TESTING_AUTH_BYPASS=true")
            return {'success': False, 'error': 'Connection failed'}
        except Exception as e:
            print(f"❌ API Request ERROR: {e}")
            return {'success': False, 'error': str(e)}

    def compare_user_agents(
        self, base_url: str, user_id: str, campaign_id: str = None
    ):
        """Compare API responses with different user agents."""
        print(f"\n{'='*80}")
        print(f"COMPARING USER AGENTS")
        print(f"{'='*80}")

        desktop_ua = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        mobile_ua = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        )

        print("\n📱 Testing MOBILE User-Agent...")
        mobile_result = self.test_api_endpoint(
            base_url, user_id, mobile_ua, campaign_id
        )

        print("\n🖥️  Testing DESKTOP User-Agent...")
        desktop_result = self.test_api_endpoint(
            base_url, user_id, desktop_ua, campaign_id
        )

        # Compare results
        print(f"\n{'='*80}")
        print(f"COMPARISON RESULTS")
        print(f"{'='*80}")
        print(f"Desktop: {desktop_result.get('total_campaigns', 0)} campaigns")
        print(f"Mobile:  {mobile_result.get('total_campaigns', 0)} campaigns")

        if desktop_result.get('total_campaigns') != mobile_result.get('total_campaigns'):
            print(
                f"\n⚠️  DIFFERENCE DETECTED: "
                f"Desktop has {desktop_result.get('total_campaigns')} campaigns, "
                f"Mobile has {mobile_result.get('total_campaigns')}"
            )

        if campaign_id:
            desktop_found = desktop_result.get('target_found')
            mobile_found = mobile_result.get('target_found')
            if desktop_found != mobile_found:
                print(
                    f"\n⚠️  TARGET CAMPAIGN DIFFERENCE: "
                    f"Desktop found={desktop_found}, Mobile found={mobile_found}"
                )

    async def run_full_diagnostic(
        self, email: str, campaign_id: str = None, base_url: str = None
    ):
        """Run comprehensive diagnostic suite."""
        print(f"\n{'='*80}")
        print(f"CAMPAIGN ISSUE DIAGNOSTIC TOOL")
        print(f"{'='*80}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"User Email: {email}")
        if campaign_id:
            print(f"Campaign ID: {campaign_id}")

        # Step 1: Find user
        print(f"\n{'='*80}")
        print(f"STEP 1: Finding user...")
        print(f"{'='*80}")
        user_info = self.find_user_by_email(email)
        if not user_info:
            print(f"❌ User not found: {email}")
            return

        user_id = user_info['uid']
        print(f"✅ User found: {user_info['email']} (UID: {user_id})")

        # Step 2: Count total campaigns
        print(f"\n{'='*80}")
        print(f"STEP 2: Counting campaigns...")
        print(f"{'='*80}")
        total_count = self.count_user_campaigns(user_id)
        print(f"Total campaigns in Firestore: {total_count}")

        # Step 3: Check specific campaign if provided
        if campaign_id:
            print(f"\n{'='*80}")
            print(f"STEP 3: Checking specific campaign...")
            print(f"{'='*80}")
            self.check_campaign_exists(user_id, campaign_id)

        # Step 4: Test backend API simulation
        print(f"\n{'='*80}")
        print(f"STEP 4: Testing backend API simulation...")
        print(f"{'='*80}")
        await self.test_backend_api_simulation(user_id, campaign_id)

        # Step 5: Test API endpoint if base_url provided
        if base_url:
            print(f"\n{'='*80}")
            print(f"STEP 5: Testing API endpoint...")
            print(f"{'='*80}")
            self.test_api_endpoint(base_url, user_id, campaign_id=campaign_id)

            # Step 6: Compare user agents if base_url provided
            print(f"\n{'='*80}")
            print(f"STEP 6: Comparing user agents...")
            print(f"{'='*80}")
            self.compare_user_agents(base_url, user_id, campaign_id)

        print(f"\n{'='*80}")
        print(f"DIAGNOSTIC COMPLETE")
        print(f"{'='*80}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Campaign Issue Diagnostic Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        '--user',
        required=True,
        help='User email address',
    )
    parser.add_argument(
        '--campaign-id',
        help='Specific campaign ID to check',
    )
    parser.add_argument(
        '--full',
        action='store_true',
        help='Run full diagnostic suite',
    )
    parser.add_argument(
        '--api-test',
        action='store_true',
        help='Test API endpoint (requires --base-url)',
    )
    parser.add_argument(
        '--user-agent-test',
        action='store_true',
        help='Compare mobile vs desktop user agents (requires --base-url)',
    )
    parser.add_argument(
        '--base-url',
        default='http://localhost:8005',
        help='Base URL for API testing (default: http://localhost:8005)',
    )

    args = parser.parse_args()

    diagnostic = CampaignDiagnostic()

    if args.full:
        await diagnostic.run_full_diagnostic(
            args.user, args.campaign_id, args.base_url
        )
    elif args.user_agent_test:
        user_info = diagnostic.find_user_by_email(args.user)
        if not user_info:
            print(f"❌ User not found: {args.user}")
            return
        diagnostic.compare_user_agents(
            args.base_url, user_info['uid'], args.campaign_id
        )
    elif args.api_test:
        user_info = diagnostic.find_user_by_email(args.user)
        if not user_info:
            print(f"❌ User not found: {args.user}")
            return
        diagnostic.test_api_endpoint(
            args.base_url, user_info['uid'], campaign_id=args.campaign_id
        )
    else:
        # Basic check
        user_info = diagnostic.find_user_by_email(args.user)
        if not user_info:
            print(f"❌ User not found: {args.user}")
            return

        if args.campaign_id:
            diagnostic.check_campaign_exists(user_info['uid'], args.campaign_id)

        await diagnostic.test_backend_api_simulation(
            user_info['uid'], args.campaign_id
        )


if __name__ == '__main__':
    asyncio.run(main())
