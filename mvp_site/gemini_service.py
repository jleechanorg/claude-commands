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

# --- NEW: Helper function to centralize the API call ---
def _call_gemini_api(prompt_contents):
    """Calls the Gemini API with a given prompt and returns the response."""
    client = get_client()
    logging.info(f"--- Calling Gemini API with prompt: {str(prompt_contents)[:300]}... ---")
    
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_contents,
        config=types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            safety_settings=SAFETY_SETTINGS
        )
    )
    return response

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
    """Generates the initial story opening."""
    # REFACTORED: Use the new helper function
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
    
    # REFACTORED: Use the new helper function
    response = _call_gemini_api([full_prompt])
    return _get_text_from_response(response)
