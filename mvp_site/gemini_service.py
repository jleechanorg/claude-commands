import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions
import sys
import json
import re
import datetime
from game_state import GameState
import constants

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def json_datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# --- CONSTANTS ---
# Use flash for standard, cheaper operations.
DEFAULT_MODEL = 'gemini-2.5-flash'
# Use pro for the single, large-context operation (initial SRD load).
LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'

MAX_TOKENS = 8192 
TEMPERATURE = 0.9
TARGET_WORD_COUNT = 400
HISTORY_TURN_LIMIT = 500
MAX_INPUT_TOKENS = 750000 
SAFE_CHAR_LIMIT = MAX_INPUT_TOKENS * 4
SAFETY_SETTINGS = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]

# NEW: Mapping from instruction type to filename using shared constants
PROMPT_FILENAMES = {
    constants.PROMPT_TYPE_NARRATIVE: constants.FILENAME_NARRATIVE,
    constants.PROMPT_TYPE_MECHANICS: constants.FILENAME_MECHANICS,
    constants.PROMPT_TYPE_CALIBRATION: constants.FILENAME_CALIBRATION,
    constants.PROMPT_TYPE_DESTINY: constants.FILENAME_DESTINY,
    constants.PROMPT_TYPE_GAME_STATE: constants.FILENAME_GAME_STATE,
    constants.PROMPT_TYPE_SRD: constants.FILENAME_SRD,
}
# --- END CONSTANTS ---

_client = None

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache = {} 

def _load_instruction_file(instruction_type):
    """
    Loads a prompt instruction file from the 'prompts' directory.
    This function is now strict: it will raise an exception if a file
    cannot be found, ensuring the application does not continue with
    incomplete instructions.
    """
    # This mapping allows us to use short, simple constants in the code
    # while still loading the descriptively named files.
    filename_map = {
        constants.PROMPT_TYPE_NARRATIVE: "narrative_system_instruction.md",
        constants.PROMPT_TYPE_MECHANICS: "mechanics_system_instruction.md",
        constants.PROMPT_TYPE_CALIBRATION: "calibration_instruction.md",
        constants.PROMPT_TYPE_DESTINY: "destiny_ruleset.md",
        constants.PROMPT_TYPE_GAME_STATE: "game_state_instruction.md",
        constants.PROMPT_TYPE_SRD: "5e_SRD_All.md",
        constants.PROMPT_TYPE_CHARACTER_TEMPLATE: "character_template.md",
    }

    global _loaded_instructions_cache
    if instruction_type not in _loaded_instructions_cache:
        file_name = filename_map.get(instruction_type)
        
        if not file_name:
            logging.error(f"FATAL: Unknown instruction type requested: {instruction_type}")
            raise ValueError(f"Unknown instruction type requested: {instruction_type}")

        file_path = os.path.join(os.path.dirname(__file__), 'prompts', file_name)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            logging.info(f"Loaded {instruction_type} instruction from {file_path}")
            _loaded_instructions_cache[instruction_type] = content
        except FileNotFoundError:
            logging.error(f"CRITICAL: System instruction file not found: {file_path}. This is a fatal error for this request.")
            raise
        except Exception as e:
            logging.error(f"CRITICAL: Error loading system instruction file {file_path}: {e}")
            raise
        
    return _loaded_instructions_cache[instruction_type]


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

