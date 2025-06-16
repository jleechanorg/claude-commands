import os
import google.generativeai as genai
import logging
from decorators import log_exceptions

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Defer model initialization to a global variable
_model = None

def get_model():
    """
    Initializes and returns the Gemini model.
    This function is now fully robust with its own try/except block.
    """
    global _model
    if _model is None:
        try:
            logging.info("--- Initializing Gemini Model for the first time ---")
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found in the deployed container!")
            
            genai.configure(api_key=api_key)
            _model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
            logging.info("--- Gemini Model Initialized Successfully ---")
        except Exception as e:
            logging.error(f"--- FAILED to initialize Gemini Model: {e} ---")
            raise
    return _model

@log_exceptions
def get_initial_story(prompt):
    """Generates the initial story opening from a user's prompt."""
    model = get_model()
    response = model.generate_content(prompt)
    return response.text

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story based on context."""
    model = get_model()
    last_gemini_response = ""
    for entry in reversed(story_context):
        if entry.get('actor') == 'gemini':
            last_gemini_response = entry.get('text', '')
            break

    if mode == 'character':
        prompt_template = "Character does {user_input}. \n\n context: {last_gemini_response}. Continue the story."
    elif mode == 'god':
        prompt_template = "{user_input}. \n\n context: {last_gemini_response}"
    else:
        raise ValueError("Invalid interaction mode specified.")

    full_prompt = prompt_template.format(user_input=user_input, last_gemini_response=last_gemini_response)
    response = model.generate_content(full_prompt)
    return response.text
