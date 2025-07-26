# Adaptive Multi-Agent Development System with Headless Automation (Max 20x Edition)

## System Overview
- **Max 20x Plan**: $200/month with 200-800 Claude Code prompts/5 hours
- **Model Access**: Sonnet 4 and Opus 4 (switch with `/model`)
- **Core Approach**: Liberal virtual agent usage with headless automation
- **Power User Features**: Multi-terminal orchestration, parallel execution, extended automation

## Initial Mode Selection
```
Claude: "Hi! What mode are you in?
1. HUMAN MODE - I'm actively available for rapid development
2. AWAY MODE - Work autonomously with comprehensive implementation
3. HEADLESS MODE - Launch extended automation (7+ hours)
4. POWER MODE - Maximum parallelization with multiple terminals"

Note: You have Max 20x with 200-800 prompts per 5 hours. Use liberally!
```

---

# UNDERSTANDING YOUR MAX 20x PLAN

## Usage Limits and Optimization

### Your Capacity
- **200-800 Claude Code prompts per 5 hours** (resets every 5 hours)
- **Average: ~500 prompts per 5 hours** = 100 prompts/hour
- **Daily capacity**: ~2,400 prompts (with perfect timing)
- **Model switching**: `/model opus` for complex work, `/model sonnet` for routine tasks

### Liberal Usage Strategy
With 200-800 prompts per 5-hour window, you can:
- Run multiple virtual agents freely
- Use frequent checkpoints and iterations
- Launch parallel headless sessions
- Maintain multiple terminal sessions when beneficial
- Switch models based on task complexity

### Model Selection Strategy
```markdown
/model opus    # Use for: Architecture, complex algorithms, security reviews
/model sonnet  # Use for: CRUD operations, documentation, routine tasks

# Automatic switching in workflows
[ARCHITECT]: /model opus
"Designing distributed payment system architecture..."

[DEVELOPER]: /model sonnet
"Implementing standard CRUD endpoints..."
```

---

# OPERATING MODES (Max 20x Optimized)

## HUMAN MODE (Rapid Interactive Development)
**Goal**: Maximum development velocity with your input
**Call Usage**: Very liberal (100-200 prompts/hour acceptable)
**Strategy**: Frequent iterations, multiple agents, rapid model switching

### Power User Workflow
```markdown
[INTERACTIVE-ARCHITECT]: /model opus
"Building distributed microservices. I'll ask targeted questions for optimal architecture..."

[You]: "Use event-driven with Kafka"

[RAPID-DEVELOPER]: "Creating service scaffolding..."
[TEST-ENGINEER]: "Writing tests in parallel..."
[API-DESIGNER]: "Documenting interfaces..."
*All working on different aspects simultaneously*

[CHECKPOINT-REVIEWER]: "10-minute checkpoint:
✅ 3 services scaffolded
✅ Event schemas defined
✅ 40% test coverage
Continue with current approach?"
```

### Ultra-Fast Iteration Pattern
```markdown
# With 100+ prompts/hour available:
Write code (2 min) → Test (1 min) → Review (1 min) → Refactor (2 min)
= 6-minute cycles with 4 agent switches
= 10 complete iterations per hour
```

## AWAY MODE (Comprehensive Autonomous Development)
**Goal**: Maximum autonomous progress
**Call Usage**: Moderate (50-100 prompts per session)
**Strategy**: Comprehensive implementations with all edge cases

### Max 20x Away Mode Benefits
- Can afford multiple specialist reviews
- Extensive testing iterations
- Comprehensive documentation generation
- Multiple refactoring passes

```markdown
[AUTONOMOUS-ARCHITECT]: /model opus
"Analyzing requirements and designing complete system..."

[BATCH-DEVELOPER]: /model sonnet
"Implementing all components with:
- Primary implementation
- Error handling pass
- Performance optimization pass
- Security hardening pass
- Documentation pass"

[SPECIALIST-TEAM]: "Running all specialists:
- SECURITY-AUDITOR (Opus mode)
- PERFORMANCE-ANALYST
- TEST-ENGINEER
- DOC-WRITER"
```

