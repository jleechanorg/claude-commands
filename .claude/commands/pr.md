# /pr Command

End-to-end implementation from idea to working pull request.

## Usage
```
/pr [task_description]
```

## What it does

Takes a task description and handles the complete implementation cycle:

1. **Analysis**: Understands the task and existing codebase
2. **Planning**: Creates implementation approach
3. **Implementation**: Writes the actual code changes
4. **Testing**: Creates/updates tests and ensures they pass
5. **Validation**: Runs all tests until 100% passing
6. **PR Creation**: Creates a complete PR ready for review

## Examples

```
/pr "Add logging configuration to main.py"
/pr "Fix bug where user names are not validated"
/pr "Add dark mode toggle to settings page"
```

## Process Flow

1. Creates feature branch: `feature/[task-name]`
2. Analyzes codebase to understand context
3. Implements solution following project patterns
4. Writes/updates relevant tests
5. Runs test suite until all tests pass
6. Creates comprehensive PR with:
   - Implementation summary
   - Test results (must be passing)
   - Files changed with explanations
   - Any breaking changes noted

## Requirements

- Clear task description
- Task scope should be reasonable (not "rewrite entire app")
- Existing tests should be passing before starting

## Safeguards

- Complexity limits to prevent overly broad changes
- User confirmation required for:
  - Major refactoring (>10 files)
  - Breaking changes
  - Deletion of existing functionality
- Automatic fallback to `/handoff` if task is too complex

## Output

Returns the PR URL and summary of implementation.

## Comparison with Other Commands

- **`/pr`**: Complete implementation from idea to PR
- **`/handoff`**: Only planning/analysis, PR for someone else to implement  
- **`/push`**: For manually completed work, creates/updates PR
- **`/execute`**: General task execution without PR creation