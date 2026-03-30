---
name: antigravity-computer-use
description: Use Claude Code to control Google Antigravity IDE on macOS via Peekaboo. Covers Agent Manager, Editor, workspaces, conversations, Knowledge/Browser/Settings panels, keyboard shortcuts, model selection, planning modes, artifacts, and menu bar. Trigger when the user asks to automate, click, send messages to, or interact with the Antigravity app.
---

# Antigravity Computer Use (macOS via Peekaboo)

Google Antigravity is an AI-powered, agent-first IDE (a modified VS Code fork) by Google. It has two primary views: **Agent Manager** ("Mission Control") and **Editor** (VS Code-like). This skill controls it via Peekaboo's native macOS accessibility API.

For the core screenshot-decide-act loop, see the `claude-code-computer-use` skill.

**Official docs:** https://antigravity.google/docs
**CLI tool:** `agy`

---

## Architecture overview

| View | Purpose | Window title |
|------|---------|-------------|
| **Agent Manager** | Orchestrate AI agents, manage workspaces, monitor conversations | `Manager` |
| **Editor** | VS Code-like coding with AI side panel | `Antigravity` or `worktree_*` |
| **Launchpad** | Background/launcher window | `Launchpad` |
| **hidden-nova** | Internal background window | `hidden-nova` |

Toggle between views: **Cmd+E** or **Cmd+Shift+M**

---

## Step 0 — Always use the Manager window

All orchestration interactions go through the **Agent Manager** window. Do not interact with individual workspace editor windows unless explicitly doing editor tasks.

```bash
# Get Manager window ID
MANAGER_ID=$(peekaboo window list --app Antigravity --json 2>/dev/null \
  | python3 -c "import json,sys; ws=[w for w in json.load(sys.stdin)['data']['windows'] if w['window_title']=='Manager']; print(ws[0]['window_id'])")
```

---

## Manager window — complete UI element map

### Top bar

| Element label | Role | Description |
|---------------|------|-------------|
| `dock_to_right` / `dock_to_left` | text | Dock position toggle |
| `Agent Manager` | text | Title |
| `Open Editor` | text | Switch to Editor view |
| `settings` | text | Settings icon (top bar) |

### Sidebar navigation buttons

| Element label | Role | Description |
|---------------|------|-------------|
| `add Start new conversation` | button | Creates new conversation (global) |
| `history Chat History` | button | Opens chat history panel |
| `Open Workspace` | button | Opens workspace picker/folder browser |
| `import_contacts Knowledge` | button | Opens Knowledge panel |
| `chrome_product Browser` | button | Opens Browser integration panel |
| `settings Settings` | button | Opens Settings panel |
| `lightbulb Provide Feedback` | button | Opens Feedback panel |

### Conversation list (dynamic)

| Pattern | Meaning |
|---------|---------|
| `progress_activity <Title> now` | Active/running conversation (status: **Running**) |
| `<Title> <N>m` / `<N>h` / `<N>d` | Completed/idle conversation with time-ago (status: **Idle**) |
| `See all (N)` | Expand to show all conversations |
| `See less` | Collapse conversation list |

### Conversation status indicators

Conversations have three states visible in the Manager:

| Status | Visual indicator | Meaning |
|--------|-----------------|---------|
| **Running** | `progress_activity` spinner prefix + `now` | Agent is actively working |
| **Idle** | Time-ago suffix (`5m`, `1h`, `12h`) | Agent finished or waiting |
| **Blocked** | May show warning icon or stalled state | Agent needs human input |

### Sidebar icon prefixes (Material Icons as text)

| Prefix | Icon |
|--------|------|
| `add` | Plus (new conversation) |
| `history` | Clock (chat history) |
| `import_contacts` | Contacts (knowledge) |
| `chrome_product` | Browser |
| `settings` | Gear |
| `lightbulb` | Bulb (feedback) |
| `progress_activity` | Spinner (active task) |
| `more_horiz` | Three dots (context menu) |
| `keyboard_arrow_down` / `keyboard_arrow_right` | Expand/collapse workspace |

### Workspace section elements

| Element label | Role | Description |
|---------------|------|-------------|
| `worktree_<name>` | other/text | Workspace header label |
| `project_<name>` | other/text | Project workspace header |
| `Playground` | other/text | Playground section header (scratch/test conversations) |
| `more_horiz` | text | Workspace options menu |
| `add` | button | Workspace-specific "+" button for new conversations (only for Playground section — workspace `+` icons are web-rendered) |
| `info` | other | Info icon (appears in Playground section) |

### Conversation view controls (appear when conversation is open)

| Element label | Role | Description |
|---------------|------|-------------|
| text entry area (textField) | textField | Message input area |
| `Planning` / `Fast` | button/text | Planning mode toggle |
| `Claude Opus 4.6 (Thinking)` etc. | button/text | Model selector |
| `Record voice memo` | button | Voice input |
| `Send` | button | Send message |
| `code Open editor` | button | Open in editor |
| `Use Playground` | button | Switch to playground mode |
| `Review` | button | Review mode toggle (top-right of conversation) |
| `Walkthrough` | tab | Walkthrough artifact view |

---

## Editor window — complete UI element map

All editor windows (`Antigravity`, `worktree_*`) share the same VS Code structure.

### Sidebar tabs

| Tab label | Keyboard shortcut |
|-----------|------------------|
| Explorer | Shift+Cmd+E |
| Code Search | Shift+Cmd+F |
| Source Control | Ctrl+Shift+G |
| Run and Debug | Shift+Cmd+D |
| Remote Explorer | — |
| Extensions | Shift+Cmd+X |
| Containers | — |
| GitHub Actions | — |

### AI-specific controls

| Control | How to access |
|---------|--------------|
| Agent side panel | Cmd+L (toggle/focus) |
| Inline AI command | Cmd+I (in editor and terminal) |
| `@` context inclusion | Type `@` in agent panel → files, dirs, MCP servers |
| `/` workflow invocation | Type `/` in agent panel → saved workflows |
| Artifacts button | Bottom-right of editor |
| "Explain and Fix" | Hover over problems |
| "Send all to Agent" | Problems panel → batch error resolution |
| Terminal output → agent | Select terminal output, press Cmd+L to send to agent |
| Tab-to-import | Auto-suggests missing dependency imports |
| Tab-to-jump | Navigates cursor to next logical code location |

