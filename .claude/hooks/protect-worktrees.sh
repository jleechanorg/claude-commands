#!/bin/bash
# protect-worktrees.sh — PreToolUse hook
# Blocks `git worktree remove` on human-created worktrees.
# Allows removal of AO-managed worktrees (basename matching ao-NNN pattern).
# Always blocks `git worktree prune` (indiscriminate).

INPUT=$(cat)
TOOL=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null)

if [ "$TOOL" != "Bash" ]; then
  exit 0
fi

CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

BLOCKED=$(python3 - "$CMD" <<'PYEOF'
import sys, re

cmd = sys.argv[1]

# Remove heredoc bodies
cmd = re.sub(r"<<'?\w+'?.*?^\w+$", '', cmd, flags=re.DOTALL|re.MULTILINE)
# Remove double-quoted strings (simple heuristic)
cmd = re.sub(r'"[^"]*"', '""', cmd)
# Remove single-quoted strings
cmd = re.sub(r"'[^']*'", "''", cmd)

# AO worktree name pattern
# Covers: ao-1350 (numeric), ao-pr263-fix (PR claim), ao-pr263 (PR claim), etc.
# AO spawn creates worktrees with ao-<descriptive> naming.
# Human worktrees typically use: worktree_*, bare names (pr263-fix), feature/...
AO_PATTERN = re.compile(r'^(ao|jc|wa|cc|ra|wc)-[a-z0-9-]+$')

# Split on common shell separators
parts = re.split(r'[;&|\n]+', cmd)
for part in parts:
    part = part.strip()
    if not part:
        continue
    tokens = part.split()
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if '=' in t or t == 'unset' or t == 'export':
            i += 1
            continue
        # Check for git worktree prune — always blocked
        if (t == 'git' and i+2 < len(tokens)
                and tokens[i+1] == 'worktree'
                and tokens[i+2] == 'prune'):
            print('BLOCKED')
            sys.exit(0)
        # Check for git worktree remove
        if (t == 'git' and i+2 < len(tokens)
                and tokens[i+1] == 'worktree'
                and tokens[i+2] == 'remove'):
            # Get the worktree path argument (after 'remove' and any flags)
            j = i + 3
            while j < len(tokens) and tokens[j].startswith('-'):
                j += 1
            if j < len(tokens):
                import os
                wt_name = os.path.basename(tokens[j].rstrip('/'))
                if AO_PATTERN.match(wt_name):
                    # AO worktree — allowed
                    break
                else:
                    # Human worktree — blocked
                    print('BLOCKED')
                    sys.exit(0)
            else:
                # No path argument — block to be safe
                print('BLOCKED')
                sys.exit(0)
        break
print('OK')
PYEOF
)

if [ "$BLOCKED" = "BLOCKED" ]; then
  echo "BLOCKED: This worktree is not an AO-managed session. Only AO worktrees (ao-*, jc-*, wc-*, etc.) can be removed by agents." >&2
  echo "Human-created worktrees require manual removal." >&2
  exit 2
fi

exit 0
