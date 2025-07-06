#!/usr/bin/env python3
"""
Start server with TESTING mode ACTUALLY enabled
"""

import sys
import os

# Add mvp_site to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

# Set environment
os.environ['TESTING'] = 'true'

# Import Flask app
from main import create_app

# Create app
app = create_app()

# THE KEY FIX: Actually set TESTING in app config!
app.config['TESTING'] = True

print("="*60)
print("🚀 SERVER STARTING WITH TESTING MODE ENABLED")
print(f"✅ app.config['TESTING'] = {app.config.get('TESTING')}")
print("✅ Test bypass headers WILL work!")
print("📍 Server at: http://localhost:8083")
print("="*60)

# Run server
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8083, debug=False)