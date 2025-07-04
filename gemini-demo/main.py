import os
import google.generativeai as genai
from flask import Flask, render_template
import time
import traceback

app = Flask(__name__)

@app.route("/")
def home():
    gemini_response = ""
    latency_seconds = 0.0
    prompt_text = "whats the weather today in long beach california"

    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        start_time = time.time()
        app.logger.info("Making request to Gemini 2.5 Flash...")
        response = model.generate_content(prompt_text)
        end_time = time.time()
        latency_seconds = end_time - start_time
        
        gemini_response = response.text
        app.logger.info(f"Successfully received response from Gemini in {latency_seconds:.2f} seconds.")

    except Exception as e:
        gemini_response = traceback.format_exc()
        app.logger.error(f"Full traceback:\n{gemini_response}")

    template_data = {
        'page_title': 'World Architecture AI - Gemini 2.5 Flash',
        'gemini_weather': gemini_response,
        'prompt_text': prompt_text,
        'latency_seconds': f"{latency_seconds:.2f}"
    }
    return render_template('index.html', **template_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
