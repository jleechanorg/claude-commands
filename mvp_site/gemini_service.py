import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONSTANTS ---
MODEL_NAME = 'gemini-2.5-flash-preview-05-20'
MAX_TOKENS = 8192 
TEMPERATURE = 0.9
TARGET_WORD_COUNT = 400
HISTORY_TURN_LIMIT = 50
SAFETY_SETTINGS = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]
# --- END CONSTANTS ---

_client = None

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache = {} 

def _load_instruction_file(instruction_type):
    global _loaded_instructions_cache
    if instruction_type not in _loaded_instructions_cache:
        file_name = ""
        header_title = ""
        if instruction_type == "narrative":
            file_name = "narrative_system_instruction.md"
            header_title = "NARRATIVE INSTRUCTIONS"
        elif instruction_type == "mechanics":
            file_name = "mechanics_system_instruction.md"
            header_title = "MECHANICS AND PROTOCOL INSTRUCTIONS"
        elif instruction_type == "calibration":
            file_name = "calibration_instruction.md"
            header_title = "CALIBRATION PROTOCOL INSTRUCTIONS"
        else:
            logging.warning(f"Unknown instruction type requested: {instruction_type}")
            _loaded_instructions_cache[instruction_type] = ""
            return ""

        file_path = os.path.join(os.path.dirname(__file__), 'prompts', file_name)
        content = ""
        try:
            with open(file_path, 'r') as f:
                content = f.read().strip()
            logging.info(f"Loaded {instruction_type} instruction from {file_path}")
        except FileNotFoundError:
            logging.warning(f"System instruction file not found: {file_path}. Proceeding without these instructions.")
        except Exception as e:
            logging.error(f"Error loading system instruction file {file_path}: {e}")
        
        # Store with header for direct use in prompt
        # We only add headers here if we intend to prepend, for system_instruction, it's the raw content
        _loaded_instructions_cache[instruction_type] = content 
        
    return _loaded_instructions_cache.get(instruction_type, "")


def get_client():
    """Initializes and returns a singleton Gemini client."""
    global _client
    if _client is None:
        logging.info("--- Initializing Gemini Client ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
        _client = genai.Client(api_key=api_key)
        logging.info("--- Gemini Client Initialized Successfully ---")
    return _client

# MODIFIED: _call_gemini_api now accepts system_instruction_text
def _call_gemini_api(prompt_contents, system_instruction_text=None):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    logging.info(f"--- Calling Gemini API with prompt: {str(prompt_contents)[:300]}... ---")
    
    # NEW: Conditionally add system_instruction to GenerateContentConfig
    generation_config_params = {
        "max_output_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "safety_settings": SAFETY_SETTINGS
    }
    if system_instruction_text:
        generation_config_params["system_instruction"] = types.Part(text=system_instruction_text) # Correctly wrap for system_instruction

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_contents,
        config=types.GenerateContentConfig(**generation_config_params)
    )
    return response

def _get_text_from_response(response):
    """Safely extracts text from a Gemini response object."""
    try:
        if response.text:
            return response.text
    except ValueError as e:
        logging.warning(f"ValueError while extracting text: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in _get_text_from_response: {e}")
    
    logging.warning(f"--- Response did not contain valid text. Full response object: {response} ---")
    return "[System Message: The model returned a non-text response. Please check the logs for details.]"

