```markdown
# True Multi-Agent Development System

## System Overview
- **Your Plan**: Max 20x ($200/month) - 200-800 Claude Code prompts per 5 hours
- **Three Independent Agents**: SUPERVISOR, WORKER, REVIEWER (**SEPARATE Claude sessions - NO shared context**)
- **Operating Modes**: HUMAN (interactive) or AWAY (autonomous)
- **Model Access**: Opus 4 and Sonnet 4 (switch with `/model`)

## **CRITICAL: Full Context Isolation**
- **SUPERVISOR**: Fresh session, reads project files only, no conversation history
- **WORKER**: Fresh session, reads task specs only, no planning context
- **REVIEWER**: Fresh session, reads requirements + code only, no implementation context
- **Communication**: 100% file-based - all agents are context-free and independent

---

# THE THREE AGENTS

## SUPERVISOR 👔
**Role**: Plans work and makes decisions
**When Active**: Start of each task, when stuck, at major milestones
**Context**: NONE - reads only project files (requirements, progress, decisions)
**Key Actions**:
- Reads project requirements and existing progress from files
- Breaks down remaining work into clear tasks
- Makes architectural decisions based on current state
- Documents all decisions and reasoning in files
- **Creates comprehensive specs that standalone agents can follow**

## WORKER 🔨
**Role**: Implements code
**When Active**: During all coding activities  
**Context**: NONE - reads only PLAN.md and task specifications
**Key Actions**:
- Reads task requirements from files
- Implements code with no planning bias
- Creates tests based on specifications
- Saves work to files for review
- **Never sees SUPERVISOR's reasoning or REVIEWER's feedback directly**

## REVIEWER 🔍
**Role**: Ensures quality
**When Active**: After each significant piece of work
**Context**: NONE - reads only requirements + implemented code
**Key Actions**:
- Reviews code against original requirements
- Finds bugs and edge cases with fresh perspective
- Checks security without implementation bias
- Writes specific feedback to files
- **Never sees WORKER's thought process or SUPERVISOR's internal decisions**

---

# TRUE MULTI-AGENT WORKFLOW

## File-Based Communication Protocol
```bash
PROJECT/
├── PLAN.md              # SUPERVISOR → WORKER communication
├── TASKS/
│   ├── task_1_spec.md   # Detailed requirements
│   ├── task_1_code.py   # WORKER output
│   ├── task_1_tests.py  # WORKER output
│   └── task_1_review.md # REVIEWER feedback
├── DECISIONS.md         # SUPERVISOR architectural decisions
└── PROGRESS.md          # Cross-session status tracking
```

## Starting a New Feature (Fully Context-Isolated Sessions)
```bash
# Step 0: Create initial requirements file
cat > PROJECT_REQUIREMENTS.md << EOF
Build a user authentication system with:
- User registration and login
- JWT tokens with refresh
- Password reset flow
- Email verification
- Rate limiting
EOF

# Session 1: SUPERVISOR (fresh context, reads requirements only)
claude --session=fresh
> SUPERVISOR: Reads PROJECT_REQUIREMENTS.md only
> Creates PLAN.md with detailed tasks based on requirements
> Writes task_1_spec.md, task_2_spec.md, etc.
> Session ends

# Session 2: WORKER (fresh context, reads task specs only)
claude --session=fresh
> WORKER: Reads task_1_spec.md only
> Implements user model with no knowledge of broader project
> Saves code to task_1_code.py and task_1_tests.py
> Session ends

# Session 3: REVIEWER (fresh context, reads requirements + code only)
claude --session=fresh  
> REVIEWER: Reads PROJECT_REQUIREMENTS.md and task_1_code.py only
> Reviews with completely fresh perspective
> Writes issues to task_1_review.md
> Session ends

# Session 4: WORKER (fresh context, reads issues + original spec only)
claude --session=fresh
> WORKER: Reads task_1_spec.md and task_1_review.md only
> Fixes issues with no memory of original implementation
> Updates code files
> Session ends
```

## Example Multi-Session Flow
```markdown
# Step 0: Requirements File Created
PROJECT_REQUIREMENTS.md contains: "Build user authentication with JWT, email verification"

