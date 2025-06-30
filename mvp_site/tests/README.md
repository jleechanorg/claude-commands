# Test Infrastructure

This directory contains organized test files for debugging and validation.

## Directory Structure

### `/wizard/` - Campaign Wizard Tests
- **`test_root_cause_red_green.js`** - ✅ **PRIMARY**: Red/green test for wizard reset root cause
- **`test_root_cause_runner.html`** - Interactive browser runner for root cause test
- `test_wizard_reset_*` - Additional wizard reset testing infrastructure
- `test_campaign_wizard_*` - Comprehensive wizard behavior tests

### `/timing/` - Performance & Timing Tests  
- **`test_campaign_timing_automated.py`** - Automated backend timing validation
- **`test_timing_runner.html`** - Browser-based timing test runner
- `test_runner.html` - General test execution interface

### `/auth/` - Authentication Tests
- **`test_auth_resilience.py`** - Authentication error handling and recovery tests

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