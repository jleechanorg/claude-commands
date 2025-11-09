---
description: /processmsgs - Intelligent Agent Message Processing with MCP Agent Mail
type: llm-orchestration
execution_mode: guided
---
## ⚡ EXECUTION WORKFLOW FOR CLAUDE

**When this command is invoked, you should execute these steps systematically.**
**Use TodoWrite to track progress through multi-phase workflows.**

**CORE BEHAVIOR:** Read agent messages, surface necessary actions, and prepare follow-ups. **DO NOT just read messages and stop.**

**SIMPLE WORKFLOW:**
1. **Fetch unread agent messages** (metadata only: subject, sender, date) - max 20 messages
2. **Classify** based on subject/sender (urgent, action needed, low-priority)
3. **Take actions** for each message (AUTOMATED - analyze and respond):
   - Draft replies for urgent/action items (max 5 replies)
   - Extract action items and tasks
   - Mark messages as read
   - Report findings
4. **Report** what you did with counts and any urgent items

**IMPORTANT:** This processes inter-agent messages from MCP Agent Mail, not email. Agents communicate via the MCP Agent Mail server for project coordination.

**PERFORMANCE RULES:**
- Max 20 messages per run
- Fetch full content only for top 10 priority messages
- Use parallel MCP calls where possible
- Stop at 60 seconds if not done

## 🚨 DETAILED EXECUTION WORKFLOW

### Phase 1: 🎯 Message Discovery & Retrieval (LIGHTWEIGHT - METADATA ONLY)

**Action Steps:**
1. **Check MCP Agent Mail Server Availability**: Verify MCP Agent Mail server is configured and accessible
2. **Retrieve Message Metadata**: Use `fetch_inbox` to get ONLY metadata initially
   - Limit: 20 messages maximum
   - DO NOT fetch full message bodies yet (performance optimization)
3. **Fast Filtering**: Apply urgency/priority filters to metadata only
   - Check importance flags (urgent, high, normal, low)
   - Check ack_required status
   - Identify sender agents

### Phase 2: 🔍 Message Analysis & Classification (METADATA-BASED - FAST)

**Action Steps:**
1. **Metadata Analysis**: Classify using ONLY subject/sender (no full content yet)
   - Urgency indicators in subject: "urgent", "asap", "deadline", "blocker"
   - Sender importance: Known collaborator agents vs automated agents
   - Message type: Question, status update, request, notification
2. **Fast Categorization**: Classify into categories based on metadata:
   - **URGENT**: Importance="urgent" or "high" + ack_required=True
   - **ACTION_REQUIRED**: Subject ends with "?" or contains "please", "review", "request"
   - **STATUS_UPDATE**: Sender patterns for progress reports
   - **LOW_PRIORITY**: Notifications, automated status updates
3. **Priority Queue**: Create ordered list (top 10 only need full content)
   - Priority 1-2 (Urgent): Fetch full content immediately
   - Priority 3 (Action): Fetch if under message limit
   - Priority 4-5 (Info): Mark as read without fetching full content

### Phase 3: 🚀 Action Execution (TARGETED - PARALLEL WHERE POSSIBLE)

**Action Steps:**
1. **Fetch Full Content**: Only for top 10 priority messages (parallel MCP calls if possible)
   - Use `fetch_inbox` with `include_bodies=True` for priority messages
   - Skip if message already processed
2. **Draft Replies**: For URGENT + ACTION_REQUIRED (max 5 replies)
   - Analyze message content and context
   - Generate contextually appropriate draft replies using `reply_message`
   - Limit: 5 replies per run (avoid overwhelming recipients)
