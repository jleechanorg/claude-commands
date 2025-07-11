# Hooks Implementation Scratchpad

**Goal**: Enhance `/review` and `/integrate` commands with Claude Code hooks for robust automation

## Research Findings

Claude Code hooks provide deterministic control at lifecycle points:
- **PreToolUse**: Execute before tool calls
- **PostToolUse**: Execute after tool calls  
- **Notification**: Custom notification handling

**Key Capabilities**:
- Shell command execution with full user permissions
- JSON configuration for matching conditions
- Exit code and JSON output for control flow
- Tool-specific or global matching

## Implementation Plan

### 1. `/review` Command Enhancement

**Current State**: Manual auto-detection via `gh pr list --head $(git branch --show-current)`

**Hook Enhancement**:
```json
{
  "PreToolUse": {
    "match": "user input matches '/review' without PR number",
    "command": "scripts/auto-detect-pr.sh",
    "description": "Auto-detect current branch PR and inject into context"
  },
  "PostToolUse": {
    "match": "files were modified during review",
    "command": "scripts/post-review-cleanup.sh", 
    "description": "Format code, run tests, update PR status"
  }
}
```

**Script: `scripts/auto-detect-pr.sh`**:
```bash
#!/bin/bash
# Auto-detect PR for current branch
current_branch=$(git branch --show-current)
pr_info=$(gh pr list --head "$current_branch" --json number,url)

if [ -z "$pr_info" ] || [ "$pr_info" = "[]" ]; then
    echo "No PR found for branch: $current_branch" >&2
    exit 1
fi

# Extract PR number and inject into context
pr_number=$(echo "$pr_info" | jq -r '.[0].number')
pr_url=$(echo "$pr_info" | jq -r '.[0].url')

# Return JSON for Claude Code to use
echo "{\"pr_number\": \"$pr_number\", \"pr_url\": \"$pr_url\", \"branch\": \"$current_branch\"}"
```

**Script: `scripts/post-review-cleanup.sh`**:
```bash
#!/bin/bash
# Post-review cleanup and validation
# Run formatters on modified files
git diff --name-only HEAD~1 | while read file; do
    case "$file" in
        *.py) black "$file" ;;
        *.js) prettier --write "$file" ;;
        *.ts) prettier --write "$file" ;;
    esac
done

# Run quick tests on modified areas
./run_tests.sh --quick

# Update PR with status
echo "Review fixes applied and tested"
```

### 2. `/integrate` Command Enhancement

**Current State**: Manual validation in integrate.sh script

**Hook Enhancement**:
```json
{
  "PreToolUse": {
    "match": "user input contains '/integrate'",
    "command": "scripts/validate-integration.sh",
    "description": "Validate branch state and custom branch name"
  },
  "PostToolUse": {
    "match": "new branch was created",
    "command": "scripts/setup-new-branch.sh",
    "description": "Setup test server and environment for new branch"
  }
}
```

**Script: `scripts/validate-integration.sh`**:
```bash
#!/bin/bash
# Pre-integration validation
current_branch=$(git branch --show-current)

# Extract custom branch name from command if provided
custom_branch=""
if [[ "$1" =~ /integrate[[:space:]]+([^[:space:]]+) ]]; then
    custom_branch="${BASH_REMATCH[1]}"
fi

# Validate custom branch name doesn't exist
if [ -n "$custom_branch" ] && git show-ref --verify --quiet "refs/heads/$custom_branch"; then
    echo "Error: Branch '$custom_branch' already exists" >&2
    exit 1
fi

# Check for uncommitted changes
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Error: Uncommitted changes detected" >&2
    exit 1
fi

# Check for unpushed commits
if git status --porcelain=v1 -b | grep -q "ahead"; then
    echo "Error: Unpushed commits detected" >&2
    exit 1
fi

echo "{\"current_branch\": \"$current_branch\", \"custom_branch\": \"$custom_branch\", \"validation\": \"passed\"}"
```

