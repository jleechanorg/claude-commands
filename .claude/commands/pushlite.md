# Push Lite Command

**Purpose**: Simple push to GitHub without test server or additional automation

**Action**: Push current branch to origin and create PR if requested

**Usage**: 
- `/pushlite` or `/pushl` - Push current branch to origin
- `/pushlite pr` or `/pushl pr` - Push and create PR
- `/pushlite force` or `/pushl force` - Force push to origin

**Examples**:
- `/pushl` - Pushes current branch to origin/branch-name
- `/pushl pr` - Pushes and creates PR to main
- `/pushl force` - Force pushes current branch (use with caution)

**Implementation**:
- Get current branch name with `git branch --show-current`
- Push to origin with `git push origin HEAD:branch-name`
- Optionally create PR with `gh pr create` if `pr` argument provided
- Skip test server management and other automation
- Lightweight alternative to full `/push` command

**Comparison with /push**:
- **`/push`**: Full automation (test server, validation, comprehensive setup)
- **`/pushl`**: Minimal operation (just git push + optional PR creation)

**Use Cases**:
- Quick documentation updates
- Small fixes that don't need full test environment
- When you want manual control over test server management
- Fast iteration during development

**Safety Features**:
- Confirms branch name before pushing
- Shows git status before push
- Reports push success/failure
- Validates remote repository access