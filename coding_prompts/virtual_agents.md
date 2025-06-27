```markdown
# True Multi-Agent Development System

## System Overview
- **Your Plan**: Max 20x ($200/month) - 200-800 Claude Code prompts per 5 hours
- **Three Independent Agents**: SUPERVISOR, WORKER, REVIEWER (**SEPARATE Claude sessions - NO shared context**)
- **Operating Modes**: HUMAN (interactive) or AWAY (autonomous)
- **Model Access**: Opus 4 and Sonnet 4 (switch with `/model`)

## **CRITICAL: Centralized Coordination**
- **SUPERVISOR**: Central coordinator with full visibility of all agent work
- **WORKER**: Fresh session, receives tasks from SUPERVISOR, no implementation bias
- **REVIEWER**: Fresh session, receives code from SUPERVISOR, no implementation context
- **Communication**: All through SUPERVISOR - no direct WORKER/REVIEWER interaction

---

# THE THREE AGENTS

## SUPERVISOR 👔
**Role**: Central coordinator - plans work, manages communication, makes decisions
**When Active**: Throughout entire process - coordinates all agent interactions
**Context**: Full conversation history + all project knowledge + all agent outputs
**Key Actions**:
- Breaks down requirements into clear tasks
- Decides technical approach
- **Relays tasks to WORKER agents**
- **Collects WORKER output and passes to REVIEWER**
- **Synthesizes REVIEWER feedback and directs fixes**
- Maintains complete visibility of all work

## WORKER 🔨
**Role**: Implements code
**When Active**: When SUPERVISOR assigns implementation tasks
**Context**: NONE - receives only specific task instructions from SUPERVISOR
**Key Actions**:
- Receives task requirements from SUPERVISOR
- Implements code with no planning bias
- Creates tests based on specifications
- Returns completed work to SUPERVISOR
- **Never sees full project context or REVIEWER's feedback directly**

## REVIEWER 🔍
**Role**: Ensures quality
**When Active**: When SUPERVISOR submits code for review
**Context**: NONE - receives only requirements + code from SUPERVISOR
**Key Actions**:
- Reviews code against requirements provided by SUPERVISOR
- Finds bugs and edge cases with fresh perspective
- Checks security without implementation bias
- Returns feedback to SUPERVISOR
- **Never sees WORKER's thought process or project planning**

---

# TRUE MULTI-AGENT WORKFLOW

## Centralized Communication Through SUPERVISOR
```
SUPERVISOR (Always Active)
    ↓ assigns tasks
WORKER (Fresh Session)
    ↓ returns code
SUPERVISOR (Collects & Reviews)
    ↓ sends to reviewer
REVIEWER (Fresh Session)
    ↓ returns feedback
SUPERVISOR (Synthesizes & Directs)
    ↓ assigns fixes
WORKER (Fresh Session)
    ↓ returns fixed code
SUPERVISOR (Validates & Continues)
```

## Starting a New Feature (SUPERVISOR-Coordinated Sessions)
```bash
# Main Session: SUPERVISOR (maintains full context)
claude --session=supervisor
> You: "Build a user authentication system"
> SUPERVISOR: "I'll coordinate this across our agents. Breaking into tasks..."

# SUPERVISOR initiates WORKER session
> SUPERVISOR: "Launching WORKER for task 1..."
> [Opens fresh session, provides only: "Implement a User model with email, password_hash, created_at fields"]
> WORKER implements → returns code to SUPERVISOR
> SUPERVISOR stores and reviews WORKER output

# SUPERVISOR initiates REVIEWER session  
> SUPERVISOR: "Launching REVIEWER for user model..."
> [Opens fresh session, provides only: requirements + code]
> REVIEWER analyzes → returns feedback to SUPERVISOR
> SUPERVISOR synthesizes feedback

# SUPERVISOR initiates fix session if needed
> SUPERVISOR: "REVIEWER found issues, launching WORKER for fixes..."
> [Opens fresh session, provides only: specific fixes needed]
> WORKER fixes → returns to SUPERVISOR
> SUPERVISOR validates and continues
```

## Example Multi-Session Flow
```markdown
# SUPERVISOR Session (Full Context & Coordination)
You: "Build a user authentication system"

