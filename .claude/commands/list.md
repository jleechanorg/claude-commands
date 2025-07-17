# List Commands Command

**Purpose**: Display all available slash commands with descriptions

**Action**: Show comprehensive list of all slash commands and their purposes

**Usage**: `/list`

## Available Slash Commands

- `/arch` - Short form of the Architecture Review command for quick access.
- `/archreview` - Conduct comprehensive architecture and design reviews using dual-perspective analysis with Gemini MCP and Claude, enhanced by ultrathink methodology.
- `/bclean` - Delete local branches without open GitHub PRs
- `/context` - Show context usage percentage, breakdown, and recommendations
- `/copilot` - Make PR mergeable by resolving ALL GitHub comments and fixing ALL failing tests
- `/coverage` - Run Python test coverage analysis and identify coverage gaps
- `/execute` - Execute tasks immediately using available tools, with optional subagent coordination
- `/execute-enhanced` - Memory-aware strategic planning and execution with pattern consultation
- `/header` - Generate mandatory branch header AND detect if previous response was missing it
- `/integrate` - Create fresh branch from main and cleanup test servers
- `/learn` - The unified learning command that captures and documents learnings with Memory MCP integration for persistent knowledge storage
- `/milestones` - Break tasks into N phases or suggest optimal milestone count
- `/optimize` - Improve code/files by removing duplicates and improving efficiency
- `/orch` - Multi-agent orchestration system for complex development tasks (short alias)
- `/orchestrate` - Multi-agent orchestration system for complex development tasks
- `/plan` - Same as `/execute` but requires user approval before implementation
- `/pr` - Complete development lifecycle from thinking through to PR review
- `/puppeteer` - Set Puppeteer MCP as the preferred browser automation tool for Claude Code CLI sessions
- `/push` - Pre-push review, validation, PR update, and test server startup
- `/pushlite` - Simple push to GitHub without test server or additional automation
- `/review` - Process ALL PR comments systematically with proper tracking and replies using enhanced analysis
- `/roadmap` - Update roadmap files
- `/scratchpad` - Update planning documentation
- `/tdd` - Test-driven development workflow
- `/test` - Run full test suite and check GitHub CI status
- `/teste` - Run end-to-end tests using mocked services (current behavior)
- `/tester` - Run end-to-end tests using actual services (Firestore + Gemini)
- `/testerc` - Run end-to-end tests using real services AND capture data for mock generation
- `/testhttp` - Run HTTP request tests with mock APIs (free)
- `/testhttpf` - Run HTTP request tests with REAL APIs (costs money!)
- `/testi` - Run integration tests
- `/testserver` - Manage test servers for branches
- `/testui` - Run REAL browser tests with mock APIs using Puppeteer MCP by default
- `/testuif` - Run REAL browser tests with REAL APIs using Puppeteer MCP by default (costs money!)
- `/think` - Engage in systematic problem-solving using sequential thinking methodology with adjustable computation levels.

**Usage**: Use `/command_name` to execute any of these commands.
Add `--help` to any command for detailed usage information.

**Implementation**: 
- Dynamically scans all .md files in the commands directory
- Extracts command names and purposes from markdown documentation
- Provides clean, sorted output of all available slash commands
- Python script available at `list.py` for dynamic generation