import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def get_initial_story(prompt):
    """Generates the initial story opening from a user's prompt."""
    full_prompt = f"You are a master storyteller. Start a new, exciting, and engaging fantasy RPG campaign based on this user's prompt: '{prompt}'. Describe the opening scene and setting in detail, and end by asking the player character, 'What do you do?'"
    response = model.generate_content(full_prompt)
    return response.text
