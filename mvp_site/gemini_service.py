import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONSTANTS ---
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
    global _client
    if _client is None:
        logging.info("--- Initializing Gemini Client ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY not found!")
        _client = genai.Client(api_key=api_key)
        logging.info("--- Gemini Client Initialized ---")
    return _client

def _call_gemini_api(prompt_contents):
    client = get_client()
    logging.info(f"--- Calling Gemini API with prompt: {str(prompt_contents)[:300]}... ---")
    
    # --- THIS IS THE FIX ---
    # `tool_config` is a valid parameter, but it must be passed INSIDE the
    # GenerateContentConfig object, not as a top-level argument.
    tool_config = types.ToolConfig(function_calling_config=types.FunctionCallingConfig(mode='none'))

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt_contents,
        config=types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            safety_settings=SAFETY_SETTINGS,
            tool_config=tool_config  # Correctly placed inside 'config'
        )
    )
    return response

def _get_text_from_response(response):
    try:
        return response.text
    except ValueError as e:
        logging.warning(f"ValueError while extracting text: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in _get_text_from_response: {e}")
    
    logging.warning(f"--- Response did not contain valid text. Full response object: {response} ---")
    return "[System Message: The model's response could not be processed. Please check the logs for details.]"

@log_exceptions
def get_initial_story(prompt):
    response = _call_gemini_api([prompt])
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context):
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
