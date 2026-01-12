#!/usr/bin/env python3
"""
Download Campaign Script - Export campaigns to local files.

This script uses the shared export logic from document_generator.py
to download campaigns from Firestore to local files. The formatting
logic (scene numbers, session headers, choice detection) is centralized
in document_generator.get_story_text_from_context_enhanced() and shared
with the web UI export button for consistency.

Usage:
    # Download by email (looks up UID automatically)
    python scripts/download_campaign.py --email user@example.com --campaign-id abc123

    # Download by UID directly
    python scripts/download_campaign.py --uid USER_UID --campaign-id abc123

    # Download all campaigns for a user
    python scripts/download_campaign.py --email user@example.com --all

    # Specify output directory and format
    python scripts/download_campaign.py --email user@example.com --campaign-id abc123 \
        --output-dir ~/Downloads --format docx

Prerequisites:
    export WORLDAI_DEV_MODE=true
    export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json
"""

import argparse
import os
import sys

# Add project root to path for imports (parent of scripts/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch

apply_clock_skew_patch()

import firebase_admin
from firebase_admin import auth, credentials

from mvp_site import document_generator, firestore_service


def find_user_by_email(email: str) -> str | None:
    """Find Firebase UID by email address."""
    # Initialize Firebase if needed
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

    try:
        user_record = auth.get_user_by_email(email)
        return user_record.uid
    except auth.UserNotFoundError:
        return None


def export_campaign(
    user_id: str,
    campaign_id: str,
    output_dir: str,
    export_format: str = "txt",
    include_scenes: bool = True,
) -> tuple[str, int] | None:
    """
    Export a campaign using the existing document_generator logic.

    Args:
        user_id: Firebase user ID
        campaign_id: Campaign ID to export
        output_dir: Directory to save the exported file
        export_format: Export format (txt, docx, pdf)
        include_scenes: Whether to include scene numbers and headers

    Returns:
        Tuple of (output_path, entry_count) or None if failed
    """
    # Get campaign data and story
    campaign_data, story_context = firestore_service.get_campaign_by_id(
        user_id, campaign_id
    )

    if not campaign_data:
        print(f"  Campaign {campaign_id} not found")
        return None

    # Validate story_context before iterating
    if story_context is None:
        print(f"  Campaign {campaign_id} has no story data")
        return None

    if not isinstance(story_context, list):
        print(f"  Campaign {campaign_id} has invalid story data format")
        return None

    campaign_title = campaign_data.get("title", "Untitled Campaign")

    # Convert story context to text format using shared enhanced formatting
    # This uses the same logic as the web UI for consistency
    story_text = document_generator.get_story_text_from_context_enhanced(
        story_context, include_scenes=include_scenes
    )

    # Create safe filename
    safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in campaign_title)
    safe_title = safe_title[:50]  # Truncate long titles
    filename = f"{safe_title}_{campaign_id[:8]}.{export_format}"
    output_path = os.path.join(output_dir, filename)

    # Generate the export file using existing document_generator
    if export_format == "txt":
        document_generator.generate_txt(story_text, output_path, campaign_title)
    elif export_format == "docx":
        document_generator.generate_docx(story_text, output_path, campaign_title)
    elif export_format == "pdf":
        document_generator.generate_pdf(story_text, output_path, campaign_title)
    else:
        print(f"  Unsupported format: {export_format}")
        return None

    return output_path, len(story_context)


def list_campaigns(user_id: str) -> list[dict]:
    """List all campaigns for a user."""
    campaigns, _ = firestore_service.get_campaigns_for_user(user_id)
    return campaigns


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download campaigns to local files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download specific campaign by email
  %(prog)s --email user@example.com --campaign-id abc123

  # Download all campaigns for a user
  %(prog)s --email user@example.com --all

  # Download to specific directory as DOCX
  %(prog)s --uid USER_UID --campaign-id abc123 --output-dir ~/Desktop --format docx

  # List campaigns without downloading
  %(prog)s --email user@example.com --list
        """,
    )

    # User identification (one required)
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("--email", help="User email address (looks up UID)")
    user_group.add_argument("--uid", help="Firebase user ID directly")

    # Campaign selection
    campaign_group = parser.add_mutually_exclusive_group()
    campaign_group.add_argument("--campaign-id", help="Specific campaign ID to download")
    campaign_group.add_argument(
        "--all", action="store_true", help="Download all campaigns"
    )
    campaign_group.add_argument(
        "--list", action="store_true", help="List campaigns without downloading"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        default=os.path.expanduser("~/Downloads"),
        help="Output directory (default: ~/Downloads)",
    )
    parser.add_argument(
        "--format",
        choices=["txt", "docx", "pdf"],
        default="txt",
        help="Export format (default: txt)",
    )
    parser.add_argument(
        "--no-scenes",
        action="store_true",
        help="Disable scene numbers and session headers (plain export)",
    )

    args = parser.parse_args()

    # Resolve user ID
    if args.email:
        print(f"Looking up user: {args.email}")
        user_id = find_user_by_email(args.email)
        if not user_id:
            print(f"User not found: {args.email}")
            sys.exit(1)
        print(f"Found UID: {user_id}")
    else:
        user_id = args.uid

    # Expand tilde in output directory and ensure it exists
    output_dir = os.path.expanduser(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    # List campaigns mode
    if args.list:
        print(f"\nCampaigns for user {user_id}:")
        print("-" * 60)
        campaigns = list_campaigns(user_id)
        for i, c in enumerate(campaigns, 1):
            title = c.get("title", "Untitled")[:40]
            cid = c.get("id", "?")
            print(f"{i:3d}. {title:<42} ID: {cid}")
        print(f"\nTotal: {len(campaigns)} campaigns")
        return

    # Get campaigns to download
    if args.campaign_id:
        campaign_ids = [args.campaign_id]
    elif args.all:
        campaigns = list_campaigns(user_id)
        campaign_ids = [c.get("id") for c in campaigns if c.get("id")]
        print(f"Found {len(campaign_ids)} campaigns to download")
    else:
        parser.error("Must specify --campaign-id, --all, or --list")

    # Download campaigns
    print(f"\nDownloading to: {output_dir}")
    print(f"Format: {args.format}")
    print("=" * 60)

    success_count = 0
    for campaign_id in campaign_ids:
        print(f"\nDownloading: {campaign_id}...")
        try:
            result = export_campaign(
                user_id,
                campaign_id,
                output_dir,
                args.format,
                include_scenes=not args.no_scenes,
            )
            if result:
                path, entries = result
                file_size = os.path.getsize(path)
                print(f"  Saved: {os.path.basename(path)}")
                print(f"  Entries: {entries}, Size: {file_size / 1024:.1f} KB")
                success_count += 1
        except Exception as e:
            print(f"  Error: {e}")

    print("=" * 60)
    print(f"Downloaded {success_count}/{len(campaign_ids)} campaigns")


if __name__ == "__main__":
    main()
