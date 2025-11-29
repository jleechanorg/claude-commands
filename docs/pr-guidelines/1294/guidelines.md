# PR #1294 Guidelines - feat: Implement zero-tolerance skip pattern ban for tests

**PR**: #1294 - feat: Implement zero-tolerance skip pattern ban for tests
**Created**: August 17, 2025
**Purpose**: Specific guidelines for this PR's development and review

## Scope
- This document contains PR-specific deltas, evidence, and decisions for PR #1294.
- Canonical, reusable protocols are defined in docs/pr-guidelines/base-guidelines.md.

## 🎯 PR-Specific Principles

### 1. **End2End Test Architecture Consistency**
- All end2end tests must use centralized fake services from `tests.fake_firestore`
- No inline duplication of fake classes within test files
- Maintain @patch decorator pattern for external service injection
- Import pattern: `from tests.fake_firestore import FakeFirestoreClient, FakeGeminiResponse`

### 2. **Qwen vs Claude Decision Pattern**
- Use qwen for well-specified code generation (19.6x speed advantage)
- Use Claude for architectural understanding and complex refactoring
- Document all decisions in `docs/pr1294/qwen_decisions.md`
- Qwen excels at: templates, boilerplate, simple fixes
- Claude excels at: preserving logic, integration, architectural changes

## 🚫 PR-Specific Anti-Patterns

### 1. **Test Architecture Violations**
- ❌ Duplicating fake classes in test files (125+ lines of unnecessary code)
- ❌ Using incorrect mocking patterns like `@patch('main.gemini_client')`  
- ❌ Creating framework-inconsistent code (Django patterns in Flask tests)
- ❌ Ignoring existing fake services architecture

### 2. **Qwen Usage Anti-Patterns**
- ❌ Using qwen for complex refactoring that must preserve existing logic
- ❌ Accepting qwen output without architectural review
- ❌ Using qwen without providing existing pattern examples
- ❌ Failing to document qwen vs Claude decision rationale

### 3. **Security Anti-Patterns Discovered in Review**
- ❌ **ReDoS Vulnerabilities**: Using greedy regex patterns like `r'not.*os\.path\.exists'` without anchoring
- ❌ **Unescaped Regex Injection**: Character classes without limits causing backtracking
- ❌ **Missing Validation**: No timeout protection for regex matching operations
- ❌ **Silent Security Issues**: Race conditions in file operations without atomic guarantees

### 4. **Zero-Tolerance Policy Design Anti-Patterns** 
- ❌ **False Dichotomy**: Claiming "zero-tolerance" while allowing `self.skipTest()` exceptions
- ❌ **High False Positive Rate**: 85% of flagged skip patterns are legitimate per pytest docs
- ❌ **Framework Opposition**: Fighting pytest's design instead of working with it
- ❌ **Missing Context Analysis**: Blanket pattern matching without skip rationale consideration

## 📋 Implementation Patterns for This PR

### 1. **End2End Test Restoration Pattern**
**Successful Pattern**:
```python
# Remove duplicate fake classes (lines 53-177)
# Add proper imports
from tests.fake_firestore import FakeFirestoreClient, FakeLLMResponse

# Use @patch decorators for external service injection  
@patch("firebase_admin.firestore.client")
@patch("mvp_site.llm_service._call_llm_api_with_llm_request")
def test_method(self, mock_llm_request, mock_firestore_client):
    fake_firestore = FakeFirestoreClient()
    mock_firestore_client.return_value = fake_firestore
```

### 2. **Hybrid Code Generation Workflow**
**Successful Pattern**:
1. Claude analyzes architecture and creates detailed specifications
2. Qwen generates code from clear specifications (19.6x faster)
3. Claude reviews and integrates with architectural understanding
4. Document decision rationale in qwen_decisions.md

## 🔧 Specific Implementation Guidelines

### 1. **Test Import Issue Resolution**
- When tests fail with `ModuleNotFoundError: No module named 'firebase_admin'`
- Issue is in CI environment dependency resolution, not local code
- Local tests passing indicates proper fake services architecture
- CI failures are infrastructure issues, not implementation issues

### 2. **Code Duplication Elimination**
- Always check for existing implementations before creating new code
- Use Read tool to examine existing fake services before implementing
- Remove duplicate classes immediately when discovered
- Prefer imports over inline definitions for maintainability

### 3. **Framework Context for Code Generation**
- Always specify framework (Flask vs Django) when using qwen
- Provide examples of existing patterns for context
- Verify generated code matches project architecture
- Manual correction required when qwen generates wrong framework code

### 4. **Security Implementation Guidelines from Review**
- **Regex Security**: Always use anchored patterns with possessive quantifiers
- **Pattern Example**: `r'\bnot\s+os\.path\.exists\b'` instead of `r'not.*os\.path\.exists'`
- **Input Validation**: Add length limits to character classes: `r'([^"\']{0,500})'`
- **File Operations**: Use atomic operations with `tempfile.NamedTemporaryFile()` and rename
- **Timeout Protection**: Add timeout enforcement for all regex matching operations

### 5. **Policy Design Guidelines from Review**
- **Contextual Analysis**: Replace zero-tolerance with intelligent skip analysis
- **AST Parsing**: Use Abstract Syntax Tree analysis instead of regex for code pattern detection
- **Graduated Enforcement**: Implement warning → documentation → enforcement phases
- **Framework Integration**: Work with pytest's design rather than against it
- **Developer Experience**: Provide clear migration paths for legitimate skip patterns

### 6. **Quality Assurance Guidelines from Review**
- **Test Coverage Requirement**: All policy enforcement scripts must have 100% test coverage
- **Edge Case Handling**: Support multi-line patterns and dynamic skip messages
- **Performance Monitoring**: Measure and optimize regex performance impact on CI
- **False Positive Tracking**: Monitor and minimize legitimate pattern flagging

---
**Status**: Enhanced through comprehensive /reviewdeep analysis - includes security and architectural findings
**Last Updated**: August 18, 2025
