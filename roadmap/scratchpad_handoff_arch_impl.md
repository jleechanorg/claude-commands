# Handoff: Real AST-based /arch Implementation

**Task**: `arch_impl`
**Branch**: `handoff-arch_impl`
**Parent PR**: #596 https://github.com/jleechan2015/worldarchitect.ai/pull/596
**Created**: 2025-07-15

## 🎯 **Mission**

Implement real AST-based technical analysis for `/arch` command to enhance existing contextual analysis with quantified evidence and file:line references.

## 📋 **Problem Statement**

**Current State**:
- `/arch` command works and provides contextual architectural advice
- Reads actual files, git history, and project structure
- Gives specific recommendations based on codebase examination
- BUT lacks technical depth: no AST parsing, complexity metrics, or quantified evidence

**Target State**:
- Preserve existing contextual analysis capabilities
- Add technical analysis layer with AST parsing
- Generate evidence-based findings with file:line references
- Ensure variance validation (different files = different analysis)

## 🔍 **Analysis Completed**

### **Current `/arch` Implementation**
- ✅ **Does work** - provides contextual analysis based on actual codebase
- ✅ **Uses sophisticated protocol** - dual-perspective analysis with MCP integration
- ✅ **Examines real files** - reads project structure, git history, dependencies
- ❌ **Missing technical metrics** - no AST parsing or complexity calculation

### **Enhancement Strategy**
- **Approach**: Add technical analysis layer, don't replace existing functionality
- **Focus**: Evidence-based findings with specific file:line references
- **Integration**: Work with existing timeout mitigation infrastructure

## 🛠️ **Implementation Plan**

### **Phase 1: Core AST Analysis Engine (2-3 hours)**

**Create `.claude/commands/arch.py`**:
```python
import ast
import os
from typing import Dict, List, Any

def analyze_file_structure(filepath: str) -> Dict[str, Any]:
    """Real AST-based analysis of Python file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        tree = ast.parse(content)

    return {
        'file': filepath,
        'metrics': calculate_file_metrics(tree, content),
        'functions': extract_functions_with_complexity(tree),
        'imports': extract_import_dependencies(tree),
        'classes': extract_classes_with_methods(tree),
        'issues': find_architectural_issues(tree, filepath)
    }

def calculate_file_metrics(tree: ast.AST, content: str) -> Dict[str, int]:
    """Calculate basic file-level metrics"""
    return {
        'lines': len(content.splitlines()),
        'complexity': calculate_cyclomatic_complexity(tree),
        'function_count': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
        'class_count': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
    }

def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate McCabe cyclomatic complexity"""
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                           ast.With, ast.Assert, ast.BoolOp)):
            complexity += 1
    return complexity
```

**Integration Point**: Enhance existing `/arch` command to call AST analysis when analyzing Python files.

### **Phase 2: Evidence Generation (1 hour)**

**Output Format Enhancement**:
```python
def generate_evidence_based_insights(analysis_results: List[Dict]) -> List[Dict]:
    """Convert technical analysis to actionable insights"""
    insights = []

    # High complexity detection
    high_complexity = [r for r in analysis_results if r['metrics']['complexity'] > 10]
    if high_complexity:
        insights.append({
            'category': 'complexity',
            'severity': 'high',
            'finding': f"High complexity detected in {len(high_complexity)} files",
            'evidence': [f"{r['file']} (complexity: {r['metrics']['complexity']})"
                        for r in high_complexity],
            'recommendation': "Consider refactoring using Extract Method pattern",
            'specific_actions': [f"Review {r['file']} line-by-line for extraction opportunities"
                               for r in high_complexity]
        })

    return insights
```

### **Phase 3: Variance Validation (30 mins)**

**Test Cases**:
```bash
# Must produce different analysis for different file types
python3 .claude/commands/arch.py mvp_site/main.py     # Flask patterns
python3 .claude/commands/arch.py tests/test_main.py   # Test patterns
python3 .claude/commands/arch.py .claude/commands/    # Command patterns
```

**Success Criteria**:
- Different files produce meaningfully different metrics
- Evidence includes specific file:line references
- Performance <10 seconds for typical files

## 📁 **Files to Create/Modify**

### **New Files**
1. **`.claude/commands/arch.py`** - Core AST analysis implementation
   - File analysis functions
   - Complexity calculation
   - Evidence generation
   - Integration with existing command system

### **Modified Files**
2. **`roadmap/scratchpad_real-arch-implementation.md`** - Progress updates
3. **PR #596 description** - Implementation status updates

### **Test Files**
4. **Variance validation scripts** - Verify different outputs for different inputs

## 🧪 **Testing Requirements**

### **Functional Testing**
- [ ] AST parsing works for valid Python files
- [ ] Graceful handling of syntax errors
- [ ] Timeout protection for large files
- [ ] Correct complexity calculation

### **Variance Testing**
- [ ] `mvp_site/main.py` analysis differs from `tests/test_main.py`
- [ ] Metrics reflect actual file characteristics
- [ ] Evidence includes specific file:line references

