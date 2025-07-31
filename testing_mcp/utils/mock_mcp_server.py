"""
Mock MCP Server

Provides a mock MCP server for unit testing without requiring actual
world_logic.py implementation. Responds with realistic test data
that matches the expected MCP protocol format.
"""

import json
import logging
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

import threading

from flask import Flask, jsonify, request

logger = logging.getLogger(__name__)


@dataclass
class MockCampaign:
    """Mock campaign data structure."""
    id: str
    name: str
    description: str
    dm_user_id: str
    created_at: str
    status: str = "active"
    player_count: int = 0
    story_content: str = ""


@dataclass
class MockCharacter:
    """Mock character data structure."""
    id: str
    name: str
    campaign_id: str
    user_id: str
    character_class: str
    level: int
    attributes: dict[str, int]
    created_at: str


@dataclass
class MockUserSettings:
    """Mock user settings data structure."""
    user_id: str
    theme: str = "default"
    notifications: bool = True
    ai_model: str = "gemini-2.0-flash-exp"
    auto_save: bool = True


class MockMCPServer:
    """Mock MCP server that responds to JSON-RPC calls with test data."""

    def __init__(self, port: int = 8001):
        self.port = port
        self.app = Flask(__name__)
        self.campaigns: dict[str, MockCampaign] = {}
        self.characters: dict[str, MockCharacter] = {}
        self.user_settings: dict[str, MockUserSettings] = {}
        self.call_count: dict[str, int] = {}
        self.setup_routes()
        self.load_mock_data()

    def setup_routes(self):
        """Setup Flask routes for MCP protocol."""

        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({"status": "ok", "server": "mock-mcp"})

        @self.app.route('/mcp', methods=['POST'])
        def handle_mcp():
            try:
                data = request.get_json()
                if not data:
                    return self._error_response(-32700, "Parse error", 1)

                method = data.get('method')
                params = data.get('params', {})
                request_id = data.get('id', 1)

                # Track call counts for testing
                self.call_count[method] = self.call_count.get(method, 0) + 1

                if method == "tools/call":
                    return self._handle_tool_call(params, request_id)
                if method == "tools/list":
                    return self._handle_tools_list(request_id)
                if method == "resources/read":
                    return self._handle_resource_read(params, request_id)
                if method == "resources/list":
                    return self._handle_resources_list(request_id)
                return self._error_response(-32601, f"Method not found: {method}", request_id)

            except Exception as e:
                logger.error(f"Error handling MCP request: {e}")
                return self._error_response(-32603, f"Internal error: {e}", 1)

    def _handle_tool_call(self, params: dict[str, Any], request_id: int) -> dict[str, Any]:
        """Handle MCP tool calls."""
        tool_name = params.get('name')
        arguments = params.get('arguments', {})

        handlers = {
            'create_campaign': self._create_campaign,
            'get_campaigns': self._get_campaigns,
            'get_campaign': self._get_campaign,
            'update_campaign': self._update_campaign,
            'create_character': self._create_character,
            'process_action': self._process_action,
            'get_campaign_state': self._get_campaign_state,
            'export_campaign': self._export_campaign,
            'get_user_settings': self._get_user_settings,
            'update_user_settings': self._update_user_settings,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return self._error_response(-32601, f"Tool not found: {tool_name}", request_id)

        try:
            result = handler(arguments)

            # Check if the handler returned an error response
            if isinstance(result, dict) and result.get("status") == "error":
                # Convert to JSON-RPC error
                error_type = result.get("error_type", "unknown_error")
                error_msg = result.get("error", "Unknown error")
                return self._error_response(-32000, f"{error_type}: {error_msg}", request_id)

            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except Exception as e:
            logger.error(f"Error in tool {tool_name}: {e}")
            return self._error_response(-32603, f"Tool error: {e}", request_id)

    def _handle_tools_list(self, request_id: int) -> dict[str, Any]:
        """List all available tools."""
        tools = [
            {"name": "create_campaign", "description": "Create a new campaign"},
            {"name": "get_campaigns", "description": "Get user's campaigns"},
            {"name": "get_campaign", "description": "Get specific campaign"},
            {"name": "update_campaign", "description": "Update campaign"},
            {"name": "create_character", "description": "Create character"},
            {"name": "process_action", "description": "Process game action"},
            {"name": "get_campaign_state", "description": "Get campaign state"},
            {"name": "export_campaign", "description": "Export campaign"},
            {"name": "get_user_settings", "description": "Get user settings"},
            {"name": "update_user_settings", "description": "Update user settings"},
        ]

        return {
            "jsonrpc": "2.0",
            "result": {"tools": tools},
            "id": request_id
        }

    def _handle_resource_read(self, params: dict[str, Any], request_id: int) -> dict[str, Any]:
        """Read an MCP resource."""
        uri = params.get('uri', '')

        if uri.startswith('campaign://'):
            # Extract campaign_id from URI like "campaign://123/state"
            parts = uri.split('/')
            if len(parts) >= 2:
                campaign_id = parts[1]
                campaign = self.campaigns.get(campaign_id)
                if campaign:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(asdict(campaign), indent=2)
                                }
                            ]
                        },
                        "id": request_id
                    }

        elif uri.startswith('user://'):
            # Extract user_id from URI like "user://123/settings"
            parts = uri.split('/')
            if len(parts) >= 2:
                user_id = parts[1]
                settings = self.user_settings.get(user_id)
                if settings:
                    return {
                        "jsonrpc": "2.0",
                        "result": {
                            "contents": [
                                {
                                    "uri": uri,
                                    "mimeType": "application/json",
                                    "text": json.dumps(asdict(settings), indent=2)
                                }
                            ]
                        },
                        "id": request_id
                    }

        return self._error_response(-32002, f"Resource not found: {uri}", request_id)

    def _handle_resources_list(self, request_id: int) -> dict[str, Any]:
        """List available resources."""
        resources = []

        # Add campaign resources
        for campaign_id in self.campaigns:
            resources.append({
                "uri": f"campaign://{campaign_id}/state",
                "name": f"Campaign {campaign_id} State",
                "description": "Campaign state and story data"
            })

        # Add user settings resources
        for user_id in self.user_settings:
            resources.append({
                "uri": f"user://{user_id}/settings",
                "name": f"User {user_id} Settings",
                "description": "User preferences and configuration"
            })

        return {
            "jsonrpc": "2.0",
            "result": {"resources": resources},
            "id": request_id
        }

    def _error_response(self, code: int, message: str, request_id: int) -> dict[str, Any]:
        """Create JSON-RPC error response."""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }

    # Tool implementations
    def _create_campaign(self, args: dict[str, Any]) -> dict[str, Any]:
        """Create a new campaign."""
        campaign_id = str(uuid.uuid4())
        campaign = MockCampaign(
            id=campaign_id,
            name=args['name'],
            description=args.get('description', ''),
            dm_user_id=args['user_id'],
            created_at=datetime.now().isoformat()
        )

        self.campaigns[campaign_id] = campaign

        return {
            "status": "success",
            "data": {
                "campaign_id": campaign_id,
                "name": campaign.name,
                "description": campaign.description,
                "dm_user_id": campaign.dm_user_id,
                "created_at": campaign.created_at
            }
        }

    def _get_campaigns(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get all campaigns for a user."""
        user_id = args['user_id']
        user_campaigns = [
            asdict(campaign) for campaign in self.campaigns.values()
            if campaign.dm_user_id == user_id
        ]

        return {
            "status": "success",
            "data": {
                "campaigns": user_campaigns
            }
        }

    def _get_campaign(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get a specific campaign."""
        campaign_id = args['campaign_id']
        user_id = args['user_id']

        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {
                "status": "error",
                "error_type": "not_found",
                "error": "Campaign not found"
            }

        if campaign.dm_user_id != user_id:
            return {
                "status": "error",
                "error_type": "permission_denied",
                "error": "Access denied"
            }

        return {
            "status": "success",
            "data": asdict(campaign)
        }

    def _update_campaign(self, args: dict[str, Any]) -> dict[str, Any]:
        """Update a campaign."""
        campaign_id = args['campaign_id']
        updates = args['updates']
        user_id = args['user_id']

        campaign = self.campaigns.get(campaign_id)
        if not campaign:
            return {
                "status": "error",
                "error_type": "not_found",
                "error": "Campaign not found"
            }

        if campaign.dm_user_id != user_id:
            return {
                "status": "error",
                "error_type": "permission_denied",
                "error": "Access denied"
            }

        # Apply updates
        for key, value in updates.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)

        return {
            "status": "success",
            "data": asdict(campaign)
        }

    def _create_character(self, args: dict[str, Any]) -> dict[str, Any]:
        """Create a character."""
        character_id = str(uuid.uuid4())
        character_data = args['character_data']

        character = MockCharacter(
            id=character_id,
            name=character_data.get('name', 'Unnamed Character'),
            campaign_id=args['campaign_id'],
            user_id=character_data.get('user_id', 'unknown'),
            character_class=character_data.get('class', 'Fighter'),
            level=character_data.get('level', 1),
            attributes=character_data.get('attributes', {
                'strength': 10, 'dexterity': 10, 'constitution': 10,
                'intelligence': 10, 'wisdom': 10, 'charisma': 10
            }),
            created_at=datetime.now().isoformat()
        )

        self.characters[character_id] = character

        return {
            "status": "success",
            "data": asdict(character)
        }

    def _process_action(self, args: dict[str, Any]) -> dict[str, Any]:
        """Process a game action."""
        return {
            "status": "success",
            "data": {
                "action_id": str(uuid.uuid4()),
                "session_id": args['session_id'],
                "action_type": args['action_type'],
                "result": "Action processed successfully",
                "narrative": f"You performed a {args['action_type']} action.",
                "game_state_updated": True,
                "timestamp": datetime.now().isoformat()
            }
        }

    def _get_campaign_state(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get campaign state (same as get_campaign for mock)."""
        return self._get_campaign(args)

    def _export_campaign(self, args: dict[str, Any]) -> dict[str, Any]:
        """Export a campaign."""
        return {
            "status": "success",
            "data": {
                "export_id": str(uuid.uuid4()),
                "format": args['format'],
                "download_url": f"/exports/{uuid.uuid4()}.{args['format']}",
                "expires_at": datetime.now().isoformat(),
                "size_bytes": 1024
            }
        }

    def _get_user_settings(self, args: dict[str, Any]) -> dict[str, Any]:
        """Get user settings."""
        user_id = args['user_id']
        settings = self.user_settings.get(user_id)

        if not settings:
            # Create default settings
            settings = MockUserSettings(user_id=user_id)
            self.user_settings[user_id] = settings

        return {
            "status": "success",
            "data": asdict(settings)
        }

    def _update_user_settings(self, args: dict[str, Any]) -> dict[str, Any]:
        """Update user settings."""
        user_id = args['user_id']
        new_settings = args['settings']

        settings = self.user_settings.get(user_id)
        if not settings:
            settings = MockUserSettings(user_id=user_id)

        # Apply updates
        for key, value in new_settings.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        self.user_settings[user_id] = settings

        return {
            "status": "success",
            "data": asdict(settings)
        }

    def load_mock_data(self):
        """Load initial mock data for testing."""
        # Create some test campaigns
        test_user = "test-user-123"

        campaign1 = MockCampaign(
            id="campaign-1",
            name="The Dragon's Lair",
            description="A classic dungeon adventure",
            dm_user_id=test_user,
            created_at="2024-01-01T00:00:00",
            story_content="The party approaches the ancient dragon's lair..."
        )

        campaign2 = MockCampaign(
            id="campaign-2",
            name="City of Shadows",
            description="Urban fantasy campaign",
            dm_user_id=test_user,
            created_at="2024-01-15T00:00:00",
            story_content="In the neon-lit streets of Neo-Tokyo..."
        )

        self.campaigns["campaign-1"] = campaign1
        self.campaigns["campaign-2"] = campaign2

        # Create test characters
        character1 = MockCharacter(
            id="char-1",
            name="Thorin Ironshield",
            campaign_id="campaign-1",
            user_id=test_user,
            character_class="Fighter",
            level=5,
            attributes={'strength': 16, 'dexterity': 12, 'constitution': 14,
                       'intelligence': 10, 'wisdom': 13, 'charisma': 8},
            created_at="2024-01-01T01:00:00"
        )

        self.characters["char-1"] = character1

        # Create test user settings
        settings = MockUserSettings(
            user_id=test_user,
            theme="dark",
            notifications=True,
            ai_model="gemini-2.0-flash-exp"
        )

        self.user_settings[test_user] = settings

    def get_call_count(self, method: str) -> int:
        """Get number of times a method was called."""
        return self.call_count.get(method, 0)

    def reset_call_counts(self):
        """Reset all call counts."""
        self.call_count.clear()

    def run(self, debug: bool = False):
        """Run the mock server."""
        self.app.run(host='0.0.0.0', port=self.port, debug=debug)


def create_mock_server(port: int = 8001) -> MockMCPServer:
    """Create and configure a mock MCP server."""
    return MockMCPServer(port)


def run_mock_server_background(port: int = 8001) -> threading.Thread:
    """Run mock server in background thread."""
    server = create_mock_server(port)

    def run_server():
        server.run(debug=False)

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    return thread


if __name__ == "__main__":
    # Run mock server directly
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    print(f"Starting mock MCP server on port {port}")
    server = create_mock_server(port)
    server.run(debug=True)
