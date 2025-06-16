import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def get_initial_story(prompt):
    """Generates the initial story opening from a user's prompt."""
    full_prompt = f"You are a master storyteller. Start a new, exciting, and engaging fantasy RPG campaign based on this user's prompt: '{prompt}'. Describe the opening scene and setting in detail, and end by asking the player character, 'What do you do?'"
    response = model.generate_content(full_prompt)
    return response.text

def continue_story(user_input, mode, story_context):
    """Generates the next part of the story based on context."""
    last_gemini_response = ""
    for entry in reversed(story_context):
        if entry.get('actor') == 'gemini':
            last_gemini_response = entry.get('text', '')
            break

    if mode == 'character':
        prompt_template = "Character does {user_input}. The last thing that happened was: {last_gemini_response}. Continue the story."
    elif mode == 'god':
        prompt_template = "God does {user_input}. The last thing that happened was: {last_gemini_response}. Continue the story."
    else:
        raise ValueError("Invalid interaction mode specified.")

    full_prompt = prompt_template.format(user_input=user_input, last_gemini_response=last_gemini_response)
    
    response = model.generate_content(full_prompt)
    return response.text
