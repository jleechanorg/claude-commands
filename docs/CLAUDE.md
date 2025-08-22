# Project Documentation

This document inherits from the root project documentation. Please refer to `../CLAUDE.md` for project-wide conventions and guidelines.

## Overview
The `docs/` directory contains comprehensive project documentation, development guides, architectural decision records, and evidence from feature development and testing processes.

## Documentation Structure

### Core Documentation
- `CLAUDE.md` - Directory-specific documentation (this file)
- Various subdirectories containing specialized documentation

### Architectural Decision Records (ADR)
- `adr/` - Architectural decisions and technical design choices
- Documents major system design decisions with rationale and consequences

### Feature Development Evidence
- `pr-guidelines/` - Pull request standards and review processes
- `tdd_evidence_*/` - Test-driven development evidence and validation
- `campaign_creation_evidence/` - Campaign feature development documentation
- `v1_vs_v2_*/` - Version comparison analysis and migration guides

### Process Documentation
- `branch-guidelines/` - Git workflow and branching strategies
- `improvement-*/` - System improvement initiatives and outcomes
- `skills/` - Development skills and training materials

### Technical Specifications
- Various PR-specific directories (`pr1057/`, `pr1286/`, etc.) containing:
  - Requirements analysis
  - Implementation evidence
  - Testing validation
  - Performance metrics

## Documentation Standards

### Writing Guidelines
1. **Clarity First** - Write for developers who are new to the project
2. **Evidence-Based** - Include screenshots, logs, and concrete examples
3. **Actionable Content** - Provide specific steps and commands
4. **Version Control** - Date all significant changes and updates
5. **Cross-References** - Link to related documentation and code

### Documentation Types

#### Setup and Configuration
- Environment setup instructions with dependency management
- Configuration guides for development, staging, and production
- Deployment procedures with rollback strategies

#### API Documentation
- REST endpoint specifications with request/response examples
- Authentication and authorization patterns
- Error handling and status code definitions

#### Development Guides
- Code style and contribution guidelines
- Testing strategies and framework usage
- Debugging procedures and troubleshooting steps

#### User Documentation
- Feature usage guides with step-by-step instructions
- Administrative procedures and access control
- FAQ and common issue resolution

## Maintenance Practices

### Document Lifecycle
- **Creation** - New features require documentation before merge
- **Updates** - Breaking changes must update affected documentation
- **Review** - Documentation reviewed during code review process
- **Archival** - Outdated documentation moved to archive directories

### Quality Assurance
- Links validated during CI/CD pipeline
- Screenshots updated when UI changes occur
- Code examples tested for accuracy
- Documentation coverage tracked for new features

## Common Documentation Patterns

### Feature Documentation Structure
```
feature_name_evidence/
├── requirements.md         # Original requirements
├── implementation.md       # Technical implementation details
├── testing_evidence/      # Screenshots and test results
├── performance_metrics.md  # Performance analysis
└── lessons_learned.md     # Development insights
```

### API Documentation Template
```markdown
## POST /api/endpoint
**Description**: Brief endpoint description

**Request**:
- Headers: Content-Type: application/json
- Body: { "field": "value" }

**Response**:
- Success (200): { "result": "data" }
- Error (400): { "error": "message" }
```

## Integration with Development Workflow

### Documentation Requirements
- All new features require user-facing documentation
- API changes require updated endpoint documentation
- Breaking changes require migration guides
- Security changes require updated security documentation

### Review Process
- Documentation changes reviewed alongside code changes
- Evidence provided for all feature claims
- Screenshots and examples validated for accuracy
- Cross-references checked for broken links

## Archive Management

### Historical Documentation
- Archive directories maintain project history
- Version-specific documentation preserved for reference
- Migration paths documented between major versions
- Legacy system integration guides maintained

### Cleanup Procedures
- Quarterly review of documentation relevance
- Outdated screenshots and examples updated
- Broken links identified and fixed
- Redundant documentation consolidated

See also: [../CLAUDE.md](../CLAUDE.md) for complete project protocols and development guidelines.