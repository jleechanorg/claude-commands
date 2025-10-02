FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application into a package directory so absolute imports like
# `from mvp_site import ...` continue to work in production images.
COPY . /app/mvp_site

# Ensure Python can resolve the `mvp_site` package when executed from the
# package directory.
ENV PYTHONPATH=/app

WORKDIR /app/mvp_site

# --- THIS IS THE FIX ---
# We've added the --timeout flag and set it to 300 seconds.
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--timeout", "300", "main:create_app()"]
