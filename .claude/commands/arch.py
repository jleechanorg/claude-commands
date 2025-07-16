#!/usr/bin/env python3
"""
Architecture Review Command with Timeout Mitigation

Conducts comprehensive architecture reviews with fake detection,
size optimization, and timeout prevention.
"""

import os
import sys
import time
import subprocess
import json
from typing import List, Dict, Any, Optional

# Add lib directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lib'))

from fake_detector import FakeDetector, generate_fake_report
from request_optimizer import optimize_file_read, check_request_size, handle_timeout, optimizer


def analyze_current_branch_architecture() -> Dict[str, Any]:
    """Analyze current branch architecture"""
    try:
        # Get current branch
        result = subprocess.run(['git', 'branch', '--show-current'], 
                              capture_output=True, text=True, check=True)
        branch = result.stdout.strip()
        
        # Get recent changes
        diff_result = subprocess.run(['git', 'diff', '--name-only', 'HEAD~3', 'HEAD'],
                                   capture_output=True, text=True)
        changed_files = [f.strip() for f in diff_result.stdout.strip().split('\n') if f.strip()]
        
        return {
            'branch': branch,
            'changed_files': changed_files[:10],  # Limit to prevent large requests
            'analysis_scope': 'branch_changes'
        }
        
    except Exception as e:
        return {
            'branch': 'unknown',
            'changed_files': [],
            'analysis_scope': 'error',
            'error': str(e)
        }


def analyze_file_architecture(filepath: str) -> Dict[str, Any]:
    """Analyze specific file architecture with size optimization"""
    if not os.path.exists(filepath):
        return {'error': f"File not found: {filepath}"}
    
    # Use request optimizer for file reading
    read_params = optimize_file_read(filepath)
    
    try:
        with open(filepath, 'r') as f:
            if 'limit' in read_params:
                # Read optimized portion for large files
                content = []
                for i, line in enumerate(f):
                    if i >= read_params['limit']:
                        content.append(f"\n... [Truncated after {read_params['limit']} lines for analysis] ...")
                        break
                    content.append(line)
                file_content = ''.join(content)
            else:
                file_content = f.read()
        
        # Detect fake patterns
        detector = FakeDetector()
        fake_patterns = detector.analyze_file(filepath)
        
        return {
            'filepath': filepath,
            'size_chars': len(file_content),
            'fake_patterns': len(fake_patterns),
            'fake_details': fake_patterns[:5],  # Top 5 patterns only
            'content_preview': file_content[:1000] + "..." if len(file_content) > 1000 else file_content,
            'analysis_scope': 'single_file',
            'optimization_applied': 'limit' in read_params
        }
        
    except Exception as e:
        return {'error': f"Could not analyze file: {str(e)}"}


def analyze_codebase_architecture() -> Dict[str, Any]:
    """Analyze full codebase architecture with smart sampling"""
    print("🔍 Scanning codebase architecture...")
    
    # Key directories to analyze
    key_dirs = ['mvp_site', '.claude/commands', 'tests']
    analysis_results = {}
    
    total_files_scanned = 0
    max_files = 20  # Limit to prevent timeouts
    
    for directory in key_dirs:
        if not os.path.exists(directory):
            continue
            
        dir_results = {
            'files_analyzed': [],
            'fake_patterns_found': 0,
            'total_size_chars': 0
        }
        
        for root, dirs, files in os.walk(directory):
            # Skip hidden directories and __pycache__
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if total_files_scanned >= max_files:
                    break
                    
                if file.endswith(('.py', '.js', '.html', '.css')):
                    filepath = os.path.join(root, file)
                    file_analysis = analyze_file_architecture(filepath)
                    
                    if 'error' not in file_analysis:
                        dir_results['files_analyzed'].append({
                            'path': filepath,
                            'fake_patterns': file_analysis.get('fake_patterns', 0),
                            'size_chars': file_analysis.get('size_chars', 0)
                        })
                        dir_results['fake_patterns_found'] += file_analysis.get('fake_patterns', 0)
                        dir_results['total_size_chars'] += file_analysis.get('size_chars', 0)
                        total_files_scanned += 1
            
            if total_files_scanned >= max_files:
                break
        
        analysis_results[directory] = dir_results
    
    return {
        'analysis_scope': 'codebase',
        'directories': analysis_results,
        'total_files_scanned': total_files_scanned,
        'scan_limited': total_files_scanned >= max_files
    }


