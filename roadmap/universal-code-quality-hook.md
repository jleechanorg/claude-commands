# Universal Code Quality Hook Implementation Roadmap

## Executive Summary

Implementation of a comprehensive **PostToolUse** hook system that automatically enforces code quality standards across multiple programming languages whenever files are modified through Claude Code's Edit, MultiEdit, or Write operations. This system provides intelligent auto-fixing with graceful degradation and comprehensive warning systems.

## System Architecture

### Core Components

#### 1. Post-Tool-Use Hook Trigger
- **Hook Name**: `post_code_quality.py`
- **Event**: PostToolUse with file modification matchers
- **Triggers**: Edit, MultiEdit, Write operations on supported file types
- **Location**: `.claude/hooks/post_code_quality.py`

#### 2. Multi-Language Support Matrix

| Language | Formatter | Linter | Type Checker | Auto-Fix |
|----------|-----------|--------|--------------|----------|
| Python | black | ruff | mypy | ✅ |
| JavaScript | prettier | eslint | - | ✅ |
| TypeScript | prettier | eslint | tsc --noEmit | ✅ |
| HTML | prettier | - | - | ✅ |
| CSS | prettier | - | - | ✅ |
| JSON | prettier | - | - | ✅ |

#### 3. Smart Project Detection
- **Monorepo-Safe**: Detects true project boundaries vs parent directories
- **Technology Stack Detection**: Auto-discovers available tooling
- **Configuration File Discovery**: Respects existing project configs
- **Fallback Behavior**: Graceful operation without full toolchain

#### 4. Auto-Fix with Warning System
- **Primary**: Attempt automatic fixes using tool's --fix flags
- **Secondary**: Report unfixable issues with context and suggestions
- **Tertiary**: Continue operation with warnings vs blocking workflow

## Implementation Phases

### Phase 1: Core Hook Infrastructure ⚙️

#### Deliverables:
1. **Hook Registration** in `.claude/settings.json`
   - PostToolUse matcher patterns for file modifications
   - Robust command execution pattern (git-based ROOT resolution)
   - Proper error handling and graceful failure

2. **Base Hook Structure** (`.claude/hooks/post_code_quality.py`)
   - Command-line argument parsing for triggered tool information
   - File change detection from tool metadata
   - Project root detection algorithm
   - Logging and output formatting

3. **Project Detection Engine**
   - Multi-level project root detection (avoid monorepo false positives)
   - Configuration file discovery (package.json, pyproject.toml, etc.)
   - Tooling availability detection (which ruff, which prettier, etc.)
   - Cache tooling discovery for performance

#### Technical Architecture:

```python
class CodeQualityHook:
    def __init__(self):
        self.project_root = self.detect_project_root()
        self.available_tools = self.discover_tooling()

    def detect_project_root(self):
        # Smart algorithm to find true project boundaries
        # Avoid monorepo false positives by looking for:
        # - package.json, pyproject.toml, Cargo.toml
        # - .git directory (but not the only indicator)
        # - node_modules, venv, target directories
        pass

    def discover_tooling(self):
        # Cache available tools to avoid repeated subprocess calls
        # Check PATH for: ruff, black, mypy, prettier, eslint, tsc
        # Respect project-local binaries in node_modules/.bin/
        pass
```

### Phase 2: Python Ecosystem Support 🐍

#### Deliverables:
1. **Ruff Integration** (`ruff check --fix`)
   - Automatic linting and fixing for common Python issues
   - Respect existing `ruff.toml` or `pyproject.toml` configuration
   - Fallback to sensible defaults if no config found

2. **Black Formatting** (`black --check` then `black`)
   - Code formatting consistency enforcement
   - Configuration discovery and respect
   - Integration with existing pre-commit hooks

3. **MyPy Type Checking** (`mypy --no-error-summary`)
   - Static type analysis with actionable warnings
   - Configuration file discovery
   - Graceful degradation if type hints not available

#### Implementation Pattern:
```python
class PythonQualityProcessor:
    def process_file(self, file_path: str) -> QualityResult:
        results = []

        # Stage 1: Ruff linting with auto-fix
        if self.tools.ruff_available:
            result = subprocess.run([
                'ruff', 'check', '--fix', '--quiet', file_path
            ], capture_output=True, text=True)
            results.append(self.parse_ruff_output(result))

        # Stage 2: Black formatting
        if self.tools.black_available:
            result = subprocess.run([
                'black', '--check', '--quiet', file_path
            ], capture_output=True)
            if result.returncode != 0:
                # Apply formatting
                subprocess.run(['black', '--quiet', file_path])
                results.append(QualityResult.formatted("Applied Black formatting"))

        # Stage 3: MyPy type checking (informational)
        if self.tools.mypy_available:
            result = subprocess.run([
                'mypy', '--no-error-summary', file_path
            ], capture_output=True, text=True)
            if result.returncode != 0:
                results.append(QualityResult.warning("Type issues", result.stdout))

        return QualityResult.combine(results)
```

### Phase 3: JavaScript/TypeScript Ecosystem Support 📄

#### Deliverables:
1. **Prettier Integration**
   - Universal formatting for JS, TS, HTML, CSS, JSON
   - Configuration discovery (.prettierrc, package.json)
   - Automatic formatting application

2. **ESLint Integration**
   - JavaScript and TypeScript linting with auto-fix
   - Respect existing ESLint configuration
   - Project-local vs global ESLint handling

3. **TypeScript Compilation Check**
   - `tsc --noEmit` for type checking
   - Project tsconfig.json discovery
   - Informational type warnings

