# /replicate

Analyze a GitHub PR and intelligently apply its missing functionality to the current branch.

## Usage
```
/replicate <PR_URL or PR_NUMBER>
```

## Examples
- `/replicate https://github.com/jleechanorg/worldarchitect.ai/pull/693`
- `/replicate PR#693`
- `/replicate 693`

## Description

The `/replicate` command automates the process of analyzing a pull request and replicating its functionality to your current branch. This is particularly useful when:
- You need to incorporate features from another PR
- You want to ensure feature parity with a reference implementation
- You're consolidating work from multiple branches

## How It Works

### 1. PR Analysis Phase
- Parses the PR URL/number to identify the repository and PR
- **🚨 MANDATORY PAGINATION PROTOCOL**: Checks total file count first using GitHub MCP tools
- Uses GitHub MCP tools to fetch complete file changes with pagination verification
- **Verification**: Ensures ALL files are analyzed, not just first 30 from API default
- Reads every single delta line (additions and deletions)
- Focuses on relevant directories (configurable)

### 2. Comparison Phase
- Compares PR changes with current branch implementation
- Identifies missing functionality, methods, or improvements
- Categorizes changes by importance and relevance
- Detects potential conflicts or overlaps

### 3. Smart Merge Phase
- Applies missing changes that enhance functionality
- Skips irrelevant changes (unrelated cleanup, different approaches)
- Maintains current enhancements and improvements
- Preserves existing functionality while adding new features
- Handles conflicts intelligently

### 4. Validation Phase
- Verifies changes don't break existing functionality
- Runs available tests to ensure stability
- Generates detailed summary of what was replicated
- Creates descriptive commit with comprehensive change log

## Features

- **Intelligent Analysis**: Uses `/e` for thorough PR examination
- **Selective Application**: Only applies relevant improvements
- **Conflict Resolution**: Smart handling of overlapping changes
- **Comprehensive Reporting**: Detailed logs of what was replicated and why
- **Safety First**: Preserves existing functionality and enhancements

## Options

- **Focus Directories**: Specify which directories to analyze (e.g., `.claude/commands/`)
- **Exclude Patterns**: Skip certain file patterns or changes
- **Dry Run Mode**: Preview changes without applying them
- **Force Mode**: Apply changes even with conflicts (requires manual resolution)

## Implementation Details

The command leverages:
- **GitHub MCP integration for PR data fetching with mandatory pagination protocols**
- **🚨 CRITICAL**: Always verifies total file count before analysis to prevent missing files
- **Pagination handling**: Automatically detects large PRs and uses appropriate API pagination
- Advanced diff analysis algorithms
- Subagent orchestration for complex comparisons
- AST-based code understanding where applicable
- Smart merge strategies to avoid conflicts

## Success Stories

Originally developed after manually analyzing PR #693, this command automates what was a complex manual process. It has proven effective for:
- Feature consolidation across branches
- Ensuring implementation completeness
- Rapid feature adoption from other developers
- Maintaining consistency across similar implementations

## Error Handling

- **Invalid PR**: Clear error if PR doesn't exist or is inaccessible
- **Merge Conflicts**: Detailed conflict reports with resolution suggestions
- **Test Failures**: Automatic rollback option if tests fail post-merge
- **Network Issues**: Graceful handling of API failures with retry logic

## Best Practices

1. Always run on a clean working tree
2. Review the replication summary before committing
3. Run tests after replication to ensure stability
4. Use focus directories for large PRs to avoid noise
5. Consider dry run mode for complex PRs first

## Related Commands

- `/pr` - Create or manage pull requests
- `/review` - Review code changes
- `/integrate` - Integrate changes from main branch
