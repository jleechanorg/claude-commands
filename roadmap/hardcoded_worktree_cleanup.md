# Hardcoded Worktree Paths Cleanup Plan

## Overview
Found multiple hardcoded worktree paths that need to be replaced with dynamic detection or configuration.

## Files with Hardcoded Paths

### High Priority (Active Code)
1. **run_ui_tests.sh** (lines 187-188, 191)
   - `/path/to/project/worktree_human/mvp_site/start_flask.py`
   - Should use environment variable or dynamic detection

2. **orchestration/recovery_coordinator.py** (line 127)
   - `/path/to/project/worktree_roadmap/agent_workspace_{agent_name}`
   - Should use project root detection

3. **.claude/commands/_copilot_modules/base.py** (line 192)
   - `f"/path/to/project/worktree_human2/{script_path}"`
   - Should use relative paths or environment variables

4. **claude_command_scripts/commands/handoff.sh** (line 119)
   - Documentation referencing specific worktree path
   - Should use template or dynamic examples

5. **tests/test_infrastructure_commands.py** (multiple lines)
   - Multiple hardcoded paths to worktree_worker8
   - Should use test fixtures or environment detection

### Medium Priority (Testing/Debug)
6. **testing_ui/debug_structured_test.py** (lines 8, 22)
   - `/home/jleechan/projects/worldarchitect.ai/worktree_human2`
   - Test file with hardcoded path

### Low Priority (Documentation/Archive)
7. Various scratchpad files with examples
8. HTML test reports with hardcoded venv paths
9. Dotfiles backup with alias

## Recommended Solutions

### 1. Environment Variables
Create standard environment variables:
```bash
export WORLDARCHITECT_PROJECT_ROOT="/home/jleechan/projects/worldarchitect.ai"
export WORLDARCHITECT_CURRENT_WORKTREE="worktree_roadmap"
```

### 2. Dynamic Detection Functions
Add to common utilities:
```python
def get_project_root():
    """Detect project root by looking for CLAUDE.md file"""
    current = os.path.abspath(".")
    while current != "/":
        if os.path.exists(os.path.join(current, "CLAUDE.md")):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("Could not find project root (CLAUDE.md not found)")

def get_worktree_root():
    """Get the current worktree directory"""
    return get_project_root()
```

### 3. Configuration File
Create `.config/paths.json`:
```json
{
    "project_root": "auto-detect",
    "worktree_pattern": "worktree_*",
    "agent_workspace_prefix": "agent_workspace_"
}
```

## Implementation Plan

### Phase 1: Critical Infrastructure
1. Fix `run_ui_tests.sh` - use relative paths or env vars
2. Fix `orchestration/recovery_coordinator.py` - use dynamic detection
3. Fix `.claude/commands/_copilot_modules/base.py` - use relative paths

### Phase 2: Test Infrastructure
1. Fix `tests/test_infrastructure_commands.py` - use test fixtures
2. Update test utilities to use dynamic detection

### Phase 3: Documentation
1. Update handoff.sh documentation
2. Clean up scratchpad references
3. Add path configuration guide

## Benefits
- **Portability**: Code works across different worktrees/systems
- **Maintainability**: No need to update hardcoded paths
- **Testing**: Tests work in any environment
- **CI/CD**: Automated systems can run anywhere
