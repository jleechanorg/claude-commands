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

**`/reviewdeep` = `/review` + `/arch` + `/thinku` + Gemini MCP + Perplexity MCP**

The command executes specialized commands with mandatory MCP integration for comprehensive analysis:

### 1. `/review` - Code Quality Analysis

**🚨 POSTS COMMENTS**
- Virtual [AI reviewer] agent performs comprehensive code analysis
- Identifies bugs, security issues, performance problems, best practice violations
- **ALWAYS POSTS** categorized review comments (🔴 Critical, 🟡 Important, 🔵 Suggestion, 🟢 Nitpick)
- **ALWAYS POSTS** general review comment with comprehensive findings summary
- Provides file-by-file analysis with specific line references

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

### 4. **Gemini MCP Integration** - Multi-Role AI Analysis (ALWAYS REQUIRED)
- **Developer Perspective**: Code quality, maintainability, performance, security vulnerabilities
- **Architect Perspective**: System design, scalability, integration points, architectural debt
- **Business Analyst Perspective**: Business value, user experience, cost-benefit, ROI analysis
- **Enhanced Context**: Uses actual Gemini AI for deep technical analysis

### 5. **Perplexity MCP Integration** - Research-Based Analysis (ALWAYS REQUIRED)
- **Industry Best Practices**: Current standards and proven approaches
- **Technical Challenges**: Common pitfalls and expert recommendations
- **Security Considerations**: Latest security patterns and vulnerability research
- **Performance Optimization**: Industry benchmarks and optimization techniques

## Analysis Flow

```
INPUT: PR/Code/Feature
    ↓
1. /review → Code quality findings & review comments
    ↓
2. /arch  → Architectural insights & design assessment
    ↓
3. /thinku → Deep reasoning synthesis & recommendations
    ↓
4. Gemini MCP → Multi-role AI analysis (Developer/Architect/Business)
    ↓
5. Perplexity MCP → Research-based best practices & industry insights
    ↓
OUTPUT: Comprehensive multi-perspective analysis with AI-enhanced insights
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

- **`/review`**: Code quality analysis only
- **`/arch`**: Architectural assessment only
- **`/thinku`**: Deep reasoning only
- **`/reviewdeep`**: All three perspectives combined for complete analysis

## Benefits of Composition

- **Modular**: Each component serves a distinct analytical purpose
- **Comprehensive**: No blind spots - covers code, design, and strategic levels
- **Efficient**: Leverages existing specialized commands rather than duplicating functionality
- **Flexible**: Individual commands can be used separately when full analysis isn't needed
- **Maintainable**: Changes to individual commands automatically improve the composite
- **AI-Enhanced**: Mandatory MCP integration provides expert-level analysis beyond traditional code review

## MCP Integration Requirements

### 🚨 MANDATORY MCP Usage
- **Gemini MCP**: ALWAYS required for multi-role AI analysis
- **Perplexity MCP**: ALWAYS required for research-based insights
- **No Fallback Mode**: MCP integration is mandatory, not optional
- **Error Handling**: Proper timeout and retry logic for MCP calls
- **Multi-Role Analysis**: Gemini provides Developer, Architect, and Business Analyst perspectives

### Implementation Notes
- Uses `mcp__gemini-cli-mcp__gemini_chat_pro` for primary analysis
- Uses `mcp__perplexity-ask__perplexity_ask` for research insights
- Integrates MCP responses into comprehensive review output
- Maintains existing command composition while adding AI enhancement layer
