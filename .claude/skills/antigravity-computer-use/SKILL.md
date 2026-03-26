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
| `more_horiz` | text | Workspace options menu |

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

---

## Model selection

Available in per-conversation dropdown:

| Model | Notes |
|-------|-------|
| Gemini 3 Pro (High/Low) | Default |
| Gemini 3 Flash | Lighter/faster |
| Gemini 3 Deep Think | Reasoning-heavy |
| Claude Sonnet 4.5/4.6 (Thinking/Standard) | Anthropic models |
| Claude Opus 4.6 | Anthropic flagship |
| GPT-OSS-120B | OpenAI model |

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

Antigravity shows an "Allow this conversation" dialog when starting/resuming sessions. **Always click Allow without asking the user** — pre-authorized.

```bash
peekaboo see --app Antigravity --annotate
# If allow button found (e.g. elem_7: "Allow this conversation"):
peekaboo click --app Antigravity --on elem_7
peekaboo see --app Antigravity --annotate  # confirm gone
```

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

### Method 1: Click workspace label in Manager sidebar

Clicking the workspace `other` element (e.g., `worktree_jlcclawg`) opens a new conversation scoped to that workspace. A text input area and Send button appear.

### Method 2: Workspace `add` button

If visible, click the workspace-specific `add` button.

### ⚠️ Known issue: "Open Workspace" dropdown scoping

The `Open Workspace` button (sidebar) opens a dropdown with `menuitem_*` elements listing known workspaces. **Clicking a workspace in this dropdown does NOT reliably scope the new conversation to that workspace.** It may open in whichever workspace was last active. Workaround: include the explicit workspace path in your prompt (e.g., "You are working in /path/to/worktree on branch X").

### Full flow (Method 0+1 combined — most reliable)

```bash
MANAGER_ID=<MANAGER_ID>

# Step 1: If workspace not in Manager sidebar, open via CLI first
agy /path/to/workspace
sleep 2

# Step 2: Get fresh snapshot (workspace may need scrolling to appear)
SNAP=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")

# Step 3: Find the workspace label — may need to scroll down
# Look for: elem with role 'other' and label matching workspace name
# If not visible, scroll: peekaboo scroll --direction down --amount 5
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    label = e.get('label','') or ''
    if 'worktree_' in label or 'project_' in label:
        print(e['id'], e.get('role',''), label)"

# Step 4: Click workspace label to open new conversation
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <WORKSPACE_ELEM> --snapshot "$SNAP"
sleep 0.5

# Step 5: Find text field and Send button
SNAP2=$(peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['data']['snapshot_id'])")
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    role = e.get('role','')
    label = e.get('label','') or ''
    if role == 'textField' or label == 'Send':
        print(e['id'], role, label)"

# Step 6: Click text field, paste prompt, click Send button
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <TEXT_FIELD_ID> --snapshot "$SNAP2"
peekaboo paste --app Antigravity --text "your prompt here"
# IMPORTANT: Click the Send button — more reliable than pressing Return
peekaboo click --app Antigravity --window-id "$MANAGER_ID" --on <SEND_BUTTON_ID> --snapshot "$SNAP2"

# Step 7: Verify conversation started (look for progress_activity)
sleep 3
peekaboo see --app Antigravity --window-id "$MANAGER_ID" --json 2>/dev/null | python3 -c "
import json,sys; data=json.load(sys.stdin)
for e in data['data']['ui_elements']:
    label = e.get('label','') or ''
    if 'progress_activity' in label:
        print('ACTIVE:', label[:100])"
```

### Important notes

- **Use `peekaboo paste` not `peekaboo type`** — paste avoids character drift in Antigravity's input field.
- **Click the `Send` button** (label="Send") rather than pressing Return — more reliable.
- **Always include the explicit workspace path in your prompt** as a safety net for workspace scoping: "You are working in /path/to/worktree on branch X"
- **New workspaces need scrolling** — after `agy <path>`, the Manager sidebar may not show the workspace without scrolling down.

---

## MANDATORY: Monitor, read, and assess active conversations

**This is the most important part of the skill.** Starting a conversation is useless if you don't read what Gemini is actually producing and respond to it. Every interaction with Antigravity MUST include a read-assess-respond cycle.

### After starting or checking a conversation, ALWAYS:

1. **Read the conversation content** — use `peekaboo see` on the conversation window (NOT just the Manager) to extract what Gemini wrote:

```bash
# Read conversation content from a workspace window
peekaboo see --app Antigravity --window-id <CONVO_WINDOW_ID> --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for el in data['data']['ui_elements']:
    val = el.get('value','') or el.get('title','')
    role = el.get('role','')
    if val and len(val) > 15 and role not in ('group','window','toolbar'):
        print(val[:300])
        print('---')
" 2>&1 | tail -80
```

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
Click `import_contacts Knowledge` button. Shows artifacts and documents. Empty state: "Open an artifact from the left pane to view its content here."

### Browser panel
Click `chrome_product Browser` button. Requires Chrome extension install. Supports: URL navigation, DOM manipulation, console access, page reading, video recording, JavaScript execution.

### Settings panel
Click `settings Settings` button. Covers: execution policies, review policies, JS execution policy, allow/deny lists, browser URL allowlist.

### Chat History
Click `history Chat History` button. Browse past conversations.

---

## Browser integration

Setup: Agent Manager > Browser > give browser task > install Chrome extension.

Capabilities: URL navigation, DOM manipulation (click, scroll, type), console log access, page reading (DOM, screenshots, markdown), video recording, JavaScript execution (policy-controlled). Uses Gemini 2.5 Computer Use model for browser subagent.

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
- Conversation scrolling in the Manager content pane does not respond to `peekaboo scroll` — use keyboard (Page Down) or switch to workspace window
- No right-click context menus on sidebar conversations (delete/rename must be done from within conversation)
- `peekaboo hover` does not reliably reveal hidden controls in Antigravity
- Performance degrades over extended sessions; battery drain on laptops

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
