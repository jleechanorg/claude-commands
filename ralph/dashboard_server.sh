#!/bin/bash
# Ralph Dashboard Web Server
# Port 9450
# Usage: ./dashboard_server.sh or ./ralph/dashboard_server.sh [--open]

set -e

cleanup() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

PORT=9450
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PRD="$SCRIPT_DIR/prd.json"
PROGRESS="$SCRIPT_DIR/progress.txt"
HTML="$SCRIPT_DIR/dashboard.html"

# Kill existing server on this port
EXISTING_PID=$(lsof -ti:$PORT 2>/dev/null || true)
if [ -n "$EXISTING_PID" ]; then
  echo "⚠️  Killing existing process on port $PORT (PID: $EXISTING_PID)"
  kill $EXISTING_PID 2>/dev/null || true
  sleep 1
fi

echo "🐺 Ralph Dashboard starting on http://localhost:$PORT"

# Simple HTTP server using Python with API endpoint
python3 -c "
import http.server, json, subprocess, os, time, socketserver

PORT = $PORT
REPO = '$REPO_ROOT'
PRD = '$PRD'
PROGRESS = '$PROGRESS'
HTML = '$HTML'

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(get_status()).encode())
        elif self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            with open(HTML, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs

def get_status():
    # Read PRD
    try:
        with open(PRD) as f:
            prd = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
        import sys
        print(f'Error reading prd.json: {e}', file=sys.stderr)
        return {'error': f'Cannot read prd.json: {e}'}

    stories = prd.get('userStories', [])
    total = len(stories)
    passed = sum(1 for s in stories if s.get('passes'))

    # Phase breakdown: derive from story ID prefixes (e.g. P1-, P15-, T1-)
    prefix_groups = {}
    for s in stories:
        sid = s.get('id', '')
        prefix = sid.split('-')[0] + '-' if '-' in sid else sid
        if prefix not in prefix_groups:
            prefix_groups[prefix] = []
        prefix_groups[prefix].append(s)
    phases = []
    for prefix in sorted(prefix_groups.keys()):
        ph_stories = prefix_groups[prefix]
        phases.append({
            'name': prefix.rstrip('-'),
            'total': len(ph_stories),
            'done': sum(1 for s in ph_stories if s.get('passes'))
        })

    # Next story
    next_s = next((s for s in stories if not s.get('passes')), None)
    next_story = f\"{next_s['id']}: {next_s['title']}\" if next_s else None

    # Recent commits
    commits = []
    try:
        out = subprocess.check_output(
            ['git', 'log', '--format=%h|%ar|%ct|%s', '-10'],
            cwd=REPO, text=True, timeout=5
        )
        for line in out.strip().split('\n'):
            if '|' in line:
                parts = line.split('|', 3)
                commits.append({'hash': parts[0], 'ago': parts[1], 'ts': int(parts[2]), 'message': parts[3]})
    except Exception as e:
        import sys
        print(f'Error reading git log: {e}', file=sys.stderr)

    # Elapsed since last commit
    elapsed = None
    if commits:
        elapsed = int(time.time()) - commits[0]['ts']

    # Ralph running?
    ralph_running = False
    ralph_pid = None
    try:
        out = subprocess.check_output(['pgrep', '-f', 'ralph/ralph.sh'], text=True, timeout=3)
        pids = out.strip().split('\n')
        if pids and pids[0]:
            ralph_running = True
            ralph_pid = pids[0]
    except subprocess.CalledProcessError:
        pass  # pgrep returns non-zero when no match (expected)

    return {
        'total': total,
        'passed': passed,
        'phases': phases,
        'next_story': next_story,
        'commits': commits,
        'last_commit_elapsed_sec': elapsed,
        'ralph_running': ralph_running,
        'ralph_pid': ralph_pid,
        'stories': [{'id': s['id'], 'title': s['title'], 'passes': s.get('passes', False)} for s in stories],
    }

with socketserver.TCPServer(('', PORT), Handler) as httpd:
    httpd.serve_forever()
" &

SERVER_PID=$!
echo "Server PID: $SERVER_PID"
sleep 1

if [ "${1:-}" = "--open" ] || [ "${1:-}" = "-o" ]; then
  if command -v open >/dev/null 2>&1; then
    open "http://localhost:$PORT"
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "http://localhost:$PORT"
  else
    echo "INFO: No browser opener found. Open http://localhost:$PORT manually."
  fi
fi

echo "Dashboard: http://localhost:$PORT"
echo "Press Ctrl+C to stop"
wait $SERVER_PID
