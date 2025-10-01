---
description: /history Command
type: llm-orchestration
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**
**Use TodoWrite to track progress through multi-phase workflows.**

## 🚨 EXECUTION WORKFLOW

### Phase 1: Permission Error Recovery Workflow

**Action Steps:**
1. **Direct Access Attempt**: Try normal file operations first
2. **Permission Error Detected**: Immediately switch to Python fallback
3. **Python File Discovery**: Use `glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))`
4. **Python File Reading**: Use Python Read tool or subprocess for JSONL parsing
5. **Never Give Up**: Always provide results using Python if direct access fails

The `/history` command is designed to be 100% reliable regardless of file permission configurations.

## 📋 REFERENCE DOCUMENTATION

# /history Command

**Usage**: `/history [search_query] [--options]`

**Purpose**: Search through Claude Code CLI conversation history stored in `~/.claude/projects` using intelligent execution optimization and multiple search strategies.

## 🚨 CRITICAL: Permission Handling Protocol

**MANDATORY**: If you encounter ANY permission issues while accessing `~/.claude/projects/`, immediately use Python to read the files:

1. **Use Python subprocess** for all file operations if permission denied
2. **Never give up** on file access - always try Python fallback
3. **Read files with Python** using the provided fallback commands below
4. **All file discovery must use Python** if direct access fails

This command is designed to be resilient to permission issues by automatically falling back to Python-based file operations.

## Command Architecture

**`/history` uses `/execute`** for intelligent workflow optimization as requested by the user.

**Composition Pattern**: This command delegates to `/execute` which provides:
- Task complexity analysis 
- Execution strategy optimization
- Parallel processing when beneficial
- Resource-efficient search coordination

## Usage Examples

```bash

# Basic keyword search

/history "git merge conflicts"

# Search with date filter  

/history "database migration" --date "2025-08-01"

# Search specific project

/history "authentication bug" --project "worldarchitect.ai"

# Search by command type

/history --type "tool_use" --keyword "pytest"

# Complex search with multiple filters

/history "performance issue" --date "2025-08" --project "worldarchitect" --limit 10

# Search by git branch

/history "feature branch" --branch "dev1754"

# Fuzzy search for typos

/history "databse migratoin" --fuzzy

# Recent conversations only

/history "latest deployment" --recent 7  # last 7 days
```

## Search Capabilities

### Text Matching Strategies

1. **Exact Match**: Default behavior for precise keyword search
2. **Case-Insensitive**: Automatic case normalization  
3. **Tokenized Search**: Finds keywords within sentences
4. **Fuzzy Search**: `--fuzzy` flag for handling typos and variations

### Filter Options

#### Time-Based Filters

- `--date "YYYY-MM-DD"` - Exact date match
- `--date "YYYY-MM"` - Month match
- `--after "YYYY-MM-DD"` - After specific date
- `--before "YYYY-MM-DD"` - Before specific date  
- `--recent N` - Last N days

#### Project/Context Filters

- `--project "name"` - Filter by project directory path
- `--cwd "/path"` - Filter by working directory
- `--branch "branch-name"` - Filter by git branch

#### Message Type Filters  

- `--type "user|assistant|summary|tool_use"` - Filter by message type (including tool executions)
- `--user-type "external"` - Filter by user type
- `--has-tools` - Convenience flag equivalent to `--type "tool_use"` or messages with tool activity
- `--has-errors` - Messages with error indicators

#### Output Control

- `--limit N` - Maximum results (default: 20)
- `--context N` - Lines of context around matches (default: 2)
- `--format "json|text|table"` - Output format (default: text)
- `--files-only` - Show only matching file names

## Implementation Details

### Performance Optimization (Based on Research)

1. **Streaming JSONL Processing**: Line-by-line parsing to avoid memory issues
2. **Pre-filtering Pipeline**: Filter by high-selectivity metadata first (date, project, session)
3. **Parallel File Processing**: Process multiple conversation files concurrently
4. **Smart File Discovery**: Efficiently locate candidate files by directory structure

### Search Algorithm

