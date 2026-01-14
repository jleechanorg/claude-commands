"""
Service Account Credentials Loader - Secure Google Cloud Authentication

This module provides flexible service account credential loading for Google Cloud services
(Firebase Admin, Cloud Storage, Vertex AI, BigQuery, etc.) with ZERO hardcoded secrets.

Supports TWO loading methods:
1. FILE-BASED: Load from serviceAccount.json file (traditional approach)
2. ENV VARS: Load credentials from environment variables (secure, git-safe)

Why This Pattern is Safe for Git:
- NO sensitive values are hardcoded in the code
- The credentials dict structure is a TEMPLATE that pulls values from env vars at runtime
- Environment variables are NEVER committed to git (they live in .env, Claude.ai settings, or GitHub Secrets)
- This code can be safely committed, shared, and open-sourced

Environment Variable Configuration:
The following environment variables are required when using env var loading:

REQUIRED:
- GOOGLE_PROJECT_ID: Your GCP project ID (e.g., "my-project-12345")
- GOOGLE_CLIENT_EMAIL: Service account email (e.g., "my-sa@my-project.iam.gserviceaccount.com")
- GOOGLE_PRIVATE_KEY: Full private key PEM string with \\n escape sequences
  (e.g., "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBg...\\n-----END PRIVATE KEY-----\\n")

OPTIONAL (recommended for full compatibility):
- GOOGLE_PRIVATE_KEY_ID: Private key ID from the service account JSON
- GOOGLE_CLIENT_ID: Client ID from the service account JSON

How to Set Environment Variables:

1. Claude.ai Projects:
   - Go to Project Settings → Environment Variables
   - Add each variable with its value
   - Variables are encrypted and never exposed in logs

2. Local Development (.env file):
   - Create .env file in project root (NEVER commit this file)
   - Add to .gitignore: echo ".env" >> .gitignore
   - Use python-dotenv to load:
     ```python
     from dotenv import load_dotenv
     load_dotenv()
     ```
   - Example .env format:
     ```
     GOOGLE_PROJECT_ID=my-project-12345
     GOOGLE_CLIENT_EMAIL=my-sa@my-project.iam.gserviceaccount.com
     GOOGLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\\nMIIE...\\n-----END PRIVATE KEY-----\\n"
     ```

3. GitHub Actions / CI:
   - Add as Repository Secrets (Settings → Secrets and variables → Actions)
   - Reference in workflow: ${{ secrets.GOOGLE_PRIVATE_KEY }}

4. Cloud Run / Production:
   - Set as environment variables in deployment configuration
   - Use Secret Manager for enhanced security

Usage Examples:

Example 1: Try file first, fallback to env vars (RECOMMENDED):
```python
from mvp_site.service_account_loader import get_service_account_credentials

# Try file first, then env vars
creds = get_service_account_credentials(
    file_path="~/serviceAccountKey.json",
    fallback_to_env=True
)

# Use with Firebase Admin
import firebase_admin
from firebase_admin import credentials
firebase_admin.initialize_app(credentials.Certificate(creds))
```

Example 2: Env vars only (sandbox/serverless environments):
```python
# Force env var loading (useful for Claude.ai, Replit, etc.)
creds = get_service_account_credentials(
    file_path=None,
    fallback_to_env=True,
    require_env_vars=True
)
```

Example 3: File only (traditional approach):
```python
# Only load from file, no env var fallback
creds = get_service_account_credentials(
    file_path="~/serviceAccountKey.json",
    fallback_to_env=False
)
```

Security Notes:
- NEVER commit .env files or serviceAccount.json to git
- NEVER hardcode credentials in source code
- NEVER log or print credential values
- Use environment-specific secrets management (Secret Manager in production)
- Rotate service account keys regularly
"""

import json
import os
from typing import Any

from mvp_site import logging_util


class ServiceAccountLoadError(Exception):
    """Raised when service account credentials cannot be loaded."""


