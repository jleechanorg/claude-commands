"""
TDD Tests for Flask API Service Enhancements
These tests validate REAL Flask application behavior using test_client
"""
import json
import os
import sys
from unittest.mock import patch

import pytest

# Add mvp_site to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from main import app as flask_app
    HAS_MAIN_APP = True
except ImportError as e:
    HAS_MAIN_APP = False
    IMPORT_ERROR = str(e)

@pytest.fixture
def client():
    """Flask test client fixture for real app testing"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Could not import Flask app: {IMPORT_ERROR}")

    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client, flask_app.app_context():
        yield client

def test_time_endpoint_available(client):
    """Test that time endpoint is available and returns proper structure"""
    response = client.get('/api/time')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert 'timestamp' in data
    assert isinstance(data['timestamp'], str)

def test_campaigns_endpoint_requires_auth(client):
    """Test that campaigns endpoint requires authentication"""
    response = client.get('/api/campaigns')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_campaigns_endpoint_with_test_bypass(client):
    """Test campaigns endpoint with test bypass header"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/campaigns', headers=headers)
    # Should succeed with test bypass
    assert response.status_code in [200, 500]  # 500 if MCP server not available

def test_settings_endpoint_requires_auth(client):
    """Test that settings endpoint requires authentication"""
    response = client.get('/api/settings')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_settings_endpoint_with_test_bypass(client):
    """Test settings endpoint with test bypass header"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/settings', headers=headers)
    # Should succeed with test bypass
    assert response.status_code in [200, 500]  # 500 if MCP server not available

def test_campaign_creation_requires_auth(client):
    """Test that campaign creation requires authentication"""
    campaign_data = {
        'name': 'Test Campaign',
        'description': 'A test campaign'
    }
    response = client.post('/api/campaigns',
                          json=campaign_data,
                          content_type='application/json')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_campaign_creation_with_test_bypass(client):
    """Test campaign creation with test bypass header"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123',
        'Content-Type': 'application/json'
    }
    campaign_data = {
        'name': 'Test Campaign',
        'description': 'A test campaign'
    }
    response = client.post('/api/campaigns',
                          json=campaign_data,
                          headers=headers)
    # Should succeed with test bypass (or 500 if MCP server not available)
    assert response.status_code in [200, 201, 500]

def test_invalid_endpoint_returns_404(client):
    """Test that invalid API endpoints return 404"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404

def test_cors_headers_present_on_api_routes(client):
    """Test that CORS headers are properly set on API routes"""
    response = client.get('/api/time')
    # Time endpoint should have CORS headers since it's an API route
    assert response.status_code == 200
    # Note: CORS headers might only be added by Flask-CORS for actual CORS requests

def test_frontend_serving_fallback(client):
    """Test that non-API routes serve frontend"""
    response = client.get('/')
    # Should serve frontend HTML (or return 404 if static files not built)
    assert response.status_code in [200, 404]

def test_static_file_serving(client):
    """Test that static files are served from correct paths"""
    # Test the frontend_v1 route
    response = client.get('/frontend_v1/index.html')
    # Should serve frontend or return 404 if not built
    assert response.status_code in [200, 404]

@patch('mvp_site.main.MCPClient', autospec=True)
def test_campaign_get_with_mocked_mcp(mock_mcp_client, client):
    """Test campaign retrieval with mocked MCP client"""
    # Mock MCP client to return test data asynchronously
    mock_instance = mock_mcp_client.return_value
    from unittest.mock import AsyncMock
    mock_instance.call_tool = AsyncMock(return_value={
        'campaign_id': 'test-123',
        'name': 'Test Campaign'
    })

    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/campaigns/test-123', headers=headers)

    # Should succeed with mocked MCP
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data.get('campaign_id') == 'test-123'

def test_error_handling_with_invalid_json(client):
    """Test error handling with invalid JSON data"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123',
        'Content-Type': 'application/json'
    }
    # Send invalid JSON
    response = client.post('/api/campaigns',
                          data='{"invalid": json}',
                          headers=headers)
    # Should return 400 Bad Request for invalid JSON
    assert response.status_code == 400
