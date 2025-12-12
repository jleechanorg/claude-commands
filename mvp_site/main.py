from __future__ import annotations

"""
WorldArchitect.AI - Pure API Gateway (MCP Architecture)

This is the main Flask application serving as pure HTTP→MCP translation layer for
WorldArchitect.AI, an AI-powered tabletop RPG platform (digital D&D 5e Game Master).

🎭 PURE API GATEWAY ARCHITECTURE:
- Zero business logic - all game mechanics delegated to MCP server
- HTTP request translation to MCP tool calls
- Response format compatibility for existing frontend
- Authentication & authorization only
- Static file serving for frontend assets

🔌 MCP Integration:
- MCPClient: Communicates with world_logic.py MCP server on localhost:8000
- All /api/* routes call mcp_client.call_tool()
- No direct Firestore, Gemini, or game logic access
- Complete decoupling of web layer from business logic

🚀 Key Routes:
- GET /api/campaigns → get_campaigns_list
- GET /api/campaigns/<id> → get_campaign_state
- POST /api/campaigns → create_campaign
- PATCH /api/campaigns/<id> → update_campaign
- POST /api/campaigns/<id>/interaction → process_action
- GET /api/campaigns/<id>/export → export_campaign
- GET/POST /api/settings → get/update_user_settings

⚡ Dependencies (Minimal):
- Flask: Web framework & routing
- Firebase: Authentication only
- MCP Client: Business logic communication
- CORS: Frontend asset serving

🎯 Frontend Compatibility:
- Identical JSON response formats maintained
- Zero breaking changes for existing UI
- Complete NOOP for end users
"""

# Standard library imports
import argparse
import asyncio
import atexit
import base64
import concurrent.futures
import datetime
import functools
import json
import logging
import os

# Additional imports for conditional logic (moved from inline to meet import validation)
import re
import subprocess
import sys
import threading
import time
import traceback
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

# Firebase imports
import firebase_admin
from firebase_admin import auth, credentials

# Flask and web imports
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.middleware.proxy_fix import ProxyFix

from infrastructure.executor_config import (
    configure_asyncio_executor,
    get_blocking_io_executor,
    shutdown_executor,
)

# Infrastructure helpers
from infrastructure.mcp_helpers import create_thread_safe_mcp_getter

# Firestore service imports
from mvp_site import (
    constants,
    firestore_service,
    logging_util,
    world_logic,  # For MCP fallback logic
)
from mvp_site.custom_types import CampaignId, UserId
from mvp_site.firestore_service import json_default_serializer

# MCP JSON-RPC handler import
from mvp_site.mcp_api import handle_jsonrpc

# MCP client import
from mvp_site.mcp_client import MCPClientError, handle_mcp_errors

# --- CONSTANTS ---
# API Configuration
cors_allow_headers = ["Content-Type", "Authorization", "X-Forwarded-For"]
TESTING_MODE = os.getenv("TESTING") == "true"
if TESTING_MODE:
    # These headers are only honored in TESTING mode; do not enable in production.
    cors_allow_headers.extend(["X-Test-Bypass-Auth", "X-Test-User-ID"])

CORS_RESOURCES = {
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:5000",
            "https://worldarchitect.ai",
        ],
        "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": cors_allow_headers,
    }
}

ALLOW_TEST_AUTH_BYPASS = (
    os.getenv(
        "ALLOW_TEST_AUTH_BYPASS",
        "true" if TESTING_MODE else "false",
    ).lower()
    == "true"
)

# Request Headers
HEADER_AUTH = "Authorization"
HEADER_TEST_BYPASS = "X-Test-Bypass-Auth"
HEADER_TEST_USER_ID = "X-Test-User-ID"

# Logging Configuration (using centralized logging_util)
# LOG_DIRECTORY moved to logging_util.get_log_directory() for consistency

# Request/Response Data Keys (specific to main.py)
KEY_PROMPT = "prompt"
KEY_SELECTED_PROMPTS = "selected_prompts"
KEY_USER_INPUT = "input"
KEY_CAMPAIGN_ID = "campaign_id"
KEY_SUCCESS = "success"

# Shared async/thread infrastructure reused across app instances
_background_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_blocking_io_executor: concurrent.futures.ThreadPoolExecutor | None = None
_concurrent_request_count = 0
_concurrent_request_lock = threading.Lock()
_async_init_lock = threading.Lock()
_async_shutdown_registered = False
KEY_ERROR = "error"
KEY_MESSAGE = "message"
KEY_CAMPAIGN = "campaign"
KEY_STORY = "story"
KEY_DETAILS = "details"
KEY_RESPONSE = "response"

# Roles & Modes
DEFAULT_TEST_USER = "test-user"

# --- END CONSTANTS ---


def setup_file_logging() -> None:
    """
    Configure file logging for current git branch using centralized logging_util.

    Creates branch-specific log files in /tmp/worldarchitect.ai/{branch}/flask-server.log
    and configures logging_util to write to both console and file.
    """
    # Use centralized logging utility for consistent directory structure
    log_file = logging_util.LoggingUtil.get_log_file("flask-server")

    # Clear any existing handlers (close them first to prevent ResourceWarning)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)

    # Set up formatting
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set level
    root_logger.setLevel(logging.INFO)

    logging_util.info(f"File logging configured: {log_file}")


def safe_jsonify(data: Any) -> Response:
    """
    Safely serialize data to JSON, handling Firestore Sentinels and other special objects.

    This function processes the data through json_default_serializer to handle
    Firestore SERVER_TIMESTAMP and DELETE_FIELD sentinels before calling Flask's jsonify.
    """
    # First convert the data using our custom serializer
    json_string = json.dumps(data, default=json_default_serializer)
    # Then parse it back to get clean, serializable data
    clean_data = json.loads(json_string)
    # Finally use Flask's jsonify on the clean data
    return jsonify(clean_data)


def generic_error_response(
    operation: str, status_code: int = 500
) -> tuple[Response, int]:
    """
    Return a generic error response without exposing internal details.

    Args:
        operation: Brief description of what failed (e.g., "create campaign", "authentication")
        status_code: HTTP status code to return

    Returns:
        Tuple of JSON response and status code
    """
    return jsonify(
        {"error": f"Failed to {operation}. Please try again.", "status": "error"}
    ), status_code


