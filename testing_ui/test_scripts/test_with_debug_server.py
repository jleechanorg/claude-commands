#!/usr/bin/env python3
"""
Start server with debug mode to see actual errors
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

os.environ['TESTING'] = 'true'

from main import create_app

app = create_app()
app.config['TESTING'] = True
app.config['DEBUG'] = True  # Enable debug for error details
app.config['PROPAGATE_EXCEPTIONS'] = True  # Show full errors

print("="*60)
print("🚀 DEBUG SERVER WITH TESTING ENABLED")
print("✅ Errors will be shown as JSON")
print("📍 Server at: http://localhost:8084")
print("="*60)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8084, debug=True)