@log_exceptions
def get_initial_story(prompt, selected_prompts=None):
    """Generates the initial story opening, using system_instruction parameter."""
    if selected_prompts is None:
        selected_prompts = []
        logging.warning("No specific system prompts selected for initial story. Using none.")

    system_instruction_parts = []
    # Load raw content for each selected prompt type, without headers here
    for p_type in ['narrative', 'mechanics', 'calibration']: # Consistent order
        if p_type in selected_prompts:
            content = _load_instruction_file(p_type)
            if content:
                system_instruction_parts.append(content)

    # Combine all selected instructions into one string for the system_instruction parameter
    system_instruction_final = "\n\n".join(system_instruction_parts)
    
    # User prompt itself (without system_prefix)
    full_prompt = f"{prompt}\n\n(Please keep the response to about {TARGET_WORD_COUNT} words.)"
    
    contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]
    
    # Pass system_instruction_final to _call_gemini_api
    response = _call_gemini_api(contents, system_instruction_text=system_instruction_final)
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story by concatenating the chat history."""
    
    # Take only the most recent turns from the full story context.
    recent_context = story_context[-HISTORY_TURN_LIMIT:]
    
    # Build a single context string from the history
    history_parts = []
    for entry in recent_context:
        actor_label = "Story" if entry.get('actor') == 'gemini' else "You"
        history_parts.append(f"{actor_label}: {entry.get('text')}")
    
    context_string = "\n\n".join(history_parts)

    # Create the final prompt for the current user turn
    if mode == 'character':
        prompt_template = "Acting as the main character {user_input}. Continue the story in about {word_count} words."
    else: # god mode
        prompt_template = "{user_input}. Continue the story in about {word_count} words."

    current_prompt_text = prompt_template.format(user_input=user_input, word_count=TARGET_WORD_COUNT)

    # Combine the context and the current prompt into one large string.
    full_prompt = f"CONTEXT:\n{context_string}\n\nYOUR TURN:\n{current_prompt_text}"
    
    # Call the API helper with the single, concatenated prompt string.
    # Note: continue_story does NOT use system_instruction as it's set in the initial call
    response = _call_gemini_api([full_prompt]) 
    return _get_text_from_response(response)

# --- Main block for rapid, direct testing ---
if __name__ == "__main__":
    print("--- Running gemini_service.py in chained conversation test mode ---")
    
    try:
        with open('local_api_key.txt', 'r') as f:
            api_key = f.read().strip()
        os.environ["GEMINI_API_KEY"] = api_key
        print("Successfully loaded API key from local_api_key.txt")
    except FileNotFoundError:
        print("\\nERROR: 'local_api_key.txt' not found.")
        sys.exit(1)
        
    get_client() # Initialize client
    
    # Example usage for testing: pass all prompt types
    test_selected_prompts = ['narrative', 'mechanics', 'calibration']

    # --- Turn 1: Initial Story ---
    print("\\n--- Turn 1: get_initial_story ---")
    turn_1_prompt = "start a story about a haunted lighthouse"
    print(f"Using prompt: '{turn_1_prompt}' with selected prompts: {test_selected_prompts}")
    turn_1_response = get_initial_story(turn_1_prompt, selected_prompts=test_selected_prompts)
    print("\\n--- LIVE RESPONSE 1 ---")
    print(turn_1_response)
    print("--- END OF RESPONSE 1 ---\\n")
    
    # Create the initial history from the real response
    history = [{'actor': 'user', 'text': turn_1_prompt}, {'actor': 'gemini', 'text': turn_1_response}]

    # --- Turn 2: Continue Story ---
    print("\\n--- Turn 2: continue_story ---")
    turn_2_prompt = "A lone ship, tossed by the raging sea, sees a faint, flickering light from the abandoned tower."
    print(f"Using prompt: '{turn_2_prompt}'")
    turn_2_response = continue_story(turn_2_prompt, 'god', history)
    print("\\n--- LIVE RESPONSE 2 ---")
    print(turn_2_response)
    print("--- END OF RESPONSE 2 ---\\n")
    
    # Update the history with the real response from turn 2
    history.append({'actor': 'user', 'text': turn_2_prompt})
    history.append({'actor': 'gemini', 'text': turn_2_response})

    # --- Turn 3: Continue Story Again ---
    print("\\n--- Turn 3: continue_story ---")
    turn_3_prompt = "The ship's captain, a grizzled old sailor named Silas, decides to steer towards the light, ignoring the warnings of his crew."
    print(f"Using prompt: '{turn_3_prompt}'")
    turn_3_response = continue_story(turn_3_prompt, 'god', history)
    print("\\n--- LIVE RESPONSE 3 ---")
    print(turn_3_response)
    print("--- END OF RESPONSE 3 ---\\n")
