# Token Management System

This document describes the centralized token management system for WorldArchitect.AI MCP servers and external API integrations.

## Overview

The token management system provides a secure, centralized way to manage API tokens for various services including GitHub and Perplexity. It consolidates token loading, validation, and configuration across all project scripts.

## System Components

### 1. Centralized Token Helper (`scripts/load_tokens.sh`)

The main component that provides:
- **Token Loading**: Securely loads tokens from `~/.token` file
- **Validation**: Validates token formats for known services
- **Testing**: Tests token functionality with live API calls
- **Template Creation**: Creates template token files for new users
- **Status Reporting**: Provides detailed token configuration status

### 2. Updated MCP Installation Script (`claude_mcp.sh`)

Enhanced to use the centralized token system with:
- **Centralized Loading**: Uses `scripts/load_tokens.sh` for all token operations
- **Fallback Support**: Legacy token loading as backup
- **Enhanced Validation**: Better token validation and error reporting
- **Improved Logging**: Detailed logging of token loading events

### 3. Test Validation Script (`test_mcp_search_servers.sh`)

Already configured to use the `~/.token` file for testing token availability.

## Token Configuration

### Creating the Token File

1. **Generate Required Tokens**:
   - **GitHub**: https://github.com/settings/tokens
     - Required scopes: `repo`, `read:org`, `read:user`
   - **Perplexity**: https://www.perplexity.ai/settings/api

2. **Create Token File**:
   ```bash
   # Create the token file
   ./scripts/load_tokens.sh create

   # Edit with your actual tokens
   nano ~/.token
   ```

3. **Token File Format**:
   ```bash
   # Token Configuration File
   # This file should be kept secure with chmod 600 permissions

   # GitHub Personal Access Token
   # Generate at: https://github.com/settings/tokens
   # Required scopes: repo, read:org, read:user
   export GITHUB_TOKEN="ghp_your_github_token_here"

   # Perplexity API Key (optional)
   # Generate at: https://www.perplexity.ai/settings/api
   export PERPLEXITY_API_KEY="pplx_your_perplexity_token_here"
   ```

4. **Secure the File**:
   ```bash
   chmod 600 ~/.token
   ```

## Usage

### Command Line Interface

The token helper script provides several commands:

```bash
# Load tokens (default command)
./scripts/load_tokens.sh load

# Check token configuration status
./scripts/load_tokens.sh status

# Test GitHub token with live API call
./scripts/load_tokens.sh test

# Create template token file
./scripts/load_tokens.sh create

# Show help
./scripts/load_tokens.sh help
```

### In Scripts

Scripts can use the centralized token system by sourcing the helper:

```bash
# Source the token helper
source scripts/load_tokens.sh

# Load tokens
if load_tokens; then
    echo "Tokens loaded successfully"
    # Use $GITHUB_TOKEN, $PERPLEXITY_API_KEY, etc.
else
    echo "Failed to load tokens"
    exit 1
fi

# Check if specific tokens are loaded
if [ "$GITHUB_TOKEN_LOADED" = true ]; then
    # Use GitHub functionality
fi

if [ "$PERPLEXITY_TOKEN_LOADED" = true ]; then
    # Use Perplexity functionality
fi
```

## Token Validation

### GitHub Token Validation

- **Format Validation**: Checks for valid GitHub token patterns:
  - Classic tokens: `ghp_[36 alphanumeric characters]`
  - Fine-grained tokens: `github_pat_[82 alphanumeric/underscore characters]`
- **API Validation**: Tests token with GitHub API `/user` endpoint
- **Scope Verification**: Ensures token has required permissions

### Perplexity Token Validation

- **Format Validation**: Checks for valid Perplexity token pattern:
  - Format: `pplx-[40+ alphanumeric characters]`

## Security Features

### Token Protection

1. **File Permissions**: Enforces `chmod 600` on token file
2. **Process Hiding**: Uses temporary curl config to hide tokens from process listings
3. **Secure Transmission**: Tokens never exposed in command line arguments
4. **Validation**: Checks token formats before use

### Error Handling

- **Graceful Degradation**: Services work with reduced functionality if tokens missing
- **Clear Error Messages**: Detailed guidance for token setup and troubleshooting
- **Logging**: Comprehensive logging without exposing sensitive data

## Troubleshooting

### Common Issues

1. **Token File Not Found**:
   ```bash
   ./scripts/load_tokens.sh create
   # Edit ~/.token with your actual tokens
   ```

2. **Invalid Token Format**:
   ```bash
   ./scripts/load_tokens.sh status
   # Check token format against documentation
   ```

3. **Token Expired**:
   ```bash
   ./scripts/load_tokens.sh test
   # Regenerate token if test fails
   ```

4. **Permission Issues**:
   ```bash
   chmod 600 ~/.token
   ```

### Debug Mode

For debugging token issues:

```bash
# Check detailed status
./scripts/load_tokens.sh status

# Test GitHub token with detailed output
./scripts/load_tokens.sh test

# Check MCP server logs
tail -f /tmp/claude_mcp_*.log
```

## Migration Guide

### From Project Root `.token` to `~/.token`

If you have an existing `.token` file in the project root:

1. **Move the file**:
   ```bash
   mv .token ~/.token
   chmod 600 ~/.token
   ```

2. **Update format if needed**:
   ```bash
   # Old format (single token)
   ghp_your_token_here

   # New format (environment variables)
   export GITHUB_TOKEN="ghp_your_token_here"
   export PERPLEXITY_API_KEY="pplx_your_token_here"
   ```

3. **Test the migration**:
   ```bash
   ./scripts/load_tokens.sh status
   ./scripts/load_tokens.sh test
   ```

### Script Updates

Scripts using the old token loading method should be updated to use the centralized system:

```bash
# OLD: Direct file reading
if [ -f ".token" ]; then
    GITHUB_TOKEN=$(cat .token)
fi

# NEW: Centralized loading
source scripts/load_tokens.sh
if load_tokens; then
    # Tokens are now available as environment variables
fi
```

## Integration with MCP Servers

### GitHub MCP Server

Uses the centralized token system for:
- Private repository access
- API rate limit increases
- Enhanced functionality

### Perplexity Search Server

Uses the centralized token system for:
- AI-powered search capabilities
- Real-time web research
- Advanced query processing

### Future Extensions

The system is designed to easily support additional tokens:
- Add new token validation functions
- Update the token file template
- Extend the loading logic

## Best Practices

1. **Security**:
   - Never commit token files to version control
   - Use minimum required token scopes
   - Regularly rotate tokens
   - Monitor token usage in logs

2. **Maintenance**:
   - Test tokens periodically
   - Update documentation when adding new services
   - Use consistent naming conventions
   - Log token-related events for debugging

3. **Development**:
   - Use the centralized system for all new scripts
   - Provide fallback behavior for missing tokens
   - Include clear error messages for token issues
   - Test both authenticated and unauthenticated paths

## Related Files

- `scripts/load_tokens.sh` - Main token helper script
- `claude_mcp.sh` - MCP installation script using centralized tokens
- `test_mcp_search_servers.sh` - Test script for MCP search servers
- `~/.token` - User token configuration file
- `/tmp/claude_mcp_*.log` - MCP installation logs
