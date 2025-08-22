# PR Guidelines Documentation

This document inherits from the root project documentation. Please refer to `../../CLAUDE.md` for project-wide conventions and guidelines.

## Overview
This directory contains comprehensive guidelines for creating, reviewing, and merging pull requests within the project. The standards ensure code quality, consistency, and proper documentation across all development workflows.

## File Inventory

### Core Documentation
- `base-guidelines.md` - Fundamental PR creation and review standards
- `CLAUDE.md` - Directory-specific documentation (this file)

### PR-Specific Guidelines
- `pr1057/` - Directory: PR-specific guidelines and evidence
- `pr1286/` - Directory: PR-specific guidelines and evidence  
- `pr1289/` - Directory: PR-specific guidelines and evidence
- `pr1292/` - Directory: PR-specific guidelines and evidence
- `pr1294/` - Directory: PR-specific guidelines and evidence

### Archive Documentation
- Various numbered PR directories containing historical guidelines and evidence

## Technology-Specific Guidelines

### Python Development
- All PRs must pass pylint with score ≥ 8.0
- Include type hints for function signatures
- Follow PEP 8 styling with black formatting
- Add docstrings for all public functions and classes
- Use `subprocess.run()` with `shell=False, timeout=30` for security

### JavaScript/TypeScript
- ESLint must pass with no errors
- Use TypeScript for all new code
- Follow project-specific style guidelines
- Include proper type definitions for complex interfaces

### React Components
- Implement proper TypeScript interfaces for props
- Use functional components with hooks
- Include component documentation
- Add unit tests for component behavior

## Content-Aware Requirements

### PR Creation Standards
- Every PR must reference corresponding documentation updates
- Breaking changes require migration guides and impact analysis
- New features need usage examples and integration documentation
- Security-related changes require threat modeling documentation

### Review Process
- All PRs require code review before merging
- Evidence-based development with proof of functionality
- Security review mandatory for authentication or data handling changes
- Performance impact assessment for significant code changes

### Documentation Standards
- PR descriptions must explain the problem and solution
- Include testing evidence and verification steps
- Document any configuration or deployment changes
- Reference related issues and dependencies

## Quality Assurance

### Code Quality Gates
- All tests must pass (zero tolerance for failing tests)
- Code coverage requirements met for new functionality
- Security scanning passes without critical vulnerabilities
- Performance benchmarks maintained or improved

### Review Checklist
- Code follows project conventions and style guidelines
- Proper error handling and logging implemented
- Documentation updated to reflect changes
- Breaking changes properly communicated and versioned

## Evidence-Based Development

### Testing Requirements
- All new features require comprehensive test coverage
- Integration tests validate end-to-end functionality
- Security tests confirm proper access controls
- Performance tests verify acceptable response times

### Documentation Evidence
- Screenshots or videos demonstrating functionality
- API documentation for new endpoints
- Configuration examples for new settings
- Migration guides for breaking changes

## Branch Management

### Branch Conventions
- Feature branches from main for new development
- Hotfix branches for critical production issues
- Release branches for version preparation
- All changes require PR regardless of size

### Merge Requirements
- Required approvals based on change scope
- CI/CD pipeline success mandatory
- Conflict resolution before merge
- Proper commit message formatting

See also: [../../CLAUDE.md](../../CLAUDE.md) for complete project protocols and development guidelines.