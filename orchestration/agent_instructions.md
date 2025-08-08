# General Instructions for All Autonomous Agents

## CRITICAL: Always Start Clean

**BEFORE doing any work:**
1. Use the `/nb` command to create a clean branch from latest main
2. This ensures your PR only contains your intended changes
3. Never work directly on an existing branch that has unrelated changes

## Workflow

1. `/nb` - Create clean branch from main
2. Make your changes
3. Run tests (`./run_tests.sh`)
4. Commit with clear message
5. `/pr` - Create pull request

## Why This Matters

Working on an existing branch with unrelated changes will:
- Create messy PRs with unrelated files
- Make code review difficult
- Risk merge conflicts
- Violate single-responsibility principle for PRs

## Example

```
/nb fix/my-specific-task
# Now you're on a clean branch
# Make your changes...
./run_tests.sh
git add -A
git commit -m "Clear description of changes"
/pr
```

Remember: One PR = One Purpose
