import os
from google import genai  # Using the user-specified import style
import logging
from decorators import log_exceptions

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- MODULE-LEVEL CONSTANTS (Client SDK Syntax) ---
MODEL_NAME = 'gemini-2.5-pro-preview-06-05'

# Using genai.types, accessed from the new import
GENERATION_CONFIG = genai.types.GenerationConfig(max_output_tokens=600)

# Using genai.types, accessed from the new import
SAFETY_SETTINGS = [
    genai.types.SafetySetting(category=genai.types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=genai.types.HarmBlockThreshold.BLOCK_NONE),
    genai.types.SafetySetting(category=genai.types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=genai.types.HarmBlockThreshold.BLOCK_NONE),
    genai.types.SafetySetting(category=genai.types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=genai.types.HarmBlockThreshold.BLOCK_NONE),
    genai.types.SafetySetting(category=genai.types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=genai.types.HarmBlockThreshold.BLOCK_NONE),
]
# --- END CONSTANTS ---

_client = None
_is_configured = False

def _configure_once():
    """Ensures genai is configured only once using our API key."""
    global _is_configured
    if not _is_configured:
        logging.info("--- Configuring Gemini API for the first time ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
        genai.configure(api_key=api_key)
        _is_configured = True
        logging.info("--- Gemini API Configured Successfully ---")

def get_client():
    """Initializes and returns a singleton Gemini client."""
    global _client
    _configure_once()
    if _client is None:
        logging.info("--- Initializing Gemini Client for the first time ---")
        _client = genai.Client()
    return _client

def _get_text_from_response(response):
    """Safely extracts text from a Gemini response object."""
    try:
        return response.text
    except ValueError:
        logging.warning("--- Gemini Response Blocked ---")
        try:
            logging.warning(f"Prompt Feedback: {response.prompt_feedback}")
            if response.candidates and response.candidates[0].safety_ratings:
                logging.warning(f"Safety Ratings: {response.candidates[0].safety_ratings}")
        except Exception as e:
            logging.error(f"Error while logging safety feedback: {e}")
        return "The response was blocked by the content safety filter. Please modify your prompt and try again."

@log_exceptions
def get_initial_story(prompt):
    """Generates the initial story opening using the client.models pattern."""
    client = get_client()
    logging.info(f"--- Trying initial prompt: {prompt[:200]}... ---")
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[prompt],
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story using the client.models pattern."""
    client = get_client()
    last_gemini_response = ""
    for entry in reversed(story_context):
        if entry.get('actor') == 'gemini':
            last_gemini_response = entry.get('text', '')
            break

    if mode == 'character':
        prompt_template = "Acting as the main charter {user_input}. \n\n context: {last_gemini_response}. Continue the story."
    elif mode == 'god':
        prompt_template = "{user_input} \n\n context: {last_gemini_response}"
    else:
        raise ValueError("Invalid interaction mode specified.")

    full_prompt = prompt_template.format(user_input=user_input, last_gemini_response=last_gemini_response)
    logging.info(f"--- Trying continue_story prompt: {full_prompt[:300]}... ---")
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[full_prompt],
        generation_config=GENERATION_CONFIG,
        safety_settings=SAFETY_SETTINGS
    )
    return _get_text_from_response(response)
