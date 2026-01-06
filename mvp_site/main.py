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
    equipment_display,
    firestore_service,
    logging_util,
    stats_display,
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
TESTING_AUTH_BYPASS_MODE = os.getenv("TESTING_AUTH_BYPASS") == "true"
if TESTING_AUTH_BYPASS_MODE:
    # These headers are only honored in TESTING_AUTH_BYPASS mode; do not enable in production.
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
        "true" if TESTING_AUTH_BYPASS_MODE else "false",
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

# D&D 5e Spell Level Lookup (for legacy string-based spell data)
# Used to infer spell level when Firestore stores spells as plain strings
SPELL_LEVEL_LOOKUP: dict[str, int] = {
    # Cantrips (Level 0)
    "dancing lights": 0, "light": 0, "mage hand": 0, "mending": 0,
    "message": 0, "minor illusion": 0, "prestidigitation": 0, "vicious mockery": 0,
    "friends": 0, "true strike": 0, "blade ward": 0, "thunderclap": 0,
    # Level 1
    "charm person": 1, "comprehend languages": 1, "cure wounds": 1,
    "detect magic": 1, "disguise self": 1, "dissonant whispers": 1,
    "faerie fire": 1, "feather fall": 1, "healing word": 1, "heroism": 1,
    "hideous laughter": 1, "tasha's hideous laughter": 1, "identify": 1,
    "illusory script": 1, "longstrider": 1, "silent image": 1, "sleep": 1,
    "speak with animals": 1, "thunderwave": 1, "unseen servant": 1,
    "bane": 1, "animal friendship": 1, "armor of agathys": 1, "hex": 1,
    "hellish rebuke": 1, "magic missile": 1, "shield": 1, "burning hands": 1,
    "chromatic orb": 1, "command": 1, "inflict wounds": 1, "guiding bolt": 1,
    "bless": 1, "protection from evil and good": 1, "sanctuary": 1,
    # Level 2
    "animal messenger": 2, "blindness/deafness": 2, "calm emotions": 2,
    "cloud of daggers": 2, "crown of madness": 2, "detect thoughts": 2,
    "enhance ability": 2, "enthrall": 2, "heat metal": 2, "hold person": 2,
    "invisibility": 2, "knock": 2, "lesser restoration": 2, "locate animals or plants": 2,
    "locate object": 2, "magic mouth": 2, "phantasmal force": 2, "pyrotechnics": 2,
    "see invisibility": 2, "shatter": 2, "silence": 2, "skywrite": 2,
    "suggestion": 2, "warding wind": 2, "zone of truth": 2, "misty step": 2,
    "mirror image": 2, "scorching ray": 2, "web": 2, "spiritual weapon": 2,
    "prayer of healing": 2, "aid": 2, "darkness": 2, "darkvision": 2,
    # Level 3
    "bestow curse": 3, "clairvoyance": 3, "dispel magic": 3, "fear": 3,
    "feign death": 3, "glyph of warding": 3, "hypnotic pattern": 3,
    "leomund's tiny hut": 3, "major image": 3, "nondetection": 3,
    "plant growth": 3, "sending": 3, "speak with dead": 3, "speak with plants": 3,
    "stinking cloud": 3, "tongues": 3, "counterspell": 3, "fireball": 3,
    "fly": 3, "haste": 3, "lightning bolt": 3, "slow": 3, "revivify": 3,
    "spirit guardians": 3, "animate dead": 3, "vampiric touch": 3,
    "mass healing word": 3, "remove curse": 3, "water breathing": 3,
    # Level 4
    "compulsion": 4, "confusion": 4, "dimension door": 4, "freedom of movement": 4,
    "greater invisibility": 4, "hallucinatory terrain": 4, "locate creature": 4,
    "polymorph": 4, "banishment": 4, "blight": 4, "death ward": 4,
    "fire shield": 4, "ice storm": 4, "phantasmal killer": 4, "stoneskin": 4,
    "wall of fire": 4, "fabricate": 4, "resilient sphere": 4,
    # Level 5
    "animate objects": 5, "awaken": 5, "dominate person": 5, "dream": 5,
    "geas": 5, "greater restoration": 5, "hold monster": 5, "legend lore": 5,
    "mass cure wounds": 5, "mislead": 5, "modify memory": 5, "planar binding": 5,
    "raise dead": 5, "scrying": 5, "seeming": 5, "teleportation circle": 5,
    "cloudkill": 5, "cone of cold": 5, "dominate beast": 5, "flame strike": 5,
    "wall of force": 5, "telekinesis": 5, "bigby's hand": 5,
    # Level 6
    "eyebite": 6, "find the path": 6, "guards and wards": 6, "mass suggestion": 6,
    "otto's irresistible dance": 6, "irresistible dance": 6, "programmed illusion": 6,
    "true seeing": 6, "chain lightning": 6, "disintegrate": 6, "globe of invulnerability": 6,
    "harm": 6, "heal": 6, "sunbeam": 6, "word of recall": 6,
    # Level 7
    "etherealness": 7, "forcecage": 7, "mirage arcane": 7, "mordenkainen's magnificent mansion": 7,
    "mordenkainen's sword": 7, "project image": 7, "regenerate": 7, "resurrection": 7,
    "symbol": 7, "teleport": 7, "delayed blast fireball": 7, "finger of death": 7,
    "fire storm": 7, "plane shift": 7, "prismatic spray": 7, "reverse gravity": 7,
    # Level 8
    "dominate monster": 8, "feeblemind": 8, "glibness": 8, "mind blank": 8,
    "power word stun": 8, "antimagic field": 8, "clone": 8, "control weather": 8,
    "earthquake": 8, "incendiary cloud": 8, "maze": 8, "sunburst": 8,
    # Level 9
    "foresight": 9, "power word heal": 9, "power word kill": 9, "true polymorph": 9,
    "wish": 9, "astral projection": 9, "gate": 9, "meteor swarm": 9,
    "prismatic wall": 9, "shapechange": 9, "time stop": 9, "weird": 9,
}


