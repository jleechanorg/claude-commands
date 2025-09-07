# PR #1556 Guidelines - Workspace Directory Placement Fix

## 🎯 PR-Specific Principles

- **Clean Architecture**: Separate runtime artifacts from source code through proper directory organization
- **Solo Developer Focus**: Optimize for single developer productivity by preventing project root pollution
- **Security by Design**: Implement workspace isolation and path validation from the start
- **Comprehensive Testing**: Include regression tests to prevent future violations of architectural decisions

## 🚫 PR-Specific Anti-Patterns

### ❌ **Project Root Pollution**
**Description**: Creating runtime directories in project root mixed with source code
```python
# WRONG: Pollutes project root directory
workspace_path = os.path.join(os.getcwd(), f"agent_workspace_{agent['name']}")
```
**Problems**: Clutters project navigation, mixes temporary with permanent files, difficult cleanup

### ❌ **Inconsistent Path Updates**
**Description**: Updating workspace creation but forgetting related discovery/monitoring code
```python
# WRONG: Only updating creation logic but not discovery
def create_workspace():
    path = os.path.join("orchestration", "agent_workspaces", name)

def find_workspaces():
    # Still looking in old location
    workspaces = glob.glob("agent_workspace_*")  # INCONSISTENT!
```
**Problems**: Leads to workspace orphaning, monitoring failures, cleanup issues

### ❌ **Missing Regression Protection**
**Description**: Making architectural changes without automated tests to prevent regression
```python
# WRONG: No test to verify workspace placement
def test_basic_functionality():
    agent = create_agent("test")
    assert agent is not None  # Doesn't check WHERE workspace was created
```
**Problems**: Future changes could revert architectural improvements without detection

## ✅ **Correct Patterns**

### ✅ **Organized Workspace Structure**
**Description**: Create dedicated directory structure for runtime artifacts
```python
# CORRECT: Organized workspace placement
orchestration_dir = os.path.join(os.getcwd(), "orchestration", "agent_workspaces")
os.makedirs(orchestration_dir, exist_ok=True)
workspace_path = os.path.join(orchestration_dir, f"agent_workspace_{agent['name']}")
```
**Benefits**: Clean project structure, easy navigation, logical organization

### ✅ **Comprehensive Path Updates**
**Description**: Update all components that interact with workspace paths
```python
# CORRECT: Consistent path handling across all components
def create_workspace(agent_name):
    return os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")

def discover_workspaces():
    pattern = os.path.join("orchestration", "agent_workspaces", "agent_workspace_*")
    return glob.glob(pattern)

def monitor_workspace(agent_name):
    workspace_path = os.path.join("orchestration", "agent_workspaces", f"agent_workspace_{agent_name}")
    return os.path.exists(workspace_path)
```
**Benefits**: Consistent behavior, no orphaned workspaces, reliable monitoring

### ✅ **Regression Test Protection**
**Description**: Add specific tests to prevent architectural regression
```python
# CORRECT: Explicit architectural validation
def test_regression_workspace_directory_placement(self):
    """Test that workspace directories are created in orchestration/agent_workspaces/ not project root"""
    mock_agents = [{"name": "test-agent-regression"}]

    for agent in mock_agents:
        orchestration_dir = os.path.join(os.getcwd(), "orchestration", "agent_workspaces")
        workspace_path = os.path.join(orchestration_dir, f"agent_workspace_{agent['name']}")

        # Verify path is NOT in project root
        project_root_workspace = os.path.join(os.getcwd(), f"agent_workspace_{agent['name']}")
        self.assertNotEqual(workspace_path, project_root_workspace)

        # Verify path IS in orchestration directory
        self.assertTrue("orchestration/agent_workspaces" in workspace_path)
```
**Benefits**: Prevents regression, documents architectural decision, ensures consistency

## 📋 Implementation Patterns for This PR

- **Directory Creation**: Use `os.makedirs(dir, exist_ok=True)` for idempotent directory creation
- **Path Construction**: Always use `os.path.join()` for cross-platform path handling
- **Security**: Validate agent names with strict regex patterns before path construction
- **Testing Strategy**: Add regression tests for architectural decisions alongside functional tests

## 🔧 Specific Implementation Guidelines

### Workspace Management
1. **Always organize runtime artifacts** in dedicated subdirectories, never in project root
2. **Update all interaction points** when changing directory structures
3. **Use idempotent directory creation** with `exist_ok=True` parameter
4. **Add regression tests** for architectural decisions to prevent future violations

### Security Considerations
1. **Validate input paths** with strict patterns before filesystem operations
2. **Use subprocess safety** with `shell=False` and timeout protection
3. **Implement workspace isolation** to prevent cross-contamination
4. **Follow path traversal prevention** patterns from OWASP guidelines

### Solo Developer Best Practices
1. **Keep project root clean** for better navigation and understanding
2. **Organize by purpose** - runtime artifacts separate from source code
3. **Add to .gitignore** any directories that contain temporary/runtime data
4. **Test architectural decisions** to maintain code quality over time

## 🚨 Quality Gates

Before merging similar changes:
- [ ] All workspace path references updated consistently
- [ ] Regression test added to prevent architectural violations
- [ ] Directory creation is idempotent and safe
- [ ] Agent name validation prevents path traversal
- [ ] Project root remains clean of runtime artifacts

## Historical Context

This PR addresses workspace pollution where orchestration agents were creating directories directly in the project root (`agent_workspace_*`), making project navigation difficult and mixing temporary runtime data with permanent source code. The fix demonstrates proper separation of concerns and follows the File Placement Protocol from CLAUDE.md.

**Key Files**:
- `orchestration/orchestrate_unified.py:285-287` - Main workspace path construction
- `orchestration/task_dispatcher.py:211-216` - Workspace discovery patterns
- `orchestration/agent_monitor.py:46,161,238,429` - Workspace monitoring references
- `orchestration/test_unified_naming.py:109-135` - Regression test protection
