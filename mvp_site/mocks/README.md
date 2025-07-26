# Mocks Directory

## Overview

This directory contains mock implementations of external services used for testing and development. These mocks allow for isolated testing of application components without requiring actual external service dependencies like Firebase or the Gemini AI API.

## Directory Structure

```
mocks/
├── __init__.py              # Package initialization
├── mock_firestore_service.py # Mock Firebase/Firestore implementation
├── mock_gemini_service.py    # Mock Gemini AI service implementation
└── data_fixtures.py         # Test data fixtures and sample data
```

## Mock Services

### mock_firestore_service.py
- **Purpose**: Mock implementation of Firebase/Firestore database operations
- **Key Features**:
  - In-memory storage for campaign and user data
  - Simulated document operations (create, read, update, delete)
  - Game state management without external dependencies
  - Story log simulation with proper data structures
  - User authentication simulation

**Main Public Methods**:
- `get_campaigns_for_user(user_id)` - Return mock campaign list
- `get_campaign_by_id(user_id, campaign_id)` - Return mock campaign data
- `create_campaign(user_id, title, prompt, story, state)` - Create mock campaign
- `update_campaign_game_state(user_id, campaign_id, state)` - Update mock state
- `add_story_entry(user_id, campaign_id, actor, text, mode)` - Add mock story entry

### mock_gemini_service.py
- **Purpose**: Mock implementation of Gemini AI service
- **Key Features**:
  - Predefined responses for common scenarios
  - Structured JSON response simulation
  - State update generation
  - Entity tracking simulation
  - Planning block generation

**Main Public Methods**:
- `get_initial_story(prompt, selected_prompts)` - Generate mock opening story
- `continue_story(user_input, mode, context, game_state)` - Generate mock continuation
- `_create_mock_response(narrative_text, state_updates)` - Helper for response creation

### data_fixtures.py
- **Purpose**: Test data fixtures and sample data for consistent testing
- **Key Features**:
  - Sample campaign data
  - Test user profiles
  - Mock game states
  - Story context examples
  - Character data templates

**Main Public Methods**:
- `get_sample_campaign()` - Return sample campaign data
- `get_sample_game_state()` - Return sample game state
- `get_sample_story_context()` - Return sample story entries
- `get_sample_user_data()` - Return sample user information

## Usage Patterns

### Testing with Mocks

#### Unit Testing
```python
import unittest
from mocks.mock_firestore_service import MockFirestoreService
from mocks.mock_gemini_service import MockGeminiService

class TestCampaignCreation(unittest.TestCase):
    def setUp(self):
        self.firestore = MockFirestoreService()
        self.gemini = MockGeminiService()

    def test_create_campaign(self):
        # Test using mocks instead of real services
        campaign_id = self.firestore.create_campaign(
            user_id="test_user",
            title="Test Campaign",
            prompt="Test prompt",
            story="Test story",
            state={}
        )
        self.assertIsNotNone(campaign_id)
```

#### Integration Testing
```python
from mocks.mock_firestore_service import MockFirestoreService
from mocks.data_fixtures import get_sample_campaign

def test_campaign_workflow():
    # Use mock service with fixture data
    mock_service = MockFirestoreService()
    campaign_data = get_sample_campaign()

    # Test full workflow with predictable data
    result = mock_service.create_campaign(**campaign_data)
    assert result is not None
```

### Development Testing
```python
# Enable mock services for development
import os
os.environ['USE_MOCK_SERVICES'] = 'true'

# Application will use mocks instead of real services
from main import create_app
app = create_app()
```

## Mock Design Principles

### 1. Behavioral Fidelity
- Mocks should behave similarly to real services
- Return data structures that match actual service responses
- Handle edge cases and error conditions appropriately
- Maintain consistent API interfaces

### 2. Test Isolation
- Each test gets independent mock instances
- No shared state between tests
- Predictable, repeatable behavior
- Clear setup and teardown procedures

### 3. Configurability
- Mocks can be configured for different test scenarios
- Support for both success and failure cases
- Customizable response data
- Flexible behavior modification

### 4. Performance
- Fast execution for rapid testing
- Minimal memory usage
- No external dependencies
- Deterministic timing

## Mock Configuration

### Environment Variables
- `USE_MOCK_SERVICES` - Enable mock services globally
- `MOCK_FIRESTORE` - Enable only Firestore mocks
- `MOCK_GEMINI` - Enable only Gemini mocks
- `TESTING` - Automatic mock enablement in test mode

