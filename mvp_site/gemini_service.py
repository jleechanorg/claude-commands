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
TARGET_WORD_COUNT = 200
HISTORY_TURN_LIMIT = 50
MAX_INPUT_TOKENS = 200000 
SAFE_CHAR_LIMIT = MAX_INPUT_TOKENS * 4
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
        header_title = "" # Not used for system_instruction parameter, but kept for consistency/future
        if instruction_type == "narrative":
            file_name = "narrative_system_instruction.md"
            header_title = "NARRATIVE INSTRUCTIONS"
        elif instruction_type == "mechanics":
            file_name = "mechanics_system_instruction.md"
            header_title = "MECHANICS AND PROTOCOL INSTRUCTIONS"
        elif instruction_type == "calibration":
            file_name = "calibration_instruction.md"
            header_title = "CALIBRATION PROTOCOL INSTRUCTIONS"
        elif instruction_type == "destiny_ruleset": # NEW TYPE
            file_name = "destiny_ruleset.md"
            header_title = "DEFAULT RULESET" # Optional header for internal understanding
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

def _call_gemini_api(prompt_contents, system_instruction_text=None):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    logging.info(f"--- Calling Gemini API with prompt: {str(prompt_contents)[:300]}... ---")
    
    generation_config_params = {
        "max_output_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "safety_settings": SAFETY_SETTINGS
    }
    if system_instruction_text:
        generation_config_params["system_instruction"] = types.Part(text=system_instruction_text)

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

def _truncate_context(story_context):
    """
    Truncates the story context first by HISTORY_TURN_LIMIT, and then
    further by character count if it still exceeds the safety limit.
    """
    # 1. Apply the turn limit first.
    context = list(story_context[-HISTORY_TURN_LIMIT:])
    
    # 2. Check character count and truncate further if needed.
    def calculate_total_chars(ctx):
        return sum(len(entry.get('text', '')) for entry in ctx)

    total_chars = calculate_total_chars(context)
    
    while total_chars > SAFE_CHAR_LIMIT and len(context) > 1:
        # Remove the oldest entry (at the beginning of the list)
        context.pop(0)
        total_chars = calculate_total_chars(context)
        logging.warning(f"Context exceeded safe char limit after turn limit. Truncating. New char count: {total_chars}")
        
    return context

@log_exceptions
def get_initial_story(prompt, selected_prompts=None):
    """Generates the initial story opening, using system_instruction parameter, including default ruleset."""
    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for initial story. Using none.")

    system_instruction_parts = []
    # Consistent order for instructions
    # Narrative, Mechanics, Calibration (from checkboxes)
    for p_type in ['narrative', 'mechanics', 'calibration']: 
        if p_type in selected_prompts:
            content = _load_instruction_file(p_type)
            if content:
                system_instruction_parts.append(content)
    
    # NEW: Always include the destiny_ruleset as a default system instruction
    destiny_ruleset_content = _load_instruction_file('destiny_ruleset')
    if destiny_ruleset_content:
        system_instruction_parts.append(destiny_ruleset_content)


    system_instruction_final = "\n\n".join(system_instruction_parts)
    
    full_prompt = f"{prompt}\n\n(Please keep the response to about {TARGET_WORD_COUNT} words.)"
    
    contents = [types.Content(role="user", parts=[types.Part(text=full_prompt)])]
    
    response = _call_gemini_api(contents, system_instruction_text=system_instruction_final)
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context, selected_prompts=None):
    """Generates the next part of the story, passing selected system instructions (excluding calibration), including default ruleset."""
    
    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for continue_story. Using none.")

    system_instruction_parts = []
    # Filter out 'calibration' for continue_story calls
    # NEW: Also ensure consistent order for continue_story
    filtered_prompts = [p_type for p_type in selected_prompts if p_type in ['narrative', 'mechanics']]

    # Load content for narrative and mechanics
    for p_type in filtered_prompts: 
        content = _load_instruction_file(p_type)
        if content:
            system_instruction_parts.append(content)
    
    # NEW: Always include the destiny_ruleset for continue_story too
    destiny_ruleset_content = _load_instruction_file('destiny_ruleset')
    if destiny_ruleset_content:
        system_instruction_parts.append(destiny_ruleset_content)


    system_instruction_final = "\n\n".join(system_instruction_parts)

    recent_context = _truncate_context(story_context)
    
    # Build a single context string from the history (User's preferred method)
    history_parts = []
    for entry in recent_context:
        actor_label = "Story" if entry.get('actor') == 'gemini' else "You"
        history_parts.append(f"{actor_label}: {entry.get('text')}")
    
    context_string = "\n\n".join(history_parts)

    # Create the final prompt for the current user turn (User's preferred method)
    if mode == 'character':
        prompt_template = "Acting as the main character do {user_input}. Continue the story in about {word_count} words."
    else: # god mode
        # User wants direct pass-through for god mode
        prompt_template = "Acting as god or the dungeon master (DM) do {user_input}"

     # Only format with word_count if it's character mode
    if mode == 'character':
        current_prompt_text = prompt_template.format(user_input=user_input, word_count=TARGET_WORD_COUNT)
    else: # god mode
        current_prompt_text = prompt_template.format(user_input=user_input)

    full_prompt = f"CONTEXT:\n{context_string}\n\nYOUR TURN:\n{current_prompt_text}"
    
    response = _call_gemini_api([full_prompt], system_instruction_text=system_instruction_final) 
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
    turn_2_response = continue_story(turn_2_prompt, 'god', history, selected_prompts=test_selected_prompts)
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
    turn_3_response = continue_story(turn_3_prompt, 'god', history, selected_prompts=test_selected_prompts)
    print("\\n--- LIVE RESPONSE 3 ---")
    print(turn_3_response)
    print("--- END OF RESPONSE 3 ---\\n")
