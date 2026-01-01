#!/usr/bin/env python3
"""
Download Campaign Script - Export campaigns to local files.

This script reuses the existing export logic from world_logic.py and
document_generator.py to download campaigns from Firestore to local files.

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
import html
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


def _normalize_text(text: str) -> str:
    """Normalize text for comparison by handling HTML entities and whitespace."""
    # Decode HTML entities (&#x27; -> ', &amp; -> &, etc.)
    normalized = html.unescape(text)
    # Normalize whitespace
    normalized = " ".join(normalized.split())
    return normalized


def get_choice_type(
    user_text: str, recent_planning_blocks: list[dict | None]
) -> tuple[str, str | None]:
    """
    Determine if user action was a planning choice or freeform.

    Args:
        user_text: The user's action text
        recent_planning_blocks: List of recent AI response planning_blocks (most recent first)

    Returns:
        Tuple of (choice_type, choice_key) where choice_type is 'freeform' or 'choice'
    """
    if not recent_planning_blocks:
        return ("freeform", None)

    # Normalize user text for comparison
    user_normalized = _normalize_text(user_text)

    # Extract title from user text (before " - " if present)
    user_title = user_normalized.split(" - ")[0].strip() if " - " in user_normalized else None

    # Check each recent planning block (most recent first)
    for planning_block in recent_planning_blocks:
        if not planning_block:
            continue

        choices = planning_block.get("choices", {})
        if not choices:
            continue

        # Check if user text matches any choice in this planning block
        for key, choice in choices.items():
            if isinstance(choice, dict):
                choice_text = choice.get("text", "")
                if not choice_text:
                    continue

                choice_normalized = _normalize_text(choice_text)

                # Method 1: Direct startswith match
                if user_normalized.startswith(choice_normalized):
                    return ("choice", key)

                # Method 2: Choice text starts with user's title (for short choice texts)
                if user_title and choice_normalized.startswith(user_title):
                    return ("choice", key)

                # Method 3: User's title matches choice text exactly
                if user_title and user_title.lower() == choice_normalized.lower():
                    return ("choice", key)

                # Method 4: Extract title from choice text and compare
                choice_title = choice_normalized.split(" - ")[0].strip() if " - " in choice_normalized else choice_normalized
                if user_title and user_title.lower() == choice_title.lower():
                    return ("choice", key)

    return ("freeform", None)


def format_story_entry(
    entry: dict, include_scene: bool = True, recent_planning_blocks: list[dict | None] | None = None
) -> str:
    """
    Format a single story entry with scene numbers, session headers, resources, and dice rolls.

    Args:
        entry: Story entry dictionary from Firestore
        include_scene: Whether to include scene number header
        recent_planning_blocks: List of recent AI response planning_blocks (for user entries)

    Returns:
        Formatted string for the entry
    """
    actor = entry.get("actor", "unknown")
    text = entry.get("text", "")
    mode = entry.get("mode")
    scene_num = entry.get("user_scene_number")
    session_header = entry.get("session_header", "")
    resources = entry.get("resources", "")
    dice_rolls = entry.get("dice_rolls", [])

    parts = []

    # Add scene header for AI responses
    if actor == "gemini" and scene_num and include_scene:
        parts.append(f"{'=' * 60}")
        parts.append(f"SCENE {scene_num}")
        parts.append(f"{'=' * 60}")

    # Add session header if present (contains timestamp, location, status)
    if session_header:
        # Clean up the session header (remove [SESSION_HEADER] prefix if present)
        clean_header = session_header.replace("[SESSION_HEADER]", "").strip()
        if clean_header:
            parts.append(f"[{clean_header}]")

    # Add resources if present
    if resources:
        parts.append(f"Resources: {resources}")

    # Add dice rolls if present
    if dice_rolls:
        parts.append("Dice Rolls:")
        for roll in dice_rolls:
            parts.append(f"  - {roll}")

    # Add blank line after metadata if we have any
    if session_header or resources or dice_rolls:
        parts.append("")

    # Add actor label with choice type for player actions
    if actor == "gemini":
        label = "Game Master"
    elif mode == "god":
        label = "God Mode"
    else:
        # Determine if this was a planning choice or freeform
        choice_type, choice_key = get_choice_type(text, recent_planning_blocks or [])
        if choice_type == "choice" and choice_key:
            label = f"Player (choice: {choice_key})"
        else:
            label = "Player (freeform)"

    parts.append(f"{label}:")
    parts.append(text)

    return "\n".join(parts)


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

    # Convert story context to text format with scene numbers and session headers
    story_parts = []
    # Track last 10 planning blocks to search for choice matches
    recent_planning_blocks: list[dict | None] = []
    MAX_PLANNING_BLOCKS = 10

    for entry in story_context:
        # Skip malformed entries
        if not isinstance(entry, dict):
            continue
        # Pass recent planning blocks for user entries to determine choice type
        formatted = format_story_entry(
            entry, include_scene=include_scenes, recent_planning_blocks=recent_planning_blocks
        )
        story_parts.append(formatted)

        # Track planning blocks from AI responses (keep last 10)
        if entry.get("actor") == "gemini":
            planning_block = entry.get("planning_block")
            if planning_block:
                # Insert at beginning (most recent first)
                recent_planning_blocks.insert(0, planning_block)
                # Keep only last N
                if len(recent_planning_blocks) > MAX_PLANNING_BLOCKS:
                    recent_planning_blocks.pop()

    story_text = "\n\n".join(story_parts)

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
    return firestore_service.get_campaigns_for_user(user_id)


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