```
1. Parse search query and extract filters
2. Discover candidate files based on project/date filters
3. For each file (in parallel):
   - Stream parse JSONL line by line
   - Pre-filter by metadata (timestamp, cwd, branch)
   - Apply text search to message content
   - Collect matches with context
4. Aggregate, rank, and format results
5. Apply output limits and formatting
```

### File Format Understanding

Based on research of `~/.claude/projects` structure:

**Directory Structure**:
```
~/.claude/projects/
├── -home-jleechan-projects-worldarchitect-ai/
│   ├── uuid1.jsonl
│   ├── uuid2.jsonl
│   └── ...
└── -home-jleechan-projects-other-project/
    └── ...
```

Note on naming: project directories are sanitized absolute paths where `/` is replaced with `-` (e.g., `/home/jleechan/projects/worldarchitect.ai` → `-home-jleechan-projects-worldarchitect-ai`). On Windows, backslashes `\` are normalized similarly.

**JSONL Format** (per conversation file):
```jsonl
{"type":"summary","summary":"Conversation summary","leafUuid":"uuid"}
{"parentUuid":null,"userType":"external","cwd":"/path","sessionId":"uuid","version":"1.0.67","gitBranch":"main","type":"user","message":{"role":"user","content":"user message"},"uuid":"uuid","timestamp":"2025-08-09T..."}
{"parentUuid":"uuid","type":"assistant","message":{"role":"assistant","content":"assistant response"},"uuid":"uuid","timestamp":"2025-08-09T..."}
```

Detection rules:
- Tool usage: records with `type:"tool_use"` or `message.toolCalls`/`toolUse` present.
- Errors: `error:true` at top-level, or `message.level in {"error","fatal"}`, or `message.content` containing standardized error markers.
Document any repository-specific variations here to keep the filters accurate.

### Integration with `/execute`

The `/history` command delegates its execution to `/execute` with a comprehensive task description that includes secure file access and robust permission handling:

```
/execute Search through Claude Code CLI conversation history with robust file access:
- Query: [user_search_query]
- Filters: [parsed_filter_options] 
- Strategy: Python-first file access with permission error handling
- Primary Access: Use Python subprocess with explicit file operations
- Fallback Strategy: If permission denied or file access fails, ALWAYS use Python3 directly
- File Discovery: python3 -c "import glob, os; print('\n'.join(glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))))"
- Content Reading: Use Python Read tool or Python subprocess to read JSONL files
- Permission Recovery: On ANY permission error, immediately switch to Python-based file operations
- Error Handling: Explicit fallback instructions - "Use Python to read files if you encounter permission issues"
- Algorithm: Python file discovery → JSONL parsing → Text search → Context extraction → Results formatting
- Output: Formatted search results with conversation context
```

**CRITICAL PERMISSION HANDLING PROTOCOL:**
If Claude encounters ANY of the following issues:
1. **Permission Denied**: Use Python subprocess to read files directly
2. **File Access Errors**: Switch to Python-based file operations immediately  
3. **Directory Access Issues**: Use `python3 -c "import os; os.listdir(os.path.expanduser('~/.claude/projects'))"`
4. **JSONL Parse Errors**: Use Python json module for robust parsing

**Python Fallback Commands:**
```bash

# Directory listing

python3 -c "import os; print('\n'.join(os.listdir(os.path.expanduser('~/.claude/projects'))))"

# File discovery  

python3 -c "import glob, os; print('\n'.join(glob.glob(os.path.expanduser('~/.claude/projects/*/*.jsonl'))))"

# File content reading (single line executable)

python3 -c "import json,sys; [print(json.dumps(json.loads(l)) if l.strip() else '') for l in open(sys.argv[1])]" ~/.claude/projects/-home-user-projects-worldarchitect-ai/uuid.jsonl

# File content reading (with error handling)  

python3 -c "import json,sys; exec('for l in open(sys.argv[1]):\\n  try:\\n    print(json.dumps(json.loads(l)))\\n  except: print(f\"Parse error: {l.strip()}\", file=sys.stderr)')" ~/.claude/projects/-home-user-projects-worldarchitect-ai/uuid.jsonl
```

This allows `/execute` to:
- Analyze the search complexity (number of files, query complexity)
- Choose optimal execution strategy (parallel vs sequential)
- Handle resource management and error recovery with Python fallback
- Provide intelligent progress reporting
- **Automatically use Python for file operations if permission issues occur**

## Output Format

### Default Text Format

```
=== Conversation History Search Results ===
Query: "git merge conflicts"
Found: 3 matches in 2 conversations

