# ⚠️ PROJECT-SPECIFIC PATHS - Requires adaptation for your environment

# HTTP Tests (Mock) Command

**Purpose**: Run HTTP request tests with mock APIs (free)

**Action**: Execute HTTP request tests using requests library with mocked API responses

**Usage**: `/testhttp`

**MANDATORY**: When using `/testhttp` command, follow this exact sequence:

1. **Verify Test Environment**
   ```bash
   vpython -c "import requests" || echo "STOP: requests library not installed"
   ```
   - ✅ Continue only if import succeeds
   - ❌ FULL STOP if not installed

2. **Start Test Server (if needed)**
   ```bash
   TESTING=true PORT=8086 vpython $PROJECT_ROOT/main.py serve &
   sleep 3
   curl -s http://localhost:8086 || echo "Note: Using different port or external server"
   ```
   - ✅ Continue even if local server fails (tests may use different setup)

3. **Run HTTP Test**
   ```bash
   TESTING=true python testing_http/test_name.py
   ```
   - ✅ Report actual HTTP responses/errors
   - ❌ NEVER pretend requests succeeded

**CRITICAL REQUIREMENTS**:
- 🚨 **HTTP requests only** - Must use requests library
- 🚨 **NO browser automation** - This is HTTP testing, not browser testing
- 🚨 **Mock APIs** - Uses mocked external API responses (free)
- ✅ **API endpoint testing** - Direct HTTP calls to test endpoints
- ❌ **NEVER use Playwright** - Use requests.get(), requests.post(), etc.

**Testing Focus**:
- API endpoint responses
- HTTP status codes
- Request/response headers
- JSON payload validation
- Authentication flows via HTTP
