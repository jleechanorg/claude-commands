#!/usr/bin/env python3
"""
Run the Flask server with TESTING mode enabled
"""

import sys
import os

# Add the mvp_site directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mvp_site'))

# Set environment variables
os.environ['TESTING'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/dev/null'

# Import and run the app
from main import create_app

if __name__ == "__main__":
    app = create_app()
    app.config['TESTING'] = True  # This is the key!
    
    print("🚀 Starting server with TESTING mode enabled...")
    print("✅ Test bypass headers will work!")
    print("📍 Server running at http://localhost:8081")
    
    app.run(host='0.0.0.0', port=8081, debug=True)