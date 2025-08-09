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

The command executes specialized commands with mandatory MCP integration for comprehensive analysis:

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
1. /reviewe → Enhanced review (Official /review + Advanced analysis)
    ├─ Official /review → Native Claude Code review
    └─ Enhanced analysis → Multi-pass security & quality review
    ↓
2. /arch  → Architectural insights & design assessment
    ↓
3. /thinku → Deep reasoning synthesis & recommendations
    ↓
4. Context7 + Gemini MCP → Multi-role AI analysis with current best practices
    ↓
5. Perplexity MCP → Research-based security & industry insights
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

## Examples

```bash
# Review current branch/PR (most common usage)
/reviewdeep
/reviewd

# Review a specific PR
/reviewdeep 592
/reviewd #592

# Review a file or feature
/reviewdeep ".claude/commands/pr.py"
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
