---
name: antigravity-computer-use
description: Use Claude Code to control Google Antigravity on macOS via Peekaboo. Extends the general claude-code-computer-use loop with Antigravity-specific workspace enumeration, element targeting, "Allow this conversation" dialog handling, and OAuth/API-key clarification. Trigger when the user asks to automate, click, send messages to, or interact with the Antigravity app.
---

# Antigravity Computer Use (macOS via Peekaboo)

This skill extends the general `claude-code-computer-use` loop. Follow all general loop rules (one action per step, screenshot-verify-repeat) and add the Antigravity-specific rules below.

For the core loop, safety policy, and invocation pattern, see the `claude-code-computer-use` skill.

**Tool selection for macOS native apps:**

| Option | Works for Antigravity? | Notes |
|--------|----------------------|-------|
| `mcp__claude-in-chrome__computer` | ❌ | Chrome browser tabs only (requires `tabId`) |
| Anthropic computer use API (`computer_20251124`) | ✅ | Requires separate agent loop with `anthropic-beta: computer-use-2025-11-24` header — not directly available in Claude Code sessions |
| **Peekaboo** (`peekaboo see/click/type/press`) | ✅ | Native macOS accessibility API — available now, implements the same screenshot→decide→act loop |

**Use Peekaboo** for this skill. It is the practical implementation of the computer use loop for macOS native apps in Claude Code sessions.

To use the true Anthropic computer use API instead, spawn a separate agent:
```bash
claude --print --permission-mode bypassPermissions \
  "Use computer use tools to [task]. App: Antigravity."
```
(This only works if the spawned Claude Code session has computer use tools provisioned.)

---

## Step 0 — Always use the Manager window

All interactions go through the **Agent Manager** window — the central Antigravity sidebar. Do not interact with individual workspace windows directly.

Note: the internal `window_title` for Agent Manager is `'Manager'` (as reported by `peekaboo window list`). Always target it by window ID or by title `"Manager"`.

Get the Manager window ID:

```bash
peekaboo window list --app Antigravity --json 2>/dev/null \
  | python3 -c "import json,sys; [print(w['window_id'], w['window_title']) for w in json.load(sys.stdin)['data']['windows']]"
# Find the line with title "Manager" and note its window_id
```

Then snapshot the Manager to enumerate workspaces and their active conversations:

```bash
peekaboo see --app Antigravity --window-id <MANAGER_ID> --annotate
```

From the output, extract:
- All workspace section headers (button labels like "worktree_agentog3")
- Their associated conversations (listed under each section)
- Active conversations (those with a progress indicator or "now")

**If the target workspace is not clear from context, STOP and ask the user:**

> "I can see these Antigravity workspaces in the Manager:
> 1. [workspace_1] — [active conversation or idle]
> 2. [workspace_2] — [active conversation or idle]
>
> Which one would you like me to work in?"

Do not proceed until the user selects a workspace. Then confirm you are operating in the Manager window before acting.

---

## "Allow this conversation" dialog — always click Allow

Antigravity shows an "Allow this conversation" (or similar permissions/consent) dialog when starting or resuming a session. **Always click Allow without asking the user** — this is pre-authorized.

Detection: after any navigation or workspace switch, re-snapshot and check for an "Allow" button or dialog element. If present, click it immediately before proceeding.

```bash
# After workspace switch — check for allow dialog
peekaboo see --app Antigravity --annotate
# If allow button found (e.g. elem_7: "Allow this conversation"):
peekaboo click --app Antigravity --on elem_7
# Re-snapshot to confirm dialog is gone before continuing
peekaboo see --app Antigravity --annotate
```

---

## Starting a new conversation in a specific workspace

Use the workspace `add` button — it reliably scopes the conversation to the correct workspace.

### How to find the add button for a workspace

The Manager sidebar lists workspaces as `other` elements (non-interactable) in `--json` output, with a corresponding `add` button (interactable) appearing in the same positional order. Map them using `--json`:

```bash
peekaboo see --app Antigravity --window-id <MANAGER_ID> --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
elems = data['data']['ui_elements']

# Workspace names appear as 'other' role elements under the Workspaces section
workspaces = [e for e in elems if e.get('role') == 'other'
              and e.get('label','').startswith('worktree_') or
              e.get('role') == 'other' and e.get('label','').startswith('project_')]

# add buttons are interactable buttons with label 'add' (not 'add Start new conversation')
add_buttons = [e for e in elems
               if e.get('role') == 'button' and e.get('label','').strip() == 'add']

# They appear in the same order — zip to map
for ws, btn in zip(workspaces, add_buttons):
    print(btn['id'], '->', ws.get('label',''))
"
# Output example:
# elem_48 -> worktree_jlcclawg
# elem_53 -> project_worldaiclaw
```