def _call_gemini_api(prompt_contents, model_name, current_prompt_text_for_logging=None, system_instruction_text=None):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    if current_prompt_text_for_logging:
        logging.info(f"--- Calling Gemini API with current prompt: {str(current_prompt_text_for_logging)[:1000]}... ---")
    logging.info(f"--- Calling Gemini API with full prompt: {str(prompt_contents)[:1000]}... ---")
    
    generation_config_params = {
        "max_output_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "safety_settings": SAFETY_SETTINGS
    }
    if system_instruction_text:
        generation_config_params["system_instruction"] = types.Part(text=system_instruction_text)

    response = client.models.generate_content(
        model=model_name,
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
def get_initial_story(prompt, selected_prompts=None, include_srd=False):
    """Generates the initial story part, including character, narrative, and mechanics instructions."""

    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for initial story. Using none.")

    system_instruction_parts = []

    # Conditionally add the character template if narrative instructions are selected.
    if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE))

    # Load calibration instructions
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CALIBRATION))

    # Conditionally add the SRD
    if include_srd:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_SRD))

    # Consistent order for instructions
    # Narrative, Mechanics, Calibration (from checkboxes)
    for p_type in [constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS, constants.PROMPT_TYPE_CALIBRATION]: 
        if p_type in selected_prompts:
            system_instruction_parts.append(_load_instruction_file(p_type))
    
    # NEW: Always include the destiny_ruleset as a default system instruction
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DESTINY))

    # NEW: Always include the game_state instructions
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

    system_instruction_final = "\n\n".join(system_instruction_parts)
    
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    
    # --- DYNAMIC MODEL SELECTION ---
    # Use the more powerful model at the beginning of the game.
    model_to_use = LARGE_CONTEXT_MODEL
    logging.info(f"Using model: {model_to_use} for initial story generation.")

    response = _call_gemini_api(contents, model_to_use, current_prompt_text_for_logging=prompt, system_instruction_text=system_instruction_final)
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context, current_game_state: GameState, selected_prompts=None):
    """Generates the next part of the story, incorporating game state and selected system instructions."""
    
    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for continue_story. Using none.")

    system_instruction_parts = []

    # Conditionally add the character template if narrative instructions are selected.
    if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE))

    # Filter out 'calibration' for continue_story calls
    # NEW: Also ensure consistent order for continue_story
    filtered_prompts = [p_type for p_type in selected_prompts if p_type in [constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS]]

    # Load content for narrative and mechanics
    for p_type in filtered_prompts: 
        system_instruction_parts.append(_load_instruction_file(p_type))
    
    # NEW: Always include the destiny_ruleset for continue_story too
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DESTINY))

    # NEW: Always include the game_state instructions
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))

    system_instruction_final = "\n\n".join(system_instruction_parts)

    recent_context = _truncate_context(story_context)
    
    # Build a timeline log and a simple list of sequence IDs
    timeline_log_parts = []
    sequence_ids = []
    for entry in recent_context:
        actor_label = "Story" if entry.get('actor') == 'gemini' else "You"
        seq_id = entry.get('sequence_id', 'N/A')
        sequence_ids.append(str(seq_id))
        timeline_log_parts.append(f"[SEQ_ID: {seq_id}] {actor_label}: {entry.get('text')}")
    
    timeline_log_string = "\n\n".join(timeline_log_parts)
    sequence_id_list_string = ", ".join(sequence_ids)

    # --- NEW: System-Generated Checkpoint Block ---
    # This is the single source of truth for the character's immediate status.
    latest_seq_id = sequence_ids[-1] if sequence_ids else 'N/A'
    current_location = current_game_state.world_data.get('current_location_name', 'Unknown')
    
    pc_data = current_game_state.player_character_data
    key_stats_parts = [
        f"XP {pc_data.get('experience', 0)}/{pc_data.get('experience_to_next_level', 'N/A')}",
        f"HP: {pc_data.get('hp_current', 'N/A')}/{pc_data.get('hp_max', 'N/A')}",
        f"Gold: {pc_data.get('gold', 0)} GP"
    ]
    key_stats_summary = " | ".join(key_stats_parts)

    active_missions = current_game_state.custom_campaign_state.get('active_missions', [])
    missions_summary = "Missions: " + (", ".join(active_missions) if active_missions else "None")

    checkpoint_block = (
        f"[CHECKPOINT BLOCK:]\\n"
        f"Sequence ID: {latest_seq_id} | Location: {current_location}\\n"
        f"Key Stats: {key_stats_summary}\\n"
        f"{missions_summary}"
    )

    # Create the final prompt for the current user turn (User's preferred method)
    if mode == 'character':
        prompt_template = "Main character: {user_input}. Continue the story in about {word_count} words and " \
            "add details for narrative, descriptions of scenes, character dialog, character emotions."
        current_prompt_text = prompt_template.format(user_input=user_input, word_count=TARGET_WORD_COUNT)
    else: # god mode
        prompt_template = "GOD MODE: {user_input}"
        current_prompt_text = prompt_template.format(user_input=user_input)

    # --- NEW: Incorporate Game State & Timeline ---
    serialized_game_state = json.dumps(current_game_state.to_dict(), indent=2, default=json_datetime_serializer)
    full_prompt = (
        f"{checkpoint_block}\\n\\n"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{sequence_id_list_string}]\\n\\n"
        f"CURRENT GAME STATE:\\n{serialized_game_state}\\n\\n"
        f"TIMELINE LOG (FOR CONTEXT):\\n{timeline_log_string}\\n\\n"
        f"YOUR TURN:\\n{current_prompt_text}"
    )
    
    # For all subsequent calls, use the standard, cheaper model.
    response = _call_gemini_api([full_prompt], DEFAULT_MODEL, current_prompt_text_for_logging=current_prompt_text, system_instruction_text=system_instruction_final) 
    return _get_text_from_response(response)

