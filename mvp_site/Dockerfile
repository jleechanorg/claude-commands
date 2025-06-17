FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# --- THIS IS THE FIX ---
# We've added the --timeout flag and set it to 300 seconds.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "main:app"]
