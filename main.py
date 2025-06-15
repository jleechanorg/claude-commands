import os
import google.generativeai as genai
from flask import Flask, render_template

# Get an instance of the logger
app = Flask(__name__)

@app.route("/")
def home():
    gemini_response = ""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            app.logger.error("GEMINI_API_KEY not set in environment.")
            raise ValueError("GEMINI_API_KEY not set in environment.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        request_options = {'timeout': 20}
        
        app.logger.info("Making request to Gemini API...")
        response = model.generate_content(
            "whats the weather today",
            request_options=request_options
        )
        gemini_response = response.text
        app.logger.info("Successfully received response from Gemini.")

    except Exception as e:
        app.logger.error(f"An error occurred while calling Gemini API: {e}", exc_info=True)
        gemini_response = f"Error: Could not get a response from Gemini. Please check the server logs."

    template_data = {
        'page_title': 'World Architecture AI - Powered by Gemini',
        'gemini_weather': gemini_response
    }
    return render_template('index.html', **template_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
