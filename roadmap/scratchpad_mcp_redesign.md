# MCP Redesign Scratchpad - Main.py Pure API Gateway Refactor

**Branch**: mcp_redesign
**Goal**: Transform main.py from monolithic Flask app to pure API gateway (translation layer only)
**Status**: Planning Phase - Execution Plan Required

## 🚨 CRITICAL: Main.py Role Definition

Per `roadmap/mcp_architecture_refactor_plan.md`, main.py should become a **Translation Layer** with these exact responsibilities:

### Explicit Main.py Responsibilities (ONLY THESE)
1. **HTTP → MCP protocol conversion** - Convert HTTP requests to MCP JSON-RPC calls
2. **MCP JSON → HTTP JSON response transformation** - Format MCP responses for frontend
3. **Authentication, CORS, static serving** - Handle auth validation and asset serving
4. **Minimal routing logic** - Simple Flask routes that delegate to MCP server

### What Main.py Should NOT Know About (REMOVE THESE)
- ❌ `from game_state import GameState` - Game logic belongs in world_logic.py
- ❌ `import firestore_service` - Database operations belong in world_logic.py
- ❌ `import llm_service` - AI operations belong in world_logic.py
- ❌ Campaign creation logic - Business logic belongs in world_logic.py
- ❌ Story processing logic - Game mechanics belong in world_logic.py
- ❌ Character management - D&D logic belongs in world_logic.py

### Current Architecture Problem
```
main.py (CURRENT - MONOLITHIC)
├── Route handlers (/campaign, /character, /session)
├── Business logic (D&D 5e game mechanics) ❌ REMOVE
├── Database operations (Firestore) ❌ REMOVE
├── AI integration (Gemini API) ❌ REMOVE
└── Static file serving ✅ KEEP
```

### Target Architecture (Pure Translation Layer)
```
main.py (TARGET - TRANSLATION LAYER ONLY)
├── HTTP → MCP protocol conversion ✅ ADD
├── MCP JSON → HTTP JSON response transformation ✅ ADD
├── Authentication, CORS, static serving ✅ KEEP
└── Minimal routing logic ✅ KEEP

world_logic.py (MCP Server - ALL BUSINESS LOGIC)
├── MCP Tools: create_campaign, create_character, process_action
├── MCP Resources: campaign_data, character_sheets, game_state
├── Business logic (D&D 5e game mechanics) ✅ MOVED HERE
├── Database operations (Firestore) ✅ MOVED HERE
└── AI integration (Gemini API) ✅ MOVED HERE
```

## Current State Analysis

### Problematic Imports in Main.py (To Remove)
From analysis of unified API testing reports, main.py currently has these problematic imports:
- `from game_state import GameState` - Direct game logic dependency
- `import firestore_service` - Direct database dependency
- `import llm_service` - Direct AI service dependency

### Business Logic in Main.py (To Move)
Based on duplication analysis, main.py contains these business logic patterns that should move to world_logic.py:
- `_prepare_game_state` - Game state management logic
- `_cleanup_legacy_state` - Game state cleanup logic
- `_build_campaign_prompt` - Campaign prompt building logic
- `_handle_debug_mode_command` - Debug mode handling logic
- Campaign creation workflows
- Story processing workflows
- Character management workflows

## Execution Plan Requirements

### Phase 1: Pure API Gateway Implementation
1. **Remove Game Logic Dependencies**
   - Remove `from game_state import GameState`
   - Remove `import firestore_service`
   - Remove `import llm_service`
   - Remove all business logic helper functions

2. **Implement MCP Client Integration**
   - Add MCP client to communicate with world_logic.py server
   - Create translation functions between HTTP and MCP JSON-RPC
   - Implement error handling for MCP communication failures

3. **Preserve Authentication & Static Serving**
   - Keep JWT authentication validation
   - Keep CORS configuration
   - Keep static file serving for frontend_v1/
   - Keep minimal routing structure

4. **Create Translation Functions**
   - HTTP request → MCP tool call conversion
   - MCP response → HTTP JSON conversion
   - Error translation (MCP errors → HTTP status codes)

### Success Criteria
- ✅ Main.py imports ONLY: Flask, MCP client, auth utilities, static serving
- ✅ Main.py contains ZERO business logic (no game mechanics)
- ✅ Main.py knows nothing about GameState, Firestore, Gemini
- ✅ All Flask routes delegate to MCP server via translation layer
- ✅ Frontend receives identical JSON responses (transparent to users)
- ✅ All tests pass (complete NOOP to users)

