# GitHub Actions CI Setup Guide

This document explains how to set up automated testing with GitHub Actions for the WorldArchitect.AI project.

## Overview

> [!IMPORTANT]
> The legacy directory-based test workflow at `.github/workflows/test.yml` was removed in December 2025 after repeated instability. Current CI coverage relies on targeted workflows such as `.github/workflows/presubmit.yml` (lint/type checks), `.github/workflows/hook-tests.yml`, and `.github/workflows/test-deployment.yml`. The steps below are **kept for reference only** in case we need to reintroduce a general test workflow; do not recreate `test.yml` without team approval.

GitHub Actions will automatically run your test suite whenever you:
- Push code to `main` or `dev` branches
- Create a pull request targeting `main`
- This ensures all code is tested before merging

## Step-by-Step Setup

### Step 1: Create Workflow Directory Structure

If the team approves reintroducing a general test workflow, create this folder structure:

```
.github/
└── workflows/
    └── test.yml
```

### Step 2: Create the Main Workflow File

Create `.github/workflows/test.yml` with this content:

```yaml
name: WorldArchitect Tests

# When to run the tests
on:
  push:
    branches: [ main, dev ]  # Run on pushes to these branches
  pull_request:
    branches: [ main ]       # Run on PRs targeting main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    # Step 1: Get your code
    - name: Checkout repository
      uses: actions/checkout@v4

    # Step 2: Set up Python (same version as your project)
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    # Step 3: Cache dependencies (speeds up future runs)
    - name: Cache pip dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-

    # Step 4: Create virtual environment (matches your local setup)
    - name: Create virtual environment
      run: |
        python -m venv venv
        echo "VIRTUAL_ENV=venv" >> $GITHUB_ENV
        echo "venv/bin" >> $GITHUB_PATH

    # Step 5: Install your dependencies
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r mvp_site/requirements.txt

    # Step 6: Run your tests (using your existing script)
    - name: Run test suite
      run: ./run_tests.sh
      env:
        TESTING: true
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        FIREBASE_SERVICE_ACCOUNT_KEY: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_KEY }}

    # Step 7: Upload test results (optional)
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()  # Run even if tests fail
      with:
        name: test-results
        path: |
          test-results/
          coverage.xml
        retention-days: 30
```

### Step 3: Set Up GitHub Secrets

Your tests need API keys, so store them securely:

1. **Go to your GitHub repository**
2. **Click Settings → Secrets and variables → Actions**
3. **Click "New repository secret"**
4. **Add these secrets**:

```
GEMINI_API_KEY
- Name: GEMINI_API_KEY
- Value: your_actual_gemini_api_key

FIREBASE_SERVICE_ACCOUNT_KEY
- Name: FIREBASE_SERVICE_ACCOUNT_KEY
- Value: your_firebase_service_account_json_content
```

### Step 4: Enhanced Workflow (Optional Features)

For a more advanced setup with additional features:

```yaml
name: WorldArchitect CI/CD

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11']  # Can add ['3.10', '3.11'] to test multiple versions

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/pip
          venv
        key: ${{ runner.os }}-${{ matrix.python-version }}-${{ hashFiles('**/requirements.txt') }}

    - name: Set up virtual environment
      run: |
        python -m venv venv
        source venv/bin/activate
        echo "VIRTUAL_ENV=$(pwd)/venv" >> $GITHUB_ENV
        echo "$(pwd)/venv/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install -r mvp_site/requirements.txt

    # Lint code (optional)
    - name: Lint with flake8
      run: |
        pip install flake8
        flake8 mvp_site/ --count --select=E9,F63,F7,F82 --show-source --statistics
      continue-on-error: true  # Don't fail build on linting issues

    - name: Run tests
      run: ./run_tests.sh
      env:
        TESTING: true
        GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        FIREBASE_SERVICE_ACCOUNT_KEY: ${{ secrets.FIREBASE_SERVICE_ACCOUNT_KEY }}

    # Post test results as PR comment
    - name: Comment PR with test results
      uses: actions/github-script@v6
      if: github.event_name == 'pull_request'
      with:
        script: |
          const { execSync } = require('child_process');
          try {
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ All tests passed successfully!'
            });
          } catch (error) {
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '❌ Tests failed. Check the Actions tab for details.'
            });
          }
```

