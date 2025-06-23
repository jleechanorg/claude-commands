# Function Test Plan: Cross-Module Integration Testing

## Definition
Function tests validate the interaction between multiple Python modules/files while mocking external dependencies (Gemini API, Firestore DB). These tests ensure our hybrid checkpoint validation system works end-to-end across the application stack.

## Test Scope
- **IN SCOPE**: Multiple Python files, method interactions, data flow validation
- **MOCKED**: Gemini API calls, Firestore database operations, network requests
- **OUT OF SCOPE**: Actual external service calls, UI interactions

## Mock Libraries to Create

### 1. `mock_gemini_service.py` - Gemini API Mock
```python
class MockGeminiClient:
    def __init__(self):
        self.responses = {
            "initial_story": "Sir Kaelan awakens in the tavern...",
            "continue_story": "The hero explores the forest depths...",
            "state_updates": {"player_character_data": {"hp_current": 75}}
        }
    
    def generate_content(self, prompt, model=None):
        # Return realistic AI responses based on prompt patterns
        pass
```

### 2. `mock_firestore_service.py` - Firestore Database Mock  
```python
class MockFirestoreClient:
    def __init__(self):
        self.campaigns = {}
        self.game_states = {}
        self.story_logs = {}
    
    def get_campaign_by_id(self, user_id, campaign_id):
        # Return mock campaign data
        pass
    
    def update_campaign_game_state(self, user_id, campaign_id, state_dict):
        # Store state updates in memory
        pass
```

### 3. `test_data_fixtures.py` - Sample Test Data
```python
SAMPLE_CAMPAIGN = {
    "id": "test_campaign_123",
    "title": "Test Adventure",
    "user_id": "test_user",
    "selected_prompts": ["narrative", "mechanics"]
}

SAMPLE_GAME_STATE = {
    "player_character_data": {
        "name": "Sir Kaelan",
        "hp_current": 85,
        "hp_max": 100
    },
    "world_data": {
        "current_location_name": "Ancient Tavern"
    },
    "custom_campaign_state": {
        "active_missions": ["Find the Lost Crown"]
    }
}

SAMPLE_STORY_CONTEXT = [
    {"actor": "user", "text": "I look around the tavern"},
    {"actor": "gemini", "text": "The tavern is dimly lit..."}
]
```

## Function Test Cases

### Test 1: Complete Interaction Flow with Validation
**Modules Tested**: `main.py` → `gemini_service.py` → `game_state.py` → `firestore_service.py`

```python
def test_complete_interaction_with_checkpoint_validation():
    # Setup mocks
    mock_firestore = MockFirestoreClient()
    mock_gemini = MockGeminiClient()
    
    # Test flow:
    # 1. User sends input via main.py handle_interaction()
    # 2. Pre-response validation in gemini_service.continue_story()
    # 3. AI generates response with state changes
    # 4. Post-response validation in main.py
    # 5. State updates applied via firestore_service
    
    # Assertions:
    # - Pre-validation logs discrepancies
    # - AI response contains expected content
    # - Post-validation detects new discrepancies
    # - State updates are correctly applied
    # - All validation logs are captured
```

### Test 2: HP Discrepancy Detection Across Modules
**Modules Tested**: `game_state.py` validation → `gemini_service.py` prompt injection → `main.py` logging

```python
def test_hp_discrepancy_detection_end_to_end():
    # Setup: Character with 25 HP
    # AI Response: "The hero lies unconscious"
    # Expected: Discrepancy detected and logged
```

### Test 3: Mission Completion State Management
**Modules Tested**: `firestore_service.py` state updates → `game_state.py` validation → `gemini_service.py` context

```python
def test_mission_completion_state_management():
    # Setup: Active missions in state
    # AI Response: "The dragon is finally defeated"
    # Expected: Mission completion discrepancy detected
    # Action: State should be updated to reflect completion
```

### Test 4: Location Consistency Validation
**Modules Tested**: Cross-module location tracking and validation

```python
def test_location_consistency_validation():
    # Setup: Character in "Tavern" per state
    # AI Response: "Standing in the dark forest"
    # Expected: Location discrepancy detected
    # Action: Validation prompt injected for next response
```

## Mock Implementation Strategy

### Phase 1: Create Mock Base Classes
1. **`mock_gemini_service.py`** - Realistic AI response patterns
2. **`mock_firestore_service.py`** - In-memory database simulation
3. **`test_data_fixtures.py`** - Comprehensive test data sets

### Phase 2: Function Test Implementation
1. **`test_function_validation_flow.py`** - End-to-end validation testing
2. **`test_function_state_management.py`** - Cross-module state handling
3. **`test_function_error_scenarios.py`** - Error handling and edge cases

### Phase 3: Integration Validation
1. **Mock behavior verification** - Ensure mocks behave like real services
2. **Data flow validation** - Verify data integrity across module boundaries
3. **Performance baseline** - Establish timing expectations

## Test File Structure
```
mvp_site/
├── test_function_validation_flow.py      # Main function tests
├── test_function_state_management.py     # State handling tests
├── test_function_error_scenarios.py      # Error/edge case tests
├── mocks/
│   ├── __init__.py
│   ├── mock_gemini_service.py            # Gemini API mock
│   ├── mock_firestore_service.py         # Firestore mock
│   └── test_data_fixtures.py             # Sample data
└── existing unit test files...
```

## Success Criteria
✅ **Cross-Module Integration**: Tests verify data flows correctly between modules  
✅ **Mock Reliability**: Mocks behave consistently like real services  
✅ **Validation Coverage**: All validation scenarios tested end-to-end  
✅ **Performance**: Function tests run in <5 seconds  
✅ **Maintainability**: Test data is reusable and easily updated  

## Next Steps
1. Create mock library foundation
2. Implement core function tests  
3. Validate mock behavior against real services
4. Add comprehensive test data scenarios
5. Document testing patterns for future use 