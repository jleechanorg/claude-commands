# Playwright Implementation Guide for WorldArchitect.AI

## Quick Start Implementation

### 1. Installation & Setup (5 minutes)

```bash
# Add to requirements.txt
echo "pytest-playwright" >> mvp_site/requirements.txt

# Install dependencies
source venv/bin/activate
pip install pytest-playwright
playwright install
```

### 2. Directory Structure (2 minutes)

```bash
# Create test directory structure
mkdir -p tests/playwright/{config,tests,fixtures,utils}
mkdir -p tests/playwright/tests/{auth,campaigns,characters,game_sessions}
mkdir -p tests/playwright/results/{traces,screenshots,videos}
```

### 3. Basic Configuration (3 minutes)

**File: `tests/playwright/config/playwright.config.py`**
```python
import os
from pathlib import Path

# Base configuration
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
TIMEOUT = 30000
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

# Test configuration
PLAYWRIGHT_CONFIG = {
    "base_url": BASE_URL,
    "timeout": TIMEOUT,
    "headless": HEADLESS,
    "viewport": {"width": 1280, "height": 720},
    "browsers": ["chromium", "firefox", "webkit"],
    "screenshot": "only-on-failure",
    "video": "retain-on-failure",
    "trace": True
}

# Selectors (update based on actual DOM)
SELECTORS = {
    "auth": {
        "login_button": "[data-testid='login-button']",
        "user_email": "#user-email"
    },
    "campaign": {
        "create_button": "[data-testid='create-campaign']",
        "campaign_list": "[data-testid='campaign-list']"
    }
}
```

### 4. First Test - Homepage (5 minutes)

**File: `tests/playwright/tests/test_homepage.py`**
```python
import pytest
from playwright.sync_api import Page, expect

def test_homepage_loads(page: Page):
    """Test that the homepage loads correctly."""
    page.goto("/")
    
    # Check page title
    expect(page).to_have_title("WorldArchitect.AI")
    
    # Check main navigation
    expect(page.locator("nav.navbar")).to_be_visible()
    expect(page.locator(".navbar-brand")).to_contain_text("WorldArchitect")

def test_homepage_performance(page: Page):
    """Test homepage performance metrics."""
    import time
    
    start_time = time.time()
    page.goto("/")
    load_time = (time.time() - start_time) * 1000
    
    # Performance assertions
    assert load_time < 3000, f"Page load too slow: {load_time}ms"
    
    # Check for essential elements
    expect(page.locator("body")).to_be_visible()
```

### 5. Pytest Configuration (2 minutes)

**File: `tests/playwright/pytest.ini`**
```ini
[pytest]
testpaths = tests/playwright
addopts = 
    --browser chromium
    --browser firefox
    --headless
    --video=retain-on-failure
    --screenshot=only-on-failure
    --output=tests/playwright/results

base_url = http://localhost:5000
```

### 6. Running Tests (1 minute)

```bash
# Run all Playwright tests
pytest tests/playwright/

# Run specific test
pytest tests/playwright/tests/test_homepage.py

# Run with specific browser
pytest tests/playwright/ --browser firefox

# Run with headed mode (see browser)
pytest tests/playwright/ --headed
```

## Advanced Implementation

### 1. Authentication Testing

**File: `tests/playwright/tests/auth/test_authentication.py`**
```python
import pytest
from playwright.sync_api import Page, expect

class TestAuthentication:
    
    def test_login_flow(self, page: Page):
        """Test complete login flow."""
        page.goto("/")
        
        # Click login button
        page.locator("[data-testid='login-button']").click()
        
        # Wait for authentication redirect/modal
        # Add specific authentication logic based on your implementation
        
        # Verify successful login
        expect(page.locator("#user-email")).to_be_visible()
    
    def test_logout_flow(self, page: Page):
        """Test logout functionality."""
        # Assume user is logged in
        page.goto("/")
        
        # Perform logout
        page.locator("[data-testid='logout-button']").click()
        
        # Verify logout
        expect(page.locator("[data-testid='login-button']")).to_be_visible()
```

### 2. Campaign Management Testing

**File: `tests/playwright/tests/campaigns/test_campaign_management.py`**
```python
import pytest
from playwright.sync_api import Page, expect

class TestCampaignManagement:
    
    def test_create_campaign(self, page: Page):
        """Test campaign creation flow."""
        page.goto("/")
        
        # Navigate to campaign creation
        page.locator("[data-testid='create-campaign']").click()
        
        # Fill campaign form
        page.fill("[data-testid='campaign-name']", "Test Campaign")
        page.fill("[data-testid='campaign-description']", "Test Description")
        
        # Submit form
        page.locator("[data-testid='submit-campaign']").click()
        
        # Verify campaign creation
        expect(page.locator("[data-testid='campaign-list']")).to_contain_text("Test Campaign")
    
    def test_campaign_deletion(self, page: Page):
        """Test campaign deletion."""
        page.goto("/")
        
        # Assuming campaign exists
        page.locator("[data-testid='delete-campaign']").first.click()
        
        # Confirm deletion
        page.locator("[data-testid='confirm-delete']").click()
        
        # Verify deletion
        expect(page.locator("[data-testid='campaign-list']")).not_to_contain_text("Test Campaign")
```

### 3. Game Session Testing

