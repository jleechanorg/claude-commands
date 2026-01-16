#!/usr/bin/env python3
"""
Comprehensive unit tests for service_account_loader.py module.

Tests cover:
- File-based credential loading
- Environment variable credential loading
- Fallback behavior (file -> env vars -> default)
- Error handling for missing credentials
- Validation of credential formats
- Proper error messages
- Private key newline conversion
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import pytest

from mvp_site.service_account_loader import (
    ServiceAccountLoadError,
    _load_credentials_from_env,
    _validate_credentials_dict,
    get_service_account_credentials,
)


class TestServiceAccountLoader(unittest.TestCase):
    """Test cases for service_account_loader module."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_creds_file = os.path.join(self.temp_dir, "test_service_account.json")
        
        # Sample valid service account credentials
        self.valid_creds_dict = {
            "type": "service_account",
            "project_id": "test-project-12345",
            "private_key_id": "test-key-id-12345",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
            "client_email": "test-sa@test-project.iam.gserviceaccount.com",
            "client_id": "123456789012345678901",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test-sa%40test-project.iam.gserviceaccount.com",
        }
        
        # Write valid credentials to test file
        with open(self.test_creds_file, "w") as f:
            json.dump(self.valid_creds_dict, f)
        
        # Clear any existing environment variables
        self.env_vars_to_clear = [
            "GOOGLE_PROJECT_ID",
            "GOOGLE_CLIENT_EMAIL",
            "GOOGLE_PRIVATE_KEY",
            "GOOGLE_PRIVATE_KEY_ID",
            "GOOGLE_CLIENT_ID",
            "WORLDAI_GOOGLE_APPLICATION_CREDENTIALS",
        ]
        self.original_env = {}
        for var in self.env_vars_to_clear:
            self.original_env[var] = os.environ.pop(var, None)

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original environment variables
        for var, value in self.original_env.items():
            if value is None:
                os.environ.pop(var, None)
            else:
                os.environ[var] = value
        
        # Clean up temporary files
        if os.path.exists(self.test_creds_file):
            os.remove(self.test_creds_file)
        os.rmdir(self.temp_dir)

    def test_load_from_file_success(self):
        """Test successful loading from file."""
        creds = get_service_account_credentials(
            file_path=self.test_creds_file,
            fallback_to_env=False
        )
        
        self.assertEqual(creds["type"], "service_account")
        self.assertEqual(creds["project_id"], "test-project-12345")
        self.assertEqual(creds["client_email"], "test-sa@test-project.iam.gserviceaccount.com")
        self.assertIn("private_key", creds)

    def test_load_from_file_with_tilde_expansion(self):
        """Test file loading with ~ expansion."""
        # Create a file in home directory
        home_file = os.path.expanduser("~/test_service_account.json")
        try:
            with open(home_file, "w") as f:
                json.dump(self.valid_creds_dict, f)
            
            creds = get_service_account_credentials(
                file_path="~/test_service_account.json",
                fallback_to_env=False
            )
            
            self.assertEqual(creds["project_id"], "test-project-12345")
        finally:
            if os.path.exists(home_file):
                os.remove(home_file)

    def test_load_from_file_not_found(self):
        """Test error when file doesn't exist."""
        with self.assertRaises(ServiceAccountLoadError) as cm:
            get_service_account_credentials(
                file_path="/nonexistent/file.json",
                fallback_to_env=False
            )
        
        self.assertIn("Failed to load service account credentials", str(cm.exception))

    def test_load_from_file_invalid_json(self):
        """Test error when file contains invalid JSON."""
        invalid_file = os.path.join(self.temp_dir, "invalid.json")
        with open(invalid_file, "w") as f:
            f.write("not valid json")
        
        with self.assertRaises(ServiceAccountLoadError):
            get_service_account_credentials(
                file_path=invalid_file,
                fallback_to_env=False
            )
        
        os.remove(invalid_file)

    def test_load_from_env_vars_success(self):
        """Test successful loading from environment variables."""
        # Set required environment variables
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        # Use escaped \n sequences as documented
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        
        creds = get_service_account_credentials(
            file_path=None,
            fallback_to_env=True,
            require_env_vars=True
        )
        
        self.assertEqual(creds["type"], "service_account")
        self.assertEqual(creds["project_id"], "test-project-12345")
        self.assertEqual(creds["client_email"], "test-sa@test-project.iam.gserviceaccount.com")
        # Verify newlines were converted
        self.assertIn("\n", creds["private_key"])
        self.assertNotIn("\\n", creds["private_key"])

    def test_load_from_env_vars_with_optional_fields(self):
        """Test loading from env vars with optional fields."""
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        os.environ["GOOGLE_PRIVATE_KEY_ID"] = "test-key-id-12345"
        os.environ["GOOGLE_CLIENT_ID"] = "123456789012345678901"
        
        creds = get_service_account_credentials(
            file_path=None,
            fallback_to_env=True,
            require_env_vars=True
        )
        
        self.assertEqual(creds["private_key_id"], "test-key-id-12345")
        self.assertEqual(creds["client_id"], "123456789012345678901")

    def test_load_from_env_vars_missing_required(self):
        """Test error when required environment variables are missing."""
        # Only set one required var
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        # Missing GOOGLE_CLIENT_EMAIL and GOOGLE_PRIVATE_KEY
        
        with self.assertRaises(ServiceAccountLoadError) as cm:
            get_service_account_credentials(
                file_path=None,
                fallback_to_env=True,
                require_env_vars=True
            )
        
        error_msg = str(cm.exception)
        self.assertIn("Missing required environment variables", error_msg)
        self.assertIn("GOOGLE_CLIENT_EMAIL", error_msg)
        self.assertIn("GOOGLE_PRIVATE_KEY", error_msg)

    def test_load_from_env_vars_private_key_newline_conversion(self):
        """Test that \\n escape sequences are converted to actual newlines."""
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        # Private key with escaped newlines
        private_key_with_escapes = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        os.environ["GOOGLE_PRIVATE_KEY"] = private_key_with_escapes
        
        creds = _load_credentials_from_env()
        
        # Verify newlines were converted
        self.assertIn("\n", creds["private_key"])
        self.assertNotIn("\\n", creds["private_key"])
        # Verify PEM format is preserved
        self.assertTrue(creds["private_key"].startswith("-----BEGIN PRIVATE KEY-----"))
        self.assertTrue(creds["private_key"].endswith("-----END PRIVATE KEY-----\n"))

    def test_fallback_file_then_env(self):
        """Test fallback from file to environment variables."""
        # File doesn't exist, but env vars are set
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        
        creds = get_service_account_credentials(
            file_path="/nonexistent/file.json",
            fallback_to_env=True
        )
        
        # Should load from env vars
        self.assertEqual(creds["project_id"], "test-project-12345")

    def test_fallback_file_preferred_over_env(self):
        """Test that file loading is preferred when both file and env vars exist."""
        # Set env vars
        os.environ["GOOGLE_PROJECT_ID"] = "env-project"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "env-sa@env-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nENV_KEY\\n-----END PRIVATE KEY-----\\n"
        
        # File exists with different values
        creds = get_service_account_credentials(
            file_path=self.test_creds_file,
            fallback_to_env=True
        )
        
        # Should load from file (not env vars)
        self.assertEqual(creds["project_id"], "test-project-12345")
        self.assertNotEqual(creds["project_id"], "env-project")

    def test_no_fallback_when_disabled(self):
        """Test that env var fallback doesn't happen when disabled."""
        # Set env vars
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        
        # File doesn't exist and fallback is disabled
        with self.assertRaises(ServiceAccountLoadError) as cm:
            get_service_account_credentials(
                file_path="/nonexistent/file.json",
                fallback_to_env=False
            )
        
        error_msg = str(cm.exception)
        self.assertIn("Failed to load service account credentials", error_msg)
        self.assertIn("Environment variable fallback is disabled", error_msg)

    def test_require_env_vars_ignores_file(self):
        """Test that require_env_vars=True ignores file_path."""
        # File exists
        # But require_env_vars=True should force env var loading
        os.environ["GOOGLE_PROJECT_ID"] = "env-project"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "env-sa@env-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nENV_KEY\\n-----END PRIVATE KEY-----\\n"
        
        creds = get_service_account_credentials(
            file_path=self.test_creds_file,  # File exists but should be ignored
            fallback_to_env=True,
            require_env_vars=True
        )
        
        # Should load from env vars (not file)
        self.assertEqual(creds["project_id"], "env-project")

    def test_validate_credentials_dict_success(self):
        """Test successful validation of credentials dictionary."""
        # Should not raise
        _validate_credentials_dict(self.valid_creds_dict, source="test")

    def test_validate_credentials_dict_missing_required_field(self):
        """Test validation error when required field is missing."""
        invalid_creds = self.valid_creds_dict.copy()
        del invalid_creds["project_id"]
        
        with self.assertRaises(ServiceAccountLoadError) as cm:
            _validate_credentials_dict(invalid_creds, source="test")
        
        error_msg = str(cm.exception)
        self.assertIn("missing required fields", error_msg)
        self.assertIn("project_id", error_msg)

    def test_validate_credentials_dict_wrong_type(self):
        """Test validation error when type is not 'service_account'."""
        invalid_creds = self.valid_creds_dict.copy()
        invalid_creds["type"] = "user_account"
        
        with self.assertRaises(ServiceAccountLoadError) as cm:
            _validate_credentials_dict(invalid_creds, source="test")
        
        error_msg = str(cm.exception)
        self.assertIn("'type' must be 'service_account'", error_msg)

    def test_validate_credentials_dict_invalid_private_key_format(self):
        """Test validation error when private key format is invalid."""
        invalid_creds = self.valid_creds_dict.copy()
        invalid_creds["private_key"] = "not a valid PEM key"
        
        with self.assertRaises(ServiceAccountLoadError) as cm:
            _validate_credentials_dict(invalid_creds, source="test")
        
        error_msg = str(cm.exception)
        self.assertIn("private_key must be a valid PEM-formatted key", error_msg)
        self.assertIn("-----BEGIN PRIVATE KEY-----", error_msg)

    def test_validate_credentials_dict_empty_private_key(self):
        """Test validation error when private key is empty."""
        invalid_creds = self.valid_creds_dict.copy()
        invalid_creds["private_key"] = ""
        
        with self.assertRaises(ServiceAccountLoadError) as cm:
            _validate_credentials_dict(invalid_creds, source="test")
        
        error_msg = str(cm.exception)
        self.assertIn("missing required fields", error_msg)
        self.assertIn("private_key", error_msg)

    def test_error_messages_are_clear(self):
        """Test that error messages provide clear guidance."""
        # Test missing env vars error
        with self.assertRaises(ServiceAccountLoadError) as cm:
            get_service_account_credentials(
                file_path=None,
                fallback_to_env=True,
                require_env_vars=True
            )
        
        error_msg = str(cm.exception)
        self.assertIn("Missing required environment variables", error_msg)
        self.assertIn("GOOGLE_PROJECT_ID", error_msg)
        self.assertIn("GOOGLE_CLIENT_EMAIL", error_msg)
        self.assertIn("GOOGLE_PRIVATE_KEY", error_msg)
        # Should mention where to set them
        error_msg_lower = error_msg.lower()
        self.assertTrue(
            ".env file" in error_msg_lower or "claude.ai" in error_msg_lower
        )

    def test_creds_dict_structure_matches_google_format(self):
        """Test that credentials dictionary matches Google service account JSON format."""
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        
        creds = _load_credentials_from_env()
        
        # Check all required fields
        self.assertEqual(creds["type"], "service_account")
        self.assertIn("project_id", creds)
        self.assertIn("private_key", creds)
        self.assertIn("client_email", creds)
        self.assertIn("auth_uri", creds)
        self.assertIn("token_uri", creds)
        self.assertIn("auth_provider_x509_cert_url", creds)
        self.assertIn("client_x509_cert_url", creds)
        
        # Check auth_uri and token_uri are correct
        self.assertEqual(creds["auth_uri"], "https://accounts.google.com/o/oauth2/auth")
        self.assertEqual(creds["token_uri"], "https://oauth2.googleapis.com/token")

    def test_client_x509_cert_url_encoding(self):
        """Test that client_x509_cert_url properly encodes @ symbol."""
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        
        creds = _load_credentials_from_env()
        
        # @ should be encoded as %40
        self.assertIn("%40", creds["client_x509_cert_url"])
        self.assertNotIn("@", creds["client_x509_cert_url"])

    def test_optional_fields_default_to_empty_string(self):
        """Test that optional fields default to empty string when not set."""
        os.environ["GOOGLE_PROJECT_ID"] = "test-project-12345"
        os.environ["GOOGLE_CLIENT_EMAIL"] = "test-sa@test-project.iam.gserviceaccount.com"
        os.environ["GOOGLE_PRIVATE_KEY"] = "-----BEGIN PRIVATE KEY-----\\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\\n-----END PRIVATE KEY-----\\n"
        # Don't set optional fields
        
        creds = _load_credentials_from_env()
        
        self.assertEqual(creds["private_key_id"], "")
        self.assertEqual(creds["client_id"], "")


if __name__ == "__main__":
    unittest.main()
