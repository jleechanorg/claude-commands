#!/usr/bin/env python3
"""
UserJot Qwen Coder Subagent
Stateless code generation using Qwen model following UserJot patterns
"""

import importlib
import importlib.util
import os
import re
import subprocess
import sys
import textwrap
import time
from typing import Any, Dict, List


def _find_claude_commands_dir() -> str | None:
    commands_dir = os.getenv("WORLDAI_CLAUDE_COMMANDS_DIR") or os.getenv(
        "CLAUDE_COMMANDS_DIR"
    )
    if commands_dir and os.path.isdir(commands_dir):
        return commands_dir

    current = os.path.abspath(os.path.dirname(__file__))
    for _ in range(8):
        candidate = os.path.join(current, ".claude", "commands")
        if os.path.isdir(candidate):
            return candidate
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

    return None


def _validate_and_sanitize_inputs(
    objective: str,
    context: Dict[str, Any],
    constraints: Dict[str, Any],
    success_criteria: str,
) -> List[str]:
    """
    Validate and sanitize all inputs to prevent security vulnerabilities
    Returns list of validation errors (empty if valid)
    """
    errors = []
    
    # Validate objective
    if not isinstance(objective, str):
        errors.append("objective must be a string")
    elif len(objective) > 10000:  # Reasonable limit
        errors.append("objective too long (max 10000 characters)")
    elif not objective.strip():
        errors.append("objective cannot be empty")
    
    # Validate context
    if not isinstance(context, dict):
        errors.append("context must be a dictionary")
    else:
        # Validate context fields
        for key, value in context.items():
            if not isinstance(key, str):
                errors.append(f"context key '{key}' must be a string")
            if isinstance(value, str) and len(value) > 50000:  # Reasonable limit for code
                errors.append(f"context['{key}'] too long (max 50000 characters)")
    
    # Validate constraints
    if not isinstance(constraints, dict):
        errors.append("constraints must be a dictionary")
    else:
        # Validate specific constraint values
        max_lines = constraints.get("max_lines")
        if max_lines is not None and (not isinstance(max_lines, int) or max_lines <= 0 or max_lines > 10000):
            errors.append("max_lines must be a positive integer <= 10000")
        
        timeout = constraints.get("timeout")
        if timeout is not None and (not isinstance(timeout, int) or timeout <= 0 or timeout > 300):
            errors.append("timeout must be a positive integer <= 300 seconds")
        
        complexity = constraints.get("complexity")
        if complexity is not None and complexity not in ["simple", "medium", "complex", "high"]:
            errors.append("complexity must be one of: simple, medium, complex, high")
    
    # Validate success_criteria
    if not isinstance(success_criteria, str):
        errors.append("success_criteria must be a string")
    elif len(success_criteria) > 1000:
        errors.append("success_criteria too long (max 1000 characters)")
    
    # Security checks for dangerous patterns (keep narrow to avoid false positives)
    dangerous_patterns = [
        r"\beval\s*\(",
        r"\bexec\s*\(",
        r"\bsubprocess\b",
        r"__import__",
    ]

    # Avoid scanning raw code context to prevent blocking legitimate snippets.
    scan_parts = [objective, success_criteria, str(constraints)]
    for key, value in context.items():
        if key in {"existing_code", "code", "snippet"}:
            continue
        scan_parts.append(str(value))
    all_text = " ".join(scan_parts)
    normalized_text = re.sub(r"\s+", " ", all_text.lower())
    for pattern in dangerous_patterns:
        if re.search(pattern, normalized_text):
            errors.append(f"potentially dangerous pattern detected: {pattern}")
    
    return errors


