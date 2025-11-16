# WorldAI MCP Server Integration

AI-powered tabletop RPG platform integration via Model Context Protocol (MCP).

## Installation

### From GitHub Repository

```bash
# Install the published package (after this PR merges)
pip install git+https://github.com/jleechanorg/worldarchitect.ai.git@main

# Install the in-flight branch for testing prior to merge
pip install git+https://github.com/jleechanorg/worldarchitect.ai.git@worktree_mcp_worldai

# Verify installation
worldarchitect-mcp --help
```

## 🛠️ Technologies

### **MCP Architecture (Model Context Protocol)**
- **MCP Server** (world_logic.py) - JSON-RPC 2.0 protocol exposing D&D game mechanics as AI tools
- **API Gateway** (main.py) - Pure HTTP ↔ MCP translation layer
- **Unified API Functions** - Consistent interface for both HTTP and MCP access
- **Performance Options** - Direct function calls or network-based MCP communication

### Backend
- **Python 3.11** with Flask framework
- **Google Gemini AI** (2.5-flash model)
- **Firebase** (Authentication & Firestore)
- **Docker** containerization
- **Google Cloud Run** deployment

### Frontend
- **Vanilla JavaScript** (ES6+)
- **Bootstrap 5.3.2** responsive UI
- **Multiple theme support** (Light, Dark, Fantasy, Cyberpunk)
- **Reorganized Assets** - Clean `frontend_v1/` structure with backward compatibility

### AI & Game Logic
- **MCP Tool Integration** - 8 specialized tools: `create_campaign`, `get_campaign_state`, `process_action`, `update_campaign`, `export_campaign`, `get_campaigns_list`, `get_user_settings`, `update_user_settings`
- **Pydantic** structured generation for improved consistency
- **MBTI personality system** for deep character interactions
- **Entity tracking** for narrative consistency
- **Dual-pass generation** for accuracy

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Firebase project with Firestore
- Google Cloud project with Gemini API access

### Installation

```bash
# Clone the repository
git clone https://github.com/jleechanorg/worldarchitect.ai.git
cd worldarchitect.ai

# Set up virtual environment (see VENV_SETUP.md for detailed instructions)
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r mvp_site/requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run locally using vpython script (includes MCP server auto-start)
./vpython mvp_site/main.py serve

# Alternative: Run MCP server separately for development
# Terminal 1: Start MCP server (package entry point)
python -m mvp_site.mcp_api --http-only --port 8000

# Terminal 2: Start API gateway
MCP_SERVER_URL=http://localhost:8000 ./vpython mvp_site/main.py serve
```

## 🤖 Claude Code Plugin Distribution

WorldArchitect.AI's `.claude/` automation suite is now packaged as an official Claude Code plugin so teams can install the same slash commands, subagents, and hooks with a single `/plugin` workflow. The repository doubles as a marketplace host via `.claude-plugin/marketplace.json`, letting you develop locally or share the plugin from any git URL.

### Install locally during development

1. Trust the repository folder in Claude Code.
2. Add the local marketplace from the project root:
   ```
   /plugin marketplace add ./
   ```
3. Install the plugin bundle:
   ```
   /plugin install worldarchitect-ai-suite@worldarchitect-suite
   ```
4. Restart Claude Code so the commands, agents, and hooks load.

### What the plugin enables

- Reuses all existing `.claude/commands/` slash commands and `.claude/agents/` subagents in one installable bundle.
- Registers the governance hooks via `hooks.plugin.json`, which automatically locate the correct scripts using `${CLAUDE_PLUGIN_ROOT}` when the plugin is enabled.
- Ships marketplace metadata so your team can host this repository or mirror it for distribution without additional packaging steps.

See `.claude-plugin/README` and `.claude/hooks/hooks.plugin.json` for component details, or run `claude --debug` to inspect plugin loading if you need to troubleshoot.

## 🔐 Credentials & Configuration

WorldArchitect.AI requires several credentials and configuration files. Here's exactly where each one should be placed:

### 🔥 Firebase Credentials

**Firebase is used for both backend database operations and frontend user authentication.**

