#!/usr/bin/env python3
"""
UserJot Documentation Generator Subagent
Stateless documentation generation following UserJot patterns
"""

import time
import re
from typing import Dict, List, Any


def generate_docs(objective: str, context: Dict[str, Any], constraints: Dict[str, Any], success_criteria: str) -> Dict[str, Any]:
    """
    Stateless documentation generator subagent
    
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
        doc_type = context.get("doc_type", "api")
        format_type = context.get("format", "markdown")
        audience = context.get("audience", "developers")
        
        if not code:
            return _create_error_response("No code provided for documentation", start_time)
        
        # Analyze code structure
        analysis = _analyze_code_structure(code)
        
        # Generate documentation sections
        sections = _generate_doc_sections(analysis, doc_type, audience)
        
        # Format documentation
        formatted_docs = _format_documentation(sections, format_type)
        
        # Calculate completeness metrics
        completeness = _calculate_completeness(sections, analysis)
        
        execution_time = time.time() - start_time
        success = completeness >= 0.7 and len(sections) > 0
        
        return {
            "result": {
                "documentation": formatted_docs,
                "sections": list(sections.keys()),
                "completeness": round(completeness * 100, 1),
                "doc_type": doc_type,
                "format": format_type,
                "word_count": len(formatted_docs.split()),
                "summary": f"Generated {doc_type} documentation with {completeness*100:.1f}% completeness"
            },
            "success": success,
            "confidence": completeness,
            "metrics": {
                "execution_time": execution_time,
                "sections_generated": len(sections),
                "completeness": completeness,
                "word_count": len(formatted_docs.split())
            },
            "notes": f"Generated {len(sections)} documentation sections"
        }
        
    except Exception as e:
        return _create_error_response(f"Documentation generation failed: {str(e)}", start_time)


def _analyze_code_structure(code: str) -> Dict[str, Any]:
    """Analyze code structure for documentation"""
    analysis = {
        "functions": [],
        "classes": [],
        "imports": [],
        "constants": [],
        "docstrings": []
    }
    
    lines = code.split('\n')
    current_class = None
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Extract imports
        if stripped.startswith(('import ', 'from ')):
            analysis["imports"].append(stripped)
        
        # Extract classes
        if stripped.startswith('class '):
            class_match = re.match(r'class\s+(\w+)', stripped)
            if class_match:
                current_class = class_match.group(1)
                analysis["classes"].append({
                    "name": current_class,
                    "line": i + 1,
                    "methods": []
                })
        
        # Extract functions/methods
        if stripped.startswith('def '):
            func_match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', stripped)
            if func_match:
                func_name = func_match.group(1)
                params = func_match.group(2)
                
                func_info = {
                    "name": func_name,
                    "params": [p.strip() for p in params.split(',') if p.strip()],
                    "line": i + 1,
                    "is_method": current_class is not None
                }
                
                if current_class:
                    # Add to current class methods
                    for cls in analysis["classes"]:
                        if cls["name"] == current_class:
                            cls["methods"].append(func_info)
                            break
                else:
                    analysis["functions"].append(func_info)
        
        # Extract constants (uppercase variables)
        if '=' in stripped and stripped.split('=')[0].strip().isupper():
            const_name = stripped.split('=')[0].strip()
            analysis["constants"].append(const_name)
        
        # Extract docstrings
        if '"""' in stripped or "'''" in stripped:
            analysis["docstrings"].append(i + 1)
    
    return analysis


def _generate_doc_sections(analysis: Dict[str, Any], doc_type: str, audience: str) -> Dict[str, str]:
    """Generate documentation sections based on analysis"""
    sections = {}
    
    # Title and overview
    sections["title"] = _generate_title(analysis, doc_type)
    sections["overview"] = _generate_overview(analysis, audience)
    
    if doc_type == "api":
        sections["installation"] = _generate_installation_section()
        sections["quick_start"] = _generate_quick_start(analysis)
        sections["api_reference"] = _generate_api_reference(analysis)
        sections["examples"] = _generate_examples(analysis)
    
    elif doc_type == "user_guide":
        sections["getting_started"] = _generate_getting_started(analysis)
        sections["usage"] = _generate_usage_examples(analysis)
        sections["configuration"] = _generate_configuration_section()
    
    elif doc_type == "technical":
        sections["architecture"] = _generate_architecture_section(analysis)
        sections["implementation"] = _generate_implementation_details(analysis)
        sections["dependencies"] = _generate_dependencies_section(analysis)
    
    # Common sections
    if analysis["functions"] or analysis["classes"]:
        sections["functions"] = _generate_functions_documentation(analysis["functions"])
        sections["classes"] = _generate_classes_documentation(analysis["classes"])
    
    return sections


