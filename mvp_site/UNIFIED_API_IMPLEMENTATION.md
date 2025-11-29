# Unified API Implementation

## Overview

The `unified_api.py` module provides a consistent JSON interface layer that both Flask and MCP server can use, extracting shared business logic and standardizing input/output formats.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Flask Routes  │    │   MCP Tools     │
│   (main.py)     │    │ (world_logic.py)│
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────────┬───────────┘
                     │
        ┌────────────▼────────────┐
        │    unified_api.py       │
        │   (Business Logic)      │
        └────────────┬────────────┘
                     │
         ┌───────────▼───────────┐
         │  Shared Services      │
         │ firestore_service.py  │
         │ llm_service.py     │
         │ game_state.py         │
         └───────────────────────┘
```

## Core Functions Implemented

### 1. `create_campaign_unified(request_data: dict) -> dict`
- **Purpose**: Unified campaign creation logic
- **Input**: Campaign title, character, setting, description, custom options
- **Output**: Campaign ID, opening story, game state
- **Extracted From**: `main.py:create_campaign_route()` and `world_logic.py:_create_campaign_tool()`

### 2. `process_action_unified(request_data: dict) -> dict`
- **Purpose**: Unified story processing and game state updates
- **Input**: User input, campaign ID, interaction mode
- **Output**: Generated story, updated game state, state changes
- **Extracted From**: `main.py:handle_interaction()` and `world_logic.py:_process_action_tool()`

### 3. `get_campaign_state_unified(request_data: dict) -> dict`
- **Purpose**: Unified campaign state retrieval
- **Input**: User ID, campaign ID
- **Output**: Campaign metadata and current game state
- **Extracted From**: `main.py:get_campaign()` and `world_logic.py:_get_campaign_state_tool()`

### 4. `update_campaign_unified(request_data: dict) -> dict`
- **Purpose**: Unified campaign updates
- **Input**: Campaign ID, updates dictionary
- **Output**: Success confirmation
- **Extracted From**: `main.py:update_campaign()` and `world_logic.py:_update_campaign_tool()`

### 5. `export_campaign_unified(request_data: dict) -> dict`
- **Purpose**: Unified campaign export (PDF/DOCX/TXT)
- **Input**: Campaign ID, export format, filename
- **Output**: Export path and metadata
- **Extracted From**: `main.py:export_campaign()` and `world_logic.py:_export_campaign_tool()`

### 6. `get_campaigns_list_unified(request_data: dict) -> dict`
- **Purpose**: Unified campaigns list retrieval
- **Input**: User ID
- **Output**: List of user's campaigns
- **Extracted From**: `main.py:get_campaigns()`

## Key Features

### Consistent JSON Input/Output
All functions follow standardized formats:

**Input Format:**
```json
{
    "user_id": "string",
    "campaign_id": "string",
    "...": "function-specific parameters"
}
```

**Success Response:**
```json
{
    "success": true,
    "...": "function-specific data"
}
```

**Error Response:**
```json
{
    "success": false,
    "error": "Error message",
    "status_code": 400
}
```

### User ID Handling
- **Flask Context**: User ID extracted from authentication token
- **MCP Context**: User ID provided as explicit parameter
- Both contexts use the same unified functions

### Error Handling
- Centralized error response formatting
- Consistent error messages across interfaces
- HTTP status codes for Flask compatibility

### Business Logic Extraction
- Game state preparation and cleanup
- Debug mode command handling
- Campaign prompt building
- Legacy state migration

## Helper Functions

### `_prepare_game_state(user_id, campaign_id)`
- Loads game state from Firestore
- Performs legacy field cleanup
- Returns GameState object with cleanup metadata

### `_cleanup_legacy_state(state_dict)`
- Removes deprecated fields from game state
- Returns cleaned state with cleanup statistics

### `_build_campaign_prompt(character, setting, description, old_prompt)`
- Builds campaign prompt from components
- Supports both new format (character/setting/description) and legacy format
- Validates that at least one component is provided

### `_handle_debug_mode_command(user_input, mode, game_state, user_id, campaign_id)`
- Processes debug mode commands (SET, ASK_STATE, UPDATE_STATE)
- Returns command response or None if not a debug command

## Response Utilities

### `create_error_response(message: str, status_code: int = 400)`
- Creates standardized error responses
- Includes success=false, error message, and status code

### `create_success_response(data: dict)`
- Creates standardized success responses
- Includes success=true and merges provided data

## Benefits

1. **Code Reuse**: Business logic implemented once, used by both interfaces
2. **Consistency**: Same JSON formats and error handling across Flask/MCP
3. **Maintainability**: Single source of truth for game logic
4. **Testing**: Test business logic once instead of testing duplicate implementations
5. **Flexibility**: Easy to add new interfaces (CLI, desktop app, etc.)

## Testing

The implementation includes comprehensive tests:
- Structure validation tests
- Input validation tests
- Business logic tests
- Response format tests
- Error handling tests

Run tests with:
```bash
cd mvp_site && python3 test_unified_api_structure.py
```

## Integration Guide

See `unified_api_examples.py` for detailed examples of:
- Flask route integration patterns
- MCP tool integration patterns
- Before/after comparison showing benefits
- User ID handling in different contexts
- Response format standardization

## Future Enhancements

1. **Async Optimization**: All functions are async-ready for future performance improvements
2. **Caching Layer**: Add response caching for frequently accessed data
3. **Rate Limiting**: Add request rate limiting at the unified layer
4. **Metrics**: Add performance monitoring and usage metrics
5. **Validation**: Add input schema validation using Pydantic