def create_game_state_from_legacy_story(story_context: list) -> GameState | None:
    """
    Parses a legacy story entry to create a GameState object.
    Returns a GameState object if a legacy block is found and parsed, otherwise None.
    """
    logging.info("Attempting to find and parse legacy game state from story context...")
    
    # Limit the search to the last 20 entries for efficiency.
    search_context = story_context[-20:]

    # Iterate backwards to find the most recent state block
    for entry in reversed(search_context):
        text = entry.get('text', '')
        if text.strip().startswith('[Mode: STORY MODE]'):
            logging.info("Found a potential legacy game state block. Parsing...")
            
            # --- Helper function for parsing numeric values ---
            def get_stat(pattern, text, is_float=False):
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val_str = match.group(1).replace(',', '')
                    try:
                        return float(val_str) if is_float else int(val_str)
                    except (ValueError, TypeError):
                        return None
                return None

            # --- Helper for parsing mission lists ---
            def parse_missions(text_block):
                missions = []
                lines = text_block.strip().split('\\n')
                for line in lines:
                    match = re.search(r'^\s*\*\s+(.*)', line)
                    if match:
                        missions.append(match.group(1).strip())
                return missions

            # --- Extract data using regex ---
            location_match = re.search(r'Location:\s*(.*)', text, re.IGNORECASE)
            location = location_match.group(1).strip() if location_match else "Unknown"

            followers = get_stat(r'Followers:\s*(\d+)', text)
            gold = get_stat(r'Gold:\s*([\d,]+)\s*GP', text)
            gold_per_day = get_stat(r'Gold/day:\s*([\d,]+)\s*GP', text)
            experience = get_stat(r'Experience:\s*([\d,.]+)', text, is_float=True)
            exp_to_next = get_stat(r'Experience to next level:\s*([\d,.]+)\s*XP', text, is_float=True)

            active_missions_match = re.search(r'Active Missions:(.*?)(?=\*   Completed Missions:|$)', text, re.DOTALL | re.IGNORECASE)
            completed_missions_match = re.search(r'Completed Missions:(.*)', text, re.DOTALL | re.IGNORECASE)

            active_missions = parse_missions(active_missions_match.group(1)) if active_missions_match else []
            completed_missions = parse_missions(completed_missions_match.group(1)) if completed_missions_match else []

            # --- Assemble the GameState object ---
            player_character_data = {
                "followers": followers,
                "gold": gold,
                "gold_per_day": gold_per_day,
                "experience": experience,
                "experience_to_next_level": exp_to_next
            }
            world_data = {
                "current_location": location
            }
            custom_campaign_state = {
                "active_missions": active_missions,
                "completed_missions": completed_missions
            }
            
            logging.info(f"Successfully parsed legacy state. Location: {location}, Gold: {gold}")
            return GameState(
                player_character_data=player_character_data,
                world_data=world_data,
                npc_data={}, # No NPC data in legacy format
                custom_campaign_state=custom_campaign_state
            )

    logging.warning("No legacy game state block found in story context.")
    return None

