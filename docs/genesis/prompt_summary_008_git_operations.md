# Git Operations Patterns (Prompts 7001-8000)

## Overview
Analysis of Git workflow patterns from authentic conversation data, focusing on branch management, pull requests, and deployment workflows.

## Git Operations Context
Git operations represent critical workflow points where code changes transition between development states and collaborative review processes.

## Primary Git Operation Triggers

### 1. Pull Request Workflow Context
**Pattern**: Code ready for review and integration
**Trigger Phrases**:
- "create PR"
- "push to pr"
- "ready for review"
- "submit pull request"
**Example Pattern**:
```
> Create PR for the user authentication feature
> Push to pr - the notification system is complete
> Ready for review: payment processing integration
> Submit pull request with comprehensive test coverage
```
**Response Approach**: Automated PR creation with proper titles, descriptions, and validation

### 2. Branch Management Context
**Pattern**: Organizing work across feature branches
**Trigger Context**: When managing multiple features or coordinating team work
**Example Pattern**:
```
> Switch to feature branch for user dashboard work
> Create new branch for the API integration project
> Merge develop branch changes into current feature
> Rebase feature branch on latest main branch
```

### 3. Deployment Coordination Context
**Pattern**: Moving code from development to production
**Trigger Context**: When features are approved and ready for deployment
**Example Pattern**:
```
> Deploy to staging for QA testing
> Promote to production after approval
> Rollback the last deployment due to issues
> Create release branch for version 2.1.0
```

## Git Operations Communication Patterns

### Direct Action Style
**Characteristics**:
- Clear, immediate git action requests
- Expectation of automated execution
- Focus on workflow progression
- Minimal explanatory context needed

**Example Phrases**:
```
> Push changes
> Create PR
> Merge to main
> Deploy to production
> Create release tag
```

### Workflow Coordination Style
**Characteristics**:
- Understanding of team collaboration needs
- Branch strategy awareness
- Review process integration
- Quality gate expectations

**Example Phrases**:
```
> Create PR with proper description and link to issues
> Push to feature branch and notify team for review
> Merge after all checks pass and approval received
> Deploy with rollback plan and monitoring
```

### Quality Assurance Style
**Characteristics**:
- Emphasis on testing and validation
- Deployment safety considerations
- Code review and approval processes
- Automated quality checks

## Git Operations Workflow Trajectories

### Feature → Review → Merge → Deploy Trajectory
**Common Sequence**: Development → `/pr` → Review/Approval → Merge → `/deploy`
1. **Development**: Feature implementation and local testing
2. **Pull Request**: Automated PR creation with descriptions and checks
3. **Review Process**: Team review, automated testing, approval
4. **Deployment**: Staging validation followed by production deployment

### Hotfix → Fast-Track → Deploy Trajectory
**Common Sequence**: Issue → Branch → Fix → `/pr` → Emergency Deploy
1. **Issue Identification**: Critical production problem requiring immediate fix
2. **Branch Creation**: Hotfix branch from production state
3. **Fix Implementation**: Minimal change to resolve critical issue
4. **Fast-Track Deployment**: Expedited review and deployment process

### Release → Stabilize → Deploy Trajectory
**Common Sequence**: Feature Freeze → Testing → `/pr` → Release Deploy
1. **Feature Freeze**: Code stabilization and integration testing
2. **Release Branch**: Dedicated branch for release preparation
3. **Stabilization**: Bug fixes and final testing
4. **Release Deployment**: Coordinated production deployment

## Git Operation Complexity Indicators

### High Complexity Git Operations (40-50%)
- Multi-branch coordination and conflict resolution
- Large feature integration with extensive changes
- Deployment coordination across multiple environments
- Release management with database migrations
- Rollback procedures with data considerations

### Moderate Complexity Git Operations (35-40%)
- Standard feature PR with review requirements
- Branch maintenance and updates
- Staging deployment with validation
- Merge conflict resolution
- Release tag creation and documentation

### Low Complexity Git Operations (10-20%)
- Simple commit and push operations
- Straightforward PR creation
- Basic branch switching
- Standard deployment to development environment

## Intent Classification for Git Operations

### 1. Code Integration (40-45%)
**Context**: Merging completed work into shared codebase
**Approach**: PR-based workflow with review and validation
**Example**: `> Create PR for the user authentication system - ready for team review`

### 2. Deployment Execution (25-30%)
**Context**: Moving validated code to production environments
**Approach**: Staged deployment with monitoring and rollback capability
**Example**: `> Deploy the latest release to production with full monitoring`

### 3. Workflow Coordination (20-25%)
**Context**: Managing collaborative development processes
**Approach**: Branch management and team coordination
**Example**: `> Coordinate the release branch merge with all team feature branches`

