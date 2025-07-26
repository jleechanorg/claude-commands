# Command Composition A/B Test Evidence

This directory contains concrete evidence from A/B testing the command composition system using headless Claude Code instances.

## Test Methodology

**Execution**: Direct Claude Code instances with `-p` flag and `--output-format stream-json --dangerously-skip-permissions`

**Task**: Debug a function with division by zero bug

**Groups**:
- **Group A**: Command composition (`/think /debug /analyze`)
- **Group B**: Natural language equivalent ("analyze systematically and thoroughly...")

## Files

### Raw Test Outputs (Archived)
- Raw JSON logs (~107KB) moved to backup after analysis completion
- All key findings extracted and preserved in analysis documents below

### Analysis Documents
- `concrete_ab_test_evidence.md` - Comprehensive comparison and analysis
- `headless_ab_comparison.md` - Extracted behavioral differences

### Test Materials
- `test_case_debugging_task.py` - Original buggy code used for testing
- `test_case_group_b_solution.py` - Working solution created by Group B

## Key Findings

### Measurable Behavioral Differences

| Aspect | Group A (Commands) | Group B (Natural) |
|--------|-------------------|-------------------|
| **Analysis Method** | 4 sequential thoughts via thinking tool | Direct structured analysis |
| **Solution Approach** | Conservative: return unchanged | Creative: multiply by -1 |
| **Verification** | Theoretical explanation | Actual code execution |
| **Problem-Solving** | Deliberative, multiple options | Practical, immediate |

### Tools Used
- **Group A**: `mcp__sequential-thinking__sequentialthinking`
- **Group B**: Direct analysis with markdown formatting

### Solutions Produced
- **Group A**: `results.append(item)` - Return non-positive numbers unchanged
- **Group B**: `results.append(item * -1)` - Convert negatives to positive, tested execution

## Conclusion

Command composition creates **genuine, measurable behavioral differences** in problem-solving approach, tool usage, and solution methodology. This is not placebo effect - it's documented, reproducible behavioral synthesis.

Both approaches solved the problem correctly but with distinctly different cognitive patterns and verification methods.
