# Test Credentials Management Guide

## Overview
This guide explains how to securely manage test credentials for WorldArchitect.AI browser testing.

## Credential Storage Options

### 1. Environment Variables (Current Session)
```bash
export TEST_EMAIL="your-test-email@example.com"
export TEST_PASSWORD="your-test-password"
```

### 2. .bashrc File (Persistent)
Add to `~/.bashrc`:
```bash
export TEST_EMAIL="your-test-email@example.com"
export TEST_PASSWORD="your-test-password"
```

### 3. Secure Config File (Recommended)
Create `~/.config/worldarchitect-ai/test-credentials.env`:
```bash
TEST_EMAIL=your-test-email@example.com
TEST_PASSWORD=your-test-password
```

Set proper permissions:
```bash
chmod 600 ~/.config/worldarchitect-ai/test-credentials.env
```

## Using the Credential Loader

### Direct Loading
```bash
# Load credentials into current shell
source testing_llm/load-test-credentials.sh

# Verify credentials are loaded
echo $TEST_EMAIL
```

### Running Tests with Authentication
```bash
# Use the wrapper script for browser tests
./testing_llm/run-browser-test-with-auth.sh /testuif

# Or with other test commands
./testing_llm/run-browser-test-with-auth.sh ./run_ui_tests.sh mock
```

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use test accounts only** - never use production credentials
3. **Rotate credentials regularly** - update test passwords periodically
4. **Restrict file permissions** - use `chmod 600` for credential files
5. **Use environment variables** in CI/CD pipelines

## Troubleshooting

### Credentials Not Loading
1. Check if variables are exported (not just set)
2. Verify file permissions on credential files
3. Ensure no typos in variable names
4. Try sourcing .bashrc manually: `source ~/.bashrc`

### Authentication Failures
1. Verify credentials are correct
2. Check if test account is active
3. Ensure no special characters need escaping
4. Test manual login in browser first

## Current Setup Status
✅ Credentials found in ~/.bashrc
✅ Credential loader script created
✅ Test wrapper script available
✅ Security best practices documented
