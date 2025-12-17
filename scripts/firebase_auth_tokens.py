#!/usr/bin/env python3
"""
Firebase ID Token Manager - Multi-User Support

Manages Firebase ID tokens for testing API endpoints with real authentication.
Supports multiple user accounts with email-based token storage.

Token file location: ~/.worldarchitect_tokens/<email>.json
Each file contains:
- id_token: The Firebase ID token for API authentication
- refresh_token: For refreshing expired tokens
- email: User email
- project_id: Firebase project ID
- created_at: Token creation timestamp
- expires_at: Approximate expiration time

Usage:
    # Authenticate and save token
    python scripts/firebase_auth_tokens.py login jleechan@gmail.com

    # Get stored token
    python scripts/firebase_auth_tokens.py get jleechan@gmail.com

    # List all saved tokens
    python scripts/firebase_auth_tokens.py list

    # Test campaign with specific user
    python scripts/firebase_auth_tokens.py test-campaign jleechan@gmail.com <campaign_id>
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add mvp_site to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

# Token storage directory
TOKEN_DIR = Path.home() / ".worldarchitect_tokens"
FIREBASE_WEB_API_KEY = os.environ.get("FIREBASE_WEB_API_KEY", "")


def get_token_path(email: str) -> Path:
    """Get the token file path for an email."""
    safe_email = email.replace("@", "_at_").replace(".", "_dot_")
    return TOKEN_DIR / f"{safe_email}.json"


def save_token(email: str, token_data: dict[str, Any]) -> None:
    """Save token data to file."""
    TOKEN_DIR.mkdir(mode=0o700, exist_ok=True)
    token_path = get_token_path(email)

    # Add metadata
    token_data["email"] = email
    token_data["created_at"] = datetime.now().isoformat()
    # Firebase ID tokens expire in 1 hour
    token_data["expires_at"] = (datetime.now() + timedelta(hours=1)).isoformat()

    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)

    # Secure the file
    os.chmod(token_path, 0o600)
    print(f"✅ Token saved to: {token_path}")


def load_token(email: str) -> dict[str, Any] | None:
    """Load token data from file."""
    token_path = get_token_path(email)

    if not token_path.exists():
        print(f"❌ No token found for: {email}")
        return None

    with open(token_path) as f:
        token_data = json.load(f)

    # Check expiration
    expires_at = datetime.fromisoformat(token_data.get("expires_at", "2000-01-01"))
    if datetime.now() > expires_at:
        print(f"⚠️  Token expired for {email} at {expires_at}")
        print("   Run: python scripts/firebase_auth_tokens.py login " + email)
        return token_data  # Return anyway, refresh might work

    return token_data


def list_tokens() -> None:
    """List all saved tokens."""
    if not TOKEN_DIR.exists():
        print("No tokens saved yet.")
        return

    print("📋 Saved Firebase Tokens:")
    print("=" * 60)

    for token_file in TOKEN_DIR.glob("*.json"):
        try:
            with open(token_file) as f:
                data = json.load(f)

            email = data.get("email", "unknown")
            expires_at = data.get("expires_at", "unknown")
            project = data.get("project_id", "unknown")

            # Check if expired
            try:
                exp_time = datetime.fromisoformat(expires_at)
                status = "✅ Valid" if datetime.now() < exp_time else "❌ Expired"
            except:
                status = "❓ Unknown"

            print(f"\n  Email: {email}")
            print(f"  Status: {status}")
            print(f"  Expires: {expires_at}")
            print(f"  Project: {project}")
            print(f"  File: {token_file.name}")
        except Exception as e:
            print(f"  Error reading {token_file.name}: {e}")


def login_with_email_password(email: str, password: str) -> dict[str, Any] | None:
    """Login using Firebase REST API with email/password."""
    import requests

    if not FIREBASE_WEB_API_KEY:
        print("❌ FIREBASE_WEB_API_KEY environment variable not set")
        print("   Get it from Firebase Console > Project Settings > General > Web API Key")
        return None

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}"

    payload = {
        "email": email,
        "password": password,
        "returnSecureToken": True
    }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        error = response.json().get("error", {})
        print(f"❌ Login failed: {error.get('message', 'Unknown error')}")
        return None

    data = response.json()

    token_data = {
        "id_token": data["idToken"],
        "refresh_token": data["refreshToken"],
        "project_id": "worldarchitect-ai",  # From your project
        "uid": data["localId"],
    }

    save_token(email, token_data)
    print(f"✅ Logged in as: {email}")
    print(f"   UID: {data['localId']}")

    return token_data


def refresh_token(email: str) -> dict[str, Any] | None:
    """Refresh an expired token using the refresh token."""
    import requests

    token_data = load_token(email)
    if not token_data or "refresh_token" not in token_data:
        print(f"❌ No refresh token available for: {email}")
        return None

    if not FIREBASE_WEB_API_KEY:
        print("❌ FIREBASE_WEB_API_KEY environment variable not set")
        return None

    url = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_WEB_API_KEY}"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": token_data["refresh_token"]
    }

    response = requests.post(url, data=payload)

    if response.status_code != 200:
        error = response.json().get("error", {})
        print(f"❌ Token refresh failed: {error.get('message', 'Unknown error')}")
        return None

    data = response.json()

    new_token_data = {
        "id_token": data["id_token"],
        "refresh_token": data["refresh_token"],
        "project_id": token_data.get("project_id", "worldarchitect-ai"),
        "uid": data["user_id"],
    }

    save_token(email, new_token_data)
    print(f"✅ Token refreshed for: {email}")

    return new_token_data


def get_id_token(email: str) -> str | None:
    """Get a valid ID token for the email, refreshing if needed."""
    token_data = load_token(email)

    if not token_data:
        return None

    # Check if expired and try to refresh
    expires_at = datetime.fromisoformat(token_data.get("expires_at", "2000-01-01"))
    if datetime.now() > expires_at:
        print("🔄 Token expired, attempting refresh...")
        token_data = refresh_token(email)
        if not token_data:
            return None

    return token_data.get("id_token")


def test_campaign(email: str, campaign_id: str, action: str = "look around") -> None:
    """Test a campaign action with the stored token."""
    import requests

    id_token = get_id_token(email)
    if not id_token:
        print("❌ Could not get valid token")
        return

    # Use local server or MCP server
    base_url = os.environ.get("MCP_SERVER_URL", "http://localhost:5001")

    print(f"\n🎮 Testing Campaign: {campaign_id}")
    print(f"   Action: {action}")
    print(f"   Server: {base_url}")

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "process_action",
            "arguments": {
                "campaign_id": campaign_id,
                "action": action
            }
        }
    }

    try:
        response = requests.post(f"{base_url}/mcp", json=payload, headers=headers, timeout=60)
        result = response.json()

        if "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            content = result.get("result", {}).get("content", [{}])[0]
            text = content.get("text", "")

            # Try to parse the JSON response
            try:
                game_data = json.loads(text)
                print(f"\n📖 Narrative: {game_data.get('narrative', 'N/A')[:200]}...")
                print(f"🎲 Dice Rolls: {game_data.get('dice_rolls', [])}")
                print(f"📊 Resources: {game_data.get('resources', 'N/A')}")

                # Check for tool_requests issue
                if game_data.get("dice_rolls") == [] or game_data.get("dice_rolls") is None:
                    if "attack" in action.lower() or "kill" in action.lower() or "eliminate" in action.lower():
                        print("\n⚠️  WARNING: Combat action but no dice rolls!")
                        print("   This may indicate the LLM isn't generating tool_requests")
            except json.JSONDecodeError:
                print(f"\n📝 Response: {text[:500]}...")

    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Firebase ID Token Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Login command
    login_parser = subparsers.add_parser("login", help="Login and save token")
    login_parser.add_argument("email", help="User email")
    login_parser.add_argument("--password", "-p", help="Password (will prompt if not provided)")

    # Get token command
    get_parser = subparsers.add_parser("get", help="Get stored token")
    get_parser.add_argument("email", help="User email")

    # Refresh token command
    refresh_parser = subparsers.add_parser("refresh", help="Refresh expired token")
    refresh_parser.add_argument("email", help="User email")

    # List command
    subparsers.add_parser("list", help="List all saved tokens")

    # Test campaign command
    test_parser = subparsers.add_parser("test-campaign", help="Test campaign with stored token")
    test_parser.add_argument("email", help="User email")
    test_parser.add_argument("campaign_id", help="Campaign ID to test")
    test_parser.add_argument("--action", "-a", default="look around", help="Action to perform")

    args = parser.parse_args()

    if args.command == "login":
        password = args.password
        if not password:
            import getpass
            password = getpass.getpass(f"Password for {args.email}: ")
        login_with_email_password(args.email, password)

    elif args.command == "get":
        token_data = load_token(args.email)
        if token_data:
            id_token = token_data.get("id_token", "")
            print(f"\n🔑 ID Token for {args.email}:")
            print(f"   {id_token[:50]}...{id_token[-20:]}")
            print(f"\n   Full token (for curl/testing):")
            print(f"   Bearer {id_token}")

    elif args.command == "refresh":
        refresh_token(args.email)

    elif args.command == "list":
        list_tokens()

    elif args.command == "test-campaign":
        test_campaign(args.email, args.campaign_id, args.action)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
