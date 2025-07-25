# Push Command

**Purpose**: Pre-push review, validation, PR update, and test server startup

**Action**: Virtual agent review → push if clean → update PR desc → start test server

**Usage**: `/push`

**Implementation**:
- Check for untracked files
- If untracked files exist, offer to include them:
  - Analyze if they're related to current PR work
  - Suggest adding test files, docs, or supporting scripts
  - Allow selection of files to include
- Perform virtual agent review of changes
- Check for code quality issues
- Verify tests pass
- Validate commit messages
- Push to remote only if all checks pass
- Create PR if needed
- **Update PR description if significant changes detected**
- Start test server on available port for this branch
- Display server URL for immediate testing

**PR Description Auto-Update**:
- Analyzes commit messages since PR creation
- Detects significant scope changes:
  - Architecture migrations (e.g., string → JSON)
  - New test protocols or policies
  - Breaking changes
  - Major feature additions
- Updates PR description to reflect current state
- Preserves test results and adds new ones
- Includes breaking change warnings if applicable

**Test Server Integration**:
- Automatically starts test server after successful push
- Uses branch-specific port allocation (6006+)
- Server accessible at http://localhost:[port]
- Logs stored in /tmp/worldarchitectai_logs/[branch].log
- Server can be stopped with `/integrate` or manually

**Untracked Files Handling**:
- Intelligently detects untracked files
- Analyzes file context:
  - Test files matching PR work (e.g., test_*.py, test_*.js)
  - Documentation updates related to changes
  - Supporting scripts or utilities
  - Temporary or debug files to ignore
- Interactive options:
  1. **Add all relevant** - Add files that appear related to PR
  2. **Select specific** - Choose individual files
  3. **Skip** - Continue without adding
  4. **Abort** - Cancel push to review files
- Auto-suggests commit messages:
  - "Add JavaScript unit tests for [feature]"
  - "Add browser tests for [functionality]"
  - "Add supporting test utilities"
- Remembers choices for similar files in future
