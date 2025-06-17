import os
from google import genai
from google.genai import types
import logging
from decorators import log_exceptions
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONSTANTS ---
MODEL_NAME = 'gemini-2.5-flash-preview-05-20'
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
    full_prompt = f"{prompt}\n\n(Please keep the response to about {TARGET_WORD_COUNT} words.)"
    response = _call_gemini_api([full_prompt])
    return _get_text_from_response(response)

# --- THIS IS THE ONLY FUNCTION THAT HAS BEEN CHANGED ---
@log_exceptions
def continue_story(user_input, mode, story_context):
    """Generates the next part of the story by concatenating the chat history."""
    
    # 1. Take only the most recent turns from the full story context.
    recent_context = story_context[-HISTORY_TURN_LIMIT:]
    
    # 2. Build a single context string from the history.
    history_parts = []
    for entry in recent_context:
        actor_label = "Story" if entry.get('actor') == 'gemini' else "You"
        history_parts.append(f"{actor_label}: {entry.get('text')}")
    
    context_string = "\n\n".join(history_parts)

    # 3. Create the final prompt for the current user turn.
    if mode == 'character':
        prompt_template = "Acting as the main character {user_input}. Continue the story in about {word_count} words."
    else: # god mode
        prompt_template = "{user_input}. Continue the story in about {word_count} words."

    current_prompt_text = prompt_template.format(user_input=user_input, word_count=TARGET_WORD_COUNT)

    # 4. Combine the context and the current prompt into one large string.
    full_prompt = f"CONTEXT:\n{context_string}\n\nYOUR TURN:\n{current_prompt_text}"
    
    # 5. Call the API helper with the single, concatenated prompt string.
    response = _call_gemini_api([full_prompt])
    return _get_text_from_response(response)

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
    
    # --- Turn 1: Initial Story ---
    print("\n--- Turn 1: get_initial_story ---")
    turn_1_prompt = "start a story about a haunted lighthouse"
    print(f"Using prompt: '{turn_1_prompt}'")
    turn_1_response = get_initial_story(turn_1_prompt)
    print("\n--- LIVE RESPONSE 1 ---")
    print(turn_1_response)
    print("--- END OF RESPONSE 1 ---\n")
    
    # Create the initial history from the real response
    history = [{'actor': 'user', 'text': turn_1_prompt}, {'actor': 'gemini', 'text': turn_1_response}]

    # --- Turn 2: Continue Story ---
    print("\n--- Turn 2: continue_story ---")
    turn_2_prompt = "A lone ship, tossed by the raging sea, sees a faint, flickering light from the abandoned tower."
    print(f"Using prompt: '{turn_2_prompt}'")
    turn_2_response = continue_story(turn_2_prompt, 'god', history)
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
    turn_3_response = continue_story(turn_3_prompt, 'god', history)
    print("\n--- LIVE RESPONSE 3 ---")
    print(turn_3_response)
    print("--- END OF RESPONSE 3 ---\n")