#### Implementation Pattern:
```python
class JavaScriptQualityProcessor:
    def process_file(self, file_path: str) -> QualityResult:
        results = []

        # Stage 1: Prettier formatting
        if self.tools.prettier_available:
            result = subprocess.run([
                'npx', 'prettier', '--write', file_path
            ], capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                results.append(QualityResult.formatted("Applied Prettier formatting"))

        # Stage 2: ESLint with auto-fix
        if self.tools.eslint_available and file_path.endswith(('.js', '.ts', '.jsx', '.tsx')):
            result = subprocess.run([
                'npx', 'eslint', '--fix', '--quiet', file_path
            ], capture_output=True, text=True, cwd=self.project_root)
            results.append(self.parse_eslint_output(result))

        # Stage 3: TypeScript checking (if applicable)
        if file_path.endswith(('.ts', '.tsx')) and self.tools.tsc_available:
            result = subprocess.run([
                'npx', 'tsc', '--noEmit'
            ], capture_output=True, text=True, cwd=self.project_root)
            if result.returncode != 0:
                results.append(QualityResult.warning("Type issues", result.stdout))

        return QualityResult.combine(results)
```

### Phase 4: Advanced Features & Integration 🔧

#### Deliverables:
1. **Hook Registration & Settings**
   - Complete registration in `.claude/settings.json`
   - Matcher patterns for specific file operations
   - Performance optimization (avoid hook on non-code files)

2. **Comprehensive Testing Suite**
   - Test cases for all supported file types
   - Mock tooling environments for CI
   - Edge case handling (missing tools, permission issues)

3. **Performance Optimization**
   - Parallel tool execution where safe
   - Caching of project configuration discovery
   - Skip processing for files outside project boundaries

4. **Documentation & Usage Guide**
   - Developer onboarding guide
   - Configuration examples
   - Troubleshooting common issues

## Hook Registration Details

### Settings.json Configuration:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit(*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/post_code_quality.py\" ] && python3 \"$ROOT/.claude/hooks/post_code_quality.py\" \"$CLAUDE_TOOL\" \"$CLAUDE_TOOL_ARGS\"; fi; exit 0'",
            "description": "Automatic code quality enforcement after file edits"
          }
        ]
      },
      {
        "matcher": "MultiEdit(*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/post_code_quality.py\" ] && python3 \"$ROOT/.claude/hooks/post_code_quality.py\" \"$CLAUDE_TOOL\" \"$CLAUDE_TOOL_ARGS\"; fi; exit 0'",
            "description": "Automatic code quality enforcement after multi-file edits"
          }
        ]
      },
      {
        "matcher": "Write(*)",
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then ROOT=$(git rev-parse --show-toplevel); [ -x \"$ROOT/.claude/hooks/post_code_quality.py\" ] && python3 \"$ROOT/.claude/hooks/post_code_quality.py\" \"$CLAUDE_TOOL\" \"$CLAUDE_TOOL_ARGS\"; fi; exit 0'",
            "description": "Automatic code quality enforcement after file creation"
          }
        ]
      }
    ]
  }
}
```

## Quality Assurance Strategy

### Testing Matrix:
- ✅ **Python Files**: .py files with ruff, black, mypy
- ✅ **JavaScript Files**: .js files with prettier, eslint
- ✅ **TypeScript Files**: .ts files with prettier, eslint, tsc
- ✅ **HTML Files**: .html files with prettier
- ✅ **CSS Files**: .css files with prettier
- ✅ **JSON Files**: .json files with prettier
- ✅ **Edge Cases**: Missing tools, invalid syntax, permission issues

### Success Criteria:
1. **Performance**: Hook execution <2 seconds for typical files
2. **Reliability**: 99% success rate with graceful failure handling
3. **Compatibility**: Works across different project structures
4. **User Experience**: Clear, actionable feedback for unfixable issues

## Risk Mitigation

### Potential Issues:
1. **Tool Dependencies**: Projects may not have required tools installed
   - **Mitigation**: Graceful degradation with informational messages

2. **Performance Impact**: Hook adds latency to file operations
   - **Mitigation**: Parallel execution, caching, skip non-code files

3. **Configuration Conflicts**: Project configs may conflict with defaults
   - **Mitigation**: Always respect existing project configuration

4. **Monorepo Complexity**: False positive project root detection
   - **Mitigation**: Smart multi-level detection algorithm

### Rollback Plan:
- Hook can be disabled by removing from `.claude/settings.json`
- Individual language support can be disabled via configuration flags
- Fallback to warnings-only mode if auto-fix causes issues

## Timeline

- **Phase 1**: 2-3 hours (Core infrastructure, project detection)
- **Phase 2**: 2-3 hours (Python ecosystem integration)
- **Phase 3**: 2-3 hours (JavaScript/TypeScript ecosystem)
- **Phase 4**: 1-2 hours (Testing, documentation, optimization)

**Total Estimated Effort**: 8-10 hours

## Success Metrics

1. **Coverage**: 100% of target file types supported (.py, .js, .ts, .html, .css, .json)
2. **Reliability**: Hook successfully processes files without errors
3. **Performance**: <2 second average execution time per file
4. **User Adoption**: Seamless integration requiring no workflow changes
5. **Quality Improvement**: Measurable reduction in linting/formatting issues in commits

## Future Enhancement Opportunities

1. **Additional Languages**: Go, Rust, Java, C++ support
2. **Custom Rules**: Project-specific quality rule definitions
3. **Performance Metrics**: Collect and report quality improvement statistics
4. **Integration**: Slack/Discord notifications for quality improvements
5. **Learning**: ML-based suggestions for project-specific quality improvements

---

**Document Status**: Draft v1.0
**Last Updated**: 2025-01-27
**Next Review**: After Phase 1 implementation
**Owner**: Claude Code Development Team
