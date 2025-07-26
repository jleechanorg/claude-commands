# Test Infrastructure

This directory contains comprehensive test files for debugging, validation, and quality assurance of WorldArchitect.AI. The test suite includes unit tests, integration tests, feature-specific tests, and specialized debugging tools.

## Test Coverage Overview

**Current Coverage (January 2025)**: 67% overall (21,031 statements, 6,975 missing)
- **main.py**: 74% (550 statements, 144 missing)
- **firestore_service.py**: 64% (254 statements, 91 missing)
- **gemini_service.py**: 70% (594 statements, 178 missing)
- **game_state.py**: 90% (169 statements, 17 missing) - Excellent!

## Directory Structure

### Core Component Tests
- **`test_main.py`** - Flask application routes and core functionality (126 test methods)
- **`test_firestore_service.py`** - Database operations and state management
- **`test_gemini_service.py`** - AI service integration and response processing
- **`test_game_state.py`** - Game state management and validation
- **`test_constants.py`** - Constants and configuration validation

### Feature-Specific Test Categories

#### Authentication & Security
- **`test_main_auth*.py`** - Authentication flow testing (4 files)
- **`test_main_security_validation.py`** - Security validation and edge cases
- **`auth/test_auth_resilience.py`** - Authentication error handling and recovery

#### JSON & Data Processing
- **`test_json_*.py`** - JSON parsing, validation, and bug fixes (15 files)
- **`test_robust_json_parser.py`** - Robust JSON parsing edge cases
- **`test_numeric_field_converter.py`** - Numeric field validation and conversion

#### AI Integration & Entity Tracking
- **`test_entity_*.py`** - Entity tracking and validation (6 files)
- **`test_narrative_*.py`** - Story generation and narrative processing (3 files)
- **`test_gemini_response*.py`** - AI response parsing and integration (2 files)

#### Game State & Combat
- **`test_combat_*.py`** - Combat mechanics and state management (2 files)
- **`test_state_*.py`** - State synchronization and updates (4 files)
- **`test_mission_*.py`** - Mission handling and conversion (2 files)

#### Debug & Development Tools
- **`test_debug_*.py`** - Debug mode functionality and parsing (7 files)
- **`test_planning_block_*.py`** - Planning block enforcement and UI (3 files)

### Specialized Test Directories

#### `/wizard/` - Campaign Wizard Tests
- **`test_root_cause_red_green.js`** - ✅ **PRIMARY**: Red/green test for wizard reset root cause
- **`test_root_cause_runner.html`** - Interactive browser runner for root cause test
- `test_wizard_reset_*` - Additional wizard reset testing infrastructure (3 files)
- `test_campaign_wizard_*` - Comprehensive wizard behavior tests (2 files)

#### `/timing/` - Performance & Timing Tests
- **`test_campaign_timing_automated.py`** - Automated backend timing validation
- **`test_timing_runner.html`** - Browser-based timing test runner
- `test_runner.html` - General test execution interface

#### `/auth/` - Authentication Tests
- **`test_auth_resilience.py`** - Authentication error handling and recovery tests

#### `/data/` - Test Data & Fixtures
- **`captured_prompts.json`** - AI prompt examples and templates
- **`sariel_campaign_exact.json`** - Complete campaign test data
- **`sariel_test_expected_output.txt`** - Expected AI response samples
- **`extract_sariel_prompts.py`** - Test data extraction utilities

## Key Tests for Future Reference

### Essential Debug Tools
1. **Root Cause Validation**: `wizard/test_root_cause_red_green.js`
   - Reproduces the exact wizard reset issue
   - Validates that navigation handler calls wizard.enable()
   - Red/green methodology for regression testing

2. **Performance Monitoring**: `timing/test_campaign_timing_automated.py`
   - Monitors campaign creation performance
   - Validates timing across AI generation and database operations

### Usage
- **Browser Tests**: Open `.html` files directly in browser
- **Python Tests**: Run with `vpython test_file.py` from project root
- **Node.js Tests**: Run with `node test_file.js`

## Maintenance Notes
- These tests document the wizard reset debugging process
- Keep for future regression testing and issue reproduction
- Tests are organized by functional area for easy navigation