### Configuration Options
```python
# Configure mock behavior
mock_service = MockFirestoreService(
    response_delay=0.1,  # Simulate network delay
    error_rate=0.05,     # Simulate 5% error rate
    max_campaigns=100    # Limit for testing
)
```

## Test Scenarios

### Success Cases
- **Campaign Creation**: Successful campaign creation with valid data
- **Story Generation**: AI responses with proper formatting
- **State Updates**: Game state modifications with validation
- **User Management**: Authentication and authorization flows

### Error Cases
- **Network Failures**: Simulated connection errors
- **Authentication Errors**: Invalid tokens and permissions
- **Data Validation**: Invalid input handling
- **Service Unavailable**: Temporary service outages

### Edge Cases
- **Large Datasets**: Handling of large campaigns or story logs
- **Concurrent Access**: Multiple users accessing same campaign
- **Rate Limiting**: API rate limit simulation
- **Resource Exhaustion**: Out of memory or storage scenarios

## Data Management

### Mock Data Lifecycle
1. **Setup**: Initialize mock data at test start
2. **Execution**: Use mock data during test execution
3. **Isolation**: Each test gets independent data
4. **Cleanup**: Automatic cleanup after test completion

### Data Persistence
- **In-Memory**: Default storage for fast testing
- **Temporary Files**: Optional file-based storage
- **Database**: Optional database simulation
- **State Reset**: Automatic state reset between tests

## Development Workflow

### Adding New Mocks
1. **Identify Service**: Determine which service needs mocking
2. **Define Interface**: Match the real service API
3. **Implement Mock**: Create mock with appropriate behavior
4. **Add Fixtures**: Create test data fixtures
5. **Test Mock**: Verify mock behavior matches expectations

### Maintaining Mocks
1. **Sync with Real Services**: Keep mocks updated with API changes
2. **Extend Test Coverage**: Add scenarios as needed
3. **Performance Optimization**: Optimize for test speed
4. **Documentation**: Keep documentation current
5. **Version Control**: Track changes alongside real services

## Integration with Test Framework

### Test Discovery
```python
# Automatic mock discovery and setup
import pytest
from mocks import setup_mocks, teardown_mocks

@pytest.fixture(autouse=True)
def setup_test_environment():
    setup_mocks()
    yield
    teardown_mocks()
```

### Test Configuration
```python
# Configure different mock behaviors per test
@pytest.mark.parametrize("mock_config", [
    {"error_rate": 0.0},    # No errors
    {"error_rate": 0.1},    # 10% error rate
    {"response_delay": 1.0} # 1 second delay
])
def test_with_different_configs(mock_config):
    # Test with different mock configurations
    pass
```

## Quality Assurance

### Mock Validation
- **Interface Compliance**: Mocks match real service interfaces
- **Data Consistency**: Mock data follows expected schemas
- **Behavior Verification**: Mock behavior matches real services
- **Performance Metrics**: Mock performance meets test requirements

### Testing Mocks
- **Unit Tests**: Test mock implementations independently
- **Integration Tests**: Test mocks with application code
- **Comparison Tests**: Compare mock vs real service behavior
- **Regression Tests**: Ensure mocks don't break existing tests

## Best Practices

### Mock Design
1. **Keep It Simple**: Mocks should be straightforward
2. **Match Interfaces**: Exactly match real service APIs
3. **Predictable Behavior**: Consistent, repeatable responses
4. **Comprehensive Coverage**: Cover all important scenarios
5. **Easy Configuration**: Simple setup and customization

### Testing with Mocks
1. **Test Isolation**: Each test uses independent mocks
2. **Realistic Data**: Use representative test data
3. **Error Scenarios**: Test both success and failure cases
4. **Performance**: Ensure mocks don't slow down tests
5. **Documentation**: Document mock behavior and limitations

## Troubleshooting

### Common Issues
1. **Mock Not Loading**: Check environment variables and imports
2. **Inconsistent Behavior**: Verify mock state isolation
3. **Performance Issues**: Optimize mock implementation
4. **Data Mismatches**: Ensure fixture data matches expectations
5. **Test Failures**: Check mock configuration and setup

### Debugging Tips
- **Logging**: Enable detailed logging for mock operations
- **State Inspection**: Check mock internal state
- **Response Validation**: Verify mock responses match expectations
- **Error Simulation**: Test error handling with controlled failures
- **Performance Monitoring**: Track mock execution times