## Current Issue: Unified API Integration Gap

Per testing reports, there's a critical integration gap:
- ✅ **Flask Integration**: COMPLETE - All 8 routes use unified_api functions
- ❌ **MCP Integration**: INCOMPLETE - 0 tools use unified_api functions
- ❌ **Business Logic Duplication**: 12 patterns duplicated across files

This refactor will resolve the integration gap by:
1. Moving ALL business logic to world_logic.py (MCP server)
2. Making main.py a pure HTTP→MCP translation layer
3. Eliminating business logic duplication entirely

## 📋 EXECUTION PLAN - Main.py Pure API Gateway Refactor

### Current State Analysis ✅ COMPLETE

**Problematic Game Logic Dependencies Found:**
- `from game_state import GameState` (line 86) - Direct game logic dependency
- `from firestore_service import ...` (line 79) - Direct database dependency
- `import llm_service as real_llm_service` (line 78) - Direct AI service dependency
- `from mocks import mock_firestore_service_wrapper, mock_llm_service_wrapper` - Test dependencies

**Business Logic in Main.py:** 12 duplicated patterns that should move to world_logic.py MCP server

### Execution Plan - Pure Translation Layer Pattern

**Goal:** Transform main.py from monolithic Flask app to pure HTTP→MCP translation layer with zero game logic

#### Phase 1: MCP Client Integration (2-3 hours)
1. **Add MCP Client Dependencies**
   - Install MCP client library
   - Create `MCPTranslationClient` class for world_logic.py communication

2. **Create Translation Functions**
   - `http_to_mcp_request()` - Convert Flask requests to MCP JSON-RPC
   - `mcp_to_http_response()` - Convert MCP responses to Flask JSON
   - `handle_mcp_errors()` - Translate MCP errors to HTTP status codes

#### Phase 2: Route Refactor (3-4 hours)
3. **Refactor All Flask Routes**
   - Replace unified_api calls with MCP client calls
   - Remove all game logic (GameState, Firestore, Gemini operations)
   - Keep only: auth validation → MCP call → response translation

4. **Remove Game Logic Dependencies**
   - Remove `from game_state import GameState`
   - Remove `from firestore_service import ...`
   - Remove `import llm_service`
   - Remove all business logic helper functions

#### Phase 3: Pure API Gateway (1-2 hours)
5. **Final Cleanup**
   - Keep only: Flask, MCP client, auth utilities, static serving
   - Ensure main.py has ZERO knowledge of game mechanics
   - Verify all routes delegate to world_logic.py MCP server

### Code Architecture Target

**New Main.py Structure:**
```python
# ONLY these imports allowed:
from flask import Flask, request, jsonify, g
from mcp.client import Client as MCPClient
import auth_utils  # JWT validation only
# NO game_state, NO firestore_service, NO llm_service

class MCPTranslationLayer:
    def __init__(self):
        self.mcp_client = MCPClient(server_url="http://localhost:8000")

    @app.route('/api/campaigns', methods=['POST'])
    @require_auth  # Keep auth
    async def create_campaign():
        # 1. Validate auth (KEEP)
        # 2. Convert HTTP → MCP JSON-RPC (ADD)
        # 3. Call world_logic.py MCP server (ADD)
        # 4. Convert MCP response → HTTP JSON (ADD)
        # NO game logic, NO database calls, NO AI calls
```

### Success Criteria
- ✅ Main.py imports ONLY: Flask, MCP client, auth utilities, static serving
- ✅ Main.py contains ZERO business logic (no game mechanics)
- ✅ Main.py knows nothing about GameState, Firestore, Gemini
- ✅ All Flask routes delegate to MCP server via translation layer
- ✅ Frontend receives identical JSON responses (complete NOOP to users)
- ✅ All tests pass - `./run_tests.sh` and `./run_ui_tests.sh mock`

### Subagent Approach
**Agent 1:** MCP client integration and translation functions
**Agent 2:** Route refactoring and game logic removal
**Agent 3:** Final cleanup and testing validation

### Risk Mitigation
- Backup main.py before changes
- Test each route individually during refactor
- Validate complete NOOP - users see no functional changes
- Maintain identical API contract for frontend

**Estimated Timeline:** 6-9 hours total
**Complexity:** High (architectural redesign)
**User Impact:** Zero (complete NOOP - same functionality, different architecture)

### Status
- ✅ **Plan Complete** - Ready for user approval and execution
- 🔄 **Next Step** - Awaiting user approval to begin implementation
