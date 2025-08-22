# CLAUDE.md - Configuration Management

**Primary Rules**: Inherits from [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md) (complete project protocols)

**Module Type**: Configuration & Settings ({{CONFIG_TECHNOLOGY_STACK}})

## 🚨 MODULE-SPECIFIC PROTOCOLS
- All configuration parameters must be documented with types and defaults
- Environment-specific overrides must maintain backward compatibility
- Secret management follows zero-hardcoded-credentials policy
- Configuration validation required at application startup

## Directory Contents Analysis
**Configuration Files** ({{CONFIG_COUNT}} files):
{{CONFIG_FILES_LIST}}

**Environment Management**:
{{ENVIRONMENT_FILES}}

**Security & Secrets**:
{{SECURITY_CONFIG}}

## Configuration Parameter Documentation
{{PARAMETER_TABLE}}

## Environment-Specific Settings
**Development Configuration**:
- Local development overrides for {{DEV_SERVICES}}
- Debug logging enabled for troubleshooting
- Development API endpoints and mock services

**Production Configuration**:
- Performance-optimized settings for {{PROD_SERVICES}}
- Security-hardened configuration with minimal logging
- Production API endpoints and authentication

**Staging Configuration**:
- Near-production environment for testing
- Staging-specific service endpoints
- Enhanced monitoring for pre-production validation

## Validation Procedures
**Configuration Schema**:
{{SCHEMA_VALIDATION}}

**Runtime Validation**:
- Validate all required parameters on startup
- Fail fast with descriptive error messages
- Log configuration loading success/failure

## Security Considerations
**Secret Management**:
- Environment variables for all secrets (API keys, tokens, passwords)
- Never commit secrets to version control
- Regular secret rotation procedures

**API Key Management**:
{{API_KEY_MANAGEMENT}}

**Configuration Access Control**:
- Restrict configuration access to authorized modules
- Sanitize logs to prevent credential exposure
- Implement configuration change auditing

## Module Context
**Purpose**: Manages application configuration, environment settings, and secure credential handling for {{APPLICATION_SCOPE}}
**Role**: Central configuration authority ensuring consistent settings across environments with security best practices
**Parent Project**: {{PARENT_PROJECT}}

## Quick Reference
- **Complete Protocols**: See [{{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md]({{RELATIVE_PATH_TO_ROOT}}/CLAUDE.md)
- **Configuration Loading**: See main application initialization
- **Environment Variables**: Document all required variables in deployment guide
- **Secret Management**: Use environment-specific secret stores in production