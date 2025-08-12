# /reviewdeep Command

**Command Summary**: Comprehensive multi-perspective review through orchestrated command composition

**Purpose**: Deep analysis combining code review, architectural assessment, and ultra thinking for complete evaluation

## Usage
```
/reviewdeep                           # Review current branch/PR (default)
/reviewdeep <pr_number|file|feature>  # Review specific target
/reviewd                              # Short alias for current branch/PR
/reviewd <pr_number|file|feature>     # Short alias with specific target
```

## Command Composition

**`/reviewdeep` = `/reviewe` (enhanced review) + `/arch` + `/thinku` + Context7 MCP + Gemini MCP + Perplexity MCP**

The command executes specialized commands with mandatory MCP integration for comprehensive analysis.

## Execution Flow

**The command delegates to `/execute` for intelligent orchestration of components:**

```markdown
/execute Perform comprehensive multi-perspective review:
1. /reviewe [target]    # Enhanced code review with security analysis
2. /arch [target]       # Architectural assessment
3. /thinku [target]     # Ultra deep thinking analysis
```

The `/execute` delegation ensures optimal execution with:
- Intelligent resource allocation
- Progress tracking via TodoWrite
- Auto-approval for review workflows
- Parallel execution where possible

Each command is executed with the same target parameter passed to `/reviewdeep`.

### 1. `/reviewe` - Enhanced Review with Official Integration

**🚨 POSTS COMPREHENSIVE COMMENTS**
- **Official Review**: Built-in Claude Code `/review` command provides baseline analysis
- **Enhanced Analysis**: Multi-pass security analysis with code-review subagent
- **Security Focus**: SQL injection, XSS, authentication flaws, data exposure
- **Bug Detection**: Runtime errors, null pointers, race conditions, resource leaks  
- **Performance Review**: N+1 queries, inefficient algorithms, memory leaks
- **Context7 Integration**: Up-to-date API documentation and framework best practices
- **ALWAYS POSTS** expert categorized comments (🔴 Critical, 🟡 Important, 🔵 Suggestion, 🟢 Nitpick)
- **ALWAYS POSTS** comprehensive security and quality assessment summary
- Provides actionable feedback with specific line references and fix recommendations

### 2. `/arch` - Architectural Assessment
- Dual-perspective architectural analysis
- System design patterns and scalability considerations
- Integration points and long-term maintainability
- Structural soundness and design quality evaluation

### 3. `/thinku` - Ultra Deep Thinking
- 12+ sequential thoughts for thorough analysis
- Multi-step reasoning with revision capability
- Complex problem decomposition and solution synthesis
- Considers second-order effects and edge cases

### 4. **Context7 + GitHub + Gemini MCP Integration** - Expert Knowledge Analysis (ALWAYS REQUIRED)
- **Context7 MCP**: Real-time API documentation and framework-specific expertise
- **GitHub MCP**: Primary for PR, files, and review comment operations
- **Developer Perspective**: Code quality, maintainability, performance, security vulnerabilities
- **Architect Perspective**: System design, scalability, integration points, architectural debt  
- **Business Analyst Perspective**: Business value, user experience, cost-benefit, ROI analysis
- **Framework Expertise**: Language-specific patterns and up-to-date best practices

### 5. **Perplexity MCP Integration** - Research-Based Analysis (ALWAYS REQUIRED)
- **Security Standards**: OWASP guidelines and latest vulnerability research
- **Industry Best Practices**: Current standards and proven approaches
- **Technical Challenges**: Common pitfalls and expert recommendations
- **Performance Optimization**: Industry benchmarks and optimization techniques
- **Emerging Patterns**: Latest security vulnerabilities and prevention techniques

## Analysis Flow

```
INPUT: PR/Code/Feature
    ↓
/EXECUTE ORCHESTRATION:
    ├─ Plans optimal workflow
    ├─ Auto-approves review tasks
    └─ Tracks progress via TodoWrite
    ↓
EXECUTE: /reviewe [target]
    ├─ Runs official /review → Native Claude Code review
    └─ Runs enhanced analysis → Multi-pass security & quality review
    └─ Posts GitHub PR comments
    ↓
EXECUTE: /arch [target]
    └─ Architectural insights & design assessment
    ↓
EXECUTE: /thinku [target]
    └─ Deep reasoning synthesis & recommendations
    ↓
MCP INTEGRATION (automatic within each command):
    ├─ Context7 MCP → Up-to-date API documentation
    ├─ Gemini MCP → Multi-role AI analysis
    └─ Perplexity MCP → Research-based security insights
    ↓
OUTPUT: Comprehensive multi-perspective analysis with native + enhanced insights
```

## What You Get

### Comprehensive Coverage
- **Code Level**: Bug detection, security analysis, performance issues
- **Architecture Level**: Design patterns, scalability, integration concerns
- **Strategic Level**: Deep reasoning about implications and recommendations

### Multi-Perspective Analysis
- **Technical Perspective**: From `/review` - immediate code quality issues
- **Design Perspective**: From `/arch` - structural and architectural concerns
- **Strategic Perspective**: From `/thinku` - deep reasoning and synthesis
- **AI-Enhanced Analysis**: From Gemini MCP - multi-role expert perspectives
- **Research-Backed Insights**: From Perplexity MCP - industry best practices and standards

### Actionable Output
**🚨 POSTS TO GITHUB PR**
- **POSTS** specific inline code comments with improvement suggestions directly to PR
- **POSTS** general review comment with comprehensive findings summary to PR
- Architectural recommendations with design alternatives
- Reasoned conclusions with prioritized action items

