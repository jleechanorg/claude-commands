# Scripts Directory

This directory contains all automation scripts and tools developed during Phase 0 of the state sync enhancement project.

## Purpose

House executable scripts and utilities for:

- Automated AI token discovery and pattern matching
- Data collection and analysis automation
- Pattern detection across the codebase  
- CI/CD integration scripts
- Testing and benchmarking utilities

## Expected Contents

### Milestone 0.2: Token Discovery Tool
- `token_discovery.py` - Main script to parse prompt files and extract AI token patterns
- `token_patterns.json` - Regular expression patterns for token identification
- Supporting utilities for report generation

### Milestone 1.3: Pattern Detection
- `pattern_detection.py` - Script to detect corruption patterns and "Two Source of Truth" problems
- CI/CD integration scripts

## Usage

All scripts should:
- Include clear documentation in docstrings
- Have executable permissions (`chmod +x`)
- Support command-line arguments for flexibility
- Output structured data (JSON) for further processing
- Include error handling and logging

## Requirements

Scripts may require Python 3.8+ and dependencies listed in requirements files.