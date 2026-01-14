"""
Script to clean up bloated God Mode directives.
Removes redundant state tracking rules (Level, XP, Gold, Date) to fix context window issues.
"""

import sys
import os
import argparse
import re
import firebase_admin
from firebase_admin import credentials, firestore

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'mvp_site'))

# Set dev mode for Firebase
os.environ.setdefault('WORLDAI_DEV_MODE', 'true')

# Apply clock skew patch BEFORE importing Firebase
from mvp_site.clock_skew_credentials import apply_clock_skew_patch
apply_clock_skew_patch()

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

db = firestore_service.get_db() 

def clean_directives(campaign_id: str, user_id: str = None, dry_run: bool = True):
    """Clean up bloated God Mode directives.
    
    Args:
        campaign_id: Campaign ID to clean
        user_id: User ID (if None, will search for campaign)
        dry_run: If True, only show what would be removed without making changes
    """
    print(f"🔍 Searching for campaign {campaign_id}...")
    
    # If user_id not provided, search for campaign using collection group
    if not user_id:
        campaigns_group = db.collection_group("campaigns")
        found_campaign = None
        
        for campaign_doc in campaigns_group.stream():
            if campaign_doc.id == campaign_id:
                found_campaign = campaign_doc
                break
        
        if not found_campaign:
            print(f"❌ Campaign {campaign_id} not found!")
            return
        
        # Extract user_id from document path
        path_parts = found_campaign.reference.path.split("/")
        if len(path_parts) >= 4 and path_parts[0] == "users" and path_parts[2] == "campaigns":
            user_id = path_parts[1]
            doc_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
        else:
            print(f"❌ Could not parse user ID from campaign path")
            return
    else:
        doc_ref = db.collection('users').document(user_id).collection('campaigns').document(campaign_id)
    
    doc = doc_ref.get()
    if not doc.exists:
        print(f"❌ Campaign not found!")
        return

    campaign_data = doc.to_dict()
    campaign_title = campaign_data.get('title', 'Untitled Campaign')
    print(f"✅ Found campaign: {campaign_title}")
    print(f"   User ID: {user_id}")
    print(f"   Campaign ID: {campaign_id}")
    if dry_run:
        print(f"   🔍 DRY RUN MODE - No changes will be made")
    
    # Get game state
    state_ref = doc_ref.collection('game_states').document('current_state')
    state_doc = state_ref.get()
    
    if not state_doc.exists:
        print("Game state not found!")
        return

    state_data = state_doc.to_dict()
    custom_state = state_data.get('custom_campaign_state') or {}
    directives = custom_state.get('god_mode_directives', [])
    
    print(f"Current directive count: {len(directives)}")
    
    # Define patterns to remove (simple string matching for safety)
    # These are state values that change, not behavioral rules
    # Match patterns that indicate specific state values (numbers, levels, stats)
    cleanup_keywords = [
        # State value patterns (with or without "Rule:" prefix)
        "Rule: Real Level",
        "Rule: Level",
        "Rule: Level is",  # "Level is 42" - specific value
        "Level is",  # "Nocturne is Level 16" or "Level is 42"
        "is Level",  # "Nocturne is Level 24"
        "Level 16",  # Specific level values
        "Level 24",
        "Level 27",
        "Level 36",
        "Level 37",
        "Level 39",
        "Level 40",
        "Level 41",
        "Level 42",
        "Level 43",
        "Level 50",
        "Level 51",
        "Lvl 12",  # Abbreviated level
        "Lvl 13",
        "Lvl 14",
        "Lvl 15",
        "Lvl 20",
        "Lvl 22",
        "Lvl 23",
        "Rule: HP",
        "Rule: HP is",  # "HP is 50" - specific value
        "HP is",  # State value
        "Rule: XP",
        "Rule: XP is",  # "XP is 5000" - specific value
        "XP is",  # "Level 40 XP is 3M"
        "XP: [",  # "XP: [current] / [needed]"
        "XP current/needed",  # State tracking
        "XP thresholds",  # "Track XP thresholds as +330,000"
        "Rule: Gold",
        "Rule: Gold is",  # "Gold is 1000" - specific value
        "Gold is",  # State value
        "gp to gold",  # "distribute 41,666 gp"
        "Rule: Soul Coin",
        "Rule: Soul Coin is",  # "Soul Coin is 25k" - specific value
        "Soul Coin",  # "Soul Coins: [count]"
        "soul coins",  # State tracking
        "soul coin",  # State tracking
        "Rule: Base Spell Save DC",
        "Rule: Base Spell Save DC is",  # Calculated value
        "Base Spell Save DC is",  # "Base Spell Save DC is 73"
        "Spell Save DC is",  # "Base Spell Save DC is 73 (Acuity 83)"
        "Spell Attack is",  # "Base Spell Attack is +52"
        "Rule: Nocturne effective Charisma",
        "Rule: effective Charisma is",  # Calculated value
        "effective Charisma is",  # "Nocturne effective Charisma with gear is 97"
        "Natural Charisma is",  # "Nocturne's Natural Charisma is 87"
        "Charisma is",  # Specific stat values
        "Charisma with gear is",  # "Effective Charisma with gear is 97"
        "Rule: Automatic",  # Usually auto-deductions (state tracking)
        "Rule: Daily",  # State tracking
        "Daily gross production",  # "Daily gross production is 2,916"
        "Daily deductions",  # "Daily deductions: 583"
        "Daily net addition",  # "Daily net addition to player stockpile"
        "Rule: Monthly",  # State tracking
        "Monthly soul coin production",  # "Monthly soul coin production is 87,500"
        "Rule: Next level",  # State tracking
        "Next level (",  # "Next level (44) requires 30,000M XP"
        "requires",  # "Level 44 requires 30,000M XP"
        "Rule: Always include",  # Formatting rules (system-level)
        "Always include 'XP:",  # Formatting
        "Always include 'Soul Coins:",  # Formatting
        "Always include Python-executed",  # This is actually behavioral, but let's check
        # Note: "Maintain" and "Track" are intentionally NOT here
        # because they might be behavioral (e.g., "Maintain buff", "Track condition")
        # The server-side validation is more precise and handles these cases
    ]
    
    # Additional patterns: directives that contain specific numbers (state values)
    # These are more aggressive and will catch things like "Level 42" or "Charisma is 87"
    numeric_state_patterns = [
        r'\bLevel \d+',  # "Level 24", "Level 42"
        r'\bLvl \d+',  # "Lvl 12", "Lvl 22"
        r'is Level \d+',  # "is Level 24"
        r'Level \d+ XP',  # "Level 40 XP is 3M"
        r'XP is \d+',  # "XP is 3M"
        r'Charisma is \d+',  # "Charisma is 87"
        r'Charisma \d+',  # "Charisma 87"
        r'DC is \d+',  # "DC is 73"
        r'Spell Save DC is \d+',  # "Spell Save DC is 73"
        r'Spell Attack is \+\d+',  # "Spell Attack is +52"
        r'production is \d+',  # "production is 87,500"
        r'deductions: \d+',  # "deductions: 583"
    ]
    
    kept_directives = []
    removed_directives = []
    removed_count = 0
    
    print(f"\n📋 Analyzing {len(directives)} directives...")
    print("=" * 80)
    
    for d in directives:
        should_remove = False
        
        # Extract rule text for matching (handle both string and dict formats)
        rule_text = ""
        if isinstance(d, dict):
            rule_text = d.get('rule', '') or ''
        elif isinstance(d, str):
            rule_text = d
        
        # Handle null values (key exists but value is None)
        if not rule_text:
            continue
        
        rule_text_lower = rule_text.lower()
        
        # Check against keyword patterns
        for keyword in cleanup_keywords:
            if keyword.lower() in rule_text_lower:
                should_remove = True
                break
        
        # Check against numeric state patterns (more aggressive)
        if not should_remove:
            for pattern in numeric_state_patterns:
                if re.search(pattern, rule_text, re.IGNORECASE):
                    # But exclude behavioral rules that might contain numbers
                    # e.g., "Always apply +2 CON" is behavioral, not state
                    behavioral_indicators = [
                        "always apply", "always use", "always include", 
                        "apply", "grant", "provide", "maintain", "track as",
                        "advantage", "disadvantage", "bonus", "modifier"
                    ]
                    is_behavioral = any(indicator in rule_text_lower for indicator in behavioral_indicators)
                    if not is_behavioral:
                        should_remove = True
                        break
        
        if should_remove:
            removed_count += 1
            removed_directives.append(rule_text)
        else:
            kept_directives.append(d)

    # Show what would be removed
    if removed_directives:
        print(f"\n🗑️  DIRECTIVES THAT WOULD BE REMOVED ({len(removed_directives)}):")
        print("=" * 80)
        for i, rule in enumerate(removed_directives, 1):
            print(f"{i:3d}. {rule[:150]}{'...' if len(rule) > 150 else ''}")
    else:
        print("\n✅ No directives would be removed")
    
    # Show what would be kept
    if kept_directives:
        print(f"\n✅ DIRECTIVES THAT WOULD BE KEPT ({len(kept_directives)}):")
        print("=" * 80)
        for i, d in enumerate(kept_directives, 1):
            rule_text = d.get('rule', '') if isinstance(d, dict) else str(d)
            print(f"{i:3d}. {rule_text[:150]}{'...' if len(rule_text) > 150 else ''}")
    else:
        print("\n⚠️  No directives would remain")

    print(f"\n📊 SUMMARY:")
    print("=" * 80)
    print(f"Original directives: {len(directives)}")
    print(f"Would be removed:    {removed_count}")
    print(f"Would remain:        {len(kept_directives)}")
    if len(directives) > 0:
        print(f"Reduction:           {removed_count / len(directives) * 100:.1f}%")
    else:
        print(f"Reduction:           N/A (no directives to reduce)")
    
    if not dry_run and len(kept_directives) < len(directives):
        # Auto-confirm when --execute flag is used
        print("\n⚠️  Executing cleanup (--execute flag provided)...")
        # Update the document
        custom_state['god_mode_directives'] = kept_directives
        state_ref.update({'custom_campaign_state': custom_state})
        print("✅ Successfully updated directives.")
        print(f"✅ Removed {removed_count} directives, kept {len(kept_directives)} directives.")
    elif not dry_run:
        print("\n✅ No changes needed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean up bloated God Mode directives")
    parser.add_argument("campaign_id", help="Campaign ID to clean")
    parser.add_argument("--user-id", help="User ID (optional, will search if not provided)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run mode (default: True)")
    parser.add_argument("--execute", action="store_true", help="Actually execute the cleanup (overrides --dry-run)")
    
    args = parser.parse_args()
    
    dry_run = args.dry_run and not args.execute
    
    clean_directives(args.campaign_id, args.user_id, dry_run=dry_run)
