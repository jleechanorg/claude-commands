import os
import sys

# --- THIS IS THE FIX ---
# First, load the API key from the local file and set the environment variable.
try:
    with open('local_api_key.txt', 'r') as f:
        api_key = f.read().strip()
    os.environ["GEMINI_API_KEY"] = api_key
except FileNotFoundError:
    print("ERROR: 'local_api_key.txt' not found.")
    sys.exit(1)

# Now that the environment is set, we can safely import our service.
import gemini_service

# Get the client object
client = gemini_service.get_client()

# --- This is how you can check for yourself ---
# Print the official help documentation for the method we are using.
print("\n--- Official SDK Documentation for client.models.generate_content ---\n")
help(client.models.generate_content)