def _generate_title(analysis: Dict[str, Any], doc_type: str) -> str:
    """Generate documentation title"""
    if analysis["classes"]:
        main_class = analysis["classes"][0]["name"]
        return f"# {main_class} {doc_type.title()} Documentation"
    elif analysis["functions"]:
        return f"# Module {doc_type.title()} Documentation"
    else:
        return f"# {doc_type.title()} Documentation"


def _generate_overview(analysis: Dict[str, Any], audience: str) -> str:
    """Generate overview section"""
    overview = "## Overview\n\n"
    
    if analysis["classes"]:
        overview += f"This module contains {len(analysis['classes'])} class(es) "
        overview += f"with a total of {sum(len(c['methods']) for c in analysis['classes'])} methods.\n\n"
    
    if analysis["functions"]:
        overview += f"Provides {len(analysis['functions'])} utility functions.\n\n"
    
    if audience == "developers":
        overview += "This documentation is intended for developers integrating with this module.\n\n"
    else:
        overview += "This documentation provides usage guidance for end users.\n\n"
    
    return overview


def _generate_installation_section() -> str:
    """Generate installation instructions"""
    return """## Installation

```bash
pip install package-name
```

Or install from source:
```bash
git clone repository-url
cd repository-name
pip install -e .
```
"""


def _generate_quick_start(analysis: Dict[str, Any]) -> str:
    """Generate quick start guide"""
    quick_start = "## Quick Start\n\n"
    
    if analysis["classes"]:
        main_class = analysis["classes"][0]["name"]
        quick_start += f"```python\nfrom module import {main_class}\n\n"
        quick_start += f"# Create instance\ninstance = {main_class}()\n\n"
        
        # Show first method if available
        if analysis["classes"][0]["methods"]:
            method = analysis["classes"][0]["methods"][0]
            quick_start += f"# Use main functionality\nresult = instance.{method['name']}()\n"
        
        quick_start += "```\n\n"
    
    elif analysis["functions"]:
        func = analysis["functions"][0]
        quick_start += f"```python\nfrom module import {func['name']}\n\n"
        quick_start += f"# Call function\nresult = {func['name']}()\n```\n\n"
    
    return quick_start


def _generate_api_reference(analysis: Dict[str, Any]) -> str:
    """Generate API reference section"""
    api_ref = "## API Reference\n\n"
    
    # Document classes
    for cls in analysis["classes"]:
        api_ref += f"### {cls['name']}\n\n"
        api_ref += f"Class defined at line {cls['line']}\n\n"
        
        for method in cls["methods"]:
            params_str = ", ".join(method["params"])
            api_ref += f"#### {method['name']}({params_str})\n\n"
            api_ref += f"Method description here.\n\n"
    
    # Document functions
    for func in analysis["functions"]:
        params_str = ", ".join(func["params"])
        api_ref += f"### {func['name']}({params_str})\n\n"
        api_ref += f"Function description here.\n\n"
    
    return api_ref


def _generate_examples(analysis: Dict[str, Any]) -> str:
    """Generate usage examples"""
    examples = "## Examples\n\n"
    
    if analysis["classes"]:
        examples += "### Basic Usage\n\n```python\n"
        cls = analysis["classes"][0]
        examples += f"from module import {cls['name']}\n\n"
        examples += f"# Initialize\nobj = {cls['name']}()\n\n"
        
        for method in cls["methods"][:2]:  # Show first 2 methods
            examples += f"# Use {method['name']}\nresult = obj.{method['name']}()\nprint(result)\n\n"
        
        examples += "```\n\n"
    
    return examples


