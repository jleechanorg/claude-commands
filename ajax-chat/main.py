import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
import time
import traceback

app = Flask(__name__)

# This route serves the main HTML page. It loads instantly.
@app.route("/")
def home():
    return render_template('index.html')

# This is the new API endpoint that our JavaScript will call.
@app.route("/api/prompt", methods=['POST'])
def api_prompt():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({'error': 'No prompt provided.'}), 400
    
    user_prompt = data['prompt']
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set in environment.")
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        start_time = time.time()
        response = model.generate_content(user_prompt)
        end_time = time.time()
        
        latency = end_time - start_time
        
        # Return the result as a JSON object
        return jsonify({
            'response_text': response.text,
            'latency_seconds': f"{latency:.2f}"
        })

    except Exception as e:
        error_trace = traceback.format_exc()
        app.logger.error(f"Full traceback:\n{error_trace}")
        # Return a JSON object with the error
        return jsonify({'error': error_trace}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
