#!/usr/bin/env python3
"""
Real AST-based technical analysis for /arch command enhancement
Provides quantified evidence and file:line references for architectural insights
"""

import ast
import os
from typing import Dict, List, Any, Optional
import sys


def analyze_file_structure(filepath: str) -> Dict[str, Any]:
    """Real AST-based analysis of Python file"""
    if not os.path.exists(filepath):
        return {'error': f'File not found: {filepath}'}
    
    if not filepath.endswith('.py'):
        return {'error': f'Not a Python file: {filepath}', 'skipped': True}
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Skip empty files
        if not content.strip():
            return {'error': f'Empty file: {filepath}', 'skipped': True}
        
        tree = ast.parse(content, filename=filepath)
        
        return {
            'file': filepath,
            'success': True,
            'metrics': calculate_file_metrics(tree, content),
            'functions': extract_functions_with_complexity(tree),
            'imports': extract_import_dependencies(tree),
            'classes': extract_classes_with_methods(tree),
            'issues': find_architectural_issues(tree, filepath)
        }
    
    except SyntaxError as e:
        return {
            'file': filepath,
            'error': f'Syntax error at line {e.lineno}: {e.msg}',
            'syntax_error': True
        }
    except Exception as e:
        return {
            'file': filepath,
            'error': f'Analysis failed: {str(e)}',
            'failed': True
        }


def calculate_file_metrics(tree: ast.AST, content: str) -> Dict[str, int]:
    """Calculate basic file-level metrics"""
    lines = content.splitlines()
    
    return {
        'lines': len(lines),
        'non_empty_lines': len([line for line in lines if line.strip()]),
        'complexity': calculate_cyclomatic_complexity(tree),
        'function_count': len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
        'class_count': len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
        'import_count': len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
        'docstring_lines': count_docstring_lines(tree)
    }


def calculate_cyclomatic_complexity(tree: ast.AST) -> int:
    """Calculate McCabe cyclomatic complexity"""
    complexity = 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                           ast.With, ast.Assert, ast.BoolOp, ast.ListComp,
                           ast.DictComp, ast.SetComp, ast.GeneratorExp)):
            complexity += 1
        elif isinstance(node, ast.Try):
            complexity += len(node.handlers)
    return complexity


def extract_functions_with_complexity(tree: ast.AST) -> List[Dict[str, Any]]:
    """Extract functions with their complexity metrics"""
    functions = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_complexity = calculate_cyclomatic_complexity(node)
            
            functions.append({
                'name': node.name,
                'line': node.lineno,
                'complexity': func_complexity,
                'args_count': len(node.args.args),
                'decorators': [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else [],
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'has_docstring': (len(node.body) > 0 and isinstance(node.body[0], ast.Expr) 
                                and isinstance(node.body[0].value, ast.Constant) 
                                and isinstance(node.body[0].value.value, str))
            })
    
    return functions


def extract_import_dependencies(tree: ast.AST) -> List[Dict[str, Any]]:
    """Extract import dependencies and patterns"""
    imports = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname,
                    'line': node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append({
                    'type': 'from_import',
                    'module': module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'line': node.lineno,
                    'level': node.level
                })
    
    return imports


def extract_classes_with_methods(tree: ast.AST) -> List[Dict[str, Any]]:
    """Extract classes with their method information"""
    classes = []
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'line': item.lineno,
                        'complexity': calculate_cyclomatic_complexity(item),
                        'is_property': any(isinstance(d, ast.Name) and d.id == 'property' 
                                         for d in item.decorator_list),
                        'is_static': any(isinstance(d, ast.Name) and d.id == 'staticmethod'
                                       for d in item.decorator_list),
                        'is_class': any(isinstance(d, ast.Name) and d.id == 'classmethod'
                                      for d in item.decorator_list)
                    })
            
            classes.append({
                'name': node.name,
                'line': node.lineno,
                'methods': methods,
                'method_count': len(methods),
                'bases': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                'decorators': [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
            })
    
    return classes


def find_architectural_issues(tree: ast.AST, filepath: str) -> List[Dict[str, Any]]:
    """Identify potential architectural issues"""
    issues = []
    
    # Check for large functions (high complexity)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            complexity = calculate_cyclomatic_complexity(node)
            if complexity > 10:
                issues.append({
                    'type': 'high_complexity',
                    'severity': 'warning' if complexity <= 15 else 'error',
                    'location': f'{filepath}:{node.lineno}',
                    'message': f'Function "{node.name}" has high complexity ({complexity})',
                    'suggestion': 'Consider breaking down into smaller functions'
                })
    
    # Check for deeply nested structures
    max_depth = calculate_max_nesting_depth(tree)
    if max_depth > 4:
        issues.append({
            'type': 'deep_nesting',
            'severity': 'warning',
            'location': filepath,
            'message': f'Maximum nesting depth is {max_depth}',
            'suggestion': 'Consider extracting nested logic into separate functions'
        })
    
    return issues


def calculate_max_nesting_depth(node: ast.AST, current_depth: int = 0) -> int:
    """Calculate maximum nesting depth in AST"""
    max_depth = current_depth
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
            child_depth = calculate_max_nesting_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
        else:
            child_depth = calculate_max_nesting_depth(child, current_depth)
            max_depth = max(max_depth, child_depth)
    
    return max_depth


def count_docstring_lines(tree: ast.AST) -> int:
    """Count total lines of docstrings in the module"""
    docstring_lines = 0
    
    # Module docstring
    if (isinstance(tree, ast.Module) and len(tree.body) > 0 
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)):
        docstring_lines += len(tree.body[0].value.value.splitlines())
    
    # Function and class docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if (len(node.body) > 0 and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)):
                docstring_lines += len(node.body[0].value.value.splitlines())
    
    return docstring_lines


