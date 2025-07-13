"""
Fake Firebase Auth service for testing.
Returns realistic auth responses instead of Mock objects.
"""

from typing import Dict, Any, Optional, List
import time
import hashlib


class FakeUserRecord:
    """Fake Firebase User Record."""
    
    def __init__(self, uid: str, email: str = None, display_name: str = None):
        self.uid = uid
        self.email = email or f"{uid}@test.com"
        self.display_name = display_name or f"Test User {uid}"
        self.email_verified = True
        self.disabled = False
        self.creation_timestamp = int(time.time())
        self.last_sign_in_timestamp = int(time.time())
        self.provider_data = []
        self.custom_claims = {}
        
    def to_dict(self):
        """Convert to dictionary representation."""
        return {
            'uid': self.uid,
            'email': self.email,
            'displayName': self.display_name,
            'emailVerified': self.email_verified,
            'disabled': self.disabled,
            'metadata': {
                'creationTime': self.creation_timestamp,
                'lastSignInTime': self.last_sign_in_timestamp
            },
            'customClaims': self.custom_claims,
            'providerData': self.provider_data
        }


class FakeDecodedToken:
    """Fake decoded Firebase token."""
    
    def __init__(self, uid: str, email: str = None, **claims):
        self.uid = uid
        self.email = email or f"{uid}@test.com"
        self.aud = "worldarchitect-ai"
        self.iss = f"https://securetoken.google.com/worldarchitect-ai"
        self.iat = int(time.time())
        self.exp = int(time.time()) + 3600  # 1 hour expiry
        self.auth_time = int(time.time())
        self.sub = uid
        
        # Add any custom claims
        for key, value in claims.items():
            setattr(self, key, value)
    
    def get(self, key: str, default=None):
        """Get token claim value."""
        return getattr(self, key, default)
    
    def __getitem__(self, key: str):
        """Dictionary-style access."""
        return getattr(self, key)
    
    def __contains__(self, key: str):
        """Check if key exists in token."""
        return hasattr(self, key)


class FakeAuthError(Exception):
    """Fake Firebase Auth error."""
    
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class FakeFirebaseAuth:
    """Fake Firebase Auth service."""
    
    def __init__(self):
        self._users: Dict[str, FakeUserRecord] = {}
        self._tokens: Dict[str, FakeDecodedToken] = {}
        self._create_default_users()
    
    def _create_default_users(self):
        """Create some default test users."""
        default_users = [
            ("test-user-123", "test@example.com", "Test User"),
            ("admin-user", "admin@worldarchitect.ai", "Admin User"),
            ("player-user", "player@test.com", "Player User")
        ]
        
        for uid, email, name in default_users:
            user = FakeUserRecord(uid, email, name)
            self._users[uid] = user
            # Create a default token for each user
            token = FakeDecodedToken(uid, email)
            self._tokens[f"token-{uid}"] = token
    
    def get_user(self, uid: str) -> FakeUserRecord:
        """Get user by UID."""
        if uid not in self._users:
            raise FakeAuthError("user-not-found", f"No user record found for UID: {uid}")
        return self._users[uid]
    
    def get_user_by_email(self, email: str) -> FakeUserRecord:
        """Get user by email."""
        for user in self._users.values():
            if user.email == email:
                return user
        raise FakeAuthError("user-not-found", f"No user record found for email: {email}")
    
    def create_user(self, uid: str = None, email: str = None, display_name: str = None, **kwargs) -> FakeUserRecord:
        """Create a new user."""
        if uid is None:
            # Generate a UID from email or random
            if email:
                uid = hashlib.md5(email.encode()).hexdigest()[:20]
            else:
                uid = f"generated-{int(time.time())}"
        
        if uid in self._users:
            raise FakeAuthError("uid-already-exists", f"User with UID {uid} already exists")
        
        user = FakeUserRecord(uid, email, display_name)
        self._users[uid] = user
        return user
    
    def update_user(self, uid: str, **kwargs) -> FakeUserRecord:
        """Update an existing user."""
        if uid not in self._users:
            raise FakeAuthError("user-not-found", f"No user record found for UID: {uid}")
        
        user = self._users[uid]
        
        if 'email' in kwargs:
            user.email = kwargs['email']
        if 'display_name' in kwargs:
            user.display_name = kwargs['display_name']
        if 'disabled' in kwargs:
            user.disabled = kwargs['disabled']
        if 'custom_claims' in kwargs:
            user.custom_claims = kwargs['custom_claims']
        
        return user
    
    def delete_user(self, uid: str):
        """Delete a user."""
        if uid not in self._users:
            raise FakeAuthError("user-not-found", f"No user record found for UID: {uid}")
        
        del self._users[uid]
        # Clean up associated tokens
        tokens_to_remove = [token_id for token_id, token in self._tokens.items() if token.uid == uid]
        for token_id in tokens_to_remove:
            del self._tokens[token_id]
    
    def verify_id_token(self, id_token: str, check_revoked: bool = False) -> FakeDecodedToken:
        """Verify an ID token."""
        # For testing, accept specific test tokens
        if id_token in self._tokens:
            token = self._tokens[id_token]
            # Check if token is expired
            if token.exp < time.time():
                raise FakeAuthError("id-token-expired", "The Firebase ID token has expired")
            return token
        
        # For test mode, create a token from the token string if it looks like a UID
        if id_token.startswith("test-") or id_token in self._users:
            uid = id_token
            if uid in self._users:
                user = self._users[uid]
                return FakeDecodedToken(uid, user.email)
        
        raise FakeAuthError("invalid-id-token", "The Firebase ID token is invalid")
    
    def create_custom_token(self, uid: str, developer_claims: Dict = None) -> str:
        """Create a custom token."""
        if uid not in self._users:
            raise FakeAuthError("user-not-found", f"No user record found for UID: {uid}")
        
        # Return a fake token string
        claims = developer_claims or {}
        token_data = f"custom-token-{uid}-{int(time.time())}"
        
        # Store the token for later verification
        decoded_token = FakeDecodedToken(uid, self._users[uid].email, **claims)
        self._tokens[token_data] = decoded_token
        
        return token_data
    
    def set_custom_user_claims(self, uid: str, custom_claims: Dict):
        """Set custom claims for a user."""
        if uid not in self._users:
            raise FakeAuthError("user-not-found", f"No user record found for UID: {uid}")
        
        self._users[uid].custom_claims = custom_claims
    
    def list_users(self, page_token: str = None, max_results: int = 1000) -> 'FakeListUsersPage':
        """List users."""
        users = list(self._users.values())
        return FakeListUsersPage(users, page_token)


class FakeListUsersPage:
    """Fake list users page result."""
    
    def __init__(self, users: List[FakeUserRecord], page_token: str = None):
        self.users = users
        self.next_page_token = None  # For simplicity, no pagination
        self.has_next_page = False
    
    def iterate_all(self):
        """Iterate over all users."""
        return iter(self.users)


# Convenience functions for test setup
def create_fake_auth() -> FakeFirebaseAuth:
    """Create a fake Firebase Auth service for testing."""
    return FakeFirebaseAuth()


def create_test_token(uid: str = "test-user-123", email: str = None) -> str:
    """Create a test token for a specific user."""
    auth_service = create_fake_auth()
    if uid not in auth_service._users:
        auth_service.create_user(uid=uid, email=email)
    return auth_service.create_custom_token(uid)