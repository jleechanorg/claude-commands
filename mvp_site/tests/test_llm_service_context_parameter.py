"""
Regression test to ensure _maybe_get_gemini_code_execution_evidence is called with context parameter.

This test verifies that continue_story() calls _maybe_get_gemini_code_execution_evidence
with the required 'context' keyword argument to prevent TypeError.

This prevents regression of the bug where context parameter was missing,
causing: "TypeError: _maybe_get_gemini_code_execution_evidence() missing 1 required keyword-only argument: 'context'"
"""

from __future__ import annotations

import ast
import inspect
from unittest.mock import Mock

import pytest

from mvp_site import constants
from mvp_site import llm_service


def test_continue_story_calls_maybe_get_gemini_code_execution_evidence_with_context():
    """Test that continue_story calls _maybe_get_gemini_code_execution_evidence with context parameter.
    
    This test ensures the bug where context parameter was missing is fixed.
    The bug caused: TypeError: _maybe_get_gemini_code_execution_evidence() missing 1 required keyword-only argument: 'context'
    
    Uses AST parsing to verify the function call includes the context parameter,
    making the test robust to code formatting changes.
    """
    # Get the source code of continue_story function
    source = inspect.getsource(llm_service.continue_story)
    
    # Parse the source into an AST so the test is robust to formatting changes
    tree = ast.parse(source)
    
    found_call = False
    found_context_kw = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Handle both direct and attribute calls:
            # _maybe_get_gemini_code_execution_evidence(...) or module._maybe_get_gemini_code_execution_evidence(...)
            func = node.func
            func_name = None
            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr
            
            if func_name == "_maybe_get_gemini_code_execution_evidence":
                found_call = True
                for kw in node.keywords:
                    if kw.arg == "context":
                        # We only require the context keyword to be present; its exact
                        # formatting in source is irrelevant. Optionally, ensure it is the
                        # literal string "continue_story" when that is statically detectable.
                        if isinstance(kw.value, ast.Constant) and kw.value.value == "continue_story":
                            found_context_kw = True
                        else:
                            # If the value is computed (e.g., variable), we still accept
                            # that the context keyword is provided.
                            found_context_kw = True
    
    assert found_call, (
        "continue_story() should call _maybe_get_gemini_code_execution_evidence()"
    )
    assert found_context_kw, (
        "continue_story() must call _maybe_get_gemini_code_execution_evidence() with the 'context' "
        "keyword argument (e.g., context='continue_story'). Missing context causes: TypeError: "
        "missing 1 required keyword-only argument: 'context'"
    )


def test_maybe_get_gemini_code_execution_evidence_requires_context_parameter():
    """Test that _maybe_get_gemini_code_execution_evidence raises TypeError without context parameter.
    
    This verifies the function signature enforces the context parameter requirement,
    preventing accidental calls without the required parameter.
    """
    mock_api_response = Mock()

    # This should raise TypeError because context is missing
    with pytest.raises(TypeError, match="missing 1 required keyword-only argument: 'context'"):
        llm_service._maybe_get_gemini_code_execution_evidence(
            provider_name=constants.LLM_PROVIDER_GEMINI,
            model_name="gemini-2.0-flash-exp",
            api_response=mock_api_response,
            # context parameter is missing - should raise TypeError
        )
