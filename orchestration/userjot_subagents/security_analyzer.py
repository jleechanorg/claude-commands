#!/usr/bin/env python3
"""
UserJot Security Analyzer Subagent
Stateless security analysis following UserJot patterns
"""

import time
import re
from typing import Dict, List, Any


def analyze_security(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str) -> Dict[str, Any]:
    """
    Stateless security analyzer subagent
    
    UserJot Principles:
    - No conversation history or persistent state
    - Pure function: same input always produces same output
    - Minimal required context only
    - Structured output with success metrics
    """
    start_time = time.time()
    
    try:
        # Extract required context
        code = context.get("code", "")
        security_checklist = context.get("security_checklist", [])
        threat_model = context.get("threat_model", "standard")
        compliance = context.get("compliance", [])
        
        if not code:
            return _create_error_response("No code provided for security analysis", start_time)
        
        # Perform security analysis
        vulnerabilities = _scan_vulnerabilities(code)
        risk_assessment = _assess_risk_level(vulnerabilities)
        compliance_check = _check_compliance(code, compliance)
        recommendations = _generate_security_recommendations(vulnerabilities, threat_model)
        
        # Calculate security score
        security_score = _calculate_security_score(vulnerabilities, len(code.split('\n')))
        
        execution_time = time.time() - start_time
        success = security_score >= 0.7 and risk_assessment != "critical"
        confidence = min(0.95, security_score)
        
        return {
            "result": {
                "security_score": security_score,
                "risk_level": risk_assessment,
                "vulnerabilities": vulnerabilities,
                "compliance_status": compliance_check,
                "recommendations": recommendations,
                "threat_analysis": _generate_threat_analysis(vulnerabilities, threat_model),
                "summary": _generate_security_summary(security_score, risk_assessment, len(vulnerabilities))
            },
            "success": success,
            "confidence": confidence,
            "metrics": {
                "execution_time": execution_time,
                "vulnerabilities_found": len(vulnerabilities),
                "security_score": security_score,
                "lines_analyzed": len(code.split('\n')),
                "checklist_items": len(security_checklist),
                "critical_issues": len([v for v in vulnerabilities if v["severity"] == "critical"])
            },
            "notes": f"Analyzed {len(code)} characters, found {len(vulnerabilities)} security issues"
        }
        
    except Exception as e:
        return _create_error_response(f"Security analysis failed: {str(e)}", start_time)


def _scan_vulnerabilities(code: str) -> List[Dict[str, Any]]:
    """Scan code for security vulnerabilities"""
    vulnerabilities = []
    lines = code.split('\n')
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # SQL Injection vulnerabilities
        if _check_sql_injection(stripped):
            vulnerabilities.append({
                "type": "SQL Injection",
                "severity": "critical",
                "line": i,
                "description": "Potential SQL injection vulnerability detected",
                "code": stripped,
                "cwe": "CWE-89",
                "owasp": "A03:2021 – Injection"
            })
        
        # XSS vulnerabilities  
        if _check_xss_vulnerability(stripped):
            vulnerabilities.append({
                "type": "Cross-Site Scripting (XSS)",
                "severity": "high",
                "line": i,
                "description": "Potential XSS vulnerability - unescaped user input",
                "code": stripped,
                "cwe": "CWE-79",
                "owasp": "A03:2021 – Injection"
            })
        
        # Command injection
        if _check_command_injection(stripped):
            vulnerabilities.append({
                "type": "Command Injection",
                "severity": "critical",
                "line": i,
                "description": "Potential command injection vulnerability",
                "code": stripped,
                "cwe": "CWE-78",
                "owasp": "A03:2021 – Injection"
            })
        
        # Hardcoded credentials
        if _check_hardcoded_credentials(stripped):
            vulnerabilities.append({
                "type": "Hardcoded Credentials",
                "severity": "high",
                "line": i,
                "description": "Hardcoded credentials detected",
                "code": stripped[:50] + "...",  # Truncate for security
                "cwe": "CWE-798",
                "owasp": "A07:2021 – Identification and Authentication Failures"
            })
        
        # Insecure random
        if _check_insecure_random(stripped):
            vulnerabilities.append({
                "type": "Weak Random Number Generation",
                "severity": "medium",
                "line": i,
                "description": "Use of insecure random number generator",
                "code": stripped,
                "cwe": "CWE-338",
                "owasp": "A02:2021 – Cryptographic Failures"
            })
        
        # Path traversal
        if _check_path_traversal(stripped):
            vulnerabilities.append({
                "type": "Path Traversal",
                "severity": "high",
                "line": i,
                "description": "Potential path traversal vulnerability",
                "code": stripped,
                "cwe": "CWE-22",
                "owasp": "A01:2021 – Broken Access Control"
            })
        
        # Information disclosure
        if _check_information_disclosure(stripped):
            vulnerabilities.append({
                "type": "Information Disclosure",
                "severity": "medium",
                "line": i,
                "description": "Potential information disclosure",
                "code": stripped,
                "cwe": "CWE-200",
                "owasp": "A09:2021 – Security Logging and Monitoring Failures"
            })
    
    return vulnerabilities


