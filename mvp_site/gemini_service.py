import os
import google.generativeai as genai
import logging
from decorators import log_exceptions

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')

@log_exceptions
def get_initial_story(prompt):
    """Generates the initial story opening from a user's prompt."""
    response = model.generate_content(prompt)
    return response.text

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story based on context."""
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
