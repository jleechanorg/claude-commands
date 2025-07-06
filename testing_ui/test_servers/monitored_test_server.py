#!/usr/bin/env python3
"""
Test server with comprehensive logging and error monitoring
"""

import sys
import os
import logging
import json
import traceback
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

os.environ['TESTING'] = 'true'

# Set up comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/combat_bug_debug.log'),
        logging.StreamHandler()
    ]
)

# Suppress some noisy loggers
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('google').setLevel(logging.WARNING)

from main import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = False  # We'll handle them

# Custom error handler to capture ALL errors
@app.errorhandler(Exception)
def handle_exception(e):
    # Log the full error
    error_id = datetime.now().strftime('%Y%m%d_%H%M%S')
    logging.error(f"\n{'='*70}")
    logging.error(f"ERROR ID: {error_id}")
    logging.error(f"ERROR TYPE: {type(e).__name__}")
    logging.error(f"ERROR MESSAGE: {str(e)}")
    logging.error(f"{'='*70}")
    logging.error(f"FULL TRACEBACK:\n{traceback.format_exc()}")
    logging.error(f"{'='*70}\n")
    
    # Return JSON response with error details
    return {
        'error': str(e),
        'error_type': type(e).__name__,
        'error_id': error_id,
        'traceback': traceback.format_exc()
    }, 500

print("="*70)
print("🔍 MONITORED TEST SERVER")
print("✅ Full error logging to: /tmp/combat_bug_debug.log")
print("✅ JSON error responses enabled")
print("✅ TESTING mode active")
print("📍 Server at: http://localhost:8086")
print("="*70)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8086, debug=False)