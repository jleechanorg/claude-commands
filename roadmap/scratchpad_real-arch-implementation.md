# Make /arch Actually Work - Real Implementation

**Branch**: `feature/real-arch-implementation`
**Goal**: Transform `/arch` from contextual advice to evidence-based technical analysis

**Updated Understanding**:
- Current `/arch` DOES work and provides contextual analysis (reads files, git context)
- Provides specific advice based on actual codebase examination
- BUT lacks technical depth: no AST parsing, complexity metrics, or quantified evidence
- Need to enhance with technical analysis layer for measurable insights

**Context from Previous Work**:
- Built comprehensive timeout mitigation system (works)
- Created fake detection utilities (works)
- Infrastructure is solid for adding technical analysis layer

## 🚨 **ENHANCEMENT NEEDED**

**What `/arch` Does Now**: Provides contextual architectural advice:
- Reads actual files and project structure
- Examines git history and development patterns
- Gives specific recommendations based on codebase context
- BUT lacks quantified technical analysis

**What We Need to Add**: Evidence-based technical metrics:
```
- High complexity detected: calculate_complexity() function has cyclomatic complexity 15 (main.py:245)
- Tight coupling found: 8 modules directly import auth.py, consider facade pattern
- Missing error handling: 12 functions lack try/catch blocks (see lines 34, 67, 123...)
```

**Enhancement Strategy**: Add technical analysis layer while preserving existing contextual analysis

## 🎯 **IMPLEMENTATION PLAN**

### **Phase 1: Minimal Viable Technical Analysis (2-3 hours)**

**Target**: Add AST-based analysis engine to enhance existing contextual analysis

**Create arch.py Implementation**:
- Real AST parsing of Python files
- File-level metrics (lines, functions, classes, complexity)
- Evidence-based output with file:line references
- Variance validation (different files = different analysis)

### **Phase 2: Enhanced Technical Analysis (1-2 hours)**

**Target**: Add dependency mapping and pattern detection

**Core Functions Needed**:
```python
def analyze_file_structure(filepath):
    """Real AST-based analysis of Python file"""
    with open(filepath, 'r') as f:
        tree = ast.parse(f.read())

    # Extract actual code elements
    analysis = {
        'classes': extract_classes_with_methods(tree),
        'functions': extract_functions_with_complexity(tree),
        'imports': extract_import_dependencies(tree),
        'complexity': calculate_cyclomatic_complexity(tree),
        'patterns': detect_design_patterns(tree),
        'issues': find_code_issues(tree, filepath)
    }

    return analysis

def extract_import_dependencies(tree):
    """Extract import statements and dependencies"""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({'type': 'import', 'name': alias.name})
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append({'type': 'from_import', 'module': module, 'name': alias.name})
    return imports

def extract_classes_with_methods(tree):
    """Extract class definitions and their methods"""
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes.append({
                'name': node.name,
                'line': node.lineno,
                'methods': methods,
                'method_count': len(methods)
            })
    return classes

def calculate_cyclomatic_complexity(tree):
    """Calculate actual cyclomatic complexity"""
    complexity = 1  # Base complexity
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(node, ast.BoolOp):
            complexity += len(node.values) - 1
    return complexity

def find_code_issues(tree, filepath):
    """Find specific architectural issues"""
    issues = []

    # Check for functions without error handling
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            has_try_except = any(isinstance(n, ast.Try) for n in ast.walk(node))
            if not has_try_except and len(node.body) > 3:  # Non-trivial function
                issues.append({
                    'type': 'missing_error_handling',
                    'location': f"{filepath}:{node.lineno}",
                    'function': node.name,
                    'severity': 'medium'
                })

    return issues
```

### **Phase 2: Directory Structure Analysis**

**Target**: Analyze project structure and dependencies

```python
import os

def analyze_project_structure(root_dir):
    """Analyze overall project architecture"""
    structure = {
        'modules': [],
        'dependencies': {},
        'patterns': [],
        'metrics': {}
    }

    # Scan all Python files
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                file_analysis = analyze_file_structure(filepath)
                structure['modules'].append({
                    'path': filepath,
                    'analysis': file_analysis
                })

    # Build dependency graph
    structure['dependencies'] = build_dependency_graph(structure['modules'])  # TODO: Implement this helper

    # Detect architectural patterns
    structure['patterns'] = detect_architectural_patterns(structure)

    return structure

def detect_architectural_patterns(structure):
    """Detect MVC, Factory, Singleton, etc. patterns"""
    patterns = []

    # Look for MVC pattern
    has_models = any('model' in m['path'].lower() for m in structure['modules'])
    has_views = any('view' in m['path'].lower() for m in structure['modules'])
    has_controllers = any('controller' in m['path'].lower() or 'main.py' in m['path'] for m in structure['modules'])

    if has_models and has_views and has_controllers:
        patterns.append({
            'pattern': 'MVC',
            'confidence': 'high',
            'evidence': 'Found model, view, and controller components'
        })

    return patterns
```

