#!/usr/bin/env python3
"""
UserJot Code Reviewer Subagent
Stateless code review functionality following UserJot patterns
"""

import time
import re
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class CodeReviewResult:
    """Structured result from code review subagent"""
    security_score: float
    quality_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    metrics: Dict[str, Any]


def review_code(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str) -> Dict[str, Any]:
    """
    Stateless code reviewer subagent
    
    UserJot Principles:
    - No conversation history or persistent state
    - Pure function: same input always produces same output
    - Minimal required context only
    - Structured output with success metrics
    
    Args:
        objective: Clear description of review goals
        context: Code and requirements only
        constraints: Time/scope limitations
        success_criteria: How to measure review success
        
    Returns:
        Structured review result with metrics
    """
    start_time = time.time()
    
    try:
        # Extract required context
        code = context.get("code", "")
        requirements = context.get("requirements", [])
        
        if not code:
            return _create_error_response("No code provided for review", start_time)
        
        # Perform stateless code analysis
        issues = _analyze_code_issues(code)
        security_score = _calculate_security_score(code, issues)
        quality_score = _calculate_quality_score(code, issues)
        recommendations = _generate_recommendations(issues, requirements)
        
        # Calculate success metrics
        execution_time = time.time() - start_time
        success = security_score >= 0.7 and quality_score >= 0.6
        confidence = min(security_score, quality_score)
        
        return {
            "result": {
                "security_score": security_score,
                "quality_score": quality_score,
                "overall_score": (security_score + quality_score) / 2,
                "issues": issues,
                "recommendations": recommendations,
                "summary": _generate_summary(security_score, quality_score, len(issues))
            },
            "success": success,
            "confidence": confidence,
            "metrics": {
                "execution_time": execution_time,
                "code_lines": len(code.split('\n')),
                "issues_found": len(issues),
                "security_score": security_score,
                "quality_score": quality_score
            },
            "notes": f"Reviewed {len(code)} characters of code with {len(issues)} issues identified"
        }
        
    except Exception as e:
        return _create_error_response(f"Code review failed: {str(e)}", start_time)


def _analyze_code_issues(code: str) -> List[Dict[str, Any]]:
    """Analyze code for common issues (enhanced security analysis)"""
    issues = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        
        # ENHANCED SECURITY ANALYSIS
        
        # Critical vulnerabilities
        if 'eval(' in line_stripped or 'exec(' in line_stripped:
            issues.append({
                "type": "security", 
                "severity": "critical",
                "line": i,
                "description": "Code injection vulnerability - eval/exec usage",
                "code": line_stripped,
                "cve_category": "CWE-94"
            })
        
        # Command injection patterns
        if any(pattern in line_stripped for pattern in ['subprocess.call', 'os.system', 'popen', 'shell=True']):
            issues.append({
                "type": "security",
                "severity": "high",
                "line": i,
                "description": "Potential command injection vulnerability",
                "code": line_stripped,
                "cve_category": "CWE-78"
            })
        
        # Hardcoded credentials
        credential_patterns = ['password', 'secret', 'token', 'key', 'api_key', 'auth']
        if any(cred in line_stripped.lower() for cred in credential_patterns) and ('=' in line and any(quote in line for quote in ['"', "'"])):
            if not any(safe in line_stripped.lower() for safe in ['input(', 'getenv(', 'config', 'environ']):
                issues.append({
                    "type": "security",
                    "severity": "high",
                    "line": i,
                    "description": "Hardcoded credentials detected",
                    "code": line_stripped,
                    "cve_category": "CWE-798"
                })
        
        # SQL injection patterns (enhanced)
        sql_injection_patterns = [
            r'SELECT.*\+.*', r'INSERT.*\+.*', r'UPDATE.*\+.*', r'DELETE.*\+.*',
            r'WHERE.*\+.*', r'\.format\(.*\).*SELECT', r'%.*SELECT', r'f".*SELECT'
        ]
        for pattern in sql_injection_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                issues.append({
                    "type": "security",
                    "severity": "high", 
                    "line": i,
                    "description": "SQL injection vulnerability - unsafe query construction",
                    "code": line_stripped,
                    "cve_category": "CWE-89"
                })
                break
        
        # Path traversal vulnerabilities
        if any(pattern in line_stripped for pattern in ['../', '..\\', 'os.path.join']) and 'open(' in line_stripped:
            issues.append({
                "type": "security",
                "severity": "medium",
                "line": i,
                "description": "Potential path traversal vulnerability",
                "code": line_stripped,
                "cve_category": "CWE-22"
            })
        
        # Insecure random generation
        if 'random.' in line_stripped and any(crypto_use in line_stripped.lower() for crypto_use in ['password', 'token', 'secret', 'key']):
            issues.append({
                "type": "security",
                "severity": "medium",
                "line": i,
                "description": "Insecure random generation for cryptographic use",
                "code": line_stripped,
                "cve_category": "CWE-338"
            })
        
        # OWASP Top 10 patterns
        # A03 - Injection
        if re.search(r'\.format\(.*input.*\)|%.*input.*|f".*input', line_stripped):
            issues.append({
                "type": "security",
                "severity": "medium",
                "line": i,
                "description": "Potential injection via user input formatting",
                "code": line_stripped,
                "cve_category": "CWE-79"
            })
        
        # Quality issues
        if len(line_stripped) > 120:
            issues.append({
                "type": "quality",
                "severity": "low",
                "line": i,
                "description": "Line too long (>120 characters)",
                "code": line_stripped[:50] + "..."
            })
        
        if line_stripped.startswith('print(') and 'debug' not in line_stripped.lower():
            issues.append({
                "type": "quality",
                "severity": "medium",
                "line": i,
                "description": "Print statement should use logging",
                "code": line_stripped
            })
        
        # Input validation
        if 'input(' in line_stripped and 'validate' not in code.lower():
            issues.append({
                "type": "security",
                "severity": "medium",
                "line": i,
                "description": "User input without validation",
                "code": line_stripped
            })
    
    return issues


