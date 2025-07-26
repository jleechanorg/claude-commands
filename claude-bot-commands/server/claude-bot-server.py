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

                # Handle null/empty prompts
                if not prompt or prompt == 'null' or prompt.strip() == '':
                    response = "❌ Error: No prompt provided or prompt is empty"
                    logger.warning("Received empty or null prompt")
                    self.send_response(400)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(response.encode('utf-8'))
                    return

                logger.info(f"Received prompt: {prompt[:100]}...")

                # Call Claude Code CLI with environment awareness
                try:
                    # Detect testing environment
                    is_testing = (os.getenv('TESTING') == 'true' or
                                os.getenv('CI') == 'true' or
                                'test' in __file__.lower())

                    # Use shorter timeout in testing environments
                    timeout = 3 if is_testing else 15

                    # Try to find Claude Code CLI
                    claude_cmd = None
                    possible_paths = [
                        os.path.expanduser('~/.claude/local/claude'),  # User-specific path first
                        '/usr/local/bin/claude',
                        '/opt/homebrew/bin/claude',
                        'claude'  # In PATH
                    ]

                    for cmd_path in possible_paths:
                        try:
                            result = subprocess.run([cmd_path, '--version'],
                                                  capture_output=True, text=True, timeout=2)
                            if result.returncode == 0:
                                claude_cmd = cmd_path
                                logger.info(f"Found Claude CLI at: {cmd_path}")
                                break
                        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                            continue

                    if claude_cmd:
                        # Use Claude CLI with appropriate timeout
                        logger.info(f"Calling Claude CLI with timeout: {timeout}s")
                        result = subprocess.run([claude_cmd, prompt],
                                              capture_output=True, text=True, timeout=timeout, check=False)
                        if result.returncode == 0 and result.stdout.strip():
                            response = result.stdout.strip()
                            logger.info(f"Claude CLI response received: {len(response)} chars")
                        else:
                            response = "❌ Error: Claude CLI execution failed or returned empty response"
                            logger.error(f"Claude CLI error: {result.stderr}")
                    else:
                        response = ("❌ Error: Claude Code CLI not found.\n\n"
                                  "Please ensure Claude Code is properly installed and in your PATH.\n\n"
                                  "Visit: https://docs.anthropic.com/en/docs/claude-code")
                        logger.error("Claude Code CLI not found in any expected location")

                except subprocess.TimeoutExpired:
                    response = f"❌ Error: Claude CLI timed out after {timeout}s (testing environment detected)"
                    logger.error(f"Claude CLI timeout after {timeout}s")
                except Exception as e:
                    response = f"❌ Error calling Claude: {str(e)}"
                    logger.error(f"Exception calling Claude: {e}")

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
