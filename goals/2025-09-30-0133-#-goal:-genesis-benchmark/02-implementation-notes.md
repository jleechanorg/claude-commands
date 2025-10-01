# Genesis TypeScript MCP Server Implementation Notes

## Architecture Overview
The TypeScript MCP server follows FastMCP patterns with Express.js as the core framework. The implementation will mirror the Python structure:

1. **Entry Points**: HTTP server (`server.ts`) and stdio server (`stdio-server.ts`)
2. **MCP Tools Layer**: Centralized tool registration and input processing
3. **Service Layer**: Campaign, Interaction, Export, Settings services with Firebase integration
4. **Repository Layer**: Data access abstraction over Firestore operations
5. **Configuration Layer**: Environment management and external service setup

## Key Technical Decisions

### Firebase Integration
- Use Firebase Admin SDK with Application Default Credentials
- Implement repository pattern for Firestore operations
- Mirror Python query structures exactly (campaigns by user_id, interactions by campaign_id)
- Handle document references and subcollections appropriately

### Gemini AI Implementation
- Use Google Generative AI SDK for TypeScript
- Replicate Python prompt engineering patterns
- Implement identical response processing and error handling
- Add request/response logging for validation

### Express.js Server Design
- Follow FastMCP HTTP entrypoint patterns
- Implement middleware for authentication, logging, security headers
- Structure routes to match Python Flask endpoints exactly
- Add comprehensive error handling with consistent response formats

### Testing Strategy
- Create Jest mocks for Firebase and Gemini services
- Replicate Python test scenarios exactly
- Add integration tests for API endpoints
- Implement test coverage reporting

## Implementation Sequence
1. Setup project structure with package.json and tsconfig
2. Create configuration layer with environment variable loading
3. Implement repository layer with Firestore operations
4. Build service layer with business logic
5. Register MCP tools and create entrypoints
6. Add comprehensive testing with mocks
7. Create deployment configuration (Dockerfile, cloudbuild)
8. Validate against Python reference implementation

## Critical Success Factors
- Maintain strict adherence to existing API contracts
- Ensure all Firestore queries use identical patterns
- Preserve Gemini AI prompt/response structures
- Complete all test scenarios with documented evidence
- Follow commit protocol for progress tracking
