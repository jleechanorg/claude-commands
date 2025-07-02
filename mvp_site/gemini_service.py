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
from entity_tracking import SceneManifest, create_from_game_state
from narrative_sync_validator import NarrativeSyncValidator
from narrative_response_schema import (
    create_structured_prompt_injection, 
    parse_structured_response,
    validate_entity_coverage,
    NarrativeResponse
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def json_datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# --- CONSTANTS ---
# Use flash for standard, cheaper operations.
DEFAULT_MODEL = 'gemini-2.5-flash'
# Use pro for large-context operations.
LARGE_CONTEXT_MODEL = 'gemini-2.5-pro'
# Use 1.5 flash for testing as requested
TEST_MODEL = 'gemini-1.5-flash'

# Use pro model for first 5 user inputs for higher quality world building
USE_PRO_MODEL_FOR_FIRST_N_INPUTS = 5

MAX_TOKENS = 50000 
TEMPERATURE = 0.9
TARGET_WORD_COUNT = 300
MAX_INPUT_TOKENS = 750000 
SAFE_CHAR_LIMIT = MAX_INPUT_TOKENS * 4

TURNS_TO_KEEP_AT_START = 25
TURNS_TO_KEEP_AT_END = 75

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
    constants.PROMPT_TYPE_ENTITY_SCHEMA: constants.FILENAME_ENTITY_SCHEMA,
}

# NEW: Centralized map of prompt types to their file paths.
# This is now the single source of truth for locating prompt files.
PATH_MAP = {
    constants.PROMPT_TYPE_NARRATIVE: constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_MECHANICS: constants.MECHANICS_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_CALIBRATION: constants.CALIBRATION_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_DESTINY: constants.DESTINY_RULESET_PATH,
    constants.PROMPT_TYPE_GAME_STATE: constants.GAME_STATE_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_CHARACTER_TEMPLATE: constants.CHARACTER_TEMPLATE_PATH,
    constants.PROMPT_TYPE_CHARACTER_SHEET: constants.CHARACTER_SHEET_TEMPLATE_PATH,
    constants.PROMPT_TYPE_ENTITY_SCHEMA: constants.ENTITY_SCHEMA_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_DUAL_SYSTEM_REFERENCE: constants.DUAL_SYSTEM_REFERENCE_PATH,
    constants.PROMPT_TYPE_MASTER_DIRECTIVE: constants.MASTER_DIRECTIVE_PATH,
    constants.PROMPT_TYPE_ATTRIBUTE_CONVERSION: constants.ATTRIBUTE_CONVERSION_PATH,
}

# --- END CONSTANTS ---

_client = None

# Store loaded instruction content in a dictionary for easy access
_loaded_instructions_cache = {} 

def _clear_client():
    """FOR TESTING ONLY: Clears the cached Gemini client."""
    global _client
    _client = None

