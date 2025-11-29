# Browser Test Framework Critical Fixes Plan

## 🚨 CRITICAL ISSUES IDENTIFIED

### Current Blockers
1. **IMPOSSIBLE PARALLEL EXECUTION**: All tests use port 6006 simultaneously
2. **DANGEROUS PROCESS KILLING**: Kills arbitrary processes matching patterns
3. **FAKE MOCK SUPPORT**: USE_MOCKS environment variable not implemented
4. **RESOURCE CONFLICTS**: Tests contaminate each other's data/processes

## 🎯 STRATEGIC APPROACH

### Phase 1: Foundation Fixes (Priority: CRITICAL)
**Estimated Time**: 1-2 days
**Goal**: Make tests safe and actually parallel

#### 1.1 Dynamic Port Allocation
**Problem**: All tests hardcoded to port 6006
**Solution**: Implement dynamic port assignment

```python
# browser_test_base.py changes needed
class FlaskServerManager:
    def __init__(self):
        self.port = self._find_free_port()
        self.process = None
        self.log_file = f"/tmp/test_server_{self.port}.log"

    def _find_free_port(self):
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
```

#### 1.2 Safe Process Management
**Problem**: Dangerous psutil.kill() on pattern matching
**Solution**: Process ownership tracking

```python
class SafeProcessManager:
    def __init__(self):
        self.owned_processes = []
        self.port = None

    def start_server(self):
        # Only kill processes we own
        for proc in self.owned_processes:
            if proc.is_running():
                proc.terminate()

        # Use subprocess.Popen with process group
        self.process = subprocess.Popen(
            [...],
            preexec_fn=os.setsid  # Create new process group
        )
        self.owned_processes.append(self.process)
```

#### 1.3 Test Isolation
**Problem**: Tests share TEST_USER_ID and contaminate data
**Solution**: Unique test identifiers

```python
class BrowserTestBase:
    def __init__(self, test_name: str):
        self.test_id = f"test_{int(time.time())}_{random.randint(1000,9999)}"
        self.test_user_id = f"browser-test-{self.test_id}"
        self.screenshot_dir = f"/tmp/worldarchitectai/browser/{self.test_id}"
```

### Phase 2: Mock/Real API Architecture (Priority: HIGH)
**Estimated Time**: 2-3 days
**Goal**: Implement true mock support while preserving real API functionality

#### 2.1 Mock Service Implementation
**Current**: USE_MOCKS does nothing
**Solution**: Implement actual mock services

```python
# mvp_site/mocks/mock_manager.py
class MockManager:
    def __init__(self):
        self.use_mocks = os.environ.get('USE_MOCKS', 'false').lower() == 'true'

    def get_firestore_service(self):
        if self.use_mocks:
            return MockFirestoreService()
        return FirestoreService()

    def get_llm_service(self):
        if self.use_mocks:
            return MockLLMService()
        return LLMService()
```

#### 2.2 Service Injection Pattern
**Problem**: Hard-coded service instantiation
**Solution**: Dependency injection

```python
# mvp_site/main.py modifications
def create_app(use_mocks=None):
    app = Flask(__name__)

    if use_mocks is None:
        use_mocks = os.environ.get('USE_MOCKS', 'false').lower() == 'true'

    if use_mocks:
        app.config['FIRESTORE_SERVICE'] = MockFirestoreService()
        app.config['GEMINI_SERVICE'] = MockGeminiService()
    else:
        app.config['FIRESTORE_SERVICE'] = FirestoreService()
        app.config['GEMINI_SERVICE'] = GeminiService()
```

#### 2.3 Mock Data Consistency
**Problem**: Mock responses are unpredictable
**Solution**: Deterministic mock data

```python
# mocks/mock_data.py
MOCK_CAMPAIGN_TEMPLATES = {
    "god_mode_test": {
        "story": "The gods watch from above...",
        "world_state": {"weather": "stormy"},
        "characters": [{"name": "Test Hero", "hp": 100}]
    }
}
```

### Phase 3: Resource Management & Cleanup (Priority: HIGH)
**Estimated Time**: 1-2 days
**Goal**: Prevent resource leaks and data contamination

#### 3.1 Comprehensive Cleanup
**Problem**: No cleanup of test data
**Solution**: Automated cleanup system

```python
class TestDataManager:
    def __init__(self, test_id: str):
        self.test_id = test_id
        self.created_campaigns = []
        self.created_files = []

    def track_campaign(self, campaign_id: str):
        self.created_campaigns.append(campaign_id)

    def cleanup(self):
        # Clean Firebase
        for campaign_id in self.created_campaigns:
            firestore_service.delete_campaign(campaign_id)

        # Clean files
        for file_path in self.created_files:
            if os.path.exists(file_path):
                os.remove(file_path)
```