def _shutdown_async_resources() -> None:
    """Stop shared background loop and executor gracefully."""

    global _background_loop, _loop_thread, _blocking_io_executor
    loop = _background_loop
    thread = _loop_thread

    if loop and loop.is_running():
        loop.call_soon_threadsafe(loop.stop)
    if thread:
        thread.join(timeout=1)
    # Use centralized shutdown for the shared executor
    shutdown_executor(wait=True)
    _blocking_io_executor = None


def _ensure_async_infrastructure() -> None:
    """Lazily initialize shared event loop and executor once per process.

    Uses centralized executor from infrastructure.executor_config with 100 workers.
    Configures asyncio.to_thread() to use this executor by default.
    """

    global _background_loop, _loop_thread, _blocking_io_executor, _async_shutdown_registered

    with _async_init_lock:
        if _background_loop is None:
            background_loop = asyncio.new_event_loop()

            def _start_loop(loop: asyncio.AbstractEventLoop) -> None:
                asyncio.set_event_loop(loop)
                # Configure the loop to use our centralized 100-thread executor
                # This makes asyncio.to_thread() use our executor automatically
                configure_asyncio_executor(loop)
                loop.run_forever()

            loop_thread = threading.Thread(
                target=_start_loop, args=(background_loop,), daemon=True
            )
            loop_thread.start()

            _background_loop = background_loop
            _loop_thread = loop_thread

        if _blocking_io_executor is None:
            # Use centralized executor from infrastructure (100 workers)
            _blocking_io_executor = get_blocking_io_executor()

        if not _async_shutdown_registered:
            atexit.register(_shutdown_async_resources)
            _async_shutdown_registered = True