### 4. Quality Assurance (10-15%)
**Context**: Ensuring code quality through git-based processes
**Approach**: Automated testing and validation in git workflows
**Example**: `> Run full test suite before allowing merge to main branch`

## Environmental Context for Git Operations

### Team Collaboration Context
- **Solo Development**: Simple linear workflows with quality emphasis
- **Small Team**: Coordination and communication focus
- **Large Team**: Process enforcement and conflict resolution
- **Open Source**: Community contribution and review processes

### Project Phase Context
- **Active Development**: Frequent feature integration
- **Release Preparation**: Stabilization and deployment focus
- **Maintenance**: Hotfix and patch management
- **Legacy**: Careful change management and testing

## Git Operations Behavioral Patterns

### Core Tenets Driving Git Operations

#### Professional Development Standards
- Systematic branch management
- Comprehensive PR descriptions
- Automated testing integration
- Code review requirements

#### Quality and Reliability Focus
- Testing before integration
- Staged deployment processes
- Rollback capability planning
- Monitoring and validation

#### Team Coordination
- Clear communication in commits and PRs
- Branch naming conventions
- Review assignment and tracking
- Release coordination

## Git Command Sequence Patterns

### Standard Feature Development Pattern
**Sequence**: Development → `/execute` → `/pr` → Review → Merge
**Usage**: Normal feature development workflow
**Success Rate**: High with proper testing and review

### Hotfix Pattern
**Sequence**: Issue → Branch → Fix → `/pr` → Fast Review → Deploy
**Usage**: Critical production issues requiring immediate attention
**Success Rate**: Moderate to high with proper testing

### Release Pattern
**Sequence**: Feature Freeze → Integration → `/pr` → Staging → Production
**Usage**: Coordinated release of multiple features
**Success Rate**: High with proper planning and testing

## Predictive Patterns for Git Operations

### High Git Operation Probability (0.6+ probability)
- Feature completion and readiness for review
- Deployment requirements after approval
- Release coordination activities
- Critical bug fixes requiring immediate deployment
- Team coordination and branch management needs

### Medium Git Operation Probability (0.3-0.6 probability)
- Work in progress requiring backup or sharing
- Experimental branch creation and management
- Code synchronization between team members
- Development environment updates

### Low Git Operation Probability (<0.3 probability)
- Initial project setup
- Configuration changes not requiring review
- Documentation-only updates
- Local development without sharing needs

## Success Indicators for Git Operations

### Process Execution Metrics
- **PR Creation Success**: Automated PR creation with proper metadata
- **Review Completion**: Timely and thorough code review process
- **Merge Success**: Clean integration without conflicts or issues
- **Deployment Success**: Successful deployment to target environment

### Quality Assurance Metrics
- **Test Coverage**: All automated tests passing before merge
- **Code Quality**: Code review approval and quality standards met
- **Documentation**: Proper commit messages, PR descriptions, and release notes
- **Rollback Capability**: Tested rollback procedures and monitoring

## Real Prompt Examples for Git Operations

### Pull Request Creation
```
> Create PR for user authentication system with comprehensive description
> Push to pr - notification feature complete with full test coverage
> Submit pull request for payment integration with security review required
> Ready for review: API enhancement with backward compatibility
> Generate PR for database migration with rollback procedures documented
```

### Branch Management
```
> Create feature branch for dashboard development
> Switch to develop branch to pick up latest changes
> Merge main branch updates into current feature branch
> Rebase feature branch on latest main to resolve conflicts
> Create hotfix branch from production tag for critical bug
```

### Deployment Operations
```
> Deploy to staging environment for QA validation
> Promote approved changes to production with monitoring
> Deploy hotfix to production with immediate rollback capability
> Release version 2.1.0 to production with database migrations
> Rollback last deployment due to performance issues
```

### Release Coordination
```
> Create release branch for version 2.0 with feature freeze
> Coordinate merge of all approved feature branches for release
> Tag production release with proper versioning and documentation
> Prepare release notes with all changes since last version
> Schedule deployment with coordinated team communication
```

### Quality Assurance Git Operations
```
> Run full test suite before allowing merge to main branch
> Validate all code review requirements completed before merge
> Ensure deployment checklist completed before production release
> Verify rollback procedures tested before major deployment
> Confirm all documentation updated before release tag creation
```

### Emergency Git Operations
```
> Create emergency hotfix for critical production security issue
> Fast-track review process for urgent payment processing fix
> Coordinate immediate deployment bypass for system outage resolution
> Implement emergency rollback for failed deployment affecting users
> Create patch release for critical bug affecting all customers
```

This analysis provides practical guidance for recognizing different git operation scenarios and implementing appropriate workflows based on urgency, team coordination needs, and quality requirements.
