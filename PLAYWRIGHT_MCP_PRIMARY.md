# 🚨 PLAYWRIGHT MCP: PRIMARY BROWSER TESTING METHOD

**MANDATORY**: Playwright MCP is the primary browser automation method for WorldArchitect.AI

## Why Playwright MCP is Primary

### ✅ **Technical Advantages**
- **AI-Optimized**: Accessibility-tree based approach designed for Claude Code
- **Zero Setup**: No local installation required (runs via MCP server)
- **Cross-Browser**: Chrome, Firefox, Safari support vs Puppeteer's Chrome-only
- **Microsoft Standard**: Official 2025 MCP server from Microsoft
- **Session Sharing**: Efficient test execution across multiple operations

### ✅ **2025 Industry Leadership**
Based on comprehensive research:
- "Playwright MCP Server currently leads due to its extensibility, multi-browser support, and tight integration with AI/LLM ecosystems"
- "Teams seeking AI-integrated browser automation are gravitating toward Playwright—especially when using the MCP standard"
- "Playwright is more future-proof for advanced automation and AI workflows in 2025"

## Required Tool Hierarchy

### 1. 🥇 **PRIMARY: Playwright MCP**
```bash
# Use Playwright MCP functions in Claude Code CLI
# Note: Replace ${MCP_HOST} and ${MCP_PORT} with the appropriate host and port for your test environment.
mcp__playwright-mcp__browser_navigate(`http://${MCP_HOST}:${MCP_PORT}?test_mode=true`)
mcp__playwright-mcp__browser_click(element="Login Button", ref="selector")
mcp__playwright-mcp__browser_take_screenshot(filename="test-state")
```

### 2. 🥈 **SECONDARY: Puppeteer MCP** 
For Chrome-specific testing only:
```bash
mcp__puppeteer-server__puppeteer_navigate("http://localhost:6006")
mcp__puppeteer-server__puppeteer_click("button[data-testid='login']")
```

### 3. 🥉 **FALLBACK: Local Playwright**
Only when MCP unavailable:
```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    # ... test code
```

## Command Integration

### Test Commands
- `/testui` = Browser tests with Playwright MCP + Mock APIs
- `/testuif` = Browser tests with Playwright MCP + Real APIs
- `/testserver start` = Start server for Playwright MCP testing

### Test URL Format
```text
http://localhost:6006?test_mode=true&test_user_id=test-123
```

## Implementation Requirements

### For New Tests
- ✅ **MUST use Playwright MCP** as first choice
- ✅ Use Puppeteer MCP only for Chrome-specific needs
- ✅ Use local Playwright only when MCP unavailable

### For Existing Tests
- 🔄 **Migration Status**: Existing files use local Playwright and need migration to Playwright MCP
- 📋 **Priority**: Migrate high-usage test files first
- 🎯 **Goal**: All new browser tests use Playwright MCP

## Function Reference

| Playwright MCP Function | Purpose |
|-------------------------|---------|
| `mcp__playwright-mcp__browser_navigate(url)` | Navigate to URL |
| `mcp__playwright-mcp__browser_click(element, ref)` | Click elements |
| `mcp__playwright-mcp__browser_type(element, ref, text)` | Fill forms |
| `mcp__playwright-mcp__browser_take_screenshot(filename)` | Capture screenshots |
| `mcp__playwright-mcp__browser_snapshot()` | Get accessibility tree |
| `mcp__playwright-mcp__browser_wait_for(text/time)` | Wait for conditions |

## Testing Protocol

### Authentication Bypass
All browser tests must use URL parameters for auth bypass:
- `test_mode=true` - Enables authentication bypass
- `test_user_id=test-123` - Sets test user ID

### Error Handling
- Use `browser_wait_for()` for asynchronous operations
- Take screenshots on failures for debugging
- Use accessibility tree data for element analysis

## Compliance

This establishes Playwright MCP as the mandatory primary browser testing method, with proper fallback hierarchy and comprehensive usage guidance.