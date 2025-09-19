#!/usr/bin/env python3
"""
Campaign Manager - Unified Campaign Operations Tool

This unified script provides comprehensive campaign management utilities:
- Query campaigns by exact name
- Delete campaigns with safety features
- Convert email to Firebase UID
- Batch operations with automation

Consolidates all campaign management functionality into a single, maintainable tool.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add mvp_site to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

import firebase_admin
from firebase_admin import auth, firestore
import firestore_service
from custom_types import UserId, CampaignId


class CampaignManager:
    """Unified campaign management class with all operations."""

    def __init__(self, output_dir: str = "docs"):
        """Initialize campaign manager with configurable output directory."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app()

    def find_user_by_email(self, email: str) -> Dict[str, Any]:
        """Find Firebase user by email address."""
        try:
            user_record = auth.get_user_by_email(email)

            user_info = {
                "email": user_record.email,
                "uid": user_record.uid,
                "email_verified": user_record.email_verified,
                "creation_timestamp": user_record.user_metadata.creation_timestamp,
                "last_sign_in_timestamp": user_record.user_metadata.last_sign_in_timestamp,
                "provider_data": [
                    {
                        "provider_id": provider.provider_id,
                        "uid": provider.uid,
                        "email": provider.email
                    }
                    for provider in user_record.provider_data
                ]
            }

            print(f"✅ Found user: {email}")
            print(f"🆔 Firebase UID: {user_record.uid}")

            return {
                "query_timestamp": datetime.now().isoformat(),
                "search_email": email,
                "user_found": True,
                "user_info": user_info
            }

        except auth.UserNotFoundError:
            print(f"❌ User not found: {email}")
            return {
                "query_timestamp": datetime.now().isoformat(),
                "search_email": email,
                "user_found": False,
                "user_info": None
            }

    def query_campaigns_by_name(self, user_id: str, campaign_name: str) -> Dict[str, Any]:
        """Query campaigns for a user with exact name match."""
        print(f"🔍 Querying campaigns for user: {user_id}")
        print(f"📝 Looking for campaigns named: '{campaign_name}'")

        # Get all campaigns for the user
        all_campaigns = firestore_service.get_campaigns_for_user(user_id)
        print(f"📊 Found {len(all_campaigns)} total campaigns for user")

        # Filter campaigns with exact name match
        matching_campaigns = []
        for campaign in all_campaigns:
            campaign_title = campaign.get('title', '')
            if campaign_title == campaign_name:
                matching_campaigns.append(campaign)
                print(f"✅ Found matching campaign: {campaign['id']}")

        print(f"🎯 Found {len(matching_campaigns)} campaigns with exact name match")

        return {
            "query_timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "campaign_name": campaign_name,
            "total_matches": len(matching_campaigns),
            "campaign_ids": [campaign['id'] for campaign in matching_campaigns],
            "full_campaign_data": matching_campaigns
        }

    def get_campaigns_to_delete(self, user_id: str, campaign_name: str, max_count: int = 100) -> List[Dict[str, Any]]:
        """Get campaigns that would be deleted (exact name match only)."""
        print(f"🔍 Finding campaigns for deletion...")
        print(f"👤 User: {user_id}")
        print(f"📝 Exact name: '{campaign_name}'")
        print(f"🛡️ Max count limit: {max_count}")

        # Get all campaigns for the user
        all_campaigns = firestore_service.get_campaigns_for_user(user_id)
        print(f"📊 Total campaigns for user: {len(all_campaigns)}")

        # Filter campaigns with EXACT name match (case-sensitive)
        exact_matches = []
        other_similar = []

        for campaign in all_campaigns:
            campaign_title = campaign.get('title', '')
            if campaign_title == campaign_name:  # EXACT match only
                exact_matches.append(campaign)
            elif campaign_name.lower() in campaign_title.lower():  # Similar but not exact
                other_similar.append(campaign)

        print(f"🎯 EXACT matches found: {len(exact_matches)}")
        print(f"📝 Similar (but different) titles found: {len(other_similar)}")

        # Show similar titles for safety
        if other_similar:
            print(f"\n⚠️ SIMILAR TITLES (will NOT be deleted):")
            for campaign in other_similar[:10]:  # Show first 10
                print(f"   - '{campaign.get('title', 'No Title')}' (ID: {campaign['id']})")
            if len(other_similar) > 10:
                print(f"   ... and {len(other_similar) - 10} more similar titles")

        # Apply safety limit
        if len(exact_matches) > max_count:
            print(f"⚠️ WARNING: Found {len(exact_matches)} exact matches, limiting to {max_count} for safety")
            exact_matches = exact_matches[:max_count]

        return exact_matches

    def delete_campaign_safe(self, user_id: str, campaign_id: str) -> bool:
        """Safely delete a single campaign."""
        try:
            db = firestore_service.get_db()

            # Delete the campaign document
            campaign_ref = (
                db.collection("users")
                .document(user_id)
                .collection("campaigns")
                .document(campaign_id)
            )

            # Check if campaign exists before deletion
            campaign_doc = campaign_ref.get()
            if not campaign_doc.exists:
                print(f"⚠️ Campaign {campaign_id} does not exist")
                return False

            # Delete the campaign
            campaign_ref.delete()
            print(f"✅ Deleted campaign: {campaign_id}")
            return True

        except Exception as e:
            print(f"❌ Error deleting campaign {campaign_id}: {e}")
            return False

    def delete_campaigns(self, user_id: str, campaign_name: str, dry_run: bool = True, force: bool = False, max_count: int = 100) -> Dict[str, Any]:
        """Delete campaigns with safety checks."""
        campaigns_to_delete = self.get_campaigns_to_delete(user_id, campaign_name, max_count)

        if not campaigns_to_delete:
            print("✅ No campaigns found with exact name match. Nothing to delete.")
            return {"campaigns_found": 0, "deleted": 0}

        print(f"\n📋 CAMPAIGNS TO DELETE ({len(campaigns_to_delete)}):")
        print("-" * 50)
        for i, campaign in enumerate(campaigns_to_delete[:10], 1):  # Show first 10
            last_played = campaign.get('last_played', 'Unknown')
            created_at = campaign.get('created_at', 'Unknown')
            print(f"{i:3d}. ID: {campaign['id']}")
            print(f"     Title: '{campaign.get('title', 'No Title')}'")
            print(f"     Last Played: {last_played}")
            print(f"     Created: {created_at}")
            print()

        if len(campaigns_to_delete) > 10:
            print(f"... and {len(campaigns_to_delete) - 10} more campaigns")

        # Handle dry-run mode
        if dry_run:
            print("🛡️ DRY-RUN MODE: No campaigns will be deleted.")
            print("Use --confirm flag to perform actual deletion.")

            results = {
                "dry_run": True,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "campaign_name": campaign_name,
                "campaigns_found": len(campaigns_to_delete),
                "campaign_ids": [c['id'] for c in campaigns_to_delete],
                "would_delete": len(campaigns_to_delete)
            }

            output_file = os.path.join(self.output_dir, "deletion_preview.json")
            print(f"📁 Saving dry-run results to {output_file}")
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)

            return results

        # Final confirmation for actual deletion
        print("⚠️ WARNING: THIS WILL PERMANENTLY DELETE CAMPAIGNS!")
        print(f"You are about to delete {len(campaigns_to_delete)} campaigns.")

        if not force:
            confirmation = input("Type 'DELETE' to confirm (case-sensitive): ")
            if confirmation != "DELETE":
                print("❌ Deletion cancelled. You must type 'DELETE' exactly.")
                return {"cancelled": True}
        else:
            print("🔥 --force flag detected, skipping interactive confirmation")

        # Perform actual deletion
        print(f"\n🗑️ Starting deletion of {len(campaigns_to_delete)} campaigns...")

        deleted_count = 0
        failed_count = 0
        deleted_ids = []
        failed_ids = []

        for i, campaign in enumerate(campaigns_to_delete, 1):
            campaign_id = campaign['id']
            print(f"Deleting {i}/{len(campaigns_to_delete)}: {campaign_id}... ", end="", flush=True)

            if self.delete_campaign_safe(user_id, campaign_id):
                deleted_count += 1
                deleted_ids.append(campaign_id)
            else:
                failed_count += 1
                failed_ids.append(campaign_id)

            # Small delay for safety
            time.sleep(0.1)

        # Results summary
        print(f"\n📊 DELETION SUMMARY:")
        print(f"✅ Successfully deleted: {deleted_count}")
        print(f"❌ Failed to delete: {failed_count}")
        print(f"📈 Total processed: {len(campaigns_to_delete)}")

        # Save deletion results
        results = {
            "deletion_completed": True,
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "campaign_name": campaign_name,
            "total_found": len(campaigns_to_delete),
            "successfully_deleted": deleted_count,
            "failed_to_delete": failed_count,
            "deleted_campaign_ids": deleted_ids,
            "failed_campaign_ids": failed_ids
        }

        output_file = os.path.join(self.output_dir, "deletion_results.json")
        print(f"📁 Saving deletion results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)

        print("✅ Deletion process completed.")
        return results


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(
        description="Campaign Manager - Unified campaign operations tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find user by email
  %(prog)s find-user [EXAMPLE_EMAIL]

  # Query campaigns by name
  %(prog)s query [EXAMPLE_UID] "My Epic Adventure"

  # Dry-run deletion
  %(prog)s delete [EXAMPLE_UID] "My Epic Adventure"

  # Actual deletion with confirmation
  %(prog)s delete [EXAMPLE_UID] "My Epic Adventure" --confirm

  # Force deletion without interactive prompt
  %(prog)s delete [EXAMPLE_UID] "My Epic Adventure" --confirm --force
        """
    )

    parser.add_argument('--output-dir', default=os.environ.get("OUTPUT_DIR", "docs"),
                        help='Output directory for results (default: docs)')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Find user command
    find_parser = subparsers.add_parser('find-user', help='Find Firebase UID by email')
    find_parser.add_argument('email', help='User email address')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query campaigns by exact name')
    query_parser.add_argument('user_id', help='Firebase user ID')
    query_parser.add_argument('campaign_name', help='Exact campaign name to search for')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete campaigns by exact name')
    delete_parser.add_argument('user_id', help='Firebase user ID')
    delete_parser.add_argument('campaign_name', help='Exact campaign name to delete')
    delete_parser.add_argument('--confirm', action='store_true', help='Perform actual deletion')
    delete_parser.add_argument('--force', action='store_true', help='Skip interactive confirmation')
    delete_parser.add_argument('--max-count', type=int, default=100, help='Maximum campaigns per batch')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        manager = CampaignManager(output_dir=args.output_dir)

        if args.command == 'find-user':
            result = manager.find_user_by_email(args.email)
            print("\n📋 USER LOOKUP RESULTS:")
            print("=" * 50)
            print(json.dumps(result, indent=2, default=str))

        elif args.command == 'query':
            result = manager.query_campaigns_by_name(args.user_id, args.campaign_name)
            print("\n📋 QUERY RESULTS:")
            print("=" * 50)
            print(json.dumps(result, indent=2))

        elif args.command == 'delete':
            dry_run = not args.confirm
            result = manager.delete_campaigns(
                args.user_id,
                args.campaign_name,
                dry_run=dry_run,
                force=args.force,
                max_count=args.max_count
            )

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
