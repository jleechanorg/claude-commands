# GENESIS.md - Enhanced Workflow Optimization Protocol

## Successful Patterns
- **Path Validation First**: Always validate file paths exist before attempting operations
- **Search Before Build**: Use existing codebase structures rather than creating duplicate functionality
- **Structured Validation Protocol**: Honor search recommendations when path mismatches detected
- **Clear Scope Boundaries**: Distinguish between separate project concerns (`genesis/` vs main codebase)
- **Direct Implementation Over Analysis**: Skip excessive planning when validation is conclusive
- **Django App Creation**: Complete app structure with models, management commands, tests, and migrations
- **PYTHONPATH Configuration**: Proper module resolution for complex Django project structures
- **Production-Ready Implementation**: Full validation, error handling, and admin interface integration
- **InfluxDB Integration Success**: Complete client with tenant-aware buckets, comprehensive error handling
- **Test-First Development**: Comprehensive test suite (7 tests) validates database layer before app layer
- **Enterprise Patterns Applied**: Proper exception handling, connection management, and multi-tenant architecture

## Avoid These Patterns
- **Path Assumptions**: Never assume target paths exist without verification
- **Duplicate Creation**: Avoid building functionality that already exists in codebase
- **Over-Engineering Simple Tasks**: Don't create complex workflows for straightforward validation
- **Context Pollution**: Don't generate excessive output when task is complete
- **Ignoring Existing Implementations**: Always check for current solutions before building new ones
- **Database Connection Dependencies**: Don't halt implementation for non-critical database connectivity
- **Migration Timing Assumptions**: Expect existing app structures may be more complex than anticipated
- **Analysis Paralysis**: Don't get stuck in planning loops when iterative implementation proves progress
- **Component-First Development**: Avoid building all components simultaneously; focus on sequential integration
- **Premature Optimization**: Implement working solutions before performance tuning

## Genesis Optimizations
- **Context Conservation**: Complete validation tasks immediately rather than planning phases
- **Subagent Efficiency**: Single-focus validation agents prevent scope creep
- **Reality-First Approach**: Validate actual codebase state before theoretical improvements
- **Clear Exit Criteria**: Define completion status explicitly (100% for validation complete)
- **Path Resolution Protocol**: Distinguish between target paths and actual implementation locations
- **Direct Execution Over Delegation**: For focused implementation work, execute directly vs expensive generation
- **Progressive Discovery Protocol**: Build incrementally as complexity is discovered (existing models, etc.)
- **Test-Driven Validation**: Implement comprehensive test suites for verification and confidence
- **Layer-by-Layer Construction**: Database → Tests → Application → Integration sequence proven effective
- **Focused Implementation**: Complete one major component fully before starting next (17% → 100% approach)
- **Real Integration Testing**: Use actual services (InfluxDB) in test environment for validation

## Core Genesis Principles Applied
- **Prime Mover Principle**: Led with validation analysis, followed with decisive action (skip task)
- **Architectural Thinking**: Recognized existing Django package structure integrity
- **Multi-Perspective Analysis**: Evaluated both target requirements and existing implementation
- **Context Efficiency**: Minimal tool usage for maximum clarity on task status

## Next Iteration Improvements
- **Multi-Tenant Clarification**: Distinguish between separate projects vs integration requirements
- **Scope Definition Protocol**: Clarify whether `genesis/` directory is independent concern
- **Integration Assessment**: Evaluate existing vs required functionality before task execution
- **Database Environment Setup**: Include PostgreSQL service validation in development workflow
- **Complex App Structure Navigation**: Expect and handle existing Django apps with multiple models/configurations
- **Migration Verification Protocol**: Test actual migration execution when database connectivity available
- **WebSocket Implementation Priority**: Real-time communication layer is critical next milestone
- **Service Integration Order**: InfluxDB ✅ → WebSocket Server → Flask Endpoints → Docker Services → Analytics Engine
- **Progress Tracking**: Maintain completion percentages for visibility into major milestones