def _load_instruction_file(instruction_type):
    """
    Loads a prompt instruction file from the 'prompts' directory.
    This function is now strict: it will raise an exception if a file
    cannot be found, ensuring the application does not continue with
    incomplete instructions.
    """
    global _loaded_instructions_cache
    if instruction_type not in _loaded_instructions_cache:
        relative_path = PATH_MAP.get(instruction_type)
        
        if not relative_path:
            logging.error(f"FATAL: Unknown instruction type requested: {instruction_type}")
            raise ValueError(f"Unknown instruction type requested: {instruction_type}")

        file_path = os.path.join(os.path.dirname(__file__), relative_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            # logging.info(f'Loaded prompt "{instruction_type}" from file: {os.path.basename(file_path)}')
            _loaded_instructions_cache[instruction_type] = content
        except FileNotFoundError:
            logging.error(f"CRITICAL: System instruction file not found: {file_path}. This is a fatal error for this request.")
            raise
        except Exception as e:
            logging.error(f"CRITICAL: Error loading system instruction file {file_path}: {e}")
            raise
    else:
        pass
        #logging.info(f'Loaded prompt "{instruction_type}" from cache.')
        
    return _loaded_instructions_cache[instruction_type]


def get_client():
    """Initializes and returns a singleton Gemini client."""
    global _client
    # FOR DEBUGGING: Always re-initialize to pick up new keys from env.
    # if _client is None:
    logging.info("--- Initializing Gemini Client ---")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
    _client = genai.Client(api_key=api_key)
    logging.info("--- Gemini Client Initialized Successfully ---")
    return _client

def _add_world_instructions_to_system(system_instruction_parts):
    """
    Add world content instructions to system instruction parts if world is enabled.
    Avoids code duplication between get_initial_story and continue_story.
    """
    from world_loader import load_world_content_for_system_instruction
    
    world_instruction = (
        "\n**CRITICAL INSTRUCTION: USE ESTABLISHED WORLD LORE**\n"
        "This campaign MUST use the Celestial Wars/Assiah world setting provided below. "
        "DO NOT create new factions, characters, or locations - USE the established ones from the world content. "
        "ACTIVELY reference characters, factions, and locations from the provided lore. "
        "The Celestial Wars Alexiel Book takes precedence over World of Assiah documentation for conflicts. "
        "When introducing NPCs or factions, draw from the established character dossiers and faction information. "
        "DO NOT invent generic fantasy elements when rich, detailed lore is provided.\n\n"
    )
    system_instruction_parts.append(world_instruction)
    
    # Load world content directly into system instruction
    world_content = load_world_content_for_system_instruction()
    system_instruction_parts.append(world_content)

def _log_token_count(model_name, user_prompt_contents, system_instruction_text=None):
    """Helper function to count and log the number of tokens being sent, with a breakdown."""
    try:
        client = get_client()
        
        # Count user prompt tokens
        user_prompt_tokens = client.models.count_tokens(model=model_name, contents=user_prompt_contents).total_tokens
        
        # Count system instruction tokens if they exist
        system_tokens = 0
        if system_instruction_text:
            # The system instruction is a single string, so it needs to be wrapped in a list for the API
            system_tokens = client.models.count_tokens(model=model_name, contents=[system_instruction_text]).total_tokens

        total_tokens = user_prompt_tokens + system_tokens
        logging.info(f"--- Sending {total_tokens} tokens to the API. (Prompt: {user_prompt_tokens}, System: {system_tokens}) ---")

    except Exception as e:
        logging.warning(f"Could not count tokens before API call: {e}")

def _call_gemini_api(prompt_contents, model_name, current_prompt_text_for_logging=None, system_instruction_text=None, use_json_mode=False):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    # Pass the system instruction text to the token logger
    _log_token_count(model_name, prompt_contents, system_instruction_text)

    if current_prompt_text_for_logging:
        logging.info(f"--- Calling Gemini API with current prompt: {str(current_prompt_text_for_logging)[:1000]}... ---")

    # The character count log is less useful now, but we'll keep it for now.
    total_chars = sum(len(p) for p in prompt_contents if isinstance(p, str))
    if system_instruction_text:
        total_chars += len(system_instruction_text)
    logging.info(f"--- Calling Gemini API with prompt of total characters: {total_chars} ---")

    generation_config_params = {
        "max_output_tokens": MAX_TOKENS,
        "temperature": TEMPERATURE,
        "safety_settings": SAFETY_SETTINGS
    }
    
    # Configure JSON response mode if requested
    if use_json_mode:
        generation_config_params["response_mime_type"] = "application/json"
        logging.info("--- Using JSON response mode for structured generation ---")
    
    # Pass the system instruction to the generate_content call
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

def _get_context_stats(context, model_name, current_game_state: GameState):
    """Helper to calculate and format statistics for a given story context."""
    if not context:
        return "Turns: 0, Chars: 0, Words: 0, Tokens: 0"
    
    chars = sum(len(entry.get(constants.KEY_TEXT, '')) for entry in context)
    words = sum(len(entry.get(constants.KEY_TEXT, '').split()) for entry in context)
    
    # Token counting is an API call, so wrap it in a try-except
    tokens = "N/A"
    try:
        client = get_client()
        # To count tokens, we create a temporary list of content parts
        parts = [types.Part(text=entry.get(constants.KEY_TEXT, '')) for entry in context]
        count_response = client.models.count_tokens(model=model_name, contents=parts)
        tokens = count_response.total_tokens
    except Exception as e:
        logging.warning(f"Could not count tokens for context stats: {e}")
        
    all_core_memories = current_game_state.custom_campaign_state.get('core_memories', [])
    stats_string = f"Turns: {len(context)}, Chars: {chars}, Words: {words}, Tokens: {tokens}, Core Memories: {len(all_core_memories)}"

    if all_core_memories:
        last_three = all_core_memories[-3:]
        stats_string += "\\n--- Last 3 Core Memories ---\\n"
        for i, memory in enumerate(last_three, 1):
            stats_string += f"  {len(all_core_memories) - len(last_three) + i}: {memory}\\n"
        stats_string += "--------------------------"

    return stats_string


def _truncate_context(story_context, max_chars: int, model_name: str, current_game_state: GameState, turns_to_keep_at_start=TURNS_TO_KEEP_AT_START, turns_to_keep_at_end=TURNS_TO_KEEP_AT_END):
    """
    Intelligently truncates the story context to fit within a given character budget.
    """
    initial_stats = _get_context_stats(story_context, model_name, current_game_state)
    logging.info(f"Initial context stats: {initial_stats}")

    current_chars = sum(len(entry.get(constants.KEY_TEXT, '')) for entry in story_context)

    if current_chars <= max_chars:
        logging.info("Context is within character budget. No truncation needed.")
        return story_context

    logging.warning(
        f"Context ({current_chars} chars) exceeds budget of {max_chars} chars. Truncating..."
    )

    total_turns = len(story_context)
    if total_turns <= turns_to_keep_at_start + turns_to_keep_at_end:
         # If we're over budget but have few turns, just take the most recent ones.
        return story_context[-(turns_to_keep_at_start + turns_to_keep_at_end):]

    start_context = story_context[:turns_to_keep_at_start]
    end_context = story_context[-turns_to_keep_at_end:]
    
    truncation_marker = {
        "actor": "system",
        "text": "[...several moments, scenes, or days have passed...]\\n[...the story continues from the most recent relevant events...]"
    }
    
    truncated_context = start_context + [truncation_marker] + end_context
    
    final_stats = _get_context_stats(truncated_context, model_name, current_game_state)
    logging.info(f"Final context stats after truncation: {final_stats}")
    
    return truncated_context

@log_exceptions
def get_initial_story(prompt, selected_prompts=None, generate_companions=False, use_default_world=False):
    """Generates the initial story part, including character, narrative, and mechanics instructions."""

    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for initial story. Using none.")

    system_instruction_parts = []

    # CRITICAL: Load master directive FIRST for highest priority
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

    # CRITICAL: Load game_state instructions SECOND for highest priority
    # This prevents "instruction fatigue" and ensures data structure compliance
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))
    
    # Load entity schema instructions for proper entity management
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_ENTITY_SCHEMA))

    # Conditionally add the character template if narrative instructions are selected.
    if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE))

    # Conditionally add the character sheet if mechanics instructions are selected.
    if constants.PROMPT_TYPE_MECHANICS in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_SHEET))


    # Consistent order for instructions
    # Narrative, Mechanics, Calibration (from checkboxes)
    for p_type in [constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS, constants.PROMPT_TYPE_CALIBRATION]: 
        if p_type in selected_prompts:
            system_instruction_parts.append(_load_instruction_file(p_type))
    
    # NEW: Always include the destiny_ruleset as a default system instruction
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DESTINY))
    
    # Add dual system reference for attribute system guidance
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DUAL_SYSTEM_REFERENCE))
    
    # Add attribute conversion guide for system switching
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_ATTRIBUTE_CONVERSION))

    # Add companion generation instruction if requested
    if generate_companions:
        companion_instruction = (
            "\n**SPECIAL INSTRUCTION: COMPANION GENERATION ACTIVATED**\n"
            "You have been specifically requested to generate 3 starting companions for this campaign. "
            "Follow Part 7: Companion Generation Protocol from the narrative instructions. "
            "In your opening narrative, introduce all 3 companions and include them in the initial STATE_UPDATES_PROPOSED block.\n\n"
        )
        system_instruction_parts.append(companion_instruction)

    # Add background summary instruction for initial story
    background_summary_instruction = (
        "\n**CRITICAL INSTRUCTION: START WITH BACKGROUND SUMMARY**\n"
        "Before beginning the actual narrative, you MUST provide a background summary section that orients the player. "
        "This should be 2-4 paragraphs covering:\n"
        "1. **World Background:** A brief overview of the setting, key factions, current political situation, and important world elements (without major spoilers)\n"
        "2. **Character History:** Who the character is, their background, motivations, and current situation (based on the prompt provided)\n"
        "3. **Current Context:** What brings them to this moment and why their story is beginning now\n\n"
        "**Requirements:**\n"
        "- Keep it concise but informative (2-4 paragraphs total)\n"
        "- NO future plot spoilers or major story reveals\n"
        "- Focus on established facts the character would know\n"
        "- End with a transition into the opening scene\n"
        "- Use a clear header like '**--- BACKGROUND ---**' to separate this from the main narrative\n\n"
        "After the background summary, proceed with the normal opening scene and narrative.\n\n"
    )
    system_instruction_parts.append(background_summary_instruction)

    # Add world instructions if requested
    if use_default_world:
        _add_world_instructions_to_system(system_instruction_parts)

    # ALWAYS add debug mode instructions for AI context and state management
    # The backend will strip debug content for users when debug_mode is False
    debug_instruction = (
        "\n**DEBUG MODE - ALWAYS GENERATE**\n"
        "You must ALWAYS include the following debug information in your response for game state management:\n"
        "\n"
        "1. **DM COMMENTARY**: Wrap any behind-the-scenes DM thoughts, rule considerations, or meta-game commentary in [DEBUG_START] and [DEBUG_END] tags.\n"
        "\n"
        "2. **DICE ROLLS**: Show ALL dice rolls throughout your response:\n"
        "   - **During Narrative**: Show important rolls (skill checks, saving throws, random events) using [DEBUG_ROLL_START] and [DEBUG_ROLL_END] tags\n"
        "   - **During Combat**: Show ALL combat rolls including attack rolls, damage rolls, initiative, saving throws, and any other dice mechanics\n"
        "   - Format: [DEBUG_ROLL_START]Rolling Perception check: 1d20+3 = 15+3 = 18 (Success)[DEBUG_ROLL_END]\n"
        "   - Include both the dice result and the final total with modifiers\n"
        "\n"
        "3. **RESOURCES USED**: Track resources expended during the scene:\n"
        "   - Format: [DEBUG_RESOURCES_START]Resources: 2 EP used (6/8 remaining), 1 spell slot level 2 (2/3 remaining), short rests: 1/2[DEBUG_RESOURCES_END]\n"
        "   - Include: Effort Points (EP), spell slots by level, short rests, long rests, hit dice, consumables\n"
        "   - Show both used and remaining for each resource\n"
        "\n"
        "4. **STATE CHANGES**: After your main narrative, include a section wrapped in [DEBUG_STATE_START] and [DEBUG_STATE_END] tags that explains what state changes you're proposing and why.\n"
        "\n"
        "**Examples:**\n"
        "- [DEBUG_START]The player is attempting a stealth approach, so I need to roll for the guards' perception...[DEBUG_END]\n"
        "- [DEBUG_ROLL_START]Guard Perception: 1d20+2 = 12+2 = 14 vs DC 15 (Failure - guards don't notice)[DEBUG_ROLL_END]\n"
        "- [DEBUG_RESOURCES_START]Resources: 0 EP used (8/8 remaining), no spell slots used, short rests: 2/2[DEBUG_RESOURCES_END]\n"
        "- [DEBUG_STATE_START]Updating player position to 'hidden behind crates' and setting guard alertness to 'unaware'[DEBUG_STATE_END]\n"
        "\n"
        "NOTE: This debug information helps maintain game state consistency and will be conditionally shown to players based on their debug mode setting.\n\n"
    )
    system_instruction_parts.append(debug_instruction)

    system_instruction_final = "\n\n".join(system_instruction_parts)
    
    # Add clear indication when using default world setting
    if use_default_world:
        prompt = f"Use default setting Assiah. {prompt}"
    
    contents = [types.Content(role="user", parts=[types.Part(text=prompt)])]
    
    # --- DYNAMIC MODEL SELECTION ---
    # Use the more powerful model at the beginning of the game.
    model_to_use = TEST_MODEL if os.environ.get('TESTING') else LARGE_CONTEXT_MODEL
    logging.info(f"Using model: {model_to_use} for initial story generation.")

    response = _call_gemini_api(contents, model_to_use, current_prompt_text_for_logging=prompt, system_instruction_text=system_instruction_final)
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context, current_game_state: GameState, selected_prompts=None, use_default_world=False):
    """
    Continues the story by calling the Gemini API with the current context and game state.
    
    Args:
        user_input: The user's input text
        mode: The interaction mode (e.g., 'character', 'story')
        story_context: List of previous story entries
        current_game_state: Current GameState object
        selected_prompts: List of selected prompt types
        use_default_world: Whether to include world content in system instructions
        
    Returns:
        The AI's response text
    """
    
    # Calculate user input count for model selection (count existing user entries + current input)
    user_input_count = len([entry for entry in (story_context or []) if entry.get(constants.KEY_ACTOR) == constants.ACTOR_USER]) + 1
    
    # --- NEW: Validate checkpoint consistency before generating response ---
    if story_context:
        # Get the most recent AI response to validate against current state
        recent_ai_responses = [entry.get(constants.KEY_TEXT, '') for entry in story_context[-3:] 
                             if entry.get(constants.KEY_ACTOR) == constants.ACTOR_GEMINI]
        if recent_ai_responses:
            latest_narrative = recent_ai_responses[-1]
            discrepancies = current_game_state.validate_checkpoint_consistency(latest_narrative)
            
            if discrepancies:
                logging.warning(f"CHECKPOINT_VALIDATION: Found {len(discrepancies)} potential discrepancies:")
                for i, discrepancy in enumerate(discrepancies, 1):
                    logging.warning(f"  {i}. {discrepancy}")
                
                # Add validation prompt to ensure AI addresses inconsistencies
                validation_instruction = (
                    "IMPORTANT: State validation detected potential inconsistencies between the game state "
                    "and recent narrative. Please ensure your response maintains strict consistency with the "
                    "CURRENT GAME STATE data, especially regarding character health, location, and mission status."
                )
                user_input = f"{validation_instruction}\n\n{user_input}"
    
    if selected_prompts is None:
        selected_prompts = [] 
        logging.warning("No specific system prompts selected for continue_story. Using none.")


    system_instruction_parts = []

    # CRITICAL: Load master directive FIRST for highest priority
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))

    # CRITICAL: Load game_state instructions SECOND for highest priority
    # This prevents "instruction fatigue" and ensures data structure compliance
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))
    
    # Load entity schema instructions for proper entity management
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_ENTITY_SCHEMA))

    # Conditionally add the character template if narrative instructions are selected.
    if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE))

    # Conditionally add the character sheet if mechanics instructions are selected.
    if constants.PROMPT_TYPE_MECHANICS in selected_prompts:
        system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_SHEET))

    # Load destiny ruleset EARLY (position 4) for system rules foundation
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DESTINY))

    # Filter out 'calibration' for continue_story calls
    # Calibration is only for initial campaign setup, not ongoing story
    selected_prompts_filtered = [p_type for p_type in selected_prompts if p_type != constants.PROMPT_TYPE_CALIBRATION]
    
    # Load user-selected prompts (excluding calibration)
    for p_type in selected_prompts_filtered:
        system_instruction_parts.append(_load_instruction_file(p_type))
    
    # Add dual system reference for attribute system guidance
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_DUAL_SYSTEM_REFERENCE))
    
    # Add attribute conversion guide for system switching
    system_instruction_parts.append(_load_instruction_file(constants.PROMPT_TYPE_ATTRIBUTE_CONVERSION))

    # Add world instructions if campaign was created with default world enabled
    if use_default_world:
        _add_world_instructions_to_system(system_instruction_parts)
    
    # ALWAYS add debug mode instructions for AI context and state management
    # The backend will strip debug content for users when debug_mode is False
    debug_instruction = (
        "\n**DEBUG MODE - ALWAYS GENERATE**\n"
        "You must ALWAYS include the following debug information in your response for game state management:\n"
        "\n"
        "1. **DM COMMENTARY**: Wrap any behind-the-scenes DM thoughts, rule considerations, or meta-game commentary in [DEBUG_START] and [DEBUG_END] tags.\n"
        "\n"
        "2. **DICE ROLLS**: Show ALL dice rolls throughout your response:\n"
        "   - **During Narrative**: Show important rolls (skill checks, saving throws, random events) using [DEBUG_ROLL_START] and [DEBUG_ROLL_END] tags\n"
        "   - **During Combat**: Show ALL combat rolls including attack rolls, damage rolls, initiative, saving throws, and any other dice mechanics\n"
        "   - Format: [DEBUG_ROLL_START]Rolling Perception check: 1d20+3 = 15+3 = 18 (Success)[DEBUG_ROLL_END]\n"
        "   - Include both the dice result and the final total with modifiers\n"
        "\n"
        "3. **RESOURCES USED**: Track resources expended during the scene:\n"
        "   - Format: [DEBUG_RESOURCES_START]Resources: 2 EP used (6/8 remaining), 1 spell slot level 2 (2/3 remaining), short rests: 1/2[DEBUG_RESOURCES_END]\n"
        "   - Include: Effort Points (EP), spell slots by level, short rests, long rests, hit dice, consumables\n"
        "   - Show both used and remaining for each resource\n"
        "\n"
        "4. **STATE CHANGES**: After your main narrative, include a section wrapped in [DEBUG_STATE_START] and [DEBUG_STATE_END] tags that explains what state changes you're proposing and why.\n"
        "\n"
        "**Examples:**\n"
        "- [DEBUG_START]The player is attempting a stealth approach, so I need to roll for the guards' perception...[DEBUG_END]\n"
        "- [DEBUG_ROLL_START]Guard Perception: 1d20+2 = 12+2 = 14 vs DC 15 (Failure - guards don't notice)[DEBUG_ROLL_END]\n"
        "- [DEBUG_RESOURCES_START]Resources: 0 EP used (8/8 remaining), no spell slots used, short rests: 2/2[DEBUG_RESOURCES_END]\n"
        "- [DEBUG_STATE_START]Updating player position to 'hidden behind crates' and setting guard alertness to 'unaware'[DEBUG_STATE_END]\n"
        "\n"
        "NOTE: This debug information helps maintain game state consistency and will be conditionally shown to players based on their debug mode setting.\n\n"
    )
    system_instruction_parts.append(debug_instruction)

    system_instruction_final = "\n\n".join(system_instruction_parts)

    # --- NEW: Budget-based Truncation ---
    # 1. Calculate the size of the "prompt scaffold" (everything except the timeline log)
    serialized_game_state = json.dumps(current_game_state.to_dict(), indent=2, default=json_datetime_serializer)
    
    # Temporarily generate other prompt parts to measure them.
    # We will generate them again *after* truncation with the final context.
    temp_checkpoint_block, temp_core_memories, temp_seq_ids = _get_static_prompt_parts(current_game_state, [])

    prompt_scaffold = (
        f"{temp_checkpoint_block}\\n\\n"
        f"{temp_core_memories}"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{temp_seq_ids}]\\n\\n"
    )
    
    # Calculate the character budget for the story context
    char_budget_for_story = SAFE_CHAR_LIMIT - len(prompt_scaffold)
    logging.info(f"Prompt scaffold is {len(prompt_scaffold)} chars. Remaining budget for story: {char_budget_for_story}")

    # Truncate the story context if it exceeds the budget
    truncated_story_context = _truncate_context(story_context, char_budget_for_story, DEFAULT_MODEL, current_game_state)

    # Now that we have the final, truncated context, we can generate the real prompt parts.
    checkpoint_block, core_memories_summary, sequence_id_list_string = _get_static_prompt_parts(current_game_state, truncated_story_context)
    
    # Serialize the game state for inclusion in the prompt
    serialized_game_state = json.dumps(current_game_state.to_dict(), indent=2, default=json_datetime_serializer)
    
    # --- ENTITY TRACKING: Create scene manifest for entity tracking ---
    # Extract session and turn numbers from game state
    session_number = current_game_state.custom_campaign_state.get('session_number', 1)
    turn_number = len(truncated_story_context) + 1  # Approximate turn count
    
    # Create entity manifest from current game state (with basic caching)
    game_state_dict = current_game_state.to_dict()
    manifest_cache_key = f"manifest_{session_number}_{turn_number}_{hash(str(sorted(game_state_dict.get('npc_data', {}).items())))}"
    
    # Simple in-memory cache for the request duration
    if not hasattr(current_game_state, '_manifest_cache'):
        current_game_state._manifest_cache = {}
    
    if manifest_cache_key in current_game_state._manifest_cache:
        entity_manifest = current_game_state._manifest_cache[manifest_cache_key]
        logging.debug("Using cached entity manifest")
    else:
        entity_manifest = create_from_game_state(game_state_dict, session_number, turn_number)
        current_game_state._manifest_cache[manifest_cache_key] = entity_manifest
        logging.debug("Created new entity manifest")
    
    entity_manifest_text = entity_manifest.to_prompt_format()
    expected_entities = entity_manifest.get_expected_entities()
    
    # Add structured entity tracking instruction
    entity_tracking_instruction = ""
    if expected_entities:
        entity_tracking_instruction = create_structured_prompt_injection(entity_manifest_text, expected_entities)
    
    timeline_log_parts = []
    # NEW: Define sequence_ids from the final recent_context
    sequence_ids = [str(entry.get('sequence_id', 'N/A')) for entry in truncated_story_context]
    for entry in truncated_story_context:
        actor_label = "Story" if entry.get(constants.KEY_ACTOR) == constants.ACTOR_GEMINI else "You"
        seq_id = entry.get('sequence_id', 'N/A')
        timeline_log_parts.append(f"[SEQ_ID: {seq_id}] {actor_label}: {entry.get(constants.KEY_TEXT)}")
    
    timeline_log_string = "\n\n".join(timeline_log_parts)

    # Create the final prompt for the current user turn (User's preferred method)
    current_prompt_text = _get_current_turn_prompt(user_input, mode)

    # --- NEW: Incorporate Game State & Timeline ---
    full_prompt = (
        f"{checkpoint_block}\\n\\n"
        f"{core_memories_summary}"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{sequence_id_list_string}]\\n\\n"
        f"CURRENT GAME STATE:\\n{serialized_game_state}\\n\\n"
        f"{entity_tracking_instruction}"
        f"TIMELINE LOG (FOR CONTEXT):\\n{timeline_log_string}\\n\\n"
        f"YOUR TURN:\\n{current_prompt_text}"
    )
    
    # For all subsequent calls, use the standard, cheaper model.
    # Use pro model for first 5 user inputs for better world building
    if os.environ.get('TESTING'):
        chosen_model = TEST_MODEL
    elif user_input_count is not None and user_input_count <= USE_PRO_MODEL_FOR_FIRST_N_INPUTS:
        chosen_model = LARGE_CONTEXT_MODEL
        logging.info(f"Using pro model for user input {user_input_count}/{USE_PRO_MODEL_FOR_FIRST_N_INPUTS}")
    else:
        chosen_model = DEFAULT_MODEL
    
    # Use structured JSON output if entity tracking is enabled
    if expected_entities:
        # Configure for JSON response
        response = _call_gemini_api([full_prompt], chosen_model, 
                                  current_prompt_text_for_logging=current_prompt_text, 
                                  system_instruction_text=system_instruction_final,
                                  use_json_mode=True)
        raw_response_text = _get_text_from_response(response)
        
        # Parse structured response
        response_text, structured_response = parse_structured_response(raw_response_text)
        
        # Validate structured response coverage
        if isinstance(structured_response, NarrativeResponse):
            coverage_validation = validate_entity_coverage(structured_response, expected_entities)
            logging.info(f"STRUCTURED_GENERATION: Coverage rate {coverage_validation['coverage_rate']:.2f}, "
                        f"Schema valid: {coverage_validation['schema_valid']}")
            
            if not coverage_validation['schema_valid']:
                logging.warning(f"STRUCTURED_GENERATION: Missing from schema: {coverage_validation['missing_from_schema']}")
        else:
            logging.warning("STRUCTURED_GENERATION: Failed to parse JSON response, falling back to plain text")
    else:
        # Standard generation without entity tracking
        response = _call_gemini_api([full_prompt], chosen_model, 
                                  current_prompt_text_for_logging=current_prompt_text, 
                                  system_instruction_text=system_instruction_final)
        response_text = _get_text_from_response(response)
    
    # --- ENTITY TRACKING VALIDATION: Validate narrative against entity manifest ---
    if expected_entities:
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=response_text,
            expected_entities=expected_entities,
            location=current_game_state.world_data.get('current_location_name', 'Unknown')
        )
        
        if not validation_result.all_entities_present:
            logging.warning(f"ENTITY_TRACKING_VALIDATION: Narrative failed entity validation")
            logging.warning(f"Missing entities: {validation_result.entities_missing}")
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logging.warning(f"Validation warning: {warning}")
            
            # Add validation context to the response for debugging
            if current_game_state.debug_mode:
                debug_validation = (
                    f"\n\n[DEBUG_VALIDATION_START]\n"
                    f"Entity Tracking Validation Result:\n"
                    f"- Expected entities: {expected_entities}\n"
                    f"- Found entities: {validation_result.entities_found}\n"
                    f"- Missing entities: {validation_result.entities_missing}\n"
                    f"- Confidence: {validation_result.confidence:.2f}\n"
                    f"[DEBUG_VALIDATION_END]"
                )
                response_text += debug_validation
    
    return response_text