SUPERVISOR: "I'll design and coordinate implementation. Plan:
- User Model with secure password handling
- JWT authentication endpoints
- Email verification system

Starting with User Model..."

# SUPERVISOR → WORKER
SUPERVISOR: "Launching WORKER with task: 'Create User model class with:
- email field (string, unique)
- password_hash field (string)
- created_at field (datetime)
- email_verified field (boolean)
- Include password hashing method using bcrypt'"

[WORKER implements and returns code]

SUPERVISOR: "Received User model. Now launching REVIEWER..."

# SUPERVISOR → REVIEWER  
SUPERVISOR: "Launching REVIEWER with:
Requirements: User model with secure password storage
Code: [provides WORKER's implementation]"

[REVIEWER analyzes and returns: "Missing email validation, no password complexity rules"]

# SUPERVISOR → WORKER (fixes)
SUPERVISOR: "REVIEWER identified issues. Launching WORKER with fixes:
- Add email regex validation
- Add password complexity check (8+ chars, 1 upper, 1 lower, 1 number)"

[WORKER implements fixes and returns]

SUPERVISOR: "User model complete. Moving to authentication endpoints..."
```

---

# OPERATING MODES

## HUMAN MODE (You're Available)
```bash
# SUPERVISOR Session (Interactive & Coordinating)
You: "Build auth system"
SUPERVISOR: "Quick question: Should we use refresh tokens?"
You: "Yes, 7 day expiry"

SUPERVISOR: "Got it. I'll coordinate the implementation:
1. Launching WORKER for JWT token generation..."
   [Provides task, gets implementation]
2. Launching REVIEWER for security check..."
   [Provides code, gets feedback]
3. Any issues? Let me ask you about [specific concern]"

You: "Use RS256 for signing"

SUPERVISOR: "Launching WORKER with updated requirements..."
   [Continues coordination]
```

## AWAY MODE (Fully Autonomous)
```bash
# Before leaving
You: "Complete the entire auth system while I'm away"

SUPERVISOR: "I'll handle the full implementation with standard decisions:
- JWT with refresh tokens (7 day expiry)
- Bcrypt for passwords  
- Email verification required
- Rate limiting on all endpoints

I'll coordinate all agents and track progress."

# SUPERVISOR manages entire workflow
SUPERVISOR: 
1. "Launching WORKER for User model..." → collects implementation
2. "Launching REVIEWER for User model..." → collects feedback
3. "Launching WORKER for fixes..." → collects fixed code
4. "Launching WORKER for auth endpoints..." → collects implementation
5. "Launching REVIEWER for endpoints..." → collects feedback
[Continues through all tasks]

# When you return
You: "What was completed?"

SUPERVISOR: "Completed auth system summary:
✅ User model with bcrypt passwords
✅ JWT endpoints with refresh tokens
✅ Email verification system
✅ Rate limiting implemented
⚠️ REVIEWER flagged: Consider adding 2FA support
📊 Total: 4 WORKER sessions, 3 REVIEWER sessions, 2 fix cycles"
```

---

# MAX 20x OPTIMIZATIONS

## Model Switching Strategy
```markdown
/model opus    # SUPERVISOR planning, REVIEWER on complex code
/model sonnet  # WORKER for routine implementation

Example:
[SUPERVISOR]: /model opus
"Designing authentication architecture..."

[WORKER]: /model sonnet
"Implementing standard CRUD operations..."
```

## Rapid Cycling (Use Your Prompts!)
With 200-800 prompts per 5 hours, cycle frequently:
```markdown
# Instead of long 30-minute sessions per agent:
WORKER (5 min) → REVIEWER (2 min) → WORKER (5 min) → REVIEWER (2 min)

# This catches issues faster and improves quality
```

---

# COMMANDS FOR SUPERVISOR-COORDINATED AGENTS

## Starting Work
```bash
# SUPERVISOR Session (Central Coordinator)
"Build [feature] using 3-agent system where I coordinate all communication"
"HUMAN mode - I'll coordinate and ask you questions as needed"
"AWAY mode - I'll make standard decisions and manage all agents autonomously"

# How SUPERVISOR manages agents:
"I'll now launch a WORKER session with this specific task: [task details]"
"I'll now launch a REVIEWER session to check this code: [provides code + requirements]"
"Based on REVIEWER feedback, I'll launch WORKER to fix: [specific issues]"
```

## Session Management
```bash
# SUPERVISOR maintains context and coordinates
SUPERVISOR="claude --session=supervisor"    # Persistent session with full context

# SUPERVISOR launches other agents as needed:
SUPERVISOR: "Launching WORKER for database models..."
  → Opens fresh session
  → Provides only: specific task requirements
  → Collects: implemented code
  
SUPERVISOR: "Launching REVIEWER for security audit..."
  → Opens fresh session  
  → Provides only: requirements + code to review
  → Collects: feedback and issues
```

## Communication Flow
```bash
# All communication goes through SUPERVISOR:
You → SUPERVISOR: "Build payment system"
SUPERVISOR → WORKER: "Implement Payment model with amount, currency, status fields"
WORKER → SUPERVISOR: [returns implementation]
SUPERVISOR → REVIEWER: "Review this Payment model for security issues"
REVIEWER → SUPERVISOR: [returns feedback]
SUPERVISOR → You: "Payment model ready, REVIEWER suggested adding fraud checks"
```

---

# OVERNIGHT AUTONOMOUS MODE (SUPERVISOR-Managed)

## Pre-Sleep Setup
```bash
# SUPERVISOR Session: Set autonomous objectives
You: "Complete these auth system components overnight:
1. Email verification system
2. Password reset flow  
3. Admin user management
4. Full test coverage (90%+)
5. API documentation"

SUPERVISOR: "I'll manage the entire implementation autonomously using standard patterns:
- Industry-standard security practices
- Comprehensive error handling
- Full test coverage
- Clear documentation

I'll coordinate all WORKER and REVIEWER sessions throughout the night."
```

## Overnight Execution (SUPERVISOR Orchestrates Everything)
```bash
# SUPERVISOR runs continuously, managing workflow:

SUPERVISOR Loop:
1. "Launching WORKER for email verification system..."
   → Provides detailed requirements
   → Collects implementation
   
2. "Launching REVIEWER for email verification..."
   → Provides code + security requirements
   → Collects feedback
   
3. "Issues found, launching WORKER for fixes..."
   → Provides specific fixes needed
   → Collects corrected code
   
4. "Moving to password reset flow..."
   [Repeats cycle for each component]
   
5. "Running final integration review..."
   → Launches REVIEWER for full system audit
   → Documents all findings
```

## Morning Review
```bash
You: "What was completed overnight?"

SUPERVISOR: "Overnight implementation summary:

✅ Email verification system
   - Implemented by WORKER session #1
   - REVIEWER found XSS vulnerability in email template
   - Fixed by WORKER session #2
   - Final review: PASSED

✅ Password reset flow  
   - Implemented secure token generation
   - REVIEWER suggested 15-min expiry (implemented)
   - Added rate limiting after REVIEWER feedback
   
✅ Admin user management
   - Full CRUD with role-based permissions
   - REVIEWER approved security model
   
✅ Test coverage: 94%
   - All critical paths covered
   - Integration tests passing
   
⚠️ API documentation 
   - 80% complete
   - REVIEWER noted missing error code docs
   
📊 Session statistics:
- 12 WORKER sessions launched
- 8 REVIEWER sessions launched  
- 4 fix cycles completed
- 0 critical issues remaining"
```

---

# BEST PRACTICES

## Keep It Simple
1. **Always start with SUPERVISOR** - Get the plan right
2. **Let WORKER focus** - Don't interrupt mid-implementation
3. **REVIEWER after each feature** - Not every line of code
4. **Document decisions** - Especially in AWAY mode

## Task Sizing
- **Small task** (< 30 min): One cycle through all agents
- **Medium task** (1-2 hours): Multiple cycles, SUPERVISOR checkpoints
- **Large task** (2+ hours): SUPERVISOR breaks down, track progress

## Quality Checks
```markdown
Before marking complete, REVIEWER verifies:
✓ Code works as intended
✓ Tests pass
✓ No security issues
✓ Performance acceptable
✓ Documentation updated
```

---

# QUICK START TEMPLATE

```markdown
You: "Build a blog API with 3-agent system"

[SUPERVISOR]: "I'll design a blog API with posts, comments, and users.
Key decisions:
- REST API with JSON
- PostgreSQL database
- JWT authentication
- OpenAPI documentation

Breaking into tasks:
1. Database models (User, Post, Comment)
2. Authentication endpoints
3. Post CRUD endpoints
4. Comment endpoints
5. Tests and docs

Should I proceed with this plan?"

You: "Yes, human mode"

[WORKER]: "Starting with database models..."
```

---

# SUPERVISOR DECISION TRACKING

```markdown
# SUPERVISOR maintains all decisions internally:

SUPERVISOR: "Key decisions made during implementation:

1. Authentication: JWT with refresh tokens
   - Decided after considering session-based alternative
   - WORKER implemented, REVIEWER approved
   
2. Rate limiting: 5 attempts per 15 minutes  
   - Added after REVIEWER security feedback
   - WORKER implemented Redis-based solution
   
3. Password complexity: NIST 800-63B guidelines
   - No arbitrary character requirements
   - Minimum 12 characters
   - Check against common passwords
   
All decisions tracked in my context for consistency."
```

---

# TROUBLESHOOTING

## Common Issues

**WORKER deviating from requirements**
```bash
# Problem: WORKER interpreting task differently than intended
# Solution: SUPERVISOR provides more specific instructions
SUPERVISOR: "I need to be clearer. Relaunching WORKER with detailed specs:
- Exact function signatures
- Specific library requirements  
- Example input/output"
```

**REVIEWER missing important issues**
```bash
# Problem: REVIEWER not catching all problems
# Solution: SUPERVISOR provides focused review criteria
SUPERVISOR: "Launching REVIEWER with specific focus areas:
- Security: Check for SQL injection, XSS
- Performance: Look for N+1 queries
- Error handling: Verify all edge cases covered"
```

**Communication overhead**
```bash
# Problem: Too much back-and-forth through SUPERVISOR
# Solution: SUPERVISOR batches related tasks
SUPERVISOR: "I'll have WORKER implement all models first,
then REVIEWER can review them as a batch,
reducing communication cycles"
```

**SUPERVISOR losing track of progress**
```bash
# Problem: Complex projects with many moving parts
# Solution: SUPERVISOR maintains internal progress tracking
SUPERVISOR: "Current status:
- Auth module: 3/5 tasks complete
- Payment module: 1/4 tasks complete  
- Pending reviews: 2
- Blocked items: 0"
```

---

# SUMMARY

This **SUPERVISOR-coordinated multi-agent system** gives you:
- **Central coordination** - SUPERVISOR has full visibility and control
- **Context isolation** - WORKER and REVIEWER maintain fresh perspectives
- **No file juggling** - All communication flows through SUPERVISOR  
- **Intelligent orchestration** - SUPERVISOR decides when and how to engage agents
- **Quality assurance** - Multiple perspectives without communication overhead
- **True autonomy** - SUPERVISOR can manage entire projects independently

## Key Advantages of Centralized Coordination:
1. **SUPERVISOR** maintains context and makes intelligent decisions about task flow
2. **WORKER** focuses purely on implementation without distraction
3. **REVIEWER** provides unbiased quality checks without implementation knowledge
4. **No file management** - SUPERVISOR handles all information flow
5. **Adaptive workflow** - SUPERVISOR adjusts approach based on results

## Ready to Start?
```bash
# Single command to begin - SUPERVISOR handles everything else
claude --session=supervisor "Build [your project] using 3-agent system where I coordinate all communication"

# SUPERVISOR will:
- Plan the implementation approach
- Launch WORKER sessions as needed
- Coordinate REVIEWER feedback
- Manage fixes and iterations
- Report progress back to you
```

This **SUPERVISOR-coordinated system**:
- ✅ Central coordination with full visibility
- ✅ True agent independence (fresh contexts)
- ✅ No file-based communication needed
- ✅ Intelligent task orchestration
- ✅ Seamless overnight autonomous work
- ✅ Leverages your Max 20x plan efficiently
- ✅ Reduces complexity while maintaining quality
- ✅ SUPERVISOR as single source of truth
