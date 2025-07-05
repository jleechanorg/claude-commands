# Slash Commands Reference

This document provides comprehensive documentation for all available slash commands in the WorldArchitect.AI development workflow.

## Command Categories

### Development Workflow Commands

#### `/tdd` or `/rg`
**Purpose**: Execute Test-Driven Development (red-green-refactor) workflow

**Usage**: 
```
/tdd
/rg
```

**Behavior**:
1. Write comprehensive failing tests FIRST
2. Run tests to confirm they fail (red state)
3. Implement minimal code to make tests pass (green state)
4. Refactor while keeping tests green
5. For UI features: Test actual user experience, not just code

**Example**:
```
User: /tdd for user authentication
Assistant: I'll implement user authentication using TDD workflow:

1. First, writing failing tests for authentication...
[Creates test file with authentication test cases]

2. Running tests to confirm failure...
[Executes tests, shows red state]

3. Implementing minimal authentication code...
[Implements basic auth to make tests pass]

4. Refactoring for better structure...
[Improves code while maintaining green tests]
```

#### `/test`
**Purpose**: Run comprehensive test suite with proper reporting

**Usage**:
```
/test
```

**Behavior**:
- Execute `./run_tests.sh` from project root
- Highlight any failing tests in red for visibility
- Fix failures immediately or ask user for guidance
- Include test results in PR descriptions
- Use `TESTING=true vpython` for integration tests

#### `/optimize`
**Purpose**: Improve code/file performance, readability, or structure

**Usage**:
```
/optimize
```

**Behavior**:
- Analyze current file/code for optimization opportunities
- Remove duplicates, condense verbose sections
- Maintain functionality while improving efficiency
- Follow user's established preferences for format choices

#### `/integrate`
**Purpose**: Execute clean Git branch management workflow

**Usage**:
```
/integrate
```

**Behavior**:
- Run integrate pattern: `git checkout main && git pull && git branch -D dev && git checkout -b dev`
- Create fresh branch from latest main
- Ensure proper branch tracking and push safety
- Follow PR-only workflow for main branch protection

### Project Management Commands

#### `/milestones N` or `/milestones suggest`
**Purpose**: Break work into structured milestone phases

**Usage**:
```
/milestones 4
/milestones suggest
```

**Behavior for `/milestones N`**:
- Break current work into N specific milestones
- After completing each milestone:
  - Update scratchpad file (`roadmap/scratchpad_[branch_name].md`)
  - Commit and push to GitHub to save state
  - Provide status update before proceeding
- Each milestone should be independently valuable and testable

**Behavior for `/milestones suggest`**:
- Analyze task complexity and dependencies
- Suggest optimal number of milestones (typically 3-7)
- Provide rationale for suggested breakdown
- List each milestone with clear objectives and success criteria

#### `/scratchpad`
**Purpose**: Create or update work-in-progress planning documents

**Usage**:
```
/scratchpad
```

**Behavior**:
Generate `roadmap/scratchpad_[branch_name].md` with:
- Project Goal: Clear statement of purpose
- Implementation Plan: Step-by-step with milestones
- Current State: Completed, in progress, blocked items
- Next Steps: Specific actionable items
- Key Context: Important decisions and findings
- Branch Info: Remote branch, PR number, merge target

### Analysis & Review Commands

#### `/context` or `/est`
**Purpose**: Analyze current session context usage

**Usage**:
```
/context
/est
```

**Behavior**:
Provides detailed breakdown including:
1. Session Context Usage: Estimated percentage of context window used
2. Breakdown by Category (system messages, file operations, conversation, tool outputs)
3. Remaining Capacity: Percentage and practical limitations
4. Usage Indicators: What suggests approaching limits
5. Recommendations: Whether to continue or start fresh session

**Example Response**:
```
Session Context Usage: ~75-85% used
- System messages: ~10-15%
- File operations: ~30-40%  
- Conversation: ~25-35%
- Tool outputs: ~10-15%

Remaining: ~15-25% (good for a few more operations)
Recommendation: Approaching limits, consider fresh session for major work
```

#### `/review` or `/copilot`
**Purpose**: Process GitHub Copilot/CodeRabbit feedback systematically

**Usage**:
```
/review
/copilot
```

**Behavior**:
- List all open PRs with AI comments
- Fetch and analyze suggestions using `gh pr view [PR_NUMBER] --comments`
- Filter comments from 'coderabbitai' user
- Apply accepted changes and explain rejections
- Create commits addressing feedback
- Update PRs with summary of changes made

## Command Implementation Notes

### Command Recognition
- Commands are case-insensitive
- Both short and long forms are supported where applicable
- Commands can appear anywhere in user input (beginning, middle, end)

### Error Handling
- Invalid commands provide helpful suggestions
- Missing parameters prompt for clarification
- Failed operations include recovery instructions

### Integration with Existing Workflow
- All commands respect existing git workflow rules
- Commands follow established coding standards
- Results include proper attribution and documentation

## Adding New Commands

To add a new slash command:

1. **Define the command** in `CLAUDE.md` under "Slash Commands" section
2. **Update this documentation** with comprehensive details
3. **Add to quick reference** in `roadmap/quick_reference.md`
4. **Test the command** with various scenarios
5. **Document any dependencies** or prerequisites

## See Also

- `CLAUDE.md` - Primary rules file with command definitions
- `roadmap/quick_reference.md` - Quick command summary
- `.cursor/rules/rules.mdc` - Cursor-specific configurations