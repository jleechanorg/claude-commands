#!/usr/bin/env python3
"""
Delete Campaigns by Exact Name - SAFE Campaign Deletion Script

This script SAFELY deletes campaigns with EXACT name match for a specific user.
Includes multiple safety checks, confirmation prompts, and dry-run mode.

⚠️ SAFETY FEATURES:
- Exact name matching only (case-sensitive)
- Dry-run mode by default
- Manual confirmation required
- Batch size limits
- Progress tracking
- Rollback information
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

# Add mvp_site to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

import firebase_admin
from firebase_admin import firestore
import firestore_service
from custom_types import UserId, CampaignId


def get_campaigns_to_delete(user_id: str, campaign_name: str, max_count: int = 100) -> List[Dict[str, Any]]:
    """
    Get campaigns that would be deleted (exact name match only).
    
    Args:
        user_id: Firebase user ID
        campaign_name: EXACT campaign name to match
        max_count: Maximum number of campaigns to return for safety
        
    Returns:
        List of campaign dictionaries that match exactly
    """
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


def delete_campaign_safe(user_id: str, campaign_id: str) -> bool:
    """
    Safely delete a single campaign.
    
    Args:
        user_id: Firebase user ID
        campaign_id: Campaign ID to delete
        
    Returns:
        True if successful, False otherwise
    """
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


def main():
    """Main function for safe campaign deletion."""
    if len(sys.argv) < 3:
        print("Usage: python3 delete_campaigns_by_name.py <user_id> <exact_campaign_name> [--confirm] [--force]")
        print("Example: python3 delete_campaigns_by_name.py vnLp2G3m21PJL6kxcuAqmWSOtm73 'My Epic Adventure'")
        print("")
        print("⚠️ SAFETY NOTES:")
        print("- Uses EXACT name matching only (case-sensitive)")
        print("- Runs in DRY-RUN mode by default (no actual deletion)")
        print("- Add --confirm flag to perform actual deletion")
        print("- Add --force flag to skip interactive confirmation")
        print("- Limited to 100 campaigns max for safety")
        sys.exit(1)
    
    user_id = sys.argv[1]
    campaign_name = sys.argv[2]
    confirm_deletion = "--confirm" in sys.argv
    
    print("🗑️ SAFE CAMPAIGN DELETION SCRIPT")
    print("=" * 50)
    print(f"🕐 Timestamp: {datetime.now().isoformat()}")
    print(f"👤 User ID: {user_id}")
    print(f"📝 Target name: '{campaign_name}'")
    print(f"🔄 Mode: {'ACTUAL DELETION' if confirm_deletion else 'DRY-RUN (no deletion)'}")
    print("")
    
    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        
        # Get campaigns to delete
        campaigns_to_delete = get_campaigns_to_delete(user_id, campaign_name, max_count=100)
        
        if not campaigns_to_delete:
            print("✅ No campaigns found with exact name match. Nothing to delete.")
            return
        
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
        
        # Safety confirmation
        if not confirm_deletion:
            print("🛡️ DRY-RUN MODE: No campaigns will be deleted.")
            print("Add --confirm flag to perform actual deletion.")
            print("")
            
            # Save dry-run results
            results = {
                "dry_run": True,
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "campaign_name": campaign_name,
                "campaigns_found": len(campaigns_to_delete),
                "campaign_ids": [c['id'] for c in campaigns_to_delete],
                "would_delete": len(campaigns_to_delete)
            }
            
            # Use configurable output directory
            output_dir = os.environ.get("OUTPUT_DIR", "docs")
            output_file = os.path.join(output_dir, "deletion_preview.json")
            os.makedirs(output_dir, exist_ok=True)
            
            print(f"📁 Saving dry-run results to {output_file}")
            with open(output_file, "w") as f:
                json.dump(results, f, indent=2)
            
            return
        
        # Final confirmation for actual deletion
        print("⚠️ WARNING: THIS WILL PERMANENTLY DELETE CAMPAIGNS!")
        print(f"You are about to delete {len(campaigns_to_delete)} campaigns.")
        
        # Check for --force flag to skip interactive confirmation
        if "--force" in sys.argv:
            print("🔥 --force flag detected, skipping interactive confirmation")
        else:
            print("Type 'DELETE' to confirm (case-sensitive): ", end="")
            confirmation = input()
            
            if confirmation != "DELETE":
                print("❌ Deletion cancelled. You must type 'DELETE' exactly.")
                return
        
        # Perform actual deletion
        print(f"\n🗑️ Starting deletion of {len(campaigns_to_delete)} campaigns...")
        
        deleted_count = 0
        failed_count = 0
        deleted_ids = []
        failed_ids = []
        
        for i, campaign in enumerate(campaigns_to_delete, 1):
            campaign_id = campaign['id']
            print(f"Deleting {i}/{len(campaigns_to_delete)}: {campaign_id}... ", end="", flush=True)
            
            if delete_campaign_safe(user_id, campaign_id):
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
        
        # Use configurable output directory
        output_dir = os.environ.get("OUTPUT_DIR", "docs")
        output_file = os.path.join(output_dir, "deletion_results.json")
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📁 Saving deletion results to {output_file}")
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ Deletion process completed.")
        
    except Exception as e:
        print(f"❌ Error in deletion process: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()