def generate_code(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str) -> Dict[str, Any]:
    """
    Stateless Qwen code generation subagent
    
    UserJot Principles:
    - No conversation history or persistent state
    - Pure function: same input always produces same output
    - Minimal required context only
    - Structured output with success metrics
    
    Args:
        objective: Clear description of code generation goals
        context: Requirements, specifications, existing code context
        constraints: Language, framework, size limitations
        success_criteria: How to measure generation success
        
    Returns:
        Structured code generation result with metrics
    """
    start_time = time.time()
    
    try:
        # INPUT VALIDATION AND SANITIZATION
        validation_errors = _validate_and_sanitize_inputs(objective, context, constraints, success_criteria)
        if validation_errors:
            return _create_error_response(f"Input validation failed: {'; '.join(validation_errors)}", start_time)
        
        # Extract required context (after validation)
        requirements = context.get("requirements", "")
        language = context.get("language", "python")
        framework = context.get("framework", "")
        existing_code = context.get("existing_code", "")
        style_guide = context.get("style_guide", "")
        
        # Extract constraints (after validation)
        max_lines = constraints.get("max_lines", 500)
        timeout = constraints.get("timeout", 30)
        complexity = constraints.get("complexity", "medium")
        
        if not objective and not requirements:
            return _create_error_response("No objective or requirements provided for code generation", start_time)
        
        # Prepare Qwen prompt
        qwen_prompt = _build_qwen_prompt(objective, requirements, language, framework, existing_code, style_guide, max_lines, complexity)
        
        # Execute Qwen command
        generated_code, qwen_success, qwen_execution_time = _execute_qwen_command(
            qwen_prompt, timeout
        )
        
        if not qwen_success:
            return _create_error_response("Qwen command execution failed", start_time)
        
        # Analyze generated code quality
        quality_metrics = _analyze_code_quality(generated_code, language, max_lines)
        quality_metrics["qwen_time"] = qwen_execution_time
        
        # Check success criteria
        success = _evaluate_success_criteria(generated_code, quality_metrics, success_criteria, max_lines)
        confidence = _calculate_confidence(quality_metrics, success)
        
        execution_time = time.time() - start_time

        return {
            "result": {
                "generated_code": generated_code,
                "language": language,
                "framework": framework,
                "estimated_lines": quality_metrics["line_count"],
                "quality_score": quality_metrics["quality_score"],
                "recommendations": quality_metrics["recommendations"],
                "summary": _generate_code_summary(quality_metrics, language, success),
            },
            "success": success,
            "confidence": confidence,
            "metrics": {
                "execution_time": execution_time,
                "qwen_execution_time": qwen_execution_time,
                "lines_generated": quality_metrics["line_count"],
                "quality_score": quality_metrics["quality_score"],
                "language": language,
                "complexity_target": complexity,
            },
            "notes": (
                f"Generated {quality_metrics['line_count']} lines of {language} code with "
                f"{quality_metrics['quality_score']:.2f} quality score"
            ),
        }
        
    except Exception as e:
        return _create_error_response(f"Code generation failed: {str(e)}", start_time)


def _build_qwen_prompt(objective: str, requirements: str, language: str, framework: str, existing_code: str, style_guide: str, max_lines: int, complexity: str) -> str:
    """Build optimized prompt for Qwen code generation"""
    
    prompt_parts = []
    
    # Core objective
    prompt_parts.append(f"Generate {language} code for: {objective}")
    
    # Requirements
    if requirements:
        prompt_parts.append(f"Requirements: {requirements}")
    
    # Framework context
    if framework:
        prompt_parts.append(f"Framework: {framework}")
    
    # Existing code context (if provided)
    if existing_code:
        prompt_parts.append(f"Existing code context:\n```{language}\n{existing_code}\n```")
    
    # Style guide
    if style_guide:
        prompt_parts.append(f"Style guide: {style_guide}")
    else:
        # Default style guidelines
        style_defaults = {
            "python": "Follow PEP 8, use type hints, include docstrings",
            "javascript": "Use ES6+, camelCase, include JSDoc comments",
            "typescript": "Use strict types, interfaces, include TSDoc",
            "java": "Follow Oracle conventions, use JavaDoc",
            "go": "Follow Go conventions, use go fmt style",
            "rust": "Follow Rust conventions, use rustfmt style"
        }
        prompt_parts.append(f"Style: {style_defaults.get(language, 'Follow language best practices')}")
    
    # Constraints
    prompt_parts.append(f"Maximum {max_lines} lines, {complexity} complexity")
    
    # Output format instructions
    prompt_parts.append(f"Return only the {language} code, no explanations or markdown formatting")
    
    return "\n\n".join(prompt_parts)


def _execute_qwen_command(prompt: str, timeout: int) -> tuple[str, bool, float]:
    """Execute Qwen command with the prepared prompt (SECURE & OPTIMIZED VERSION)"""
    try:
        qwen_start = time.time()
        commands_dir = _find_claude_commands_dir()
        if not commands_dir:
            return "", False, time.time() - qwen_start
        
        # PERFORMANCE OPTIMIZATION: Try direct import first (much faster)
        if commands_dir not in sys.path:
            sys.path.append(commands_dir)

        spec = importlib.util.find_spec("qwen")
        if spec is None:
            return _execute_qwen_subprocess(prompt, timeout, qwen_start, commands_dir)

        qwen_module = importlib.import_module("qwen")
        execute_qwen_request = getattr(qwen_module, "execute_qwen_request", None)
        if not callable(execute_qwen_request):
            return _execute_qwen_subprocess(prompt, timeout, qwen_start, commands_dir)

        result = execute_qwen_request(prompt)

        if result and isinstance(result, str):
            return result.strip(), True, time.time() - qwen_start
        return "", False, time.time() - qwen_start
            
    except Exception as e:
        print(f"Qwen execution error: {e}")
        return "", False, 0.0