def _get_static_prompt_parts(current_game_state: GameState, story_context: list):
    """Helper to generate the non-timeline parts of the prompt."""
    sequence_ids = [str(entry.get('sequence_id', 'N/A')) for entry in story_context]
    sequence_id_list_string = ", ".join(sequence_ids)
    latest_seq_id = sequence_ids[-1] if sequence_ids else 'N/A'

    current_location = current_game_state.world_data.get('current_location_name', 'Unknown')
    
    pc_data = current_game_state.player_character_data
    # The key stats are now generated by the LLM in the [CHARACTER_RESOURCES] block.
    active_missions = current_game_state.custom_campaign_state.get('active_missions', [])
    if active_missions:
        # Handle both old style (list of strings) and new style (list of dicts)
        mission_names = []
        for m in active_missions:
            if isinstance(m, dict):
                # For dict format, try to get 'name' field, fallback to 'title' or convert to string
                name = m.get('name') or m.get('title') or str(m)
            else:
                # For string format, use as-is
                name = str(m)
            mission_names.append(name)
        missions_summary = "Missions: " + (", ".join(mission_names) if mission_names else "None")
    else:
        missions_summary = "Missions: None"

    ambition = pc_data.get('core_ambition')
    milestone = pc_data.get('next_milestone')
    ambition_summary = ""
    if ambition and milestone:
        ambition_summary = f"Ambition: {ambition} | Next Milestone: {milestone}"

    core_memories = current_game_state.custom_campaign_state.get('core_memories', [])
    core_memories_summary = ""
    if core_memories:
        core_memories_list = "\\n".join([f"- {item}" for item in core_memories])
        core_memories_summary = f"CORE MEMORY LOG (SUMMARY OF KEY EVENTS):\\n{core_memories_list}\\n\\n"

    checkpoint_block = (
        f"[CHECKPOINT BLOCK:]\\n"
        f"Sequence ID: {latest_seq_id} | Location: {current_location}\\n"
        f"{missions_summary}\\n"
        f"{ambition_summary}"
    )

    return checkpoint_block, core_memories_summary, sequence_id_list_string

