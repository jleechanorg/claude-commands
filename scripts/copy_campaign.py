#!/usr/bin/env python3
"""
Copy Campaign Script - Duplicate a campaign with all its data
Copies everything from Firestore as-is without modifying fields.
"""

import os
import sys
import traceback

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'mvp_site'))

# Set dev mode for Firebase
os.environ.setdefault('WORLDAI_DEV_MODE', 'true')

# Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

import firebase_admin
from firebase_admin import credentials, firestore
import firestore_service

# Initialize Firebase
if not firebase_admin._apps:
    creds_path = os.environ.get("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        creds_path = os.path.expanduser(creds_path)
        if os.path.exists(creds_path):
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        else:
            firebase_admin.initialize_app()
    else:
        firebase_admin.initialize_app()

def copy_campaign(source_user_id: str, source_campaign_id: str, dest_user_id: str | None = None, copy_suffix: str = "(copy)") -> str:
    """Copy a campaign and all its subcollections, adding suffix to the name.
    
    Copies everything from Firestore as-is without modifying any fields.
    
    Args:
        source_user_id: User ID of the source campaign
        source_campaign_id: Campaign ID to copy
        dest_user_id: User ID for destination (default: same as source)
        copy_suffix: Suffix to add to campaign name (default: "(copy)")
    """
    db = firestore_service.get_db()
    
    # Use source user_id as dest if not specified
    if dest_user_id is None:
        dest_user_id = source_user_id
    
    # Get source campaign
    source_ref = db.collection("users").document(source_user_id).collection("campaigns").document(source_campaign_id)
    source_data = source_ref.get()
    
    if not source_data.exists:
        raise ValueError(f"Campaign {source_campaign_id} not found for user {source_user_id}")
    
    # Get campaign data - copy everything as-is
    campaign_data = source_data.to_dict()
    
    # Update name to always add suffix to the end
    original_name = campaign_data.get("title", "Untitled Campaign")
    # Always append the suffix to the end of the original title
    campaign_data["title"] = f"{original_name} {copy_suffix}"
    
    # Create new campaign with auto-generated ID
    campaigns_ref = db.collection("users").document(dest_user_id).collection("campaigns")
    new_campaign_ref = campaigns_ref.document()
    new_campaign_id = new_campaign_ref.id
    
    # Set campaign data - copy everything including all timestamps
    new_campaign_ref.set(campaign_data)
    
    print(f"✅ Created new campaign: {new_campaign_id}")
    print(f"📝 Name: {campaign_data['title']}")
    
    # Copy all subcollections - copy everything as-is
    subcollections = ["story", "game_states", "notes", "characters"]
    
    for subcollection_name in subcollections:
        source_subcoll = source_ref.collection(subcollection_name)
        new_subcoll = new_campaign_ref.collection(subcollection_name)
        
        # Copy all documents in subcollection - copy everything as-is
        count = 0
        for doc in source_subcoll.stream():
            doc_data = doc.to_dict()
            
            # Set with same document ID to preserve ordering and all fields
            new_subcoll.document(doc.id).set(doc_data)
            count += 1
        
        if count > 0:
            print(f"  ✅ Copied {count} documents from {subcollection_name}")
    
    # Return campaign ID - URL generation should be done by caller
    # since PR preview URLs are temporary and environment-specific
    print(f"\n✅ Campaign copied successfully!")
    print(f"📋 Campaign ID: {new_campaign_id}")
    print(f"💡 Note: Campaign data is in Firestore. Generate URL based on your environment.")
    
    return new_campaign_id

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Copy a campaign with all its data")
    parser.add_argument("source_user_id", nargs="?", help="User ID of the source campaign")
    parser.add_argument("source_campaign_id", nargs="?", help="Campaign ID to copy")
    parser.add_argument("--dest-user-id", help="User ID for destination (default: same as source)")
    parser.add_argument("--suffix", default="(copy)", help="Suffix to add to campaign name (default: '(copy)')")
    parser.add_argument("--find-by-title", help="Find campaign by title (searches all users)")
    parser.add_argument("--find-by-id", help="Find campaign by campaign ID (searches all users)")
    
    args = parser.parse_args()
    
    # If --find-by-id is provided, search for the campaign by ID using collection group
    if args.find_by_id:
        print(f"🔍 Searching for campaign with ID: {args.find_by_id}")
        db = firestore_service.get_db()
        
        # Use collection group query to find campaign across all users efficiently
        # Iterate through campaigns and check document ID (much faster than iterating users)
        campaigns_group = db.collection_group("campaigns")
        found_campaign = None
        
        for campaign_doc in campaigns_group.stream():
            if campaign_doc.id == args.find_by_id:
                found_campaign = campaign_doc
                break
        
        if found_campaign:
            campaign_data = found_campaign.to_dict()
            title = campaign_data.get("title", "Untitled Campaign")
            
            # Extract user_id from document path: users/{user_id}/campaigns/{campaign_id}
            path_parts = found_campaign.reference.path.split("/")
            if len(path_parts) >= 4 and path_parts[0] == "users" and path_parts[2] == "campaigns":
                user_id = path_parts[1]
                print(f"✅ Found campaign: {title}")
                print(f"   User ID: {user_id}")
                print(f"   Campaign ID: {args.find_by_id}")
                args.source_user_id = user_id
                args.source_campaign_id = args.find_by_id
            else:
                print(f"❌ Could not parse user ID from campaign path: {found_campaign.reference.path}")
                sys.exit(1)
        else:
            print(f"❌ No campaign found with ID '{args.find_by_id}'")
            sys.exit(1)
    
    # If --find-by-title is provided, search for the campaign
    elif args.find_by_title:
        print(f"🔍 Searching for campaign with title: {args.find_by_title}")
        db = firestore_service.get_db()
        campaigns_found = []
        
        # Search all users
        users_ref = db.collection("users")
        for user_doc in users_ref.stream():
            user_id = user_doc.id
            campaigns_ref = user_doc.reference.collection("campaigns")
            for campaign_doc in campaigns_ref.stream():
                campaign_data = campaign_doc.to_dict()
                title = campaign_data.get("title", "")
                if args.find_by_title.lower() in title.lower():
                    campaigns_found.append({
                        "user_id": user_id,
                        "campaign_id": campaign_doc.id,
                        "title": title
                    })
        
        if not campaigns_found:
            print(f"❌ No campaigns found matching '{args.find_by_title}'")
            sys.exit(1)
        
        if len(campaigns_found) == 1:
            print(f"✅ Found campaign: {campaigns_found[0]['title']}")
            args.source_user_id = campaigns_found[0]["user_id"]
            args.source_campaign_id = campaigns_found[0]["campaign_id"]
        else:
            print(f"⚠️  Found {len(campaigns_found)} matching campaigns:")
            for i, camp in enumerate(campaigns_found, 1):
                print(f"  {i}. {camp['title']} (User: {camp['user_id'][:20]}..., Campaign: {camp['campaign_id']})")
            print("❌ Please specify exact user_id and campaign_id")
            sys.exit(1)
    
    # Validate required arguments
    if not args.source_user_id or not args.source_campaign_id:
        parser.print_help()
        print("\n❌ Error: source_user_id and source_campaign_id are required")
        print("   Or use --find-by-title to search for a campaign")
        sys.exit(1)
    
    try:
        campaign_id = copy_campaign(
            args.source_user_id,
            args.source_campaign_id,
            dest_user_id=args.dest_user_id,
            copy_suffix=args.suffix
        )
        print(f"\n🔗 Campaign ID: {campaign_id}")
        print(f"💡 To access: Use your environment's base URL + /game/{campaign_id}")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        sys.exit(1)
