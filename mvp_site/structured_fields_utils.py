"""
Utility functions for handling structured fields in AI responses.
Prevents code duplication across main.py and other modules.
"""

import constants


def extract_structured_fields(gemini_response_obj):
    """
    Extract structured fields from a GeminiResponse object.
    
    Args:
        gemini_response_obj: GeminiResponse object with optional structured_response
        
    Returns:
        dict: Dictionary containing structured fields, empty if none present
    """
    structured_fields = {}
    
    if gemini_response_obj.structured_response:
        structured_fields = {
            constants.FIELD_SESSION_HEADER: getattr(gemini_response_obj.structured_response, constants.FIELD_SESSION_HEADER, ''),
            constants.FIELD_PLANNING_BLOCK: getattr(gemini_response_obj.structured_response, constants.FIELD_PLANNING_BLOCK, ''),
            constants.FIELD_DICE_ROLLS: getattr(gemini_response_obj.structured_response, constants.FIELD_DICE_ROLLS, []),
            constants.FIELD_RESOURCES: getattr(gemini_response_obj.structured_response, constants.FIELD_RESOURCES, ''),
            constants.FIELD_DEBUG_INFO: getattr(gemini_response_obj.structured_response, constants.FIELD_DEBUG_INFO, {})
        }
    
    return structured_fields