## HEADLESS MODE (Extended Power User Automation)
**Goal**: Maximize 7+ hour autonomous execution
**Strategy**: Parallel specialist execution, comprehensive coverage
**Unique Advantage**: Can run multiple headless sessions without concern

### Parallel Headless Orchestra
```bash
#!/bin/bash
# max-20x-overnight.sh

# Main development (Opus for complex logic)
claude -p "As BATCH-DEVELOPER using Opus: Implement complete payment system per CLAUDE.md" \
  --allowedTools "all" &

# Parallel testing (Sonnet is fine for tests)
claude -p "As TEST-ENGINEER using Sonnet: Write comprehensive test suite achieving 95% coverage" \
  --allowedTools "all" &

# Security audit (Opus for thorough analysis)
claude -p "As SECURITY-AUDITOR using Opus: Deep security analysis with threat modeling" \
  --allowedTools "read,analyze" &

# Performance profiling
claude -p "As PERFORMANCE-ANALYST: Profile and optimize all critical paths" \
  --allowedTools "all" &

# Documentation (Sonnet for standard docs)
claude -p "As DOC-WRITER using Sonnet: Generate complete documentation suite" \
  --allowedTools "read,write" &

wait
echo "Parallel overnight development complete"
```

## POWER MODE (Maximum Parallelization)
**New for Max 20x**: Leverage your high prompt limit for true parallel development
**Strategy**: Multiple terminals running specialized agent teams
**Use When**: Large projects, tight deadlines, complex systems

### Power Mode Configuration
```bash
# Terminal 1: Backend Team (opus-heavy)
/model opus
Virtual Agents: ARCHITECT, DEVELOPER, DB-SPECIALIST, API-DESIGNER

# Terminal 2: Frontend Team (sonnet-heavy)
/model sonnet
Virtual Agents: UI-DEVELOPER, FRONTEND-SPECIALIST, UX-DESIGNER

# Terminal 3: Infrastructure Team (mixed)
Virtual Agents: DEVOPS, SECURITY-AUDITOR, PERFORMANCE-ANALYST

# Terminal 4: Quality Team (opus for thorough review)
/model opus
Virtual Agents: TEST-ENGINEER, REVIEWER, DOC-WRITER
```

---

# VIRTUAL AGENT STRATEGIES FOR MAX 20x

## Liberal Agent Switching
With your prompt capacity, optimize for quality over conservation:

```markdown
# Old approach (conserving calls)
[DEVELOPER]: Write feature + tests + docs (30 min)

# Max 20x approach (optimize quality)
[DEVELOPER]: Write feature (10 min)
[TEST-ENGINEER]: Write tests (5 min)
[REVIEWER]: Initial review (3 min)
[DEVELOPER]: Address feedback (5 min)
[SECURITY-AUDITOR]: Security check (3 min)
[PERFORMANCE-ANALYST]: Performance check (3 min)
[DOC-WRITER]: Document (5 min)
[REVIEWER]: Final review (2 min)
= Better quality through specialization
```

## Model-Optimized Agents

### Opus-Preferred Agents
```markdown
/model opus
- ARCHITECT: Complex system design
- SECURITY-AUDITOR: Threat analysis
- ALGORITHM-DESIGNER: Complex algorithms
- REVIEWER: Catching subtle bugs
```

### Sonnet-Suitable Agents
```markdown
/model sonnet
- DEVELOPER: Standard implementation
- TEST-ENGINEER: Writing tests
- DOC-WRITER: Documentation
- REFACTORER: Code cleanup
```

## Parallel Virtual Agent Patterns

### The Swarm Pattern
```markdown
# Launch multiple specialists simultaneously
[SECURITY-AUDITOR]: "Analyzing auth flow..."
[PERFORMANCE-ANALYST]: "Profiling database queries..."
[API-DESIGNER]: "Reviewing REST conventions..."
[TEST-ENGINEER]: "Checking coverage gaps..."

[SUPERVISOR]: "Integrating all specialist feedback..."
```

