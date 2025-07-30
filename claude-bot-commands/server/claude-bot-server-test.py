#!/usr/bin/env python3
"""
Test version of Claude endpoint server for GitHub slash commands.
This version simulates Claude responses without requiring the actual Claude Code CLI.
Use this for testing the GitHub integration workflow.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import logging
import time
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeTestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/claude':
            try:
                # Parse the POST data
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length).decode('utf-8')

                # Handle both form-encoded and JSON data
                if self.headers.get('Content-Type', '').startswith('application/json'):
                    data = json.loads(post_data)
                    prompt = data.get('prompt', '')
                else:
                    # Form-encoded data
                    parsed_data = urllib.parse.parse_qs(post_data)
                    prompt = parsed_data.get('prompt', [''])[0]

                logger.info(f"Received prompt: {prompt[:100]}...")

                # Simulate processing time
                time.sleep(2)

                # Generate a test response
                response = f"""**🤖 Claude Test Response**

You asked: "{prompt}"

This is a simulated response from the Claude endpoint test server. The actual system would forward this prompt to Claude Code CLI and return the real response.

**System Status:**
- ✅ Endpoint server working
- ✅ Request parsing successful
- ✅ Response formatting complete
- 🧪 Test mode active

**Next Steps:**
1. Configure GitHub secrets (REPO_ACCESS_TOKEN, CLAUDE_ENDPOINT)
2. Set up self-hosted runner with 'claude' label
3. Replace with real claude-endpoint-server.py for production

Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}"""

                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))

                logger.info(f"Sent test response for prompt: {prompt[:50]}...")

            except Exception as e:
                logger.error(f"Error processing request: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Internal server error: {str(e)}".encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Claude test endpoint server is running")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # Override to use our logger
        logger.info(format % args)

if __name__ == '__main__':
    port = int(os.getenv('CLAUDE_ENDPOINT_PORT', '5001'))
    server = HTTPServer(('127.0.0.1', port), ClaudeTestHandler)
    logger.info(f"Starting Claude TEST endpoint server on http://127.0.0.1:{port}")
    logger.info("🧪 TEST MODE: This server simulates Claude responses")
    logger.info("Health check available at http://127.0.0.1:{}/health".format(port))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down test server...")
