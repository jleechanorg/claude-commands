# Zen MCP Implementation Guide

## Quick Start Guide

### 1. Installation

#### Option A: Quick Install (Recommended)
```bash
# Install and run Zen MCP Server
uvx run zen-mcp-server
```

#### Option B: Clone and Setup
```bash
# Clone repository
git clone https://github.com/BeehiveInnovations/zen-mcp-server.git
cd zen-mcp-server

# Run setup script
./run-server.sh  # Linux/Mac
# or
./run-server.ps1  # Windows
```

### 2. API Key Configuration

Create environment variables for your AI providers:

```bash
# Required: At least one of these
export GEMINI_API_KEY="your-gemini-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export OPENROUTER_API_KEY="your-openrouter-api-key"

# Optional: Additional providers
export DIAL_API_BASE="your-dial-api-base"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 3. Claude Code Integration

Create `.mcp.json` in your project root:

```json
{
  "mcpServers": {
    "zen-mcp": {
      "command": "zen-mcp-server",
      "args": [],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}"
      }
    }
  }
}
```

## Tool Usage Examples

### Project Planning
```
/zen:planner break down the authentication system implementation into manageable steps
```

### Code Review
```
/zen:codereview analyze the user management module for security vulnerabilities and best practices
```

### Debugging
```
/zen:debug investigate why the Flask session management is not working correctly
```

### Multi-Model Consensus
```
/zen:consensus use gpt-4:for and gemini:against to evaluate whether we should implement caching
```

### Deep Analysis
```
/zen:analyze examine the database schema and suggest optimization opportunities
```

## Best Practices

### 1. Model Selection Strategy
- **Quick tasks**: Use faster models (Gemini Flash, GPT-3.5)
- **Complex reasoning**: Use advanced models (GPT-4, Claude, Gemini Pro)
- **Cost optimization**: Start with cheaper models, escalate if needed

### 2. Context Management
- Use conversation threading for related tasks
- Leverage context revival for long-running projects
- Reference previous discussions in new queries

### 3. Security Considerations
- Store API keys securely (environment variables, not in code)
- Be cautious with sensitive code in multi-model conversations
- Review AI provider data policies

### 4. Workflow Integration
- Start with one tool at a time
- Build familiarity before expanding usage
- Create team guidelines for consistent usage

## Troubleshooting

### Common Issues

#### 1. API Key Errors
```
Error: Missing API key for provider
```
**Solution**: Verify environment variables are set correctly

#### 2. Connection Issues
```
Error: Failed to connect to MCP server
```
**Solution**: Check server is running and port is available

#### 3. Model Selection Errors
```
Error: Model not available or rate limited
```
**Solution**: Try different model or check provider status

### Debug Commands
```bash
# Check server status
ps aux | grep zen-mcp-server

# Test API keys
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# View server logs
tail -f ~/.local/share/zen-mcp-server/logs/server.log
```

## Advanced Configuration

### Custom Model Aliases
Edit `conf/custom_models.json`:
```json
{
  "aliases": {
    "fast": "gemini-1.5-flash",
    "smart": "gpt-4-turbo",
    "local": "ollama:llama3.1"
  }
}
```

### Tool-Specific Configuration
```json
{
  "tools": {
    "codereview": {
      "default_model": "gpt-4",
      "max_tokens": 4000,
      "temperature": 0.1
    },
    "planner": {
      "default_model": "gemini-pro",
      "max_tokens": 2000,
      "temperature": 0.7
    }
  }
}
```

## Performance Optimization

### 1. Caching Strategy
- Enable response caching for repeated queries
- Use local models for development/testing
- Implement request batching where possible

### 2. Cost Management
- Monitor API usage across providers
- Set up usage alerts
- Use cheaper models for non-critical tasks

### 3. Latency Optimization
- Choose geographically closer providers
- Use faster models for real-time interactions
- Implement request queuing for batch operations

## Team Adoption Strategy

### Phase 1: Individual Testing
- Install and configure on developer machines
- Test basic tools (chat, planner)
- Gather initial feedback

### Phase 2: Project Integration
- Add to specific projects
- Use for code reviews and planning
- Document team experiences

### Phase 3: Full Deployment
- Roll out to all development teams
- Provide training and guidelines
- Monitor usage and optimize

## Monitoring and Metrics

### Key Metrics to Track
- API usage and costs per provider
- Response times and error rates
- Developer adoption and satisfaction
- Productivity impact measurements

### Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "~/.local/share/zen-mcp-server/logs/server.log"
  }
}
```

## Integration with WorldArchitect.AI

### Specific Use Cases
1. **Game Logic Review**: Use codereview tool for D&D rule implementations
2. **Content Planning**: Use planner for story arc development
3. **Bug Investigation**: Use debug tool for game state issues
4. **Security Audit**: Use secaudit for user data protection

### Recommended Configuration
```json
{
  "mcpServers": {
    "zen-mcp": {
      "command": "zen-mcp-server",
      "args": [],
      "env": {
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

### Project-Specific Tools
- Use `analyze` for Flask architecture review
- Use `secaudit` for Firebase security assessment
- Use `planner` for feature development roadmaps
- Use `codereview` for AI prompt optimization

---

**Implementation Guide Version**: 1.0  
**Date**: 2025-01-06  
**Status**: Ready for Implementation