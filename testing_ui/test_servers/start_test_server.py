#!/usr/bin/env python3
"""
Start Flask server with TESTING mode properly enabled
"""

import sys
import os

# Add mvp_site to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

# Set required environment variables
os.environ['TESTING'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''  # Empty string instead of /dev/null

# Mock Firebase Admin to avoid credential issues
import firebase_admin
from unittest.mock import Mock, MagicMock

# Create mock Firestore client
mock_db = MagicMock()
mock_firestore = MagicMock()
mock_firestore.client.return_value = mock_db

# Mock the Firebase admin initialization
firebase_admin._apps = {'[DEFAULT]': Mock()}  # Pretend it's already initialized

# Replace firestore module with mock
sys.modules['firebase_admin.firestore'] = mock_firestore

# Now import the app
from main import create_app

if __name__ == "__main__":
    app = create_app()
    
    # CRITICAL: Enable testing mode
    app.config['TESTING'] = True
    
    print("="*60)
    print("🚀 TEST SERVER STARTING WITH TESTING MODE ENABLED")
    print("✅ app.config['TESTING'] = True")
    print("✅ Test bypass headers will work!")
    print("✅ Using mock Firestore (no credentials needed)")
    print("📍 Server at: http://localhost:8082")
    print("="*60)
    
    # Run on a different port to avoid conflicts
    app.run(host='0.0.0.0', port=8082, debug=False)