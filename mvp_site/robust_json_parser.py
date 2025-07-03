"""
Robust JSON parser for handling various forms of incomplete or malformed JSON from LLMs
"""
import json
import re
import logging
from typing import Tuple, Dict, Any, Optional
from json_utils import (
    try_parse_json,
    complete_truncated_json,
    extract_json_boundaries,
    extract_field_value
)


class RobustJSONParser:
    """
    A robust parser that can handle various forms of incomplete JSON responses.
    Designed specifically for LLM outputs that might be truncated or malformed.
    """
    
    @staticmethod
    def parse(text: str) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Attempts to parse JSON text with multiple fallback strategies.
        
        Args:
            text: The potentially incomplete JSON string
            
        Returns:
            tuple: (parsed_dict or None, was_incomplete)
        """
        if not text:
            return None, False
        
        text = text.strip()
        
        # Strategy 1: Try standard JSON parsing first
        result, success = try_parse_json(text)
        if success:
            return result, False
        
        # Strategy 2: Find JSON boundaries and fix common issues
        try:
            fixed_json = RobustJSONParser._fix_json_boundaries(text)
            if fixed_json != text:
                result = json.loads(fixed_json)
                logging.info("Successfully fixed JSON boundaries")
                return result, True
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logging.debug(f"JSON boundary fix failed: {e}")
            pass
        
        # Strategy 3: Try to complete incomplete JSON
        try:
            completed_json = RobustJSONParser._complete_json(text)
            result = json.loads(completed_json)
            logging.info("Successfully completed incomplete JSON")
            return result, True
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logging.debug(f"JSON completion failed: {e}")
            pass
        
        # Strategy 4: Extract fields individually using regex
        try:
            extracted = RobustJSONParser._extract_fields(text)
            if extracted:
                logging.info("Successfully extracted fields from malformed JSON")
                return extracted, True
        except Exception as e:
            logging.debug(f"Field extraction failed: {e}")
            pass
        
        # Strategy 5: Last resort - try to fix and parse again
        try:
            aggressively_fixed = RobustJSONParser._aggressive_fix(text)
            if aggressively_fixed and aggressively_fixed != '{}':
                result = json.loads(aggressively_fixed)
                logging.info("Successfully parsed with aggressive fixes")
                return result, True
        except json.JSONDecodeError:
            pass
        except Exception as e:
            logging.debug(f"Aggressive fix failed: {e}")
            pass
        
        logging.error("All JSON parsing strategies failed")
        return None, True
    
    @staticmethod
    def _fix_json_boundaries(text: str) -> str:
        """Fix common JSON boundary issues"""
        extracted = extract_json_boundaries(text)
        return extracted if extracted else text
    
    @staticmethod
    def _complete_json(text: str) -> str:
        """Attempt to complete incomplete JSON"""
        return complete_truncated_json(text)
    
    @staticmethod
    def _extract_fields(text: str) -> Optional[Dict[str, Any]]:
        """Extract individual fields using regex"""
        result = {}
        
        # Extract narrative field
        narrative = extract_field_value(text, 'narrative')
        if narrative is not None:
            result['narrative'] = narrative
        
        # Extract entities_mentioned array
        entities_match = re.search(
            r'"entities_mentioned"\s*:\s*\[(.*?)\]',
            text,
            re.DOTALL
        )
        if entities_match:
            entities_str = entities_match.group(1)
            # Parse entity list
            entities = []
            for match in re.finditer(r'"([^"]*)"', entities_str):
                entities.append(match.group(1))
            result['entities_mentioned'] = entities
        
        # Extract location_confirmed
        location = extract_field_value(text, 'location_confirmed')
        if location is not None:
            result['location_confirmed'] = location
        
        return result if result else None
    
    @staticmethod
    def _aggressive_fix(text: str) -> str:
        """Aggressively fix JSON by rebuilding it from extracted parts"""
        extracted = RobustJSONParser._extract_fields(text)
        if not extracted:
            # If we can't extract anything, try to at least get some text
            # Look for any substantial text content
            text_match = re.search(r':\s*"([^"]+)', text)
            if text_match:
                extracted = {'narrative': text_match.group(1)}
            else:
                return '{}'
        
        # Rebuild clean JSON
        return json.dumps(extracted)


def parse_llm_json_response(response_text: str) -> Tuple[Dict[str, Any], bool]:
    """
    Parse potentially incomplete JSON response from LLM.
    
    Args:
        response_text: Raw response from LLM that should be JSON
        
    Returns:
        tuple: (parsed_dict, was_incomplete)
    """
    parser = RobustJSONParser()
    result, was_incomplete = parser.parse(response_text)
    
    if result is None:
        # If no JSON could be parsed, treat the entire text as narrative
        logging.info("No JSON found in response, treating as plain text narrative")
        return {"narrative": response_text.strip(), "entities_mentioned": [], "location_confirmed": "Unknown"}, True
    
    # Ensure required fields exist
    if 'narrative' not in result:
        result['narrative'] = ""
    if 'entities_mentioned' not in result:
        result['entities_mentioned'] = []
    if 'location_confirmed' not in result:
        result['location_confirmed'] = "Unknown"
    
    return result, was_incomplete


# Example usage for testing
if __name__ == "__main__":
    # Test with the user's example
    incomplete_json = '''{"narrative": "[SESSION_HEADER]\\nTimestamp: Year 1620, Kythorn, Day 10, 02:05 PM\\nLocation: The Eastern March, on the road to the Dragon's Tooth mountains.\\nStatus: Lvl 1 Fighter/Paladin | HP: 12/12 | Gold: 25gp\\nResources:\\n- Hero Points: 1/1\\n\\nSir Andrew ignored Gareth's probing question, his focus narrowing back to the mission. He folded the map with crisp, efficient movements and tucked it away. His duty was clear; the feelings of his companions were secondary variables. He turned to the other two members of his small company, his expression a mask of command.\\n\\n\\"Report,\\" he said, his voice flat and devoid of warmth. He looked first to Kiera Varrus, the scout, whose cynical eyes were already scanning the treacherous path ahead.\\n\\nKiera spat on the ground, pulling her leather hood tighter against the wind. \\"It's a goat track at best, Sir Knight. Not a proper road. The ground is loose shale, easy to turn an ankle or alert anything hiding in the rocks.\\" She squinted at the mountains.'''
    
    result, was_incomplete = parse_llm_json_response(incomplete_json)
    print(f"Was incomplete: {was_incomplete}")
    print(f"Narrative length: {len(result['narrative'])}")
    print(f"First 100 chars: {result['narrative'][:100]}...")
    print(f"Last 100 chars: ...{result['narrative'][-100:]}")