# PR #1782 Guidelines - Render MCP Server Integration

**PR**: #1782 - Render MCP Server Integration
**Created**: 2025-09-29
**Purpose**: Specific guidelines for Render MCP server integration development and review

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1782.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### 1. **Infrastructure as Code First**
- All Render MCP configurations must be defined in version-controlled render.yaml Blueprints
- Never rely on manual Render dashboard configuration for reproducible deployments
- Test Blueprint validity before merging

### 2. **Security-First API Integration**
- API keys must NEVER appear in command line arguments (visible via `ps`)
- Use secure JSON stdin for authentication headers
- Implement comprehensive API key redaction in all log outputs
- Validate escaping for special characters in JSON payloads

### 3. **Solo Developer Security Focus**
- Filter out enterprise paranoia anti-patterns
- Focus on real vulnerabilities with actual exploit paths
- Prioritize usability while maintaining essential security controls

## 🚫 PR-Specific Anti-Patterns

### **API Key Exposure Vulnerabilities**
```bash
# ❌ CRITICAL SECURITY VULNERABILITY - API keys in command line
claude mcp add --header "Authorization: Bearer $RENDER_API_KEY" render
# Visible in process list via `ps` command - severe security risk

# ✅ SECURE IMPLEMENTATION - JSON stdin with redaction
add_output=$(claude mcp add-json --scope user "render" - 2>&1 <<EOF
{"type":"http","url":"https://mcp.render.com/mcp","headers":{"Authorization":"Bearer $escaped_api_key"}}
EOF
)
add_output_redacted=${add_output//${RENDER_API_KEY}/<RENDER_API_KEY>}
```

### **Fragile Logic Patterns**
```bash
# ❌ FRAGILE ANTI-PATTERN - Increment then decrement pattern
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))
# ... logic that might fail ...
TOTAL_SERVERS=$((TOTAL_SERVERS - 1))  # Creates coupling and fragility

# ✅ ROBUST PATTERN - Consistent counting at decision points
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))  # Count at start of installation attempt
# No conditional decrements - counter reflects actual attempts
```

### **JSON Escaping Oversights**
```bash
# ❌ UNESCAPED JSON GENERATION - Breaks with special characters
{"Authorization":"Bearer $RENDER_API_KEY"}  # Fails if key contains quotes/backslashes

# ✅ PROPER JSON ESCAPING - Handles all special characters
escaped_api_key="${RENDER_API_KEY//\\/\\\\}"  # Escape backslashes
escaped_api_key="${escaped_api_key//\"/\\\"}"    # Escape quotes
{"Authorization":"Bearer $escaped_api_key"}
```

## 📋 Implementation Patterns for This PR

### **MCP Server Registration Pattern**
1. **Configuration Validation**: Verify API key and endpoint accessibility
2. **Secure Registration**: Use JSON stdin with proper escaping
3. **Error Handling**: Comprehensive output redaction
4. **State Management**: Consistent server counting without correction logic

### **Binary Response Protocol for PR Comments**
- Use `[AI responder] ✅ **DONE**: [technical details]` format
- Include specific file locations and line numbers for all fixes
- Provide git verification commands for all claimed implementations
- Apply zero-tolerance coverage standard (100% of comments addressed)

### **Evidence-Based Development Protocol**
- All security fixes must include before/after code examples
- Provide specific git commands for verification
- Document exact file locations and line numbers for changes
- Include rationale for chosen implementation approach over alternatives

## 🔧 Specific Implementation Guidelines

### **API Key Security Implementation**
```bash
# Required escaping sequence for JSON safety
escaped_api_key="${RENDER_API_KEY//\\/\\\\}"  # Handle backslashes first
escaped_api_key="${escaped_api_key//\"/\\\"}"    # Then handle quotes

# Secure JSON generation pattern
add_output=$(claude mcp add-json --scope user "render" - 2>&1 <<EOF
{"type":"http","url":"https://mcp.render.com/mcp","headers":{"Authorization":"Bearer $escaped_api_key"}}
EOF
)

# Mandatory output redaction for logs
add_output_redacted=${add_output//${RENDER_API_KEY}/<RENDER_API_KEY>}
```

### **Server Counting Logic Pattern**
```bash
# Count at start of section (consistent with other servers)
TOTAL_SERVERS=$((TOTAL_SERVERS + 1))

# No conditional decrements - counter reflects installation attempts
# This creates predictable counting behavior matching other server types
```

### **Error Handling with Redaction**
```bash
# All error outputs must use redacted versions
if [[ $? -ne 0 ]]; then
    echo "Error: MCP add command failed"
    echo "$add_output_redacted" | log_message  # Console output
    log_message "$add_output_redacted"         # Log file output
fi
```

### **Comment Response Protocol**
- Every comment must receive either DONE implementation or explicit NOT DONE response
- Technical responses must include working code examples
- All responses must reference specific git commit evidence
- Use binary classification (DONE/NOT DONE) for clear status tracking

## 🚨 Critical Security Requirements

### **Command Line Safety**
- NEVER pass sensitive data via command line arguments
- Use stdin, environment variables, or configuration files for secrets
- Validate all inputs before processing

### **Log Security**
- Redact API keys from ALL logged output
- Apply redaction before any echo, log, or error message
- Include both successful and error output redaction

### **JSON Payload Security**
- Escape ALL special characters before JSON generation
- Test JSON validity with complex API keys containing quotes/backslashes
- Validate escaping preserves authentication functionality

## 📊 Quality Gates for This PR

### **Security Validation**
- [ ] No API keys visible in process arguments via `ps` command
- [ ] All log outputs properly redacted
- [ ] JSON escaping handles quotes, backslashes, and other special characters
- [ ] Error handling preserves security through redaction

### **Logic Validation**
- [ ] Server counting consistent with other server types
- [ ] No fragile increment/decrement coupling patterns
- [ ] Error paths handle edge cases gracefully
- [ ] State management predictable and debuggable

### **Integration Validation**
- [ ] MCP server registration successful with test API keys
- [ ] render.yaml Blueprint syntax valid
- [ ] Error messages informative without exposing secrets
- [ ] Uninstallation process removes configurations cleanly

### **Comment Coverage Validation**
- [ ] 100% of PR comments addressed with DONE/NOT DONE responses
- [ ] All DONE responses include working implementation evidence
- [ ] Git verification commands provided for all fixes
- [ ] Binary protocol followed for clear status tracking

---
**Status**: Created by /guidelines command - comprehensive guidelines for Render MCP integration
**Last Updated**: 2025-09-29
**Evidence Location**: claude_mcp.sh lines 1440-1500 (core implementation)
