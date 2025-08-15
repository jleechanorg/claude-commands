# Fake Code Detection Hook - Complete Test Matrix

## 🧪 TDD Test Matrix for detect_speculation_and_fake_code.sh

### **Matrix 1: Pattern Detection Coverage (Pattern Type × Code Context × Expected Result)**

| Pattern Category | Pattern Variant | Code Context | Expected Exit Code | Expected Warning | TDD Status |
|------------------|------------------|--------------|-------------------|------------------|------------|
| **TODO Patterns** | `TODO: implement` | Function comment | 2 | ✅ | [1,1,1] RED→GREEN |
| **TODO Patterns** | `TODO fix this` | Inline comment | 2 | ✅ | [1,1,2] RED→GREEN |
| **TODO Patterns** | `@todo implement` | Docstring | 2 | ✅ | [1,1,3] RED→GREEN |
| **FIXME Patterns** | `FIXME: replace` | Function body | 2 | ✅ | [1,2,1] RED→GREEN |
| **FIXME Patterns** | `fixme - update` | Class method | 2 | ✅ | [1,2,2] RED→GREEN |
| **Placeholder Patterns** | `placeholder_function` | Function name | 2 | ✅ | [1,3,1] RED→GREEN |
| **Placeholder Patterns** | `placeholder for testing` | Comment text | 2 | ✅ | [1,3,2] RED→GREEN |
| **Simulation Patterns** | `simulate_api_call` | Function name | 2 | ✅ | [1,4,1] RED→GREEN |
| **Simulation Patterns** | `Simulate.*response` | Function body | 2 | ✅ | [1,4,2] RED→GREEN |
| **Production Disclaimers** | `in production.*would` | Comment | 2 | ✅ | [1,5,1] RED→GREEN |
| **Production Disclaimers** | `In production, this would use` | Docstring | 2 | ✅ | [1,5,2] RED→GREEN |
| **Theoretical Patterns** | `theoretical.*performance` | Comment | 2 | ✅ | [1,6,1] RED→GREEN |
| **Return Null Patterns** | `For now.*return.*None` | Function body | 2 | ✅ | [1,7,1] RED→GREEN |
| **Marker Patterns** | `would go here` | Placeholder comment | 2 | ✅ | [1,8,1] RED→GREEN |

### **Matrix 2: Clean Code Validation (Code Type × Language × Expected Result)**

| Code Type | Language/Context | Sample Code | Expected Exit Code | TDD Status |
|-----------|------------------|-------------|-------------------|------------|
| **Production Functions** | Python | `def calculate_sum(a, b): return a + b` | 0 | [2,1,1] RED→GREEN |
| **Production Functions** | JavaScript | `function processData(data) { return data.map(x => x * 2); }` | 0 | [2,1,2] RED→GREEN |
| **Production Functions** | Shell | `process_files() { for f in "$@"; do echo "$f"; done; }` | 0 | [2,1,3] RED→GREEN |
| **Proper Comments** | Documentation | `# This function calculates the fibonacci sequence` | 0 | [2,2,1] RED→GREEN |
| **Implementation Notes** | Planning | `# Algorithm: Use dynamic programming for optimization` | 0 | [2,2,2] RED→GREEN |
| **Configuration Code** | Config files | `SERVER_PORT=8080\nDATABASE_URL=postgresql://localhost/db` | 0 | [2,3,1] RED→GREEN |
| **Test Assertions** | Unit tests | `assert calculate_sum(2, 3) == 5` | 0 | [2,4,1] RED→GREEN |

### **Matrix 3: Security Features Testing (Security Feature × Input Type × Expected Behavior)**

| Security Feature | Input Type | Test Scenario | Expected Behavior | TDD Status |
|------------------|------------|---------------|-------------------|------------|
| **Path Validation** | Normal path | `/home/user/project` | Accept | [3,1,1] RED→GREEN |
| **Path Validation** | Path traversal | `/home/user/../etc/passwd` | Reject | [3,1,2] RED→GREEN |
| **Path Validation** | Relative traversal | `../../../etc/passwd` | Reject | [3,1,3] RED→GREEN |
| **Path Validation** | Null byte injection | `/home/user/project\0.txt` | Reject | [3,1,4] RED→GREEN |
| **Path Validation** | Newline injection | `/home/user/project\n/etc/passwd` | Reject | [3,1,5] RED→GREEN |
| **File Operations** | Normal creation | Valid temp file creation | Atomic write | [3,2,1] RED→GREEN |
| **File Operations** | Permission denied | Read-only directory | Graceful error | [3,2,2] RED→GREEN |
| **File Operations** | Disk full | No space available | Cleanup temp files | [3,2,3] RED→GREEN |
| **Pattern Injection** | Regex metacharacters | `.*[dangerous].*` | Safe handling | [3,3,1] RED→GREEN |
| **Command Injection** | Shell metacharacters | `; rm -rf /` | No execution | [3,3,2] RED→GREEN |