**Script: `scripts/setup-new-branch.sh`**:
```bash
#!/bin/bash
# Post-integration setup
new_branch=$(git branch --show-current)

# Setup test server for new branch
./test_server_manager.sh setup "$new_branch"

# Create initial scratchpad
touch "roadmap/scratchpad_${new_branch}.md"
echo "# Scratchpad for $new_branch" > "roadmap/scratchpad_${new_branch}.md"

# Log integration
echo "$(date): Integrated to $new_branch" >> tmp/integration_log.txt

echo "New branch '$new_branch' setup complete"
```

## Configuration Location

**File**: `.claude/hooks.json`
```json
{
  "hooks": [
    {
      "event": "PreToolUse",
      "match": {
        "pattern": "/review(?!\\s+\\d+)",
        "description": "Review command without PR number"
      },
      "command": "scripts/auto-detect-pr.sh",
      "workingDirectory": ".",
      "enabled": true
    },
    {
      "event": "PostToolUse", 
      "match": {
        "toolUsed": "Edit",
        "contextContains": "/review"
      },
      "command": "scripts/post-review-cleanup.sh",
      "workingDirectory": ".",
      "enabled": true
    },
    {
      "event": "PreToolUse",
      "match": {
        "pattern": "/integrate",
        "description": "Integration command validation"
      },
      "command": "scripts/validate-integration.sh",
      "workingDirectory": ".",
      "enabled": true
    },
    {
      "event": "PostToolUse",
      "match": {
        "toolUsed": "Bash",
        "commandContains": "git checkout -b"
      },
      "command": "scripts/setup-new-branch.sh", 
      "workingDirectory": ".",
      "enabled": true
    }
  ]
}
```

## Benefits of Hook Implementation

### Reliability
- **Deterministic behavior** vs markdown documentation
- **Proper error handling** with exit codes
- **Validation before execution** prevents bad states

### Automation  
- **Automatic PR detection** for /review
- **Branch validation** for /integrate
- **Post-action cleanup** (formatting, testing)
- **Environment setup** for new branches

### Developer Experience
- **Seamless workflow** with no manual steps
- **Consistent behavior** across team members  
- **Better error messages** and guidance
- **Automatic environment management**

## Implementation Steps

1. **Create scripts directory**: `mkdir -p scripts`
2. **Write hook scripts**: Create the 4 scripts above
3. **Make scripts executable**: `chmod +x scripts/*.sh`
4. **Create hooks configuration**: `.claude/hooks.json`
5. **Test each hook individually**: Verify script behavior
6. **Test integration**: Run full workflow with hooks
7. **Document usage**: Update command documentation
8. **Add to PR**: Include hooks in PR #505 or new PR

## Testing Strategy

### Unit Testing Scripts
```bash
# Test PR detection
./scripts/auto-detect-pr.sh

# Test integration validation  
./scripts/validate-integration.sh

# Test branch setup
./scripts/setup-new-branch.sh
```

### Integration Testing
```bash
# Test full /review workflow
# 1. Create test branch with PR
# 2. Run /review command
# 3. Verify PR auto-detection
# 4. Make changes during review
# 5. Verify post-review cleanup

# Test full /integrate workflow  
# 1. Create feature branch
# 2. Run /integrate customname
# 3. Verify validation and setup
```

## Security Considerations

- **Script permissions**: Ensure scripts are owned by user and not world-writable
- **Input validation**: Sanitize any user input passed to scripts
- **Error handling**: Graceful failure modes that don't break workflow
- **Logging**: Track hook execution for debugging

## Future Enhancements

- **Notification hooks**: Custom notifications for PR status changes
- **Tool-specific hooks**: Different behavior for different file types
- **Context injection**: More sophisticated data passing between hooks and commands
- **Conditional execution**: More complex matching conditions

## Notes

- Hooks execute with full user permissions - be careful!
- Test thoroughly before enabling in production workflow
- Consider gradual rollout (enable one hook at a time)
- Monitor performance impact of hook execution
- Document hook behavior for team members

---

**Status**: Planning phase - ready for implementation
**Next Steps**: Create scripts directory and begin with /review auto-detection hook
**Priority**: High - would significantly improve command reliability and UX