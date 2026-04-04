#!/usr/bin/env python3
"""Extract PR title from gh pr create command for enforce-agento-prefix.sh hook."""
import re
import sys

cmd = sys.stdin.read()
# Match --title or -t followed by quoted or unquoted value
m = re.search(r'(?:--title|-t)\s+(?:"([^"]*)"|\'([^\']*)\'|(\S+))', cmd)
if m:
    print(m.group(1) or m.group(2) or m.group(3))
