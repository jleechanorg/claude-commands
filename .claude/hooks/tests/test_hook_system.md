# Hook System Testing Guide

## Next Session Testing Checklist

When you start your next Claude Code session, test these scenarios to verify the anti-demo hook system:

### Test 1: RED - Demo Code Detection
Create a file with placeholder code:
```python
def get_user_profile(user_id):
    # TODO: implement database lookup
    return "demo user data"
```
**Expected**: Anti-demo hook should warn about TODO and demo return value

### Test 2: RED - Multiple Patterns
Create a file with multiple issues:
```python
class DataProcessor:
    def process(self, data):
        # Placeholder implementation
        return {"status": "fake success"}
```
**Expected**: Hook should detect "placeholder" and "fake" patterns

### Test 3: GREEN - Clean Implementation  
Create a proper implementation:
```python
def calculate_tax(amount, rate=0.08):
    if not isinstance(amount, (int, float)) or amount < 0:
        raise ValueError("Amount must be non-negative number")
    return round(amount * rate, 2)
```
**Expected**: No warnings, hook should pass silently

### Test 4: GREEN - Test File Exception
Create a test file (name contains "test"):
```python
# File: test_user_service.py
def test_user_creation():
    mock_data = {"id": 1, "name": "demo user"}
    assert mock_data["name"] == "demo user"
```
**Expected**: Hook should allow demo/mock patterns in test files

### Test 5: Header Hook Verification
After any command, check if response ends with:
```
[Local: <branch> | Remote: <upstream> | PR: <number> <url>]
```
**Expected**: Header should appear at end of every response

## Validation Commands

Check if anti-demo hook logged issues:
```bash
cat /tmp/claude_verify_implementation.txt
```

Verify hooks are active:
```bash
jq '.hooks' ~/.claude/settings.json
```

## Red-Green Testing Protocol

1. **RED Phase**: Write intentionally bad code, verify detection
2. **GREEN Phase**: Write clean code, verify it passes
3. **REFACTOR Phase**: Improve any detected issues

## Success Criteria

✅ Anti-demo hook detects placeholder patterns
✅ Clean code passes without warnings  
✅ Test files are properly excluded
✅ Issues are logged to verification file
✅ Header hook generates branch info consistently
✅ No false positives on legitimate code

## Troubleshooting

If hooks don't trigger:
1. Check settings.json paths are absolute
2. Verify script permissions (`chmod +x`)
3. Restart Claude Code session for settings changes
4. Check for jq installation (`which jq`)