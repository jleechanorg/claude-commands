---
name: cmux-find-workspace-by-topic
description: "Find the cmux workspace hosting a given topic (e.g. \"agy\", \"bq\", \"lvl\"), AND any meta-question about cmux workspace finding/steering confusion. Trigger phrases: \"find the cmux workspace for X\", \"which cmux tab is doing X\", \"find the [topic] workspace\", \"locate the X cmux workspace\", \"what cmux surface is on X\", \"w:misc - X\", \"improve hermes confusion with cmux workspace finding\", \"skillify cmux workspace routing\", \"audit cmux workflow\", \"review cmux skills\", \"hermes doesn't find the right workspace\". Solves the recurring confusion where the cmux shim points at a stale dev CLI / wrong socket and Hermes doesn't find the workspace that's actually in a different live session. Always start with the multi-socket probe + keyword grep — do NOT trust `cmux list-workspaces` from the default shim. Load this skill BEFORE any 'find a workspace by topic' task AND before any meta audit of cmux workflows (load cmux parent + cmux-mcp-server-options in the same chain)."
---

# Find the cmux Workspace for a Topic

The single most common cmux task from the gateway: user names a topic (`agy`, `bq logging`, `cost`, `mobile load`, etc.) and you need to find the cmux workspace hosting it. This is harder than it looks because **multiple live cmux sessions can coexist** (prod + dev), the `~/.local/bin/cmux` shim points at **one** of them, and the workspace you want is often in the other one.

**Verified pattern, 2026-06-25 (agy workspace search):** the shim's hardcoded default was `/tmp/cmux-debug-fix-agy-hook-deny.sock` (a dead dev CLI). The actual `agy` workspace lived in `/private/tmp/cmux-debug-may-18.sock` (a different live dev session). Without the multi-socket probe, the workspace was invisible.

## The 3-step recipe (always run, always in this order)

### Step 1 — Probe all candidate cmux sockets

The shim (`~/.local/bin/cmux`) may be pointed at a dead build or the wrong session. **Enumerate ALL live sockets** before trusting any single `cmux <verb>` call:

```bash
for s in /tmp/cmux*.sock /private/tmp/cmux*.sock \
         ~/.local/state/cmux/cmux.sock; do
  if [ -S "$s" ]; then
    r=$(printf '{"id":"q","method":"ping","params":{}}\n' | nc -U -w 2 "$s" 2>&1)
    [ -n "$r" ] && echo "LIVE: $s → $r" | head -c 200
  fi
done
# Also check pointer files — cmux writes its preferred socket path here
cat /tmp/cmux-last-socket-path 2>/dev/null
ls /Users/$USER/.local/state/cmux/*-last-socket-path 2>/dev/null
# Each pointer references a build-date-suffixed socket like cmux-debug-may-18.sock
```

Output: usually 1-2 LIVE entries (prod `cmux.sock` + one debug `cmux-debug-*.sock`). If the shim's default socket isn't in the LIVE list, the shim is pointing at a dead build.

**Full diagnostic + the multi-app probe recipe (unattended-safe):** `cmux/SKILL.md` § "Two cmux sessions can be live at the same time" and `references/multi-app-socket-probe-recipe-2026-06-24.md`.

### Step 2 — Grep the workspace list of EVERY live session for the topic keyword

```bash
for s in /tmp/cmux-debug-*.sock /private/tmp/cmux-debug-*.sock \
         ~/.local/state/cmux/cmux.sock; do
  if [ -S "$s" ]; then
    echo "=== $s ==="
    # `workspace list` is the canonical alias; `list-workspaces` works too
    cmux --socket "$s" workspace list 2>/dev/null \
      | grep -iE "<keyword>" \
      || echo "  (no match)"
  fi
done
# Topic keyword → match against the TITLE column (after the workspace ref), not the ref itself.
# E.g. for "agy", expect a match like:
#   workspace:72  w: misc - agy
```

Output: a `workspace:N` + human title for each live session that has the topic. If exactly one match: that's the workspace. If multiple matches across sessions: the user has two live cmux apps hosting the same topic — pick the one with the active surface (`[selected]` in `cmux tree --all`).

