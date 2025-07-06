# TASK-132: GitHub Actions /testi Integration - Requirements & Implementation

## Task Overview
Add automated integration test execution using /testi command on every PR targeting main branch, with full output reporting and artifact collection.

## Autonomous Implementation Requirements

### 1. Create New Workflow File
- **File**: `.github/workflows/integration-tests.yml`
- **Trigger**: Only on pull requests targeting main branch (not on main branch pushes)
- **Status**: Show red X on failure but allow merge (don't block)

### 2. Environment Setup
- **Python**: Activate venv using existing project structure
- **Environment Variables**: Set `TESTING=true`
- **Command**: Use `vpython` script (not direct python)
- **Working Directory**: Run from project root

### 3. Required Secrets
- **Firebase Credentials**: Configure `FIREBASE_SERVICE_ACCOUNT_KEY` secret
- **Gemini API Key**: Configure `GEMINI_API_KEY` secret
- Ensure these are available to the workflow

### 4. Test Execution
- **Command**: `vpython mvp_site/test_integration/test_integration.py`
- **Timeout**: Set reasonable timeout (suggest 10 minutes)
- **Continue on Error**: Yes (show status but don't fail the workflow)

### 5. Output Handling
- **PR Comments**: Add full test output to PR as comment
- **Artifacts**: Upload test logs and any generated files
- **Status**: Report pass/fail status in PR checks

### 6. Integration with Existing Workflows
- **Separate File**: Create as standalone workflow
- **Naming**: Use descriptive name like "Integration Tests"
- **No Conflicts**: Ensure it doesn't interfere with existing actions

## Implementation Details

### Workflow Structure:
```yaml
name: Integration Tests
on:
  pull_request:
    branches: [ main ]
jobs:
  integration-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
      - name: Activate venv and install dependencies
      - name: Run integration tests
      - name: Comment PR with results
      - name: Upload artifacts
```

### Required Components:
1. **Python setup** (version matching project)
2. **Virtual environment** activation
3. **Dependencies** installation
4. **Environment variables** configuration
5. **Test execution** with vpython
6. **Result processing** and commenting
7. **Artifact collection** and upload

## Success Criteria
- [ ] New workflow file created at `.github/workflows/integration-tests.yml`
- [ ] Triggers only on PRs targeting main (not main pushes)
- [ ] Uses vpython command with TESTING=true environment
- [ ] Accesses Firebase and Gemini API credentials
- [ ] Posts full test output as PR comment
- [ ] Uploads test artifacts (logs, generated files)
- [ ] Shows red/green status without blocking merge
- [ ] Integrates cleanly with existing GitHub Actions

## Dependencies
- Existing vpython script functionality
- Firebase service account key in GitHub secrets
- Gemini API key in GitHub secrets
- Project's virtual environment setup

## Estimated Time: 1.5 hours
- Workflow file creation: 45 minutes
- Testing and debugging: 30 minutes
- Documentation: 15 minutes

## Testing Plan
1. Create test PR to verify workflow triggers
2. Confirm environment variables and secrets work
3. Verify test output appears in PR comments
4. Check artifact upload functionality
5. Ensure existing workflows continue working