### **Matrix 4: Exclusion Filter Testing (Filter Type × Content Type × Expected Result)**

| Filter Category | Content Type | Test Input | Expected Result | TDD Status |
|-----------------|--------------|------------|-----------------|------------|
| **Claude Metadata** | Session data | `{"session_id": "abc", "tool_input": "test"}` | Ignore (exit 0) | [4,1,1] RED→GREEN |
| **Claude Metadata** | Tool response | `{"tool_response": "result", "status": "complete"}` | Ignore (exit 0) | [4,1,2] RED→GREEN |
| **Hook Definitions** | Pattern definitions | `FAKE_CODE_PATTERNS["TODO"]="description"` | Ignore (exit 0) | [4,2,1] RED→GREEN |
| **Hook Definitions** | Configuration | `.claude/settings.json hook config` | Ignore (exit 0) | [4,2,2] RED→GREEN |
| **Documentation** | Hook documentation | `This hook detects fake code patterns` | Ignore (exit 0) | [4,3,1] RED→GREEN |
| **Normal Code** | Mixed content | `Real function + metadata comment` | Process normally | [4,4,1] RED→GREEN |

### **Matrix 5: Warning File Generation (File State × Content Type × Expected Outcome)**

| File State | Content Type | Test Scenario | Expected File Creation | TDD Status |
|------------|--------------|---------------|----------------------|------------|
| **No Existing File** | Single violation | TODO pattern detected | Create warning file | [5,1,1] RED→GREEN |
| **No Existing File** | Multiple violations | TODO + FIXME patterns | Create with all violations | [5,1,2] RED→GREEN |
| **Existing Warning** | New violation | Different pattern detected | Overwrite with new warning | [5,2,1] RED→GREEN |
| **Permission Issues** | Read-only directory | Cannot write to docs/ | Graceful error handling | [5,3,1] RED→GREEN |
| **Cleanup Success** | Post-fix state | No violations detected | No warning file created | [5,4,1] RED→GREEN |

### **Matrix 6: Edge Cases and Error Conditions (Error Type × Input Condition × Expected Behavior)**

| Error Category | Input Condition | Test Scenario | Expected Behavior | TDD Status |
|----------------|-----------------|---------------|-------------------|------------|
| **No Git Repository** | Non-git directory | Run hook outside git repo | Graceful error message | [6,1,1] RED→GREEN |
| **Missing CLAUDE.md** | Invalid project root | No CLAUDE.md file found | Error with clear message | [6,1,2] RED→GREEN |
| **Empty Input** | No stdin data | Echo nothing to hook | Clean exit (code 0) | [6,2,1] RED→GREEN |
| **Binary Input** | Non-text data | Binary file contents | Skip processing safely | [6,2,2] RED→GREEN |
| **Large Input** | Massive text file | 100MB+ input data | Handle without memory issues | [6,2,3] RED→GREEN |
| **Unicode Input** | International text | UTF-8 with emojis/symbols | Process correctly | [6,3,1] RED→GREEN |
| **Mixed Patterns** | Complex scenarios | Multiple pattern types + metadata | Detect all violations | [6,4,1] RED→GREEN |

## 📊 **Complete Matrix Coverage Summary**

**Total Test Matrix Cells**: 42 systematic test cases covering:
- ✅ **Pattern Detection**: 14 different pattern types and contexts
- ✅ **Clean Code Validation**: 7 legitimate code scenarios  
- ✅ **Security Features**: 9 security attack vectors and protections
- ✅ **Exclusion Filters**: 6 content types that should be ignored
- ✅ **Warning Files**: 5 file generation and management scenarios
- ✅ **Edge Cases**: 7 error conditions and boundary cases

## 🚨 **Matrix TDD Implementation Rules**

**RULE 1**: All 42 test cases must FAIL in RED phase before implementation
**RULE 2**: Each matrix cell must have corresponding shell test function
**RULE 3**: GREEN phase implements minimal code to pass each matrix test
**RULE 4**: REFACTOR phase must maintain 100% matrix test coverage
**RULE 5**: Matrix coverage report required before completion

## 🎯 **Priority Test Implementation Order**

### **Phase 1 (Critical Core)**: 
- Pattern Detection Matrix (14 tests) - Core functionality
- Clean Code Validation (7 tests) - Prevent false positives

### **Phase 2 (Security)**:
- Security Features Matrix (9 tests) - Prevent vulnerabilities
- Exclusion Filters (6 tests) - Prevent interference

### **Phase 3 (Robustness)**:
- Warning File Generation (5 tests) - User experience
- Edge Cases (7 tests) - Error handling

**Next Step**: Implement RED phase with all 42 matrix tests failing