## Implementation Protocol

**When `/reviewdeep` is invoked, it delegates to `/execute` for orchestration:**

```markdown
/execute Perform deep review with comprehensive multi-perspective analysis:

Step 1: Execute enhanced review
/reviewe [target]

Step 2: Execute architectural assessment  
/arch [target]

Step 3: Execute ultra deep thinking
/thinku [target]

Step 4: Synthesize all findings into comprehensive report
```

**The `/execute` delegation provides**:
- Automatic workflow planning and optimization
- Built-in progress tracking with TodoWrite
- Intelligent parallelization where applicable
- Resource-efficient execution

**Important**: Each command must be executed with the same target parameter. If no target is provided, all commands operate on the current branch/PR.

## Examples

```bash
# Review current branch/PR (most common usage)
/reviewdeep
# This executes: /reviewe → /arch → /thinku
/reviewd

# Review a specific PR
/reviewdeep 592
# This executes: /reviewe 592 → /arch 592 → /thinku 592
/reviewd #592

# Review a file or feature
/reviewdeep ".claude/commands/pr.py"
# This executes: /reviewe ".claude/commands/pr.py" → /arch ".claude/commands/pr.py" → /thinku ".claude/commands/pr.py"
/reviewd "velocity doubling implementation"
```

## When to Use

- **Major architectural changes** - Need both code and design analysis
- **High-risk implementations** - Require thorough multi-angle examination
- **Performance-critical code** - Need technical + strategic assessment
- **Security-sensitive features** - Comprehensive vulnerability analysis
- **Complex integrations** - Architectural + implementation concerns
- **Before production deployment** - Complete readiness evaluation

## Comparison with Individual Commands

- **`/review`**: Official built-in code review (basic)
- **`/reviewe`**: Enhanced review (official + advanced analysis)
- **`/arch`**: Architectural assessment only
- **`/thinku`**: Deep reasoning only
- **`/reviewdeep`**: All perspectives combined for complete analysis

## Benefits of Composition

- **Modular**: Each component serves a distinct analytical purpose
- **Comprehensive**: No blind spots - covers code, design, and strategic levels
- **Efficient**: Leverages existing specialized commands rather than duplicating functionality
- **Flexible**: Individual commands can be used separately when full analysis isn't needed
- **Maintainable**: Changes to individual commands automatically improve the composite
- **AI-Enhanced**: Mandatory MCP integration provides expert-level analysis beyond traditional code review

## Review Principles & Philosophy

### Core Principles (Applied During Analysis)
- **Verify Before Modify**: Ensure bugs are reproduced and root causes understood before suggesting fixes
- **Incremental and Isolated Changes**: Recommend small, atomic modifications that can be tested independently
- **Test-Driven Resolution**: Suggest writing tests for bug scenarios before implementing fixes
- **Defensive Validation**: Recommend input checks, error handling, and assertions to guard against invalid states
- **Fail Fast, Fail Loud**: No silent fallbacks - errors should be explicit and actionable

### Development Tenets (Beliefs That Guide Reviews)
- **Bugs Are Opportunities**: Each issue is a chance to enhance robustness, not just patch symptoms
- **Prevention Over Cure**: Prioritize practices that avoid bugs (code reuse, proper abstractions)
- **Simplicity Wins**: Simpler code is less error-prone - avoid over-engineering
- **CI Parity Is Sacred**: All code must run deterministically in CI vs local environments
- **Continuous Learning**: Document patterns from failures to prevent recurrence

### Quality Goals (What Reviews Aim For)
- **Zero Regressions**: Ensure changes don't introduce new bugs
- **High Code Coverage**: Recommend 80-90% test coverage for critical paths
- **Maintainable Codebase**: Fixes should improve readability and modularity
- **Fast MTTR**: Issues should be resolvable within hours with proper documentation
- **Reduced Bug Density**: Lower bugs per 1000 lines through preventive patterns

### 6. **Testing & CI Safety Analysis** (Enhanced from /reviewe)
Building on the code-level checks from `/reviewe`, this phase analyzes system-wide patterns:

- **Subprocess Discipline at Scale**: System-wide timeout enforcement patterns
- **Skip Pattern Elimination**: Zero tolerance policy enforcement across entire codebase
- **CI Parity Validation**: Test infrastructure consistency analysis
- **Resource Management Patterns**: System-level cleanup strategies
- **Input Sanitization Architecture**: Security patterns across all entry points
- **Error Handling Philosophy**: Consistent error propagation strategies

## MCP Integration Requirements

### 🚨 MANDATORY MCP Usage
- **Context7 MCP**: ALWAYS required for up-to-date API documentation and framework expertise
- **Gemini MCP**: ALWAYS required for multi-role AI analysis  
- **Perplexity MCP**: ALWAYS required for research-based security and best practice insights
- **No Fallback Mode**: All MCP integrations are mandatory, not optional
- **Error Handling**: Proper timeout and retry logic for MCP calls
- **Expert Integration**: Context7 provides current API docs, Gemini provides analysis, Perplexity provides research

### Implementation Notes
- Uses `mcp__gemini-cli-mcp__gemini_chat_pro` for primary analysis
- Uses `mcp__perplexity-ask__perplexity_ask` for research insights
- Integrates MCP responses into comprehensive review output
- Maintains existing command composition while adding AI enhancement layer