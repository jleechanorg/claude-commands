FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY mvp_site/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the infrastructure package (required by gunicorn.conf.py)
COPY infrastructure/ /app/infrastructure/

# Copy the application into a package directory so absolute imports like
# `from mvp_site import ...` continue to work in production images.
COPY mvp_site/ /app/mvp_site/

# Copy world data to be accessible by mvp_site/world_loader.py
COPY world/ /app/mvp_site/world/


# Ensure Python can resolve both `mvp_site` and `infrastructure` packages
ENV PYTHONPATH=/app

WORKDIR /app/mvp_site

# Production-optimized Gunicorn configuration with gthread workers
# Configuration file provides: workers, threads, timeout, logging, and lifecycle management
# Performance: 12+ concurrent requests vs 1 request with default sync worker
# Requires infrastructure package for worker configuration helpers
CMD ["gunicorn", "-c", "gunicorn.conf.py", "main:create_app()"]
