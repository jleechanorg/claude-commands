# Services Layer Architecture

This document inherits from the root project documentation. Please refer to `../../CLAUDE.md` for project-wide conventions and guidelines.

## Overview
The services layer handles business logic, external integrations, and data management for the MVP application. Services provide a clean abstraction between controllers and data access layers.

## Key Components

### Firebase Integration Services
- `firebase_service.py` - Core Firebase client setup and connection utilities
- `firestore_service.py` - Firestore database operations and query management
- `auth_service.py` - Firebase Authentication integration and user management
- Implements retry logic and error handling for network calls
- Manages connection pooling and rate limiting

### Core Business Services
- `campaign_service.py` - Campaign creation, editing, and lifecycle management
- `user_service.py` - User profile management and preferences
- `content_service.py` - Content generation and validation
- `analytics_service.py` - Usage tracking and performance metrics

### AI Integration Services
- `llm_service.py` - Language model integration for content generation
- `prompt_service.py` - AI prompt management and optimization
- Handles AI response validation and fallback strategies

## Development Guidelines

### Service Design Principles
1. **Single Responsibility** - Each service focuses on one business domain
2. **Stateless Operations** - Services maintain no internal state between calls
3. **Dependency Injection** - External dependencies injected for testability
4. **Error Handling** - Comprehensive exception handling with meaningful messages
5. **Logging Integration** - Structured logging with correlation IDs

### Security Requirements
- **Input Validation** - All service inputs validated before processing
- **Authentication** - User context validated for protected operations
- **Data Sanitization** - User data sanitized to prevent injection attacks
- **Access Control** - Role-based permissions enforced at service level

### Common Service Patterns

#### Service Method Structure
```python
def create_campaign(self, user_id: str, campaign_data: dict) -> dict:
    # 1. Validate inputs
    self._validate_campaign_data(campaign_data)
    
    # 2. Check permissions
    if not self._user_can_create_campaign(user_id):
        raise AuthorizationError("Insufficient permissions")
    
    # 3. Business logic
    campaign = self._process_campaign_creation(campaign_data)
    
    # 4. Persist data
    campaign_id = self.firestore.create_campaign(campaign)
    
    # 5. Return result
    return {'success': True, 'campaign_id': campaign_id}
```

#### Error Handling Pattern
```python
try:
    result = external_service.call()
except ExternalServiceError as e:
    logger.error(f"Service call failed: {e}", extra={'correlation_id': request_id})
    raise ServiceUnavailableError("External service temporarily unavailable")
```

## Testing Standards

### Unit Testing
- Mock all external dependencies (Firebase, AI services)
- Test business logic in isolation
- Validate error handling paths
- Ensure proper input validation

### Integration Testing
- Test service interactions with real Firebase instances
- Validate end-to-end workflows
- Test error recovery and retry mechanisms
- Performance testing for critical paths

## Quality Assurance

### Code Quality
- Type hints required for all public methods
- Docstrings for complex business logic
- Code coverage target: 95%+ for service layer
- Regular security audits for data handling

### Performance Standards
- Response time targets: <200ms for simple operations
- Batch operations for bulk data processing
- Caching strategies for frequently accessed data
- Monitoring and alerting for service health

See also: [../../CLAUDE.md](../../CLAUDE.md) for complete project protocols and development guidelines.