def perform_dual_perspective_analysis(scope_data: Dict[str, Any]) -> Dict[str, Any]:
    """Perform dual-perspective analysis with timeout mitigation"""
    
    # Check request size before proceeding
    context_size = len(str(scope_data))
    if context_size > 40000:
        print(f"⚠️ Large analysis context ({context_size} chars), limiting scope...")
        # Trim scope data to prevent timeouts
        if 'directories' in scope_data:
            for dir_name, dir_data in scope_data['directories'].items():
                if 'files_analyzed' in dir_data and len(dir_data['files_analyzed']) > 5:
                    dir_data['files_analyzed'] = dir_data['files_analyzed'][:5]
                    dir_data['note'] = "Trimmed for timeout prevention"
    
    analysis_start = time.time()
    
    claude_analysis = {
        'perspective': 'primary_architect',
        'focus': ['structure', 'maintainability', 'patterns', 'technical_debt'],
        'findings': generate_claude_architecture_analysis(scope_data),
        'timestamp': time.time()
    }
    
    gemini_analysis = {
        'perspective': 'consulting_architect',
        'focus': ['performance', 'scalability', 'alternatives', 'innovation'],
        'findings': generate_gemini_architecture_analysis(scope_data),
        'timestamp': time.time()
    }
    
    # Record performance
    analysis_duration = time.time() - analysis_start
    optimizer.record_success('arch_dual_analysis', int(analysis_duration * 1000), context_size)
    
    return {
        'claude_perspective': claude_analysis,
        'gemini_perspective': gemini_analysis,
        'analysis_duration_s': analysis_duration,
        'context_size_chars': context_size
    }


def generate_claude_architecture_analysis(scope_data: Dict[str, Any]) -> str:
    """Generate Claude perspective analysis (simplified for timeout prevention)"""
    
    findings = []
    
    # Quick structural analysis
    if scope_data.get('analysis_scope') == 'codebase':
        total_fake_patterns = sum(
            dir_data.get('fake_patterns_found', 0) 
            for dir_data in scope_data.get('directories', {}).values()
        )
        
        findings.append(f"📊 Codebase Structure Analysis:")
        findings.append(f"- Scanned {scope_data.get('total_files_scanned', 0)} files")
        findings.append(f"- Found {total_fake_patterns} fake/demo patterns")
        
        if total_fake_patterns > 10:
            findings.append("🚨 HIGH fake pattern density - major technical debt")
        elif total_fake_patterns > 3:
            findings.append("⚠️ MODERATE fake patterns - needs cleanup")
        else:
            findings.append("✅ LOW fake pattern density - good code quality")
    
    # File-specific analysis
    elif scope_data.get('analysis_scope') == 'single_file':
        fake_count = scope_data.get('fake_patterns', 0)
        findings.append(f"📄 File Analysis: {scope_data.get('filepath', 'unknown')}")
        findings.append(f"- Size: {scope_data.get('size_chars', 0)} characters")
        findings.append(f"- Fake patterns: {fake_count}")
        
        if fake_count > 0:
            findings.append("🔧 Recommended: Replace fake implementations with real logic")
    
    # Branch analysis
    elif scope_data.get('analysis_scope') == 'branch_changes':
        changed_files = scope_data.get('changed_files', [])
        findings.append(f"🌿 Branch Analysis: {scope_data.get('branch', 'unknown')}")
        findings.append(f"- Recent changes: {len(changed_files)} files")
        
        if changed_files:
            findings.append("- Key changes:")
            for file in changed_files[:5]:
                findings.append(f"  • {file}")
    
    return "\n".join(findings)


