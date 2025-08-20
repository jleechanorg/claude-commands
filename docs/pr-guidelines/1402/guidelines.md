# PR #1402 Guidelines - Stop Serena MCP Server Auto-Browser Opening

**PR**: #1402 - Stop the Serena MCP Server from automatically opening a web browser
**Created**: August 20, 2025
**Purpose**: Specific guidelines for Serena MCP configuration standardization and team setup

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1402.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### 1. **Team Configuration Standardization**
- **Pattern**: Configuration files in `.serena/` directory for team-wide consistency
- **Evidence**: Created standardized `serena_config.yml` with consistent dashboard behavior
- **Learning**: Team configs prevent individual environment differences

### 2. **Hardcoded Path Prevention**
- **Critical Pattern**: Never include user-specific paths in team configuration files
- **Evidence**: Initially included `/Users/jleechan/projects/...` causing bot feedback
- **Solution**: Use empty arrays with auto-population comments for user-specific data

## 🚫 PR-Specific Anti-Patterns

### **Configuration Path Hardcoding**
```yaml
# ❌ WRONG - Hardcoded user paths in team config
projects:
  - name: worldarchitect.ai
    path: /Users/jleechan/projects/worldarchitect.ai/worktree_worker1

# ✅ CORRECT - Empty with auto-population explanation  
projects: []
# Project paths are auto-generated per user when activating projects through Serena chat commands.
# This prevents hardcoded user-specific paths that won't work for other team members.
```

### **Incomplete Comment Coverage Response**
- **Problem**: Initial 50% coverage (1 reply for 2 original comments)
- **Solution**: Comprehensive issue comment addressing both bots plus individual responses
- **Pattern**: Ensure 100% coverage through both threaded and general responses

## 📋 Implementation Patterns for This PR

### **Serena MCP Configuration Structure**
```yaml
# Core dashboard control
web_dashboard: true                    # Enable dashboard functionality
web_dashboard_open_on_launch: false   # Prevent auto-browser opening
log_level: 20                         # Info level logging

# Team-safe user data
projects: []                          # Auto-populated per user
# Explanatory comment about why empty
```

### **Team Documentation Approach**
- **Setup Instructions**: Clear copy commands for user directory setup
- **Manual Access**: Explicit URLs and port fallback instructions
- **Troubleshooting**: Common issues and resolution steps
- **Team Usage**: Emphasize local copy requirement for consistency

### **Bot Comment Resolution Protocol**
1. **Identify Issues**: Extract specific problems from bot comments
2. **Fix Systematically**: Address root cause (hardcoded paths)
3. **Respond Comprehensively**: Both threaded replies and general issue comments
4. **Verify Coverage**: Ensure 100% comment coverage before completion

## 🔧 Specific Implementation Guidelines

### **For Similar Configuration PRs**
1. **Check for Hardcoded Paths**: Scan all config files for user-specific paths
2. **Use Auto-Population Comments**: Explain why sections are empty/auto-filled
3. **Provide Team Setup Instructions**: Clear steps for local configuration
4. **Document Manual Access**: Alternative ways to access functionality

### **For Bot Comment Response**
1. **Address All Comments**: Never leave bot feedback unaddressed
2. **Use Issue Comments**: General responses for broad architectural feedback
3. **Use Review Comments**: Specific responses for line-by-line feedback
4. **Verify Coverage**: Check GitHub API for 100% response rate

### **Performance Optimization Opportunities**
- **Target Time**: 2-3 minutes for copilot execution
- **Actual Time**: 5m 3s (exceeded target by 2+ minutes)
- **Optimization Areas**: Parallel comment processing, cached pattern recognition
- **Success Factors**: 100% comment coverage, systematic issue resolution

## 🎯 Key Learnings

### **Configuration Sharing Best Practices**
- Empty arrays with explanatory comments prevent team conflicts
- User-specific data should auto-populate, not be hardcoded
- Documentation must explain why certain sections appear empty

### **GitHub Bot Integration**
- Both Copilot and Cursor bots flag similar issues (user-specific paths)
- Comprehensive responses ensure automated feedback loops close properly
- Issue comments complement review comments for full coverage

### **Copilot Workflow Optimization**
- 9-phase workflow successfully identified and resolved all issues
- Performance exceeded target but maintained quality
- Pattern capture enables continuous improvement

---
**Status**: Template enhanced with PR #1402 specific patterns and learnings
**Last Updated**: August 20, 2025
**Coverage**: 100% comment resolution, 5m 3s execution time
**Key Pattern**: Hardcoded path prevention in team configuration files