# Real-Mode Testing Framework - Scratchpad

## Branch: feature/real-mode-testing-framework
## PR: #569 - https://github.com/jleechan2015/worldarchitect.ai/pull/569
## Date: 2025-07-14

## Goal
Build a comprehensive testing framework that can run end-to-end tests against real services (not just mocks) to catch bugs that slip through mock testing. This addresses the Firestore persistence bug found in PR #551 where test mocks didn't match real service behavior.

## High-Level Architecture

### Three Testing Modes
1. **`/teste`** - Mock mode (current behavior) - Fast, no cost, isolated
2. **`/tester`** - Real mode - Uses actual services, costs money, validates real behavior
3. **`/testerc`** - Real + Capture mode - Real services + data capture for analysis

### Core Abstraction: TestServiceProvider
```python
class TestServiceProvider:
    def get_firestore(self) -> Any
    def get_gemini(self) -> Any
    def get_auth(self) -> Any

class MockServiceProvider(TestServiceProvider):
    # Current mock implementations

class RealServiceProvider(TestServiceProvider):
    # Real service connections with test isolation
```

## Subagent Strategy & Coordination

### Phase-Based Development with Specialized Agents

#### Phase 1: Foundation Agent 🏗️
**Responsibility**: Create the TestServiceProvider abstraction layer
**Duration**: ~6 hours
**Deliverables**:
- `TestServiceProvider` interface
- `MockServiceProvider` implementation (wrap existing mocks)
- `RealServiceProvider` implementation (real services with test isolation)
- Service factory for provider selection based on `TEST_MODE` env var
- Configuration management for real service credentials

**Validation Criteria**:
- Interface allows seamless switching between mock/real services
- Both providers implement identical interface
- Configuration properly isolates test vs production services
- Unit tests validate provider behavior

#### Phase 2: Command Agent ⚡
**Responsibility**: Implement slash commands and bash scripts
**Duration**: ~4 hours
**Dependencies**: Foundation Agent complete
**Deliverables**:
- `/teste` command - sets `TEST_MODE=mock`
- `/tester` command - sets `TEST_MODE=real`
- `/testerc` command - sets `TEST_MODE=capture`
- Corresponding bash scripts for each mode
- Environment variable configuration and validation

**Validation Criteria**:
- Commands properly set TEST_MODE environment
- Scripts execute tests with correct service providers
- Error handling for missing configuration/credentials
- Help documentation for each command

#### Phase 3: Capture Agent 📊
**Responsibility**: Add data capture capabilities for mock/real analysis
**Duration**: ~5 hours
**Dependencies**: Foundation Agent complete (can run parallel to Command Agent)
**Deliverables**:
- Data capture framework that records real service interactions
- Structured logging for API request/response pairs
- Capture storage in `/tmp/test_captures/[timestamp]/`
- Analysis tools to compare captured vs mock behavior
- Mock accuracy validation reports

**Validation Criteria**:
- Captures all service interactions without affecting test outcomes
- Data format enables comparison between mock and real behavior
- Storage cleanup prevents disk exhaustion
- Analysis identifies discrepancies between mock/real responses

#### Phase 4: Integration Agent 🔗
**Responsibility**: Update existing tests to support dual modes
**Duration**: ~8 hours
**Dependencies**: All previous phases complete
**Deliverables**:
- pytest fixtures that provide appropriate TestServiceProvider
- unittest setUp() modifications for service provider injection
- Test isolation improvements (separate collections, cleanup)
- Cost safeguards and resource limits for real services
- Documentation updates and migration examples

**Validation Criteria**:
- Existing tests run unchanged in mock mode
- High-value tests support real mode execution
- Resource cleanup prevents cost overruns
- Documentation explains when and how to use each mode

## Milestone Tracking System

**Location**: `/tmp/milestone_real_mode_testing.json`

**Structure**:
- Phase definitions with dependencies
- Agent assignments and status tracking
- Deliverable checklists
- Validation criteria
- Progress percentages
- Risk assessment and mitigation

**Usage**:
- Each agent updates their phase status
- Dependencies block subsequent phases
- Central coordination point for handoffs
- Progress visibility for stakeholders

## Technical Implementation Details

### Environment Variable Control
```bash
TEST_MODE=mock    # Use MockServiceProvider
TEST_MODE=real    # Use RealServiceProvider
TEST_MODE=capture # Use RealServiceProvider + data capture
```

### Service Provider Factory
```python
def get_service_provider() -> TestServiceProvider:
    mode = os.getenv('TEST_MODE', 'mock')
    if mode == 'mock':
        return MockServiceProvider()
    elif mode in ['real', 'capture']:
        return RealServiceProvider(capture=(mode == 'capture'))
    else:
        raise ValueError(f"Invalid TEST_MODE: {mode}")
```

### Real Service Configuration
- **Firestore**: Separate test collections (e.g., `test_users`, `test_campaigns`)
- **Gemini**: Separate project or API key with quota limits
- **Auth**: Test-specific credentials with minimal permissions
- **Cleanup**: Automated deletion of test data after runs

### Data Capture Format
```json
{
  "timestamp": "2025-07-14T10:30:00Z",
  "service": "firestore",
  "operation": "get_document",
  "request": {"collection": "users", "doc_id": "test-123"},
  "response": {"name": "Test User", "created": "2025-07-14"},
  "duration_ms": 45,
  "test_context": "test_user_creation"
}
```

## Safety & Cost Management

### Safeguards
- **Resource Limits**: Cap API calls per test run
- **Approval Gates**: Require explicit user consent for real service tests
- **Isolation**: Test data completely separate from production
- **Monitoring**: Track API usage and costs
- **Cleanup**: Automated deletion of test resources

### Cost Estimates
- **Development**: ~23 hours total
- **API Testing**: $5-10 per month for regular testing
- **Maintenance**: ~2 hours per month

## Success Metrics

1. **Bug Detection**: Framework catches bugs that mocks miss
2. **Test Confidence**: Measurable increase in deployment confidence
3. **Mock Accuracy**: Captured data improves mock fidelity
4. **Development Velocity**: Framework doesn't slow down development

## Risk Assessment

### Medium Risks
- **API Costs**: Mitigated by resource limits and approval gates
- **Test Data Pollution**: Mitigated by isolated test collections/projects

### Low Risks
- **Service Authentication**: Mitigated by separate test credentials and documentation

## Next Steps

1. ✅ Create milestone tracking JSON
2. ✅ Create this comprehensive scratchpad
3. 🔄 Deploy Foundation Agent to build TestServiceProvider abstraction
4. ⏳ Deploy Command Agent to implement slash commands
5. ⏳ Deploy Capture Agent to add data capture
6. ⏳ Deploy Integration Agent to update existing tests

## Context & Background

This framework was motivated by the Firestore persistence bug discovered in PR #551, where the `think` command wasn't properly persisting to Firestore. The bug existed because:

1. Test mocks didn't accurately reflect real Firestore behavior
2. Integration tests passed with mocks but failed with real services
3. No mechanism existed to validate mock accuracy against real services

The real-mode testing framework solves this by:
- Enabling tests to run against actual services
- Capturing real service behavior for mock validation
- Providing confidence that tests validate actual system behavior

## Related Work
- **PR #551**: Contains the actual Firestore persistence fix that motivated this framework
- **CLAUDE.md**: Will be updated with new testing command documentation
- **Existing Test Suite**: Will be gradually migrated to support dual modes

---

**Status**: Foundation work complete, ready for subagent deployment
**Next Action**: Deploy Foundation Agent to implement TestServiceProvider abstraction