def _execute_qwen_subprocess(
    prompt: str, timeout: int, start_time: float, commands_dir: str
) -> tuple[str, bool, float]:
    """Fallback subprocess execution (secure but slower)"""
    try:
        # SECURITY FIX: Use stdin to pass prompt instead of f-string injection
        # This prevents command injection attacks through malicious prompts
        python_script = textwrap.dedent(
            """
            import os
            import sys

            commands_dir = os.environ.get("WORLDAI_CLAUDE_COMMANDS_DIR") or os.environ.get("CLAUDE_COMMANDS_DIR")
            if commands_dir:
                sys.path.append(commands_dir)

            try:
                from qwen import execute_qwen_request
                prompt = sys.stdin.read()
                result = execute_qwen_request(prompt)
                print(result)
            except Exception as e:
                print(f"Error: {e}", file=sys.stderr)
                sys.exit(1)
            """
        ).lstrip()
        
        # Execute with secure stdin input
        env = os.environ.copy()
        env["WORLDAI_CLAUDE_COMMANDS_DIR"] = commands_dir
        cwd = os.path.dirname(os.path.abspath(__file__))
        if not os.path.isdir(cwd):
            raise FileNotFoundError(f"Subprocess cwd does not exist: {cwd}")

        result = subprocess.run(
            ["python", "-c", python_script],
            input=prompt,  # Pass prompt via stdin (secure)
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=cwd,
        )
        
        if result.returncode == 0:
            generated_code = result.stdout.strip()
            return generated_code, True, time.time() - start_time
        else:
            print(f"Qwen subprocess failed: {result.stderr}")
            return "", False, time.time() - start_time
            
    except subprocess.TimeoutExpired:
        return "", False, time.time() - start_time
    except Exception as e:
        print(f"Qwen subprocess error: {e}")
        return "", False, time.time() - start_time


def _analyze_code_quality(code: str, language: str, max_lines: int) -> Dict[str, Any]:
    """Analyze quality of generated code"""
    if not code or code.strip() == "":
        return {
            "line_count": 0,
            "quality_score": 0.0,
            "recommendations": ["No code generated"],
            "issues": ["Empty output"]
        }
    
    lines = code.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    
    quality_metrics = {
        "line_count": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "issues": [],
        "recommendations": []
    }
    
    # Basic quality checks
    # Check for basic code structure
    if language == "python":
        quality_score = _analyze_python_quality(code, quality_metrics)
    elif language in ["javascript", "typescript"]:
        quality_score = _analyze_js_quality(code, quality_metrics)
    else:
        quality_score = _analyze_generic_quality(code, quality_metrics)
    
    # Length compliance
    if len(lines) > max_lines:
        quality_score *= 0.8
        quality_metrics["issues"].append(f"Exceeds maximum lines ({len(lines)} > {max_lines})")
        quality_metrics["recommendations"].append("Consider breaking into smaller functions")
    
    quality_metrics["quality_score"] = round(quality_score, 2)
    return quality_metrics


def _analyze_python_quality(code: str, metrics: Dict[str, Any]) -> float:
    """Analyze Python-specific code quality"""
    score = 1.0
    
    # Check for basic Python patterns
    if "def " not in code and "class " not in code:
        score *= 0.8
        metrics["issues"].append("No functions or classes defined")
    
    # Check for docstrings
    if '"""' not in code and "'''" not in code:
        score *= 0.9
        metrics["recommendations"].append("Add docstrings for better documentation")
    
    # Check for imports (if needed)
    if "import " in code or "from " in code:
        score += 0.1  # Bonus for proper imports
    
    # Check for type hints
    if "->" in code or ": " in code:
        score += 0.1  # Bonus for type hints
        
    return min(1.0, score)


def _analyze_js_quality(code: str, metrics: Dict[str, Any]) -> float:
    """Analyze JavaScript/TypeScript code quality"""
    score = 1.0
    
    # Check for basic structure
    if "function " not in code and "=>" not in code and "class " not in code:
        score *= 0.8
        metrics["issues"].append("No functions or classes defined")
    
    # Check for modern syntax
    if "const " in code or "let " in code:
        score += 0.1  # Bonus for modern variable declarations
    
    if "var " in code:
        score *= 0.9
        metrics["recommendations"].append("Prefer const/let over var")
    
    return min(1.0, score)


