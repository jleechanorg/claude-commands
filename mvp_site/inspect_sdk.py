import logging
import os
import sys

# --- API KEY LOADING ---
# Look for Google API key in home directory first, then project root
try:
    home_key_path = os.path.expanduser("~/.gemini_api_key.txt")
    project_key_path = 'gemini_api_key.txt'

    if os.path.exists(home_key_path):
        with open(home_key_path, 'r') as f:
            api_key = f.read().strip()
        logging.info(f"Loaded API key from {home_key_path}")
    elif os.path.exists(project_key_path):
        with open(project_key_path, 'r') as f:
            api_key = f.read().strip()
        logging.info(f"Loaded API key from {project_key_path}")
    else:
        logging.error("API key not found in ~/.gemini_api_key.txt or gemini_api_key.txt")
        sys.exit(1)

    os.environ["GEMINI_API_KEY"] = api_key
except Exception as e:
    logging.error(f"Failed to load API key: {e}")
    sys.exit(1)

# Now that the environment is set, we can safely import our service.
import gemini_service

# Get the client object
client = gemini_service.get_client()

# --- This is how you can check for yourself ---
# Print the official help documentation for the method we are using.
logging.info("Official SDK Documentation for client.models.generate_content")
help(client.models.generate_content)