**File: `tests/playwright/tests/game_sessions/test_game_interaction.py`**
```python
import pytest
from playwright.sync_api import Page, expect

class TestGameInteraction:
    
    def test_send_message(self, page: Page):
        """Test sending a message in game session."""
        page.goto("/game/[campaign_id]")
        
        # Send message
        page.fill("[data-testid='chat-input']", "Hello, world!")
        page.locator("[data-testid='send-message']").click()
        
        # Verify message sent
        expect(page.locator("[data-testid='chat-messages']")).to_contain_text("Hello, world!")
    
    def test_ai_response(self, page: Page):
        """Test AI response to user input."""
        page.goto("/game/[campaign_id]")
        
        # Send message
        page.fill("[data-testid='chat-input']", "I want to explore the forest")
        page.locator("[data-testid='send-message']").click()
        
        # Wait for AI response (with timeout)
        page.wait_for_selector("[data-testid='ai-response']", timeout=10000)
        
        # Verify AI response
        expect(page.locator("[data-testid='ai-response']")).to_be_visible()
```

### 4. Cross-Browser Testing

**File: `tests/playwright/tests/test_cross_browser.py`**
```python
import pytest
from playwright.sync_api import Page, expect

@pytest.mark.parametrize("browser_name", ["chromium", "firefox", "webkit"])
def test_cross_browser_compatibility(page: Page, browser_name: str):
    """Test compatibility across different browsers."""
    page.goto("/")
    
    # Basic functionality tests
    expect(page).to_have_title("WorldArchitect.AI")
    expect(page.locator("nav.navbar")).to_be_visible()
    
    # Take screenshot for visual comparison
    page.screenshot(path=f"tests/playwright/results/screenshots/{browser_name}_homepage.png")
```

### 5. Performance Testing

**File: `tests/playwright/tests/test_performance.py`**
```python
import pytest
from playwright.sync_api import Page, expect
import time

class TestPerformance:
    
    def test_page_load_performance(self, page: Page):
        """Test page load performance."""
        start_time = time.time()
        page.goto("/")
        load_time = (time.time() - start_time) * 1000
        
        # Performance assertions
        assert load_time < 3000, f"Page load too slow: {load_time}ms"
        
        # Check for performance metrics
        page.evaluate("""
            () => {
                const perfData = performance.getEntriesByType('navigation')[0];
                window.loadTime = perfData.loadEventEnd - perfData.loadEventStart;
            }
        """)
        
        load_time_js = page.evaluate("window.loadTime")
        assert load_time_js < 2000, f"DOM load too slow: {load_time_js}ms"
    
    def test_api_response_time(self, page: Page):
        """Test API response times."""
        # Monitor network requests
        api_responses = []
        
        def handle_response(response):
            if "/api/" in response.url:
                api_responses.append({
                    "url": response.url,
                    "status": response.status,
                    "time": response.request.timing
                })
        
        page.on("response", handle_response)
        page.goto("/")
        
        # Wait for API calls
        page.wait_for_timeout(2000)
        
        # Check API response times
        for response in api_responses:
            # Assuming timing is available
            assert response["status"] < 400, f"API error: {response['url']}"
```

## CI/CD Integration

### GitHub Actions Configuration

**File: `.github/workflows/playwright.yml`**
```yaml
name: Playwright Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        playwright install --with-deps
    
    - name: Start Flask application
      run: |
        python mvp_site/main.py &
        sleep 5
    
    - name: Run Playwright tests
      run: |
        pytest tests/playwright/ --browser=chromium --browser=firefox
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: tests/playwright/results/
```

## Best Practices

### 1. Selector Strategy
- Use `data-testid` attributes for stable selectors
- Avoid CSS selectors that may change
- Use semantic HTML attributes when possible

### 2. Test Data Management
- Use fixtures for test data
- Clean up test data after tests
- Use isolated test environments

### 3. Error Handling
- Add proper waits for async operations
- Handle flaky tests with retries
- Capture screenshots/videos on failures

### 4. Performance Optimization
- Run tests in parallel
- Use headed mode only for debugging
- Optimize test execution order

## Integration with Existing Tests

### 1. Test Organization
```
tests/
├── unit/              # Existing unit tests
├── integration/       # Existing integration tests
├── playwright/        # New Playwright tests
│   ├── e2e/          # End-to-end tests
│   ├── visual/       # Visual regression tests
│   └── performance/  # Performance tests
└── fixtures/         # Shared test fixtures
```

### 2. Test Runner Integration
```bash
# Run all tests
./run_tests.sh --include-playwright

# Run only Playwright tests
./run_tests.sh --playwright-only

# Run critical path tests
./run_tests.sh --smoke-tests
```

### 3. Reporting Integration
- Integrate with existing test reporting
- Add Playwright results to CI/CD pipeline
- Create combined test reports

## Next Steps

1. **Week 1**: Install and configure Playwright
2. **Week 2**: Implement core flow tests
3. **Week 3**: Add cross-browser testing
4. **Week 4**: Integrate with CI/CD
5. **Week 5**: Add performance and accessibility tests
6. **Week 6**: Team training and documentation

## Support Resources

- **Documentation**: https://playwright.dev/python/
- **Examples**: https://github.com/microsoft/playwright-python/tree/main/examples
- **Community**: https://github.com/microsoft/playwright/discussions
- **Training**: Internal team training sessions

---

**Implementation Time**: 2-3 weeks  
**Team Training**: 1 week  
**Maintenance**: Ongoing  
**ROI**: High (improved quality, faster development)