### The Pipeline Pattern
```markdown
# Continuous flow with no waiting
[ARCHITECT] → [DEVELOPER] → [TEST-ENGINEER] → [REVIEWER]
     ↓              ↓               ↓              ↓
  Plan next    Start next      Test next    Review all
```

---

# TASK COMPLEXITY WITH MAX 20x

## Revised Complexity Levels

### Level 0-1: Batch Processing
With your capacity, batch simple tasks:
```markdown
[BATCH-DEVELOPER]: "Implementing all 10 CRUD endpoints in one session"
[BATCH-TESTER]: "Writing tests for all endpoints"
[BATCH-DOCUMENTER]: "Documenting all APIs"
```

### Level 2-3: Parallel Specialists
Run specialists in parallel, not sequential:
```markdown
# All at once, not one by one
[DEVELOPER]: Implementation
[SECURITY-AUDITOR]: Real-time security review
[TEST-ENGINEER]: Test-as-you-code
[DOC-WRITER]: Live documentation
```

### Level 4: Full Orchestra
```markdown
# Terminal 1
[SUPERVISOR]: Orchestrating 3 teams
[ARCHITECT]: Designing next phase

# Terminal 2-4
[TEAM-BACKEND]: 5 virtual agents
[TEAM-FRONTEND]: 5 virtual agents
[TEAM-INFRA]: 5 virtual agents
```

---

# EXECUTION PATTERNS FOR POWER USERS

## Continuous Development Pipeline

### Morning Sprint (2-3 hours)
```markdown
/model opus
[ARCHITECT]: "Today's battle plan..." (15 min)

# Parallel execution
[DEVELOPER-1]: Backend features
[DEVELOPER-2]: Frontend features
[DEVELOPER-3]: Infrastructure
[TEST-ENGINEER]: Following behind all devs
[REVIEWER]: Continuous review cycle

# 50-75 prompts/hour - well within limits
```

### Afternoon Optimization (2 hours)
```markdown
# Switch specialists rapidly
[PERFORMANCE-ANALYST]: "Found 3 slow queries" (10 min)
[DEVELOPER]: "Optimizing..." (15 min)
[TEST-ENGINEER]: "Verify performance" (5 min)

[SECURITY-AUDITOR]: "Found XSS vulnerability" (10 min)
[DEVELOPER]: "Patching..." (10 min)
[TEST-ENGINEER]: "Security regression tests" (10 min)

# Rapid 5-10 minute specialist cycles
```

### Evening Automation Setup (30 min)
```markdown
/model opus
[ARCHITECT]: "Planning overnight work..."

Update CLAUDE.md with:
- 20-30 tasks for overnight
- Specific model preferences
- Quality targets
- Integration points

Launch 3-5 parallel headless sessions
```

---

# RATE LIMIT MANAGEMENT FOR MAX 20x

## Usage Tracking Dashboard
```bash
#!/bin/bash
# max20x-usage.sh

USAGE_FILE=".claude-usage.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M')
WINDOW_START=$(date -d '5 hours ago' '+%Y-%m-%d %H:%M')

# Log current usage
echo "$TIMESTAMP: $1 prompts - $2" >> $USAGE_FILE

# Calculate 5-hour window
WINDOW_USAGE=$(awk -v start="$WINDOW_START" '$1" "$2 >= start {sum += $3} END {print sum}' $USAGE_FILE)

# Visual indicator
if [ $WINDOW_USAGE -lt 200 ]; then
    STATUS="🟢 AGGRESSIVE MODE"
elif [ $WINDOW_USAGE -lt 500 ]; then
    STATUS="🟡 NORMAL USAGE"
elif [ $WINDOW_USAGE -lt 700 ]; then
    STATUS="🟠 MONITOR USAGE"
else
    STATUS="🔴 APPROACHING LIMIT"
fi

echo "5-hour usage: $WINDOW_USAGE/800 prompts $STATUS"

# Model recommendation
if [ $WINDOW_USAGE -gt 600 ]; then
    echo "💡 Consider switching to Sonnet for routine tasks"
fi
```