def get_service_account_credentials(
    file_path: str | None = None,
    fallback_to_env: bool = True,
    require_env_vars: bool = False,
) -> dict[str, Any]:
    """
    Load Google service account credentials from file or environment variables.

    This function tries multiple loading strategies in order:
    1. Load from file (if file_path provided and exists)
    2. Load from environment variables (if fallback_to_env=True)

    Args:
        file_path: Path to serviceAccount.json file (supports ~ expansion)
                  If None, skips file loading
        fallback_to_env: If True, try loading from env vars when file fails
        require_env_vars: If True, ONLY load from env vars (ignore file_path)

    Returns:
        dict: Service account credentials dictionary compatible with
              google.oauth2.service_account.Credentials.from_service_account_info()
              and firebase_admin.credentials.Certificate()

    Raises:
        ServiceAccountLoadError: If credentials cannot be loaded from any source

    Environment Variables Required (when using env var loading):
        GOOGLE_PROJECT_ID: GCP project ID
        GOOGLE_CLIENT_EMAIL: Service account email
        GOOGLE_PRIVATE_KEY: Private key PEM string (with \\n escape sequences)
        GOOGLE_PRIVATE_KEY_ID: (optional) Private key ID
        GOOGLE_CLIENT_ID: (optional) Client ID
    """
    # Strategy 1: Try loading from file (unless require_env_vars is True)
    if not require_env_vars and file_path:
        try:
            expanded_path = os.path.expanduser(file_path)
            if os.path.exists(expanded_path):
                logging_util.info(
                    f"Loading service account from file: {expanded_path}"
                )
                with open(expanded_path) as f:
                    creds = json.load(f)
                    _validate_credentials_dict(creds, source="file")
                    logging_util.info(
                        f"✅ Successfully loaded credentials from file: {expanded_path}"
                    )
                    return creds
            else:
                logging_util.warning(
                    f"Service account file not found: {expanded_path}"
                )
        except Exception as e:
            logging_util.warning(
                f"Failed to load credentials from file {file_path}: {e}"
            )
            if not fallback_to_env:
                raise ServiceAccountLoadError(
                    f"Failed to load credentials from file {file_path}: {e}"
                ) from e

    # Strategy 2: Try loading from environment variables
    if fallback_to_env or require_env_vars:
        try:
            logging_util.info("Attempting to load service account from environment variables")
            creds = _load_credentials_from_env()
            _validate_credentials_dict(creds, source="environment variables")
            logging_util.info(
                "✅ Successfully loaded credentials from environment variables"
            )
            return creds
        except ServiceAccountLoadError as e:
            if require_env_vars:
                # If env vars were explicitly required, propagate the error
                raise
            logging_util.warning(f"Failed to load credentials from env vars: {e}")

    # If we get here, all strategies failed
    error_msg = "Failed to load service account credentials from any source. "
    if file_path:
        error_msg += f"File path '{file_path}' not found or invalid. "
    if fallback_to_env or require_env_vars:
        error_msg += "Environment variables missing or incomplete (need GOOGLE_PROJECT_ID, GOOGLE_CLIENT_EMAIL, GOOGLE_PRIVATE_KEY)."
    else:
        error_msg += "Environment variable fallback is disabled."

    raise ServiceAccountLoadError(error_msg)