# SUPERVISOR Session (No Context - Reads Requirements Only)
claude --session=fresh "Read PROJECT_REQUIREMENTS.md, create implementation plan"

SUPERVISOR Session Output → PLAN.md:
```
## Authentication System Plan
### Task 1: User Model
- File: models/user.py
- Requirements: email, password_hash, created_at, email_verified
- Constraints: unique email, password complexity validation
- Tests: test_user_model.py
- Success criteria: All tests pass, coverage >90%
- Dependencies: None
- Estimated time: 2 hours
```

# WORKER Session (No Context - Reads Task Spec Only)
claude --session=fresh "Read task_1_spec.md, implement user model"
WORKER implements models/user.py with:
- No knowledge of broader project goals
- No awareness of SUPERVISOR's reasoning
- Pure focus on meeting task specifications

# REVIEWER Session (No Context - Reads Requirements + Code Only)
claude --session=fresh "Read PROJECT_REQUIREMENTS.md and models/user.py, review implementation"
REVIEWER writes REVIEW.md:
```
## Issues Found:
- Missing email validation regex
- Password hash not using bcrypt
- No rate limiting consideration
- Tests don't cover edge cases
```

# WORKER Fix Session (No Context - Reads Task + Issues Only) 
claude --session=fresh "Read task_1_spec.md and task_1_review.md, fix issues"
WORKER fixes code with:
- No memory of original implementation approach
- Fresh perspective on solving the specific issues
- No bias from previous implementation attempts
```

---

# OPERATING MODES

## HUMAN MODE (You're Available)
```bash
# Step 1: Create requirements with your input
cat > PROJECT_REQUIREMENTS.md << EOF
Build auth system with:
- JWT tokens (refresh tokens: 7 day expiry)
- Email verification required
- Password complexity: min 8 chars, numbers, symbols
EOF

# Step 2: SUPERVISOR Session (Fresh context, reads requirements)
claude --session=fresh "Read PROJECT_REQUIREMENTS.md, create detailed implementation plan"
# SUPERVISOR writes PLAN.md, task specs, etc. - Session ends

# Step 3: WORKER Sessions (All autonomous, context-free)
claude --session=fresh "Implement task 1 from task_1_spec.md"
claude --session=fresh "Implement task 2 from task_2_spec.md"

# Step 4: REVIEWER Session (Fresh context, autonomous)  
claude --session=fresh "Review all auth code against PROJECT_REQUIREMENTS.md"

# Step 5: Check progress with fresh SUPERVISOR
claude --session=fresh "Read all progress files, summarize status and next steps"
```

## AWAY MODE (Fully Autonomous)
```bash
# Before leaving: Create comprehensive requirements
cat > PROJECT_REQUIREMENTS.md << EOF
Complete auth system with standard enterprise patterns:
- JWT with refresh tokens (7 day expiry)
- Bcrypt for passwords (min 12 rounds)
- Email verification required
- Rate limiting: 5 attempts per 15 min
- Admin user management
- Full test coverage (>90%)
- API documentation
EOF

# SUPERVISOR Session (Fresh context, reads requirements only)
claude --session=fresh "Read PROJECT_REQUIREMENTS.md, create comprehensive implementation plan"
# Outputs: PLAN.md, task_1_spec.md through task_8_spec.md, DECISIONS.md
# Session ends

# Autonomous execution (all context-free, can run in parallel)
claude --session=fresh "Implement task 1 from task_1_spec.md" &
claude --session=fresh "Implement task 2 from task_2_spec.md" &
claude --session=fresh "Implement task 3 from task_3_spec.md" &

# Reviews (fresh context, parallel)
claude --session=fresh "Review task 1 against PROJECT_REQUIREMENTS.md" &
claude --session=fresh "Review task 2 against PROJECT_REQUIREMENTS.md" &

# Fixes (fresh context, no memory of original implementation)
claude --session=fresh "Fix task 1 issues from task_1_review.md" &
claude --session=fresh "Fix task 2 issues from task_2_review.md" &