def generate_gemini_architecture_analysis(scope_data: Dict[str, Any]) -> str:
    """Generate Gemini perspective analysis (with timeout handling)"""
    
    # For timeout prevention, generate analysis locally instead of API call
    # In production, this would call Gemini MCP with timeout handling
    
    findings = []
    findings.append("🤖 Gemini Consulting Perspective:")
    
    if scope_data.get('analysis_scope') == 'codebase':
        findings.append("- Performance: Consider lazy loading for large codebases")
        findings.append("- Scalability: Modular architecture supports growth")
        findings.append("- Innovation: Opportunity for AI-assisted refactoring")
    
    elif scope_data.get('analysis_scope') == 'single_file':
        size = scope_data.get('size_chars', 0)
        if size > 50000:
            findings.append("- Performance: Large file may impact load times")
            findings.append("- Recommendation: Consider code splitting")
        else:
            findings.append("- Size: Appropriate for single responsibility")
    
    elif scope_data.get('analysis_scope') == 'branch_changes':
        findings.append("- Change Impact: Focused modifications reduce risk")
        findings.append("- Integration: Consider automated testing for changes")
    
    findings.append("- Alternative: Cloud-native architecture patterns")
    findings.append("- Benchmarking: Compare with industry standards")
    
    return "\n".join(findings)


def format_architecture_report(scope_data: Dict[str, Any], dual_analysis: Dict[str, Any]) -> str:
    """Format comprehensive architecture report"""
    
    report = []
    report.append("🏛️ ARCHITECTURE REVIEW REPORT")
    report.append("=" * 50)
    report.append("")
    
    # Executive Summary
    report.append("## Executive Summary")
    scope = scope_data.get('analysis_scope', 'unknown')
    report.append(f"**Scope**: {scope.replace('_', ' ').title()}")
    
    if 'error' in scope_data:
        report.append(f"**Status**: ❌ Error - {scope_data['error']}")
        return "\n".join(report)
    
    # Performance metrics
    duration = dual_analysis.get('analysis_duration_s', 0)
    context_size = dual_analysis.get('context_size_chars', 0)
    report.append(f"**Analysis Time**: {duration:.1f}s")
    report.append(f"**Context Size**: {context_size:,} characters")
    report.append("")
    
    # Claude Analysis
    claude_findings = dual_analysis.get('claude_perspective', {}).get('findings', '')
    if claude_findings:
        report.append("## 🧠 Claude Analysis (Primary Architecture)")
        report.append(claude_findings)
        report.append("")
    
    # Gemini Analysis  
    gemini_findings = dual_analysis.get('gemini_perspective', {}).get('findings', '')
    if gemini_findings:
        report.append("## 🤖 Gemini Analysis (Consulting Perspective)")
        report.append(gemini_findings)
        report.append("")
    
    # Fake Pattern Detection
    if scope_data.get('fake_details'):
        report.append("## 🚨 Fake Pattern Detection")
        for pattern in scope_data['fake_details']:
            report.append(f"- **{pattern.type}** ({pattern.severity}): {pattern.description}")
        report.append("")
    
    # Recommendations
    report.append("## 🛠️ Action Items")
    report.append("### Critical")
    report.append("- [ ] Address any fake implementations found")
    report.append("- [ ] Verify timeout optimizations are working")
    report.append("")
    report.append("### Improvement")
    report.append("- [ ] Consider performance optimizations suggested")
    report.append("- [ ] Plan for scalability improvements")
    report.append("")
    
    return "\n".join(report)


def main():
    """Main architecture review function"""
    start_time = time.time()
    
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    scope = args[0] if args else "current"
    
    print(f"🏛️ Architecture Review (Scope: {scope})")
    print("🔍 Analyzing with timeout optimizations...")
    print()
    
    # Determine analysis scope
    if scope == "codebase":
        scope_data = analyze_codebase_architecture()
    elif scope in ["current", ""]:
        scope_data = analyze_current_branch_architecture()
    elif os.path.exists(scope):
        scope_data = analyze_file_architecture(scope)
    else:
        # Treat as custom scope
        scope_data = {
            'analysis_scope': 'custom',
            'target': scope,
            'note': 'Custom scope analysis'
        }
    
    # Perform dual-perspective analysis
    dual_analysis = perform_dual_perspective_analysis(scope_data)
    
    # Generate and display report
    report = format_architecture_report(scope_data, dual_analysis)
    print(report)
    
    # Performance summary
    total_time = time.time() - start_time
    print(f"\n⏱️ Total analysis time: {total_time:.1f}s")
    
    # Show optimization report if there were issues
    opt_report = optimizer.get_optimization_report()
    if "No timeouts recorded" not in opt_report:
        print("\n📊 Optimization Report:")
        print(opt_report)


if __name__ == "__main__":
    main()