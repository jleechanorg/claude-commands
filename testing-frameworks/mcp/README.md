# MCP Architecture Testing Infrastructure

This directory contains comprehensive testing infrastructure for the MCP (Model Context Protocol) architecture refactor, where main.py becomes a translation layer and world_logic.py becomes an MCP server.

## Test Status
✅ All 158 tests passing with MCP architecture compatibility fixes

## Architecture Overview

```
world_logic.py (MCP Server)
├── MCP Tools: create_campaign, create_character, process_action
├── MCP Resources: campaign_data, character_sheets, game_state
└── Pure business logic (D&D 5e mechanics)

main.py (Translation Layer)
├── HTTP → MCP protocol conversion
├── MCP JSON → HTTP JSON response transformation
├── Authentication, CORS, static serving
└── Minimal routing logic
```

## Test Structure

### 1. Integration Tests (`integration/`)
- `test_mcp_server.py` - Tests MCP server standalone
- `test_translation_layer.py` - Tests HTTP → MCP translation
- `test_end_to_end.py` - Complete workflow tests
- `test_error_handling.py` - Error propagation and circuit breakers

### 2. Test Utilities (`utils/`)
- `mcp_test_client.py` - MCP client for testing
- `mock_mcp_server.py` - Mock server for unit tests
- `test_helpers.py` - Common test utilities

### 3. Mock Data (`mock_data/`)
- `campaign_responses.json` - Mock campaign data
- `character_responses.json` - Mock character data
- `error_responses.json` - Mock error scenarios

### 4. Performance (`performance/`)
- `benchmark_mcp_vs_direct.py` - Performance comparison
- `load_testing.py` - Concurrent user simulation

### 5. Deployment (`deployment/`)
- `docker-compose.yml` - Multi-service deployment
- `health_checks.py` - Service health monitoring
- `env_configs/` - Environment configurations

## Running Tests

```bash
# All MCP tests
./run_mcp_tests.sh

# Integration tests only
./run_mcp_tests.sh integration

# Performance benchmarks
./run_mcp_tests.sh performance

# With real services (costs money)
./run_mcp_tests.sh --real-apis
```

## Expected MCP Tools

Based on the refactor plan, these tools will be implemented in world_logic.py:

- `create_campaign(name, description, user_id) → dict`
- `create_character(campaign_id, character_data) → dict`
- `process_action(session_id, action_type, action_data) → dict`
- `get_campaign_state(campaign_id, user_id) → dict`
- `get_campaigns(user_id) → dict`
- `update_campaign(campaign_id, updates, user_id) → dict`
- `export_campaign(campaign_id, format, user_id) → dict`
- `get_user_settings(user_id) → dict`
- `update_user_settings(user_id, settings) → dict`

## Environment Setup

1. Install MCP library (if not already installed):
   ```bash
   pip install mcp
   ```

2. Start Redis (for session management):
   ```bash
   docker run -d -p 6379:6379 redis:alpine
   ```

3. Set environment variables:
   ```bash
   export MCP_SERVER_URL=http://localhost:8000
   export TEST_MODE=mock  # or 'real' for actual APIs
   ```

## Development Workflow

1. **Write tests first** - Follow TDD protocol from the plan
2. **Mock first** - Start with mock responses, then real servers
3. **Integration testing** - Verify HTTP → MCP → Business Logic flow
4. **Performance validation** - Ensure no significant latency increase
5. **NOOP verification** - All existing browser tests must still pass

## Critical Success Factors

- ✅ Complete NOOP to users - no visible changes
- ✅ All existing tests continue to pass
- ✅ MCP protocol correctly wraps existing functionality
- ✅ Error handling and authentication preserved
- ✅ Performance parity maintained
