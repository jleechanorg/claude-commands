# Initial Request

**Date**: 2025-08-09 22:27
**Requester**: User
**Type**: Engineering Design + Migration

## Original Request

> lets just make the eng design but ensure we run /requirements-start and redesign run_tests.sh to be python and find all places that refeerence it and change it. Lets also change run_ci_replica or whatevever its called to be python and find all place isnt he code to change it

## Extracted Requirements

### Primary Objectives
1. **Redesign `run_tests.sh` to Python**: Convert the existing shell script to a Python implementation
2. **Redesign `run_ci_replica` to Python**: Convert the existing CI replication script to Python  
3. **Update all references**: Find and update all places in the codebase that reference these scripts
4. **Create comprehensive engineering design**: Document the migration approach and implementation

### Context from Previous Analysis
- The current `run_tests.sh` has memory issues due to unlimited parallel process spawning
- Each test file spawns its own Python process, causing 18GB+ memory usage with 60+ test files
- Coverage mode works fine (sequential) but normal mode causes out-of-memory crashes
- Python with `multiprocessing.Pool` would provide better process management and memory control

### Migration Scope
- **Script 1**: `run_tests.sh` → Python equivalent
- **Script 2**: `run_ci_replica` (or similar CI script) → Python equivalent
- **References**: All files, documentation, GitHub Actions, etc. that call these scripts
- **Functionality**: Maintain exact same command-line interface and behavior