"""
Gunicorn configuration for WorldArchitect.AI production deployment
Optimized for I/O-bound workloads (MCP, Firestore, Gemini API calls)

This configuration uses gthread workers for improved concurrency while maintaining
compatibility with all Python libraries (Firebase, Firestore, Gemini SDK).

Performance Improvement:
- Before: 1 worker (sync) = 1 concurrent request
- After: (2*CPU+1) workers × 4 threads = 12+ concurrent requests on 1 CPU

Note: Worker and thread configuration logic has been extracted to infrastructure package
for testability and reusability across the project.
"""

import os
import sys

# Import worker configuration from infrastructure package
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
from infrastructure import worker_config

# Centralized timeout (mirrors scripts/timeout_config.sh)
# Fail fast if env var is set to invalid value - config errors should crash
_request_timeout_env = os.environ.get("WORLDARCH_TIMEOUT_SECONDS", "600")
REQUEST_TIMEOUT_SECONDS = int(_request_timeout_env)  # Raises ValueError if invalid

# Server socket
# Cloud Run provides the PORT environment variable - must use it
bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
backlog = 2048  # Maximum number of pending connections

# Worker processes
# Calculated by worker_config library with environment-aware defaults:
# - preview environment: 1 worker (512MB memory constraint)
# - production: (2*CPU+1) workers
# - GUNICORN_WORKERS env var overrides both
workers = worker_config.get_workers()

# Worker class: gthread for threaded workers
# Each worker process has multiple threads for handling concurrent requests
worker_class = "gthread"

# Threads per worker
# Each thread can handle one request simultaneously
# Default: 4 threads, configurable via GUNICORN_THREADS env var
threads = worker_config.get_threads()

# Maximum number of simultaneous clients (only used by async workers)
worker_connections = 1000

# Worker lifecycle management
# Restart workers after handling this many requests (prevents memory leaks)
max_requests = 1000
# Add jitter to prevent all workers restarting simultaneously
max_requests_jitter = 50

# Timeouts
# Worker timeout - must be long enough for AI operations
# ⚠️ Keep this aligned with Cloud Run + load balancer + client timeouts (10 minutes/600s)
# to prevent premature termination of long-running Gemini/API calls. Do not lower without
# updating every layer and the associated tests/docs. Pulls from WORLDARCH_TIMEOUT_SECONDS
# so deployments using scripts/timeout_config.sh stay in sync with runtime behavior.
timeout = REQUEST_TIMEOUT_SECONDS  # 10 minutes for long-running Gemini/API calls
# Graceful shutdown timeout
graceful_timeout = 30
# Keep-alive connections
keepalive = 2

# Logging
accesslog = "-"  # Log to stdout (Cloud Run compatible)
errorlog = "-"  # Log to stderr (Cloud Run compatible)
loglevel = "info"
# Enhanced access log format with request duration
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "worldarchitect-gunicorn"

# Server mechanics
daemon = False  # Run in foreground (required for containers)
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Debugging (set via environment variable)
reload = os.getenv("GUNICORN_RELOAD", "False").lower() == "true"
reload_extra_files = []

# Security
limit_request_line = 4094  # Maximum size of HTTP request line
limit_request_fields = 100  # Maximum number of headers
limit_request_field_size = 8190  # Maximum size of header


def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Gunicorn master starting with configuration:")
    server.log.info(f"  Workers: {workers}")
    server.log.info(f"  Worker class: {worker_class}")
    server.log.info(f"  Threads per worker: {threads}")
    server.log.info(f"  Total concurrent requests: {workers * threads}")
    server.log.info(f"  Timeout: {timeout}s")


def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Gunicorn reloading workers")


def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received INT or QUIT signal")


def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received ABORT signal")
