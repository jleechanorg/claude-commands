# /reviewdeep Command

Deep architecture and implementation review using ultra thinking mode, /arch review, and Gemini MCP with role switching.

## Usage
```
/reviewdeep                           # Review current branch/PR (default)
/reviewdeep <pr_number|file|feature>  # Review specific target
/reviewd                              # Short alias for current branch/PR
/reviewd <pr_number|file|feature>     # Short alias with specific target
```

## What it does

Performs a comprehensive multi-phase analysis:

### Phase 1: Ultra Thinking (12-point analysis)

1. **Architecture Soundness** - Design patterns, separation of concerns
2. **Implementation Quality** - Code correctness, best practices
3. **Practical Feasibility** - Real-world usability, edge cases
4. **Error Handling** - Failure modes, recovery mechanisms
5. **Performance Impact** - Resource usage, scalability
6. **Integration Issues** - Compatibility with existing systems
7. **Security Concerns** - Vulnerabilities, data protection
8. **Testing Strategy** - Coverage, quality, maintainability
9. **Cost Analysis** - Resource consumption, API usage
10. **Success Probability** - Realistic assessment of outcomes
11. **Required Improvements** - Specific actionable items
12. **Final Verdict** - Go/no-go recommendation with conditions

### Phase 2: Architecture Review (/arch integration)

- Executes `/arch` command for dual-perspective analysis
- Claude and Gemini alternate architect/reviewer roles
- Provides architectural insights and recommendations

### Phase 3: Gemini MCP Multi-Role Analysis

Analyzes from three distinct perspectives using role switching:

1. **Developer Role**
   - Code quality and maintainability
   - Implementation correctness
   - Performance and security
   - Testing adequacy

2. **Architect Role**
   - System design patterns
   - Scalability considerations
   - Integration points
   - Long-term maintainability

3. **Business Analyst Role**
   - Business value delivered
   - User experience impact
   - Cost-benefit analysis
   - ROI considerations

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

## Output Format

### Core Analysis
- **Verdict**: X% production ready with summary
- **Strengths**: Architectural and implementation wins
- **Critical Flaws**: Must-fix issues with severity
- **Realistic Assessment**: Probability of success
- **Required Improvements**: Prioritized action items
- **Bottom Line**: Executive summary

### Additional Insights
- **Architecture Review**: Detailed /arch output with dual perspectives
- **Gemini Multi-Role**: Insights from developer, architect, and analyst viewpoints
- **Synthesized Recommendations**: Combined insights from all analysis methods

## Integration Details

The command orchestrates multiple analysis tools:

1. **Ultra Thinking Mode**: 12+ sequential thoughts for deep analysis
2. **/arch Command**: Automatic execution for architecture review
3. **Gemini MCP**: Three separate API calls with role switching
4. **Synthesis Engine**: Combines all perspectives into cohesive recommendations

## Comparison with Other Review Commands

- `/review` - Standard code review with basic checks
- `/arch` - Architecture-focused dual perspective only
- `/reviewdeep` - Complete analysis: ultra thinking + /arch + Gemini multi-role

## When to Use

- Major architectural changes
- High-risk implementations
- Performance-critical code
- Security-sensitive features
- Complex integrations
- Before production deployment

## Configuration

The command automatically:
- Enables ultra thinking mode (12+ sequential thoughts)
- Executes /arch for architecture review
- Calls Gemini MCP with 3 role switches
- Analyzes from 5+ distinct perspectives
- Considers second-order effects
- Provides probability assessments
- Generates actionable improvements

## API Usage

- **Ultra Thinking**: 1 extended call with 12+ thoughts
- **/arch Integration**: 1 architecture review call
- **Gemini MCP**: 3 separate calls (one per role)
- **Total**: ~5 API calls for comprehensive analysis