def _calculate_security_score(code: str, issues: List[Dict[str, Any]]) -> float:
    """Calculate security score based on issues found"""
    security_issues = [i for i in issues if i["type"] == "security"]
    
    if not security_issues:
        return 1.0
    
    # Weight issues by severity
    severity_weights = {"critical": 0.5, "high": 0.3, "medium": 0.15, "low": 0.05}
    total_deduction = sum(severity_weights.get(issue["severity"], 0.1) for issue in security_issues)
    
    # Score starts at 1.0, deduct for issues
    score = max(0.0, 1.0 - total_deduction)
    return round(score, 2)


def _calculate_quality_score(code: str, issues: List[Dict[str, Any]]) -> float:
    """Calculate code quality score"""
    quality_issues = [i for i in issues if i["type"] == "quality"]
    
    if not quality_issues:
        return 1.0
    
    # Basic quality metrics
    lines = code.split('\n')
    non_empty_lines = [l for l in lines if l.strip()]
    
    if not non_empty_lines:
        return 0.0
    
    # Deduct for quality issues
    issue_deduction = len(quality_issues) * 0.1
    
    # Simple complexity check
    complexity_indicators = code.count('if ') + code.count('for ') + code.count('while ') + code.count('try:')
    complexity_ratio = complexity_indicators / len(non_empty_lines) if non_empty_lines else 0
    complexity_deduction = max(0, (complexity_ratio - 0.3) * 0.5)
    
    score = max(0.0, 1.0 - issue_deduction - complexity_deduction)
    return round(score, 2)


def _generate_recommendations(issues: List[Dict[str, Any]], requirements: List[str]) -> List[str]:
    """Generate actionable recommendations based on issues"""
    recommendations = []
    
    # Security recommendations
    security_issues = [i for i in issues if i["type"] == "security"]
    if security_issues:
        recommendations.append("🔒 Implement input validation for all user inputs")
        recommendations.append("🔒 Use parameterized queries to prevent SQL injection")
        recommendations.append("🔒 Store passwords using proper hashing (bcrypt, scrypt)")
        
        if any(i["severity"] == "critical" for i in security_issues):
            recommendations.append("🚨 CRITICAL: Remove eval/exec usage - major security risk")
    
    # Quality recommendations  
    quality_issues = [i for i in issues if i["type"] == "quality"]
    if quality_issues:
        recommendations.append("📏 Follow line length limits (120 characters)")
        recommendations.append("📝 Replace print statements with proper logging")
        recommendations.append("🧹 Consider refactoring complex functions")
    
    # Requirement-based recommendations
    for req in requirements:
        if "secure" in req.lower():
            recommendations.append("🛡️ Add security testing and penetration testing")
        if "test" in req.lower():
            recommendations.append("🧪 Implement comprehensive unit test coverage")
    
    return list(set(recommendations))  # Remove duplicates


def _generate_summary(security_score: float, quality_score: float, issue_count: int) -> str:
    """Generate human-readable summary"""
    overall_score = (security_score + quality_score) / 2
    
    if overall_score >= 0.9:
        grade = "Excellent"
    elif overall_score >= 0.8:
        grade = "Good"
    elif overall_score >= 0.7:
        grade = "Acceptable"
    elif overall_score >= 0.6:
        grade = "Needs Improvement"
    else:
        grade = "Poor"
    
    return f"Code Review: {grade} (Security: {security_score:.1f}, Quality: {quality_score:.1f}) - {issue_count} issues found"


def _create_error_response(error_message: str, start_time: float) -> Dict[str, Any]:
    """Create standardized error response"""
    return {
        "result": None,
        "success": False,
        "confidence": 0.0,
        "metrics": {
            "execution_time": time.time() - start_time,
            "error": True
        },
        "notes": error_message,
        "error": error_message
    }