def get_spell_level(spell_name: str) -> int:
    """Look up spell level from name. Returns 0 (cantrip) if unknown."""
    normalized = spell_name.lower().strip()
    return SPELL_LEVEL_LOOKUP.get(normalized, 0)


# --- END CONSTANTS ---


def setup_file_logging() -> None:
    """
    Configure unified logging for Flask server.

    Uses centralized logging_util.setup_unified_logging() to ensure
    consistent logging across all entry points (Flask, MCP, tests).
    Logs go to both Cloud Logging (stdout/stderr) and local file.
    """
    logging_util.setup_unified_logging("flask-server")


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

    global \
        _background_loop, \
        _loop_thread, \
        _blocking_io_executor, \
        _async_shutdown_registered

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
            # Allow automated test flows to bypass Firebase verification (TESTING_AUTH_BYPASS mode only)
            if (
                TESTING_AUTH_BYPASS_MODE
                and ALLOW_TEST_AUTH_BYPASS
                and request.headers.get(HEADER_TEST_BYPASS, "").lower() == "true"
            ):
                kwargs["user_id"] = request.headers.get(
                    HEADER_TEST_USER_ID, "test-user-123"
                )
                logging_util.info(
                    "TESTING_AUTH_BYPASS auth bypass activated for user_id=%s", kwargs["user_id"]
                )
                return f(*args, **kwargs)

            # Authentication uses real Firebase; bypass is only available in TESTING_AUTH_BYPASS mode
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
                            payload_b64 = token_parts[1] + "=" * (
                                4 - len(token_parts[1]) % 4
                            )
                            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                            token_exp = payload.get("exp", 0)
                            current_time = time.time()

                            if current_time <= token_exp + extended_tolerance:
                                # Within extended tolerance - accept the token
                                # Firebase uses 'user_id' or 'sub' for the uid in JWT payload
                                decoded_token = payload
                                # Normalize uid field - Firebase SDK returns 'uid', JWT has 'sub' or 'user_id'
                                if "uid" not in decoded_token:
                                    decoded_token["uid"] = payload.get(
                                        "sub"
                                    ) or payload.get("user_id")
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
            # Parse pagination params from query string
            story_limit = request.args.get("story_limit", 300, type=int)
            story_limit = min(max(story_limit, 10), 500)  # Clamp between 10-500

            logging_util.info(
                f"🎮 LOADING GAME PAGE: user={user_id}, campaign={campaign_id}, "
                f"story_limit={story_limit}"
            )

            # OPTIMIZED: Fetch campaign metadata and paginated story separately
            # This avoids loading all 30MB+ of story into memory for large campaigns
            campaign_data = await run_blocking_io(
                firestore_service.get_campaign_metadata, user_id, campaign_id
            )
            if not campaign_data:
                return jsonify({"error": "Campaign not found"}), 404

            # Get paginated story (only last N entries, fetched at query level)
            story_result = await run_blocking_io(
                firestore_service.get_story_paginated,
                user_id,
                campaign_id,
                limit=story_limit,
            )
            story = story_result.get("entries", [])

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

            # Debug logging with size diagnostics to identify bloat
            total_story_size = sum(len(json.dumps(e, default=str)) for e in processed_story)
            avg_entry_size = total_story_size // len(processed_story) if processed_story else 0
            logging_util.info(
                f"Campaign {campaign_id} story: {len(processed_story)} entries, "
                f"total={total_story_size/1024:.1f}KB, avg={avg_entry_size/1024:.1f}KB/entry"
            )
            # Log size breakdown for first 3 AI entries to identify bloat sources
            for i, entry in enumerate(processed_story[:3]):
                if entry.get("actor") == constants.ACTOR_GEMINI:
                    size_breakdown = {
                        k: len(json.dumps(v, default=str))
                        for k, v in entry.items()
                        if k not in ["actor", "mode", "timestamp"]
                    }
                    top_fields = sorted(size_breakdown.items(), key=lambda x: -x[1])[:5]
                    logging_util.info(
                        f"Entry {i} size breakdown (top 5): "
                        + ", ".join(f"{k}={v/1024:.1f}KB" for k, v in top_fields)
                    )

            # Map to original response format with pagination metadata
            response_data = {
                KEY_CAMPAIGN: campaign_data,
                KEY_STORY: processed_story,
                "game_state": game_state.to_dict() if game_state else {},
                # Pagination metadata for frontend "load older" functionality
                "story_pagination": {
                    "total_count": story_result.get("total_count", len(processed_story)),
                    "fetched_count": story_result.get("fetched_count", len(processed_story)),
                    "has_older": story_result.get("has_older", False),
                    "oldest_timestamp": story_result.get("oldest_timestamp"),
                    "oldest_id": story_result.get("oldest_id"),
                },
            }

            # Enhanced debug logging
            logging_util.info(f"🎯 BACKEND RESPONSE for campaign {campaign_id}:")
            logging_util.info(
                f"  Campaign Title: '{campaign_data.get('title', 'NO_TITLE')}'"
            )
            logging_util.info(f"  Story entries: {len(processed_story)}")
            logging_util.info(
                f"  Pagination: {story_result.get('fetched_count')}/{story_result.get('total_count')} "
                f"(has_older={story_result.get('has_older')})"
            )

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

    @app.route("/api/campaigns/<campaign_id>/story", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_story_paginated(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        """
        Paginated story endpoint for loading older entries.

        Query params:
            limit: Number of entries to return (default 100, max 500)
            before: ISO timestamp to fetch entries before (for pagination)

        Returns:
            {
                story: [...entries...],
                pagination: {total_count, fetched_count, has_older, oldest_timestamp}
            }
        """
        try:
            limit = request.args.get("limit", 100, type=int)
            limit = min(max(limit, 1), 500)  # Clamp between 1-500
            before_timestamp = request.args.get("before")
            before_id = request.args.get("before_id")
            newer_count = max(request.args.get("newer_count", 0, type=int) or 0, 0)
            newer_gemini_count = max(
                request.args.get("newer_gemini_count", 0, type=int) or 0,
                0,
            )

            if before_timestamp:
                try:
                    datetime.datetime.fromisoformat(before_timestamp.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    return jsonify({KEY_ERROR: "Invalid 'before' timestamp; expected ISO-8601 string"}), 400

            # Ensure campaign exists (mirror GET /api/campaigns/<id>)
            campaign_meta = await run_blocking_io(
                firestore_service.get_campaign_metadata, user_id, campaign_id
            )
            if not campaign_meta:
                return jsonify({KEY_SUCCESS: False, KEY_ERROR: "Campaign not found"}), 404

            logging_util.info(
                f"📖 STORY PAGINATION: campaign={campaign_id}, limit={limit}, "
                f"before={before_timestamp}"
            )

            # Get paginated story entries
            story_result = await run_blocking_io(
                firestore_service.get_story_paginated,
                user_id,
                campaign_id,
                limit=limit,
                before_timestamp=before_timestamp,
                before_id=before_id,
                newer_count=newer_count,
                newer_gemini_count=newer_gemini_count,
            )
            story = story_result.get("entries", [])

            # Get user settings for debug mode
            user_settings = (
                await run_blocking_io(firestore_service.get_user_settings, user_id)
                or {}
            )
            debug_mode = bool(user_settings.get("debug_mode", False))

            # Process story entries based on debug mode
            if not debug_mode:
                story = world_logic._strip_game_state_fields(story)

            response_data = {
                KEY_STORY: story,
                "pagination": {
                    "total_count": story_result.get("total_count", len(story)),
                    "fetched_count": story_result.get("fetched_count", len(story)),
                    "has_older": story_result.get("has_older", False),
                    "oldest_timestamp": story_result.get("oldest_timestamp"),
                    "oldest_id": story_result.get("oldest_id"),
                },
            }

            return jsonify(response_data)
        except ValueError as e:
            logging_util.warning(f"Get story paginated validation error: {e}")
            return jsonify({KEY_ERROR: str(e)}), 400
        except Exception as e:
            logging_util.error(f"Get story paginated error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify(
                {
                    KEY_SUCCESS: False,
                    KEY_ERROR: "Failed to retrieve story entries",
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

    @app.route("/api/campaigns/<campaign_id>/equipment", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_equipment(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        """Fetch and format equipment from game state without hitting LLM.

        Returns formatted equipment summary directly from game_state.
        This is a fast, deterministic operation - no AI processing required.
        """
        try:
            # Get game state from Firestore
            game_state = await run_blocking_io(
                firestore_service.get_campaign_game_state, user_id, campaign_id
            )
            if not game_state:
                return (
                    jsonify({KEY_SUCCESS: False, KEY_ERROR: "Campaign not found"}),
                    404,
                )

            # Extract equipment using deterministic function (no LLM)
            equipment_list = equipment_display.extract_equipment_display(game_state)

            # Build formatted summary
            if equipment_list:
                summary = equipment_display.build_equipment_summary(
                    equipment_list, "Your Equipment"
                )
            else:
                summary = "You don't have any equipment yet."

            return jsonify({
                KEY_SUCCESS: True,
                "equipment_summary": summary,
                "equipment_list": equipment_list,
            })

        except Exception as e:
            logging_util.error(f"Get equipment error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify({
                KEY_SUCCESS: False,
                KEY_ERROR: "Failed to retrieve equipment",
            }), 500

    @app.route("/api/campaigns/<campaign_id>/stats", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_stats(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        """Fetch character stats from game state without hitting LLM.

        Returns:
        - Base stats (naked, without equipment bonuses)
        - Effective stats (with equipment bonuses applied)
        - HP, level, AC, and other combat-relevant stats

        Game state locations:
        - game_state.player_character_data.stats: {str, dex, con, int, wis, cha}
        - game_state.player_character_data.hp_current, hp_max
        - game_state.player_character_data.level
        - game_state.player_character_data.equipment: items with potential bonuses
        - game_state.item_registry: item definitions with stats/bonuses
        """
        try:
            game_state = await run_blocking_io(
                firestore_service.get_campaign_game_state, user_id, campaign_id
            )
            if not game_state:
                return (
                    jsonify({KEY_SUCCESS: False, KEY_ERROR: "Campaign not found"}),
                    404,
                )

            pc_data_raw = (
                game_state.player_character_data
                if hasattr(game_state, "player_character_data")
                else {}
            ) or {}
            pc_data_dict = (
                pc_data_raw
                if isinstance(pc_data_raw, dict)
                else vars(pc_data_raw)
                if hasattr(pc_data_raw, "__dict__")
                else {}
            )

            # Helper to safely get values from pc_data (handles both dict and object)
            def safe_get(key: str, default: Any = None) -> Any:
                if key in pc_data_dict:
                    return pc_data_dict.get(key, default)
                if hasattr(pc_data_raw, key):
                    return getattr(pc_data_raw, key, default)
                return default

            # Extract base stats
            stat_keys = {
                "str": "strength",
                "dex": "dexterity",
                "con": "constitution",
                "int": "intelligence",
                "wis": "wisdom",
                "cha": "charisma",
            }

            naked_stats: dict[str, Any] = {}
            effective_stats_raw: dict[str, Any] = {}

            def coerce_stat_source(raw_source: Any, label: str) -> dict[str, Any]:
                """Return a dict-like stat source or log and fall back to empty."""
                if isinstance(raw_source, dict):
                    return raw_source
                if raw_source not in (None, {}):
                    logging_util.warning(
                        f"Stats parse fallback: ignoring non-dict {label} source type {type(raw_source).__name__}"
                    )
                return {}

            # Check for base_attributes (naked stats) first - new schema
            base_attrs = coerce_stat_source(safe_get("base_attributes"), "base_attributes")

            # Check multiple possible locations for effective stats: attributes, stats, aptitudes
            aptitudes = safe_get("aptitudes") or {}
            stat_sources = [
                coerce_stat_source(safe_get("attributes"), "attributes"),
                coerce_stat_source(safe_get("stats"), "stats"),
                coerce_stat_source(aptitudes, "aptitudes"),
                pc_data_dict if isinstance(pc_data_dict, dict) else {},
            ]
            def extract_stat_value(source: dict, short_key: str, long_key: str, upper_key: str) -> Any:
                """Extract stat value from a source dict, handling various formats."""
                for key in [short_key, upper_key, long_key]:
                    if key in source:
                        val = source[key]
                        if isinstance(val, dict) and "score" in val:
                            return val["score"]
                        return val
                return None

            # Extract naked stats from base_attributes (new schema)
            for short_key, long_key in stat_keys.items():
                upper_key = short_key.upper()
                val = extract_stat_value(base_attrs, short_key, long_key, upper_key)
                if val is not None:
                    naked_stats[short_key] = val

            # Extract effective stats from attributes/stats/aptitudes
            for short_key, long_key in stat_keys.items():
                upper_key = short_key.upper()
                for source in stat_sources:
                    if not isinstance(source, dict):
                        continue
                    val = extract_stat_value(source, short_key, long_key, upper_key)
                    if val is not None:
                        effective_stats_raw[short_key] = val
                        break
                if short_key not in effective_stats_raw:
                    logging_util.warning(
                        f"Stats parse fallback: missing {short_key}/{long_key}; defaulting to 10"
                    )
                    effective_stats_raw[short_key] = 10

            # If no base_attributes (legacy schema), use effective as naked
            # This maintains backward compatibility
            if not naked_stats:
                naked_stats = dict(effective_stats_raw)

            # Calculate modifiers
            def calc_modifier(score: int) -> int:
                return (score - 10) // 2

            naked_with_mods = {}
            for stat, value in naked_stats.items():
                try:
                    score = int(value) if value is not None else 10
                except (ValueError, TypeError):
                    logging_util.warning(
                        f"Stats parse fallback: invalid value for {stat} -> {value!r}; defaulting to 10"
                    )
                    score = 10
                mod = calc_modifier(score)
                sign = "+" if mod >= 0 else ""
                naked_with_mods[stat] = {"score": score, "modifier": f"{sign}{mod}"}

            # Get equipment bonuses from item_registry
            item_registry = getattr(game_state, "item_registry", {}) or {}
            # Check both 'equipment' and 'inventory' keys (game state uses 'inventory')
            equipment = safe_get("equipment") or safe_get("inventory") or {}
            equipped_items: dict[str, Any] = {}
            if isinstance(equipment, dict):
                equipped_raw = equipment.get("equipped") or {}
                if isinstance(equipped_raw, dict):
                    equipped_items.update(equipped_raw)

                # Also check flat equipment format where slots live at top level
                equipment_slots = {
                    "head",
                    "body",
                    "armor",
                    "cloak",
                    "neck",
                    "hands",
                    "feet",
                    "ring",
                    "instrument",
                    "main_hand",
                    "off_hand",
                    "mainhand",
                    "offhand",
                    "weapon",
                    "shield",
                    "amulet",
                    "necklace",
                    "belt",
                    "boots",
                    "gloves",
                    "bracers",
                }
                for slot in equipment_slots:
                    if slot in equipment and slot not in equipped_items:
                        item_data = equipment[slot]
                        # Skip items explicitly marked as unequipped
                        if isinstance(item_data, dict) and not item_data.get(
                            "equipped", True
                        ):
                            continue
                        equipped_items[slot] = item_data

            # Calculate equipment bonuses
            equipment_bonuses = {}
            bonus_pattern_combined = re.compile(
                r"(?:(?P<val>[+-]?\d+)\s*(?P<stat>STR|DEX|CON|INT|WIS|CHA|AC))|"
                r"(?:(?P<stat_alt>STR|DEX|CON|INT|WIS|CHA|AC)\s*(?P<val_alt>[+-]?\d+))",
                re.IGNORECASE,
            )

            for slot, item_ref in equipped_items.items():
                if not item_ref:
                    continue

                stat_string: str | None = None
                if isinstance(item_ref, str):
                    if item_ref in item_registry:
                        item_data = item_registry[item_ref]
                        item_stats = item_data.get("stats", "")
                        if isinstance(item_stats, str):
                            stat_string = item_stats
                    if stat_string is None:
                        # Legacy inline equipment format like "Helm (+2 AC)"
                        stat_string = item_ref
                elif isinstance(item_ref, dict):
                    inline_stats = item_ref.get("stats")
                    if isinstance(inline_stats, str):
                        stat_string = inline_stats
                    else:
                        inline_name = item_ref.get("name")
                        if isinstance(inline_name, str):
                            stat_string = inline_name

                if not stat_string:
                    continue

                used_spans: list[tuple[int, int]] = []

                # Check for "(Max X)" cap patterns in the stat string
                max_cap_pattern = re.compile(r"\(Max\s*(\d+)\)", re.IGNORECASE)
                max_cap_match = max_cap_pattern.search(stat_string)
                stat_max_cap = int(max_cap_match.group(1)) if max_cap_match else None

                for match in bonus_pattern_combined.finditer(stat_string):
                    span = match.span()
                    if any(start < span[1] and span[0] < end for start, end in used_spans):
                        continue
                    stat_name = match.group("stat") or match.group("stat_alt")
                    bonus_val = match.group("val") or match.group("val_alt")
                    if not stat_name or bonus_val is None:
                        continue
                    stat_key = stat_name.lower()
                    # Ignore base AC values like "AC 15" to avoid double-counting armor.
                    # Only apply explicit signed AC bonuses (e.g., "+2 AC" or "AC +2").
                    if stat_key == "ac" and not str(bonus_val).startswith(("+", "-")):
                        continue
                    # Check for "(Max X)" cap and respect it
                    max_cap_pattern = re.compile(r"\(Max\s*(\d+)\)", re.IGNORECASE)
                    max_cap_match = max_cap_pattern.search(stat_string)
                    stat_max_cap = int(max_cap_match.group(1)) if max_cap_match else None
                    try:
                        bonus_int = int(bonus_val)
                        # Apply max cap if present
                        if stat_max_cap is not None and stat_key in naked_stats:
                            naked_val = int(naked_stats.get(stat_key, 0))
                            # Cap the bonus so naked + bonus doesn't exceed max
                            max_bonus = max(0, stat_max_cap - naked_val)
                            bonus_int = min(bonus_int, max_bonus)
                        equipment_bonuses[stat_key] = equipment_bonuses.get(stat_key, 0) + bonus_int
                        used_spans.append(span)
                    except (ValueError, TypeError):
                        logging_util.warning(
                            "Unable to parse equipment bonus '%s' for stat '%s'", bonus_val, stat_name
                        )

            # Calculate effective stats (base + equipment bonuses)
            effective_stats = {}
            for stat, data in naked_with_mods.items():
                bonus = equipment_bonuses.get(stat, 0)
                effective_score = data["score"] + bonus
                effective_mod = calc_modifier(effective_score)
                sign = "+" if effective_mod >= 0 else ""
                effective_stats[stat] = {
                    "score": effective_score,
                    "modifier": f"{sign}{effective_mod}",
                    "bonus_from_equipment": bonus if bonus else None,
                }

            # Get other combat stats
            hp_current = safe_get("hp_current", safe_get("hp", 0))
            hp_max = safe_get("hp_max", 0)
            level = safe_get("level", 1)
            ac = safe_get("ac", safe_get("armor_class", 10))
            try:
                ac_base_val = int(ac)
            except (TypeError, ValueError):
                ac_base_val = 10
            ac_bonus = equipment_bonuses.get("ac", 0)
            effective_ac = ac_base_val + ac_bonus

            # Build formatted summary
            lines = ["━━━ Character Stats ━━━"]
            ac_display = f"AC: {ac_base_val}"
            if ac_bonus:
                ac_display += f" (effective: {effective_ac})"

            lines.append(f"Level {level} | HP: {hp_current}/{hp_max} | {ac_display}")
            lines.append("")
            lines.append("▸ Naked Stats (without equipment):")
            stat_order = ["str", "dex", "con", "int", "wis", "cha"]
            stat_names = {"str": "STR", "dex": "DEX", "con": "CON", "int": "INT", "wis": "WIS", "cha": "CHA"}
            for stat in stat_order:
                if stat in naked_with_mods:
                    data = naked_with_mods[stat]
                    lines.append(f"  • {stat_names.get(stat, stat.upper())}: {data['score']} ({data['modifier']})")

            if equipment_bonuses:
                lines.append("")
                lines.append("▸ Equipment Bonuses:")
                for stat, bonus in equipment_bonuses.items():
                    if bonus:
                        bonus_sign = f"+{bonus}" if bonus > 0 else str(bonus)
                        lines.append(f"  • {stat_names.get(stat, stat.upper())}: {bonus_sign}")

                lines.append("")
                lines.append("▸ Effective Stats (with equipment):")
                for stat in stat_order:
                    if stat in effective_stats:
                        data = effective_stats[stat]
                        lines.append(
                            f"  • {stat_names.get(stat, stat.upper())}: {data['score']} ({data['modifier']})"
                        )

            # Extract and deduplicate features/feats using shared module
            features = safe_get("features", [])
            unique_features = stats_display.deduplicate_features(features)

            # Only add header if there are actual features after deduplication
            if unique_features:
                lines.append("")
                lines.append("▸ Features & Feats:")
                for feat in unique_features:
                    lines.append(f"  • {feat}")

            return jsonify({
                KEY_SUCCESS: True,
                "stats_summary": "\n".join(lines),
                "naked_stats": naked_with_mods,
                "effective_stats": effective_stats,
                "equipment_bonuses": equipment_bonuses,
                "combat_stats": {
                    "level": level,
                    "hp_current": hp_current,
                    "hp_max": hp_max,
                    "ac": ac_base_val,
                    "effective_ac": effective_ac,
                },
                "features": unique_features,
            })

        except Exception as e:
            logging_util.error(f"Get stats error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify({
                KEY_SUCCESS: False,
                KEY_ERROR: "Failed to retrieve stats",
            }), 500

    @app.route("/api/campaigns/<campaign_id>/spells", methods=["GET"])
    @limiter.limit(campaign_rate_limit)
    @check_token
    @async_route
    async def get_spells(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        """Fetch spells and class resources from game state without hitting LLM.

        Returns:
        - Spells known/available
        - Spells prepared/memorized
        - Spell slots (current/max by level)
        - Class resources (ki points, rage, channel divinity, etc.)

        Game state locations:
        - game_state.player_character_data.spells: list of known spells
        - game_state.player_character_data.spells_prepared: prepared spell list
        - game_state.player_character_data.spell_slots: {level: {current, max}}
        - game_state.player_character_data.resources: class features and uses
        - game_state.player_character_data.cantrips: cantrips known
        """
        try:
            game_state = await run_blocking_io(
                firestore_service.get_campaign_game_state, user_id, campaign_id
            )
            if not game_state:
                return (
                    jsonify({KEY_SUCCESS: False, KEY_ERROR: "Campaign not found"}),
                    404,
                )

            pc_data_raw = (
                game_state.player_character_data
                if hasattr(game_state, "player_character_data")
                else {}
            ) or {}
            pc_data_dict = (
                pc_data_raw
                if isinstance(pc_data_raw, dict)
                else vars(pc_data_raw)
                if hasattr(pc_data_raw, "__dict__")
                else {}
            )

            # Helper to safely get values from pc_data (handles both dict and object)
            def safe_get(key: str, default: Any = None) -> Any:
                if key in pc_data_dict:
                    return pc_data_dict.get(key, default)
                if hasattr(pc_data_raw, key):
                    return getattr(pc_data_raw, key, default)
                return default

            # Extract spell information
            def normalize_spell_list(raw: Any) -> list[Any]:
                if raw is None:
                    return []
                if isinstance(raw, list):
                    return raw
                if isinstance(raw, str):
                    return [raw]
                return []

            cantrips = normalize_spell_list(safe_get("cantrips", []))
            spells_known = normalize_spell_list(safe_get("spells", safe_get("spells_known", [])))
            spells_prepared = normalize_spell_list(
                safe_get("spells_prepared", safe_get("spells_memorized", []))
            )

            # Extract spell slots - handle various formats
            spell_slots_raw = safe_get("spell_slots", {})
            spell_slots = {}
            if isinstance(spell_slots_raw, dict):
                for level, data in spell_slots_raw.items():
                    if isinstance(data, dict):
                        spell_slots[level] = {
                            "current": data.get("current", data.get("remaining", 0)),
                            "max": data.get("max", data.get("total", 0)),
                        }
                    elif isinstance(data, (int, str)):
                        # Simple format: level -> remaining slots (max unknown)
                        try:
                            remaining = int(data)
                        except (ValueError, TypeError):
                            logging_util.warning(
                                f"Spells parse fallback: invalid spell slot value for level {level}: {data!r}; skipping"
                            )
                            continue
                        spell_slots[level] = {"current": remaining, "max": 0}

            # Also check for spell_slots_level_X format
            pc_items = (
                pc_data_dict.items()
                if isinstance(pc_data_dict, dict)
                else []
            )
            for key, value in pc_items:
                if key.startswith("spell_slots_level_"):
                    level = key.replace("spell_slots_level_", "")
                    if level not in spell_slots:
                        try:
                            max_slots = int(value)
                        except (ValueError, TypeError):
                            # Ignore malformed slot values; treat as unavailable
                            logging_util.warning(
                                f"Spells parse fallback: invalid spell_slots_level_{level} value {value!r}; skipping"
                            )
                            continue
                        spell_slots[level] = {"current": max_slots, "max": max_slots}

            # Extract class resources (HD, lay on hands, divine sense, ki, rage, etc.)
            resources_raw = safe_get("resources", {})
            class_resources = {}

            if isinstance(resources_raw, dict):
                # Copy to avoid mutating game state, but exclude spell_slots
                # (spell_slots are displayed separately in the Spell Slots section)
                class_resources = {
                    k: v for k, v in resources_raw.items() if k != "spell_slots"
                }

                # Also check for spell_slots inside resources (format: {level_X: {used, max}})
                resources_spell_slots = resources_raw.get("spell_slots", {})
                if isinstance(resources_spell_slots, dict):
                    for level_key, slot_data in resources_spell_slots.items():
                        if isinstance(slot_data, dict):
                            # Format: level_1: {used: 1, max: 4} -> current = max - used
                            # Convert to int to handle string values from Firestore
                            try:
                                max_val = int(slot_data.get("max", 0))
                                used_val = int(slot_data.get("used", 0))
                                current_val = max_val - used_val
                            except (ValueError, TypeError):
                                max_val = 0
                                used_val = 0
                                current_val = 0
                            # Extract level number from "level_1" format
                            level = level_key.replace("level_", "") if level_key.startswith("level_") else level_key
                            # Only add if not already populated from top-level spell_slots
                            if level not in spell_slots:
                                spell_slots[level] = {"current": current_val, "max": max_val}
            elif isinstance(resources_raw, str):
                # Parse string format like "HD: 3/5 | Lay on Hands: 15/15"
                parts = resources_raw.split("|")
                for part in parts:
                    if ":" in part:
                        name, value = part.split(":", 1)
                        class_resources[name.strip()] = value.strip()

            # Also check for common resource fields at top level
            resource_fields = [
                "hit_dice", "hd", "lay_on_hands", "divine_sense", "channel_divinity",
                "ki_points", "ki", "rage", "rages", "bardic_inspiration", "sorcery_points",
                "superiority_dice", "second_wind", "action_surge", "arcane_recovery",
                "wild_shape", "infusions"
            ]
            for field in resource_fields:
                field_value = safe_get(field)
                if field_value is not None and field not in class_resources:
                    class_resources[field] = field_value

            # Normalize spells for comparison (handles dicts vs. strings and ordering)
            def spell_signature(spell: Any) -> tuple[str, str]:
                if isinstance(spell, dict):
                    name = spell.get("name", "")
                    level_val = spell.get("level", "")
                else:
                    name = spell
                    level_val = ""

                name_norm = str(name).strip().lower() if name is not None else ""
                level_norm = str(level_val).strip().lower() if level_val not in (None, "") else ""
                return name_norm, level_norm

            normalized_spells_known: set[tuple[str, str]] = set()
            for spell in spells_known or []:
                signature = spell_signature(spell)
                if signature[0]:
                    normalized_spells_known.add(signature)

            normalized_spells_prepared: set[tuple[str, str]] = set()
            for spell in spells_prepared or []:
                signature = spell_signature(spell)
                if signature[0]:
                    normalized_spells_prepared.add(signature)

            # Build formatted summary
            lines = ["━━━ Spells & Resources ━━━"]

            # Cantrips
            if cantrips:
                lines.append("")
                lines.append("▸ Cantrips (at will):")
                for cantrip in cantrips:
                    name = cantrip.get("name", "Unknown Cantrip") if isinstance(cantrip, dict) else str(cantrip)
                    lines.append(f"  • {name}")

            # Spell slots
            if spell_slots:
                lines.append("")
                lines.append("▸ Spell Slots:")
                for level in sorted(
                    spell_slots.keys(),
                    key=lambda x: (0, int(x)) if str(x).isdigit() else (1, str(x)),
                ):
                    data = spell_slots[level]
                    max_display = data["max"] if data.get("max") not in (0, None, "") else "?"
                    lines.append(f"  • Level {level}: {data['current']}/{max_display}")

            # Spells prepared - grouped by level
            if spells_prepared:
                lines.append("")
                lines.append("▸ Spells Prepared:")
                # Group spells by level
                prepared_by_level: dict[str, list[str]] = {}
                for spell in spells_prepared:
                    name = spell.get("name", "Unknown Spell") if isinstance(spell, dict) else str(spell)
                    # Get level from dict, or look up from spell name for legacy string data
                    if isinstance(spell, dict):
                        level = spell.get("level", 0)
                    else:
                        level = get_spell_level(name)
                    level_str = str(level) if level is not None else "0"
                    if level_str not in prepared_by_level:
                        prepared_by_level[level_str] = []
                    prepared_by_level[level_str].append(name)
                # Sort by level and display
                for level_key in sorted(prepared_by_level.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                    spell_names = prepared_by_level[level_key]
                    if level_key == "0":
                        level_label = "Cantrips"
                    else:
                        level_label = f"Level {level_key}"
                    lines.append(f"  {level_label}: {', '.join(sorted(spell_names))}")

            # Spells known (if different from prepared) - grouped by level
            if spells_known and normalized_spells_known != normalized_spells_prepared:
                lines.append("")
                lines.append("▸ Spells Known:")
                # Group spells by level
                spells_by_level: dict[str, list[str]] = {}
                for spell in spells_known:
                    name = spell.get("name", "Unknown Spell") if isinstance(spell, dict) else str(spell)
                    # Get level from dict, or look up from spell name for legacy string data
                    if isinstance(spell, dict):
                        level = spell.get("level", 0)
                    else:
                        level = get_spell_level(name)
                    # Normalize level to string
                    level_str = str(level) if level is not None else "0"
                    if level_str not in spells_by_level:
                        spells_by_level[level_str] = []
                    spells_by_level[level_str].append(name)
                # Sort by level and display
                for level_key in sorted(spells_by_level.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                    spell_names = spells_by_level[level_key]
                    if level_key == "0":
                        level_label = "Cantrips"
                    else:
                        level_label = f"Level {level_key}"
                    lines.append(f"  {level_label}: {', '.join(sorted(spell_names))}")

            # Class resources
            if class_resources:
                lines.append("")
                lines.append("▸ Class Resources:")
                for resource_name, value in class_resources.items():
                    display_name = resource_name.replace("_", " ").title()
                    if isinstance(value, dict):
                        current = value.get("current", value.get("remaining", "?"))
                        maximum = value.get("max", value.get("total", "?"))
                        lines.append(f"  • {display_name}: {current}/{maximum}")
                    else:
                        lines.append(f"  • {display_name}: {value}")

            # If nothing found
            if len(lines) == 1:
                lines.append("")
                lines.append("No spells or special resources found.")
                lines.append("(Non-spellcasting classes may not have spell slots)")

            return jsonify({
                KEY_SUCCESS: True,
                "spells_summary": "\n".join(lines),
                "cantrips": cantrips,
                "spells_known": spells_known,
                "spells_prepared": spells_prepared,
                "spell_slots": spell_slots,
                "class_resources": class_resources,
            })

        except Exception as e:
            logging_util.error(f"Get spells error: {e}")
            logging_util.error(traceback.format_exc())
            return jsonify({
                KEY_SUCCESS: False,
                KEY_ERROR: "Failed to retrieve spells",
            }), 500

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
    @limiter.limit(settings_rate_limit)  # Settings access is moderate frequency
    @check_token
    @async_route
    async def api_settings(user_id: UserId) -> Response | tuple[Response, int]:
        """Get or update user settings."""
        try:
            if request.method == "GET":
                # Use MCP client for getting settings
                request_data = {"user_id": user_id}

                # Delegate to world_logic for centralized defaults handling
                result = await world_logic.get_user_settings_unified(
                    {"user_id": user_id}
                )

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
                    "spicy_mode",
                    "pre_spicy_model",
                    "pre_spicy_provider",
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
                        filtered_data["llm_provider"] = (
                            constants.infer_provider_from_model(
                                filtered_data["gemini_model"],
                                provider_hint=constants.LLM_PROVIDER_GEMINI,
                            )
                        )
                    elif "openrouter_model" in filtered_data:
                        filtered_data["llm_provider"] = (
                            constants.infer_provider_from_model(
                                filtered_data["openrouter_model"],
                                provider_hint=constants.LLM_PROVIDER_OPENROUTER,
                            )
                        )
                    elif "cerebras_model" in filtered_data:
                        filtered_data["llm_provider"] = (
                            constants.infer_provider_from_model(
                                filtered_data["cerebras_model"],
                                provider_hint=constants.LLM_PROVIDER_CEREBRAS,
                            )
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

    @app.route("/api/constants/models", methods=["GET"])
    @limiter.limit(settings_rate_limit)
    @check_token
    def get_model_constants(user_id: UserId) -> Response:
        """Expose model defaults to keep frontend aligned with backend constants."""

        return jsonify(
            {
                "SPICY_MODEL": constants.SPICY_OPENROUTER_MODEL,
                "DEFAULT_GEMINI_MODEL": constants.DEFAULT_GEMINI_MODEL,
                "DEFAULT_OPENROUTER_MODEL": constants.DEFAULT_OPENROUTER_MODEL,
                "DEFAULT_CEREBRAS_MODEL": constants.DEFAULT_CEREBRAS_MODEL,
            }
        )

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
        root_logger = logging_util.getLogger()
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging_util.FileHandler):
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