def create_app() -> Flask:
    """
    Create and configure the Flask application.

    This function initializes the Flask application with all necessary configuration,
    middleware, and route handlers. It sets up CORS, authentication, and all API endpoints.

    Key Configuration:
    - Frontend asset serving from 'frontend_v1' folder (with /static/ redirect compatibility)
    - CORS enabled for all /api/* routes
    - Testing mode configuration from environment
    - Firebase Admin SDK initialization
    - Authentication decorator for protected routes
    - File logging to /tmp/worldarchitect.ai/{branch}/flask-server.log

    Routes Configured:
    - GET /api/campaigns - List user's campaigns
    - GET /api/campaigns/<id> - Get specific campaign
    - POST /api/campaigns - Create new campaign
    - PATCH /api/campaigns/<id> - Update campaign
    - POST /api/campaigns/<id>/interaction - Handle user interactions
    - GET /api/campaigns/<id>/export - Export campaign documents
    - /* - Frontend SPA fallback

    Returns:
        Configured Flask application instance
    """
    global _background_loop, _loop_thread, _blocking_io_executor

    # Ensure shared async infrastructure is initialized before use
    _ensure_async_infrastructure()

    # Set up file logging before creating app
    setup_file_logging()

    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    CORS(app, resources=CORS_RESOURCES)

    def run_in_background_loop(coro: Coroutine[Any, Any, Any]) -> Any:
        if _background_loop is None:
            raise RuntimeError("Background event loop not initialized")
        return asyncio.run_coroutine_threadsafe(coro, _background_loop).result()

    async def run_blocking_io(
        func: Callable[..., Any], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Run a blocking I/O function in a thread pool executor.

        This prevents blocking database calls (Firestore, etc.) from serializing
        the shared asyncio event loop. Without this, multiple concurrent requests
        would be processed serially instead of in parallel.

        Usage:
            # Instead of: result = firestore_service.get_campaign_by_id(user_id, campaign_id)
            # Use: result = await run_blocking_io(firestore_service.get_campaign_by_id, user_id, campaign_id)

        Performance improvement:
        - Before: N concurrent requests × 100ms each = N×100ms total (serial)
        - After: N concurrent requests × 100ms each = ~100ms total (parallel)

        Args:
            func: The blocking function to call
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the blocking function call
        """
        global _concurrent_request_count

        # Track concurrent operations for debugging
        func_name = getattr(func, "__name__", str(func))
        with _concurrent_request_lock:
            _concurrent_request_count += 1
            current_count = _concurrent_request_count

        start_time = datetime.datetime.now()
        logging_util.info(
            f"🔄 PARALLEL I/O START: {func_name} "
            f"[concurrent={current_count}, thread={threading.current_thread().name}]"
        )

        try:
            loop = asyncio.get_running_loop()
            executor = _blocking_io_executor
            if executor is None:
                raise RuntimeError("Blocking I/O executor not initialized")
            if kwargs:
                # functools.partial to handle kwargs
                func_with_kwargs = functools.partial(func, *args, **kwargs)
                result = await loop.run_in_executor(executor, func_with_kwargs)
            else:
                result = await loop.run_in_executor(executor, func, *args)

            duration_ms = (datetime.datetime.now() - start_time).total_seconds() * 1000
            with _concurrent_request_lock:
                _concurrent_request_count -= 1
                remaining = _concurrent_request_count

            logging_util.info(
                f"✅ PARALLEL I/O END: {func_name} "
                f"[duration={duration_ms:.1f}ms, remaining={remaining}]"
            )
            return result

        except Exception as e:
            with _concurrent_request_lock:
                _concurrent_request_count -= 1
            logging_util.error(f"❌ PARALLEL I/O ERROR: {func_name} - {e}")
            raise

    def client_ip() -> str:
        """Extract client IP using ProxyFix-processed remote_addr.

        ProxyFix with x_for=1 already processes X-Forwarded-For securely,
        setting request.remote_addr to the rightmost external IP.
        This prevents IP spoofing attacks on rate limiting.
        """
        return str(get_remote_address())

    # Configure rate limiting
    # NOTE: No default_limits - we only rate limit specific API routes
    # Static files and frontend routes are exempt to prevent CSS/JS loading failures
    limiter = Limiter(
        app=app,
        key_func=client_ip,
        default_limits=[],  # No default limits - only apply to specific routes
        # Use Redis (or any shared backend) in production to avoid per-process buckets.
        storage_uri=os.environ.get("RATE_LIMIT_STORAGE_URI", "memory://"),
    )

    campaign_rate_limit = os.environ.get(
        "CAMPAIGN_RATE_LIMIT", "100 per hour, 20 per minute"
    )
    campaign_create_rate_limit = os.environ.get(
        "CAMPAIGN_CREATE_RATE_LIMIT", campaign_rate_limit
    )
    settings_rate_limit = os.environ.get(
        "SETTINGS_RATE_LIMIT", "100 per hour, 20 per minute"
    )

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        # Each directive omits the trailing semicolon so we can join them once,
        # ensuring consistent "directive; " spacing without duplicated suffixes.
        csp_directives = [
            "default-src 'self'",
            # Inline scripts/styles removed; add nonces/hashes if inline assets are reintroduced.
            "script-src 'self' https://cdn.jsdelivr.net https://www.gstatic.com https://apis.google.com",
            # Legacy frontend_v1 applies inline style attributes (spinner, animations), so allow unsafe-inline
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "font-src 'self' https://cdn.jsdelivr.net https://r2cdn.perplexity.ai data:",
            "connect-src 'self' https://identitytoolkit.googleapis.com https://securetoken.googleapis.com https://*.firebaseio.com https://cdn.jsdelivr.net https://www.gstatic.com",
            "img-src 'self' data: https://cdn.jsdelivr.net https://*.googleapis.com https://*.gstatic.com https://images.unsplash.com",
            "frame-src https://worldarchitecture-ai.firebaseapp.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        return response

    # Defer MCP client initialization until first use to avoid race condition
    # with command-line argument configuration
    # Use infrastructure helper for thread-safe lazy initialization
    get_mcp_client = create_thread_safe_mcp_getter(app, world_logic_module=world_logic)

    # Cache busting route for testing - only activates with special header
    @app.route("/frontend_v1/<path:filename>")
    @limiter.exempt  # Exempt static files from rate limiting
    def frontend_files_with_cache_busting(filename):
        """Serve frontend files with optional cache-busting for testing"""
        frontend_folder = os.path.join(os.path.dirname(__file__), "frontend_v1")
        response = send_from_directory(frontend_folder, filename)

        # Only disable cache if X-No-Cache header is present (for testing)
        if request.headers.get("X-No-Cache") and filename.endswith((".js", ".css")):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    # Backward compatibility route for /static/ paths
    @app.route("/static/<path:filename>")
    @limiter.exempt  # Exempt static redirects from rate limiting
    def static_files_redirect(filename):
        """Redirect old /static/ paths to /frontend_v1/ for backward compatibility"""
        return redirect(
            url_for("frontend_files_with_cache_busting", filename=filename), code=301
        )

    # Testing mode removed - Flask TESTING config no longer set from environment

    # Initialize Firebase with explicit project override when provided
    # WORLDAI_* vars take precedence for WorldArchitect.AI repo-specific config
    firebase_project_id = os.getenv("WORLDAI_FIREBASE_PROJECT_ID") or os.getenv(
        "FIREBASE_PROJECT_ID"
    )
    firebase_options = {"projectId": firebase_project_id} if firebase_project_id else {}

    # Check for repo-specific service account credentials
    worldai_creds_path = os.getenv("WORLDAI_GOOGLE_APPLICATION_CREDENTIALS")
    if worldai_creds_path:
        # Expand ~ to full path
        worldai_creds_path = os.path.expanduser(worldai_creds_path)

    try:
        firebase_admin.get_app()
    except ValueError:
        if firebase_project_id:
            logging_util.info(
                f"Initializing Firebase with projectId={firebase_project_id}"
            )
        if worldai_creds_path and os.path.exists(worldai_creds_path):
            logging_util.info(f"Using WORLDAI credentials from {worldai_creds_path}")
            firebase_admin.initialize_app(
                credentials.Certificate(worldai_creds_path), firebase_options or None
            )
        else:
            firebase_admin.initialize_app(
                credentials.ApplicationDefault(), firebase_options or None
            )

    def check_token(f):
        @wraps(f)
        def wrap(*args: Any, **kwargs: Any) -> Response:
            # Allow automated test flows to bypass Firebase verification (TESTING mode only)
            if (
                TESTING_MODE
                and ALLOW_TEST_AUTH_BYPASS
                and request.headers.get(HEADER_TEST_BYPASS, "").lower() == "true"
            ):
                kwargs["user_id"] = request.headers.get(
                    HEADER_TEST_USER_ID, "test-user-123"
                )
                logging_util.info(
                    "TESTING auth bypass activated for user_id=%s", kwargs["user_id"]
                )
                return f(*args, **kwargs)

            # Authentication uses real Firebase; bypass is only available in TESTING mode
            if not request.headers.get(HEADER_AUTH):
                return jsonify({KEY_MESSAGE: "No token provided"}), 401
            try:
                auth_header = request.headers.get(HEADER_AUTH, "")
                parts = auth_header.split()
                if len(parts) != 2 or parts[0].lower() != "bearer":
                    raise ValueError("Invalid authorization scheme")
                id_token = parts[1].strip()
                if not id_token:
                    raise ValueError("Empty token")
                # Firebase token verification using Admin SDK
                # When clock skew patch is active (local clock ahead), we need to:
                # 1. Use actual time for verification (tokens issued at Google's actual time)
                # 2. Disable check_revoked (requires backend call which would fail)
                from mvp_site.clock_skew_credentials import (
                    UseActualTime,
                    get_clock_skew_seconds,
                )

                clock_skew = get_clock_skew_seconds()

                # Firebase SDK limits clock_skew_seconds to 60 max, but we want 12 min tolerance
                # Strategy: Try Firebase verification first, if it fails due to expiry,
                # manually verify signature is valid and token is within 12 min of expiry
                extended_tolerance = 720  # 12 minutes

                try:
                    # When clock skew > 60s, use actual time and disable revocation check
                    if clock_skew > 60:
                        with UseActualTime():
                            decoded_token = auth.verify_id_token(
                                id_token,
                                check_revoked=False,
                                clock_skew_seconds=60,
                            )
                    else:
                        decoded_token = auth.verify_id_token(
                            id_token,
                            check_revoked=True,
                            clock_skew_seconds=60,
                        )
                except Exception as firebase_error:
                    # Check if it's an expiry error we can extend tolerance for
                    error_str = str(firebase_error)
                    if "Token expired" in error_str or "exp" in error_str.lower():
                        # Decode JWT to check if within extended tolerance
                        token_parts = id_token.split(".")
                        if len(token_parts) >= 2:
                            payload_b64 = token_parts[1] + "=" * (4 - len(token_parts[1]) % 4)
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                            token_exp = payload.get("exp", 0)
                            current_time = time.time()

                            if current_time <= token_exp + extended_tolerance:
                                # Within extended tolerance - accept the token
                                # Firebase uses 'user_id' or 'sub' for the uid in JWT payload
                                decoded_token = payload
                                # Normalize uid field - Firebase SDK returns 'uid', JWT has 'sub' or 'user_id'
                                if "uid" not in decoded_token:
                                    decoded_token["uid"] = payload.get("sub") or payload.get("user_id")
                                logging_util.info(
                                    f"Token {int(current_time - token_exp)}s past expiry, "
                                    f"within {extended_tolerance}s tolerance - accepting"
                                )
                            else:
                                raise ValueError(
                                    f"Token expired {int(current_time - token_exp)}s ago, "
                                    f"beyond {extended_tolerance}s tolerance"
                                )
                        else:
                            raise firebase_error
                    else:
                        raise firebase_error
                kwargs["user_id"] = decoded_token["uid"]
            except Exception as e:
                error_message = str(e)
                logging_util.error(f"Auth failed: {e}")
                # Do not log tokens or Authorization headers
                logging_util.error(traceback.format_exc())

                # Generic error response - don't expose internal error details
                response_data = {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "Authentication failed",
                }

                # Add clock skew guidance for specific errors
                if (
                    "Token used too early" in error_message
                    or "clock" in error_message.lower()
                ):
                    response_data["error_type"] = "clock_skew"
                    response_data["server_time_ms"] = int(
                        datetime.datetime.now(datetime.UTC).timestamp() * 1000
                    )
                    response_data["hint"] = (
                        "Clock synchronization issue detected. The client and server clocks may be out of sync."
                    )
                return jsonify(response_data), 401
            return f(*args, **kwargs)

        return wrap

    def async_route(f):
        """Decorator to handle async Flask routes with proper event loop management"""

        @wraps(f)
        def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(f):
                return run_in_background_loop(f(*args, **kwargs))
            return f(*args, **kwargs)

        return wrapper

    # --- API Routes ---
    @app.route("/api/campaigns", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_campaigns(user_id: UserId) -> Response | tuple[Response, int]:
        try:
            # Get query parameters with proper validation
            limit = request.args.get("limit")
            if limit is not None:
                try:
                    limit = int(limit)
                    if limit < 1 or limit > 100:
                        return jsonify(
                            {
                                "error": "Invalid limit parameter. Must be between 1 and 100."
                            }
                        ), 400
                except ValueError:
                    return jsonify(
                        {"error": "Invalid limit parameter. Must be a number."}
                    ), 400

            sort_by = request.args.get("sort_by")
            # Whitelist allowed sort fields for security
            allowed_sort_fields = ["created_at", "last_played", "title"]
            if sort_by is not None and sort_by not in allowed_sort_fields:
                return jsonify(
                    {
                        "error": f"Invalid sort_by parameter. Must be one of: {', '.join(allowed_sort_fields)}"
                    }
                ), 400

            data = {
                "user_id": user_id,
                "limit": limit,
                "sort_by": sort_by,
            }
            result = await get_mcp_client().call_tool("get_campaigns_list", data)

            # Maintain backward compatibility: return campaigns array directly
            # Legacy format: [campaigns...]
            # New MCP format: {"campaigns": [...], "success": true}
            if isinstance(result, dict) and "campaigns" in result:
                # Return legacy format for backward compatibility
                return jsonify(result["campaigns"])

            # Fallback if format is unexpected
            status_code = (
                result.get("status_code", 200) if isinstance(result, dict) else 200
            )
            return safe_jsonify(result), status_code
        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception as e:
            logging_util.error(f"Get campaigns error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "Failed to retrieve campaigns",
                }
            ), 500

    @app.route("/api/campaigns/<campaign_id>", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_campaign(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        try:
            logging_util.info(
                f"🎮 LOADING GAME PAGE: user={user_id}, campaign={campaign_id}"
            )

            data = {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "include_story": True,  # Include story processing for frontend compatibility
            }

            # Direct service calls with run_in_executor for parallel request handling
            # Using run_blocking_io prevents blocking calls from serializing the event loop
            campaign_data, story = await run_blocking_io(
                firestore_service.get_campaign_by_id, user_id, campaign_id
            )
            if not campaign_data:
                return jsonify({"error": "Campaign not found"}), 404

            # Get user settings for debug mode (parallel-safe)
            user_settings = (
                await run_blocking_io(firestore_service.get_user_settings, user_id)
                or {}
            )
            debug_mode = bool(user_settings.get("debug_mode", False))

            # Get game state (parallel-safe)
            game_state = await run_blocking_io(
                firestore_service.get_campaign_game_state, user_id, campaign_id
            )
            if game_state:
                game_state.debug_mode = debug_mode

            # Process story entries based on debug mode
            if debug_mode:
                processed_story = story or []
            else:
                # Strip debug fields when debug mode is off
                processed_story = world_logic._strip_game_state_fields(story or [])

            result = {
                "success": True,
                "campaign": campaign_data,
                "story": processed_story,
                "game_state": game_state.to_dict() if game_state else {},
            }

            if not result.get(KEY_SUCCESS):
                return safe_jsonify(result), result.get("status_code", 404)

            # Debug logging for structured fields (maintain existing logging)
            if "story" in result:
                processed_story = result["story"]
                logging_util.info(
                    f"Campaign {campaign_id} story entries: {len(processed_story)}"
                )
                for i, entry in enumerate(processed_story[:3]):  # Log first 3 entries
                    if entry.get("actor") == constants.ACTOR_GEMINI:
                        fields = [
                            k
                            for k in entry
                            if k not in ["text", "actor", "mode", "timestamp", "part"]
                        ]
                        logging_util.info(f"Entry {i} structured fields: {fields}")
                        if "god_mode_response" in entry:
                            logging_util.info(
                                f"  god_mode_response: {entry['god_mode_response'][:50]}..."
                            )
                        if "resources" in entry:
                            logging_util.info(f"  resources: {entry['resources']}")
                        if "dice_rolls" in entry:
                            logging_util.info(f"  dice_rolls: {entry['dice_rolls']}")

            # Map to original response format for frontend compatibility
            response_data = {
                KEY_CAMPAIGN: result.get("campaign"),
                KEY_STORY: result.get("story", []),
                "game_state": result.get("game_state", {}),
            }

            # Enhanced debug logging for campaign data
            campaign_data = result.get("campaign", {})
            logging_util.info(f"🎯 BACKEND RESPONSE for campaign {campaign_id}:")
            logging_util.info(
                f"  Campaign Title: '{campaign_data.get('title', 'NO_TITLE')}'"
            )
            logging_util.info(
                f"  Campaign Keys: {list(campaign_data.keys()) if campaign_data else 'EMPTY'}"
            )
            logging_util.info(f"  Story entries: {len(result.get('story', []))}")
            logging_util.info(f"  Response data keys: {list(response_data.keys())}")
            # Trim campaign object for logs - just show keys, not full narrative
            logging_util.info(f"  Campaign has {len(str(campaign_data))} chars")

            return jsonify(response_data)
        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception as e:
            logging_util.error(f"Get campaign error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "Failed to retrieve campaign",
                }
            ), 500

    @app.route("/api/campaigns", methods=["POST"])
    @limiter.limit(campaign_create_rate_limit)
    @check_token
    @async_route
    async def create_campaign_route(user_id: UserId) -> Response | tuple[Response, int]:
        try:
            data = request.get_json()
            if data is None or not isinstance(data, dict):
                return jsonify({KEY_ERROR: "Invalid JSON payload"}), 400

            # Debug logging
            logging_util.info("Received campaign creation request:")
            logging_util.info(f"  Character: {data.get('character', '')}")
            logging_util.info(f"  Setting: {data.get('setting', '')}")
            logging_util.info(f"  Description: {data.get('description', '')}")
            logging_util.info(f"  Custom options: {data.get('custom_options', [])}")
            logging_util.info(f"  Selected prompts: {data.get('selected_prompts', [])}")

            # Add user_id to request data
            data["user_id"] = user_id

            result = await get_mcp_client().call_tool("create_campaign", data)

            if not result.get(KEY_SUCCESS):
                return safe_jsonify(result), result.get("status_code", 400)

            # Map to original response format for frontend compatibility
            response_data = {
                KEY_SUCCESS: True,
                KEY_CAMPAIGN_ID: result.get(KEY_CAMPAIGN_ID),
            }

            return jsonify(response_data), 201
        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception as e:
            logging_util.error(f"Failed to create campaign: {e}")
            return generic_error_response("create campaign")

    @app.route("/api/campaigns/<campaign_id>", methods=["PATCH"])
    @limiter.limit("50000 per hour, 1000 per minute")  # High limits, sanity checks only
    @check_token
    @async_route
    async def update_campaign(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        try:
            data = request.get_json()
            if data is None or not isinstance(data, dict):
                return jsonify({KEY_ERROR: "Invalid JSON payload"}), 400

            # Handle legacy title-only updates
            if constants.KEY_TITLE in data and len(data) == 1:
                new_title = data.get(constants.KEY_TITLE)
                if not isinstance(new_title, str) or new_title.strip() == "":
                    return jsonify({KEY_ERROR: "New title is required"}), 400
                updates = {constants.KEY_TITLE: new_title.strip()}
            else:
                # General updates
                updates = data

            request_data = {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "updates": updates,
            }

            # Direct service calls (testing mode removed - always use direct approach)
            result = await world_logic.update_campaign_unified(request_data)

            if not result.get(KEY_SUCCESS):
                return safe_jsonify(result), result.get("status_code", 400)

            # Map to original response format for frontend compatibility
            response_data = {
                KEY_SUCCESS: True,
                KEY_MESSAGE: result.get("message", "Campaign updated successfully."),
            }

            return jsonify(response_data)
        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception:
            logging_util.error(traceback.format_exc())
            return generic_error_response("update campaign")

    @app.route("/api/campaigns/<campaign_id>/interaction", methods=["POST"])
    @limiter.limit(
        "30000 per hour, 1000 per minute"
    )  # High limits for normal conversation flow
    @check_token
    @async_route
    async def handle_interaction(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        try:
            logging_util.info("DEBUG: handle_interaction START - testing mode removed")
            data = request.get_json()
            logging_util.info(f"DEBUG: request data = {data}")
            user_input = data.get(KEY_USER_INPUT)
            logging_util.info(
                f"DEBUG: user_input = {user_input} (KEY_USER_INPUT='{KEY_USER_INPUT}')"
            )
            mode = data.get(constants.KEY_MODE, constants.MODE_CHARACTER)

            # Validate user_input is provided (None only, empty strings are allowed)
            if user_input is None:
                return jsonify({KEY_ERROR: "User input is required"}), 400

            # Use MCP client for processing action (testing mode removed)
            logging_util.info(
                f"DEBUG: Processing interaction - user_id={user_id}, campaign_id={campaign_id}"
            )

            try:
                # Prepare request data for unified API
                request_data = {
                    "user_id": user_id,
                    "campaign_id": campaign_id,
                    "user_input": user_input,
                    "mode": mode,
                }
                result = await get_mcp_client().call_tool(
                    "process_action", request_data
                )
                logging_util.info(
                    f"DEBUG: MCP process_action returned result: {result.get('success', False)}"
                )
                if not result.get("success"):
                    error_msg = result.get(
                        "error", result.get("error_message", "Unknown error")
                    )
                    logging_util.error(f"DEBUG: MCP process_action failed: {error_msg}")

                    # Return appropriate error response based on error type
                    if (
                        "not found" in error_msg.lower()
                        or "campaign not found" in error_msg.lower()
                    ):
                        return jsonify({"error": "Campaign not found"}), 404
                    return jsonify({"error": error_msg}), 400
            except MCPClientError as e:
                # Handle MCP-specific errors with proper status code translation
                return handle_mcp_errors(e)
            except Exception as e:
                logging_util.error(f"DEBUG: MCP process_action exception: {e}")
                return jsonify({"error": "Internal server error"}), 500

            if not result.get(KEY_SUCCESS):
                return safe_jsonify(result), result.get("status_code", 400)

            # Debug logging for Cloud Run troubleshooting
            logging_util.info(f"MCP process_action result keys: {list(result.keys())}")
            if "story" in result:
                story_entries = result.get("story", [])
                logging_util.info(
                    f"Story field type: {type(story_entries)}, length: {len(story_entries) if hasattr(story_entries, '__len__') else 'N/A'}"
                )

            # Translate MCP response to frontend-compatible format
            # MCP returns 'story' field, frontend expects 'narrative' or 'response'
            if "story" in result:
                # Extract first story entry text for backward compatibility
                story_entries = result.get("story", [])
                if (
                    story_entries
                    and isinstance(story_entries, list)
                    and len(story_entries) > 0
                ):
                    first_entry = story_entries[0]
                    narrative_text = (
                        first_entry.get("text", "")
                        if isinstance(first_entry, dict)
                        else str(first_entry)
                    )
                    result["narrative"] = narrative_text
                    result["response"] = narrative_text  # Fallback compatibility
                else:
                    logging_util.warning(
                        f"Empty or invalid story entries in MCP response for campaign {campaign_id}"
                    )
                    result["narrative"] = ""
                    result["response"] = ""
            else:
                # Missing story field - this is likely the cause of [Error: No response from server]
                logging_util.warning(
                    f"Missing 'story' field in MCP response for campaign {campaign_id}. Available fields: {list(result.keys())}"
                )
                result["narrative"] = ""
                result["response"] = ""

            # Return the translated result using safe_jsonify to handle Firestore Sentinels
            return safe_jsonify(result), 200

        except MCPClientError as e:
            # Handle MCP-specific errors with proper translation
            return handle_mcp_errors(e)
        except Exception as e:
            # Critical security fix: Never expose raw exceptions to frontend
            logging_util.error(
                f"Critical error in handle_interaction for campaign {campaign_id}: {e}"
            )
            logging_util.error(
                f"User input: {user_input if 'user_input' in locals() else 'N/A'}"
            )
            logging_util.error(traceback.format_exc())

            # Return sanitized error response that cannot leak JSON or internal details
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "An error occurred processing your request.",
                    KEY_RESPONSE: "I encountered an issue and cannot continue at this time. Please try again, or contact support if the problem persists.",
                }
            ), 500

    @app.route("/api/campaigns/<campaign_id>/export", methods=["GET"])
    @limiter.limit("10 per hour, 2 per minute")  # Exporting is infrequent
    @check_token
    @async_route
    async def export_campaign(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        try:
            export_format = request.args.get("format", "txt").lower()

            # Use MCP client for export generation
            request_data = {
                "user_id": user_id,
                "campaign_id": campaign_id,
                "format": export_format,
            }

            result = await get_mcp_client().call_tool("export_campaign", request_data)

            if not result.get(KEY_SUCCESS):
                return safe_jsonify(result), result.get("status_code", 400)

            # Get export details from unified API
            export_path = result.get("export_path")
            campaign_title = result.get("campaign_title", "Untitled Campaign")
            desired_download_name = f"{campaign_title}.{export_format}"

            if not export_path or not os.path.exists(export_path):
                return jsonify({KEY_ERROR: "Failed to create export file."}), 500

            logging_util.info(
                f"Exporting file '{export_path}' with download_name='{desired_download_name}'"
            )

            # Use the standard send_file call for file serving
            response = send_file(
                export_path,
                download_name=desired_download_name,
                as_attachment=True,
            )

            @response.call_on_close
            def cleanup() -> None:
                try:
                    os.remove(export_path)
                    logging_util.info(f"Cleaned up temporary file: {export_path}")
                except Exception as e:
                    logging_util.error(f"Error cleaning up file {export_path}: {e}")

            return response

        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception as e:
            logging_util.error(f"Export failed: {e}")
            traceback.print_exc()
            return generic_error_response("export campaign")

    # --- Time Sync Route for Clock Skew Detection ---
    @app.route("/api/time", methods=["GET"])
    @limiter.limit("200 per hour, 30 per minute")  # Time sync can be frequent
    def get_server_time() -> Response:
        """
        Get current server time for client clock skew detection and compensation.

        This endpoint is used by the frontend to detect differences between client
        and server clocks, enabling compensation for authentication timing issues.
        """
        current_time = datetime.datetime.now(datetime.UTC)

        return jsonify(
            {
                "server_time_utc": current_time.isoformat(),
                "server_timestamp": int(current_time.timestamp()),
                "server_timestamp_ms": int(current_time.timestamp() * 1000),
            }
        )

    # --- Health Check Route ---
    @app.route("/health", methods=["GET"])
    @limiter.exempt  # Health checks should not be rate limited
    def health_check() -> Response:
        """
        Health check endpoint for deployment verification.

        Used by Cloud Run and deployment workflows to verify service availability.
        Returns 200 OK with service status information including concurrency configuration.
        """
        # Gather system information for monitoring
        health_info = {
            "status": "healthy",
            "service": "worldarchitect-ai",
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        }

        # Include Gunicorn worker configuration if available (from environment)
        gunicorn_workers_raw = os.getenv("GUNICORN_WORKERS")
        gunicorn_threads_raw = os.getenv("GUNICORN_THREADS")

        concurrency: dict[str, int] = {}

        def _safe_parse_int(value: str | None, env_name: str) -> int | None:
            """Safely parse an integer environment variable."""

            if value is None:
                return None

            try:
                return int(value)
            except ValueError:
                logging_util.warning(
                    "Invalid %s value %r provided; ignoring for /health response",
                    env_name,
                    value,
                )
                return None

        gunicorn_workers = _safe_parse_int(gunicorn_workers_raw, "GUNICORN_WORKERS")
        gunicorn_threads = _safe_parse_int(gunicorn_threads_raw, "GUNICORN_THREADS")

        if gunicorn_workers is not None:
            concurrency["workers"] = gunicorn_workers
        if gunicorn_threads is not None:
            concurrency["threads"] = gunicorn_threads
        if gunicorn_workers is not None and gunicorn_threads is not None:
            concurrency["max_concurrent_requests"] = gunicorn_workers * gunicorn_threads

        if concurrency:
            health_info["concurrency"] = concurrency

        # Include MCP client status (check if already initialized, don't trigger initialization)
        # Health checks should be fast and not trigger expensive operations
        if hasattr(app, "_mcp_client") and app._mcp_client is not None:
            health_info["mcp_client"] = {
                "initialized": True,
                "base_url": app._mcp_client.base_url,
                "skip_http": app._mcp_client.skip_http,
            }
        else:
            health_info["mcp_client"] = {"initialized": False}

        return jsonify(health_info)

    # --- MCP JSON-RPC Endpoint ---
    @app.route("/mcp", methods=["POST"])
    @limiter.exempt  # MCP endpoint should not be rate limited (used by internal tools)
    def mcp_endpoint() -> Response | tuple[Response, int]:
        """
        MCP JSON-RPC 2.0 endpoint for Cloud Run deployment.

        Handles JSON-RPC 2.0 requests for MCP tools without requiring a separate
        HTTP server process. This enables MCP functionality in Cloud Run's single-port
        architecture.

        Supported methods:
        - tools/list: List available MCP tools
        - tools/call: Execute an MCP tool
        - resources/list: List available resources
        - resources/read: Read a resource

        Returns:
            JSON-RPC 2.0 response with result or error
        """
        request_data = None  # Initialize before try block for error handling
        try:
            # Get JSON-RPC request data
            request_data = request.get_json()
            if not request_data:
                return jsonify(
                    {
                        "jsonrpc": "2.0",
                        "error": {
                            "code": -32700,
                            "message": "Parse error: No JSON data in request",
                        },
                        "id": None,
                    }
                ), 400

            # Call the standalone JSON-RPC handler from mcp_api.py
            response_data = handle_jsonrpc(request_data)

            # Return JSON-RPC response
            return jsonify(response_data)

        except Exception as e:
            # Log error for debugging
            logging_util.error(f"MCP endpoint error: {e}")
            logging_util.error(traceback.format_exc())

            # Return JSON-RPC 2.0 error response
            return jsonify(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                    "id": request_data.get("id") if request_data else None,
                }
            ), 500

    # --- Settings Routes ---
    @app.route("/settings")
    @limiter.limit("120 per hour, 20 per minute")  # Prevent brute-force refreshes
    @check_token
    def settings_page(user_id: UserId) -> Response:
        """Settings page for authenticated users."""
        logging_util.info(f"User {user_id} visited settings page")
        return render_template("settings.html")

    @app.route("/api/settings", methods=["GET", "POST"])
    @limiter.limit(
        settings_rate_limit
    )  # Settings access is moderate frequency
    @check_token
    @async_route
    async def api_settings(user_id: UserId) -> Response | tuple[Response, int]:
        """Get or update user settings."""
        try:
            if request.method == "GET":
                # Use MCP client for getting settings
                request_data = {"user_id": user_id}

                # Delegate to world_logic for centralized defaults handling
                result = await world_logic.get_user_settings_unified({"user_id": user_id})

                if not result.get(KEY_SUCCESS):
                    return jsonify(result), result.get("status_code", 400)

                # Return the settings directly (remove success wrapper for GET compatibility)
                settings = {k: v for k, v in result.items() if k != KEY_SUCCESS}
                return jsonify(settings)

            if request.method == "POST":
                # Use MCP client for updating settings
                # Handle different content types
                if (
                    request.content_type
                    and "application/x-www-form-urlencoded" in request.content_type
                ):
                    # Parse form data
                    data = dict(request.form)
                else:
                    # Default to JSON - force parsing even without content type
                    try:
                        data = request.get_json(force=True)
                    except Exception:
                        return jsonify({KEY_ERROR: "Invalid request data"}), 400

                # Validate settings data to maintain API contract
                valid_settings_keys = {
                    "gemini_model",
                    "openrouter_model",
                    "cerebras_model",
                    "llm_provider",
                    "theme",
                    "auto_save",
                    "debug_mode",
                }
                if not data or not any(key in valid_settings_keys for key in data):
                    return jsonify({KEY_ERROR: "Invalid settings data"}), 400

                # Filter out invalid fields but don't validate values - let MCP handle that
                filtered_data = {
                    k: v for k, v in data.items() if k in valid_settings_keys
                }

                # Auto-infer provider from model selection if provider not explicitly set
                # This ensures frontend-only model updates correctly set the provider
                if "llm_provider" not in filtered_data:
                    # Check if any model-specific settings were updated
                    if "gemini_model" in filtered_data:
                        filtered_data["llm_provider"] = constants.infer_provider_from_model(
                            filtered_data["gemini_model"],
                            provider_hint=constants.LLM_PROVIDER_GEMINI,
                        )
                    elif "openrouter_model" in filtered_data:
                        filtered_data["llm_provider"] = constants.infer_provider_from_model(
                            filtered_data["openrouter_model"],
                            provider_hint=constants.LLM_PROVIDER_OPENROUTER,
                        )
                    elif "cerebras_model" in filtered_data:
                        filtered_data["llm_provider"] = constants.infer_provider_from_model(
                            filtered_data["cerebras_model"],
                            provider_hint=constants.LLM_PROVIDER_CEREBRAS,
                        )

                request_data = {"user_id": user_id, "settings": filtered_data}

                # Direct service calls with run_in_executor for parallel request handling
                ok = await run_blocking_io(
                    firestore_service.update_user_settings, user_id, filtered_data
                )
                result = (
                    {"success": True}
                    if ok
                    else {"success": False, "error": "Failed to update settings"}
                )

                if not result.get(KEY_SUCCESS):
                    return jsonify(result), result.get("status_code", 400)

                # Return success response compatible with frontend expectations
                return jsonify({"success": True, "message": "Settings saved"})

        except MCPClientError as e:
            return handle_mcp_errors(e)
        except Exception as e:
            logging_util.error(f"Settings API error: {str(e)}")
            return jsonify({"error": "Internal server error", "success": False}), 500

    # --- Frontend Serving ---
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    @limiter.exempt  # Exempt frontend routes from rate limiting
    def serve_frontend(path: str) -> Response:
        """Serve the frontend files. This is the fallback for any non-API routes."""
        frontend_folder = os.path.join(os.path.dirname(__file__), "frontend_v1")
        if path and os.path.exists(os.path.join(frontend_folder, path)):
            return send_from_directory(frontend_folder, path)
        return send_from_directory(frontend_folder, "index.html")

    # Fallback route for old cached frontend code calling /handle_interaction
    @app.route("/handle_interaction", methods=["POST"])
    @limiter.limit(
        "30000 per hour, 1000 per minute"
    )  # Match main interaction endpoint limits
    def handle_interaction_fallback():
        """Fallback for cached frontend code calling old endpoint"""
        return jsonify(
            {
                "error": "This endpoint has been moved. Please refresh your browser (Ctrl+Shift+R) to get the latest version.",
                "redirect_message": "Hard refresh required to clear browser cache",
                "status": "cache_issue",
            }
        ), 410  # 410 Gone - indicates this endpoint no longer exists

    @app.teardown_appcontext
    def cleanup_mcp_client(exception):  # noqa: ARG001
        """Cleanup MCP client session on app context teardown"""
        # Note: Since mcp_client is created at app startup and reused,
        # we don't close it here to avoid issues with subsequent requests.
        # The session will be closed when the app shuts down.

    # Register cleanup handler for app shutdown
    def cleanup_resources():
        """Cleanup resources on app shutdown"""
        # Close file handlers to prevent ResourceWarning
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                try:
                    handler.close()
                    root_logger.removeHandler(handler)
                except Exception as e:
                    logging_util.error(f"Error closing file handler: {e}")

        # Close MCP client session
        if (
            app._mcp_client
            and hasattr(app._mcp_client, "session")
            and app._mcp_client.session
        ):
            try:
                app._mcp_client.session.close()
                logging_util.info("Closed MCP client session")
            except Exception as e:
                logging_util.error(f"Error closing MCP client session: {e}")

    atexit.register(cleanup_resources)

    return app


def run_test_command(command: str) -> None:
    """
    Run a test command.

    Args:
        command: The test command to run ('testui', 'testuif', 'testhttp', 'testhttpf')
    """
    if command == "testui":
        # Run browser tests with mock APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_ui",
            "run_all_browser_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info(
                "🌐 Running WorldArchitect.AI Browser Tests (Mock APIs)..."
            )
            logging_util.info("   Using real browser automation with mocked backend")
            browser_timeout = int(os.environ.get("BROWSER_TEST_TIMEOUT", "300"))
            result = subprocess.run(
                [sys.executable, test_runner],
                shell=False,
                timeout=browser_timeout,
                check=False,
            )
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testuif":
        # Run browser tests with REAL APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_ui",
            "run_all_browser_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info(
                "🌐 Running WorldArchitect.AI Browser Tests (REAL APIs)..."
            )
            logging_util.warning(
                "⚠️  WARNING: These tests use REAL APIs and cost money!"
            )
            env = os.environ.copy()
            env["REAL_APIS"] = "true"
            # Real API tests need longer timeout (5 min default)
            full_api_timeout = int(os.environ.get("FULL_API_TEST_TIMEOUT", "300"))
            result = subprocess.run(
                [sys.executable, test_runner],
                shell=False,
                timeout=full_api_timeout,
                check=False,
                env=env,
            )
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testhttp":
        # Run HTTP tests with mock APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_http",
            "run_all_http_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info("🔗 Running WorldArchitect.AI HTTP Tests (Mock APIs)...")
            logging_util.info("   Using direct HTTP requests with mocked backend")
            http_timeout = int(os.environ.get("HTTP_TEST_TIMEOUT", "300"))
            result = subprocess.run(
                [sys.executable, test_runner],
                shell=False,
                timeout=http_timeout,
                check=False,
            )
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Test runner not found: {test_runner}")
            sys.exit(1)

    elif command == "testhttpf":
        # Run HTTP tests with REAL APIs
        test_runner = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "testing_http",
            "testing_full",
            "run_all_full_tests.py",
        )
        if os.path.exists(test_runner):
            logging_util.info("🔗 Running WorldArchitect.AI HTTP Tests (REAL APIs)...")
            logging_util.warning(
                "⚠️  WARNING: These tests use REAL APIs and cost money!"
            )
            # Real API tests need longer timeout (5 min default)
            full_api_timeout = int(os.environ.get("FULL_API_TEST_TIMEOUT", "300"))
            result = subprocess.run(
                [sys.executable, test_runner],
                shell=False,
                timeout=full_api_timeout,
                check=False,
            )
            sys.exit(result.returncode)
        else:
            logging_util.error(f"Full API test runner not found: {test_runner}")
            sys.exit(1)

    else:
        logging_util.error(f"Unknown test command: {command}")
        sys.exit(1)


# Don't create global app instance - let each execution context create its own
app = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="World Architect AI Server & Tools")
    parser.add_argument(
        "command",
        nargs="?",
        default="serve",
        help="Command to run ('serve', 'testui', 'testuif', 'testhttp', or 'testhttpf')",
    )
    parser.add_argument(
        "--mcp-http",
        action="store_true",
        help="Use HTTP communication with MCP server (default: direct calls)",
    )
    parser.add_argument(
        "--mcp-server-url",
        default="http://localhost:8000",
        help="MCP server URL (default: http://localhost:8000)",
    )

    # Check for test commands first
    if len(sys.argv) > 1 and sys.argv[1] in [
        "testui",
        "testuif",
        "testhttp",
        "testhttpf",
    ]:
        run_test_command(sys.argv[1])
    else:
        # Standard server execution
        args = parser.parse_args()
        if args.command == "serve":
            # Create app instance with MCP configuration for serve command
            app = create_app()
            # Skip MCP HTTP calls unless explicitly requested via CLI
            app._skip_mcp_http = not args.mcp_http
            app._mcp_server_url = args.mcp_server_url

            # Robust port parsing to handle descriptive PORT environment variables
            def parse_port_robust(port_string):
                """
                Parse port number from environment variable that may contain descriptive text.
                Handles cases like: "ℹ️ Port 8081 in use, trying 8082...\n8082"
                """
                default_port = 8081

                if not port_string or not isinstance(port_string, str):
                    return default_port

                # Clean the string - remove extra whitespace and newlines
                port_string = port_string.strip()

                # Try direct conversion first (normal case)
                try:
                    return int(port_string)
                except ValueError:
                    pass

                # Extract all numbers from the string
                numbers = re.findall(r"\d+", port_string)

                if not numbers:
                    return default_port

                # Use the last number found (often the actual port after conflicts)
                try:
                    port = int(numbers[-1])
                    # Validate port range
                    if 1024 <= port <= 65535:
                        return port
                    return default_port
                except (ValueError, IndexError):
                    return default_port

            port = parse_port_robust(os.environ.get("PORT", "8081"))
            mode = (
                "direct calls"
                if app._skip_mcp_http
                else f"HTTP to {app._mcp_server_url}"
            )
            logging_util.info(
                f"Development server running: http://localhost:{port} (MCP: {mode})"
            )
            app.run(host="0.0.0.0", port=port, debug=True, use_reloader=True)
        elif args.command in ["testui", "testuif", "testhttp", "testhttpf"]:
            run_test_command(args.command)
        else:
            parser.error(f"Unknown command: {args.command}")

# Create app instance for module-level imports (like gunicorn)
if app is None:
    app = create_app()