def generate_evidence_based_insights(analysis_results: List[Dict]) -> List[Dict]:
    """Convert technical analysis to actionable insights"""
    insights = []
    successful_results = [r for r in analysis_results if r.get('success', False)]
    
    if not successful_results:
        return insights
    
    # High complexity detection
    high_complexity_files = []
    high_complexity_functions = []
    
    for result in successful_results:
        file_complexity = result['metrics']['complexity']
        if file_complexity > 20:
            high_complexity_files.append((result['file'], file_complexity))
        
        for func in result['functions']:
            if func['complexity'] > 10:
                high_complexity_functions.append((result['file'], func['name'], func['line'], func['complexity']))
    
    if high_complexity_files:
        insights.append({
            'category': 'complexity',
            'severity': 'high',
            'finding': f"High file complexity detected in {len(high_complexity_files)} files",
            'evidence': [f"{file} (complexity: {complexity})" for file, complexity in high_complexity_files],
            'recommendation': "Consider refactoring complex files using Extract Method/Class patterns",
            'specific_actions': [f"Review {file} for refactoring opportunities" for file, _ in high_complexity_files]
        })
    
    if high_complexity_functions:
        insights.append({
            'category': 'function_complexity',
            'severity': 'medium',
            'finding': f"High function complexity detected in {len(high_complexity_functions)} functions",
            'evidence': [f"{file}:{line} {name}() (complexity: {complexity})" 
                        for file, name, line, complexity in high_complexity_functions],
            'recommendation': "Break down complex functions into smaller, focused units",
            'specific_actions': [f"Refactor {file}:{line} {name}()" 
                               for file, name, line, _ in high_complexity_functions[:5]]  # Limit to first 5
        })
    
    # Documentation analysis
    undocumented_functions = []
    for result in successful_results:
        for func in result['functions']:
            if not func['has_docstring'] and not func['name'].startswith('_'):
                undocumented_functions.append((result['file'], func['name'], func['line']))
    
    if len(undocumented_functions) > 5:  # Only report if significant
        insights.append({
            'category': 'documentation',
            'severity': 'low',
            'finding': f"Missing documentation in {len(undocumented_functions)} public functions",
            'evidence': [f"{file}:{line} {name}()" for file, name, line in undocumented_functions[:10]],
            'recommendation': "Add docstrings to public functions for better maintainability",
            'specific_actions': ["Add docstrings following project conventions"]
        })
    
    return insights


def analyze_project_files(file_patterns: List[str]) -> Dict[str, Any]:
    """Analyze multiple files and generate comprehensive insights"""
    analysis_results = []
    
    for pattern in file_patterns:
        if os.path.isfile(pattern):
            result = analyze_file_structure(pattern)
            analysis_results.append(result)
        elif os.path.isdir(pattern):
            # Analyze Python files in directory
            for root, dirs, files in os.walk(pattern):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        result = analyze_file_structure(filepath)
                        analysis_results.append(result)
    
    insights = generate_evidence_based_insights(analysis_results)
    
    return {
        'analysis_results': analysis_results,
        'insights': insights,
        'summary': {
            'total_files': len(analysis_results),
            'successful_analyses': len([r for r in analysis_results if r.get('success', False)]),
            'syntax_errors': len([r for r in analysis_results if r.get('syntax_error', False)]),
            'insights_generated': len(insights)
        }
    }


