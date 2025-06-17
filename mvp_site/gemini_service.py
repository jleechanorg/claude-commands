import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONSTANTS ---
MODEL_NAME = 'gemini-1.5-flash-latest'
MAX_TOKENS = 8192
TEMPERATURE = 0.9
TARGET_WORD_COUNT = 400
HISTORY_TURN_LIMIT = 50
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
        logging.info("--- Initializing Gemini Client ---")
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("CRITICAL: GEMINI_API_KEY environment variable not found!")
        _client = genai.Client(api_key=api_key)
        logging.info("--- Gemini Client Initialized Successfully ---")
    return _client

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

@log_exceptions
def get_initial_story(prompt):
    """Generates the initial story opening."""
    client = get_client()
    # --- THIS IS THE FIX ---
    # 1. Instantiate the model directly.
    model = genai.GenerativeModel(MODEL_NAME)
    full_prompt = f"{prompt}\n\n(Please keep the response to about {TARGET_WORD_COUNT} words.)"
    logging.info(f"--- Calling model.generate_content for initial story. Prompt: {full_prompt[:200]}... ---")

    # 2. Call generate_content on the model instance.
    response = model.generate_content(
        contents=[full_prompt],
        generation_config=types.GenerationConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        ),
        safety_settings=SAFETY_SETTINGS
    )
    return _get_text_from_response(response)

@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story using a stateful ChatSession."""
    client = get_client()
    # --- THIS IS THE FIX ---
    # 1. Instantiate the model directly.
    model = genai.GenerativeModel(MODEL_NAME)
    recent_context = story_context[-HISTORY_TURN_LIMIT:]
    
    history = []
    for entry in recent_context:
        actor = 'user' if entry.get('actor') == 'user' else 'model'
        history.append({'role': actor, 'parts': [entry.get('text')]})

    # 2. Start a chat session from the model object.
    chat_session = model.start_chat(history=history)

    if mode == 'character':
        prompt_text = f"Acting as the main character {user_input}. Continue the story in about {TARGET_WORD_COUNT} words."
    else: # god mode
        prompt_text = f"{user_input}. Continue the story in about {TARGET_WORD_COUNT} words."
    
    logging.info(f"--- Sending message to chat session. Prompt: {prompt_text[:200]}... ---")

    # 3. Use the chat session's send_message method.
    response = chat_session.send_message(
        content=prompt_text,
        generation_config=types.GenerationConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=TEMPERATURE
        ),
        safety_settings=SAFETY_SETTINGS
    )
    return _get_text_from_response(response)

# --- Main block for rapid, direct testing ---
if __name__ == "__main__":
    print("--- Running gemini_service.py in direct test mode ---")
    
    try:
        with open('local_api_key.txt', 'r') as f:
            api_key = f.read().strip()
        os.environ["GEMINI_API_KEY"] = api_key
        print("Successfully loaded API key from local_api_key.txt")
    except FileNotFoundError:
        print("\nERROR: 'local_api_key.txt' not found.")
        sys.exit(1)
        
    print("\n--- Test Case 1: get_initial_story ---")
    test_prompt = "start a story about a haunted lighthouse"
    print(f"Using test prompt: '{test_prompt}'")
    initial_response = get_initial_story(test_prompt)
    print("\n--- LIVE RESPONSE ---")
    print(initial_response)
    print("--- END OF RESPONSE ---\n")
    
    print("\n--- Test Case 2: continue_story with history limit ---")
    mock_history = [{'actor': 'gemini', 'text': 'The old lighthouse stood on a jagged cliff, its light long extinguished.'}]
    
    next_input = "A lone ship, tossed by a sudden squall, sees a faint light from the abandoned tower."
    print(f"Using follow-up input: '{next_input}'")
    
    continue_response = continue_story(next_input, 'god', mock_history)
    print("\n--- LIVE RESPONSE ---")
    print(continue_response)
    print("--- END OF RESPONSE ---\n")