def _load_credentials_from_env() -> dict[str, Any]:
    """
    Load service account credentials from environment variables.

    Required Environment Variables:
        GOOGLE_PROJECT_ID: GCP project ID
        GOOGLE_CLIENT_EMAIL: Service account email
        GOOGLE_PRIVATE_KEY: Private key PEM string

    Optional Environment Variables:
        GOOGLE_PRIVATE_KEY_ID: Private key ID
        GOOGLE_CLIENT_ID: Client ID

    Returns:
        dict: Service account credentials dictionary

    Raises:
        ServiceAccountLoadError: If required env vars are missing
    """
    # Check required environment variables
    project_id = os.environ.get("GOOGLE_PROJECT_ID")
    client_email = os.environ.get("GOOGLE_CLIENT_EMAIL")
    private_key = os.environ.get("GOOGLE_PRIVATE_KEY")

    # Validate required fields
    missing_vars = []
    if not project_id:
        missing_vars.append("GOOGLE_PROJECT_ID")
    if not client_email:
        missing_vars.append("GOOGLE_CLIENT_EMAIL")
    if not private_key:
        missing_vars.append("GOOGLE_PRIVATE_KEY")

    if missing_vars:
        raise ServiceAccountLoadError(
            f"Missing required environment variables: {', '.join(missing_vars)}. "
            "Please set these variables in your environment (.env file, Claude.ai project settings, "
            "or GitHub Secrets). See module docstring for detailed instructions."
        )

    # Optional fields (enhance compatibility but not strictly required)
    private_key_id = os.environ.get("GOOGLE_PRIVATE_KEY_ID", "")
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")

    # Build the credentials dictionary
    # This matches the structure of a Google service account JSON file
    creds_dict = {
        "type": "service_account",
        "project_id": project_id,
        "private_key_id": private_key_id,  # Optional but recommended
        "private_key": private_key,
        "client_email": client_email,
        "client_id": client_id,  # Optional but recommended
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email.replace('@', '%40')}",
    }

    logging_util.debug(
        f"Loaded credentials for project: {project_id}, "
        f"service account: {client_email[:20]}..."
    )

    return creds_dict


def _validate_credentials_dict(creds: dict[str, Any], source: str) -> None:
    """
    Validate that credentials dictionary has required fields.

    Args:
        creds: Credentials dictionary to validate
        source: Human-readable source name for error messages

    Raises:
        ServiceAccountLoadError: If required fields are missing
    """
    required_fields = ["type", "project_id", "private_key", "client_email"]
    missing_fields = [field for field in required_fields if not creds.get(field)]

    if missing_fields:
        raise ServiceAccountLoadError(
            f"Invalid credentials from {source}: missing required fields: {', '.join(missing_fields)}"
        )

    # Validate type field
    if creds.get("type") != "service_account":
        raise ServiceAccountLoadError(
            f"Invalid credentials from {source}: 'type' must be 'service_account', "
            f"got '{creds.get('type')}'"
        )

    # Basic validation for private key format
    private_key = creds.get("private_key", "")
    if not private_key.startswith("-----BEGIN PRIVATE KEY-----"):
        raise ServiceAccountLoadError(
            f"Invalid credentials from {source}: private_key must be a valid PEM-formatted key "
            "starting with '-----BEGIN PRIVATE KEY-----'"
        )

    logging_util.debug(f"✅ Credentials from {source} validated successfully")


# Example usage for testing (not executed when imported)
if __name__ == "__main__":
    import sys

    print("=== Service Account Loader Test ===\n")

    # Example: Try loading with fallback
    try:
        print("Attempting to load credentials (file first, then env vars)...")
        creds = get_service_account_credentials(
            file_path="~/serviceAccountKey.json",
            fallback_to_env=True
        )
        print(f"✅ Successfully loaded credentials!")
        print(f"   Project ID: {creds.get('project_id')}")
        print(f"   Service Account: {creds.get('client_email')}")
        print(f"   Source: {'file' if os.path.exists(os.path.expanduser('~/serviceAccountKey.json')) else 'environment variables'}")
    except ServiceAccountLoadError as e:
        print(f"❌ Failed to load credentials: {e}")
        print("\nTo use environment variables, set these variables:")
        print("  - GOOGLE_PROJECT_ID")
        print("  - GOOGLE_CLIENT_EMAIL")
        print("  - GOOGLE_PRIVATE_KEY")
        sys.exit(1)

    print("\n=== Test Complete ===")
