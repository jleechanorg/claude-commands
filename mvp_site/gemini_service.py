import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- MODULE-LEVEL CONSTANTS ---
MODEL_NAME = 'gemini-2.5-pro-preview-06-05'
MAX_TOKENS = 600
TEMPERATURE = 0.9
SAFETY_SETTINGS = [
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
    types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
]
# --- END CONSTANTS ---

_client = None

def get_client():
    """Initializes and returns a singleton Gemini client."""
    global _client
    if _client is None:
        logging.info("--- Initializing Gemini Client for the first time ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
        _client = genai.Client(api_key=api_key)
        logging.info("--- Gemini Client Initialized Successfully ---")
    return _client

def _call_gemini_api(prompt_contents):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    logging.info(f"--- Calling Gemini API with prompt: {str(prompt_contents)[:300]}... ---")
    
    tool_config = {'function_calling_config': {'mode': 'none'}}

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_contents,
        tool_config=tool_config,
        config=types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            safety_settings=SAFETY_SETTINGS
        )
    )
    return response

# --- THIS IS THE FIX ---
def _get_text_from_response(response):
    """
    Safely extracts text from a Gemini response object with robust, transparent logging.
    """
    try:
        # The happy path: if response.text exists and is not None, return it.
        return response.text
    except ValueError as e:
        # This is the most likely error, often for safety blocks.
        # Log the ACTUAL error message from the exception first.
        logging.warning(f"ValueError while extracting text: {e}")
    except Exception as e:
        # Catch any other unexpected errors during text extraction.
        logging.error(f"Unexpected error in _get_text_from_response: {e}")
    
    # If we reach here, it means .text failed or was empty.
    # Log the full response object for complete debugging visibility.
    logging.warning(f"--- Response did not contain valid text. Full response object: {response} ---")
    
    # Return a helpful, accurate message to the user.
    return "[System Message: The model's response could not be processed. Please check the logs for details.]"


@log_exceptions
def get_initial_story(prompt):
    """Generates the initial story opening."""
    response = _call_gemini_api([prompt])
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story."""
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
    
    response = _call_gemini_api([full_prompt])
    return _get_text_from_response(response)
