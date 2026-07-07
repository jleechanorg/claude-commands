#!/usr/bin/env python3
"""cmux socket client helper.

Updated 2026-06-11:
- The default socket at /tmp/cmux.sock is a legacy assumption. Real cmux builds
  create debug sockets with build-date suffixes (e.g. /tmp/cmux-debug-may-18.sock).
- If CMUX_SOCKET_PATH is unset, run `cmux identify` to discover the real path.
- If `cmux` isn't on PATH either, fall back to globbing /tmp/cmux-*.sock.
"""
import glob
import json
import os
import shutil
import socket
import subprocess
import sys

DEFAULT_SOCKETS = ("/tmp/cmux.sock", "/tmp/cmux-debug-*.sock")


def discover_socket_path():
    """Find the actual cmux Unix socket.

    Priority:
    1. $CMUX_SOCKET_PATH if set and the file exists.
    2. Output of `cmux identify` (the `socket_path` field) — most reliable.
    3. Glob /tmp/cmux-*.sock.
    4. Fall back to /tmp/cmux.sock (will likely fail, but raises clearly).
    """
    env = os.environ.get("CMUX_SOCKET_PATH")
    if env and os.path.exists(env):
        return env
    if shutil.which("cmux"):
        try:
            out = subprocess.run(
                ["cmux", "identify"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                data = json.loads(out.stdout)
                sock = data.get("socket_path")
                if sock and os.path.exists(sock):
                    return sock
        except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError):
            pass
    matches = sorted(glob.glob("/tmp/cmux-*.sock") + glob.glob("/tmp/cmux.sock"))
    for m in matches:
        if os.path.exists(m):
            return m
    return "/tmp/cmux.sock"


def rpc(method, params=None, req_id=1, socket_path=None):
    """Send a JSON-RPC request to the cmux socket."""
    if socket_path is None:
        socket_path = discover_socket_path()
    payload = {"id": req_id, "method": method, "params": params or {}}
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(10)
            sock.connect(socket_path)
            sock.sendall(json.dumps(payload).encode("utf-8") + b"\n")
            chunks = []
            while True:
                buf = sock.recv(65536)
                if not buf:
                    break
                chunks.append(buf)
            return json.loads(b"".join(chunks).decode("utf-8"))
    except (FileNotFoundError, ConnectionRefusedError) as e:
        return {"error": f"Socket not available: {socket_path}", "details": str(e)}
    except socket.timeout:
        return {"error": f"Timeout talking to {socket_path}"}


def main():
    if len(sys.argv) < 2:
        print("Usage: cmux_client.py <method> [params_json]")
        print("Example: cmux_client.py workspace.list")
        print("         cmux_client.py surface.send_text '{\"text\": \"ls\\n\"}'")
        sys.exit(1)

    method = sys.argv[1]
    params = {}
    if len(sys.argv) > 2:
        params = json.loads(sys.argv[2])

    result = rpc(method, params)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
