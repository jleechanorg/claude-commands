---
description: /4layer - Four-Layer Minimal Repro Testing Protocol
type: testing
execution_mode: immediate
---
## ⚡ EXECUTION INSTRUCTIONS FOR CLAUDE
**When this command is invoked, YOU (Claude) must execute these steps immediately:**
**This is NOT documentation - these are COMMANDS to execute right now.**

**PRIMARY REFERENCE**: See `.claude/skills/pr-blocker-min-repro.md` for complete protocol details.

## 🚨 EXECUTION WORKFLOW

### Minimal Repro Ladder

Execute tests in this order, **stopping only when blocker is conclusively reproduced**:

**1. Unit Tests** (`$PROJECT_ROOT/tests/`)
```bash
./vpython -m pytest $PROJECT_ROOT/tests/test_[relevant].py -q
```

**2. End-to-End Tests** (`$PROJECT_ROOT/tests/test_end2end/`)
```bash
./vpython -m pytest $PROJECT_ROOT/tests/test_end2end/test_[feature]_end2end.py -q
```

**3. MCP/HTTP API Tests** (real local server, `testing_mcp/`)
```bash
./vpython testing_mcp/[domain]/test_[feature]_real.py
```

**4. Browser Tests** (final escalation, `testing_ui/`)
```bash
./vpython testing_ui/[domain]/test_[feature]_browser.py
```

### Action Steps

1. **Identify blocker** - Determine which feature/component is failing
2. **Start at Layer 1** - Run unit tests first
3. **Climb ladder** - Continue to next layer until blocker is conclusively reproduced
4. **Collect evidence** - Record full absolute paths to evidence bundles
5. **Report results** - Document which layer reproduced the issue

### Evidence Requirements

After each test run:
- Print full absolute evidence path (e.g., `/tmp/your-project.com/[branch]/[test]/latest/`)
- Grep logs for failure signatures
- Verify screenshot + log consistency
- Record exact evidence directory and critical lines

### Classification

- **Unit layer failure** → Backend logic bug
- **End2end layer failure** → Integration/API issue
- **MCP layer failure** → Server/MCP protocol issue
- **Browser layer failure** → UI/frontend issue

## 📋 REFERENCE DOCUMENTATION

# /4layer - Four-Layer Minimal Repro Testing Protocol

## Purpose

Reproduce PR-blocking issues with the **fastest reliable testing ladder**: unit → end2end → MCP API → browser.

This command implements the minimal repro protocol from `.claude/skills/pr-blocker-min-repro.md`.

## Usage

```bash
/4layer [blocker_description]
```

## Testing Ladder (execute in order)

### Layer 1: Unit Tests
- **Location**: `$PROJECT_ROOT/tests/`
- **Purpose**: Test isolated modules/functions
- **Speed**: Fastest (seconds)
- **Example**: `./vpython -m pytest $PROJECT_ROOT/tests/test_settings_api.py -q`

### Layer 2: End-to-End Tests
- **Location**: `$PROJECT_ROOT/tests/test_end2end/`
- **Purpose**: Full backend flow with mocked external services
- **Speed**: Fast (seconds to minutes)
- **Example**: `./vpython -m pytest $PROJECT_ROOT/tests/test_end2end/test_faction_settings_end2end.py -q`

### Layer 3: MCP/HTTP API Tests (Real Local Server)
- **Location**: `testing_mcp/`
- **Purpose**: Real server with MCP/HTTP API calls
- **Speed**: Medium (minutes)
- **Example**: `./vpython testing_mcp/faction/test_faction_settings_real.py`

### Layer 4: Browser Tests (Real Services)
- **Location**: `testing_ui/`
- **Purpose**: Full UI automation with real browser
- **Speed**: Slowest (minutes to tens of minutes)
- **Example**: `./vpython testing_ui/test_llm_settings_browser.py`

## Key Principles

1. **Stop climbing when blocker is reproduced** - Don't waste time on higher layers
2. **Keep provider/user isolation** - Ensure test data and state are isolated per test run so parallel executions don't interfere with each other
3. **Always attach concrete evidence** - Full paths, log lines, screenshots
4. **Classify by layer** - Failure layer indicates root cause location

## Benefits

- **Efficiency**: Start with fastest tests, escalate only when needed
- **Precision**: Identify exact layer where bug manifests
- **Evidence**: Concrete paths and logs for debugging
- **Speed**: Avoid slow browser tests when unit tests suffice
