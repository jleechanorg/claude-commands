# Testing Guide for WorldArchitect.AI

## Test Structure

Tests are organized into two directories:

### `/tests/` - Unit Tests
- Run automatically in GitHub Actions CI
- Do not require external services
- Use mocks for Firebase and Gemini API calls
- Fast and deterministic
- Run on every PR and push

### `/test_integration/` - Integration Tests
- **Not run in GitHub Actions CI**
- Make real API calls to external services:
  - Google Gemini API
  - Firebase Firestore
- Require proper credentials and setup
- Should be run locally before major releases

## Running Tests

### Unit Tests Only (CI Safe)
```bash
# From mvp_site directory
TESTING=true python -m unittest discover -s tests -p "test_*.py"
```

### Integration Tests Only
```bash
# From mvp_site directory
./run_integration_tests.sh

# Or run individually:
TESTING=true python test_integration/test_live_firestore.py
```

### All Tests (Local Development)
```bash
# Requires proper setup with API keys
source venv/bin/activate
TESTING=true python -m unittest discover
```

## Integration Test Requirements

To run integration tests, you need:

1. **Gemini API Key**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Firebase Service Account**
   - Place `serviceAccountKey.json` in the project root
   - Or set `FIREBASE_SERVICE_ACCOUNT_KEY` environment variable

3. **Python Virtual Environment**
   ```bash
   source venv/bin/activate
   ```

## GitHub Actions

The `.github/workflows/test.yml` workflow:
- Only runs tests in the `/tests/` directory
- Ignores `/test_integration/` completely
- No API credentials needed
- Fast and reliable CI/CD

## Test Exclusion Strategy

### Directory-Based Exclusion
- **Entire `test_integration/` directory** is excluded from CI
- This includes all subdirectories and files within `test_integration/`
- Simplifies maintenance - no need to list individual files

### Integration Test Categories
The `test_integration/` directory contains:
- **Gemini API Tests** - Tests that make real calls to Google Gemini API
- **Firestore API Tests** - Tests that interact with real Firebase Firestore
- **Manual Tests** - Tests requiring specific setup in `manual_tests/` subdirectory
- **Integration Framework** - Support libraries and utilities

## Adding New Tests

### Unit Tests
1. Add to `/tests/` directory
2. Use mocks for external services
3. Will run automatically in CI

### Integration Tests
1. Add to `/test_integration/` directory
2. Document any special requirements
3. Update `run_integration_tests.sh` if needed
4. Will NOT run in CI (intentionally)
