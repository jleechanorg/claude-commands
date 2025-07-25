# /teste - End2End Tests (Mock Mode)

**Purpose**: Run end-to-end tests using mocked services (current behavior)

**Usage**: `/teste`

**Script**: `./claude_command_scripts/teste.sh`

## Description

Runs the full end2end test suite using fake/mocked services:
- `FakeFirestoreClient` instead of real Firestore
- `MockGeminiClient` instead of real Gemini API
- Fast execution, no external dependencies
- Tests API contracts and basic flow

## Environment

- `TEST_MODE=mock`
- `TESTING=true`
- Uses existing mock implementations

## Test Coverage

- ✅ API endpoint contracts
- ✅ Response structure validation
- ✅ Basic error handling
- ❌ Real service behavior
- ❌ Database persistence validation
- ❌ Network/timing issues

## Related Commands

- `/tester` - Real mode (actual services)
- `/testerc` - Real mode with data capture

## Output

Shows test results with focus on:
- Pass/fail status for each test
- API contract validation
- Mock behavior verification

**Note**: This mode may miss bugs that only occur with real services (like the Firestore persistence bug we just fixed).