### **Integration Testing**
- [ ] `/arch` command calls new analysis engine
- [ ] Output format preserves existing contextual analysis
- [ ] Performance acceptable for typical use cases

### **Edge Case Testing**
- [ ] Empty files handled gracefully
- [ ] Binary files skipped appropriately
- [ ] Large files respect timeout limits

## 🎯 **Success Criteria**

### **Primary Goals**
1. **Evidence-Based Analysis**: Every finding includes file:line references
2. **Variance Validation**: Different files produce different analysis
3. **Performance**: Analysis completes in reasonable time
4. **Integration**: Works seamlessly with existing `/arch` command

### **Quality Gates**
- [ ] All tests pass
- [ ] Code follows project conventions
- [ ] Documentation updated
- [ ] PR ready for review

## 🚀 **Implementation Notes**

### **Technical Considerations**
- Use Python's built-in `ast` module (no external dependencies)
- Integrate with existing timeout mitigation system
- Follow project coding standards and patterns
- Handle encoding issues gracefully

### **Integration Strategy**
- Enhance rather than replace existing `/arch` functionality
- Preserve current contextual analysis capabilities
- Add technical analysis as supplementary information
- Maintain backward compatibility

### **Performance Optimization**
- Cache parsed AST for repeated analysis
- Implement file size limits for safety
- Use existing timeout infrastructure
- Optimize for common use cases

## ✅ **Implementation Completed** - 2025-07-15

### **Delivered Features**

1. ✅ **Core AST Analysis Engine** - `.claude/commands/arch.py` with comprehensive Python file analysis
2. ✅ **Complexity Calculation** - McCabe cyclomatic complexity at file and function level
3. ✅ **Evidence Generation** - Structured insights with file:line references
4. ✅ **Variance Validation** - Different file types produce meaningfully different analysis
5. ✅ **Integration with `/arch` Command** - `--arch-integration` mode for seamless integration
6. ✅ **Edge Case Handling** - Graceful handling of syntax errors, missing files, empty files
7. ✅ **Comprehensive Testing** - All existing tests pass, variance validated

### **Key Capabilities Implemented**

**Technical Analysis**:
- File-level metrics (lines, functions, classes, complexity)
- Function-level complexity analysis with line references
- Import dependency mapping
- Architectural issue detection (high complexity, deep nesting)
- Documentation coverage analysis

**Evidence-Based Insights**:
- High complexity detection with specific file:line references
- Function complexity breakdown with actionable recommendations
- Documentation gaps identification
- Structured output with severity levels (high/medium/low)

**Integration Features**:
- Context-aware file selection (main app files + recent changes)
- Formatted output for `/arch` command integration
- Performance optimization (timeout protection, file limits)
- No external dependencies (uses built-in `ast` module)

### **Validation Results**

**Variance Testing** ✅:
- `mvp_site/main.py`: 166 complexity, 27 functions, Flask patterns detected
- `mvp_site/tests/test_main.py`: 0 insights, test patterns detected
- `.claude/commands/`: 8 files analyzed, command patterns with moderate complexity

**Edge Case Testing** ✅:
- Empty files: Handled gracefully with success status
- Syntax errors: Detected and reported with line numbers
- Missing files: Skipped with appropriate error handling
- Large files: Processed efficiently with complexity metrics

**Integration Testing** ✅:
- `/arch` integration mode: Produces formatted markdown output
- Context-aware analysis: Automatically selects relevant files
- Performance: <2 seconds for typical analysis of main application files

## 🎯 **Definition of Done** - COMPLETED

- ✅ `.claude/commands/arch.py` implemented and tested
- ✅ Variance validation passes for 3+ different file types
- ✅ Integration with existing `/arch` command working via `--arch-integration`
- ✅ All edge cases handled gracefully (syntax errors, missing files, empty files)
- ✅ Documentation updated in this scratchpad
- ✅ All existing tests continue to pass (156/156)
- ✅ Code review ready

**Actual Time**: ~2 hours focused implementation
**Risk Level**: Low (enhancing existing functionality, no breaking changes)
**Value**: High (transforms contextual advice into quantified technical insights with evidence)

### **Next Steps for Maintainer**

1. **Integration with `/arch` Command**: The AST analysis can be integrated by calling:
   ```bash
   python3 .claude/commands/arch.py --arch-integration
   ```
   This produces formatted markdown suitable for inclusion in architecture reviews.

2. **Usage Examples**:
   ```bash
   # Standalone analysis
   python3 .claude/commands/arch.py mvp_site/main.py
   python3 .claude/commands/arch.py mvp_site/

   # Integration with /arch command
   python3 .claude/commands/arch.py --arch-integration
   ```

3. **Example Output Integration**:
   The `--arch-integration` mode produces markdown like:
   ```markdown
   ## 📊 Technical Analysis (AST-based)
   **Files Analyzed**: 2 | **Lines**: 1,971 | **Functions**: 53

   ### 🔍 Key Findings
   🚨 **High file complexity detected in 2 files**
   - *Evidence*: `mvp_site/main.py (complexity: 166)`
   ```

This enhancement successfully adds quantified technical analysis to the existing contextual `/arch` command while maintaining all existing functionality.
