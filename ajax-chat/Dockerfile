# Use the official Python 3.13.3 image to match your environment
FROM python:3.13.3-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
# This is done first to leverage Docker's layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (main.py, templates folder)
COPY . .

# The command to run the application using Gunicorn.
# Cloud Run automatically sets the PORT environment variable.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