def _get_current_turn_prompt(user_input, mode):
    """Helper to generate the text for the user's current action."""
    if mode == 'character':
        prompt_template = "Main character: {user_input}. Continue the story in about {word_count} words and " \
            "add details for narrative, descriptions of scenes, character dialog, character emotions."
        return prompt_template.format(user_input=user_input, word_count=TARGET_WORD_COUNT)
    else: # god mode
        prompt_template = "GOD MODE: {user_input}"
        return prompt_template.format(user_input=user_input)

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
        text = entry.get(constants.KEY_TEXT, '')
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
def _clean_markdown_from_json(json_string: str) -> str:
    """
    Cleans various markdown formatting patterns from JSON strings that LLMs might generate.
    Handles code blocks, bold formatting, HTML tags, and other common markdown decorations.
    """
    # Start with the original string, stripped of leading/trailing whitespace
    cleaned = json_string.strip()
    
    # Remove HTML tags (like <strong>, </strong>) first
    cleaned = re.sub(r'<[^>]+>', '', cleaned)
    
    # Remove lines that are purely markdown decorations or commentary
    lines = cleaned.split('\n')
    json_lines = []
    for line in lines:
        stripped_line = line.strip()
        # Skip lines that are just markdown decorations or commentary
        if (stripped_line and 
            not re.match(r'^[\*\-_=]+$', stripped_line) and           # Lines of just asterisks/dashes
            not re.match(r'^\*[^{]*\*$', stripped_line) and           # Lines wrapped in asterisks without JSON
            not re.match(r'^\*.*\*$', stripped_line) and              # Any line wrapped in single asterisks
            not re.match(r'^[^{}\[\]]*update[^{}\[\]]*$', stripped_line, re.IGNORECASE)):  # Commentary lines mentioning "update"
            json_lines.append(line)
    
    cleaned = '\n'.join(json_lines)
    
    # Handle mixed formatting patterns like **```json...```**
    # Remove outer bold markers around code blocks
    if cleaned.startswith("**```") and cleaned.endswith("```**"):
        cleaned = cleaned[2:-2]  # Remove ** from both ends
    
    # Handle markdown code blocks (```json and ```) - do this AFTER line filtering
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    # Remove bold markdown formatting (**text**)
    # Handle both single-line and multi-line bold wrapping
    cleaned = re.sub(r'^\*\*\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*\*\*$', '', cleaned, flags=re.MULTILINE)
    
    # Remove italic markdown formatting (*text*)
    cleaned = re.sub(r'^\*\s*', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*\*$', '', cleaned, flags=re.MULTILINE)
    
    # Final cleanup: strip whitespace
    cleaned = cleaned.strip()
    
    return cleaned

def parse_llm_response_for_state_changes(llm_text_response: str) -> dict:
    """
    Parses the full text response from the LLM to find and extract the JSON object
    containing proposed state changes. It is robust to multiple state update blocks,
    parsing the last valid one it finds.
    """
    # Use re.findall to get all occurrences of the state update block.
    # This handles cases where the AI might generate multiple blocks in its thought process.
    matches = re.findall(r'\[STATE_UPDATES_PROPOSED\](.*?)\[END_STATE_UPDATES_PROPOSED\]', llm_text_response, re.DOTALL)

    if not matches:
        logging.info("No state update block found in the LLM response.")
        return {}

    # Iterate through the found blocks in reverse order, taking the last valid one.
    for json_string in reversed(matches):
        json_string = json_string.strip()
        
        if not json_string:
            continue # Skip empty blocks

        # Clean up markdown formatting from the LLM response
        json_string = _clean_markdown_from_json(json_string)

        try:
            proposed_changes = json.loads(json_string)
            
            if isinstance(proposed_changes, dict):
                logging.info("Successfully parsed a valid state update block.")
                return proposed_changes
            else:
                logging.warning(f"Found a state update block, but parsed JSON was not a dictionary. Type: {type(proposed_changes)}. Content: {proposed_changes}")
        except json.JSONDecodeError:
            logging.warning(f"Found a state update block, but it contained invalid JSON. Content: `{json_string}`")
            continue # Try the next block

    logging.warning("Found state update block(s), but none contained valid JSON.")
    return {}

# --- Main block for rapid, direct testing ---
if __name__ == "__main__":
    print("--- Running gemini_service.py in chained conversation test mode ---")
    
    try:
        # Look for Google API key in home directory first, then project root
        home_key_path = os.path.expanduser("~/.gemini_api_key.txt")
        project_key_path = "gemini_api_key.txt"
        
        if os.path.exists(home_key_path):
            with open(home_key_path, 'r') as f:
                api_key = f.read().strip()
            print(f"Successfully loaded API key from {home_key_path}")
        elif os.path.exists(project_key_path):
            with open(project_key_path, 'r') as f:
                api_key = f.read().strip()
            print(f"Successfully loaded API key from {project_key_path}")
        else:
            print("\nERROR: API key not found in ~/.gemini_api_key.txt or gemini_api_key.txt")
            sys.exit(1)
            
        os.environ["GEMINI_API_KEY"] = api_key
    except Exception as e:
        print(f"\nERROR: Failed to load API key: {e}")
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
