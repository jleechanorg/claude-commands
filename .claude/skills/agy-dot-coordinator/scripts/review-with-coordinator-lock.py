#!/usr/bin/env python3
"""Candidate: run one bounded review command under the existing global flock.
Does not create, inspect, release, or reinterpret STOP or delivery markers.
"""
import fcntl, os, sys
from pathlib import Path

def main(argv):
    if not argv or argv[0] != '--' or len(argv) < 2:
        print('usage: review-with-coordinator-lock.py -- command [args...]', file=sys.stderr)
        return 2
    path = Path(os.environ.get('COORDINATOR_LOCK_FILE', '/tmp/ai.gemini.agy-dot-coordinator.lock'))
    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(path, os.O_CREAT | os.O_WRONLY | os.O_APPEND, 0o600)
    except OSError as error:
        print(f"Cannot open coordinator lock: {error}", file=sys.stderr)
        return 2
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print('Coordinator or review owns the global lock', file=sys.stderr)
            return 2
        os.set_inheritable(fd, True)
        try:
            os.execvp(argv[1], argv[1:])
        except OSError as error:
            print(f"Cannot exec {argv[1]}: {error}", file=sys.stderr)
            return 127
    finally:
        os.close(fd)
if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