#### 3.2 Browser Resource Management
**Problem**: Browser processes may leak
**Solution**: Proper lifecycle management

```python
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.contexts = []

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for context in self.contexts:
            context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
```

### Phase 4: Parallel Execution Orchestration (Priority: MEDIUM)
**Estimated Time**: 2-3 days
**Goal**: True parallel execution with proper coordination

#### 4.1 Test Queue Management
**Problem**: Uncontrolled parallel execution
**Solution**: Managed test queue with resource limits

```python
# test_orchestrator.py
class TestOrchestrator:
    def __init__(self, max_concurrent=3):
        self.max_concurrent = max_concurrent
        self.running_tests = {}
        self.available_ports = queue.Queue()

    def initialize_port_pool(self):
        for _ in range(self.max_concurrent):
            port = self._find_free_port()
            self.available_ports.put(port)

    async def run_test(self, test_class):
        port = await self.available_ports.get()
        try:
            result = await self._execute_test(test_class, port)
            return result
        finally:
            self.available_ports.put(port)
```

#### 4.2 Resource Throttling
**Problem**: Resource exhaustion with 10 simultaneous tests
**Solution**: Intelligent resource management

```python
class ResourceManager:
    def __init__(self):
        self.max_browsers = 3  # Limit browser instances
        self.max_servers = 3   # Limit server instances
        self.semaphore_browser = asyncio.Semaphore(self.max_browsers)
        self.semaphore_server = asyncio.Semaphore(self.max_servers)
```

### Phase 5: Enhanced Error Handling & Monitoring (Priority: MEDIUM)
**Estimated Time**: 1-2 days
**Goal**: Robust error handling and observability

#### 5.1 Comprehensive Error Handling
```python
class TestExecutionContext:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.errors = []
        self.screenshots = []

    def handle_error(self, error: Exception, context: str):
        self.errors.append({
            'error': str(error),
            'context': context,
            'timestamp': time.time(),
            'screenshot': self.take_error_screenshot()
        })
```

#### 5.2 Test Metrics & Reporting
```python
class TestMetrics:
    def collect_metrics(self):
        return {
            'execution_time': self.end_time - self.start_time,
            'api_calls_made': len(self.api_calls),
            'screenshots_taken': len(self.screenshots),
            'errors_encountered': len(self.errors)
        }
```

## 🔧 IMPLEMENTATION STRATEGY

### Execution Order (Critical Path)
1. **IMMEDIATE (Day 1)**:
   - Fix dynamic port allocation
   - Implement safe process management
   - Add test isolation

2. **SHORT TERM (Days 2-3)**:
   - Implement mock services
   - Add service injection
   - Create resource cleanup

3. **MEDIUM TERM (Days 4-7)**:
   - Build test orchestration
   - Add comprehensive error handling
   - Implement monitoring

### Risk Mitigation
- **Backward Compatibility**: Keep existing test interfaces
- **Incremental Rollout**: Test fixes with single test first
- **Real API Preservation**: Never compromise real API functionality
- **Developer Experience**: Maintain simple command-line interface

## 🎯 ACCEPTANCE CRITERIA

### Must Have (MVP)
- ✅ True parallel execution (tests don't interfere)
- ✅ Real Firebase/Gemini API support (non-negotiable)
- ✅ Working mock mode for cost-free testing
- ✅ Safe process management (no arbitrary kills)
- ✅ Proper resource cleanup

### Should Have
- ✅ Resource throttling to prevent system overload
- ✅ Comprehensive error reporting
- ✅ Test data isolation and cleanup
- ✅ Performance monitoring

### Nice to Have
- ✅ Retry logic for flaky tests
- ✅ Test result caching
- ✅ Advanced scheduling algorithms
- ✅ Integration with CI/CD metrics

## 🚀 IMMEDIATE NEXT ACTIONS

1. **Create feature branch**: `fix/browser-test-framework`
2. **Start with Phase 1.1**: Dynamic port allocation (highest impact, lowest risk)
3. **Test incrementally**: Verify each fix before proceeding
4. **Maintain real API support**: Never break existing functionality

## 📊 SUCCESS METRICS

- **Reliability**: 100% of tests pass consistently
- **Performance**: Tests complete in <5 minutes total
- **Safety**: Zero process killing outside test scope
- **Cost**: Mock mode incurs $0 API costs
- **Maintainability**: New tests easy to add and modify

---

**OWNER**: Browser Test Framework Team
**PRIORITY**: CRITICAL
**TIMELINE**: 7-10 days
**DEPENDENCIES**: None (self-contained)
**RISK LEVEL**: Medium (touching critical testing infrastructure)
