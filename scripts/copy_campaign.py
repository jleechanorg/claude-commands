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
    
    # Update name to add suffix
    original_name = campaign_data.get("title", "Untitled Campaign")
    # Check if suffix already exists, if so add number
    if copy_suffix in original_name:
        # Extract base name and increment number
        if "(copy 2)" in original_name:
            campaign_data["title"] = original_name.replace("(copy 2)", "(copy 3)")
        elif "(copy)" in original_name:
            campaign_data["title"] = original_name.replace("(copy)", "(copy 2)")
        else:
            campaign_data["title"] = f"{original_name} {copy_suffix}"
    else:
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
    subcollections = ["story", "game_state", "notes", "characters"]
    
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
    parser.add_argument("source_user_id", help="User ID of the source campaign")
    parser.add_argument("source_campaign_id", help="Campaign ID to copy")
    parser.add_argument("--dest-user-id", help="User ID for destination (default: same as source)")
    parser.add_argument("--suffix", default="(copy)", help="Suffix to add to campaign name (default: '(copy)')")
    
    args = parser.parse_args()
    
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