@log_exceptions
def parse_llm_response_for_state_changes(llm_text_response: str) -> dict:
    """
    Parses the raw text response from the LLM to find and extract a
    JSON block containing proposed state changes.
    """
    # Regex to find the content between the delimiters, capturing the JSON inside.
    # re.DOTALL (s) flag allows '.' to match newlines.
    match = re.search(r'\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]', llm_text_response, re.DOTALL)
    
    if not match:
        return {}

    json_string = match.group(1).strip()
    
    try:
        proposed_changes = json.loads(json_string)
        if isinstance(proposed_changes, dict):
            return proposed_changes
        else:
            logging.warning(f"Parsed state changes is not a dictionary: {proposed_changes}")
            return {}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON from state update block: {e}")
        logging.error(f"Invalid JSON string was: {json_string}")
        return {}

# --- Main block for rapid, direct testing ---
if __name__ == "__main__":
    print("--- Running gemini_service.py in chained conversation test mode ---")
    
    try:
        with open('local_api_key.txt', 'r') as f:
            api_key = f.read().strip()
        os.environ["GEMINI_API_KEY"] = api_key
        print("Successfully loaded API key from local_api_key.txt")
    except FileNotFoundError:
        print("\nERROR: 'local_api_key.txt' not found.")
        sys.exit(1)
        
    get_client() # Initialize client
    
    # Example usage for testing: pass all prompt types
    test_selected_prompts = ['narrative', 'mechanics', 'calibration']
    test_game_state = GameState(
        player_character_data={"name": "Test Character", "hp_current": 10},
        world_data={"current_location_name": "The Testing Grounds"},
        npc_data={},
        custom_campaign_state={}
    )

    # --- Turn 1: Initial Story ---
    print("\n--- Turn 1: get_initial_story ---")
    turn_1_prompt = "start a story about a haunted lighthouse"
    print(f"Using prompt: '{turn_1_prompt}' with selected prompts: {test_selected_prompts}")
    turn_1_response = get_initial_story(turn_1_prompt, selected_prompts=test_selected_prompts)
    print("\n--- LIVE RESPONSE 1 ---")
    print(turn_1_response)
    print("--- END OF RESPONSE 1 ---\n")
    
    # Create the initial history from the real response
    history = [{'actor': 'user', 'text': turn_1_prompt}, {'actor': 'gemini', 'text': turn_1_response}]

    # --- Turn 2: Continue Story ---
    print("\n--- Turn 2: continue_story ---")
    turn_2_prompt = "A lone ship, tossed by the raging sea, sees a faint, flickering light from the abandoned tower."
    print(f"Using prompt: '{turn_2_prompt}'")
    turn_2_response = continue_story(turn_2_prompt, 'god', history, test_game_state, selected_prompts=test_selected_prompts)
    print("\n--- LIVE RESPONSE 2 ---")
    print(turn_2_response)
    print("--- END OF RESPONSE 2 ---\n")
    
    # Update the history with the real response from turn 2
    history.append({'actor': 'user', 'text': turn_2_prompt})
    history.append({'actor': 'gemini', 'text': turn_2_response})

    # --- Turn 3: Continue Story Again ---
    print("\n--- Turn 3: continue_story ---")
    turn_3_prompt = "The ship's captain, a grizzled old sailor named Silas, decides to steer towards the light, ignoring the warnings of his crew."
    print(f"Using prompt: '{turn_3_prompt}'")
    turn_3_response = continue_story(turn_3_prompt, 'god', history, test_game_state, selected_prompts=test_selected_prompts)
    print("\n--- LIVE RESPONSE 3 ---")
    print(turn_3_response)
    print("--- END OF RESPONSE 3 ---\n")
