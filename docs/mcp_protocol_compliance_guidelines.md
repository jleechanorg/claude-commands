# MCP Protocol Compliance & Async Safety Guidelines

**Document Created**: 2025-08-26  
**Branch**: mcp-async-fixes-extracted  
**Status**: Production Guidelines

## Purpose

This document establishes mandatory guidelines to prevent MCP (Model Context Protocol) compliance violations and async event loop conflicts that can break core application functionality.

## Critical Issues Addressed

### 1. MCP JSON-RPC Protocol Compliance Break (CRITICAL)
- **Issue**: Custom payload format breaking JSON-RPC 2.0 standard
- **Impact**: Makes MCP client incompatible with standard MCP servers
- **Resolution**: Restore standard JSON-RPC protocol using existing helper methods

### 2. Unsafe Async Event Loop Usage (CRITICAL)  
- **Issue**: Direct `asyncio.run()` usage causing RuntimeError in existing event loops
- **Impact**: Test failures and potential production async conflicts
- **Resolution**: ThreadPoolExecutor pattern for safe async execution

### 3. Boolean Logic Inversion (HIGH)
- **Issue**: Inverted boolean flags causing opposite behavior
- **Impact**: MCP HTTP mode controlled by wrong flag logic
- **Resolution**: Correct conditional logic with proper defaults

## Mandatory Guidelines

### G1: MCP JSON-RPC Protocol Standards

**🚨 CRITICAL RULE**: All MCP communication must use standard JSON-RPC 2.0 protocol

**Requirements:**
- ✅ Use JSON-RPC 2.0 format for all MCP tool calls
- ✅ Use protocol helpers (`_make_jsonrpc_request`, `_handle_jsonrpc_response`)
- ❌ NEVER use custom payload formats
- ❌ NEVER bypass error handling/validation

**Code Pattern:**
```python
# ✅ CORRECT - Standard JSON-RPC
params = {"name": tool_name}
if arguments is not None:
    params["arguments"] = arguments
request_data = self._make_jsonrpc_request("tools/call", params)
response = self.session.post(
    f"{self.base_url}/mcp",
    json=request_data,
    timeout=self.timeout
)
response.raise_for_status()
response_data = response.json()
result = self._handle_jsonrpc_response(response_data)
```

### G2: Async Event Loop Safety

**🚨 CRITICAL RULE**: NEVER use unsafe `asyncio.run()` in environments with existing event loops

**Requirements:**
- ✅ Always check for existing event loop before `asyncio.run()`
- ✅ Use ThreadPoolExecutor pattern for nested async execution
- ❌ NEVER assume no event loop exists without checking
- ❌ NEVER use bare `asyncio.run()` in test methods

**Safe Pattern:**
```python
# ✅ CORRECT - Safe async execution  
try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    # No event loop running, safe to use asyncio.run
    return asyncio.run(self.call_tool(tool_name, arguments))
else:
    # Already in an event loop, use thread pool with proper async handling
    def sync_wrapper():
        # Create new event loop in thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            return new_loop.run_until_complete(self.call_tool(tool_name, arguments))
        finally:
            new_loop.close()
            
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(sync_wrapper)
        return future.result()
```

### G3: Boolean Logic & Flag Handling

**🚨 HIGH PRIORITY RULE**: Boolean flags must have clear, predictable behavior

**Requirements:**
- ✅ Explicit conditional logic with clear defaults
- ✅ Comments explaining flag behavior and expected values
- ❌ NEVER use simple boolean inversion without null checks
- ❌ NEVER assume CLI argument parsing behavior

**Safe Pattern:**
```python
# ✅ CORRECT - Explicit conditional with default  
# Default: use HTTP mode (i.e., do NOT skip HTTP) unless the CLI explicitly disables it
app._skip_mcp_http = (not args.mcp_http) if (args.mcp_http is not None) else False

# ❌ WRONG - Simple inversion (breaks on None)  
flag_value = not cli_flag  # Fails when cli_flag is None
```

## Security Hardening

### Header Redaction for Sensitive Data
```python
# Redact sensitive headers in validation responses
safe_headers = {
    k: ("<redacted>" if k.lower() in {"authorization", "set-cookie"} else v)
    for k, v in raw_headers.items()
}
```

### Exception Handling Specificity
```python
# Use specific exception types instead of broad Exception handling
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
except requests.exceptions.RequestException as e:  # Specific exception for requests
    logging.error("Request failed: %s", e)
# instead of: except Exception as e:
```

### Shell Script Security
```bash
# Safe secrets parsing (prevents arbitrary code execution)
if [[ -z "${GEMINI_API_KEY:-}" && -f "$HOME/.gemini_api_key_secret" ]]; then
    GEMINI_API_KEY="$(awk -F= '/^[[:space:]]*GEMINI_API_KEY[[:space:]]*=/{val=$2; gsub(/^[[:space:]]+|[[:space:]]+$/, "", val); gsub(/^"+|"+$/, "", val); print val; exit}' "$HOME/.gemini_api_key_secret")"
    export GEMINI_API_KEY
fi

# ❌ DANGEROUS - Arbitrary code execution vulnerability:
# source "$HOME/.gemini_api_key_secret"
```

## Implementation Examples

### Example 1: Safe MCP Tool Call
```python
class MCPClient:
    async def call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call MCP tool using standard JSON-RPC protocol."""
        # Use standard protocol helpers
        params = {"name": tool_name}
        if arguments:
            params["arguments"] = arguments
        
        request_data = self._make_jsonrpc_request("tools/call", params)
        response = self.session.post(f"{self.base_url}/mcp", json=request_data)
        
        # Handle response using protocol helpers
        if not (200 <= response.status_code < 300):
            raise MCPClientError(f"HTTP error {response.status_code}")
        return self._handle_jsonrpc_response(response.json())
```

### Example 2: Safe Async-to-Sync Bridge
```python
def call_tool_sync(self, tool_name: str, arguments: dict = None) -> dict:
    """Synchronous wrapper with safe event loop handling."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No event loop running, safe to use asyncio.run
        return asyncio.run(self.call_tool(tool_name, arguments))
    else:
        # Use ThreadPoolExecutor with fresh event loop
        def sync_wrapper():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.call_tool(tool_name, arguments))
            finally:
                new_loop.close()
                
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(sync_wrapper)
            return future.result()
```

## Success Metrics

**Protocol Compliance:**
- 100% of MCP communication uses JSON-RPC 2.0 standard
- Zero custom payload formats in production code
- All MCP responses properly handle protocol errors

**Async Safety:**  
- Zero RuntimeError exceptions from async operations
- All async-to-sync bridges use safe execution patterns
- ThreadPoolExecutor pattern consistently applied

**Boolean Logic Reliability:**
- All CLI flags explicitly handle None/default cases  
- Flag behavior documented and predictable
- Zero unexpected boolean inversion issues

---

**Document Owner**: MCP Platform Team  
**Last Updated**: 2025-08-26
**Next Review**: 2025-11-26
