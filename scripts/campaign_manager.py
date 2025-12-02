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
from typing import Any

# Add mvp_site to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

# Apply clock skew patch BEFORE importing Firebase (handles time sync issues)
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth

import firestore_service


class CampaignManager:
    """Unified campaign management class with all operations."""

    def __init__(self, output_dir: str = "docs"):
        """Initialize campaign manager with configurable output directory."""
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Initialize Firebase with explicit credentials if not already done
        if not firebase_admin._apps:
            # Try WORLDAI credentials first, then fall back to default
            creds_path = os.environ.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path:
                creds_path = os.path.expanduser(creds_path)
                if os.path.exists(creds_path):
                    from firebase_admin import credentials
                    cred = credentials.Certificate(creds_path)
                    firebase_admin.initialize_app(cred)
                    print(f"✅ Firebase initialized with: {creds_path}")
                else:
                    firebase_admin.initialize_app()
            else:
                firebase_admin.initialize_app()

    def find_user_by_email(self, email: str) -> dict[str, Any]:
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

    def query_campaigns_by_name(self, user_id: str, campaign_name: str) -> dict[str, Any]:
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

    def get_campaigns_to_delete(self, user_id: str, campaign_name: str, max_count: int = 100) -> list[dict[str, Any]]:
        """Get campaigns that would be deleted (exact name match only)."""
        print("🔍 Finding campaigns for deletion...")
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
            print("\n⚠️ SIMILAR TITLES (will NOT be deleted):")
            for campaign in other_similar[:10]:  # Show first 10
                print(f"   - '{campaign.get('title', 'No Title')}' (ID: {campaign['id']})")
            if len(other_similar) > 10:
                print(f"   ... and {len(other_similar) - 10} more similar titles")

        # Apply safety limit
        if len(exact_matches) > max_count:
            print(f"⚠️ WARNING: Found {len(exact_matches)} exact matches, limiting to {max_count} for safety")
            exact_matches = exact_matches[:max_count]

        return exact_matches

    def analyze_user_activity(self, email: str, month: str | None = None) -> dict[str, Any]:
        """Analyze user's campaign activity with token usage estimation.

        Args:
            email: User's email address
            month: Optional month filter in YYYY-MM format (e.g., '2025-11')

        Returns:
            Detailed analytics including campaigns, entries, and token estimates
        """
        from collections import defaultdict

        # Find user by email
        user_info = self.find_user_by_email(email)
        if not user_info.get("user_found"):
            return {"error": f"User not found: {email}"}

        uid = user_info["user_info"]["uid"]
        print(f"\n📊 Analyzing activity for UID: {uid}")

        # Get Firestore client
        db = firestore_service.get_db()
        campaigns_ref = db.collection("users").document(uid).collection("campaigns")
        campaigns = list(campaigns_ref.stream())

        print(f"📁 Total campaigns: {len(campaigns)}")

        # Token estimation constants (from llm_service.py)
        BASE_TOKENS = 43000  # System instructions
        WORLD_TOKENS_ESTIMATE = 50000  # Conservative estimate
        TOKENS_PER_TURN = 500  # Average per story entry
        MAX_HISTORY_TURNS = 100  # Truncation limit

        # Organize by month
        by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in campaigns:
            data = c.to_dict()
            activity_date = data.get("last_played") or data.get("created_at")
            if activity_date:
                if hasattr(activity_date, "timestamp"):
                    dt = datetime.fromtimestamp(activity_date.timestamp())
                else:
                    dt = activity_date
                month_key = dt.strftime("%Y-%m")
                by_month[month_key].append({
                    "id": c.id,
                    "title": data.get("title", "Untitled"),
                    "last_played": dt,
                    "created_at": data.get("created_at"),
                })

        # Filter to specific month if requested
        months_to_analyze = [month] if month else sorted(by_month.keys(), reverse=True)[:3]

        results: dict[str, Any] = {
            "email": email,
            "uid": uid,
            "total_campaigns": len(campaigns),
            "analysis_timestamp": datetime.now().isoformat(),
            "months": {},
        }

        for m in months_to_analyze:
            if m not in by_month:
                continue

            month_data: dict[str, Any] = {
                "campaigns": [],
                "total_entries": 0,
                "estimated_input_tokens": 0,
                "estimated_cost_short": 0.0,
                "estimated_cost_long": 0.0,
            }

            for camp_info in by_month[m]:
                # Count story entries
                story_ref = campaigns_ref.document(camp_info["id"]).collection("story")
                entry_count = sum(1 for _ in story_ref.stream())

                # Estimate tokens for this campaign
                # Each API call includes context that grows with history (capped at MAX_HISTORY_TURNS)
                camp_tokens = 0
                for i in range(entry_count):
                    history_tokens = min(i, MAX_HISTORY_TURNS) * TOKENS_PER_TURN
                    request_tokens = BASE_TOKENS + WORLD_TOKENS_ESTIMATE + history_tokens
                    camp_tokens += request_tokens

                month_data["campaigns"].append({
                    "id": camp_info["id"],
                    "title": camp_info["title"][:50],
                    "entries": entry_count,
                    "estimated_tokens": camp_tokens,
                    "last_played": camp_info["last_played"].strftime("%Y-%m-%d %H:%M"),
                })
                month_data["total_entries"] += entry_count
                month_data["estimated_input_tokens"] += camp_tokens

            # Calculate cost estimates
            tokens_m = month_data["estimated_input_tokens"] / 1_000_000
            month_data["estimated_cost_short"] = round(tokens_m * 2.0, 2)  # $2/M
            month_data["estimated_cost_long"] = round(tokens_m * 4.0, 2)   # $4/M

            results["months"][m] = month_data
            print(f"\n📅 {m}: {len(month_data['campaigns'])} campaigns, "
                  f"{month_data['total_entries']} entries, "
                  f"~{month_data['estimated_input_tokens']:,} tokens")

        return results

    def estimate_campaign_costs(self, email: str, month: str | None = None, top_n: int = 20) -> dict[str, Any]:
        """Estimate per-campaign costs sorted by most expensive.

        Args:
            email: User's email address
            month: Optional month filter in YYYY-MM format (e.g., '2025-11')
            top_n: Number of top campaigns to show (default 20)

        Returns:
            Detailed per-campaign cost breakdown sorted by cost
        """
        from collections import defaultdict

        # Find user by email
        user_info = self.find_user_by_email(email)
        if not user_info.get("user_found"):
            return {"error": f"User not found: {email}"}

        uid = user_info["user_info"]["uid"]
        print(f"\n💰 Estimating per-campaign costs for UID: {uid}")

        # Get Firestore client
        db = firestore_service.get_db()
        campaigns_ref = db.collection("users").document(uid).collection("campaigns")
        campaigns = list(campaigns_ref.stream())

        print(f"📁 Total campaigns: {len(campaigns)}")

        # Token estimation constants (from llm_service.py)
        BASE_TOKENS = 43000  # System instructions
        WORLD_TOKENS_ESTIMATE = 50000  # Conservative world content estimate
        TOKENS_PER_TURN = 500  # Average tokens per story entry
        MAX_HISTORY_TURNS = 100  # Truncation limit (TURNS_TO_KEEP_AT_START + TURNS_TO_KEEP_AT_END)

        # Pricing (Gemini 3 Pro per 1M tokens)
        SHORT_CONTEXT_INPUT = 2.0   # $2/M for ≤200K tokens
        LONG_CONTEXT_INPUT = 4.0    # $4/M for >200K tokens
        SHORT_CONTEXT_OUTPUT = 12.0 # $12/M for ≤200K tokens
        LONG_CONTEXT_OUTPUT = 18.0  # $18/M for >200K tokens
        CONTEXT_THRESHOLD = 200_000 # 200K token threshold

        # Average output tokens per response (conservative estimate)
        AVG_OUTPUT_TOKENS = 800

        campaign_costs: list[dict[str, Any]] = []

        for c in campaigns:
            data = c.to_dict()
            campaign_id = c.id
            title = data.get("title", "Untitled")

            # Get activity date for filtering
            activity_date = data.get("last_played") or data.get("created_at")
            if activity_date:
                if hasattr(activity_date, "timestamp"):
                    dt = datetime.fromtimestamp(activity_date.timestamp())
                else:
                    dt = activity_date
                month_key = dt.strftime("%Y-%m")
            else:
                month_key = "unknown"
                dt = None

            # Skip if month filter is set and doesn't match
            if month and month_key != month:
                continue

            # Count story entries
            story_ref = campaigns_ref.document(campaign_id).collection("story")
            entries = list(story_ref.stream())
            entry_count = len(entries)

            if entry_count == 0:
                continue  # Skip campaigns with no entries

            # Calculate token usage for this campaign
            # Each API call includes growing context (capped at MAX_HISTORY_TURNS)
            total_input_tokens = 0
            total_output_tokens = 0
            short_context_requests = 0
            long_context_requests = 0

            for i in range(entry_count):
                # History tokens grow with each turn (capped)
                history_tokens = min(i, MAX_HISTORY_TURNS) * TOKENS_PER_TURN
                request_tokens = BASE_TOKENS + WORLD_TOKENS_ESTIMATE + history_tokens

                total_input_tokens += request_tokens
                total_output_tokens += AVG_OUTPUT_TOKENS

                if request_tokens > CONTEXT_THRESHOLD:
                    long_context_requests += 1
                else:
                    short_context_requests += 1

            # Calculate costs
            short_input_cost = (total_input_tokens / 1_000_000) * SHORT_CONTEXT_INPUT
            long_input_cost = (total_input_tokens / 1_000_000) * LONG_CONTEXT_INPUT
            short_output_cost = (total_output_tokens / 1_000_000) * SHORT_CONTEXT_OUTPUT
            long_output_cost = (total_output_tokens / 1_000_000) * LONG_CONTEXT_OUTPUT

            # Blended cost based on actual context sizes
            short_ratio = short_context_requests / entry_count if entry_count > 0 else 1.0
            long_ratio = long_context_requests / entry_count if entry_count > 0 else 0.0

            blended_input_cost = (short_ratio * short_input_cost) + (long_ratio * long_input_cost)
            blended_output_cost = (short_ratio * short_output_cost) + (long_ratio * long_output_cost)
            total_blended_cost = blended_input_cost + blended_output_cost

            campaign_costs.append({
                "campaign_id": campaign_id,
                "title": title[:60],
                "month": month_key,
                "last_played": dt.strftime("%Y-%m-%d %H:%M") if dt else "unknown",
                "entry_count": entry_count,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "short_context_requests": short_context_requests,
                "long_context_requests": long_context_requests,
                "cost_short_context": round(short_input_cost + short_output_cost, 4),
                "cost_long_context": round(long_input_cost + long_output_cost, 4),
                "cost_blended": round(total_blended_cost, 4),
                "avg_context_size": int(total_input_tokens / entry_count) if entry_count > 0 else 0,
            })

        # Sort by blended cost (most expensive first)
        campaign_costs.sort(key=lambda x: x["cost_blended"], reverse=True)

        # Calculate totals
        total_entries = sum(c["entry_count"] for c in campaign_costs)
        total_input = sum(c["total_input_tokens"] for c in campaign_costs)
        total_output = sum(c["total_output_tokens"] for c in campaign_costs)
        total_short_cost = sum(c["cost_short_context"] for c in campaign_costs)
        total_long_cost = sum(c["cost_long_context"] for c in campaign_costs)
        total_blended = sum(c["cost_blended"] for c in campaign_costs)

        # Print summary
        print(f"\n{'='*70}")
        print(f"💰 PER-CAMPAIGN COST REPORT")
        print(f"{'='*70}")
        print(f"📧 User: {email}")
        print(f"📅 Month filter: {month or 'All time'}")
        print(f"📊 Campaigns analyzed: {len(campaign_costs)}")
        print(f"📝 Total story entries: {total_entries:,}")
        print(f"🔢 Total input tokens: {total_input:,}")
        print(f"🔢 Total output tokens: {total_output:,}")
        print(f"\n💵 COST ESTIMATES:")
        print(f"   Short context (≤200K): ${total_short_cost:.2f}")
        print(f"   Long context (>200K):  ${total_long_cost:.2f}")
        print(f"   Blended (actual):      ${total_blended:.2f}")

        print(f"\n{'='*70}")
        print(f"📈 TOP {min(top_n, len(campaign_costs))} MOST EXPENSIVE CAMPAIGNS:")
        print(f"{'='*70}")
        print(f"{'Rank':<5} {'Title':<35} {'Entries':<8} {'Tokens':<12} {'Cost':<10}")
        print(f"{'-'*70}")

        for i, camp in enumerate(campaign_costs[:top_n], 1):
            title_short = camp["title"][:33] + ".." if len(camp["title"]) > 35 else camp["title"]
            tokens_str = f"{camp['total_input_tokens']:,}"
            print(f"{i:<5} {title_short:<35} {camp['entry_count']:<8} {tokens_str:<12} ${camp['cost_blended']:.2f}")

        results = {
            "email": email,
            "uid": uid,
            "month_filter": month,
            "analysis_timestamp": datetime.now().isoformat(),
            "summary": {
                "campaigns_analyzed": len(campaign_costs),
                "total_entries": total_entries,
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "cost_short_context": round(total_short_cost, 2),
                "cost_long_context": round(total_long_cost, 2),
                "cost_blended": round(total_blended, 2),
            },
            "campaigns": campaign_costs[:top_n],  # Top N only to keep output manageable
            "all_campaigns_count": len(campaign_costs),
        }

        return results

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

    def delete_campaigns(self, user_id: str, campaign_name: str, dry_run: bool = True, force: bool = False, max_count: int = 100) -> dict[str, Any]:
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
        print("\n📊 DELETION SUMMARY:")
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

    # Analytics command
    analytics_parser = subparsers.add_parser('analytics', help='Analyze user campaign activity with token estimates')
    analytics_parser.add_argument('email', help='User email address')
    analytics_parser.add_argument('--month', help='Filter to specific month (YYYY-MM format)')

    # Cost report command (per-campaign costs)
    cost_parser = subparsers.add_parser('cost-report', help='Estimate per-campaign costs sorted by most expensive')
    cost_parser.add_argument('email', help='User email address')
    cost_parser.add_argument('--month', help='Filter to specific month (YYYY-MM format)')
    cost_parser.add_argument('--top', type=int, default=20, help='Number of top campaigns to show (default: 20)')

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

        elif args.command == 'analytics':
            result = manager.analyze_user_activity(args.email, month=args.month)
            print("\n📊 ANALYTICS RESULTS:")
            print("=" * 60)
            print(json.dumps(result, indent=2, default=str))

            # Save to file
            output_file = os.path.join(args.output_dir, "analytics_results.json")
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📁 Results saved to: {output_file}")

        elif args.command == 'cost-report':
            result = manager.estimate_campaign_costs(args.email, month=args.month, top_n=args.top)

            # Save to file
            output_file = os.path.join(args.output_dir, "cost_report.json")
            with open(output_file, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"\n📁 Full report saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
