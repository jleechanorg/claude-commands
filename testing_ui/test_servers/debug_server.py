#!/usr/bin/env python3
"""
Debug server that will show us the actual 500 error
"""

import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mvp_site')))

os.environ['TESTING'] = 'true'

# Set up logging to capture errors
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/debug_server_errors.log'),
        logging.StreamHandler()
    ]
)

from main import create_app

app = create_app()
app.config['TESTING'] = True
app.config['PROPAGATE_EXCEPTIONS'] = True

# Custom error handler to log 500 errors
@app.errorhandler(500)
def internal_error(error):
    import traceback
    error_trace = traceback.format_exc()
    logging.error(f"500 ERROR:\n{error_trace}")
    
    # Return JSON with error details
    return {
        'error': str(error),
        'traceback': error_trace
    }, 500

print("="*60)
print("🔍 DEBUG SERVER - Will capture 500 errors")
print("✅ Errors logged to: /tmp/debug_server_errors.log")
print("📍 Server at: http://localhost:8085")
print("="*60)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8085, debug=False)  # debug=False to use our handler