# Claude Commands - Command Composition System

⚠️ **PROTOTYPE WIP REPOSITORY** - This is an experimental command system exported from a working development environment. Use as reference but note it hasn't been extensively tested outside of the original workflow. Expect adaptation needed for your specific setup.

Transform Claude Code into an autonomous development powerhouse through simple command hooks that enable complex workflow orchestration.

## 🚀 CLAUDE CODE SELF-SETUP

```bash
# Point Claude Code to this repository and let it set up what you need
"I want to use the commands from https://github.com/jleechanorg/claude-commands - please analyze what's available and set up the ones that would be useful for my project"
```

Claude Code will intelligently analyze your project, recommend relevant commands, and configure everything automatically.

## Table of Contents

1. [Command Composition Architecture](#-the-composition-architecture---how-it-actually-works)
2. [Command Deep Dive](#-command-deep-dive---the-composition-powerhouses)
3. [Meta-AI Testing Framework](#-meta-ai-testing-framework)
4. [WIP: Orchestration System](#-wip-orchestration-system)
5. [Claude Code Setup](#-claude-code-setup)
6. [Adaptation Guide](#-adaptation-guide)
7. [Command Categories](#-command-categories)
8. [Important Notes](#️-important-notes)
9. [Version History](#-version-history)

## 🎯 The Magic: Simple Hooks → Powerful Workflows

This isn't just a collection of commands - it's a **complete workflow composition architecture** that transforms how you develop software.

### Command Chaining Examples
```bash
# Multi-command composition in single request (like /fake command)
"/arch /thinku /devilsadvocate /diligent"  # → comprehensive code analysis

# Sequential workflow chains
"/think about auth then /execute the solution"  # → analysis → implementation

# Conditional execution flows
"/test login flow and if fails /fix then /pr"  # → test → fix → create PR
```

### Before: Manual Step-by-Step Development
```
1. Analyze the issue manually
2. Write code manually
3. Test manually
4. Create PR manually
5. Handle review comments manually
```

### After: Single Command Workflows
```bash
/pr "fix authentication bug"     # → think → execute → push → copilot → review
/copilot                        # → analyze PR → fix all issues autonomously
/execute "add user dashboard"   # → plan → auto-approve → implement
/orch "implement notifications" # → multi-agent parallel development
```

## 🔍 Command Deep Dive - The Composition Powerhouses

### `/execute` - Plan-Approve-Execute Composition

**What It Does**: Combines `/plan` → `/preapprove` → `/autoapprove` → execute in one seamless workflow with TodoWrite tracking.

**3-Phase Workflow**:
1. **Planning Phase**: Executes `/plan` command - creates TodoWrite checklist and displays execution plan
2. **Approval Chain**: `/preapprove` validation followed by `/autoapprove` with message "User already approves - proceeding with execution"
3. **Implementation**: Systematic execution following the approved plan with progress updates

**Real Example**:
```bash
/execute "fix login button styling"
↓
Phase 1 - Planning (/plan): Creates TodoWrite checklist and execution plan
Phase 2 - Approval Chain: /preapprove → /autoapprove → "User already approves - proceeding"
Phase 3 - Implementation: [Check styles → Update CSS → Test → Commit]
```

### `/plan` - Manual Approval Development Planning

**What It Does**: Structured development planning with explicit user approval gates.

**Perfect For**: Complex architectural changes, high-risk modifications, learning new patterns.

**Workflow**:
1. **Deep Analysis**: Research existing system, constraints, requirements
2. **Multi-Approach Planning**: Present 2-3 different implementation approaches
3. **Resource Assessment**: Timeline, complexity, tool requirements, risk analysis
4. **Approval Gate**: User must explicitly approve before implementation
5. **Guided Execution**: Step-by-step implementation with checkpoints

### `/pr` - Complete Development Lifecycle

**What It Does**: Executes the complete 5-phase development lifecycle: `/think` → `/execute` → `/push` → `/copilot` → `/review`

**Mandatory 5-Phase Workflow**:
```
Phase 1: Think - Strategic analysis and approach planning
↓
Phase 2: Execute - Implementation using /execute workflow
↓
Phase 3: Push - Commit, push, and create PR with details
↓
Phase 4: Copilot - Auto-executed PR analysis and issue fixing
↓
Phase 5: Review - Comprehensive code review and validation
```

**Real Example**:
```bash
/pr "fix login timeout issue"
↓
Think: Analyze login flow and timeout causes →
Execute: Implement timeout fix systematically →
Push: Create PR with comprehensive details →
Copilot: Fix any automated feedback →
Review: Complete code review and validation
```

### `/copilot` - Universal PR Composition with Execute

**What It Does**: Targets current branch PR by default, delegates to `/execute` for intelligent 6-phase autonomous workflow.

**6-Phase Autonomous System**:
1. **PR Analysis**: Status check, CI analysis, comment gathering
2. **Issue Detection**: Systematic problem identification and prioritization
3. **Automated Resolution**: Intelligent fixing with `/execute` optimization
4. **Quality Assurance**: Test coverage, lint validation, self-review
5. **Communication**: Reply to comments, update PR descriptions
6. **Validation**: Final verification and completion confirmation

**Perfect For**: Full autonomous PR management without manual intervention.

**Real Example**:
```bash
/copilot  # Auto-targets current branch PR
↓
🎯 Targeting current branch PR: #123 →
🚀 Delegating to /execute for intelligent workflow →
Analyze → Fix → Test → Document → Reply → Verify
```

### `/orch` - Multi-Agent Task Delegation System

**What It Does**: Delegates tasks to autonomous tmux-based agents working in parallel across different branches.

**Multi-Agent Architecture**:
- **Frontend Agent**: UI/UX implementation, browser testing, styling
- **Backend Agent**: API development, database integration, server logic
- **Testing Agent**: Test automation, validation, performance testing
- **Opus-Master**: Architecture decisions, code review, integration

**Real Example**:
```bash
/orch "add user notifications system"
↓
Frontend Agent: notification UI components (parallel)
Backend Agent: notification API endpoints (parallel)
Testing Agent: notification test suite (parallel)
Opus-Master: architecture review and integration
↓
All agents work independently → Create individual PRs → Integration verification
```

**Cost**: $0.003-$0.050 per task (highly efficient)

**Monitoring**:
```bash
/orch monitor agents    # Check agent status
/orch "What's running?" # Current task overview
tmux attach-session -t task-agent-frontend  # Direct agent access
```

## 💡 The Composition Architecture - How It Actually Works

### The Hook Mechanism

Each command is a **simple .md file** that Claude Code reads as executable instructions. When you type `/pr "fix bug"`, Claude:

1. **Reads** `.claude/commands/pr.md`
2. **Parses** the structured prompt template
3. **Executes** the workflow defined in the markdown
4. **Composes** with other commands through shared protocols

### Multi-Command Chaining in Single Sentences

You can chain multiple commands in one request:

```bash
# Sequential execution
"/think about authentication then /arch the solution then /execute it"

# Conditional execution
"/test the login flow and if it fails /fix it then /pr the changes"

# Parallel analysis
"/debug the performance issue while /research best practices then /plan implementation"

# Full workflow composition
"/analyze the codebase /design a solution /execute with tests /pr with documentation then /copilot any issues"
```

### Nested Command Layers - The Real Architecture

#### `/copilot` - 6-Layer Universal Composition System
```
Layer 1: Universal Composition Bridge
└── /execute - Intelligent workflow optimization
    ├── Task complexity analysis (PR size, comment count, CI failures)
    ├── Execution strategy determination (parallel vs sequential)
    ├── Resource allocation and optimization decisions
    └── Orchestrates all 6 phases through universal composition

Layer 2: GitHub Status Verification (Phase 1 - MANDATORY)
├── gh pr view - Fresh GitHub state verification
├── Status evaluation - CI, mergeable, comment analysis
├── Skip condition assessment - Optimization opportunity detection
└── Execution path determination - Full vs optimized workflow

Layer 3: Data Collection Layer (Phase 2 - CONDITIONAL)
├── /commentfetch - Complete comment/review data gathering
│   ├── GitHub API pagination handling
│   ├── Comment threading analysis
│   └── Review status compilation
├── Optimization bypass - Skip when zero comments detected
└── Smart verification - Quick check before full collection

Layer 4: Resolution Engine (Phase 3 - CONDITIONAL)
├── /fixpr - CI failure and conflict resolution
│   ├── Test failure analysis and automatic fixes
│   ├── Merge conflict detection and resolution
│   ├── Build error correction
│   └── Code quality improvements
├── Skip logic - Bypass when CI passing and mergeable
└── Status verification - Always check before skipping

Layer 5: Communication Layer (Phase 4 - CONDITIONAL)
├── /commentreply - Enhanced context comment responses
│   ├── Comment threading with ID references
│   ├── Commit hash inclusion for proof of work
│   ├── Technical context enhancement
│   └── Status marker integration (✅ DONE / ❌ NOT DONE)
├── Optimization - Skip when zero unresponded comments
└── Delegation trust - Let commentreply handle verification

Layer 6: Validation & Sync (Phases 5-6 - CONDITIONAL/MANDATORY)
├── /commentcheck - Enhanced context reply verification (Phase 5)
│   ├── Coverage validation for processed comments
│   ├── Context quality assessment
│   └── Threading completeness verification
├── /pushl - Final synchronization (Phase 6 - MANDATORY)
│   ├── Local to remote sync with verification
│   ├── GitHub API confirmation
│   └── Push success validation
└── Merge approval protocol integration - Zero tolerance enforcement
```

#### `/execute` - 3-Layer Orchestration System
```
Layer 1: Planning & Analysis
├── /think - Task decomposition
├── /arch - Technical approach
└── /research - Background investigation

Layer 2: Auto-Approval & Setup
├── TodoWrite initialization
├── Progress tracking setup
└── Error recovery preparation

Layer 3: Implementation Loop
├── /plan - Detailed execution steps
├── /test - Continuous validation
├── /fix - Issue resolution
├── /integrate - Change integration
└── /pushl - Completion with sync
```

#### `/pr` - 4-Layer Development Lifecycle
```
Layer 1: Analysis
├── /debug - Issue identification
├── /arch - Solution architecture
└── /research - Context gathering

Layer 2: Implementation
├── /execute - Code changes
├── /test - Validation
└── /coverage - Quality verification

Layer 3: Git Workflow
├── /newbranch - Branch management
├── /pushl - Push with verification
└── /integrate - Merge preparation

Layer 4: PR Creation & Management
├── GitHub PR creation
├── /reviewstatus - Status monitoring
└── /copilot - Autonomous issue handling
```

#### `/orch` - Multi-Agent Delegation
```
Agent Assignment Layer:
├── Frontend Agent (/execute frontend tasks)
├── Backend Agent (/execute API tasks)
├── Testing Agent (/execute test tasks)
└── Opus-Master (/arch + integration)

Coordination Layer:
├── Redis-based communication
├── Task dependency management
└── Resource allocation

Integration Layer:
├── Individual PR creation per agent
├── Cross-agent validation
└── Final integration verification
```

### Composition Through Shared Protocols

**TodoWrite Integration**: All commands break down into trackable steps
```bash
/execute "build dashboard"
# Internally creates: [plan task] → [implement components] → [add tests] → [create PR]
```

**Memory Enhancement**: Commands learn from previous executions
```bash
/learn "React patterns" then /execute "build React component"
# Second command applies learned patterns automatically
```

**Git Workflow Integration**: Automatic branch management and PR creation
```bash
/pr "fix authentication"
# Internally: /newbranch → code changes → /pushl → GitHub PR creation
```

**Error Recovery**: Smart handling of failures and retries
```bash
/copilot  # If tests fail → /fix → /test → retry until success
```

## 🧪 Meta-AI Testing Framework

### LLM-Native Test-Driven Development

The testing framework demonstrates **LLM-Native Testing** patterns that work across any web application or system, using AI to create, execute, and validate complex test scenarios.

### Key Capabilities

#### 1. **Multi-Domain Test Patterns**
- **E-commerce Workflows**: Checkout flows, payment processing, inventory management
- **Authentication Systems**: OAuth, SSO, multi-factor authentication, session management
- **Content Management**: CRUD operations, media upload, content moderation
- **API Testing**: Endpoint validation, response verification, error handling

#### 2. **AI-First Test Development**
- **Intelligent Test Generation**: AI creates comprehensive test scenarios
- **Dynamic Assertion Creation**: Context-aware validation criteria
- **Failure Analysis**: Automatic root cause identification
- **Test Maintenance**: AI updates tests when systems change

### Test File Structure

Each test follows a structured `.md` format designed for LLM execution:

```markdown
# Test: [Component/Feature Name]

## Pre-conditions
- Server requirements, test data setup, environment configuration

## Test Steps
1. **Navigate**: URL and setup
2. **Execute**: Detailed interaction steps using Playwright MCP
3. **Verify**: Expected outcomes with assertions
4. **Evidence**: Screenshot requirements for validation

## Expected Results
**PASS Criteria**: Specific conditions for test success
**FAIL Indicators**: What indicates test failure

## Bug Analysis
**Root Cause**: Analysis of why test fails
**Fix Location**: Files/components that need changes
```

### Generic Testing Examples

The framework works across any web application:

```markdown
# Test: E-commerce Checkout Flow
## Test Steps
1. **Navigate**: Load product page, add items to cart
2. **Execute**: Click checkout, fill payment form, submit order
3. **Verify**: Order confirmation displayed, email sent
4. **Evidence**: Screenshots of each step

# Test: Social Media Login
## Test Steps
1. **Navigate**: Go to login page
2. **Execute**: Test OAuth providers (Google, Facebook, Twitter)
3. **Verify**: Profile data populated correctly
4. **Evidence**: User dashboard screenshot

# Test: API Documentation Interface
## Test Steps
1. **Navigate**: Load API docs page
2. **Execute**: Test endpoint examples, copy code snippets
3. **Verify**: Code examples work, responses match docs
4. **Evidence**: Network tab screenshots
```

### Integration with Command Composition

Meta-testing integrates seamlessly with the command system:

```bash
# Red-Green-Refactor with LLM tests
/tdd "authentication flow"        # Creates failing LLM test
/testuif test_auth.md             # Execute test with Playwright MCP
/fix "implement OAuth flow"       # Fix code to make test pass
/testuif test_auth.md             # Verify test now passes
```

### Matrix Testing Integration

LLM tests incorporate comprehensive matrix testing:
- **Field Interaction Matrices**: Test all input combinations
- **State Transition Testing**: Validate workflow paths
- **Edge Case Validation**: Systematic boundary testing
- **Cross-Browser Compatibility**: Multi-environment validation

## 🚧 WIP: Orchestration System

### Multi-Agent Task Delegation Prototype

The orchestration system is an **active development prototype** that demonstrates autonomous multi-agent development workflows.

### Architecture Overview

```
Agent Assignment Layer:
├── Frontend Agent (/execute frontend tasks)
├── Backend Agent (/execute API tasks)
├── Testing Agent (/execute test tasks)
└── Opus-Master (/arch + integration)

Coordination Layer:
├── Redis-based communication
├── Task dependency management
└── Resource allocation

Integration Layer:
├── Individual PR creation per agent
├── Cross-agent validation
└── Final integration verification
```

### Real-World Performance Metrics

- **Cost**: $0.003-$0.050 per task (highly efficient)
- **Parallel Capacity**: 3-5 agents simultaneously
- **Success Rate**: 85% first-time-right with proper task specifications
- **Integration Success**: 90% cross-agent coordination without conflicts

### Usage Examples

```bash
# Basic task delegation
/orch "implement user dashboard with tests and documentation"

# Complex multi-component feature
/orch "add notification system with real-time updates, email integration, and admin controls"

# System monitoring
/orch monitor agents              # Check agent status
/orch "What's running?"          # Current task overview
tmux attach-session -t task-agent-frontend  # Direct agent access
```

### Development Status

**✅ Working Features**:
- Multi-agent task assignment with capability-based routing
- Redis coordination for inter-agent communication
- Tmux session management with isolated workspaces
- Individual PR creation per agent with branch management
- Cost-effective parallel execution ($0.003-$0.050/task)

**🚧 In Development**:
- Advanced dependency management between agents
- Cross-agent code review and integration testing
- Automatic scaling based on workload
- Enhanced error recovery and retry mechanisms

**🔮 Future Roadmap**:
- Integration with Meta-AI Testing Framework for agent validation
- Machine learning optimization of task routing algorithms
- Advanced collaboration patterns for complex architectural changes
- Integration with CI/CD pipelines for continuous deployment

### Building Block Composition Patterns

**Cognitive Chains**: `/think` + `/arch` + `/debug` = Deep analysis workflows
**Quality Chains**: `/test` + `/fix` + `/verify` = Quality assurance workflows
**Development Chains**: `/plan` + `/implement` + `/validate` = Development workflows

### The Hook Architecture

**Simple**: Each command is just a `.md` file that Claude Code reads as executable instructions
**Powerful**: These simple hooks enable complex behavior through composition rather than complexity
**Autonomous**: Commands chain together for complete workflows like "analyze → implement → test → create PR"

## 🎯 What You're Really Getting

This export contains **80+ commands** that transform Claude Code into:

1. **Autonomous Development Environment**: Single commands handle complete workflows
2. **Multi-Agent System**: Parallel task execution with specialized agents
3. **Quality Assurance Integration**: Automatic testing and validation
4. **Git Workflow Automation**: Branch management and PR creation
5. **Memory-Enhanced Learning**: System learns from previous executions

## 🔧 Claude Code Setup

### Intelligent Self-Setup (Recommended)
```bash
# Let Claude Code analyze and set up what you need
"I want to use the commands from https://github.com/jleechanorg/claude-commands - please analyze what's available and set up the ones that would be useful for my project"
```

Claude Code will:
1. **Analyze** your project structure and needs
2. **Recommend** relevant commands for your workflow  
3. **Install** selected commands to `.claude/commands/`
4. **Configure** hook automation in `.claude/settings.json`
5. **Test** setup and provide usage examples

### What Gets Set Up
- **Command Definitions**: Workflow orchestration commands (`/execute`, `/pr`, `/copilot`)
- **Hook Configuration**: Essential automation hooks for git workflow
- **Project Integration**: Adapted paths and references for your specific project
- **Usage Guidance**: Personalized examples based on your codebase

### Start Using Commands
```bash
# After setup, use powerful workflow commands
/execute "implement user authentication"  # → Full implementation workflow
/pr "fix performance issues"             # → Analysis → fix → PR creation  
/copilot                                # → Fix PR conflicts and comments
```

## 🎯 Adaptation Guide

### Project-Specific Placeholders

Commands contain placeholders that need adaptation:
- `$PROJECT_ROOT/` → Your project's main directory
- `your-project.com` → Your domain/project name
- `$USER` → Your username
- `TESTING=true python` → Your test execution pattern

### Example Adaptations

**Before** (exported):
```bash
TESTING=true python $PROJECT_ROOT/test_file.py
```

**After** (adapted):
```bash
npm test src/components/test_file.js
```

## 🚀 Advanced Features

### Multi-Command Compositions

Chain commands for complex workflows:
```bash
/execute "analyze codebase architecture"  # Deep analysis with TodoWrite
/plan "redesign authentication system"    # Structured planning with approval
/pr "implement OAuth integration"         # Full development lifecycle
/copilot                                 # Autonomous issue resolution
```

### Agent Orchestration

Parallel development with specialized agents:
```bash
/orch "build user dashboard"
# Spawns: Frontend agent + Backend agent + Testing agent + Architecture reviewer
# Result: 4 parallel PRs with integrated final solution
```

### Memory-Enhanced Development

Commands learn from previous executions:
```bash
/learn "authentication patterns"  # Capture knowledge
/execute "implement SSO"         # Apply learned patterns
# System remembers successful approaches and applies them
```

## 📚 Command Categories

### 🧠 Cognitive Commands (Semantic Composition)
`/think`, `/arch`, `/debug`, `/learn`, `/analyze`, `/research`

### ⚙️ Operational Commands (Protocol Enforcement)
`/headless`, `/handoff`, `/orchestrate`, `/orch`

### 🔧 Tool Commands (Direct Execution)
`/execute`, `/test`, `/pr`, `/copilot`, `/plan`

### 🎯 Workflow Orchestrators
`/pr`, `/copilot`, `/execute`, `/orch` - Complete multi-step workflows

### 🔨 Building Blocks
Individual commands that compose into larger workflows

## ⚠️ Important Notes

### Reference Export
This is a reference export from a working Claude Code project. Commands may need adaptation for your specific environment, but Claude Code excels at helping you customize them.

### Requirements
- Claude Code CLI
- Git repository context
- Project-specific adaptations for paths and commands

### Support
- Commands include adaptation warnings where project-specific changes needed
- Install script provides clear guidance for customization
- README examples show adaptation patterns

## 🎉 The Result: Workflow Transformation

Transform your development process from manual step-by-step work to autonomous workflow orchestration where single commands handle complex multi-phase processes.

This isn't just command sharing - it's **workflow transformation** through the power of command composition.

## 📚 Version History

### v1.1.0 (2025-08-09)

**Export Statistics**:
- Commands: 116 command definitions  
- Hooks: 13 Claude Code automation hooks
- Scripts: 5 infrastructure scripts

**Changes**:
- Comprehensive command system (116 commands) with enhanced automation
- Enhanced hook automation (13 hooks) including speculation detection and root file management
- Infrastructure automation (5 scripts) for development environment setup
- Template-based README generation with dynamic content replacement
- Obsolete file cleanup and maintenance for repository hygiene
- Additive export strategy preserving existing content while adding new features
- Enhanced content filtering and path normalization for cross-project compatibility
- Version tracking and change history management for transparent updates
- Single version history placement at bottom of README with table of contents integration

---

🚀 **Generated with [Claude Code](https://claude.ai/code)**

**Co-Authored-By: Claude <noreply@anthropic.com>**
