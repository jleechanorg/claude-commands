import os
import google.generativeai as genai
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    gemini_response = ""
    try:
        # The API key is securely accessed from an environment variable.
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")
        
        genai.configure(api_key=api_key)

        # Create the model
        model = genai.GenerativeModel('gemini-pro')

        # Ask Gemini the question
        response = model.generate_content("whats the weather today")
        gemini_response = response.text

    except Exception as e:
        # If anything goes wrong, we'll show an error message.
        print(f"An error occurred: {e}")
        gemini_response = f"Error: Could not get a response from Gemini. {e}"

    template_data = {
        'page_title': 'World Architecture AI - Powered by Gemini',
        'gemini_weather': gemini_response
    }
    return render_template('index.html', **template_data)

if __name__ == "__main__":
    # For local testing, you would set the GEMINI_API_KEY environment variable.
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
