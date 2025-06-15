import os
from flask import Flask, render_template
from datetime import datetime
import pytz

app = Flask(__name__)

@app.route("/")
def home():
    utc_time = datetime.now(pytz.utc)
    pacific_time = utc_time.astimezone(pytz.timezone('US/Pacific'))
    template_data = {
        'server_time': pacific_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        'page_title': 'World Architecture AI (jlc)'
    }
    return render_template('index.html', **template_data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
