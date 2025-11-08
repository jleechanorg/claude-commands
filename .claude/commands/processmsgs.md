---
description: /processmsgs - Intelligent Email Processing with MCP Gmail Agent
type: llm-orchestration
execution_mode: guided
---
## ⚡ EXECUTION WORKFLOW FOR CLAUDE

**When this command is invoked, you should execute these steps systematically.**
**Important: Always create drafts for user review before any send operations.**
**Use TodoWrite or an equivalent tracker to monitor progress through multi-phase workflows.**

**CORE BEHAVIOR:** Read messages, surface necessary actions, and prepare follow-ups. **DO NOT just read messages and stop.**

**SIMPLE WORKFLOW:**
1. **Fetch unread emails** (metadata only: subject, sender, date) - max 20 emails
2. **Classify** based on subject/sender (urgent, action needed, low-priority)
3. **Take actions** for each email (FULLY AUTOMATED - no user confirmation needed):
   - Draft responses for urgent/action items (max 5 drafts - automatically saved)
   - Apply labels (claude-processed, urgent, action-required)
   - Archive low-priority emails
   - Star urgent items
4. **Report** what you did with counts and any urgent items

**IMPORTANT:** Drafts are created automatically and saved to Gmail. Nothing is sent. User reviews/sends drafts later in Gmail at their convenience. This keeps execution fast (10-30s) and automated.

**PERFORMANCE RULES:**
- Max 20 emails per run
- Fetch full content only for top 10 priority emails
- Batch label/archive operations (not one-by-one)
- Use parallel MCP calls where possible
- Stop at 60 seconds if not done

## 🚨 DETAILED EXECUTION WORKFLOW

### Phase 1: 🎯 Email Discovery & Retrieval (LIGHTWEIGHT - METADATA ONLY)

**Action Steps:**
1. **Check MCP Gmail Server Availability**: Verify MCP Gmail server is configured and accessible
2. **Retrieve Email Metadata**: Use Gmail query filters to fetch ONLY metadata (id, subject, from, date)
   - Limit: 20 emails maximum
   - Query: `is:unread` or `newer_than:1d` with server-side filtering
   - DO NOT fetch full email bodies yet (performance optimization)
3. **Fast Filtering**: Apply urgency/priority filters to metadata only
   - Sender domain whitelist (e.g., @company.com, @client.com)
   - Subject keywords (urgent, deadline, action required)
   - Skip automated senders (noreply@, no-reply@, notifications@)

### Phase 2: 🔍 Email Analysis & Classification (METADATA-BASED - FAST)

**Action Steps:**
1. **Metadata Analysis**: Classify using ONLY subject/sender (no full content yet)
   - Urgency indicators in subject: "urgent", "asap", "deadline", "action required"
   - Sender importance: Known domains vs automated senders
   - Information type: Newsletter patterns, notification patterns
2. **Fast Categorization**: Classify into categories based on metadata:
   - **URGENT**: Subject contains urgency keywords + important sender
   - **ACTION_REQUIRED**: Subject ends with "?" or contains "please", "request"
   - **AUTOMATED**: Sender matches noreply/automated patterns
   - **LOW_PRIORITY**: Newsletters, notifications, automated emails
3. **Priority Queue**: Create ordered list (top 10 only need full content)
   - Priority 1-2 (Urgent): Fetch full content immediately
   - Priority 3 (Action): Fetch if under email limit
   - Priority 4-5 (Info/Auto): Archive without reading full content

### Phase 3: 🚀 Action Execution (BATCHED - PARALLEL WHERE POSSIBLE)

**Action Steps:**
1. **Fetch Full Content**: Only for top 10 priority emails (parallel MCP calls)
   - Use parallel tool invocation for multiple email fetches
   - Skip if email already processed (has "claude-processed" label)
2. **Draft Responses**: For URGENT + ACTION_REQUIRED (max 5 drafts)
   - Generate contextually appropriate draft replies
   - **AUTOMATICALLY save drafts** using MCP Gmail tools (parallel if possible)
   - NO user confirmation needed during execution - drafts are safe, nothing sent
   - Limit: 5 drafts per run (user reviews in Gmail later, not during command)
