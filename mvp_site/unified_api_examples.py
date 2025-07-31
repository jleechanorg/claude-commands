"""
Examples showing how to use unified_api.py from both Flask and MCP contexts.

This file demonstrates the integration patterns for using the unified API layer
to provide consistent functionality across different interfaces.
"""

# Example 1: Flask Route Integration
"""
# In main.py - Replace existing route with unified API call

@app.route("/api/campaigns", methods=["POST"])
@check_token
def create_campaign_route(user_id: UserId) -> Response | tuple[Response, int]:
    from unified_api import create_campaign_unified

    # Extract Flask request data
    data = request.get_json()

    # Add user_id from Flask auth context
    request_data = data.copy()
    request_data["user_id"] = user_id

    # Call unified function
    result = await create_campaign_unified(request_data)

    # Return Flask response
    if result.get("success"):
        return jsonify(result), 201
    else:
        return jsonify(result), result.get("status_code", 400)
"""

# Example 2: MCP Tool Integration
"""
# In world_logic.py - Replace existing tool function with unified API call

async def _create_campaign_tool(args: dict[str, Any]) -> list[TextContent]:
    from unified_api import create_campaign_unified

    # MCP args already contain user_id and other parameters
    result = await create_campaign_unified(args)

    # Return MCP TextContent response
    return [
        TextContent(
            type="text",
            text=json.dumps(result, default=json_default_serializer)
        )
    ]
"""

# Example 3: Comparison of Old vs New Approach

"""
OLD APPROACH (Duplicated Logic):

# main.py
@app.route("/api/campaigns/<campaign_id>/actions", methods=["POST"])
@check_token
def handle_interaction(user_id: UserId, campaign_id: CampaignId):
    # 100+ lines of business logic
    data = request.get_json()
    user_input = data.get("user_input")
    # ... complex processing ...
    return jsonify(response)

# world_logic.py
async def _process_action_tool(args: dict[str, Any]) -> list[TextContent]:
    # Same 100+ lines of business logic duplicated
    user_input = args["user_input"]
    # ... identical complex processing ...
    return [TextContent(type="text", text=json.dumps(response))]

NEW APPROACH (Unified Logic):

# unified_api.py - Single source of truth
async def process_action_unified(request_data: dict[str, Any]) -> dict[str, Any]:
    # 100+ lines of business logic - implemented once

# main.py - Thin wrapper
@app.route("/api/campaigns/<campaign_id>/actions", methods=["POST"])
@check_token
def handle_interaction(user_id: UserId, campaign_id: CampaignId):
    data = request.get_json()
    data["user_id"] = user_id
    data["campaign_id"] = campaign_id
    result = await process_action_unified(data)
    return jsonify(result), result.get("status_code", 200)

# world_logic.py - Thin wrapper
async def _process_action_tool(args: dict[str, Any]) -> list[TextContent]:
    result = await process_action_unified(args)
    return [TextContent(type="text", text=json.dumps(result))]
"""

# Example 4: Error Handling Consistency

"""
Before: Different error formats
Flask: {"error": "Message", "status": 400}
MCP: {"error": "Message"}

After: Consistent error format
Both: {"error": "Message", "success": false, "status_code": 400}
"""

# Example 5: Testing Benefits

"""
Before: Test both implementations separately
- test_main_routes.py
- test_world_logic_tools.py

After: Test unified logic once
- test_unified_api.py tests the business logic
- Integration tests verify thin wrappers work
"""

# Example 6: User ID Handling

"""
Flask Context (user_id from authentication):
request_data = {
    "title": "My Campaign",
    "character": "Knight",
    # user_id added from Flask auth
}
request_data["user_id"] = user_id_from_auth_token

MCP Context (user_id in explicit parameters):
request_data = {
    "user_id": "explicit-user-123",
    "title": "My Campaign",
    "character": "Knight"
}

Both call: await create_campaign_unified(request_data)
"""

# Example 7: Response Format Standardization

"""
All unified functions return:
{
    "success": true/false,
    "error": "message" (if failed),
    "status_code": 200/400/500 (for Flask compatibility),
    ...response_data
}

Flask routes convert to HTTP responses:
if result["success"]:
    return jsonify(result), 200
else:
    return jsonify(result), result["status_code"]

MCP tools convert to TextContent:
return [TextContent(type="text", text=json.dumps(result))]
"""
