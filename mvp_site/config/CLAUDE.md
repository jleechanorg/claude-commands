# Configuration Management

This document inherits from the root project documentation. Please refer to `../../CLAUDE.md` for project-wide conventions and guidelines.

## Overview
Centralized configuration system for the MVP site application. Manages environment-specific settings, Firebase integration, and application parameters through a hierarchical configuration structure.

## File Inventory

### Core Configuration Files
- `__init__.py` - Package initialization and configuration factory
- `constants.py` - Application-wide constants and default values
- `settings.py` - Base configuration classes and environment management

### Environment-Specific Configurations
- Development environment settings managed through environment variables
- Staging environment configuration with Firebase staging instances
- Production environment settings with optimized performance parameters

## Configuration Architecture

### Environment Management
```python
# Configuration loading pattern
from mvp_site.config import get_config
config = get_config()  # Automatically detects environment
```

### Firebase Integration
- Firestore database configuration with collection settings
- Firebase Authentication configuration and user management
- Firebase Storage configuration for file uploads and assets

### Application Settings
- Flask application configuration with security settings
- CORS configuration for cross-origin request handling
- Logging configuration with structured output

## Technology-Specific Guidelines

### Python Configuration Patterns
- Use class-based settings with inheritance hierarchy
- Environment variables override file-based settings
- All configuration values must have defaults or be explicitly required
- Implement validation for critical configuration parameters

### Security Requirements
- Never commit secrets or API keys to version control
- Use environment-specific secret management
- Implement proper access controls for configuration data
- Validate all external configuration inputs

### Firebase Configuration
- Separate Firebase projects for development, staging, and production
- Service account key management for server-side operations
- Firestore security rules configuration and validation
- Authentication provider configuration (email, Google, etc.)

## Development Guidelines

### Configuration Loading
- Configuration loads at application startup
- Support for environment variable overrides
- Graceful degradation for missing optional settings
- Clear error messages for missing required configuration

### Validation Requirements
- All configuration parameters must be validated on load
- Type checking for configuration values
- Range validation for numeric parameters
- URL validation for external service endpoints

### Documentation Standards
- All configuration keys must be documented with purpose
- Environment-specific overrides require clear documentation
- Default values must be explained and justified
- Configuration changes require updates to this documentation

## Common Configuration Patterns

### Firebase Configuration
```python
FIREBASE_CONFIG = {
    'apiKey': os.getenv('FIREBASE_API_KEY'),
    'authDomain': os.getenv('FIREBASE_AUTH_DOMAIN'),
    'projectId': os.getenv('FIREBASE_PROJECT_ID'),
    'databaseURL': os.getenv('FIREBASE_DATABASE_URL')
}
```

### Flask Application Settings
```python
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    TESTING_AUTH_BYPASS = os.getenv('TESTING_AUTH_BYPASS', 'False').lower() == 'true'
```

### Logging Configuration
```python
LOGGING_CONFIG = {
    'level': os.getenv('LOG_LEVEL', 'INFO'),
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'handlers': ['console', 'file']
}
```

## Environment Variables

### Required Environment Variables
- `FIREBASE_PROJECT_ID` - Firebase project identifier
- `FIREBASE_API_KEY` - Firebase web API key
- `SECRET_KEY` - Flask application secret key

### Optional Environment Variables
- `FLASK_DEBUG` - Enable debug mode (default: False)
- `LOG_LEVEL` - Logging level (default: INFO)
- `TESTING_AUTH_BYPASS` - Enable testing mode (default: False)

## Quality Assurance

### Configuration Validation
- All critical configuration validated at startup
- Clear error messages for configuration issues
- Automated testing of configuration loading
- Environment-specific configuration testing

### Security Standards
- Regular rotation of secrets and API keys
- Access controls for configuration management
- Audit logging for configuration changes
- Encryption of sensitive configuration data

See also: [../../CLAUDE.md](../../CLAUDE.md) for complete project protocols and development guidelines.