# When you return: Fresh supervisor assessment
claude --session=fresh "Read all project files, summarize completed work and remaining tasks"
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

# COMMANDS FOR CONTEXT-ISOLATED AGENTS

## Starting Work
```bash
# SUPERVISOR Session (Full Context)
"Plan [feature] using 3-agent system, write detailed specs for context-free workers"
"HUMAN mode - I'll answer questions, write comprehensive PLAN.md"
"AWAY mode - make standard decisions, document everything for workers"

# WORKER Sessions (No Context)
claude --session=fresh "Read PLAN.md, implement task [N]"
claude --session=fresh "Read task_[N]_review.md, fix issues"

# REVIEWER Sessions (No Context)
claude --session=fresh "Review task [N] code against original requirements"
```

## Session Management
```bash
# ALL agents run in fresh sessions - complete context isolation
SUPERVISOR="claude --session=fresh"        # Fresh every time
WORKER="claude --session=fresh"            # Fresh every time  
REVIEWER="claude --session=fresh"          # Fresh every time

# Example workflow - all agents are context-free
$SUPERVISOR "Read PROJECT_REQUIREMENTS.md, create plan"     # Reads requirements only
$WORKER "Read task_1_spec.md, implement"                   # Reads task spec only
$REVIEWER "Read requirements + code, review"               # Reads requirements + code only
$WORKER "Read task_1_review.md + spec, fix issues"         # Reads review + spec only
```

## File-Based Commands
```bash
# Instead of "switching agents" in conversation:
echo "Fix login endpoint performance" > URGENT_TASK.md
claude --session=fresh "Address issue in URGENT_TASK.md"

# Chain work through files
claude --session=fresh "Read TODO.md, complete next task, update PROGRESS.md"
claude --session=fresh "Review PROGRESS.md, check latest completed work"
```

---

# OVERNIGHT AUTONOMOUS MODE (Actually Feasible)

## Pre-Sleep Setup
```bash
# SUPERVISOR Session: Create comprehensive plan
cat > TONIGHT_REQUIREMENTS.md << EOF
Complete these auth system components:
1. Email verification system
2. Password reset flow  
3. Admin user management
4. Full test coverage (90%+)
5. API documentation

Use secure, industry-standard patterns.
EOF

claude --session=fresh "Read TONIGHT_REQUIREMENTS.md, create detailed implementation plan"
# SUPERVISOR outputs: PLAN.md, task_1_spec.md, task_2_spec.md, etc.
```

## Overnight Execution (Parallel Independent Sessions)
```bash
#!/bin/bash
# overnight_work.sh

# Phase 1: Implementation (parallel workers)
claude --session=worker1 "Implement task 1 from PLAN.md" > logs/worker1.log &
claude --session=worker2 "Implement task 2 from PLAN.md" > logs/worker2.log &
claude --session=worker3 "Implement task 3 from PLAN.md" > logs/worker3.log &

wait # Wait for all workers to complete

# Phase 2: Review (parallel reviewers)  
claude --session=reviewer1 "Review task 1 against spec" > logs/review1.log &
claude --session=reviewer2 "Review task 2 against spec" > logs/review2.log &
claude --session=reviewer3 "Review task 3 against spec" > logs/review3.log &

wait # Wait for all reviews

# Phase 3: Fixes (parallel fix sessions)
claude --session=fixer1 "Fix task 1 issues from review" > logs/fix1.log &
claude --session=fixer2 "Fix task 2 issues from review" > logs/fix2.log &
claude --session=fixer3 "Fix task 3 issues from review" > logs/fix3.log &

wait # Wait for all fixes

# Phase 4: Final integration test
claude --session=integrator "Run full test suite and document results" > logs/integration.log
```

