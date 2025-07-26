#!/usr/bin/env python3
"""
Local Claude endpoint server for GitHub slash commands.
Runs a simple HTTP server that accepts prompts and forwards them to Claude Code CLI.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import json
import urllib.parse
import logging
import tempfile
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ClaudeHandler(BaseHTTPRequestHandler):
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
                
                # Create a temporary file with the prompt
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    f.write(prompt)
                    temp_file = f.name
                
                try:
                    # Call Claude Code CLI with the prompt
                    # Adjust this command based on how Claude Code is installed on your system
                    result = subprocess.run([
                        'claude-code', 
                        '--message', prompt
                    ], capture_output=True, text=True, timeout=60)
                    
                    if result.returncode == 0:
                        response = result.stdout
                    else:
                        response = f"Error: {result.stderr}"
                        logger.error(f"Claude Code error: {result.stderr}")
                    
                finally:
                    # Clean up temp file
                    os.unlink(temp_file)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
                
                logger.info(f"Sent response: {response[:100]}...")
                
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
            self.wfile.write(b"Claude endpoint server is running")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Override to use our logger
        logger.info(format % args)

if __name__ == '__main__':
    port = int(os.getenv('CLAUDE_ENDPOINT_PORT', '5001'))
    server = HTTPServer(('127.0.0.1', port), ClaudeHandler)
    logger.info(f"Starting Claude endpoint server on http://127.0.0.1:{port}")
    logger.info("Health check available at http://127.0.0.1:{}/health".format(port))
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()