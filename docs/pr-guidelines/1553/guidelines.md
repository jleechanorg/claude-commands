# PR #1553 Guidelines - MCP Slash Commands Global Installation

## Context
- **PR Focus**: MCP slash commands global installation with uvx
- **Key Technologies**: Python packaging, uvx, shell scripting, security hardening
- **Security Priority**: High - subprocess security and shell injection prevention

## Patterns Applied Successfully
✅ **FILE JUSTIFICATION PROTOCOL**:
- Applied comprehensive file justification for all new files
- Verified integration attempts before file creation
- Documented necessity and integration proof

✅ **SECURITY-FIRST APPROACH**:
- Eliminated shell injection vulnerabilities with shell=False
- Added timeout parameters to prevent hanging subprocess calls
- Implemented comprehensive security testing validation

✅ **PARALLEL AGENT ORCHESTRATION**:
- copilot-fixpr: Technical implementation and security fixes
- copilot-analysis: Comment processing and communication coordination
- Effective separation of concerns and tool usage boundaries

## Anti-Patterns Avoided
❌ **Shell Injection Risks**: Avoided shell=True in subprocess calls
❌ **Missing Timeouts**: Added timeout parameters to all subprocess operations
❌ **Inadequate Testing**: Created comprehensive test suite with security focus

## Lessons Learned
🎯 **Agent Coordination**: Parallel agents need clear tool boundaries
🎯 **Security Testing**: Comprehensive security test suites catch vulnerabilities
🎯 **Package Configuration**: Production-ready pyproject.toml prevents deployment issues

## Implementation Guidelines
- Always use shell=False for subprocess security
- Include timeout parameters for all subprocess calls
- Create comprehensive test suites for new functionality
- Follow FILE JUSTIFICATION PROTOCOL for all file creation
- Apply security-first approach to all subprocess operations

## Success Metrics
- Zero shell injection vulnerabilities
- Comprehensive test coverage
- Production-ready package configuration
- FILE JUSTIFICATION PROTOCOL compliance
