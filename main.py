import os
import google.generativeai as genai
from flask import Flask, render_template
import traceback

app = Flask(__name__)

@app.route("/")
def home():
    gemini_response = ""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")
        
        genai.configure(api_key=api_key)
        
        # *** THE FIX: Using the correct Gemini 2.5 Pro Preview model name ***
        model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
        
        app.logger.info("Making request to Gemini 2.5 Pro...")
        response = model.generate_content("whats the weather today")
        gemini_response = response.text
        app.logger.info("Successfully received response from Gemini.")

    except Exception as e:
        gemini_response = traceback.format_exc()
        app.logger.error(f"Full traceback:\n{gemini_response}")

    template_data = {
        'page_title': 'World Architecture AI - Gemini 2.5 Pro',
        'gemini_weather': gemini_response
    }
    return render_template('index.html', **template_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