3. **Extract Tasks**: For emails with action items (lightweight extraction)
   - Extract specific tasks and deadlines
   - Create simple task list in output (don't create external tasks yet)
4. **Batch Label Operations**: Apply labels in single batch operation
   - Collect all email IDs needing labels first
   - Single MCP batch call to apply all labels at once
   - Labels: "claude-processed", "action-required", "urgent"
5. **Batch Archive**: Archive low-priority emails in single operation
   - Collect all AUTOMATED and LOW_PRIORITY email IDs
   - Single MCP batch archive call (not one-by-one)
6. **Star Urgent**: Flag URGENT emails (parallel operation if >1)

### Phase 4: 📊 Summary & Reporting (CONCISE OUTPUT)

**Action Steps:**
1. **Concise Summary**: Single-paragraph overview with counts
   - Total emails scanned: X (metadata only)
   - Fully processed: Y (with content analysis)
   - Categories: Urgent: N, Action: M, Low-priority: P
2. **Actions Taken**: Bulleted list (max 10 lines)
   - Drafts created: N
   - Emails labeled: M
   - Emails archived: P
   - Emails starred: Q
3. **Urgent Items**: Highlight ONLY urgent items (max 3)
   - Show subject + sender + brief summary
4. **Performance**: Report execution time and efficiency
   - Execution time: Xs
   - MCP calls made: N (target: <10 for good performance)

## 📋 REFERENCE DOCUMENTATION

# /processmsgs Command - Intelligent Email Processing with MCP Gmail Agent

**Usage**: `/processmsgs [options]`

**Purpose**: Automated email processing that reads messages, analyzes content, and takes intelligent actions - never just reads and does nothing

## 🛠️ Prerequisites

- MCP Gmail server configured in `.claude/settings.json`
- Gmail API authentication completed (see `.claude/skills/mcp-gmail-agent.md`)
- Appropriate Gmail permissions (read, compose, modify)

## 📚 Command Options

```bash
/processmsgs                    # Process all unread emails
/processmsgs recent             # Process emails from last 24h regardless of read status
/processmsgs urgent             # Process only urgent/flagged emails
/processmsgs sender:example.com # Process emails from specific domain
/processmsgs label:inbox        # Process emails with specific label
```

## 🎯 What This Command Does

**Core Actions (NEVER just read):**
1. **Reads** unread emails using MCP Gmail tools
2. **Analyzes** content for action items, urgency, importance
3. **Classifies** emails into categories
4. **Drafts** responses for emails requiring action
5. **Labels** emails for organization
6. **Archives** low-priority emails
7. **Flags** urgent items
8. **Creates** task lists from action items
9. **Reports** summary of all actions taken

**Anti-Pattern Prevention:**
- ❌ Reading emails without taking action
- ❌ Processing without classification
- ❌ Analysis without follow-up
- ✅ Every email processed is classified and reported, with actions taken where appropriate

## ⚡ Performance Optimization

**Lightweight & Fast Execution:**
- **20 email limit**: Processes max 20 emails per run (prevents timeout)
- **Metadata-first**: Fetches only subject/sender initially, full content on-demand
- **Top 10 rule**: Only fetches full content for top 10 priority emails
- **Batch operations**: Labels/archives in single MCP calls (not iterative)
- **Parallel calls**: Uses parallel MCP tool invocation where possible
- **60s timeout**: Stops processing at 60 seconds (early exit)
- **5 draft limit**: Max 5 drafts per run (user reviews later in Gmail, not during execution)

**Typical Performance:**
- Execution time: 10-30 seconds for 20 emails
- MCP calls: 5-8 calls total (batch operations reduce overhead)
- Context usage: <10K tokens (metadata-focused approach)

## 🚀 Workflow Integration

**Typical Use Cases:**
- **Morning Routine**: `/processmsgs` - Process overnight emails before starting work
- **Quick Check**: `/processmsgs urgent` - Handle time-sensitive matters
- **Batch Processing**: `/processmsgs recent` - Process accumulated messages
- **Targeted Review**: `/processmsgs sender:client.com` - Focus on specific communications

## 🔐 Security & Privacy

**Safe Automation Model:**
- **Drafts created automatically** - Safe operation, nothing is sent without user action
- User reviews and sends drafts from Gmail at their convenience
- All actions (label, archive, star) are reversible and safe
- NO emails sent automatically - only drafts created

**Data Handling:**
- Email content analyzed locally, not stored permanently
- No external API calls beyond configured MCP Gmail server
- User maintains full control over what gets sent (reviews drafts in Gmail)

## 📊 Success Metrics

**Processing Results Include:**
- Total emails processed
- Categories breakdown (urgent: 2, action: 5, info: 10, etc.)
- Actions taken (drafts: 3, labels: 15, archived: 8, flagged: 2)
- Tasks created with deadlines
- Urgent items requiring immediate attention

## 🔄 Continuous Improvement

**Learning Mechanism:**
- Track which actions user approves/modifies
- Improve classification accuracy over time
- Adapt to user's communication patterns
- Suggest better email management strategies

## 🛡️ Error Handling

**Graceful Failures:**
- MCP server unavailable → Report status, suggest troubleshooting
- Authentication expired → Provide re-authentication instructions
- API rate limits → Process in batches, queue remaining
- Network issues → Retry with exponential backoff

## 🚨 CRITICAL: Classification-First Accountability

**Every email MUST be classified and reported. Actions are required when appropriate:**
- **URGENT** and **ACTION_REQUIRED** emails demand concrete follow-up (draft, label, task, etc.)
- **INFORMATION** and **AUTOMATED** emails may simply be summarized and archived if no action is needed
- Always explain what was processed and why each item was handled that way

**NEVER output**: "I've read 10 emails" without detailing the disposition of each message.

## 📖 Related Skills

See `.claude/skills/mcp-gmail-agent.md` for detailed MCP Gmail server setup and authentication instructions.

## 🎓 Examples

### Basic Processing
```bash
/processmsgs
```
**Output:**
```
📧 Email Processing Complete

Processed: 15 emails
├─ URGENT (2): Client deadline inquiry, Server alert
├─ ACTION_REQUIRED (5): PR reviews, Meeting requests
├─ INFORMATION (6): Team updates, Release notes
└─ AUTOMATED (2): Newsletter, Notifications

Actions Taken:
✅ 3 draft replies created (PR reviews)
✅ 2 emails flagged as urgent
✅ 5 action items extracted to task list
✅ 8 emails labeled and archived
✅ 2 emails starred for follow-up

⚠️ URGENT ATTENTION REQUIRED:
1. Client deadline moved to tomorrow - draft response prepared
2. Server CPU usage >90% - investigate immediately
```

### Targeted Processing
```bash
/processmsgs sender:github.com
```
**Output:**
```
📧 GitHub Email Processing Complete

Processed: 8 GitHub emails
├─ PR Comments (3)
├─ Issue Mentions (2)
├─ Security Alerts (1)
├─ Release Notifications (2)

Actions Taken:
✅ 3 draft responses to PR comments
✅ 1 security issue flagged URGENT
✅ 2 PRs added to review queue
✅ 2 release emails archived
```

## 🔗 Integration Points

- **Task Management**: Extracted tasks can integrate with `/memory` command
- **PR Workflow**: GitHub emails trigger `/copilot` or `/fixpr` workflows
- **Calendar**: Meeting requests auto-draft acceptance/decline responses
- **Documentation**: Questions about codebase can trigger `/learn` lookups

## ⚙️ Configuration

**Configuration roadmap:** Future iterations may add configurable thresholds for auto-archiving, urgency keyword tuning, and trusted sender lists. Track progress in the linked follow-up issue before attempting to rely on configuration files.

## 🎯 Success Criteria

Command considered successful when:
1. ✅ All retrieved emails classified
2. ✅ Appropriate actions taken for each category (mandatory for URGENT/ACTION_REQUIRED)
3. ✅ Summary report generated
4. ✅ Urgent items clearly highlighted
5. ✅ User can act on provided information immediately
