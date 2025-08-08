# PR #1187 Scope Correction Plan

## 🚨 CRITICAL ISSUE: API Compatibility Violation

**Problem**: PR #1187 violates the architectural principle that **"v1 and v2 APIs should be the same"** by mixing backend Python changes with frontend v2 integration work.

**Root Cause**: This PR started as "v2 campaign creation API integration" but evolved into a massive backend refactor that breaks API compatibility constraints.

## 📋 Current PR Violations

### Backend Changes (VIOLATE COMPATIBILITY)
- **`mvp_site/main.py`**: Import organization, port change 5005→8081
- **`mvp_site/game_state.py`**: Core game logic modifications  
- **`mvp_site/gemini_request.py`**: AI request handling changes
- **`mvp_site/world_logic.py`**: Game world logic modifications

### Frontend Changes (COMPATIBLE)  
- **`mvp_site/frontend_v2/`**: React component updates
- **CSS/styling**: Frontend presentation improvements
- **Component logic**: Client-side functionality

## 🎯 Correction Strategy

### Phase 1: Backend Change Reversion
**Objective**: Remove all Python backend modifications to restore API compatibility

1. **Revert main.py changes**:
   - Restore original import structure
   - Revert port change from 8081 back to 5005
   - Remove unnecessary import reorganization

2. **Revert core logic files**:
   - `game_state.py` → restore original implementation
   - `gemini_request.py` → restore original API handling
   - `world_logic.py` → restore original game mechanics

3. **Remove backend test expectations**:
   - Tests expecting `clock_skew_seconds` parameter
   - Tests expecting MockModeToggle imports
   - Move to separate backend improvement PR

### Phase 2: Frontend v2 Preservation
**Objective**: Maintain all valid frontend improvements

1. **Preserve React components**:
   - Keep all `frontend_v2/` directory changes
   - Maintain component functionality improvements
   - Preserve CSS and styling updates

2. **Validate API compatibility**:
   - Ensure React v2 works with original backend
   - Test identical API endpoints work for both v1/v2
   - Confirm no frontend code expects backend changes

### Phase 3: Clean Commit Structure
**Objective**: Create clear separation of concerns

1. **Revert commit**: "Revert backend changes to maintain v1/v2 API compatibility"
2. **Preserve commit**: "Maintain frontend v2 components only"
3. **Update commit**: "Move backend-specific tests to separate category"

## 🔍 Implementation Details

### Files to Revert (Backend)
```
mvp_site/main.py
mvp_site/game_state.py  
mvp_site/gemini_request.py
mvp_site/world_logic.py
```

### Files to Preserve (Frontend)
```
mvp_site/frontend_v2/**/*
mvp_site/static/css/**/*  
mvp_site/templates/**/* (if v2 related)
```

### Tests to Relocate
```
mvp_site/tests/test_auth_clock_skew.py → backend_improvements/
roadmap/tests/test_milestone2_api_validation.py → backend_improvements/
```

## ✅ Success Criteria

1. **API Compatibility Restored**: v1 and v2 use identical backend APIs
2. **No Python Backend Changes**: Zero Flask/Python modifications in final PR
3. **Frontend Functionality Preserved**: All v2 React improvements maintained
4. **Test Suite Passes**: No backend-expectation test failures
5. **Architectural Compliance**: PR follows "v1/v2 APIs must be identical" principle

## 🚀 Next Steps

1. **Execute reversion plan** using Serena MCP for targeted file analysis
2. **Test API compatibility** between v1 and v2 frontends
3. **Create separate backend improvement PR** for clock skew and other enhancements
4. **Update PR description** to reflect frontend-only scope

## 📚 Architectural Learning

This correction reinforces the critical importance of:
- **Scope discipline**: PRs should have single, clear architectural purpose
- **API contract enforcement**: Compatibility constraints must be respected
- **Separation of concerns**: Backend and frontend evolution should be independent
- **Test architecture**: Tests should validate contracts, not implementation details

**Principle**: Frontend architectural improvements must never require backend modifications to maintain true v1/v2 compatibility.