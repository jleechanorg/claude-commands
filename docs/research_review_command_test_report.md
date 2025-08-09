# Research Test Report: Default /review Command in Claude Code CLI

**Date**: 2025-08-09
**Research Query**: "what is the default /review command in Claude Code CLI"
**Branch**: research-review-command
**Agent**: task-agent-19903515

## Research Methodology

This research was conducted using the `/research` command which combines:
1. Ultra-depth sequential thinking (`/thinku`) for systematic analysis
2. Multi-engine search (`/perp`) across multiple information sources
3. Cross-validation across different AI models and sources

## Sources Consulted

### Primary Sources
1. **Official Anthropic Documentation**
   - URL: https://docs.anthropic.com/en/docs/claude-code/cli-reference
   - URL: https://docs.anthropic.com/en/docs/claude-code/slash-commands
   - Status: Successfully accessed and verified

2. **Local Project Implementation**
   - File: `.claude/commands/review.md`
   - Status: Successfully read and analyzed

3. **Secondary AI Model Consultation**
   - Perplexity AI search engine
   - Gemini Flash model consultation

## Research Findings

### 1. Built-in Command Definition

According to official Anthropic documentation (docs.anthropic.com/en/docs/claude-code/slash-commands), `/review` is listed as a **built-in slash command** with the following specification:

**Command**: `/review`
**Purpose**: Request code review

### 2. Command Type Classification

The `/review` command is classified as:
- **Built-in slash command** (not a CLI command)
- **Interactive mode command** (used within Claude Code sessions)
- **Customizable command** (can be overridden with project-specific implementations)

### 3. Default Implementation Details

Based on research findings:

**Basic Functionality**: The default `/review` command provides code review functionality, but the official documentation only provides the high-level purpose: "Request code review"

**Actual Behavior**: According to Perplexity AI research, the default behavior includes:
- AI-powered code review analysis
- Automated feedback on bugs, improvements, style guide adherence
- Can target PRs, files, or code snippets
- Provides instant feedback acting as an "AI code reviewer"

### 4. Project-Level Customization

**Finding**: This project contains a custom implementation at `.claude/commands/review.md` that significantly extends the default functionality.

**Custom Implementation Features**:
- Systematic PR comment processing with virtual [AI reviewer] agent
- Comprehensive code quality analysis with categorized issues (🔴 Critical, 🟡 Important, 🔵 Suggestion, 🟢 Nitpick)
- Automatic PR detection and analysis
- GitHub API integration for posting review comments
- File-by-file analysis with detailed reporting

### 5. Architecture Discovery

**Built-in vs Custom**: The research revealed that:
1. Claude Code CLI provides a basic built-in `/review` command
2. Projects can override this with custom implementations in `.claude/commands/review.md`
3. Custom implementations take precedence over built-in commands
4. The distinction between built-in and custom is shown in `/help` with "(project)" or "(user)" tags

### 6. Cross-Reference Validation

**Source Consistency**: Multiple sources confirmed:
- `/review` exists as a built-in slash command
- Purpose is code review functionality
- Can be customized at project level
- Works within Claude Code interactive sessions

**Source Conflicts**: One AI model (Gemini) provided information about a different command (`/commentcheck`) when asked about `/review`, indicating potential confusion between similar commands.

## Limitations and Gaps

1. **Official Documentation Limited**: The official Anthropic documentation provides only the basic purpose ("Request code review") without detailed implementation specifics.

2. **Default Behavior Details**: Specific details about the default implementation behavior were primarily found through secondary AI sources rather than official documentation.

3. **Version Specificity**: Research did not identify version-specific differences in `/review` command behavior.

## Objective Assessment

**What was definitively established**:
- `/review` is officially a built-in slash command in Claude Code CLI
- Its stated purpose is "Request code review"
- It can be customized with project-specific implementations
- It operates in interactive mode, not as a CLI command

**What required secondary source validation**:
- Specific details about default behavior and functionality
- Implementation details and feature set
- Integration with GitHub and PR workflows

**What remained unclear**:
- Exact default implementation source code or detailed behavior specification
- Version history or changes to default implementation
- Differences between built-in behavior and typical custom implementations

## Conclusion

The default `/review` command in Claude Code CLI is a built-in slash command designed to "Request code review" according to official documentation. While the core functionality exists as a built-in command, projects commonly implement custom versions with enhanced features, as evidenced by the detailed implementation found in this project's `.claude/commands/review.md` file.

---

**Note**: This report documents exactly what the research process returned without interpretation or editorial judgment, as requested in the task specification.