# Migration Notes

## API Key Changes for Grok MCP Server

### Breaking Change: XAI_API_KEY → GROK_API_KEY Priority

**Date**: 2025-11-08  
**Affected Component**: Grok MCP Server integration (`scripts/mcp_common.sh`)

#### What Changed
The priority for Grok API key environment variables has been updated:
- **Before**: `XAI_API_KEY` was checked first, with `GROK_API_KEY` as fallback
- **After**: `GROK_API_KEY` is now the primary variable, with `XAI_API_KEY` as fallback for backward compatibility

#### Why This Changed
The new `@chinchillaenterprises/mcp-grok` package uses `GROK_API_KEY` as its standard environment variable name, aligning with the package's expected configuration.

#### Migration Required
If you currently use `XAI_API_KEY` for Grok authentication:

1. **Option 1: Update to new standard (Recommended)**
   ```bash
   # Update your environment configuration
   export GROK_API_KEY="your-api-key"
   # Remove or keep XAI_API_KEY as backup
   ```

2. **Option 2: No action needed**
   - `XAI_API_KEY` still works as a fallback
   - However, if both are set, `GROK_API_KEY` takes priority

#### Configuration Examples

**Before:**
```bash
export XAI_API_KEY="your-api-key"
```

**After (Recommended):**
```bash
export GROK_API_KEY="your-api-key"
```

**Backward Compatible:**
```bash
# Both will work, GROK_API_KEY takes priority if both set
export GROK_API_KEY="your-api-key"
export XAI_API_KEY="your-api-key"  # Fallback
```

## Configuration Improvements

### Environment Variable for Backend URL

**Date**: 2025-11-08  
**Affected Components**: 
- `scripts/mcp_common.sh`
- `scripts/secondo-cli.sh`
- `.claude/skills/ai-universe-httpie.md`
- `.claude/skills/ai-universe-second-opinion-workflow.md`
- `.claude/commands/second_opinion.md`

#### What Changed
Backend URLs are now configurable via the `SECOND_OPINION_MCP_URL` environment variable instead of being hardcoded.

#### Usage
```bash
# Use default dev URL (no action needed)
# Default: https://ai-universe-backend-dev-114133832173.us-central1.run.app/mcp

# Or set custom URL
export SECOND_OPINION_MCP_URL="https://your-production-backend.example.com/mcp"
```

#### Benefits
- Easier to switch between dev/staging/production environments
- No code changes needed when backend URLs change
- Consistent configuration across all scripts and documentation

## Code Quality Improvements

### Grok Package Path Extraction

**Date**: 2025-11-08  
**Affected Component**: `scripts/mcp_common.sh`

#### What Changed
The Grok package path (`@chinchillaenterprises/mcp-grok/dist/index.js`) has been extracted to a variable (`GROK_PACKAGE_PATH`) for easier maintenance.

#### Benefits
- Single point of change if package structure changes
- Improved code maintainability
- Reduced risk of inconsistencies across multiple locations