📁 worldarchitect.ai | 📅 2025-08-01 | 🌿 dev1754132318
💬 "I need help resolving git merge conflicts in the authentication module..."
   Context: Discussion about merge strategy and conflict resolution tools
   File: 7859c820-1ba2-41c5-9db1-22c6814455e6.jsonl

📁 worldarchitect.ai | 📅 2025-07-28 | 🌿 main  
💬 "The git merge created conflicts in package.json..."
   Context: Package dependency conflicts during feature merge
   File: a1b2c3d4-e5f6-7890-abcd-ef1234567890.jsonl
```

### JSON Format (`--format json`)

```json
{
  "query": "git merge conflicts",
  "total_matches": 3,
  "total_files": 2,
  "results": [
    {
      "conversation_id": "7859c820-1ba2-41c5-9db1-22c6814455e6",
      "project": "worldarchitect.ai", 
      "date": "2025-08-01",
      "branch": "dev1754132318",
      "match": {
        "message": "I need help resolving git merge conflicts...",
        "context": ["Previous message...", "Matched message", "Next message..."],
        "timestamp": "2025-08-01T11:00:11.845Z"
      }
    }
  ]
}
```

### Table Format (`--format table`)

```
Query: git merge conflicts | Matches: 3 | Files: 2
┌──────────────────────┬───────────────┬──────────────┬───────────────┬──────────────────────────────────────┐
│ conversation_id      │ project       │ date         │ branch        │ message_snippet                      │
├──────────────────────┼───────────────┼──────────────┼───────────────┼──────────────────────────────────────┤
│ 7859c820-...-55e6    │ worldarchitect│ 2025-08-01   │ dev1754132318 │ I need help resolving git merge ...  │
│ a1b2c3d4-...-7890    │ worldarchitect│ 2025-07-28   │ main          │ The git merge created conflicts ...  │
└──────────────────────┴───────────────┴──────────────┴───────────────┴──────────────────────────────────────┘
```

## Error Handling

- **Missing Directory**: Graceful handling if `~/.claude/projects` doesn't exist - use Python to check with `os.path.exists()`
- **Corrupted JSONL**: Skip malformed lines with warning using Python json module
- **Permission Issues**: **AUTOMATIC PYTHON FALLBACK** - never fail due to permissions, always try Python subprocess
- **Large Result Sets**: Automatic pagination and memory management
- **No Matches**: Helpful suggestions for refining search query
- **File Access Failures**: Immediate switch to Python-based file operations with detailed error recovery

## Integration Features

### Secure File Access

The command uses secure direct access to `~/.claude/projects/` directory, avoiding symlink vulnerabilities while maintaining search functionality within the project workspace.

### Memory MCP Integration

Search patterns and frequently accessed conversations can be cached in Memory MCP for faster repeated searches.

### Command Composition  

Can be combined with other commands:
```bash
/history "database issue" | /learn    # Learn from historical database solutions
/history "deployment error" | /debug  # Debug with historical context
```

## Advanced Features

### Semantic Search (Future Enhancement)

- Leverage embeddings for conceptual similarity matching
- Find conversations about similar topics even with different keywords

### Query Intelligence

- Auto-suggest corrections for common typos
- Recommend related search terms based on conversation patterns
- Historical query analysis for better search suggestions

## Examples of Complex Searches

```bash

# Find all tool usage in August 2025

/history --type "tool_use" --date "2025-08" --format table

# Search for authentication-related conversations in specific project

/history "auth login password" --project "worldarchitect" --limit 5

# Find recent error discussions 

/history "error exception failed" --recent 14 --has-tools

# Fuzzy search with context

/history "databse migratoin problm" --fuzzy --context 5

# Find conversations about specific files

/history "main.py" --project "worldarchitect" --format json
```

This command provides comprehensive conversation history search capabilities while leveraging `/execute` for intelligent performance optimization as requested.
