#!/usr/bin/env python3
"""
Find User by Email - Get Firebase UID from email address

This script looks up a Firebase user by email to get their UID.
"""

import json
import os
import sys
from datetime import datetime

# Add mvp_site to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

import firebase_admin
from firebase_admin import auth


def find_user_by_email(email: str) -> dict:
    """
    Find Firebase user by email address.
    
    Args:
        email: User's email address
        
    Returns:
        Dictionary with user information including UID
    """
    try:
        # Get user by email
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
        
        return user_info
        
    except auth.UserNotFoundError:
        print(f"❌ User not found: {email}")
        return None
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None


def main():
    """Main function to find user by email."""
    if len(sys.argv) != 2:
        print("Usage: python3 find_user_by_email.py <email>")
        print("Example: python3 find_user_by_email.py jleechan@gmail.com")
        sys.exit(1)
    
    email = sys.argv[1]
    
    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        
        # Find user
        user_info = find_user_by_email(email)
        
        if user_info:
            # Output results as JSON
            results = {
                "query_timestamp": datetime.now().isoformat(),
                "search_email": email,
                "user_found": True,
                "user_info": user_info
            }
            
            print("\n📋 USER LOOKUP RESULTS:")
            print("=" * 50)
            print(json.dumps(results, indent=2, default=str))
            
            return results
        else:
            results = {
                "query_timestamp": datetime.now().isoformat(),
                "search_email": email,
                "user_found": False,
                "user_info": None
            }
            
            print("\n📋 USER LOOKUP RESULTS:")
            print("=" * 50)
            print(json.dumps(results, indent=2))
            
            return results
            
    except Exception as e:
        print(f"❌ Error in user lookup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()