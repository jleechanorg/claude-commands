# Scripts Directory

## Overview
The `scripts/` directory contains 40+ utility scripts for Firebase operations, memory backup, testing, and development environment management. Scripts are organized into functional categories with specific sub-modules for specialized operations.

This document inherits from the root project documentation. Please refer to `../CLAUDE.md` for project-wide conventions and guidelines.

## Directory Structure
```
scripts/
├── debug/ # Debugging utilities (3 scripts)
├── tests/ # Testing infrastructure (3 scripts)
├── openai_automation/ # OpenAI browser automation (4 files)
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
- **`campaign_manager.py`** - **PRODUCTION CAMPAIGN MANAGEMENT** (see below)

## 🔥 Production Campaign Queries (campaign_manager.py)

**CRITICAL: Use this script to query REAL production campaigns by email.**

The Firestore database uses Firebase Auth UIDs (not emails) as user identifiers. This script
handles the email-to-UID conversion automatically.

### Prerequisites
```bash
# Set environment for clock skew fix
export WORLDAI_DEV_MODE=true
export WORLDAI_GOOGLE_APPLICATION_CREDENTIALS=~/serviceAccountKey.json
```

### Commands

**1. Find User by Email:**
```bash
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py find-user jleechan@gmail.com
```
Output: Firebase UID and user metadata

**2. Analyze User Activity (with token estimation):**
```bash
# Analyze last 3 months
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py analytics jleechan@gmail.com

# Analyze specific month
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py analytics jleechan@gmail.com --month 2025-11
```
Output: Campaigns, story entries, estimated token usage, and cost projections

**3. Query Campaigns by Name:**
```bash
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py query <UID> "My Epic Adventure"
```

**4. Delete Campaigns (dry-run first!):**
```bash
# Dry run - shows what would be deleted
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py delete <UID> "My Epic Adventure"

# Actual deletion (requires typing 'DELETE' to confirm)
WORLDAI_DEV_MODE=true python scripts/campaign_manager.py delete <UID> "My Epic Adventure" --confirm
```

### Token Estimation Constants
The analytics command uses these constants from `llm_service.py`:
- Base system instructions: ~43,000 tokens
- World content estimate: ~50,000 tokens
- Tokens per story entry: ~500 tokens
- Max history turns: 100 (truncation limit)
- 200K threshold: Above this, requests use "long context" pricing (2x cost)

### Cost Tiers (Gemini 3 Pro)
- Short context (≤200K tokens): $2/M input, $12/M output
- Long context (>200K tokens): $4/M input, $18/M output

### OpenAI Automation (../automation/openai_automation/)
- **`codex_github_mentions.py`** - Automate "GitHub mention" tasks in OpenAI Codex
- **`oracle_cli.py`** - CLI tool for asking GPT-5 Pro questions via browser
- **`start_chrome_debug.sh`** - Launch Chrome with remote debugging (CDP)
- **`README.md`** - Comprehensive documentation and usage guide

**Key Features:**
- Non-detectable automation using Chrome DevTools Protocol (CDP)
- Reuses existing browser session to preserve login state
- No headless mode to avoid detection
- Automated PR updates for Codex GitHub mention tasks

**Location:** Files moved to `automation/openai_automation/` directory

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

### Test Infrastructure (tests/)
- `test_crdt_integration.py` - CRDT system integration testing
- `scripts/tests/test_crdt_validation.py` - Consolidated CRDT validation suite (properties, edge, production, performance, security)
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

### OpenAI Automation
```bash
# Start Chrome in debug mode (required first)
./automation/openai_automation/start_chrome_debug.sh

# Log into OpenAI in the opened Chrome window
# Then run automation scripts:

# Automate Codex GitHub mention tasks
python3 automation/openai_automation/codex_github_mentions.py

# Ask GPT-5 Pro a question
python3 automation/openai_automation/oracle_cli.py "What is quantum computing?"

# Interactive mode
python3 automation/openai_automation/oracle_cli.py --interactive
```

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
