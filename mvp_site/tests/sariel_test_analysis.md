# Sariel Test Files Analysis

## Summary of Test Files

### 1. test_sariel_single_campaign_full.py
- **Purpose**: Run ONE Sariel campaign with first 10 interactions, validating all entities and game state
- **API Calls**:
  - 1 campaign creation (POST)
  - 10 interactions (POST)
  - 10 game state checks (GET)
  - **Total: 21 API calls**
- **Unique Features**:
  - Comprehensive validation of game state integrity
  - Detailed entity tracking with found/missing counts
  - Validates all game state fields (player_character_data, npc_data, world_data, combat_state)
  - Tracks Cassian problem specifically
  - Prints detailed per-interaction results

### 2. test_sariel_with_prompts.py
- **Purpose**: Run ONE Sariel campaign with first 10 interactions, logging prompts sent to LLM
- **API Calls**:
  - 1 campaign creation (POST)
  - 10 interactions (POST)
  - **Total: 11 API calls** (no state checks)
- **Unique Features**:
  - Monkey patches llm_service to capture prompts
  - Logs first 50 lines of each prompt sent to LLM
  - Saves all captured prompts to JSON file
  - Focuses on prompt debugging

### 3. test_sariel_production_validation.py
- **Purpose**: Test with detailed field-level validation counts
- **API Calls**:
  - 1 campaign creation (POST)
  - 3 interactions (POST) - runs only 3 for faster results
  - 4 game state checks (GET) - initial + after each interaction
  - **Total: 8 API calls**
- **Unique Features**:
  - Counts all fields recursively for each entity type
  - Uses all 3 AI personas (narrative, mechanics, calibration)
  - Uses all custom options to maximize token count
  - Detailed field count breakdown per entity
  - Focuses on state evolution tracking

### 4. test_sariel_full_validation.py
- **Purpose**: Run 10 full replays with complete validation
- **API Calls**:
  - 10 campaigns (10 POST)
  - 5 interactions per campaign (50 POST)
  - 5 state checks per campaign (50 GET)
  - **Total: 110 API calls** (10 runs × 11 calls per run)
- **Unique Features**:
  - Multiple full campaign runs for consistency testing
  - Comprehensive validation errors tracking
  - Per-run and overall statistics
  - Cassian problem success rate across runs

### 5. test_sariel_exact_production.py
- **Purpose**: Test using exact production campaign example, always picks choice 1
- **API Calls**:
  - 1 campaign creation (POST)
  - Variable interactions from sariel_campaign_exact.json
  - 5 additional auto-interactions with choice 1
  - State checks after each interaction
  - **Total: ~15-20 API calls** (depends on exact data)
- **Unique Features**:
  - Uses exact production prompts from JSON
  - Auto-continues with choice 1 strategy
  - Recursive field counting
  - Checks for STATE_UPDATES_PROPOSED in narrative
  - Extracts choice options from narrative

### 6. test_sariel_consolidated.py
- **Purpose**: Consolidated test replacing redundant tests
- **Configuration**:
  - SARIEL_DEBUG_PROMPTS=true - enables prompt logging
  - SARIEL_FULL_TEST=true - runs 10 interactions (default: 3)
  - SARIEL_REPLAYS=N - number of campaign runs (default: 1)
- **API Calls**:
  - Default: 1 campaign + 3 interactions = 4 API calls
  - Full test: 1 campaign + 10 interactions = 11 API calls
  - With replays: N × calls per run
- **Features**:
  - Combines functionality from tests 1, 2, and 3
  - Configurable via environment variables
  - Entity validation
  - Game state field counting
  - Optional prompt debugging
  - Results saved to JSON in debug mode

## Redundancy Analysis

### Tests that can be removed:

1. **test_sariel_single_campaign_full.py** - Fully covered by test_sariel_consolidated.py with SARIEL_FULL_TEST=true
2. **test_sariel_with_prompts.py** - Fully covered by test_sariel_consolidated.py with SARIEL_DEBUG_PROMPTS=true
3. **test_sariel_production_validation.py** - Mostly covered by test_sariel_consolidated.py (except the recursive field counting)

### Tests to keep:

1. **test_sariel_consolidated.py** - The main consolidated test
2. **test_sariel_full_validation.py** - Unique multi-run validation (110 API calls)
3. **test_sariel_exact_production.py** - Unique production flow with auto-choice selection

## Recommendations

1. Remove the three redundant tests listed above
2. Consider adding recursive field counting from test_sariel_production_validation.py to test_sariel_consolidated.py if needed
3. Update test documentation to clarify when to use each remaining test