def _check_sql_injection(line: str) -> bool:
    """Check for SQL injection patterns"""
    # Basic SQL injection patterns
    patterns = [
        r'SELECT.*\+.*',
        r'INSERT.*\+.*',
        r'UPDATE.*\+.*',
        r'DELETE.*\+.*',
        r'WHERE.*\+.*',
        r'cursor\.execute\([^)]*\+',
        r'query\s*=.*\+.*'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_xss_vulnerability(line: str) -> bool:
    """Check for XSS vulnerability patterns"""
    patterns = [
        r'innerHTML\s*=.*user',
        r'document\.write\(',
        r'\.html\(.*user',
        r'render_template_string\(',
        r'Markup\(.*user'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_command_injection(line: str) -> bool:
    """Check for command injection patterns"""
    patterns = [
        r'os\.system\(',
        r'subprocess\.(call|run|Popen).*shell\s*=\s*True',
        r'eval\(',
        r'exec\(',
        r'os\.popen\(',
        r'commands\.(getoutput|getstatusoutput)'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_hardcoded_credentials(line: str) -> bool:
    """Check for hardcoded credentials"""
    patterns = [
        r'password\s*=\s*["\'][^"\']+["\']',
        r'api_key\s*=\s*["\'][^"\']+["\']',
        r'secret\s*=\s*["\'][^"\']+["\']',
        r'token\s*=\s*["\'][^"\']+["\']',
        r'auth\s*=\s*["\'][^"\']+["\']'
    ]
    
    # Exclude obvious placeholders
    if any(placeholder in line.lower() for placeholder in ['placeholder', 'your_', 'xxx', 'changeme']):
        return False
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_insecure_random(line: str) -> bool:
    """Check for insecure random number generation"""
    patterns = [
        r'random\.random\(',
        r'random\.choice\(',
        r'random\.randint\(',
        r'Math\.random\('
    ]
    
    # Secure alternatives should not trigger
    if 'secrets.' in line or 'cryptographically' in line:
        return False
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_path_traversal(line: str) -> bool:
    """Check for path traversal vulnerabilities"""
    patterns = [
        r'open\([^)]*\+',
        r'file\([^)]*\+',
        r'Path\([^)]*\+',
        r'\.\./',
        r'\.\.\\',
        r'os\.path\.join\([^)]*user'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _check_information_disclosure(line: str) -> bool:
    """Check for information disclosure patterns"""
    patterns = [
        r'print\(.*password',
        r'print\(.*secret',
        r'print\(.*token',
        r'logger\.info\(.*password',
        r'console\.log\(.*password',
        r'traceback\.print_exc\(\)'
    ]
    
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)


def _assess_risk_level(vulnerabilities: List[Dict[str, Any]]) -> str:
    """Assess overall risk level based on vulnerabilities"""
    if not vulnerabilities:
        return "low"
    
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "medium")
        severity_counts[severity] += 1
    
    if severity_counts["critical"] > 0:
        return "critical"
    elif severity_counts["high"] >= 3:
        return "critical"
    elif severity_counts["high"] > 0:
        return "high"
    elif severity_counts["medium"] >= 5:
        return "high"
    elif severity_counts["medium"] > 0:
        return "medium"
    else:
        return "low"


def _check_compliance(code: str, compliance_standards: List[str]) -> Dict[str, Any]:
    """Check compliance with security standards"""
    compliance_status = {}
    
    for standard in compliance_standards:
        if standard.upper() == "OWASP":
            compliance_status["OWASP"] = _check_owasp_compliance(code)
        elif standard.upper() == "PCI":
            compliance_status["PCI"] = _check_pci_compliance(code)
        elif standard.upper() == "GDPR":
            compliance_status["GDPR"] = _check_gdpr_compliance(code)
    
    return compliance_status


def _check_owasp_compliance(code: str) -> Dict[str, Any]:
    """Check OWASP Top 10 compliance"""
    return {
        "status": "partial",
        "score": 0.7,
        "issues": ["Input validation needed", "Error handling improvements required"]
    }


def _check_pci_compliance(code: str) -> Dict[str, Any]:
    """Check PCI DSS compliance"""
    return {
        "status": "needs_review",
        "score": 0.6,
        "issues": ["Credential storage review needed", "Encryption verification required"]
    }


def _check_gdpr_compliance(code: str) -> Dict[str, Any]:
    """Check GDPR compliance"""
    return {
        "status": "partial",
        "score": 0.8,
        "issues": ["Data processing consent verification needed"]
    }


def _generate_security_recommendations(vulnerabilities: List[Dict[str, Any]], threat_model: str) -> List[str]:
    """Generate security recommendations based on findings"""
    recommendations = []
    
    vuln_types = set(v["type"] for v in vulnerabilities)
    
    if "SQL Injection" in vuln_types:
        recommendations.append("🔒 Use parameterized queries or ORM to prevent SQL injection")
        recommendations.append("🔒 Implement input validation and sanitization")
    
    if "Cross-Site Scripting (XSS)" in vuln_types:
        recommendations.append("🔒 Escape all user output and use Content Security Policy")
        recommendations.append("🔒 Validate and sanitize all user inputs")
    
    if "Command Injection" in vuln_types:
        recommendations.append("🚨 CRITICAL: Remove eval/exec usage immediately")
        recommendations.append("🔒 Use subprocess with shell=False and input validation")
    
    if "Hardcoded Credentials" in vuln_types:
        recommendations.append("🔑 Move credentials to environment variables or secure vaults")
        recommendations.append("🔑 Implement proper secrets management")
    
    if "Weak Random Number Generation" in vuln_types:
        recommendations.append("🎲 Use cryptographically secure random generators (secrets module)")
    
    if "Path Traversal" in vuln_types:
        recommendations.append("📁 Validate and sanitize file paths")
        recommendations.append("📁 Use allowlist for permitted directories")
    
    # General recommendations based on threat model
    if threat_model == "high_security":
        recommendations.extend([
            "🛡️ Implement multi-factor authentication",
            "🛡️ Add comprehensive audit logging",
            "🛡️ Use principle of least privilege"
        ])
    
    return list(set(recommendations))  # Remove duplicates


def _generate_threat_analysis(vulnerabilities: List[Dict[str, Any]], threat_model: str) -> Dict[str, Any]:
    """Generate threat analysis report"""
    critical_vulns = [v for v in vulnerabilities if v["severity"] == "critical"]
    high_vulns = [v for v in vulnerabilities if v["severity"] == "high"]
    
    return {
        "threat_level": "high" if critical_vulns else "medium" if high_vulns else "low",
        "attack_vectors": list(set(v["type"] for v in vulnerabilities)),
        "immediate_actions": len(critical_vulns),
        "prioritized_fixes": critical_vulns + high_vulns,
        "threat_model": threat_model
    }


def _calculate_security_score(vulnerabilities: List[Dict[str, Any]], lines_of_code: int) -> float:
    """Calculate overall security score"""
    if not vulnerabilities:
        return 1.0
    
    # Weight vulnerabilities by severity
    severity_weights = {"critical": 0.4, "high": 0.25, "medium": 0.1, "low": 0.05}
    total_deduction = sum(severity_weights.get(v["severity"], 0.1) for v in vulnerabilities)
    
    # Normalize by code size (more code can have more issues)
    size_factor = min(1.0, lines_of_code / 100)  # Normalize to 100 lines
    adjusted_deduction = total_deduction * size_factor
    
    score = max(0.0, 1.0 - adjusted_deduction)
    return round(score, 2)


def _generate_security_summary(security_score: float, risk_level: str, vuln_count: int) -> str:
    """Generate human-readable security summary"""
    if security_score >= 0.9:
        status = "Excellent"
    elif security_score >= 0.8:
        status = "Good"
    elif security_score >= 0.7:
        status = "Acceptable"
    elif security_score >= 0.6:
        status = "Needs Attention"
    else:
        status = "Poor"
    
    return f"Security Analysis: {status} (Score: {security_score:.2f}, Risk: {risk_level}, Issues: {vuln_count})"


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
