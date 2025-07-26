# Validation Commands Reference

## Search Commands
```bash
# Search for documented features in prompts
grep -r "__DELETE__" prompts/
grep -r "special_token" prompts/

# Verify implementation exists
grep -r "__DELETE__" *.py
grep -r "process.*special_token" *.py

# Check for dynamic usage
grep -r "json.dumps.*default=" *.py
grep -r "getattr" *.py
```

## Git Commands

### Pre-Push Verification
```bash
git branch --show-current           # Check current branch
git branch -vv                      # Verify branch tracking
git push --dry-run                  # Test push safety
git log main..HEAD --oneline       # Check commits
git diff main...HEAD --name-only   # Verify files
git rev-list --count main..HEAD    # Count commits
```

### Safe Branch Creation
```bash
git checkout main
git pull origin main
git checkout -b feature-branch-name
```

### PR Workflow
```bash
gh pr checkout <PR_NUMBER>          # Apply PR for testing
gh pr create                        # Create new PR
gh pr view [PR_NUMBER] --comments   # View PR comments
```

## Test Commands
```bash
./run_tests.sh                                              # Run all tests
TESTING=true vpython mvp_site/test_file.py                # Run specific test
vpython -m unittest mvp_site.test_module.TestClass.test_method
python3 test_prototype_working.py                          # Prototype tests
```
