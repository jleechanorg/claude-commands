import os
from google import genai
from google.genai import types
import logging
import logging_util
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
from gemini_response import GeminiResponse
# Import entity tracking mitigation modules
from entity_preloader import EntityPreloader
from entity_instructions import EntityInstructionGenerator
from entity_validator import EntityValidator
from dual_pass_generator import DualPassGenerator
from entity_tracking import SceneManifest, create_from_game_state

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize entity tracking mitigation modules
entity_preloader = EntityPreloader()
instruction_generator = EntityInstructionGenerator()
entity_validator = EntityValidator()
dual_pass_generator = DualPassGenerator()

def json_datetime_serializer(obj):
    """JSON serializer for datetime objects."""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# --- CONSTANTS ---
# Use flash for all operations.
DEFAULT_MODEL = 'gemini-2.5-flash'
# Use 1.5 flash for testing as requested
TEST_MODEL = 'gemini-1.5-flash'

# Model cycling order for 503 errors - try these in sequence
MODEL_FALLBACK_CHAIN = [
    "gemini-2.5-flash",                     
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-flash",                     # Cross-generation fallback
    "gemini-2.0-flash-lite",                # Highest availability
]

# No longer using pro model for any inputs

MAX_TOKENS = 50000
TEMPERATURE = 0.9
TARGET_WORD_COUNT = 300
# Add a safety margin for JSON responses
JSON_MODE_MAX_TOKENS = 50000  # Reduced limit when using JSON mode for reliability
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

