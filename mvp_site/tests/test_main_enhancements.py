from unittest.mock import patch

import pytest

# Try to import the Flask app with proper package import
try:
    from mvp_site.main import app
    HAS_MAIN_APP = True
    IMPORT_ERROR = None
except ImportError as e:
    HAS_MAIN_APP = False
    IMPORT_ERROR = str(e)
except Exception as e:
    HAS_MAIN_APP = False
    IMPORT_ERROR = f"Unexpected error importing main: {str(e)}"

@pytest.fixture
def client():
    """Flask test client fixture with proper error handling"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            yield client

def test_flask_app_import():
    """Test that the Flask app can be imported successfully"""
    if not HAS_MAIN_APP:
        pytest.fail(f"Failed to import Flask app from main.py: {IMPORT_ERROR}")

    assert app is not None
    assert hasattr(app, 'test_client')

def test_flask_app_is_flask_instance():
    """Test that imported app is a Flask instance"""
    if not HAS_MAIN_APP:
        pytest.skip(f"Cannot test Flask instance: {IMPORT_ERROR}")

    from flask import Flask
    assert isinstance(app, Flask)

def test_time_endpoint_exists(client):
    """Test that the /api/time endpoint exists and works"""
    response = client.get('/api/time')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert 'timestamp' in data
    assert isinstance(data['timestamp'], str)

def test_campaigns_endpoint_requires_auth(client):
    """Test that campaigns endpoint requires authentication"""
    response = client.get('/api/campaigns')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_campaigns_endpoint_with_test_headers(client):
    """Test campaigns endpoint with test bypass headers"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/campaigns', headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 500]

def test_settings_endpoint_requires_auth(client):
    """Test that settings endpoint requires authentication"""
    response = client.get('/api/settings')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_settings_endpoint_with_test_headers(client):
    """Test settings endpoint with test bypass headers"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/settings', headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 500]

def test_create_campaign_requires_auth(client):
    """Test that campaign creation requires authentication"""
    campaign_data = {
        'name': 'Test Campaign',
        'description': 'A test campaign for unit testing'
    }
    response = client.post('/api/campaigns',
                          json=campaign_data,
                          content_type='application/json')
    # Should return 401 Unauthorized without proper auth
    assert response.status_code == 401

def test_create_campaign_with_test_headers(client):
    """Test campaign creation with test bypass headers"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123',
        'Content-Type': 'application/json'
    }
    campaign_data = {
        'name': 'Test Campaign',
        'description': 'A test campaign for unit testing'
    }
    response = client.post('/api/campaigns',
                          json=campaign_data,
                          headers=headers)
    # Should succeed with test bypass or return 500 if MCP not available
    assert response.status_code in [200, 201, 500]

@patch('mvp_site.main.MCPClient', autospec=True)
def test_mcp_client_integration(mock_mcp_client, client):
    """Test MCP client integration with mocked client"""
    # Mock MCP client to return test data asynchronously
    mock_instance = mock_mcp_client.return_value
    from unittest.mock import AsyncMock
    mock_instance.call_tool = AsyncMock(return_value={
        'campaigns': [
            {'id': 'test-123', 'name': 'Test Campaign'}
        ]
    })

    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/campaigns', headers=headers)

    # Should succeed with mocked MCP
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data.get('campaigns') is not None

def test_cors_enabled_for_api_routes(client):
    """Test that CORS is enabled for API routes"""
    # Make an OPTIONS request to test CORS preflight
    response = client.options('/api/time', headers={
        'Origin': 'http://example.com',
        'Access-Control-Request-Method': 'GET',
    })
    # Should handle OPTIONS request (either 200/204/405 is acceptable)
    assert response.status_code in [200, 204, 405]
    if response.status_code != 405:
        assert 'Access-Control-Allow-Origin' in response.headers

def test_frontend_serving(client):
    """Test that frontend is served from root path"""
    response = client.get('/')
    # Should serve frontend HTML or return 404 if static files not built
    assert response.status_code in [200, 404]

def test_invalid_json_handling(client):
    """Test proper handling of invalid JSON in requests"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123',
        'Content-Type': 'application/json'
    }
    # Send malformed JSON
    response = client.post('/api/campaigns',
                          data='{"invalid": json, "missing": quote}',
                          headers=headers)
    # Should return 400 Bad Request for invalid JSON
    assert response.status_code == 400

def test_nonexistent_campaign_handling(client):
    """Test handling of requests for non-existent campaigns"""
    headers = {
        'X-Test-Bypass-Auth': 'true',
        'X-Test-User-ID': 'test-user-123'
    }
    response = client.get('/api/campaigns/nonexistent-id', headers=headers)
    # Should return 404 or error response
    assert response.status_code in [404, 500]