def _generate_functions_documentation(functions: List[Dict[str, Any]]) -> str:
    """Generate functions documentation"""
    if not functions:
        return ""
    
    doc = "## Functions\n\n"
    
    for func in functions:
        params_str = ", ".join(func["params"]) if func["params"] else ""
        doc += f"### `{func['name']}({params_str})`\n\n"
        doc += f"Function at line {func['line']}\n\n"
        doc += "**Parameters:**\n"
        
        for param in func["params"]:
            if param and param != "self":
                doc += f"- `{param}`: Parameter description\n"
        
        doc += "\n**Returns:**\nReturn value description\n\n"
    
    return doc


def _generate_classes_documentation(classes: List[Dict[str, Any]]) -> str:
    """Generate classes documentation"""
    if not classes:
        return ""
    
    doc = "## Classes\n\n"
    
    for cls in classes:
        doc += f"### `{cls['name']}`\n\n"
        doc += f"Class definition at line {cls['line']}\n\n"
        
        if cls["methods"]:
            doc += "**Methods:**\n\n"
            for method in cls["methods"]:
                params_str = ", ".join(method["params"]) if method["params"] else ""
                doc += f"#### `{method['name']}({params_str})`\n\n"
                doc += f"Method description\n\n"
        
        doc += "\n"
    
    return doc


def _generate_getting_started(analysis: Dict[str, Any]) -> str:
    """Generate getting started section"""
    return "## Getting Started\n\nStep-by-step guide to using this module.\n\n"


def _generate_usage_examples(analysis: Dict[str, Any]) -> str:
    """Generate usage examples for user guide"""
    return "## Usage Examples\n\nCommon usage patterns and examples.\n\n"


def _generate_configuration_section() -> str:
    """Generate configuration section"""
    return "## Configuration\n\nConfiguration options and settings.\n\n"


def _generate_architecture_section(analysis: Dict[str, Any]) -> str:
    """Generate architecture documentation"""
    return "## Architecture\n\nSystem architecture and design decisions.\n\n"


def _generate_implementation_details(analysis: Dict[str, Any]) -> str:
    """Generate implementation details"""
    return "## Implementation Details\n\nTechnical implementation information.\n\n"


def _generate_dependencies_section(analysis: Dict[str, Any]) -> str:
    """Generate dependencies section"""
    deps = "## Dependencies\n\n"
    
    if analysis["imports"]:
        deps += "**Imports:**\n"
        for imp in analysis["imports"]:
            deps += f"- `{imp}`\n"
        deps += "\n"
    
    return deps


def _format_documentation(sections: Dict[str, str], format_type: str) -> str:
    """Format documentation in specified format"""
    if format_type == "markdown":
        return "\n".join(sections.values())
    elif format_type == "rst":
        # Convert markdown to RST-like format
        formatted = ""
        for content in sections.values():
            # Simple conversion - replace # with =
            rst_content = content.replace("# ", "")
            rst_content = rst_content.replace("## ", "")
            rst_content = rst_content.replace("### ", "")
            formatted += rst_content + "\n"
        return formatted
    else:
        return "\n".join(sections.values())


def _calculate_completeness(sections: Dict[str, str], analysis: Dict[str, Any]) -> float:
    """Calculate documentation completeness score"""
    base_score = 0.5  # Base for having any documentation
    
    # Score for having key sections
    key_sections = ["title", "overview", "examples"]
    section_score = sum(0.1 for section in key_sections if section in sections)
    
    # Score for documenting code elements
    code_coverage = 0.0
    total_elements = len(analysis["functions"]) + len(analysis["classes"])
    
    if total_elements > 0:
        documented_elements = 0
        if "functions" in sections and analysis["functions"]:
            documented_elements += len(analysis["functions"])
        if "classes" in sections and analysis["classes"]:
            documented_elements += len(analysis["classes"])
        
        code_coverage = documented_elements / total_elements * 0.4
    
    return min(1.0, base_score + section_score + code_coverage)


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