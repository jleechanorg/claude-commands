# Scripts Directory

## Overview
The `scripts/` directory contains 40+ utility scripts for Firebase operations, memory backup, testing, and development environment management. Scripts are organized into functional categories with specific sub-modules for specialized operations.

This document inherits from the root project documentation. Please refer to `../CLAUDE.md` for project-wide conventions and guidelines.

## Directory Structure
```
scripts/
├── debug/ # Debugging utilities (3 scripts)
├── memory_sync/ # Memory synchronization tools (5 scripts)
├── tests/ # Testing infrastructure (6 scripts)
└── [root] # Core utility scripts (40+ files)
```

## Script Inventory

### Core Automation Scripts
- `memory_backup.sh` - Primary memory backup orchestration with CRDT support
- `sync_check.sh` - Git synchronization and unpushed commit detection
- `setup-dev-env.sh` - Development environment initialization and configuration
- `claude_backup.sh` - Claude memory backup with distributed locking
- `install-git-hooks.sh` - Git workflow automation setup

### Firebase Administration
- `firebase_user_analytics.py` - User behavior analytics and reporting
- `firebase_collection_group_analytics.py` - Collection group analysis
- `debug_firebase_connection.py` - Firebase connectivity diagnostics
- `validate_firebase_auth.py` - Authentication configuration validation
- `test_firebase_read_write.py` - Read/write operation testing

### Development Utilities
- `analyze_git_stats.py` - Git repository statistics and analysis
- `campaign_analyzer.py` - Campaign data analysis and validation
- `pr_comment_formatter.py` - Pull request comment formatting
- `validate_imports.py` - Python import dependency validation
- `testing_help.sh` - Development testing assistance

### Debug Module (debug/)
- `debug_monitor.sh` - System monitoring and diagnostics
- `test_monitor.sh` - Test execution monitoring
- `test_few_files.sh` - Selective file testing utility

### Memory Sync Module (memory_sync/)
- `backup_memory_enhanced.py` - Enhanced memory backup with CRDT
- `fetch_memory.py` - Memory retrieval and synchronization
- `merge_memory.py` - Memory state merging and conflict resolution
- `convert_memory_format.py` - Memory format conversion utilities
- `setup_memory_sync.sh` - Memory synchronization setup

### Test Infrastructure (tests/)
- `test_crdt_integration.py` - CRDT system integration testing
- `test_memory_backup_crdt.py` - Memory backup CRDT validation
- `test_crdt_properties.py` - CRDT mathematical properties testing
- `test_concurrent_memory.sh` - Concurrent memory operation testing
- `test_parallel_memory_backup.sh` - Parallel backup testing
- `test_race_condition.sh` - Race condition detection

## Development Guidelines

### Shell Script Standards
- Use `#!/bin/bash` shebang with `set -e` for error handling
- Include comprehensive error trapping and cleanup
- Follow project logging patterns using `logging_util`
- Use descriptive variable names with snake_case convention
- Include header documentation with purpose and usage

### Python Script Standards
- Follow PEP 8 styling with project-specific conventions
- Include type hints for all function parameters and returns
- Use argparse for command-line argument parsing
- Implement proper exception handling with specific exception types
- Maintain Python 3.11+ compatibility for production systems

### Security Requirements
- Use `subprocess.run()` with `shell=False, timeout=30` for security
- Never use shell=True with user input to prevent injection
- Implement explicit error handling and stderr capture
- Follow project subprocess security patterns

## Automation Patterns

### Git Integration
- Branch management and merging automation
- Commit validation and formatting standardization
- Repository state synchronization across environments
- Conflict resolution workflows with manual override support

### Firebase Operations
- Automated deployment with environment detection
- Analytics data extraction and processing pipelines
- Configuration validation and testing frameworks
- User management batch operations with audit trails

### Memory Management
- CRDT-based memory synchronization across distributed systems
- Conflict-free replica data types for concurrent operations
- Distributed locking mechanisms for backup coordination
- Backup integrity validation and recovery procedures

## Development Environment Setup

The `setup-dev-env.sh` script configures:
- Python virtual environment with project dependencies
- Firebase CLI tools and authentication
- Git hooks for automated quality checks
- System dependencies and PATH configuration
- Development tool integration

## Testing Framework

Comprehensive testing infrastructure includes:
- CRDT conflict scenario simulation and validation
- Firebase operation integration testing
- Memory state consistency verification
- Performance benchmarking and load testing
- Race condition detection and mitigation testing

## Common Usage Patterns

### Memory Backup
```bash
./scripts/memory_backup.sh --mode=incremental
./scripts/memory_backup_crdt.sh --distributed-lock
```

### Development Setup
```bash
./scripts/setup-dev-env.sh --full-install
source venv/bin/activate
```

### Firebase Testing
```bash
./scripts/validate_firebase_auth.py --environment=dev
./scripts/test_firebase_read_write.py --collection=campaigns
```

## Quality Assurance

All scripts follow project-wide quality standards:
- Error handling with graceful degradation
- Logging integration with project monitoring
- Security compliance with subprocess protocols
- Documentation standards with inline comments
- Testing coverage with automated validation

See also: [../CLAUDE.md](../CLAUDE.md) for complete project protocols and development guidelines.