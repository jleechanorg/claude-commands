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

**`/reviewdeep` = `/review` + `/arch` + `/thinku`**

The command executes three specialized commands in sequence for comprehensive analysis:

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
OUTPUT: Comprehensive multi-perspective analysis
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