def format_analysis_for_arch_command(analysis_results: List[Dict], insights: List[Dict]) -> str:
    """Format analysis results for integration with /arch command"""
    output = []
    
    # Summary section
    successful = [r for r in analysis_results if r.get('success', False)]
    total_files = len(analysis_results)
    total_lines = sum(r['metrics']['lines'] for r in successful)
    total_functions = sum(r['metrics']['function_count'] for r in successful)
    
    output.append("## 📊 Technical Analysis (AST-based)")
    output.append(f"**Files Analyzed**: {total_files} | **Lines**: {total_lines:,} | **Functions**: {total_functions}")
    output.append("")
    
    if insights:
        output.append("### 🔍 Key Findings")
        for insight in insights:
            severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "💡"}.get(insight['severity'], "📋")
            output.append(f"{severity_emoji} **{insight['finding']}**")
            output.append(f"   - *Category*: {insight['category']}")
            output.append(f"   - *Recommendation*: {insight['recommendation']}")
            
            if insight['evidence'][:2]:  # Show first 2 evidence items
                output.append("   - *Evidence*:")
                for evidence in insight['evidence'][:2]:
                    output.append(f"     - `{evidence}`")
                if len(insight['evidence']) > 2:
                    output.append(f"     - ... and {len(insight['evidence']) - 2} more")
            output.append("")
    
    # File-level metrics for high-complexity files
    high_complexity_files = [(r['file'], r['metrics']) for r in successful 
                            if r['metrics']['complexity'] > 15]
    
    if high_complexity_files:
        output.append("### 📈 Complexity Metrics")
        for filepath, metrics in high_complexity_files[:5]:  # Top 5
            filename = os.path.basename(filepath)
            output.append(f"**{filename}**: {metrics['complexity']} complexity, "
                         f"{metrics['function_count']} functions, {metrics['lines']} lines")
        if len(high_complexity_files) > 5:
            output.append(f"*... and {len(high_complexity_files) - 5} more files with high complexity*")
        output.append("")
    
    return "\n".join(output)


def get_contextual_files_for_analysis() -> List[str]:
    """Get contextual files for /arch command analysis"""
    files_to_analyze = []
    
    # Always include main application files
    main_files = ['mvp_site/main.py', 'mvp_site/firestore_service.py']
    for file_path in main_files:
        if os.path.exists(file_path):
            files_to_analyze.append(file_path)
    
    # Add recent changes (if available via git)
    try:
        import subprocess
        # Get files modified in current branch vs main
        result = subprocess.run(['git', 'diff', '--name-only', 'main...HEAD'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            changed_files = [f for f in result.stdout.strip().split('\n') 
                           if f.endswith('.py') and os.path.exists(f)]
            files_to_analyze.extend(changed_files[:10])  # Limit to 10 files
    except:
        pass  # Git not available or other issue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_files = []
    for f in files_to_analyze:
        if f not in seen:
            seen.add(f)
            unique_files.append(f)
    
    return unique_files


def run_arch_integration_analysis() -> str:
    """Run AST analysis for /arch command integration"""
    files_to_analyze = get_contextual_files_for_analysis()
    
    if not files_to_analyze:
        return "## 📊 Technical Analysis\n*No Python files found for analysis*\n"
    
    result = analyze_project_files(files_to_analyze)
    return format_analysis_for_arch_command(result['analysis_results'], result['insights'])


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 arch.py <file_or_directory> [file2] [file3] ...")
        print("       python3 arch.py --arch-integration  # For /arch command integration")
        sys.exit(1)
    
    if sys.argv[1] == '--arch-integration':
        # Integration mode for /arch command
        print(run_arch_integration_analysis())
        sys.exit(0)
    
    # Analyze provided files/directories
    result = analyze_project_files(sys.argv[1:])
    
    print(f"=== AST Analysis Results ===")
    print(f"Files analyzed: {result['summary']['total_files']}")
    print(f"Successful: {result['summary']['successful_analyses']}")
    print(f"Syntax errors: {result['summary']['syntax_errors']}")
    print(f"Insights: {result['summary']['insights_generated']}")
    print()
    
    # Print insights
    for insight in result['insights']:
        print(f"[{insight['severity'].upper()}] {insight['finding']}")
        print(f"Category: {insight['category']}")
        print(f"Recommendation: {insight['recommendation']}")
        if insight['evidence']:
            print("Evidence:")
            for evidence in insight['evidence'][:3]:  # Show first 3
                print(f"  - {evidence}")
            if len(insight['evidence']) > 3:
                print(f"  ... and {len(insight['evidence']) - 3} more")
        print()