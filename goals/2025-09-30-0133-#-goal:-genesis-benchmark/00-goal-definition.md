# Genesis TypeScript MCP Server Implementation Goal

## Refined Goal Analysis
Implement a TypeScript-based FastMCP server in `/Users/jleechan/projects_other/worldai_genesis2` that reproduces the Python MCP server at `/Users/jleechan/projects/worktree_ralph/mvp_site/`, including identical API behavior, Firestore persistence, Gemini AI integrations, and full automated/manual test parity.

## Context & Requirements
The WorldArchitect AI Python Flask backend implements a complete Model Context Protocol server with campaign management, player interactions, document exports, and user settings. The TypeScript migration must:

1. **Replicate Core Functionality**: All 10+ MCP tools and REST API endpoints
2. **Preserve Data Contracts**: Firestore document schemas and Gemini AI response structures
3. **Maintain Test Parity**: Execute identical validation scenarios from `/Users/jleechan/projects/worktree_ralph/testing_llm/`
4. **Follow FastMCP Patterns**: Use Express.js with FastMCP factory functions for HTTP/stdio compatibility

## Technical Scope
- Express.js REST API server with health checks and MCP tool registration
- Firebase Admin SDK integration with Firestore persistence
- Google Generative AI (Gemini) service implementation
- Jest testing framework with comprehensive mocks
- Dockerfile and deployment configuration
- Environment variable management with credential copying

## Success Definition
A production-ready TypeScript MCP server that passes all existing tests and demonstrates functional parity with the Python reference implementation through documented evidence of identical behavior.
