# Example: Push Command with Untracked Files

When you have untracked files and run `/push` or `/pushl`, here's what happens:

## Scenario 1: Test files created during PR work

```
$ /push

🔍 Checking for untracked files...

Found 2 untracked files:
  📄 test_collapsible_browser.py
  📄 test_ui_mock_verification.py

These appear to be test files related to your current PR work.

What would you like to do?
  1. Add all files and commit them
  2. Select specific files to add
  3. Continue without adding (push existing commits only)
  4. Cancel push operation

Your choice: 1

✅ Adding all untracked files...
Suggested commit message: "Add browser tests for collapsible description functionality"

Proceed with this commit message? (y/n/edit): y

✅ Files committed successfully
🚀 Continuing with push...
```

## Scenario 2: Mixed untracked files

```
$ /pushl

🔍 Checking for untracked files...

Found 4 untracked files:
  📄 test_collapsible_description.js    [TEST - Related to PR]
  📄 mvp_site/tests/test_ui_helpers.py   [TEST - Related to PR]
  📄 debug_output.log                    [TEMP - Likely temporary]
  📄 .env.local                          [CONFIG - Local config]

Smart analysis suggests:
- 2 files appear related to your PR (test files)
- 2 files appear to be local/temporary

What would you like to do?
  1. Add suggested files (test files only)
  2. Select specific files to add
  3. Continue without adding any files
  4. Cancel push operation

Your choice: 1

✅ Adding suggested files:
  - test_collapsible_description.js
  - mvp_site/tests/test_ui_helpers.py

Commit message: "Add unit tests for collapsible description feature"

✅ Files committed and pushed successfully!
```

## Benefits

1. **No Lost Work**: Test files created during PR development are offered for inclusion
2. **Smart Detection**: Recognizes patterns like test_*.py, test_*.js as likely PR-related
3. **Clean Commits**: Suggests appropriate commit messages based on file types
4. **Flexibility**: Can add all, select specific, or skip entirely
5. **Safety**: Option to cancel if you need to review files first