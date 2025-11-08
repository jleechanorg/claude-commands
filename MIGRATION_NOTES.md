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

### Command Syntax Standardization

**Date**: 2025-11-08  
**Affected Component**: `scripts/mcp_common.sh`

#### What Changed
The MCP server installation commands now use a standardized syntax with the `--` separator:
```bash
${MCP_CLI_BIN} mcp add [scope-args] [cli-args] <server-name> [env-flags] -- <command> [cmd-args]
```

#### CLI Compatibility
The script is designed to work with both:
- **Claude CLI** (`claude` command)
- **Codex CLI** (`codex` command)

The `MCP_CLI_BIN` environment variable controls which CLI is used (defaults to `claude`).

#### Command Structure
The new syntax places components in this order:
1. Base command: `${MCP_CLI_BIN} mcp add`
2. Scope arguments: `--scope local` or `--scope user`
3. Additional CLI arguments (if any)
4. Server name: e.g., `"grok"`
5. Environment flags: e.g., `--env "GROK_API_KEY=..."`
6. Separator: `--`
7. Execution command: e.g., `node` or `npx`
8. Command arguments: package path or name

#### Example Commands
```bash
# Grok server with direct node execution
claude mcp add --scope local "grok" --env "GROK_API_KEY=xxx" -- node /path/to/grok/index.js

# Standard npm package with npx
claude mcp add --scope local "server-name" -- npx @package/name
```

#### Compatibility Notes
- The `--` separator is a POSIX standard for separating options from arguments
- Both Claude and Codex CLI tools support this syntax
- The script includes specific logic to handle differences between the two CLIs (lines 725-731)

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
