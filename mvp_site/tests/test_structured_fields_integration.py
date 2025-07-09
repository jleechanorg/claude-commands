#!/usr/bin/env python3
"""
Integration test for structured fields flow through main, gemini_service, and firestore_service.
Only mocks external services (Gemini API and Firestore database), not Python modules.
"""
import unittest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
import constants


class TestStructuredFieldsIntegration(unittest.TestCase):
    """Integration test for structured fields through the full stack"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Test data
        self.user_id = 'test-user-123'
        self.campaign_id = 'test-campaign-456'
        
        # Headers for test authentication
        self.test_headers = {
            'X-Test-Bypass': 'true',
            'X-Test-User-Id': self.user_id
        }


if __name__ == '__main__':
    unittest.main()