## Strategic Usage Patterns

### First Half of 5-Hour Window (0-2.5 hours)
- Use Opus liberally
- Run parallel operations
- Multiple virtual agents
- Aggressive iteration
- Target: 400-500 prompts

### Second Half of 5-Hour Window (2.5-5 hours)
- Switch to Sonnet for routine work
- Focus on single-session efficiency
- Complete documentation and tests
- Prepare for next window
- Target: 200-300 prompts

---

# OPTIMAL CONFIGURATIONS

## Development Environment Setup
```bash
# .claude-config.json
{
  "max_20x_mode": true,
  "default_model": "opus",
  "fallback_model": "sonnet",
  "parallel_sessions": 4,
  "usage_tracking": true,
  "automation": {
    "headless_duration": "7h",
    "parallel_specialists": true,
    "comprehensive_tests": true,
    "security_depth": "maximum"
  }
}
```

## Project Structure for Large Codebases
```
project/
├── .claude/
│   ├── CLAUDE.md           # Main context (up to 10k lines)
│   ├── agents/             # Agent-specific instructions
│   │   ├── architect.md
│   │   ├── security.md
│   │   └── performance.md
│   ├── decisions/          # Timestamped decision logs
│   └── usage/              # Usage tracking
├── src/                    # Your large codebase
└── tests/                  # Comprehensive test suite
```

---

# QUICK REFERENCE FOR MAX 20x

## Commands
```markdown
/model opus      # Complex work (uses more tokens)
/model sonnet    # Routine work (token efficient)

# In headless mode
--model opus     # Force Opus model
--model sonnet   # Force Sonnet model
```

## Usage Guidelines
```markdown
0-200 prompts used → AGGRESSIVE: Opus everything, parallel all
200-500 prompts → NORMAL: Mix models, steady pace
500-700 prompts → CAREFUL: Prefer Sonnet, single sessions
700-800 prompts → CONSERVE: Essential work only, wait for reset
```

## Power Patterns
```markdown
Morning: Architecture + Parallel Development (Opus-heavy)
Midday: Implementation + Testing (Mixed models)
Afternoon: Reviews + Optimization (Specialist rotation)
Evening: Setup overnight automation (Strategic planning)
Night: 7+ hour headless execution (Automated)
```

## Best Practices for Max 20x
1. **Use Opus for high-value work** (architecture, security, algorithms)
2. **Use Sonnet for volume work** (CRUD, tests, documentation)
3. **Run specialists in parallel**, not sequential
4. **Launch multiple headless sessions** overnight
5. **Track usage per 5-hour window**, not daily
6. **Switch models strategically** based on task and usage
7. **Leverage full prompt capacity** - you're paying for it!

---

# GETTING STARTED WITH MAX 20x

1. **Set Default Model**:
   ```
   /model opus
   "I have Max 20x - let's build aggressively"
   ```

2. **Create Power User Structure**:
   ```bash
   mkdir -p .claude/{agents,decisions,usage}
   echo "MAX_20X=true" > .env
   ```

3. **Launch Power Mode**:
   ```
   "Power mode - building distributed system with 3 microservices"
   [ARCHITECT]: "Excellent! With Max 20x, we'll run parallel development teams..."
   ```

Remember: You have 200-800 prompts per 5 hours. Most users average 500. That's 100 prompts/hour. Use them to build faster and better!
```

This Max 20x edition emphasizes:
- ✅ Liberal usage patterns appropriate for 200-800 prompts/5 hours
- ✅ Strategic model switching between Opus and Sonnet
- ✅ Power user patterns with parallel execution
- ✅ 5-hour window tracking (not daily)
- ✅ Aggressive parallelization strategies
- ✅ Large codebase optimizations
- ✅ Multi-session headless automation
- ✅ Power Mode for maximum parallelization

The system now fully leverages your Max 20x investment for maximum development velocity!
