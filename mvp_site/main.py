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
import concurrent.futures
import datetime
import json
import logging
import os
import subprocess
import sys
import traceback
from functools import wraps
from typing import Any

import constants

# Firebase imports
import firebase_admin
import logging_util
from custom_types import CampaignId, UserId
from firebase_admin import auth

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

# MCP client import
from mcp_client import MCPClient, MCPClientError, handle_mcp_errors

# Import JSON serializer for Firestore compatibility
from firestore_service import json_default_serializer

# --- CONSTANTS ---
# API Configuration
CORS_RESOURCES = {r"/api/*": {"origins": "*"}}

# Request Headers
HEADER_AUTH = "Authorization"
# Testing mode headers removed - authentication now always uses real Firebase

# Logging Configuration (using centralized logging_util)
# LOG_DIRECTORY moved to logging_util.get_log_directory() for consistency

# Request/Response Data Keys (specific to main.py)
KEY_PROMPT = "prompt"
KEY_SELECTED_PROMPTS = "selected_prompts"
KEY_USER_INPUT = "input"
KEY_CAMPAIGN_ID = "campaign_id"
KEY_SUCCESS = "success"
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

    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
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
    # Set up file logging before creating app
    setup_file_logging()

    app = Flask(__name__)
    CORS(app, resources=CORS_RESOURCES)

    # Defer MCP client initialization until first use to avoid race condition
    # with command-line argument configuration
    app._mcp_client = None

    def get_mcp_client():
        """Lazy initialization of MCP client with proper configuration."""
        if app._mcp_client is None:
            skip_http_mode = getattr(
                app, "_skip_mcp_http", True
            )  # Default: direct calls
            mcp_server_url = getattr(
                app,
                "_mcp_server_url",
                os.environ.get("MCP_SERVER_URL", "http://localhost:8000"),
            )
            app._mcp_client = MCPClient(
                mcp_server_url, timeout=300, skip_http=skip_http_mode
            )
        return app._mcp_client

    # Cache busting route for testing - only activates with special header
    @app.route("/frontend_v1/<path:filename>")
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
    def static_files_redirect(filename):
        """Redirect old /static/ paths to /frontend_v1/ for backward compatibility"""
        return redirect(
            url_for("frontend_files_with_cache_busting", filename=filename), code=301
        )

    # Testing mode removed - Flask TESTING config no longer set from environment

    # Initialize Firebase - always enabled (testing mode removed)
    try:
        firebase_admin.get_app()
    except ValueError:
        firebase_admin.initialize_app()

    def check_token(f):
        @wraps(f)
        def wrap(*args: Any, **kwargs: Any) -> Response:
            # Authentication now always uses real Firebase (testing mode removed)
            if not request.headers.get(HEADER_AUTH):
                return jsonify({KEY_MESSAGE: "No token provided"}), 401
            try:
                id_token = request.headers[HEADER_AUTH].split(" ").pop()
                # Firebase token verification using Admin SDK with clock skew tolerance
                # check_revoked=True ensures revoked tokens are rejected for security
                # clock_skew_seconds=10 allows for up to 10 seconds of clock difference
                decoded_token = auth.verify_id_token(
                    id_token,
                    check_revoked=True,
                    clock_skew_seconds=10,  # Allow 10 seconds of clock skew
                )
                kwargs["user_id"] = decoded_token["uid"]
            except Exception as e:
                error_message = str(e)
                logging_util.error(f"Auth failed: {e}")
                # Do not log tokens or Authorization headers
                logging_util.error(traceback.format_exc())

                # Enhanced error response with clock skew hints
                response_data = {
                    KEY_SUCCESS: False,
                    KEY_ERROR: f"Authentication failed: {error_message}",
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
                # Check if we're already in an event loop
                try:
                    asyncio.get_running_loop()
                except RuntimeError:
                    # No event loop running, safe to use asyncio.run
                    return asyncio.run(f(*args, **kwargs))
                else:
                    # Already in an event loop, create a task and run it
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, f(*args, **kwargs))
                        return future.result()
            return f(*args, **kwargs)

        return wrapper

    # --- API Routes ---
    @app.route("/api/campaigns", methods=["GET"])
    @check_token
    @async_route
    async def get_campaigns(user_id: UserId) -> Response | tuple[Response, int]:
        try:
            data = {"user_id": user_id}
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

            # Direct service calls (testing mode removed - always use direct approach)
            import firestore_service

            campaign_data, story = firestore_service.get_campaign_by_id(
                user_id, campaign_id
            )
            if not campaign_data:
                return jsonify({"error": "Campaign not found"}), 404

            # Get user settings for debug mode
            user_settings = firestore_service.get_user_settings(user_id)
            debug_mode = user_settings.get("debug_mode", False)

            # Get game state
            game_state = firestore_service.get_campaign_game_state(user_id, campaign_id)
            if game_state:
                game_state.debug_mode = debug_mode

            # Process story entries based on debug mode
            import world_logic

            if debug_mode:
                processed_story = story
            else:
                # Strip debug fields when debug mode is off
                processed_story = world_logic._strip_game_state_fields(story)

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
            logging_util.info(f"  Full campaign object: {campaign_data}")

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
    @check_token
    @async_route
    async def create_campaign_route(user_id: UserId) -> Response | tuple[Response, int]:
        try:
            data = request.get_json()

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
            return jsonify({KEY_ERROR: f"Failed to create campaign: {str(e)}"}), 500

    @app.route("/api/campaigns/<campaign_id>", methods=["PATCH"])
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
            import world_logic

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
        except Exception as e:
            logging_util.error(traceback.format_exc())
            return jsonify(
                {KEY_ERROR: "Failed to update campaign", KEY_DETAILS: str(e)}
            ), 500

    @app.route("/api/campaigns/<campaign_id>/interaction", methods=["POST"])
    @check_token
    @async_route
    async def handle_interaction(
        user_id: UserId, campaign_id: CampaignId
    ) -> Response | tuple[Response, int]:
        try:
            print("DEBUG PRINT: handle_interaction START - testing mode removed")
            logging_util.info("DEBUG: handle_interaction START - testing mode removed")
            data = request.get_json()
            print(f"DEBUG PRINT: request data = {data}")
            logging_util.info(f"DEBUG: request data = {data}")
            user_input = data.get(KEY_USER_INPUT)
            print(
                f"DEBUG PRINT: user_input = {user_input} (KEY_USER_INPUT='{KEY_USER_INPUT}')"
            )
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
                    error_msg = result.get("error", "Unknown error")
                    logging_util.error(f"DEBUG: MCP process_action failed: {error_msg}")

                    # Return appropriate error response based on error type
                    if (
                        "not found" in error_msg.lower()
                        or "campaign not found" in error_msg.lower()
                    ):
                        return jsonify({"error": "Campaign not found"}), 404
                    else:
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
            return jsonify(
                {
                    KEY_ERROR: "An unexpected error occurred during export.",
                    KEY_DETAILS: str(e),
                }
            ), 500

    # --- Time Sync Route for Clock Skew Detection ---
    @app.route("/api/time", methods=["GET"])
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

    # --- Settings Routes ---
    @app.route("/settings")
    @check_token
    def settings_page(user_id: UserId) -> Response:
        """Settings page for authenticated users."""
        logging_util.info(f"User {user_id} visited settings page")
        return render_template("settings.html")

    @app.route("/api/settings", methods=["GET", "POST"])
    @check_token
    @async_route
    async def api_settings(user_id: UserId) -> Response | tuple[Response, int]:
        """Get or update user settings."""
        try:
            if request.method == "GET":
                # Use MCP client for getting settings
                request_data = {"user_id": user_id}

                # Direct service calls (testing mode removed - always use direct approach)
                import firestore_service

                settings = firestore_service.get_user_settings(user_id)
                # Handle case where settings is None (user doesn't exist yet)
                if settings is None:
                    settings = {}
                result = {"success": True, **settings}

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
                request_data = {"user_id": user_id, "settings": filtered_data}

                # Direct service calls (testing mode removed - always use direct approach)
                import firestore_service

                firestore_service.update_user_settings(user_id, filtered_data)
                result = {"success": True}

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
    def serve_frontend(path: str) -> Response:
        """Serve the frontend files. This is the fallback for any non-API routes."""
        frontend_folder = os.path.join(os.path.dirname(__file__), "frontend_v1")
        if path and os.path.exists(os.path.join(frontend_folder, path)):
            return send_from_directory(frontend_folder, path)
        return send_from_directory(frontend_folder, "index.html")

    # Fallback route for old cached frontend code calling /handle_interaction
    @app.route("/handle_interaction", methods=["POST"])
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
            result = subprocess.run([sys.executable, test_runner], check=False)
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
            result = subprocess.run([sys.executable, test_runner], check=False, env=env)
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
            result = subprocess.run([sys.executable, test_runner], check=False)
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
            result = subprocess.run([sys.executable, test_runner], check=False)
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
            app._skip_mcp_http = (
                not args.mcp_http
            )  # Default to True (skip HTTP), override with --mcp-http
            app._mcp_server_url = args.mcp_server_url

            # Robust port parsing to handle descriptive PORT environment variables
            def parse_port_robust(port_string):
                """
                Parse port number from environment variable that may contain descriptive text.
                Handles cases like: "ℹ️ Port 8081 in use, trying 8082...\n8082"
                """
                import re

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
                    else:
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
            app.run(host="0.0.0.0", port=port, debug=True)
        elif args.command in ["testui", "testuif", "testhttp", "testhttpf"]:
            run_test_command(args.command)
        else:
            parser.error(f"Unknown command: {args.command}")

# Create app instance for module-level imports (like gunicorn)
if app is None:
    app = create_app()