#### Backend (Python/Flask) - Service Account Key
```bash
# Location (required):
<PROJECT_ROOT>/serviceAccountKey.json

# Purpose: Server-side Firebase Admin SDK operations
# Used by: Backend Python code, integration tests, analytics scripts
# Detection: Automatic via firebase_admin.initialize_app()
```

#### Frontend (React V2) - Client Configuration
```bash
# Location (required):
<PROJECT_ROOT>/mvp_site/frontend_v2/.env

# Setup Instructions:
1. Copy the template: cp mvp_site/frontend_v2/.env.example mvp_site/frontend_v2/.env
2. Edit .env with your actual Firebase project credentials from Firebase Console
3. The .env file is gitignored and will not be committed to version control

# Required Variables (get from Firebase Console > Project Settings):
VITE_FIREBASE_API_KEY=your-actual-firebase-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
# ... other Firebase config values
```

### 🤖 Gemini AI Credentials

**Gemini API powers the AI Game Master functionality.**

#### Option 1: Environment Variable (Recommended)
```bash
export GEMINI_API_KEY=your-gemini-api-key-here
```

#### Option 2: File-based (Legacy Support)
```bash
# Any of these locations work:
~/.gemini_api_key.txt
<PROJECT_ROOT>/gemini_api_key.txt
<PROJECT_ROOT>/local_api_key.txt
```

### 🌍 Environment Files Summary

| Component | File Location | Purpose |
|-----------|---------------|---------|
| **Backend** | `serviceAccountKey.json` (project root) | Firebase Admin SDK |
| **Frontend V2** | `mvp_site/frontend_v2/.env` | Client-side Firebase config |
| **Testing** | `testing_http/testing_full/.env` | HTTP testing configuration |
| **Gemini** | Environment variable or `~/*.txt` file | AI API access |

### 🛡️ Security Notes

- ✅ **All credential files are gitignored** - Safe to place in specified locations
- ✅ **No hardcoded credentials** - Everything uses environment variables or secure files
- ✅ **Separate privileges** - Backend has admin access, frontend has user-level access
- ⚠️ **Never commit** `.env` files or API keys to version control

### 🔧 Troubleshooting Credential Issues

#### Firebase Authentication Errors

**"Token used too early" / Clock Skew Error**
```
Error: Authentication failed: Token used too early, 1754334195 < 1754334197
```
- **Cause**: System clock is slightly ahead of Firebase servers (2+ seconds)
- **Fix**: Automatic retry with progressive delays (1.5s, 3s) - should resolve automatically
- **Manual Fix**: Sync system clock with `sudo ntpdate -s time.nist.gov` (Linux/Mac)

**"Missing Firebase environment variables"**
```
Error: Missing required Firebase environment variables: VITE_FIREBASE_API_KEY
```
- **Cause**: `.env` file missing or incorrect location
- **Fix**: Ensure `.env` file exists at `mvp_site/frontend_v2/.env` with all VITE_FIREBASE_* variables

**"Could not find Firebase key"**
```
Error: Could not find Firebase key at /path/to/serviceAccountKey.json
```
- **Cause**: Service account key not in project root
- **Fix**: Copy `serviceAccountKey.json` to `<PROJECT_ROOT>/serviceAccountKey.json`

#### Gemini API Errors

**"GEMINI_API_KEY environment variable not found"**
- **Cause**: API key not set in environment or file
- **Fix**: Set environment variable or create file at `~/.gemini_api_key.txt`

#### Quick Setup Verification
```bash
# Check if all credentials are in place:
ls -la <PROJECT_ROOT>/serviceAccountKey.json
ls -la <PROJECT_ROOT>/mvp_site/frontend_v2/.env
echo $GEMINI_API_KEY
```

### Docker Deployment

```bash
# Build the container
docker build -t worldarchitect-ai .

# Run with environment variables
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your-key \
  -e FIREBASE_PROJECT_ID=your-project \
  worldarchitect-ai
```

## 🏗️ MCP Architecture Transformation

WorldArchitect.AI has undergone a complete architectural transformation to implement the Model Context Protocol (MCP), representing the largest change in the project's history:

- **Before**: Monolithic 1885-line main.py handling everything from HTTP routing to D&D game mechanics
- **After**: Clean separation with 1,373-line MCP server (`world_logic.py`) and 1,170-line API gateway (`main.py`)
- **Benefits**: 75% code reduction in request handling, improved testability, AI tool integration ready, microservices foundation
- **Compatibility**: 100% backward compatible - all existing APIs work identically

The MCP server exposes the same 8 specialized tools listed above, enabling future AI assistant integrations while maintaining the same user experience.

## 🎮 Features

- **Campaign Management**: Create and manage multiple campaigns
- **AI Game Master**: Three specialized personas for different play styles
- **Full D&D 5e Support**: Complete rule implementation
- **Character & God Modes**: Standard play or administrative control
- **State Persistence**: Never lose your progress
- **Export Functionality**: Save your adventures in multiple formats
- **Debug Mode**: Full transparency into AI decisions

## 🧪 Testing

### **Core Testing**
```bash
# Run all tests (includes MCP integration tests)
./run_tests.sh

# Run with coverage
./run_tests.sh --coverage

# Run integration tests
./run_tests.sh --integration

# Run specific test with vpython
TESTING=true ./vpython mvp_site/test_file.py
```

### **MCP Architecture Testing**
```bash
# Run MCP-specific tests
./testing_mcp/run_mcp_tests.sh

# Test MCP server integration
./vpython testing_mcp/integration/test_end_to_end.py

# Performance benchmarks (MCP vs direct calls)
./vpython testing_mcp/performance/benchmark_mcp_vs_direct.py

# Docker-based deployment testing
cd testing_mcp && docker-compose up --build
```

### **Browser & API Testing**
```bash
# Browser tests (using real browser automation)
./run_ui_tests.sh mock

# HTTP API tests
./run_http_tests.sh mock

# Full end-to-end tests with real APIs (costs money)
./run_ui_tests.sh real
```

## 🔬 Command Composition System Validation

### Overview
We've validated a **True Universal Command Composition System** that enables natural language control of AI behavior through semantic composition. This system allows commands like `/think /analyze /arch` to reliably modify how Claude approaches problems.

### Key Findings from A/B Testing

**✅ Proven Capabilities:**
- **Behavioral Modification**: Reliably changes thinking patterns across 15+ headless Claude instances
- **Tool Integration**: Commands consistently trigger appropriate MCP tools (99% vs 20% for natural language)
- **Emergent Structure**: Complex 8-step analytical frameworks emerge naturally from command combinations
- **Cross-Context Consistency**: Patterns hold across debugging, strategic analysis, and meta-cognitive tasks

**📊 Test Results:**
- **Test Set A** (Debugging): Command composition → systematic 6-8 thought analysis; Natural language → direct problem-solving
- **Test Set B** (Strategic Analysis): Command composition → comprehensive risk-reward frameworks; Natural language → focused recommendations
- **Sample Evidence**: `tmp/ab_test_results_analysis.md` contains full behavioral pattern documentation

**🎯 Honest Positioning:**
- **Accurate Claim**: "Behavioral modification technology that reliably changes how Claude approaches problems"
- **What It Provides**: Consistent systematic analysis, tool integration, behavioral predictability
- **What Needs Validation**: Outcome quality improvements, user preference, cost-benefit analysis

### Architecture & Implementation
- **Meta-prompt Approach**: Leverages Claude's natural language processing vs rigid parsing
- **Universal Composition**: Any command combination works through semantic understanding
- **Tool Ecosystem Integration**: Reliable bridge between user intent and MCP capabilities

### Next Steps
1. **Outcome Validation**: Measure solution effectiveness, not just process sophistication
2. **User Studies**: Blind evaluation of output quality and user preferences
3. **Mechanism Research**: Test alternative explanations vs architectural uniqueness
4. **Real-world Application**: Identify specific use cases where behavioral consistency adds value

*See `roadmap/scratchpad_dev1752948734.md` for complete validation methodology and balanced critical assessment.*

---

**For deployment documentation, see:**
- [GitHub Actions Workflows](.github/workflows/README.md)
- [Production Deployment Guide](docs/GITHUB_ACTIONS_AUTO_DEPLOY.md)
