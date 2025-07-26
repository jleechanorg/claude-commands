# Task 1: Create Failing Tests for Time Pressure Features

## Objective
Write comprehensive tests that verify the time pressure system functionality. These tests should fail initially (red state) and pass after implementation.

## Requirements

Create test file: `mvp_site/test_time_pressure.py`

### Test Cases to Implement:

1. **test_time_sensitive_events_tracked**
   - Verify events with deadlines are stored in game state
   - Check deadline structure includes all required fields
   - Ensure events can be added and retrieved

2. **test_npc_agenda_progression**
   - Verify NPCs have agendas with goals and progress
   - Test that progress increases over time
   - Check milestone tracking works correctly

3. **test_deadline_consequences**
   - Test that missing a deadline triggers consequences
   - Verify consequence text is generated
   - Check that event status changes to "failed"

4. **test_warning_generation**
   - Test warnings at different urgency levels:
     - 3+ days: subtle hint
     - 1-2 days: clear warning
     - <1 day: urgent alert
   - Verify warning count increments

5. **test_world_resource_depletion**
   - Test resources deplete at specified rates
   - Verify critical level triggers consequences
   - Check depletion calculations are correct

6. **test_time_advancement**
   - Test different action time costs:
     - Combat: 6 seconds/round
     - Short rest: 1 hour
     - Long rest: 8 hours
   - Verify calendar advances correctly

### Test Structure
```python
import unittest
from unittest.mock import Mock, patch
from game_state import GameState
from gemini_service import GeminiService

class TestTimePressure(unittest.TestCase):
    def setUp(self):
        self.game_state = GameState()
        self.gemini_service = GeminiService()
        # Setup test data

    def test_time_sensitive_events_tracked(self):
        # Should fail initially
        # Test implementation here

    # Additional tests...
```

### Success Criteria
- All tests fail when first run (before implementation)
- Tests cover all major time pressure features
- Tests use appropriate mocking for AI service
- Clear test names and assertions