### **Phase 3: Evidence-Based Insights**

**Target**: Generate specific, actionable recommendations

```python
def generate_architectural_insights(analysis):
    """Convert analysis into actionable insights"""
    insights = []

    # Complexity analysis
    high_complexity_functions = [
        f for f in analysis['functions']
        if f.get('complexity', 0) > 10
    ]

    if high_complexity_functions:
        insights.append({
            'category': 'complexity',
            'severity': 'high',
            'finding': f"High complexity detected in {len(high_complexity_functions)} functions",
            'evidence': [f"{f['name']} (complexity: {f['complexity']}, {f['file']}:{f['line']})"
                        for f in high_complexity_functions[:3]],
            'recommendation': "Refactor complex functions using Extract Method pattern",
            'specific_actions': [
                f"Break down {f['name']} function into smaller methods"
                for f in high_complexity_functions[:2]
            ]
        })

    # Dependency analysis
    high_coupling_modules = find_highly_coupled_modules(analysis)
    if high_coupling_modules:
        insights.append({
            'category': 'coupling',
            'severity': 'medium',
            'finding': f"High coupling detected in {len(high_coupling_modules)} modules",
            'evidence': [f"{m['name']} imported by {len(m['importers'])} modules"
                        for m in high_coupling_modules],
            'recommendation': "Consider introducing facade or mediator patterns",
            'specific_actions': [
                f"Create facade for {m['name']} to reduce direct dependencies"
                for m in high_coupling_modules[:2]
            ]
        })

    return insights
```

### **Phase 4: Integration with Existing Infrastructure**

**Target**: Use timeout mitigation and fake detection

```python
def main():
    """Enhanced /arch with real analysis and timeout protection"""
    start_time = time.time()

    # Use timeout mitigation from existing infrastructure
    from request_optimizer import optimize_file_read, check_request_size

    # Determine scope
    scope = sys.argv[1] if len(sys.argv) > 1 else "current"

    if scope == "current":
        # Analyze current branch changes
        analysis = analyze_current_branch_architecture()
    elif os.path.isfile(scope):
        # Analyze specific file with size optimization
        read_params = optimize_file_read(scope)
        analysis = analyze_single_file_architecture(scope, read_params)
    elif os.path.isdir(scope):
        # Analyze directory structure
        analysis = analyze_project_structure(scope)

    # Generate evidence-based insights
    insights = generate_architectural_insights(analysis)

    # Format and display results
    report = format_architecture_report(insights, analysis)
    print(report)

    # Performance monitoring
    duration = time.time() - start_time
    print(f"\n⏱️ Analysis completed in {duration:.1f}s")

    # Validate we're not returning fake results
    if not insights or all(i.get('evidence') == [] for i in insights):
        print("⚠️ Warning: Analysis may be incomplete or fake")
```

## 🧪 **VALIDATION STRATEGY**

### **Test Cases**:
1. **Different Files = Different Results**:
   ```bash
   python3 arch.py mvp_site/main.py    # Should find Flask patterns
   python3 arch.py tests/test_main.py  # Should find test patterns
   python3 arch.py .claude/commands/   # Should find command patterns
   ```

2. **Evidence Traceability**:
   ```bash
   # Every insight should include specific evidence
   grep -E "(line \d+|function \w+|complexity: \d+)" output.txt
   ```

3. **Actionability Check**:
   ```bash
   # Should provide specific actions, not generic advice
   grep -E "(refactor|extract|create|implement)" output.txt
   ```

## 📋 **IMPLEMENTATION CHECKLIST**

- [ ] **Create real AST parsing functions** (2 hours)
- [ ] **Build dependency analysis** (1 hour)
- [ ] **Implement evidence-based insights** (1 hour)
- [ ] **Integrate with timeout mitigation** (30 min)
- [ ] **Test variance with 3 different targets** (30 min)
- [ ] **Validate evidence traceability** (30 min)
- [ ] **Run fake detection on new code** (15 min)

**Total Estimated Time**: 5-6 hours
**Success Criteria**: Different inputs produce different, evidence-based architectural insights

## 🚀 **NEXT STEPS**

1. **Start with single file analysis** - get AST parsing working
2. **Add evidence extraction** - specific line numbers, metrics
3. **Build insight generation** - convert analysis to recommendations
4. **Test variance** - verify different files give different results
5. **Expand to directory analysis** - full project structure

**Goal**: Replace placeholder `/arch` with real architectural analysis that provides specific, evidence-based insights users can act on.

**Context Preserved**: Can continue implementation work on this focused scope without losing the broader context of making all tools real.