## Morning Review
```bash
# Fresh SUPERVISOR Session: Assess overnight work
claude --session=fresh "Read all project files, summarize overnight progress"

SUPERVISOR (fresh context) reads:
- TONIGHT_REQUIREMENTS.md (original goals)
- All task files: task_1_code.py, task_1_tests.py, task_1_review.md
- All progress files: task_2_code.py, task_2_tests.py, task_2_review.md
- integration_results.md

SUPERVISOR (with no memory of planning decisions): "Overnight Assessment:
✅ Email verification system (task_1_code.py) - meets requirements
✅ Password reset with secure tokens (task_2_code.py) - properly implemented
✅ Admin user CRUD operations (task_3_code.py) - complete with tests
✅ 92% test coverage achieved - exceeds 90% target
⚠️ API docs partially complete (see task_5_review.md for specific gaps)
📄 All implementation follows documented specs

Remaining work: Complete API documentation sections highlighted in reviews."
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

# SIMPLE DECISION LOG

```markdown
# DECISIONS.md

## 2024-01-26: Authentication System
Agent: SUPERVISOR
Decision: Use JWT with refresh tokens
Reason: Stateless, scalable, industry standard
Alternative: Session-based (requires Redis)

Agent: REVIEWER  
Decision: Add rate limiting to login
Reason: Prevent brute force attacks
Implementation: 5 attempts per 15 minutes
```

---

# TROUBLESHOOTING

## Common Issues

**WORKER deviating from plan**
```bash
# Problem: Worker interpreting requirements differently
# Solution: More detailed task specifications
SUPERVISOR session: "Write more specific implementation details in task_N_spec.md"
```

**REVIEWER being too lenient/harsh**
```bash
# Problem: Inconsistent review standards
# Solution: Standardized review criteria  
SUPERVISOR session: "Create REVIEW_STANDARDS.md with specific criteria"
```

**Lost context between sessions**
```bash
# Problem: Important decisions not captured in files
# Solution: Better documentation
SUPERVISOR session: "Document all architectural decisions in DECISIONS.md"
```

**Workers not finding files**
```bash
# Problem: File organization unclear
# Solution: Standard file structure
mkdir -p {tasks,reviews,code,tests,docs}
echo "File locations:" > FILE_STRUCTURE.md
```

**Sessions not truly independent**
```bash
# Problem: Accidentally reusing sessions
# Solution: Always use --session=fresh for WORKER/REVIEWER
alias worker="claude --session=fresh"
alias reviewer="claude --session=fresh"
```

---

# SUMMARY

This **true multi-agent system** gives you:
- **Genuine context isolation** - No shared bias between agents
- **Independent perspectives** - WORKER and REVIEWER see problems differently  
- **Parallel execution** - Multiple sessions can run simultaneously
- **True overnight work** - File-based coordination enables autonomous operation
- **Quality built-in** - Fresh REVIEWER eyes catch what WORKER missed
- **Scalability** - Add more WORKER/REVIEWER sessions as needed

## Key Advantages of Full Context Isolation:
1. **SUPERVISOR** plans based purely on requirements - no conversation bias
2. **WORKER** implements without planning bias - often finds better solutions  
3. **REVIEWER** reviews without implementation bias - catches real issues
4. **All agents** approach problems with completely fresh perspective
5. **Parallel work** - Multiple truly independent sessions can run simultaneously
6. **True autonomy** - Genuine overnight work through pure file coordination
7. **No memory contamination** - Each agent sees only what they need to see

## Ready to Start?
```bash
# Step 1: Create requirements file
echo "Build [describe your project requirements]" > PROJECT_REQUIREMENTS.md

# Step 2: Fresh SUPERVISOR planning session
claude --session=fresh "Read PROJECT_REQUIREMENTS.md, create comprehensive implementation plan"

# Step 3: Launch completely independent agents
claude --session=fresh "Read task_1_spec.md, implement task 1"
claude --session=fresh "Read PROJECT_REQUIREMENTS.md + task_1_code.py, review implementation"
claude --session=fresh "Read task_1_review.md + task_1_spec.md, fix issues"
```

This **genuine multi-agent system**:
- ✅ True agent independence (no shared context)
- ✅ File-based coordination protocol
- ✅ Parallel execution capability  
- ✅ Real overnight autonomous work
- ✅ Fresh perspectives from each agent
- ✅ Leverages your Max 20x plan efficiently
- ✅ Actually implementable with current Claude Code capabilities
- ✅ Not roleplaying - genuine multi-agent architecture
