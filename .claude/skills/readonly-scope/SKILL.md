---
name: readonly-scope
description: Interpret user-requested read-only work as protecting Git-tracked files while allowing commands and writes outside the Git index.
---

# Read-only scope

When Jeffrey says `read-only` or `readonly`, do not modify files currently
tracked by Git in the repository or worktree. Do not stage or add new files to
the Git index. Determine the boundary from live Git state (`git ls-files` and
`git status`), not from file type or location.

Running commands, tests, servers, and read-only external queries is allowed.
Writing untracked, ignored, temporary, evidence, memory, bead, state, cache, or
other non-Git-tracked files is also allowed. Read-only does not cancel other
actions explicitly requested in the same live message, such as setting a goal,
updating beads, or running `/learn` or `/up`.

Do not alter pre-existing tracked-file changes, the index, commits, branches,
or remote Git state under read-only. Read-only by itself does not authorize
unrelated PR comments, PR state changes, merges, deployments, or external
messages. A more specific live instruction or a broader prohibition such as
`no changes` or `no mutations` wins.