def _analyze_generic_quality(code: str, metrics: Dict[str, Any]) -> float:
    """Analyze generic code quality"""
    score = 1.0
    
    # Basic structure checks
    lines = code.split('\n')
    comment_lines = sum(1 for line in lines if line.strip().startswith(('//','#', '/*', '*')))
    
    if comment_lines == 0:
        score *= 0.9
        metrics["recommendations"].append("Add comments for better code documentation")
    
    # Check for reasonable line lengths
    long_lines = sum(1 for line in lines if len(line) > 120)
    if long_lines > len(lines) * 0.1:  # More than 10% long lines
        score *= 0.9
        metrics["recommendations"].append("Consider shorter line lengths for readability")
    
    return score


def _evaluate_success_criteria(code: str, quality_metrics: Dict[str, Any], success_criteria: str, max_lines: int) -> bool:
    """Evaluate if generated code meets success criteria"""
    if not code or code.strip() == "":
        return False
    
    # Basic success: Code generated and reasonable quality
    basic_success = (
        quality_metrics["line_count"] > 0 and
        quality_metrics["quality_score"] >= 0.6 and
        quality_metrics["line_count"] <= max_lines
    )
    
    # Parse success criteria if provided
    if success_criteria and success_criteria != "Task completed successfully":
        criteria_lower = success_criteria.lower()
        
        # Check for specific criteria
        if "functional" in criteria_lower:
            # For functional code, need functions/classes
            return basic_success and ("def " in code or "function " in code or "class " in code)
        
        if "tested" in criteria_lower:
            # For tested code, need test patterns
            return basic_success and ("test" in code.lower() or "assert" in code.lower())
        
        if "documented" in criteria_lower:
            # For documented code, need comments/docstrings
            return basic_success and ('"""' in code or "'''" in code or "//" in code or "#" in code)
    
    return basic_success


def _calculate_confidence(quality_metrics: Dict[str, Any], success: bool) -> float:
    """Calculate confidence score for code generation"""
    if not success:
        return 0.0
    
    # Base confidence from quality score
    confidence = quality_metrics["quality_score"]
    
    # Adjust based on issues
    issue_count = len(quality_metrics.get("issues", []))
    if issue_count > 0:
        confidence *= (1.0 - (issue_count * 0.1))
    
    # Bonus for good structure
    if quality_metrics["line_count"] > 10:  # Non-trivial code
        confidence += 0.1
    
    return round(min(1.0, max(0.0, confidence)), 2)


def _generate_code_summary(quality_metrics: Dict[str, Any], language: str, success: bool) -> str:
    """Generate human-readable code generation summary"""
    line_count = quality_metrics["line_count"]
    quality_score = quality_metrics["quality_score"]
    
    if not success:
        return f"Code generation failed - {line_count} lines generated with quality {quality_score:.1f}"
    
    quality_level = "excellent" if quality_score >= 0.9 else "good" if quality_score >= 0.7 else "acceptable"
    
    return f"Generated {line_count} lines of {quality_level} {language} code (quality: {quality_score:.1f})"


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


def demo_qwen_subagent():
    """Demonstrate Qwen subagent functionality"""
    print("🤖 Qwen Coder Subagent Demo")
    print("=" * 40)
    
    # Test scenarios
    test_scenarios = [
        {
            "objective": "Create a simple calculator class",
            "context": {
                "language": "python",
                "requirements": "Basic arithmetic operations (add, subtract, multiply, divide)",
                "style_guide": "Use type hints and docstrings"
            },
            "constraints": {
                "max_lines": 50,
                "complexity": "simple"
            },
            "success_criteria": "Functional calculator with error handling"
        },
        {
            "objective": "Generate async data fetcher function",
            "context": {
                "language": "javascript", 
                "framework": "Node.js",
                "requirements": "Fetch data from API with error handling and retry logic"
            },
            "constraints": {
                "max_lines": 30,
                "complexity": "medium"
            },
            "success_criteria": "Async function with proper error handling"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📝 Test {i}: {scenario['objective']}")
        print("-" * 30)
        
        result = generate_code(
            scenario["objective"],
            scenario["context"], 
            scenario["constraints"],
            scenario["success_criteria"]
        )
        
        print(f"✅ Success: {result['success']}")
        print(f"🎯 Confidence: {result['confidence']}")
        print(f"⏱️ Time: {result['metrics']['execution_time']:.2f}s")
        
        if result['success']:
            print(f"📏 Lines Generated: {result['result']['estimated_lines']}")
            print(f"🏆 Quality Score: {result['result']['quality_score']}")
            print(f"💡 Summary: {result['result']['summary']}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    demo_qwen_subagent()