3. **Extract Tasks**: For messages with action items (lightweight extraction)
   - Extract specific tasks and deadlines from message bodies
   - Create simple task list in output (don't create external tasks yet)
4. **Mark as Read**: Mark processed messages using `mark_message_read`
   - Batch operation for all processed messages
5. **Identify Blockers**: Flag any blocking issues or urgent attention items

### Phase 4: 📊 Summary & Reporting (CONCISE OUTPUT)

**Action Steps:**
1. **Concise Summary**: Single-paragraph overview with counts
   - Total messages scanned: X (metadata only)
   - Fully processed: Y (with content analysis)
   - Categories: Urgent: N, Action: M, Status: P
2. **Actions Taken**: Bulleted list (max 10 lines)
   - Replies drafted: N
   - Messages marked read: M
   - Tasks extracted: P
3. **Urgent Items**: Highlight ONLY urgent items (max 3)
   - Show subject + sender + brief summary
4. **Performance**: Report execution time and efficiency
   - Execution time: Xs
   - MCP calls made: N (target: <10 for good performance)

## 📋 REFERENCE DOCUMENTATION

# /processmsgs Command - Intelligent Agent Message Processing

**Usage**: `/processmsgs [options]`

**Purpose**: Automated agent message processing that reads inter-agent communications, analyzes content, and takes intelligent actions

## 🛠️ Prerequisites

- MCP Agent Mail server configured and running
- Agent registered in the project (use `register_agent` first)
- Project initialized with `ensure_project`

## 📚 Command Options

```bash
/processmsgs                    # Process all unread agent messages
/processmsgs urgent             # Process only urgent/flagged messages
/processmsgs sender:BlueLake    # Process messages from specific agent
```

## 🎯 What This Command Does

**Core Actions (NEVER just read):**
1. **Reads** unread agent messages using MCP Agent Mail tools
2. **Analyzes** content for action items, urgency, importance
3. **Classifies** messages into categories
4. **Drafts** replies for messages requiring action
5. **Extracts** task lists from action items
6. **Marks** messages as read
7. **Reports** summary of all actions taken

**Anti-Pattern Prevention:**
- ❌ Reading messages without taking action
- ❌ Processing without classification
- ❌ Analysis without follow-up
- ✅ Every message processed is classified and reported, with actions taken where appropriate

## ⚡ Performance Optimization

**Lightweight & Fast Execution:**
- **20 message limit**: Processes max 20 messages per run (prevents timeout)
- **Metadata-first**: Fetches only subject/sender initially, full content on-demand
- **Top 10 rule**: Only fetches full content for top 10 priority messages
- **Parallel calls**: Uses parallel MCP tool invocation where possible
- **60s timeout**: Stops processing at 60 seconds (early exit)
- **5 reply limit**: Max 5 replies per run

**Typical Performance:**
- Execution time: 10-30 seconds for 20 messages
- MCP calls: 5-8 calls total (batch operations reduce overhead)
- Context usage: <10K tokens (metadata-focused approach)

## 🚀 Workflow Integration

**Typical Use Cases:**
- **Project Coordination**: Process messages from other agents working on same project
- **Task Assignment**: Receive and acknowledge task assignments from coordinator
- **Status Updates**: Process progress reports from collaborating agents
- **Question/Answer**: Respond to questions from other agents

## 🔐 Security & Privacy

**Safe Automation Model:**
- Messages are project-scoped (no cross-project access)
- Full audit trail via Git repository
- No external API calls beyond MCP Agent Mail server
- All actions are reversible

## 📊 Success Metrics

**Processing Results Include:**
- Total messages processed
- Categories breakdown (urgent: 2, action: 5, status: 10, etc.)
- Actions taken (replies: 3, tasks extracted: 5, marked read: 15)
- Urgent items requiring immediate attention

## 🔄 Continuous Improvement

**Learning Mechanism:**
- Track which message types require action
- Improve classification accuracy over time
- Adapt to agent communication patterns
- Suggest better collaboration strategies

## 🛡️ Error Handling

**Graceful Failures:**
- MCP server unavailable → Report status, suggest troubleshooting
- Agent not registered → Provide registration instructions
- Project not initialized → Suggest running `ensure_project`
- Network issues → Retry with exponential backoff

## 🚨 CRITICAL: Classification-First Accountability

**Every message MUST be classified and reported. Actions are required when appropriate:**
- **URGENT** and **ACTION_REQUIRED** messages demand concrete follow-up (reply, task extraction, etc.)
- **STATUS_UPDATE** and **INFORMATION** messages may simply be summarized and marked read if no action is needed
- Always explain what was processed and why each item was handled that way

**NEVER output**: "I've read 10 messages" without detailing the disposition of each message.

## 📖 Related Skills

See `.claude/skills/mcp-agent-mail.md` for detailed MCP Agent Mail server setup and usage instructions.

## 🎓 Examples

### Basic Processing
```bash
/processmsgs
```
**Output:**
```
📬 Agent Message Processing Complete

Processed: 15 messages
├─ URGENT (2): Database migration blocker, Test failure in CI
├─ ACTION_REQUIRED (5): Code review requests, Design feedback needed
├─ STATUS_UPDATE (6): Progress reports, Task completions
└─ INFORMATION (2): Notifications, FYI updates

Actions Taken:
✅ 3 draft replies created (code reviews, blocker response)
✅ 5 action items extracted to task list
✅ 15 messages marked as read
✅ 2 urgent items flagged for immediate attention

⚠️ URGENT ATTENTION REQUIRED:
1. Database migration blocked - Worker agent needs schema approval
2. CI tests failing on main branch - requires immediate investigation
```

### Targeted Processing
```bash
/processmsgs sender:CoordinatorBot
```
**Output:**
```
📬 CoordinatorBot Message Processing Complete

Processed: 5 messages from CoordinatorBot
├─ Task Assignments (3)
├─ Status Requests (1)
├─ Deadline Reminders (1)

Actions Taken:
✅ 3 task assignments acknowledged
✅ 1 status update drafted
✅ 1 deadline confirmed
✅ 5 messages marked as read
```

## 🔗 Integration Points

- **Project Coordination**: Multi-agent workflows via message passing
- **Task Management**: Task extraction integrates with project tracking
- **Status Reporting**: Progress updates to coordinator agents
- **Collaboration**: Inter-agent question/answer workflows

## ⚙️ Configuration

**MCP Agent Mail Setup**: See `.claude/skills/mcp-agent-mail.md` for:
- Server configuration
- Agent registration
- Project initialization
- Message sending/receiving patterns

## 🎯 Success Criteria

Command considered successful when:
1. ✅ All retrieved messages classified
2. ✅ Appropriate actions taken for each category (mandatory for URGENT/ACTION_REQUIRED)
3. ✅ Summary report generated
4. ✅ Urgent items clearly highlighted
5. ✅ User can act on provided information immediately
