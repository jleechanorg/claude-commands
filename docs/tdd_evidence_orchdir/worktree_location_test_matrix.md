# Worktree Location Test Matrix - All Scenario Combinations

## **Matrix 1: Repository Context × Location Calculation (Core Functionality)**

| Repository Type | Repository Name | Expected Base Path | Expected Agent Dir | Notes |
|---|---|---|---|---|
| **GitHub SSH Remote** | worldarchitect.ai | ~/projects/orch_worldarchitect.ai/ | ~/projects/orch_worldarchitect.ai/task-agent-xyz | Extract from git@github.com:user/repo.git |
| **GitHub HTTPS Remote** | my-project | ~/projects/orch_my-project/ | ~/projects/orch_my-project/tmux-pr123 | Extract from https://github.com/user/repo.git |
| **Local Repository** | local-repo | ~/projects/orch_local-repo/ | ~/projects/orch_local-repo/agent_workspace_test | No remote origin case |
| **Complex Repo Name** | my.complex-repo_name | ~/projects/orch_my.complex-repo_name/ | ~/projects/orch_my.complex-repo_name/task-agent-feature | Handle special characters |
| **No Git Repository** | N/A | ERROR | ERROR | Should fail gracefully |

## **Matrix 2: Workspace Configuration × Custom Naming**

| Workspace Config | Custom Name | Custom Root | Expected Result | Behavior |
|---|---|---|---|---|
| **None** | None | None | ~/projects/orch_{repo}/agent-name | Default behavior |
| **Custom Name Only** | tmux-pr123 | None | ~/projects/orch_{repo}/tmux-pr123 | Use custom name in default root |
| **Custom Root Only** | None | /tmp/.worktrees | /tmp/.worktrees/agent-name | Use custom root with default name |
| **Both Custom** | tmux-pr456 | ~/.cache/worktrees | ~/.cache/worktrees/tmux-pr456 | Override both name and location |
| **Relative Root** | None | .worktrees | {current_dir}/.worktrees/agent-name | Relative path handling |

## **Matrix 3: Git Operations × Repository States**

| Git State | Operation | Expected Behavior | Error Handling |
|---|---|---|---|
| **Clean Main** | git worktree add | Success with new location | Standard git worktree creation |
| **Dirty Working Tree** | git worktree add | Success (worktree unaffected) | Continue despite local changes |
| **Branch Exists** | git worktree add -b existing | Error from git | Propagate git error |
| **No Main Branch** | git worktree add main | Error from git | Fallback to default branch |
| **No Git Repository** | git worktree add | Error | Return early with error |

## **Matrix 4: Edge Cases × Path Handling**

| Edge Case | Input | Expected Output | Validation |
|---|---|---|---|
| **Path Expansion** | ~/projects/orch_repo | /Users/user/projects/orch_repo | Expand tilde properly |
| **Path Creation** | Non-existent dirs | Create parent directories | mkdir -p behavior |
| **Permission Issues** | Read-only parent | Error gracefully | Check permissions |
| **Long Paths** | Very long repo names | Truncate or handle | Path length limits |
| **Special Characters** | Repo with spaces/symbols | Sanitize path components | Safe filesystem names |

## **Matrix 5: Agent Types × Workspace Patterns**

| Agent Type | Naming Pattern | Expected Directory | Integration |
|---|---|---|---|
| **task-agent** | task-agent-{task} | ~/projects/orch_repo/task-agent-implement-auth | Standard task agents |
| **tmux-pr** | tmux-pr{number} | ~/projects/orch_repo/tmux-pr123 | PR-specific agents |
| **custom-name** | user-specified | ~/projects/orch_repo/custom-name | User-provided names |
| **agent_workspace** | agent_workspace_* | ~/projects/orch_repo/agent_workspace_test | Legacy pattern support |
| **collision-name** | duplicate-name-2 | ~/projects/orch_repo/duplicate-name-2 | Handle name conflicts |

## **Total Matrix Tests**: 45 systematic test cases covering all worktree location scenarios

### **Test Categories:**
- **Repository Detection**: 5 tests for different repo types and remote configurations
- **Workspace Configuration**: 5 tests for custom naming and root path options
- **Git Operations**: 5 tests for different git repository states
- **Edge Cases**: 5 tests for path handling and error conditions
- **Agent Integration**: 5 tests for different agent naming patterns

### **Coverage Requirements:**
- ✅ All git remote URL formats (SSH, HTTPS, local)
- ✅ All workspace configuration combinations
- ✅ All error conditions and edge cases
- ✅ All agent naming patterns
- ✅ Directory creation and permission handling

### **Expected Outcomes:**
- **Repository Name Extraction**: Correctly parse repo name from various git remote formats
- **Path Construction**: Build proper ~/projects/orch_{repo}/ base paths
- **Directory Management**: Create parent directories as needed
- **Error Handling**: Graceful failures with informative messages
- **Integration**: Seamless compatibility with existing agent workflows

### **Validation Criteria:**
- All tests must FAIL initially (RED phase)
- Implementation makes tests pass incrementally (GREEN phase)
- Refactoring maintains all test coverage (REFACTOR phase)
- No regression in existing worktree functionality