### Step 3 — Discover the focused surface and read its screen

Once you have `workspace:N`:

```bash
SOCK=<the socket that returned the match>
cmux --socket "$SOCK" list-pane-surfaces --workspace=workspace:N
# Look for the leading `*` → that's the focused surface (the one to steer/read).
# Then:
cmux --socket "$SOCK" read-screen --workspace=workspace:N \
  --surface=surface:M --lines 40
# Or for a surface that's NOT the focused one, use the focus-then-read recipe
# in cmux/SKILL.md § "Reading a Non-Focused Surface" — `read-screen` ignores
# non-focused refs.
```

## What to do when no workspace matches

If step 2 returns "no match" in every live session:

1. **The work may exist in a worktree with no cmux surface driving it.** Check:
   ```bash
   git -C /Users/$USER/projects/<repo> worktree list
   for wt in $(git -C /Users/$USER/projects/<repo> worktree list --porcelain \
               | awk '/^worktree/ {print $2}'); do
     branch=$(git -C "$wt" branch --show-current 2>/dev/null)
     echo "$wt → $branch"
   done | grep -iE "<topic-keywords>"
   ```
2. **Search the user's recent PRs and Slack history** for the topic — the workspace may have been closed since the work landed.
3. **Report the gap explicitly:** "No live cmux workspace matches `<keyword>`. The work is in `<wt>` on branch `<branch>` with no cmux surface, OR the workspace was closed."

Don't fabricate a workspace. Don't grep harder hoping to find one. Report the gap.

## Common trap — the user's name doesn't match the workspace title

The user says "find the **agy** workspace." The actual cmux title is "**w: misc - agy**" (with the `misc` prefix). Hermes earlier burned 4 turns looking for "agy" as a substring of "workspace:..." titles before realizing the keyword has to match the column AFTER the ref.

**Rule:** when the user names a topic, **match against the title column only** (after stripping the `workspace:N` prefix and any status markers like `[selected]`). Don't expect titles to contain all the topic words — they often have prefixes (`w:`, `g -`, `lvl:`, etc.).

If you can't find the topic in any title, **ask the user for the workspace name verbatim** (e.g. "is it `misc - agy` or `w: agy`?"). Don't burn more than 2 grep iterations.

## Topic vs. label drift — verify the surface matches the topic

Workspace titles are **labels set at creation time**, not guarantees of current work. A workspace named "lvl: clean flags" might be driving `mobile load` PRs. After finding the candidate workspace:

1. `cmux identify --workspace=workspace:N` → get the focused `surface_ref` + `tty`.
2. `ps -ef | grep ttysNNN` → identify the agent + launch cwd.
3. Confirm the cwd's branch / `gh pr list --head <branch>` matches the topic.

If the label/content doesn't match: the topic might be in **another workspace whose title doesn't contain the keyword** — fall back to `git worktree list` + branch-name grep (same as "no match" path above).

## Don't

- **Don't trust `cmux list-workspaces` from the shim alone.** The shim may point at a dead dev CLI or the wrong live session. Always enumerate ALL live sockets first.
- **Don't grep the socket filename for the topic.** Sockets are named `cmux-debug-<build-date>.sock`, not after the topic.
- **Don't `cmux read-screen --workspace=workspace:N --surface=surface:M` without re-discovering the surface ID first.** Surface IDs rotate when panes are recreated. Always re-run `list-pane-surfaces --workspace=workspace:N` before reading.
- **Don't grep `~/.local/state/cmux/` for the topic.** That dir holds socket-pointer files, not workspace names.
- **Don't tell the user "no such workspace" without enumerating worktrees + recent PRs first.** The work may live on disk with no cmux surface — that's a real finding, not a "not found."

## Companion skills

- `cmux` (parent) — Unix socket / CLI reference, including the "Two cmux sessions" multi-session pattern and "Reading a Non-Focused Surface" focus-then-read recipe.
- `cmux-terminal-review` — bulk terminal inventory (Healthy/Risky/Blocked digest). Use that for "what are all the terminals doing," not this skill.
- `find-slack-thread-pr-for-request` — when the user references a topic in Slack history ("remember that agy work we did last week"), cross-reference Slack before concluding the work is gone.