# NEW: Centralized map of prompt types to their file paths.
# This is now the single source of truth for locating prompt files.
PATH_MAP = {
    constants.PROMPT_TYPE_NARRATIVE: constants.NARRATIVE_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_MECHANICS: constants.MECHANICS_SYSTEM_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_GAME_STATE: constants.GAME_STATE_INSTRUCTION_PATH,
    constants.PROMPT_TYPE_CHARACTER_TEMPLATE: constants.CHARACTER_TEMPLATE_PATH,
    # constants.PROMPT_TYPE_ENTITY_SCHEMA: constants.ENTITY_SCHEMA_INSTRUCTION_PATH, # Integrated into game_state
    constants.PROMPT_TYPE_MASTER_DIRECTIVE: constants.MASTER_DIRECTIVE_PATH,
    constants.PROMPT_TYPE_DND_SRD: constants.DND_SRD_INSTRUCTION_PATH,
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
            logging_util.error(f"FATAL: Unknown instruction type requested: {instruction_type}")
            raise ValueError(f"Unknown instruction type requested: {instruction_type}")

        file_path = os.path.join(os.path.dirname(__file__), relative_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            # logging.info(f'Loaded prompt "{instruction_type}" from file: {os.path.basename(file_path)}')
            _loaded_instructions_cache[instruction_type] = content
        except FileNotFoundError:
            logging_util.error(f"CRITICAL: System instruction file not found: {file_path}. This is a fatal error for this request.")
            raise
        except Exception as e:
            logging_util.error(f"CRITICAL: Error loading system instruction file {file_path}: {e}")
            raise
    else:
        pass
        #logging.info(f'Loaded prompt "{instruction_type}" from cache.')
        
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


class PromptBuilder:
    """Encapsulates prompt building logic for the Gemini service."""

    def __init__(self, game_state=None):
        """Initialize the PromptBuilder.

        Args:
            game_state: Optional GameState used for dynamic instructions.
        """
        self.game_state = game_state
    
    def build_core_system_instructions(self):
        """
        Build the core system instructions that are always loaded first.
        Returns a list of instruction parts.
        """
        parts = []
        
        # CRITICAL: Load master directive FIRST to establish hierarchy and authority
        # This must come before all other instructions to set the precedence rules
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_MASTER_DIRECTIVE))
        
        # CRITICAL: Load game_state instructions SECOND (highest authority per master directive)
        # This prevents "instruction fatigue" and ensures data structure compliance
        # NOTE: Entity schemas are now integrated into game_state_instruction.md for LLM optimization
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_GAME_STATE))
        
        # Add debug mode instructions THIRD for technical functionality
        # The backend will strip debug content for users when debug_mode is False
        parts.append(_build_debug_instructions())
        
        return parts
    
    def add_character_instructions(self, parts, selected_prompts):
        """
        Conditionally add character-related instructions based on selected prompts.
        """
        # Conditionally add the character template if narrative instructions are selected
        if constants.PROMPT_TYPE_NARRATIVE in selected_prompts:
            parts.append(_load_instruction_file(constants.PROMPT_TYPE_CHARACTER_TEMPLATE))
    
    def add_selected_prompt_instructions(self, parts, selected_prompts):
        """
        Add instructions for selected prompt types in consistent order.
        """
        # Define the order for consistency (calibration archived)
        prompt_order = [constants.PROMPT_TYPE_NARRATIVE, constants.PROMPT_TYPE_MECHANICS]
        
        # Add in order
        for p_type in prompt_order:
            if p_type in selected_prompts:
                parts.append(_load_instruction_file(p_type))
    
    def add_system_reference_instructions(self, parts):
        """
        Add system reference instructions that are always included.
        """
        # Always include the D&D SRD instruction (replaces complex dual-system approach)
        parts.append(_load_instruction_file(constants.PROMPT_TYPE_DND_SRD))
    
    def build_companion_instruction(self):
        """Build companion instruction text."""

        state = None
        if self.game_state is not None:
            if hasattr(self.game_state, "to_dict"):
                state = self.game_state.to_dict()
            elif hasattr(self.game_state, "data"):
                state = self.game_state.data

        companions = None
        if isinstance(state, dict):
            companions = state.get("game_state", {}).get("companions")

        if companions and isinstance(companions, dict):
            lines = ["**ACTIVE COMPANIONS**"]
            for name, info in companions.items():
                if not isinstance(info, dict):
                    continue
                cls = info.get("class", "Unknown")
                lines.append(f"- {name} ({cls})")
            return "\n".join(lines)

        # Fallback to static instruction used during initial story generation
        return (
            "\n**SPECIAL INSTRUCTION: COMPANION GENERATION ACTIVATED**\n"
            "You have been specifically requested to generate 3 starting companions for this campaign. "
            "Follow Part 7: Companion Generation Protocol from the narrative instructions. "
            "In your opening narrative, introduce all 3 companions and include them in the initial STATE_UPDATES_PROPOSED block.\n\n"
        )
    
    def build_background_summary_instruction(self):
        """Build background summary instruction text."""

        state = None
        if self.game_state is not None:
            if hasattr(self.game_state, "to_dict"):
                state = self.game_state.to_dict()
            elif hasattr(self.game_state, "data"):
                state = self.game_state.data

        story = None
        if isinstance(state, dict):
            story = state.get("game_state", {}).get("story")

        summary = None
        if isinstance(story, dict):
            summary = story.get("summary")

        if summary:
            return f"**STORY SUMMARY**\n{summary}"

        # Fallback to static background instruction
        return (
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
    
    def build_continuation_reminder(self):
        """
        Build reminders for story continuation, especially planning blocks.
        """
        return (
            "\n**CRITICAL REMINDER FOR STORY CONTINUATION**\n"
            "1. **MANDATORY PLANNING BLOCK**: Every STORY MODE response MUST end with '--- PLANNING BLOCK ---'\n"
            "2. **Think Commands**: If the user says 'think', 'plan', 'consider', 'strategize', or 'options', "
            "generate ONLY internal thoughts with a deep think block (pros/cons). DO NOT take narrative actions.\n"
            "3. **Standard Responses**: All other responses should include narrative continuation followed by "
            "a standard planning block with 3-4 action options.\n"
            "4. **Never Skip**: The planning block is MANDATORY - never end a response without one.\n\n"
        )
    
    def finalize_instructions(self, parts, use_default_world=False):
        """
        Finalize the system instructions by adding world instructions.
        Returns the complete system instruction string.
        """
        # Add world instructions if requested
        if use_default_world:
            _add_world_instructions_to_system(parts)
        
        # Debug instructions already added at the beginning in build_core_system_instructions
        
        return "\n\n".join(parts)


def _build_debug_instructions():
    """
    Build the debug mode instructions that are always included for game state management.
    The backend will strip debug content for users when debug_mode is False.
    
    Returns:
        str: The formatted debug instruction string
    """
    return (
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
        "   - Format: [DEBUG_RESOURCES_START]Resources: 1 HD used (2/3 remaining), 1 spell slot level 2 (2/3 remaining), short rests: 1/2[DEBUG_RESOURCES_END]\n"
        "   - Include: Hit Dice (HD), spell slots by level, class features (ki points, rage, etc.), consumables, exhaustion\n"
        "   - Show both used and remaining for each resource\n"
        "\n"
        "4. **STATE CHANGES**: After your main narrative, include a section wrapped in [DEBUG_STATE_START] and [DEBUG_STATE_END] tags that explains what state changes you're proposing and why.\n"
        "\n"
        "**Examples:**\n"
        "- [DEBUG_START]The player is attempting a stealth approach, so I need to roll for the guards' perception...[DEBUG_END]\n"
        "- [DEBUG_ROLL_START]Guard Perception: 1d20+2 = 12+2 = 14 vs DC 15 (Failure - guards don't notice)[DEBUG_ROLL_END]\n"
        "- [DEBUG_RESOURCES_START]Resources: 0 HD used (3/3 remaining), no spell slots used, short rests: 2/2[DEBUG_RESOURCES_END]\n"
        "- [DEBUG_STATE_START]Updating player position to 'hidden behind crates' and setting guard alertness to 'unaware'[DEBUG_STATE_END]\n"
        "\n"
        "NOTE: This debug information helps maintain game state consistency and will be conditionally shown to players based on their debug mode setting.\n\n"
    )


def _prepare_entity_tracking(game_state, story_context, session_number):
    """
    Prepare entity tracking manifest and expected entities.
    
    Args:
        game_state: Current GameState object
        story_context: List of story context entries
        session_number: Current session number
        
    Returns:
        tuple: (entity_manifest_text, expected_entities, entity_tracking_instruction)
    """
    # Extract turn number from story context
    turn_number = len(story_context) + 1
    
    # Create entity manifest from current game state (with basic caching)
    game_state_dict = game_state.to_dict()
    manifest_cache_key = f"manifest_{session_number}_{turn_number}_{hash(str(sorted(game_state_dict.get('npc_data', {}).items())))}"
    
    # Simple in-memory cache for the request duration
    if not hasattr(game_state, '_manifest_cache'):
        game_state._manifest_cache = {}
    
    if manifest_cache_key in game_state._manifest_cache:
        entity_manifest = game_state._manifest_cache[manifest_cache_key]
        logging.debug("Using cached entity manifest")
    else:
        entity_manifest = create_from_game_state(game_state_dict, session_number, turn_number)
        game_state._manifest_cache[manifest_cache_key] = entity_manifest
        logging.debug("Created new entity manifest")
    
    entity_manifest_text = entity_manifest.to_prompt_format()
    expected_entities = entity_manifest.get_expected_entities()
    
    # Always add structured response format instruction (for both entity tracking and general JSON response)
    entity_tracking_instruction = create_structured_prompt_injection(entity_manifest_text, expected_entities)
    
    return entity_manifest_text, expected_entities, entity_tracking_instruction


def _build_timeline_log(story_context):
    """
    Build the timeline log string from story context.
    
    Args:
        story_context: List of story context entries
        
    Returns:
        str: Formatted timeline log
    """
    timeline_log_parts = []
    for entry in story_context:
        actor_label = "Story" if entry.get(constants.KEY_ACTOR) == constants.ACTOR_GEMINI else "You"
        seq_id = entry.get('sequence_id', 'N/A')
        timeline_log_parts.append(f"[SEQ_ID: {seq_id}] {actor_label}: {entry.get(constants.KEY_TEXT)}")
    
    return "\n\n".join(timeline_log_parts)


def _build_continuation_prompt(checkpoint_block, core_memories_summary, sequence_id_list_string,
                             serialized_game_state, entity_tracking_instruction, 
                             timeline_log_string, current_prompt_text):
    """
    Build the full continuation prompt.
    
    Returns:
        str: Complete prompt for continuation
    """
    return (
        f"{checkpoint_block}\\n\\n"
        f"{core_memories_summary}"
        f"REFERENCE TIMELINE (SEQUENCE ID LIST):\\n[{sequence_id_list_string}]\\n\\n"
        f"CURRENT GAME STATE:\\n{serialized_game_state}\\n\\n"
        f"{entity_tracking_instruction}"
        f"TIMELINE LOG (FOR CONTEXT):\\n{timeline_log_string}\\n\\n"
        f"YOUR TURN:\\n{current_prompt_text}"
    )


def _select_model_for_continuation(user_input_count):
    """
    Select the appropriate model based on testing mode and input count.
    
    Args:
        user_input_count: Number of user inputs so far
        
    Returns:
        str: Model name to use
    """
    if os.environ.get('TESTING'):
        return TEST_MODEL
    else:
        return DEFAULT_MODEL


def _process_structured_response(raw_response_text, expected_entities):
    """
    Process structured JSON response and validate entity coverage.
    
    Args:
        raw_response_text: Raw response from API
        expected_entities: List of expected entity names
        
    Returns:
        tuple: (response_text, structured_response) where structured_response is NarrativeResponse or None
    """
    response_text, structured_response = parse_structured_response(raw_response_text)
    
    # Validate structured response coverage
    if isinstance(structured_response, NarrativeResponse):
        coverage_validation = validate_entity_coverage(structured_response, expected_entities)
        logging.info(f"STRUCTURED_GENERATION: Coverage rate {coverage_validation['coverage_rate']:.2f}, "
                    f"Schema valid: {coverage_validation['schema_valid']}")
        
        if not coverage_validation['schema_valid']:
            logging_util.warning(f"STRUCTURED_GENERATION: Missing from schema: {coverage_validation['missing_from_schema']}")
        
        # Append state updates to response text if present
        if hasattr(structured_response, 'state_updates') and structured_response.state_updates:
            import json
            state_updates_text = f"\n\n[STATE_UPDATES_PROPOSED]\n{json.dumps(structured_response.state_updates, indent=2)}\n[END_STATE_UPDATES_PROPOSED]"
            response_text = response_text + state_updates_text
            logging.info("Appended state updates from structured response to response text")
    else:
        logging_util.warning("STRUCTURED_GENERATION: Failed to parse JSON response, falling back to plain text")
    
    return response_text, structured_response


def _validate_entity_tracking(response_text, expected_entities, game_state):
    """
    Validate that the narrative includes all expected entities.
    
    Args:
        response_text: Generated narrative text
        expected_entities: List of expected entity names
        game_state: Current GameState object
        
    Returns:
        str: Response text with debug validation if in debug mode
    """
    validator = NarrativeSyncValidator()
    validation_result = validator.validate(
        narrative_text=response_text,
        expected_entities=expected_entities,
        location=game_state.world_data.get('current_location_name', 'Unknown')
    )
    
    if not validation_result.all_entities_present:
        logging_util.warning(f"ENTITY_TRACKING_VALIDATION: Narrative failed entity validation")
        logging_util.warning(f"Missing entities: {validation_result.entities_missing}")
        if validation_result.warnings:
            for warning in validation_result.warnings:
                logging_util.warning(f"Validation warning: {warning}")
    
    # Add validation context to the response for debugging
    if game_state.debug_mode and expected_entities:
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

def _call_gemini_api_with_model_cycling(prompt_contents, model_name, current_prompt_text_for_logging=None, system_instruction_text=None):
    """
    Calls the Gemini API with model cycling on 503 errors.
    Tries the requested model first, then cycles through fallback models.
    Always uses JSON mode for structured responses.
    
    Args:
        prompt_contents: The content to send to the API
        model_name: Primary model to try first  
        current_prompt_text_for_logging: Text for logging purposes (optional)
        system_instruction_text: System instructions (optional)
    
    Returns:
        Gemini API response object with JSON response
    """
    client = get_client()
    
    # Create ordered list starting with requested model, then fallbacks
    models_to_try = [model_name]
    for fallback_model in MODEL_FALLBACK_CHAIN:
        if fallback_model != model_name and fallback_model not in models_to_try:
            models_to_try.append(fallback_model)
    
    if current_prompt_text_for_logging:
        logging.info(f"--- Calling Gemini API with current prompt: {str(current_prompt_text_for_logging)[:1000]}... ---")

    # Log both character and estimated token counts for transition period
    total_chars = sum(len(p) for p in prompt_contents if isinstance(p, str))
    if system_instruction_text:
        total_chars += len(system_instruction_text)
    estimated_tokens = total_chars // 4  # Rough estimate: 1 token per 4 characters
    logging.info(f"--- Calling Gemini API with prompt of {total_chars} characters (~{estimated_tokens} tokens) ---")

    last_error = None
    
    for attempt, current_model in enumerate(models_to_try):
        try:
            # Log token count for the current model being tried
            _log_token_count(current_model, prompt_contents, system_instruction_text)
            
            if attempt > 0:
                logging.warning(f"--- Attempting fallback model #{attempt}: {current_model} (after {attempt} failed attempts) ---")
            else:
                logging.info(f"--- Attempting primary model: {current_model} ---")

            generation_config_params = {
                "max_output_tokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "safety_settings": SAFETY_SETTINGS
            }
            
            # Configure JSON response mode if requested
            # Always use JSON response mode for consistent structured output
            generation_config_params["response_mime_type"] = "application/json"
            # Use reduced token limit for JSON mode to ensure proper completion
            generation_config_params["max_output_tokens"] = JSON_MODE_MAX_TOKENS
            if attempt == 0:  # Only log once
                logging.info(f"--- Using JSON response mode with reduced token limit ({JSON_MODE_MAX_TOKENS}) ---")
            
            # Pass the system instruction to the generate_content call
            if system_instruction_text:
                generation_config_params["system_instruction"] = types.Part(text=system_instruction_text)

            response = client.models.generate_content(
                model=current_model,
                contents=prompt_contents,
                config=types.GenerateContentConfig(**generation_config_params)
            )
            
            if attempt > 0:
                logging.warning(f"--- SUCCESS: Fallback model {current_model} worked after {attempt} failed attempts ---")
            else:
                logging.info(f"--- SUCCESS: Primary model {current_model} worked ---")
            
            return response
            
        except Exception as e:
            last_error = e
            error_message = str(e)
            
            # Try to extract status code from different exception types
            status_code = None
            
            # Check if the exception has a status_code attribute
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            # Check if it's a ServerError with the status in the message
            elif '503 UNAVAILABLE' in error_message:
                status_code = 503
            elif '429' in error_message:
                status_code = 429
            elif '400' in error_message and "not found" in error_message.lower():
                status_code = 400
            
            if status_code == 503:  # Service unavailable
                logging.warning(f"--- Model {current_model} overloaded (503), trying next model... ---")
                continue
            elif status_code == 429:  # Rate limit
                logging.warning(f"--- Model {current_model} rate limited (429), trying next model... ---")
                continue
            elif status_code == 400 and "not found" in error_message.lower():  # Model not found
                logging.warning(f"--- Model {current_model} not found (400), trying next model... ---")
                continue
            else:
                # For other errors, don't continue cycling - raise immediately
                logging.error(f"--- Non-recoverable error with model {current_model}: {e} ---")
                raise e
    
    # If we get here, all models failed
    logging.error(f"--- ALL MODELS FAILED: Tried {len(models_to_try)} models: {models_to_try} ---")
    logging.error(f"--- Last error: {last_error} ---")
    
    # Ensure we have a meaningful error to raise
    if last_error is None:
        raise RuntimeError(f"All {len(models_to_try)} Gemini models failed but no specific error was captured")
    raise last_error

def _call_gemini_api(prompt_contents, model_name, current_prompt_text_for_logging=None, system_instruction_text=None):
    """
    Call Gemini API with model cycling on errors.
    
    This function always uses JSON mode for consistent structured responses.
    
    Args:
        prompt_contents: The content to send to the API
        model_name: Primary model to try first  
        current_prompt_text_for_logging: Text for logging purposes (optional)
        system_instruction_text: System instructions (optional)
    
    Returns:
        Gemini API response object with JSON response
    """
    return _call_gemini_api_with_model_cycling(
        prompt_contents, model_name, current_prompt_text_for_logging, system_instruction_text
    )

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

    # Use PromptBuilder to construct system instructions
    builder = PromptBuilder()
    
    # Build core instructions
    system_instruction_parts = builder.build_core_system_instructions()
    
    # Add character-related instructions
    builder.add_character_instructions(system_instruction_parts, selected_prompts)
    
    # Add selected prompt instructions
    builder.add_selected_prompt_instructions(system_instruction_parts, selected_prompts)
    
    # Add system reference instructions
    builder.add_system_reference_instructions(system_instruction_parts)
    
    # Add companion generation instruction if requested
    if generate_companions:
        system_instruction_parts.append(builder.build_companion_instruction())
    
    # Add background summary instruction for initial story
    system_instruction_parts.append(builder.build_background_summary_instruction())
    
    # Finalize with world and debug instructions
    system_instruction_final = builder.finalize_instructions(system_instruction_parts, use_default_world)
    
    # Add clear indication when using default world setting
    if use_default_world:
        prompt = f"Use default setting Assiah. {prompt}"
    
    # --- ENTITY TRACKING FOR INITIAL STORY ---
    # Extract expected entities from the prompt for initial tracking
    expected_entities = []
    entity_preload_text = ""
    entity_specific_instructions = ""
    entity_tracking_instruction = ""
    
    # Try to extract character name from prompt
    import re
    # Look for "Player Character: Name" or "PC: Name" patterns
    character_match = re.search(r'(?:Player\s+Character|PC|Character):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', prompt)
    if character_match:
        character_name = character_match.group(1).strip()
        expected_entities.append(character_name)
        logging.info(f"Detected player character name from prompt: {character_name}")
    
    # Extract NPCs mentioned in prompt - look for specific patterns
    # "NPCs including X, Y, and Z" or "advisor named X"
    npc_patterns = [
        r'NPCs?\s+(?:including|such as)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)*)',
        r'(?:advisor|companion|member)s?\s+(?:named?|called?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
    ]
    
    for pattern in npc_patterns:
        matches = re.findall(pattern, prompt)
        for match in matches:
            # Split by commas if multiple NPCs listed
            npc_names = [n.strip() for n in match.split(',')]
            for npc in npc_names:
                if npc and npc not in expected_entities and npc not in ['and', 'or', 'the', 'a', 'an']:
                    expected_entities.append(npc)
                    logging.info(f"Detected NPC from prompt: {npc}")
    
    # Create a minimal initial game state for entity tracking
    if expected_entities:
        # Create minimal game state for entity tracking
        pc_name = expected_entities[0] if expected_entities else "Unknown"
        initial_game_state = {
            'player_character_data': {
                'name': pc_name,
                'hp': 10,
                'max_hp': 10,
                'level': 1,
                'string_id': f"pc_{pc_name.lower().replace(' ', '_')}_001"
            },
            'npc_data': {},
            'world_data': {'current_location_name': 'The throne room'},
            'combat_state': {'in_combat': False}
        }
        
        # 1. Entity Pre-Loading (Option 3)
        entity_preload_text = entity_preloader.create_entity_preload_text(
            initial_game_state, 1, 1, 'Starting Location'
        )
        
        # 2. Entity-Specific Instructions (Option 5)
        entity_instructions = instruction_generator.generate_entity_instructions(
            entities=expected_entities,
            player_references=[prompt],
            location='Starting Location',
            story_context=""
        )
        entity_specific_instructions = entity_instructions
        
        # 3. Create entity manifest for tracking using create_from_game_state
        # For initial story, we use session 1, turn 1
        entity_manifest = create_from_game_state(initial_game_state, 1, 1)
        entity_manifest_text = entity_manifest.to_prompt_format()
        entity_tracking_instruction = create_structured_prompt_injection(entity_manifest_text, expected_entities)
    
    # Build enhanced prompt with entity tracking
    enhanced_prompt = prompt
    if entity_preload_text or entity_specific_instructions or entity_tracking_instruction:
        enhanced_prompt = (
            f"{entity_preload_text}"
            f"{entity_specific_instructions}"
            f"{entity_tracking_instruction}"
            f"\nUSER REQUEST:\n{prompt}"
        )
        logging.info(f"Added entity tracking to initial story. Expected entities: {expected_entities}")
    
    # Add character creation reminder if mechanics is enabled
    if selected_prompts and constants.PROMPT_TYPE_MECHANICS in selected_prompts:
        enhanced_prompt = constants.CHARACTER_CREATION_REMINDER + "\n\n" + enhanced_prompt
        logging.info("Added character creation reminder to initial story prompt")
    
    contents = [types.Content(role="user", parts=[types.Part(text=enhanced_prompt)])]
    
    # --- MODEL SELECTION ---
    # Use default model for all operations.
    model_to_use = TEST_MODEL if os.environ.get('TESTING') else DEFAULT_MODEL
    logging.info(f"Using model: {model_to_use} for initial story generation.")

    response = _call_gemini_api(contents, model_to_use, current_prompt_text_for_logging=prompt, 
                              system_instruction_text=system_instruction_final)
    raw_response_text = _get_text_from_response(response)
    
    # Process structured response for consistency
    response_text, structured_response = _process_structured_response(raw_response_text, expected_entities or [])
    
    # --- ENTITY VALIDATION FOR INITIAL STORY ---
    if expected_entities:
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=response_text,
            expected_entities=expected_entities,
            location='Starting Location'
        )
        
        if not validation_result.all_entities_present:
            logging.warning(f"Initial story failed entity validation. Missing: {validation_result.entities_missing}")
            # For initial story, we'll log but not retry to avoid complexity
            # The continue_story function will handle retry logic for subsequent interactions
    
    return GeminiResponse.create(response_text, structured_response, raw_response_text)