### Step 5: Commit and Push

> [!NOTE]
> Only follow this step after the team confirms we should add back a general test workflow. Otherwise, rely on the existing presubmit/deployment workflows already in the repo.

```bash
# Create the directory structure
mkdir -p .github/workflows

# Create the workflow file (add the YAML content above)
# Then commit and push (once approved):
git add .github/workflows/test.yml
git commit -m "Add GitHub Actions CI workflow for automated testing"
git push origin main
```

### Step 6: Verify It Works

1. **After pushing, go to your GitHub repo**
2. **Click the "Actions" tab**
3. **You should see your workflow running**
4. **Click on the workflow run to see detailed logs**

### Step 7: Status Badges (Optional)

Add a status badge to your README.md (only if the test workflow above is reintroduced):

```markdown
![Tests](https://github.com/jleechan2015/worldarchitect.ai/workflows/WorldArchitect%20Tests/badge.svg)
```

## What Happens After Setup?

- **Every push** to `main` or `dev` → Tests run automatically
- **Every PR** to `main` → Tests run automatically
- **Test results** show up in the GitHub interface
- **Failed tests** prevent merging (if you enable branch protection)
- **Notifications** sent to you if tests fail

## Branch Protection Rules (Recommended)

To enforce that tests must pass before merging:

1. **Go to GitHub repo → Settings → Branches**
2. **Add rule for `main` branch**
3. **Check "Require status checks to pass"**
4. **Select your GitHub Actions test workflow**

This prevents anyone from merging code that breaks tests.

## Troubleshooting Common Issues

### Tests fail in CI but work locally:
- Check that all dependencies are in `requirements.txt`
- Verify environment variables are set correctly
- Make sure your `run_tests.sh` script is executable

### Secrets aren't working:
- Double-check secret names match exactly
- Verify the secret values are correct
- Check for extra spaces or characters

### Virtual environment issues:
- Ensure venv creation and activation commands are correct
- Check that Python version matches your local setup

### Integration test failures:
- Verify API keys are valid and have correct permissions
- Check if rate limits are being hit
- Ensure test data doesn't conflict between parallel runs

## Advanced Features

### Matrix Testing
Test against multiple Python versions:
```yaml
strategy:
  matrix:
    python-version: ['3.10', '3.11', '3.12']
```

### Conditional Jobs
Skip tests for documentation-only changes:
```yaml
- name: Check for code changes
  id: changes
  uses: dorny/paths-filter@v2
  with:
    filters: |
      code:
        - 'mvp_site/**'
        - 'requirements.txt'
```

### Performance Monitoring
Track test execution time:
```yaml
- name: Upload performance data
  uses: benchmark-action/github-action-benchmark@v1
  with:
    tool: 'pytest'
    output-file-path: benchmark.json
```

## Integration with Development Workflow

### Pre-push Hooks (Optional Local Setup)
Create `.git/hooks/pre-push`:
```bash
#!/bin/bash
echo "Running tests before push..."
./run_tests.sh
if [ $? -ne 0 ]; then
    echo "Tests failed! Push aborted."
    exit 1
fi
```

### Notification Setup
Configure notifications in GitHub Settings → Notifications to get alerts when builds fail.

## Maintenance

### Regular Updates
- Update action versions quarterly (e.g., `actions/checkout@v4` → `actions/checkout@v5`)
- Review and update Python versions annually
- Monitor GitHub Actions usage limits

### Security
- Rotate secrets annually
- Review workflow permissions
- Keep dependencies updated

---

## Quick Reference Commands

```bash
# Create workflow directory
mkdir -p .github/workflows

# Check workflow syntax
gh workflow validate .github/workflows/test.yml

# List recent workflow runs
gh run list

# View specific run details
gh run view [run-id]

# Re-run failed workflows
gh run rerun [run-id]
```
