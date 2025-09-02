# /copilotc - Convergent Copilot (Autonomous GitHub Comment Resolution)

## 🎯 Purpose
**Universal composition command combining convergence + copilot for autonomous GitHub comment resolution**

Runs `/conv` (convergence) and `/copilot` in an autonomous loop until all serious GitHub comments are resolved.

## 🚀 Command Architecture - Universal Composition

**Pattern**: Autonomous convergence-driven PR comment resolution system

**Flow**:
```
1. `/conv "resolve all serious GitHub comments"`
2. Auto-execute `/copilot` for each iteration  
3. Continue until convergence criteria met (all serious comments resolved)
4. Success when GitHub shows clean PR status
```

## 🔄 Autonomous Operation Protocol

**FULLY AUTONOMOUS**: This command operates without user intervention until completion or iteration limit reached.

### Universal Composition Implementation

**Phase 1: Goal Definition & Convergence Setup**
```bash
# Execute convergence with GitHub comment resolution goal
/conv "resolve all serious GitHub comments and make PR mergeable"
```

**Phase 2: Integrated Copilot Processing**
- Within each convergence iteration, automatically execute `/copilot`
- Use copilot's direct orchestration for rapid comment processing
- Validate resolution success after each copilot run
- Continue convergence until all serious comments addressed

**Phase 3: Success Validation**
- Check GitHub PR status for remaining serious issues
- Verify comment thread resolution
- Confirm mergeable status
- Exit when convergence criteria fully met

## 🎛️ Configuration Options

**Default Behavior**: 
- **Max Iterations**: 10 (inherited from `/conv` default)
- **Success Criteria**: All serious GitHub comments resolved + PR mergeable
- **Validation Method**: GitHub API status checks + comment analysis

**Custom Usage**:
```bash
/copilotc                    # Use default settings (10 iterations max)
/copilotc --max-iterations 5 # Custom iteration limit
```

## 🚨 Autonomous Operation Rules

**CONVERGENCE-DRIVEN**: Uses `/conv` autonomous goal achievement system
- **No user prompts**: Continues until success or iteration limit
- **Smart iteration**: Each cycle improves PR state toward mergeable status  
- **Evidence-based success**: GitHub API confirmation of comment resolution
- **Auto-learning**: Convergence system learns from each iteration

**COPILOT INTEGRATION**: Leverages `/copilot` fast processing within each iteration
- **Direct GitHub MCP**: Fast comment processing and resolution
- **Performance optimized**: 2-3 minute copilot cycles vs 20+ minute alternatives
- **Comprehensive coverage**: Processes all comment types systematically

## 💡 Use Cases

**Perfect for**:
- PRs with multiple unresolved review comments
- Automated PR preparation for merge
- Continuous integration comment resolution
- Large PR cleanup and finalization

**Example Scenarios**:
- "Fix all the review comments on PR #123"
- "Clean up PR before merge approval"
- "Resolve CI failures and review feedback"
- "Make PR mergeable state"

## ⚡ Performance Expectations

**Target Performance**: 
- **Per Iteration**: 2-3 minutes (copilot processing)
- **Total Time**: 10-30 minutes (depending on comment complexity)
- **Success Rate**: High (convergence + copilot proven systems)

**Success Pattern**: Most PRs achieve clean status within 3-5 iterations

## 🔗 Related Commands

- `/conv` - Base convergence system (autonomous goal achievement)
- `/copilot` - Fast direct PR processing (2-3 minute cycles)
- `/fixprc` - Similar autonomous PR comment fixing (specialized variant)
- `/pr` - Complete development lifecycle (includes copilot phase)

## 🎯 Success Criteria

**Command completes successfully when**:
1. ✅ All serious GitHub comments resolved or addressed
2. ✅ PR shows mergeable status (no blocking issues)
3. ✅ Comment threads properly closed or acknowledged
4. ✅ CI/GitHub checks passing (where applicable)

**Iteration ends when**: Max iterations reached OR success criteria fully met

## Implementation Notes

**Universal Composition**: This command uses the universal composition system to intelligently orchestrate `/conv` and `/copilot` together, creating an autonomous loop optimized for GitHub comment resolution.

**Context Efficiency**: Convergence system includes context optimization and direct goal processing for efficient operation across multiple iterations.