Note: `add` buttons have negative Y coordinates (e.g., `-870`) — this is normal; clicks succeed.

### Full flow

```bash
# 1. Get snapshot and click the workspace's add button
SNAP=$(peekaboo see --app Antigravity --window-id <MANAGER_ID> --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
peekaboo click --app Antigravity --window-id <MANAGER_ID> --on <ADD_ELEM_ID> --snapshot "$SNAP"

# 2. Re-snapshot and find the text entry area
SNAP2=$(peekaboo see --app Antigravity --window-id <MANAGER_ID> --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
# Find textField with label 'text entry area'
peekaboo see --app Antigravity --window-id <MANAGER_ID> --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if e.get('role','') == 'textField' and 'text entry' in (e.get('label','') or '').lower():
        print(e['id'], e.get('label',''))"
# → e.g. elem_107 "text entry area"

# 3. Click to focus, paste prompt, send
peekaboo click --app Antigravity --window-id <MANAGER_ID> --on <TEXT_FIELD_ID> --snapshot "$SNAP2"
peekaboo paste --app Antigravity --text "your prompt here"
peekaboo press return --app Antigravity

# 4. Verify — re-snapshot and confirm conversation appears with progress_activity indicator
sleep 2
peekaboo see --app Antigravity --window-id <MANAGER_ID> --annotate
```

**Use `peekaboo paste` not `peekaboo type`** — paste avoids character drift in Antigravity's input field.

## Element targeting rules

1. Always confirm `[win] Window: Manager` in `see` output before acting.
2. Use `--on elem_N` with `--snapshot <ID>` for reliability.
3. After clicking the workspace add button, verify a `textField 'text entry area'` appears before pasting.
4. After send, re-snapshot and confirm the prompt appears as a new conversation item with `progress_activity` or `now`.

---

## Listing all workspaces and conversations

Use this when the user asks "what's happening in Antigravity", "list all conversations", "what are the agents doing", or similar.

### How to enumerate and summarize

```bash
# 1. Get Manager window ID
MANAGER_ID=$(peekaboo window list --app Antigravity --json 2>/dev/null \
  | python3 -c "import json,sys; ws=[w for w in json.load(sys.stdin)['data']['windows'] if w['window_title']=='Manager']; print(ws[0]['window_id'])")

# 2. Snapshot Manager
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
elems = data['data']['ui_elements']

current_ws = None
for e in elems:
    label = e.get('label', '') or ''
    role = e.get('role', '')

    # Workspace header
    if role == 'other' and (label.startswith('worktree_') or label.startswith('project_')):
        # strip arrow prefix if collapsed/expanded
        ws_name = label.replace('keyboard_arrow_down ', '').replace('keyboard_arrow_right ', '')
        current_ws = ws_name
        print(f'\n### {ws_name}')

    # Conversations (buttons that are not control buttons)
    elif role == 'button' and current_ws and label not in ('add Start new conversation', 'history Chat History', 'Open Workspace', 'See less', 'See all (7)', 'Use Playground'):
        active = 'now' in label or 'progress_activity' in label
        marker = ' [ACTIVE]' if active else ''
        clean = label.replace('progress_activity ', '').replace(' now', '')
        print(f'  - {clean}{marker}')
"
```

### Output format to present to the user

For each workspace, report:
- Workspace name
- Each conversation title (strip `progress_activity` and timestamps like `5m`, `12h`)
- Mark `[ACTIVE]` on any currently running conversation
- After listing, add a **Summary** section inferring what each workspace appears to be focused on and a **Next Steps** suggestion based on active conversations

Example output:

```
### worktree_jlcclawg
  - Reviewing Open Pull Requests [ACTIVE]
  - Testing System Functionality
  - Reviewing Merged PRs

### worktree_agentog3
  - Auditing Orchestration Component Wiring [ACTIVE]
  - Reviewing PRs and Fixing Bugs

---
**Summary:**
- jlcclawg: PR review cycle in progress; one agent actively reviewing open PRs
- agentog3: Orchestration audit running; PR fix work queued

**Next steps:**
- jlcclawg: Check PR review results once the active conversation completes
- agentog3: Review audit findings; address any wiring issues found
```

---

## OAuth vs API key clarification

- OpenClaw agent auth inside Antigravity uses OAuth. Do not replace or reconfigure it.
- If `peekaboo see --analyze` fails with `OPENAI_API_KEY not found`, that is from Peekaboo's optional image-analysis backend — **not** an Antigravity auth failure. Skip `--analyze` or set `OPENAI_API_KEY` if visual analysis is needed.

---

## Completion criteria

Declare completion only when:

- Goal state is visible in screenshot evidence (e.g., message appears in the correct Antigravity workspace), or
- You are blocked and provide the exact blocker + required human input.

Always return:

- Final status
- Last 3 step logs
- Screenshot/file references (if available)