def _validate_and_enforce_planning_block(response_text, user_input, game_state, chosen_model, system_instruction):
    """
    Validates that a story mode response ends with a planning block.
    If missing, asks the LLM to generate an appropriate planning block.
    
    Args:
        response_text: The AI's response text
        user_input: The user's input to determine if deep think block is needed
        game_state: Current game state for context
        chosen_model: Model to use for generation
        system_instruction: System instruction for the LLM
        
    Returns:
        str: Response text with planning block ensured
    """
    # Skip planning block enforcement during character creation
    if re.search(r"\[CHARACTER CREATION", response_text, re.IGNORECASE):
        logging.info("Skipping planning block for character creation step")
        return response_text
    
    # Skip planning block if user is switching to god/dm mode
    if any(phrase in user_input.lower() for phrase in constants.MODE_SWITCH_PHRASES):
        logging.info("User switching to god/dm mode - skipping planning block")
        return response_text
    
    # Skip planning block if AI response indicates mode switch
    if "[Mode: DM MODE]" in response_text or "[Mode: GOD MODE]" in response_text:
        logging.info("Response indicates mode switch - skipping planning block")
        return response_text
    
    # Check if response already contains a planning block
    if "--- PLANNING BLOCK ---" in response_text:
        logging.info("Planning block found in response")
        return response_text
    
    logging.warning("PLANNING_BLOCK_MISSING: Story mode response missing required planning block")
    
    # Determine if we need a deep think block based on keywords
    think_keywords = ['think', 'plan', 'consider', 'strategize', 'options']
    user_input_lower = user_input.lower()
    needs_deep_think = any(keyword in user_input_lower for keyword in think_keywords)
    
    # Strip any trailing whitespace
    response_text = response_text.rstrip()
    
    # Create prompt to generate planning block with proper context isolation
    # Extract current character info for context
    pc_name = game_state.player_character_data.get('name', 'the character') if game_state.player_character_data else 'the character'
    current_location = game_state.world_data.get('current_location_name', 'current location') if game_state.world_data else 'current location'
    
    if needs_deep_think:
        planning_prompt = f"""
CRITICAL: Generate planning options ONLY for {pc_name} in {current_location}.
DO NOT reference other characters, campaigns, or unrelated narrative elements.

The player just said: "{user_input}"

They are asking to think/plan/consider their options. Generate ONLY a planning block using the think_planning_block template format from your system instructions.

Full narrative context:
{response_text}"""
    else:
        planning_prompt = f"""
CRITICAL: Generate planning options ONLY for {pc_name} in {current_location}.
DO NOT reference other characters, campaigns, or unrelated narrative elements.

Generate ONLY a planning block using the standard_choice_block template format from your system instructions.

Full narrative context:
{response_text}"""
    
    # Generate planning block using LLM
    try:
        planning_response = _call_gemini_api(
            [planning_prompt], 
            chosen_model, 
            current_prompt_text_for_logging="Planning block generation",
            system_instruction_text=system_instruction
        )
        planning_block = _get_text_from_response(planning_response)
        
        # Ensure it starts with newlines and the header
        if not planning_block.startswith("\n\n--- PLANNING BLOCK ---"):
            planning_block = "\n\n" + planning_block.strip()
        
        # Append the planning block
        response_text = response_text + planning_block
        logging.info(f"Added LLM-generated {'deep think' if needs_deep_think else 'standard'} planning block")
        
    except Exception as e:
        logging.error(f"Failed to generate planning block: {e}")
        # Fallback to a minimal generic block
        response_text = response_text + "\n\n--- PLANNING BLOCK ---\nWhat would you like to do next?\n1. **[Continue_1]:** Continue with your current course of action.\n2. **[Explore_2]:** Explore your surroundings.\n3. **[Other_3]:** Describe a different action you'd like to take."
    
    return response_text

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


    # Use PromptBuilder to construct system instructions
    builder = PromptBuilder(current_game_state)
    
    # Build core instructions
    system_instruction_parts = builder.build_core_system_instructions()
    
    # Add character-related instructions
    builder.add_character_instructions(system_instruction_parts, selected_prompts)
    
    # Add selected prompt instructions (filter calibration for continue_story)
    builder.add_selected_prompt_instructions(system_instruction_parts, selected_prompts)
    
    # Add system reference instructions
    builder.add_system_reference_instructions(system_instruction_parts)
    
    # Add continuation-specific reminders (planning blocks) only in character mode
    if mode == constants.MODE_CHARACTER:
        system_instruction_parts.append(builder.build_continuation_reminder())
    
    # Finalize with world and debug instructions
    system_instruction_final = builder.finalize_instructions(system_instruction_parts, use_default_world)

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
    scaffold_tokens = len(prompt_scaffold) // 4
    story_budget_tokens = char_budget_for_story // 4
    logging.info(f"Prompt scaffold is {len(prompt_scaffold)} chars (~{scaffold_tokens} tokens). Remaining budget for story: {char_budget_for_story} chars (~{story_budget_tokens} tokens)")

    # Truncate the story context if it exceeds the budget
    truncated_story_context = _truncate_context(story_context, char_budget_for_story, DEFAULT_MODEL, current_game_state)

    # Now that we have the final, truncated context, we can generate the real prompt parts.
    checkpoint_block, core_memories_summary, sequence_id_list_string = _get_static_prompt_parts(current_game_state, truncated_story_context)
    
    # Serialize the game state for inclusion in the prompt
    serialized_game_state = json.dumps(current_game_state.to_dict(), indent=2, default=json_datetime_serializer)
    
    # --- ENTITY TRACKING: Create scene manifest for entity tracking ---
    # Always prepare entity tracking to ensure JSON response format
    session_number = current_game_state.custom_campaign_state.get('session_number', 1)
    _, expected_entities, entity_tracking_instruction = _prepare_entity_tracking(
        current_game_state, truncated_story_context, session_number
    )
    
    # Build timeline log
    timeline_log_string = _build_timeline_log(truncated_story_context)
    
    # Enhanced entity tracking with mitigation strategies
    entity_preload_text = ""
    entity_specific_instructions = ""
    
    if expected_entities:
        # 1. Entity Pre-Loading (Option 3)
        game_state_dict = current_game_state.to_dict()
        turn_number = len(truncated_story_context) + 1
        current_location = current_game_state.world_data.get('current_location_name', 'Unknown')
        entity_preload_text = entity_preloader.create_entity_preload_text(
            game_state_dict, session_number, turn_number, current_location
        )
        
        # 2. Entity-Specific Instructions (Option 5)
        player_references = [user_input] if user_input else []
        entity_instructions = instruction_generator.generate_entity_instructions(
            entities=expected_entities,
            player_references=player_references,
            location=current_location,
            story_context=timeline_log_string
        )
        entity_specific_instructions = entity_instructions

    # Create the final prompt for the current user turn (User's preferred method)
    current_prompt_text = _get_current_turn_prompt(user_input, mode)

    # Build the full prompt with entity tracking enhancements
    enhanced_entity_tracking = entity_tracking_instruction
    if entity_preload_text or entity_specific_instructions:
        enhanced_entity_tracking = (
            f"{entity_preload_text}"
            f"{entity_specific_instructions}"
            f"{entity_tracking_instruction}"
        )
    
    full_prompt = _build_continuation_prompt(
        checkpoint_block, core_memories_summary, sequence_id_list_string,
        serialized_game_state, enhanced_entity_tracking, 
        timeline_log_string, current_prompt_text
    )
    
    # Select appropriate model
    chosen_model = _select_model_for_continuation(user_input_count)
    
    # ALWAYS use structured JSON output for consistent response format
    # This ensures state updates, planning blocks, and narrative are properly structured
    response = _call_gemini_api([full_prompt], chosen_model, 
                              current_prompt_text_for_logging=current_prompt_text, 
                              system_instruction_text=system_instruction_final)
    raw_response_text = _get_text_from_response(response)
    
    # Process structured response (handles both entity tracking and non-entity cases)
    response_text, structured_response = _process_structured_response(raw_response_text, expected_entities or [])
    
    # Validate entity tracking if enabled
    if expected_entities:
        # First do basic validation
        validator = NarrativeSyncValidator()
        validation_result = validator.validate(
            narrative_text=response_text,
            expected_entities=expected_entities,
            location=current_game_state.world_data.get('current_location_name', 'Unknown')
        )
        
        if not validation_result.all_entities_present:
            logging_util.warning(f"ENTITY_TRACKING_VALIDATION: Narrative failed entity validation")
            logging_util.warning(f"Missing entities: {validation_result.entities_missing}")
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    logging_util.warning(f"Validation warning: {warning}")
            
            # Attempt dual-pass retry (Option 7)
            logging.info("ENTITY_TRACKING_RETRY: Attempting dual-pass generation to fix missing entities")
            
            # Create generation callback for API calls
            def generation_callback(prompt):
                response = _call_gemini_api([prompt], chosen_model, 
                                          current_prompt_text_for_logging=current_prompt_text,
                                          system_instruction_text=system_instruction_final)
                return _get_text_from_response(response)
            
            # Use dual-pass generator to fix missing entities
            dual_pass_result = dual_pass_generator.generate_with_dual_pass(
                initial_prompt=full_prompt,
                expected_entities=expected_entities,
                location=current_game_state.world_data.get('current_location_name', 'Unknown'),
                generation_callback=generation_callback
            )
            
            if dual_pass_result.final_narrative:
                response_text = dual_pass_result.final_narrative
                # Calculate injected entities from the difference between passes
                injected_count = len(dual_pass_result.total_entities_found) - len(dual_pass_result.first_pass.entities_found)
                logging.info(f"ENTITY_TRACKING_RETRY: Dual-pass succeeded. "
                           f"Entities recovered: {injected_count}")
            else:
                logging.error("ENTITY_TRACKING_RETRY: Dual-pass generation failed")
        
        # Use the common validation function to add debug info if needed
        response_text = _validate_entity_tracking(response_text, expected_entities, current_game_state)
    
    # Validate and enforce planning block for story mode
    # Check if user is switching to god mode with their input
    user_input_lower = user_input.lower().strip()
    is_switching_to_god_mode = user_input_lower in constants.MODE_SWITCH_SIMPLE
    
    # Also check if the AI response indicates DM MODE
    is_dm_mode_response = '[Mode: DM MODE]' in response_text or '[Mode: GOD MODE]' in response_text
    
    # Only add planning blocks if:
    # 1. Currently in character mode
    # 2. User isn't switching to god mode
    # 3. AI response isn't in DM mode
    if mode == constants.MODE_CHARACTER and not is_switching_to_god_mode and not is_dm_mode_response:
        response_text = _validate_and_enforce_planning_block(
            response_text, user_input, current_game_state, chosen_model, system_instruction_final
        )
    
    return GeminiResponse.create(response_text, structured_response, raw_response_text)

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
        # Check if user is requesting planning/thinking
        think_keywords = ['think', 'plan', 'consider', 'strategize', 'options']
        user_input_lower = user_input.lower()
        is_think_command = any(keyword in user_input_lower for keyword in think_keywords)
        
        if is_think_command:
            # Emphasize planning for think commands
            prompt_template = "Main character: {user_input}. Generate the character's INTERNAL THOUGHTS ONLY with a deep think planning block. " \
                "DO NOT take any narrative actions. End with '--- PLANNING BLOCK ---' containing pros/cons analysis."
        else:
            # Standard story continuation with planning block reminder
            prompt_template = "Main character: {user_input}. Continue the story in about {word_count} words and " \
                "add details for narrative, descriptions of scenes, character dialog, character emotions. " \
                "MANDATORY: End your response with '--- PLANNING BLOCK ---' containing options for the player."
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