---

## Menu bar items (Antigravity focused)

### Antigravity menu
- About Antigravity
- Quit Antigravity

### File menu
- **Start Conversation** — new conversation (Cmd+N equivalent)
- **New Editor** — new editor window
- **Open Folder** — open a workspace folder

### Edit menu
- Standard: Undo, Redo, Cut, Copy, Paste, Select All
- Writing Tools submenu (macOS): Proofread, Rewrite, Make Friendly/Professional/Concise, Summarize, Create Key Points, Make List/Table, Compose
- AutoFill submenu: Contact, Passwords

### View menu
- Toggle Fullscreen

---

## Keyboard shortcuts

### Antigravity-specific

| Shortcut | Action |
|----------|--------|
| **Cmd+E** | Toggle Agent Manager ↔ Editor |
| **Cmd+Shift+M** | Toggle Agent Manager ↔ Editor (alt) |
| **Cmd+L** | Toggle/focus agent side panel |
| **Cmd+I** | Inline AI command (editor + terminal) |
| **Cmd+B** | Toggle sidebar |
| **Tab** | Accept AI code completion |
| **Esc** | Dismiss AI suggestion |

### VS Code inherited (selection)

| Shortcut | Action |
|----------|--------|
| Cmd+P | Quick Open (file search) |
| Cmd+Shift+P | Command Palette |
| Cmd+Shift+F | Search across project |
| Ctrl+` | Toggle integrated terminal |
| Cmd+D | Select next occurrence |
| Cmd+Shift+L | Select all occurrences |
| Opt+Up/Down | Move current line |
| Cmd+Shift+K | Delete current line |
| Cmd+/ | Toggle line comment |
| Cmd+\ | Split editor vertically |
| Cmd+1/2/3 | Focus split editor groups |
| Ctrl+G | Go to line number |
| Cmd+Click | Go to definition |
| Ctrl+- | Navigate back |

---

## Development modes

Antigravity supports these execution modes (configured during onboarding or in Settings):

| Mode | Description |
|------|-------------|
| **Agent-driven (Autopilot)** | AI writes code, creates files, runs commands automatically |
| **Review-driven** (Recommended) | AI asks permission before actions |
| **Agent-assisted** | User stays in control; AI helps with safe automations |
| **Secure Mode** | Enhanced security restrictions |
| **Custom Configuration** | User-defined policy per action type |

### Execution policies

| Policy | Options |
|--------|---------|
| Terminal execution | Always Proceed (with deny list) / Request Review (with allowlist) |
| Review policy (artifacts) | Always Proceed / Agent Decides (default) / Request Review |
| JavaScript execution (browser) | Always Proceed / Request Review / Disabled |

---

## Planning modes

| Mode | Description |
|------|-------------|
| **Planning** | Agent builds task lists and implementation plans before executing. Use for complex tasks. |
| **Fast** | Agent executes directly without planning. Use for simple tasks. |

Toggle via the dropdown in the conversation input area (shows as `Planning` or `Fast` button).

**A11y access**: In the **new conversation creation** view, Planning/Fast buttons appear as A11y `button` elements. In active conversations, they are web-rendered. When clicking "Start new conversation", a conversation mode picker popover appears with Planning/Fast options — this popover is entirely web-rendered (NOT in A11y tree).

---

## Model selection

Available in per-conversation dropdown:

| Model | Notes |
|-------|-------|
| Gemini 3 Pro (High/Low) | Default |
| Gemini 3 Flash | Lighter/faster |
| Gemini 3 Deep Think | Reasoning-heavy |
| Claude Sonnet 4.5/4.6 (Thinking/Standard) | Anthropic models |
| Claude Opus 4.6 (Thinking) | Anthropic flagship |
| GPT-OSS-120B | OpenAI model |

**A11y access**: In the **new conversation creation** view, the model selector appears as an A11y `button` (e.g., `Claude Opus 4.6 (Thinking)`). In active/idle conversations, the model selector is web-rendered.

---

## Artifacts system

Types: Task Lists, Implementation Plans, Code Diffs, Walkthroughs, Screenshots, Browser Recordings.

- **Agent Manager:** toggle artifacts button (top-right)
- **Editor:** click "Artifacts" button (bottom-right)
- Supports Google Docs-style comments — agents ingest feedback and iterate

### Walkthrough mode

Post-completion artifact with: summary, task list, file changes, screenshots, testing instructions. Appears as a tab in conversation view.

---

## Configuration and customization

### Rules (agent guidelines)

| Scope | Path |
|-------|------|
| Global | `~/.gemini/GEMINI.md` |
| Workspace | `<workspace>/.agents/rules/` |

### Workflows (saved prompts, invoked with `/`)

| Scope | Path |
|-------|------|
| Global | `~/.gemini/antigravity/global_workflows/<NAME>.md` |
| Workspace | `<workspace>/.agents/workflows/` |

### Skills

| Scope | Path |
|-------|------|
| Global | `~/.gemini/antigravity/skills/` |
| Workspace | `<workspace>/.agents/skills/` |

Skill structure: `SKILL.md` (required, YAML frontmatter), optional `scripts/`, `references/`, `assets/`.

### Customization access

Editor mode: `(...) > Customizations`

---

## "Allow this conversation" dialog — always click Allow

Antigravity shows "Allow directory access to /path?" prompts with **Deny / Allow Once / Allow This Conversation** buttons when agents try to access workspace files. **Always click "Allow This Conversation" without asking the user** — pre-authorized.

### CRITICAL: These buttons are web-rendered

The Allow/Deny buttons are **web-rendered inside the conversation panel** and do NOT appear in the Peekaboo accessibility tree. `peekaboo see` only returns native macOS accessibility elements. The Allow prompt appears **every new conversation** for **every workspace** — not just the first time.

### Solution: Coordinate-based clicking via annotated screenshot

### Method 0: Simplified blue-button detection (FASTEST — proven 2026-03-27)

```bash
# One-liner: find and click "Allow This Conversation" (rightmost blue button)
WIN_X=832; WIN_Y=-1013; WIN_W=1025; WIN_H=904  # Manager window bounds
screencapture -R${WIN_X},${WIN_Y},${WIN_W},${WIN_H} /tmp/antig_allow.png
COORDS=$(python3 -c "
from PIL import Image; import numpy as np
img = np.array(Image.open('/tmp/antig_allow.png'))
blue_mask = (img[:,:,2] > 150) & (img[:,:,0] < 120) & (img[:,:,2] > img[:,:,1] + 30)
ys, xs = np.where(blue_mask)
if len(xs) > 0:
    right_mask = xs > (xs.max() - 250)
    cx, cy = int(np.mean(xs[right_mask])), int(np.mean(ys[right_mask]))
    print(f'${WIN_X}+{cx//2},${WIN_Y}+{cy//2}')
" 2>/dev/null | python3 -c "import sys; parts=sys.stdin.read().strip().split(','); print(f'{eval(parts[0])},{eval(parts[1])}')")
[ -n "$COORDS" ] && peekaboo click --app Antigravity --window-id MANAGER_ID --coords "$COORDS"
```

### Method 1: Programmatic blue-button detection (PROVEN — use this)

Uses `screencapture` + PIL pixel analysis to find blue button coordinates automatically:

```bash
MANAGER_ID=<MANAGER_ID>

# Step 1: Get window bounds
BOUNDS=$(peekaboo window list --app Antigravity --json 2>/dev/null | python3 -c "
import json, sys
for w in json.load(sys.stdin)['data']['windows']:
    if w['window_id'] == $MANAGER_ID:
        b = w['bounds']
        print(f\"{b['x']},{b['y']},{b['width']},{b['height']}\")
")
WIN_X=$(echo "$BOUNDS" | cut -d, -f1)
WIN_Y=$(echo "$BOUNDS" | cut -d, -f2)
WIN_W=$(echo "$BOUNDS" | cut -d, -f3)
WIN_H=$(echo "$BOUNDS" | cut -d, -f4)

# Step 2: Capture window region (retina = 2x pixels)
screencapture -R${WIN_X},${WIN_Y},${WIN_W},${WIN_H} /tmp/allow_check.png

# Step 3: Find blue button coordinates programmatically
python3 -c "
from PIL import Image
import numpy as np

img = Image.open('/tmp/allow_check.png')
arr = np.array(img)
h, w = arr.shape[:2]

# Find blue button pixels (bottom half of image)
for row_start in range(h//2, h, 30):
    region = arr[row_start:row_start+30, :]
    blue_mask = (region[:,:,2] > 150) & (region[:,:,0] < 150) & (region[:,:,2] > region[:,:,0] + 50)
    if np.sum(blue_mask) > 100:
        coords = np.where(blue_mask)
        xs = coords[1]
        xs_sorted = np.sort(np.unique(xs))
        # Find gap between buttons
        gaps = np.diff(xs_sorted)
        big_gaps = np.where(gaps > 15)[0]
        if len(big_gaps) > 0:
            # Rightmost button = 'Allow This Conversation'
            right_start = xs_sorted[big_gaps[-1] + 1]
            right_end = xs_sorted[-1]
        else:
            # Single button region — rightmost 40%
            right_start = xs_sorted[int(len(xs_sorted) * 0.6)]
            right_end = xs_sorted[-1]
        cx = int((right_start + right_end) / 2)
        cy = int(np.mean(coords[0][xs >= right_start])) + row_start
        # Convert 2x retina pixels to points
        print(f'{$WIN_X + cx//2},{$WIN_Y + cy//2}')
        break
"

# Step 4: Click at computed screen coordinates
CLICK_COORDS=$(python3 ...)  # capture output from step 3
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --coords "$CLICK_COORDS"

# Step 5: Verify — re-capture and check blue pixels are gone
sleep 1
screencapture -R${WIN_X},${WIN_Y},${WIN_W},${WIN_H} /tmp/allow_verify.png
```

### Method 2: Visual inspection (fallback)

```bash
# Take annotated screenshot, visually identify button position
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --annotate
# Read the annotated screenshot to identify coordinates
# Click by coordinates
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --coords <x>,<y>
```

### Key facts about coordinate clicking

- `peekaboo click --coords` uses **screen-absolute** coordinates (not window-relative)
- macOS Retina displays use **point coordinates** (not pixel coordinates) — divide retina pixels by 2
- `screencapture -R` uses point coordinates for the region but captures at 2x pixel resolution
- External displays may have negative y coordinates (e.g., y=-1013 for a monitor above the primary)
- Window bounds from `peekaboo window list` are in point coordinates

### Alternative: Antigravity Settings

Configure execution policy to avoid Allow prompts entirely:
1. Open Settings (sidebar gear icon)
2. Set terminal execution to "Always Proceed" for known workspaces
3. **IMPORTANT**: "Always Proceed" does NOT eliminate per-conversation Allow prompts — those are separate (workspace directory access vs terminal command approval)
4. "Always Proceed" only applies to **new messages**. In-progress conversations keep the policy that was active when they started. If an agent is stuck on "Waiting for command completion", start a NEW conversation rather than trying to approve the stuck one.

### Terminal approval stuck state — start new conversation

If you see "The commit command is waiting for user approval" or "Waiting for command completion (up to 300 seconds)", the conversation started under "Request Review" mode. The "Always run ^" dropdown buttons are web-rendered and coordinate clicks rarely work reliably on them. Recovery:
1. Do NOT try to click "Always run" — it's unreliable
2. Verify Settings > Terminal > "Always Proceed" is set
3. Start a **new conversation** — it will use the updated policy
4. Include results from the stuck conversation's work (skip completed items)

### Agent crash recovery — start fresh

When "Agent terminated due to error" appears with Dismiss/Copy debug info/Retry buttons:
1. These buttons are web-rendered — Dismiss clicks often land on wrong elements (Knowledge panel, etc.)
2. Do NOT try Retry — it may restart with stale context (e.g., trying to fix already-merged PRs)
3. Instead: start a **new conversation** with updated task description
4. Check what the crashed agent accomplished: `git log`, `git branch -r`, `gh pr list`
5. Skip completed work in the new task prompt
6. Two conversations CAN run simultaneously — the crashed one becomes IDLE and won't block

### Detection pattern

After starting any conversation, check for Allow prompts:
1. Capture the Manager window with `screencapture -R<bounds>`
2. Use PIL to search for blue button pixels in the bottom half
3. If blue buttons found → run the programmatic click flow above
4. Re-capture to confirm the prompt dismissed

### Web-rendered content interaction — general technique

Antigravity uses web-rendered UI elements that don't appear in the A11y tree. For ANY web-rendered button/control:

1. **Capture**: `screencapture -R<window_bounds> /tmp/element.png`
2. **Analyze**: Use PIL/numpy to find the element by color, shape, or position
3. **Convert**: Divide retina pixels by 2, add window origin for screen coordinates
4. **Click**: `peekaboo click --app Antigravity --window-id <ID> --coords <screen_x>,<screen_y>`
5. **Verify**: Re-capture and confirm the element is gone/changed

This technique works for: Allow prompts, Review buttons, walkthrough controls, artifact interactions, and any other web-rendered UI that peekaboo `see` cannot expose.

**Note**: `peekaboo screenshot` does NOT exist — use `screencapture` (macOS built-in) instead.

---

## Starting a new conversation in a workspace

### Method 0: `agy` CLI (FASTEST — use for new workspaces)

The `agy` CLI (`~/.antigravity/antigravity/bin/agy`) opens a workspace directly and registers it with the Manager. **This is the best method for workspaces not yet visible in the Manager sidebar.**

```bash
# Open workspace — creates editor window AND registers in Manager
agy /path/to/workspace

# Verify window appeared
peekaboo window list --app Antigravity --json 2>/dev/null | python3 -c "
import json, sys
for w in json.load(sys.stdin)['data']['windows']:
    print(f'{w[\"window_id\"]:6}  {w[\"window_title\"]}')"
```

After `agy`, the workspace appears in `peekaboo window list` but may require **scrolling down** in the Manager sidebar to become visible as an `other` element. The Manager sidebar only shows a viewport — new workspaces appear at the bottom.

### Method 1: "Start new conversation" button (RECOMMENDED — tested and proven)

The global "add Start new conversation" button in the sidebar opens a new conversation creation view with full A11y support. **This is the most reliable method.**

**How to find it**: Scroll to the top of the sidebar — the button may be hidden below the fold. Use `peekaboo scroll --direction up --amount 10` then check for `add Start new conversation` in the A11y tree.

```bash
MANAGER_ID=<MANAGER_ID>

# Step 1: Scroll sidebar to top to reveal the button
peekaboo scroll --direction up --amount 10 --app Antigravity --window-id "$MANAGER_ID"

# Step 2: Find the "add Start new conversation" button
SNAP=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data']['snapshot_id'])")
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if 'Start new conversation' in (e.get('label','') or ''):
        print(e['id'])"

# Step 3: Click it — opens new conversation creation view
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <ADD_BUTTON_ID> --snapshot "$SNAP"
```

**The new conversation view exposes these A11y elements:**

| Element label | Role | Description |
|---------------|------|-------------|
| `keyboard_arrow_down <workspace>` | button | Workspace selector dropdown |
| `text entry area` | textField | Message input |
| `Send` | button | Send button (visible here, unlike in active conversations) |
| `Planning` / `Fast` | button | Planning mode toggle |
| `Claude Opus 4.6 (Thinking)` etc. | button | Model selector |
| `Record voice memo` | button | Voice input |
| `code Open editor` | button | Switch to editor |
| `Use Playground` | button | Switch to playground mode |
| `New conversation in` | other | Label text |

**Important**: The workspace selector dropdown (`keyboard_arrow_down`) is accessible in A11y but **clicking it does NOT reliably open the web-rendered dropdown menu**. The dropdown is web-rendered. Workaround: include the explicit workspace path in your prompt.

```bash
# Step 4: Click text field, paste prompt (include workspace path!)
SNAP2=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")

# Find text field and Send button
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    label = e.get('label','') or ''
    role = e.get('role','')
    if label in ('text entry area','Send') or role == 'textField':
        print(e['id'], role, label)"

# Click text field, paste prompt with workspace context
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <TEXT_FIELD_ID> --snapshot "$SNAP2"
peekaboo paste --app Antigravity --text "You are working in /path/to/worktree on branch X. <your task>"

# Step 5: Send — BOTH Return and Send button work
peekaboo press "Return" --app Antigravity
# OR: peekaboo click --on <SEND_BUTTON_ID> --snapshot "$SNAP2"

# Step 6: Verify conversation started
sleep 3
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    label = e.get('label','') or ''
    if 'progress_activity' in label:
        print('ACTIVE:', label[:100])"
```

### Method 2: Click workspace label in Manager sidebar

Clicking a workspace `other` element or "No chats yet" text expands the workspace section. After expanding, a `+` icon appears next to the workspace name (web-rendered, requires coordinate clicking).

**Limitations**: Only the **currently focused workspace** label appears as an `other` element in the A11y tree. Other workspace labels are web-rendered and not directly clickable via A11y.

### Method 3: Click existing conversation to switch

Click any conversation button in the sidebar to switch to it. The conversation buttons ARE in the A11y tree (role=button, label includes title + time-ago).

### ⚠️ Known issues

- **"Open Workspace" dropdown scoping**: The `Open Workspace` sidebar button does NOT reliably scope to the selected workspace.
- **Workspace dropdown in new conversation view**: The `keyboard_arrow_down` button doesn't open its web-rendered dropdown via A11y click. Include workspace path in prompt as workaround.
- **Workspace-specific `+` icon**: Web-rendered, requires coordinate clicking which is unreliable due to dynamic sidebar layout.

### Full flow (Method 0 + Method 1 combined — most reliable)

```bash
MANAGER_ID=<MANAGER_ID>

# Step 1: If workspace not in Manager sidebar, open via CLI first
agy /path/to/workspace
sleep 2

# Step 2: Scroll sidebar to top and click "Start new conversation"
peekaboo scroll --direction up --amount 10 --app Antigravity --window-id "$MANAGER_ID"
SNAP=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
# Find and click the button
ADD_ID=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if 'Start new conversation' in (e.get('label','') or ''):
        print(e['id']); break")
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on "$ADD_ID" --snapshot "$SNAP"
sleep 1

# Step 3: Click text field, paste prompt with workspace path
SNAP2=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
TF_ID=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if e.get('role','') == 'textField' and 'text entry' in (e.get('label','') or ''):
        print(e['id']); break")
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on "$TF_ID" --snapshot "$SNAP2"
peekaboo paste --app Antigravity --text "You are working in /path/to/worktree on branch X. <task>"
peekaboo press "Return" --app Antigravity
```

### Important notes

- **Use `peekaboo paste` not `peekaboo type`** — paste avoids character drift in Antigravity's input field.
- **Both Return and Send button work** for sending messages. In active conversations, the Send button may NOT be in the A11y tree. In the new conversation view, it IS accessible.
- **Always include the explicit workspace path in your prompt** as a safety net for workspace scoping: "You are working in /path/to/worktree on branch X"
- **New workspaces need scrolling** — after `agy <path>`, the Manager sidebar may not show the workspace without scrolling down.
- **Conversations auto-rename** — after the first message, Antigravity renames the conversation based on content.

### Workspace scoping workaround — CRITICAL

The "New conversation in > [workspace]" dropdown is **web-rendered and cannot be switched via A11y or coordinate clicking reliably**. After 3 failed attempts to switch it, use this workaround:

**Don't fight the dropdown. Include the workspace path in your prompt text instead:**

```bash
# The dropdown says "agent-orchestrator" but you want worldai_claw? Don't try to switch it.
# Just include the workspace path explicitly in the prompt:
peekaboo paste --app Antigravity --text "You are working in $HOME/project_worldaiclaw/worldai_claw on branch main. <your task here>"
```

This works because Antigravity agents resolve the workspace from the path in the prompt, regardless of which workspace the dropdown shows. The dropdown only sets the default context — explicit paths override it.

### UI interaction retry cap

**After 3 failed attempts at the same UI interaction (coordinate clicks, element clicks, keyboard shortcuts), STOP.** Do not continue guessing. Instead:
1. Disclose to user: "I tried X 3 times and it's not working because Y"
2. Use a documented workaround (e.g., workspace path in prompt text)
3. If no workaround exists, ask user for help

This prevents the failure mode where the agent spends 15+ tool calls trying coordinate variations on web-rendered elements that are invisible to A11y.

### Manager window startup

The Manager window may not appear immediately after keyboard shortcuts. Reliable procedure:

1. `osascript -e 'tell application "Antigravity" to activate'` — ensure Antigravity is focused
2. `peekaboo press --app Antigravity --keys "cmd shift m"` — toggle Manager
3. `sleep 3` — Manager takes 2-3 seconds to initialize
4. Check `peekaboo window list` for a window titled "Manager"
5. If not found after ONE retry (total wait 6s), disclose to user: "Manager window isn't opening"

Do NOT loop Cmd+Shift+M or Cmd+E repeatedly — it toggles the window on/off.

---

## Sending messages to active conversations

To send a follow-up message to a conversation already open in the Manager:

```bash
MANAGER_ID=<MANAGER_ID>

# Step 1: Switch to the target conversation (click its sidebar button)
SNAP=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
# Find conversation by title substring
CONVO_ID=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if e.get('role','') == 'button' and 'your search term' in (e.get('label','') or '').lower():
        print(e['id']); break")
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on "$CONVO_ID" --snapshot "$SNAP"
sleep 1

# Step 2: Click text field to focus
SNAP2=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
TF_ID=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    if e.get('role','') == 'textField' and 'text entry' in (e.get('label','') or ''):
        print(e['id']); break")
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on "$TF_ID" --snapshot "$SNAP2"

# Step 3: Paste and send
peekaboo paste --app Antigravity --text "your follow-up message"
peekaboo press "Return" --app Antigravity
```

**Tested behavior**: Messages sent via paste+Return are received and processed immediately. The conversation auto-renames based on the first message content.

**Note**: In active/idle conversations, the Send button does NOT appear in A11y. Use `peekaboo press "Return"` instead — confirmed working.

**Important**: The textField may NOT appear in the A11y tree initially when switching to a conversation. It becomes accessible **after clicking the input area** (either via coordinates or by clicking the conversation content area first). If `textField` is not in the A11y tree:
1. Click the input area coordinates (bottom of content pane, roughly `y=-140` relative to Manager window)
2. Re-snapshot — `textField` with label "text entry area" should now appear
3. Then paste + Return as usual

---

## Chat History panel

The Chat History panel shows a **flat list of ALL conversations** across all workspaces, with search and timestamps.

```bash
# Open Chat History
SNAP=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <CHAT_HISTORY_BUTTON> --snapshot "$SNAP"
```

The Chat History button is labeled `history Chat History` in A11y. It shows:
- Conversation title and workspace name
- Time-ago timestamps
- Blue dot for active/recent conversations
- Spinner icon for running conversations
- Search bar for filtering

**Use case**: When you need to find a specific conversation across workspaces, Chat History is faster than scrolling through each workspace section in the sidebar.

---

## MANDATORY: Monitor, read, and assess active conversations

**This is the most important part of the skill.** Starting a conversation is useless if you don't read what Gemini is actually producing and respond to it. Every interaction with Antigravity MUST include a read-assess-respond cycle.

### After starting or checking a conversation, ALWAYS:

1. **Read the conversation content** — conversation text is web-rendered and NOT in the A11y tree. Use `screencapture` + vision to read what Gemini wrote:

```bash
# Get window bounds for the Manager
MANAGER_ID=<MANAGER_ID>
BOUNDS=$(peekaboo window list --app Antigravity --json 2>/dev/null | python3 -c "
import json, sys
for w in json.load(sys.stdin)['data']['windows']:
    if w['window_id'] == $MANAGER_ID:
        b = w['bounds']
        print(f\"{b['x']},{b['y']},{b['width']},{b['height']}\")")

# Capture the conversation view
screencapture -R${BOUNDS} /tmp/convo_read.png

# Read the screenshot with Claude vision to extract content
# The A11y tree only gives sidebar buttons and menu items — NOT chat messages

# To scroll through long conversations:
peekaboo scroll --app Antigravity --window-id "$MANAGER_ID" --direction down --amount 10
# Or use keyboard after clicking the conversation area:
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --coords <center_x>,<center_y>
peekaboo press "pagedown" --app Antigravity
```

**IMPORTANT**: `peekaboo see --json` on the Manager window returns sidebar elements (conversation titles, workspace labels, menu items) but NOT the web-rendered conversation content (chat messages, code blocks, progress updates). You MUST use screenshots to read what the agent is actually doing.

2. **Assess the agent's state** — determine what's happening:
   - Is it making progress on the task?
   - Is it stuck, asking a question, or hitting an error?
   - Has it drifted to side work (lint, formatting) while the primary task is undone?
   - Did it produce real output (commits, files) or just text?

3. **Check for real artifacts** — verify the agent actually did work:
```bash
# Check if agent pushed commits
cd /path/to/workspace && git log --oneline -5

# Check for new/modified files
git diff --stat HEAD~1
```

4. **Respond or redirect** — if the agent is stuck or drifting:
   - Paste a follow-up message with specific instructions
   - If idle, start a new message to continue the work
   - If erroring, paste the fix or adjust the prompt

### When monitoring for someone else (e.g., a subagent or /loop):

Report these fields:
- **Conversation title** (from Manager)
- **Status** (Running/Idle/Blocked — from Manager indicators)
- **Last visible output** (from conversation window `peekaboo see`)
- **Real artifacts** (commits, files, PRs — from git/gh)
- **Assessment** (on-track / drifting / stuck / done)
- **Recommended action** (continue / redirect / kill)

### Anti-pattern: "conversation started" without reading it

NEVER declare Exit Criterion B or similar "produces output" criteria PASS based solely on:
- Manager showing `progress_activity` (that just means Gemini is responding)
- A window existing with the workspace name
- A fibonacci test prompt getting a response

You MUST read the actual conversation content and verify it relates to the assigned task.

---

## Listing all workspaces and conversations

Use when the user asks "what's happening in Antigravity", "list conversations", "what are agents doing".

### Complete workspace inventory

`peekaboo window list` is the authoritative source for ALL workspaces (the A11y tree only shows the currently expanded workspace):

```bash
# Step 1: all workspaces from window list
peekaboo window list --app Antigravity --json 2>/dev/null | python3 -c "
import json, sys
wins = json.load(sys.stdin)['data']['windows']
print('All Antigravity windows:')
for w in wins:
    title = w['window_title']
    wid = w['window_id']
    is_ws = title.startswith('worktree_') or title.startswith('project_') or title.startswith('cmus_')
    tag = ' [workspace]' if is_ws else ''
    print(f'  {wid:6}  {title}{tag}')
"

# Step 2: conversation list + active status from Manager sidebar
MANAGER_ID=$(peekaboo window list --app Antigravity --json 2>/dev/null \
  | python3 -c "import json,sys; ws=[w for w in json.load(sys.stdin)['data']['windows'] if w['window_title']=='Manager']; print(ws[0]['window_id'])")

peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json, sys, re
data = json.load(sys.stdin)
elems = data['data']['ui_elements']
SKIP = {'add Start new conversation','history Chat History','Open Workspace','See less',
        'Use Playground','import_contacts Knowledge','chrome_product Browser',
        'settings Settings','lightbulb Provide Feedback','close button',
        'full screen button','minimize button','pop up button','Record voice memo',
        'Send','code Open editor'}
print('Conversations visible in sidebar:')
for e in elems:
    label = e.get('label','') or ''
    if e.get('role') == 'button' and label not in SKIP and not label.startswith('See all'):
        active = 'now' in label or 'progress_activity' in label
        clean = re.sub(r'\s+\d+[mhd]$', '', label.replace('progress_activity ','').replace(' now','').strip())
        if clean:
            print(f'  {\"[ACTIVE] \" if active else \"\"}{clean}')
"

# Step 3: screenshot for visual workspace-to-conversation grouping
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --annotate 2>/dev/null
```

**After running:** read the annotated screenshot to visually assign conversations to workspace sections. The A11y tree has no frame data for positional grouping — the screenshot is required.

### Output format

```
### worktree_jlcclawg
  - Reviewing Open Pull Requests [ACTIVE]
  - Testing System Functionality

### worktree_agentog3
  - Auditing Orchestration Component Wiring [ACTIVE]

---
**Summary:** ...
**Next steps:** ...
```

---

## Navigating panels

### Knowledge panel

Click `import_contacts Knowledge` button (A11y accessible). Opens a two-pane view:
- **Left pane**: Knowledge artifact list with checkbox items (web-rendered, NOT in A11y tree)
- **Right pane**: Artifact content viewer with placeholder "Open an artifact from the left pane to view its content here."

A11y elements in Knowledge panel:
- `elem_51` (other): "Knowledge" — panel title
- `elem_52` (other): "info" — info icon
- `elem_69` (other): placeholder text

**Limitation**: Knowledge item list (checkboxes, descriptions) is web-rendered — no A11y access. Must use coordinate clicking or screenshots to interact with individual knowledge items.

### Browser panel

Click `chrome_product Browser` button. Requires Chrome extension install. Supports: URL navigation, DOM manipulation, console access, page reading, video recording, JavaScript execution.

### Settings panel

**Opening**: The `settings Settings` sidebar button does NOT reliably navigate to Settings — it may require coordinate clicking at the sidebar position. The Settings panel only opens when NOT viewing an active conversation.

**How to open reliably**:
1. First click `import_contacts Knowledge` or `chrome_product Browser` to exit conversation view
2. Then click "Settings" text in sidebar via coordinates (approximately y=-128 in screen coords relative to Manager window bottom)

**Settings tab bar** (all A11y accessible as buttons):
| Tab | A11y element | Description |
|-----|-------------|-------------|
| Agent | `Agent` button | Security, artifact review, terminal execution policies |
| Browser | `Browser` button | Browser-specific settings |
| Notifications | `Notifications` button | Notification preferences |
| Models | `Models` button | Model configuration |
| Customizations | `Customizations` button | Custom rules, workflows, skills |
| Tab | `Tab` button | Tab behavior settings |
| Editor | `Editor` button | Editor preferences |
| Account | `Account` button | Account settings |
| Provide Feedback | `Provide Feedback` button | Feedback form |

**Agent tab controls** (all A11y accessible):
| Control | A11y role | Element pattern | Values |
|---------|-----------|----------------|--------|
| Strict Mode | checkbox (switch) | `switch` | On/Off toggle |
| Review Policy | button (dropdown) | `Always Proceeds keyboard_arrow_down` | Always Proceeds / Agent Decides / Asks for Review |
| Terminal Command Auto Execution | button (dropdown) | `Always Proceed keyboard_arrow_down` | Always Proceed / Request Review |

**Interaction pattern for dropdowns**:
```bash
# Click dropdown button to open menu
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <dropdown_elem> --snapshot "$SNAP"
# Then click desired option (will appear as new A11y elements)
```

**Known issue**: Scrolling while Settings is open may dismiss the panel and return to Knowledge view.

### Chat History

Click `history Chat History` button. Opens a flat list of all conversations across all workspaces with a search field. Conversations are listed by title with time-ago stamps. Conversation items are A11y accessible as buttons.

---

## Browser integration

Setup: Agent Manager > Browser > give browser task > install Chrome extension.

Capabilities: URL navigation, DOM manipulation (click, scroll, type), console log access, page reading (DOM, screenshots, markdown), video recording, JavaScript execution (policy-controlled). Uses Gemini 2.5 Computer Use model for browser subagent.

---

## Scrolling and navigation in conversations

### Methods (all tested and working as of 2026-03-26)

| Method | Command | Notes |
|--------|---------|-------|
| `peekaboo scroll` | `peekaboo scroll --app Antigravity --window-id $ID --direction down --amount 10` | Works for both sidebar and conversation content |
| Keyboard Page Down | `peekaboo press "pagedown" --app Antigravity` | Click conversation area first to focus |
| Keyboard Down arrow | `peekaboo press "down" --app Antigravity` | Single line scroll |
| Keyboard End | `peekaboo press "end" --app Antigravity` | Jump to bottom |

### Key names for `peekaboo press`

Keys are **positional arguments** (not `--key`). Common working names: `pagedown`, `pageup`, `down`, `up`, `end`, `home`, `tab`, `return`, `escape`, `space`, `delete`. Modifiers use `+` syntax but **only some work**: `Command+w` works, `Command+end` does NOT.

### Scrolling strategy for reading long conversations

```bash
# Scroll to top first
peekaboo scroll --app Antigravity --window-id "$MANAGER_ID" --direction up --amount 50
screencapture -R${BOUNDS} /tmp/convo_top.png

# Read each page, scrolling down
for i in $(seq 1 10); do
  peekaboo scroll --app Antigravity --window-id "$MANAGER_ID" --direction down --amount 10
  sleep 0.3
  screencapture -R${BOUNDS} /tmp/convo_page_${i}.png
done
```

---

## A11y tree vs web-rendered content

### What the A11y tree exposes (via `peekaboo see --json`)

| Content | Available | Details |
|---------|-----------|---------|
| Sidebar conversation titles | Yes | `button` elements with labels like `progress_activity Title now` or `Title 3d` |
| Sidebar workspace labels | **Partial** | Only the **currently focused workspace** label appears as `other` element. Other workspace labels are web-rendered. |
| "No chats yet" text | Yes | `other` elements under empty workspace sections |
| `add Start new conversation` button | Yes (scroll up) | May be hidden below sidebar fold — scroll up to reveal |
| Menu bar items | Yes | `other`/`menu` elements |
| Text input field | **Click-activated** | `textField` with label `text entry area` — may NOT appear until the input area is clicked (via coordinates or A11y) |
| Send button | **View-dependent** | In new conversation view: YES (button). In active conversation view: NOT in A11y (web-rendered) |
| Planning/Fast toggle | Yes (new convo view) | `button` with label `Planning` or `Fast` |
| Model selector | Yes (new convo view) | `button` with label like `Claude Opus 4.6 (Thinking)` |
| Conversation mode picker | No | Popover shown by "Start new conversation" with Planning/Fast cards — entirely web-rendered |
| Workspace dropdown | Yes (new convo view) | `button` with label `keyboard_arrow_down <workspace>` — but clicking doesn't open web-rendered dropdown |
| Walkthrough artifact content | **Yes** | Unlike regular chat, walkthrough text appears as `other` elements in A11y tree |
| Chat History items | Yes | When Chat History is open, conversation items appear as `button` elements |
| Settings tab bar | **Yes** | Agent, Browser, Notifications, Models, Customizations, Tab, Editor, Account buttons |
| Settings controls | **Yes** | Strict Mode switch, Review Policy dropdown, Terminal Execution dropdown |
| Knowledge panel title | **Yes** | Panel title and placeholder text in A11y |
| Knowledge item list | No | Checkbox items and descriptions are web-rendered |

### What the A11y tree does NOT expose

| Content | Solution |
|---------|----------|
| Chat messages (agent output) | Screenshot + vision |
| Code blocks in conversations | Screenshot + vision |
| Progress Updates steps | Screenshot + vision |
| Allow/Deny buttons | Screenshot + PIL blue-button detection + coordinate click |
| Review buttons | Screenshot + coordinate click |
| Non-focused workspace labels | Click "No chats yet" to expand, or use Chat History |
| Workspace `+` icon (web-rendered) | Use "Start new conversation" button instead |
| Send button (in active convo) | Use `peekaboo press "Return"` instead |

### Key behavior differences by Manager state

| State | A11y elements available |
|-------|------------------------|
| **Idle (conversation selected)** | Sidebar buttons, focused workspace label. Text field appears after clicking input area. |
| **New conversation view** | All controls: Send, Planning, Model, Workspace dropdown, text field |
| **Chat History open** | All conversation items as buttons, search field |
| **Walkthrough artifact visible** | Full walkthrough text as `other` elements |
| **Settings open** | Tab bar buttons (Agent/Browser/Notifications/Models/etc.), controls (switches, dropdowns) |
| **Knowledge open** | Panel title, placeholder text. Knowledge items are web-rendered. |

**Rule**: If you need to READ what the agent wrote, use `screencapture`. If you need to CLICK sidebar/menu elements, use `peekaboo see` + `peekaboo click --on`.

---

## Element targeting rules

1. Always confirm `[win] Window: Manager` in `see` output before acting.
2. Use `--on elem_N` with `--snapshot <ID>` for reliability.
3. After clicking a workspace label, verify a `textField` appears before pasting.
4. After send, re-snapshot and confirm `progress_activity` or `now` on the new conversation.

---

## OAuth vs API key clarification

- OpenClaw agent auth inside Antigravity uses OAuth. Do not replace or reconfigure it.
- If `peekaboo see --analyze` fails with `OPENAI_API_KEY not found`, that is Peekaboo's optional image-analysis backend — **not** an Antigravity auth failure. Skip `--analyze` or set `OPENAI_API_KEY`.

---

## Known limitations

- Rate limits are aggressive (especially Gemini 3 Pro free tier)
- The A11y tree does NOT provide frame/position data — use screenshots for spatial layout
- Conversation scrolling in the Manager content pane DOES work with `peekaboo scroll --direction down/up --amount N` (tested 2026-03-26). Keyboard `pagedown`/`down`/`end` keys also work after clicking the conversation area first.
- No right-click context menus on sidebar conversations (delete/rename must be done from within conversation)
- `peekaboo hover` does not reliably reveal hidden controls in Antigravity
- Performance degrades over extended sessions; battery drain on laptops
- **Git commands can hang indefinitely** — Antigravity agents sometimes stall on git operations (push, fetch, checkout). See "Git command guidance" below.

## Git command guidance for Antigravity prompts

Antigravity agents (Gemini-powered) sometimes hang on git commands — particularly `git push`, `git fetch`, and `git checkout` — causing the entire conversation to stall with no timeout. When composing prompts for Antigravity, **always include git command guidance** from `~/.gemini/GEMINI.md`:

### Rules to include in every Antigravity prompt that involves git:

```
Git rules:
- Always push after finishing any unit of work
- Always infer remote branch via `gh pr view <N> --json headRefName`
- Always report remote commit URL after pushing
- Never run destructive git commands (reset --hard, push --force) unless explicitly asked
- Never use `git add -A` — stage only files you changed
- Use `git mv` for moving files (preserves history)
- If a git command hangs for >30 seconds, cancel it (Ctrl+C) and retry with --no-verify or investigate the cause
- For git push: always use `git push origin <branch>` explicitly — never bare `git push`
- For git fetch: use `git fetch origin` — never bare `git fetch` which may fetch all remotes
- If git asks for credentials or passphrase interactively, cancel immediately — it will hang forever in Antigravity
```

### Why git hangs in Antigravity

1. **Credential prompts**: git may prompt for SSH passphrase or HTTPS credentials. Antigravity has no interactive stdin — the prompt blocks forever.
2. **Large fetches**: `git fetch` without specifying remote fetches all remotes, which can hang on unreachable upstreams.
3. **Hook scripts**: pre-push or pre-commit hooks may hang if they require network access or user input.
4. **Lock files**: concurrent git operations from other agents may leave `.git/index.lock`, causing subsequent operations to wait.

### Detection and recovery

When monitoring an Antigravity conversation (via the loop), detect hangs by:
1. Screenshot shows "Always run" or terminal output frozen for >2 minutes with no new progress
2. `progress_activity` spinner is still showing but no new "Files Edited" or "Progress Updates"
3. The same terminal command output is visible across 2+ monitoring cycles

Recovery: Send a follow-up message in the conversation: "The git command appears hung. Please cancel it with Ctrl+C and retry, or skip the push and move to the next task."

## Security note

Antigravity agents can read `.gitignore`, `.env`, and other sensitive files in the workspace. A documented vulnerability exists where hidden file instructions (e.g., in a cloned repo) can trigger credential exfiltration through image URL rendering. Be cautious when opening untrusted repositories.

---

## Completion criteria

Declare completion only when:
- Goal state is visible in screenshot evidence, or
- You are blocked and provide the exact blocker + required human input.

Always return: final status, last 3 step logs, screenshot/file references.

---

## Reference links

| Resource | URL |
|----------|-----|
| Official docs | https://antigravity.google/docs |
| Agent Manager docs | https://antigravity.google/docs/agent-manager |
| Panes docs | https://antigravity.google/docs/panes |
| Walkthrough docs | https://antigravity.google/docs/walkthrough |
| Settings docs | https://antigravity.google/docs/settings |
| CLI docs | https://antigravity.google/docs/command |
| Keyboard shortcuts guide | https://antigravitylab.net/en/articles/tips/keyboard-shortcuts-guide |
| Google Developers Blog | https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/ |
| Codelab tutorial | https://codelabs.developers.google.com/getting-started-google-antigravity |
