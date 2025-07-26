# Integration Test Command

**Purpose**: Run integration tests

**Action**: Execute integration test suite

**Usage**: `/testi`

**Implementation**:
- Run: `source venv/bin/activate && TESTING=true python3 mvp_site/test_integration/test_integration.py`
- Execute from project root
- Ensure virtual environment is activated
- Use TESTING=true environment variable
- Analyze integration test results
- Fix any integration failures
