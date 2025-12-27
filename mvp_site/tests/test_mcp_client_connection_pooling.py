"""
TDD tests for MCP client connection pooling

Tests verify that the MCP client:
1. Configures HTTPAdapter for connection pooling
2. Has correct pool_connections setting
3. Has correct pool_maxsize setting
4. Has retry configuration
5. Mounts adapters for both HTTP and HTTPS
"""

import unittest

import requests

from mvp_site.mcp_client import MCPClient


class TestMCPClientConnectionPooling(unittest.TestCase):
    """Test suite for MCP client HTTP connection pooling"""

    def test_mcp_client_creates_session_with_http_adapter(self):
        """RED→GREEN: MCPClient should create session with HTTPAdapter"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        # Session should be created
        self.assertIsNotNone(client.session, "Session should be created")
        self.assertIsInstance(
            client.session, requests.Session, "Should be a requests.Session"
        )

        # Should have adapters mounted
        http_adapter = client.session.get_adapter("http://")
        https_adapter = client.session.get_adapter("https://")

        self.assertIsNotNone(http_adapter, "HTTP adapter should be mounted")
        self.assertIsNotNone(https_adapter, "HTTPS adapter should be mounted")

        # Adapters should be HTTPAdapter instances
        self.assertIsInstance(
            http_adapter, requests.adapters.HTTPAdapter, "HTTP adapter type"
        )
        self.assertIsInstance(
            https_adapter, requests.adapters.HTTPAdapter, "HTTPS adapter type"
        )

    def test_connection_pool_size_configuration(self):
        """RED→GREEN: Connection pool should have correct pool_maxsize"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")

        # Check pool_maxsize (max connections per pool)
        # We configured it to 20 in mcp_client.py
        self.assertEqual(
            http_adapter.poolmanager.connection_pool_kw.get("maxsize"),
            20,
            "pool_maxsize should be 20 for concurrent requests",
        )

    def test_connection_pool_cache_configuration(self):
        """RED→GREEN: Connection pool should cache connections for multiple hosts"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")

        # Check pool_connections (number of pools to cache)
        # We configured it to 10 in mcp_client.py
        self.assertEqual(
            http_adapter._pool_connections,
            10,
            "pool_connections should be 10 for caching multiple host pools",
        )

    def test_retry_configuration(self):
        """RED→GREEN: HTTPAdapter should have retry configuration"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")

        # Check max_retries configuration
        # We configured it to 3 in mcp_client.py
        self.assertEqual(
            http_adapter.max_retries.total,
            3,
            "max_retries should be 3 for automatic retry",
        )

    def test_both_http_and_https_have_same_configuration(self):
        """RED→GREEN: Both HTTP and HTTPS adapters should have same config"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")
        https_adapter = client.session.get_adapter("https://")

        # Both should have same pool_connections
        self.assertEqual(
            http_adapter._pool_connections,
            https_adapter._pool_connections,
            "HTTP and HTTPS should have same pool_connections",
        )

        # Both should have same pool_maxsize
        http_maxsize = http_adapter.poolmanager.connection_pool_kw.get("maxsize")
        https_maxsize = https_adapter.poolmanager.connection_pool_kw.get("maxsize")
        self.assertEqual(
            http_maxsize, https_maxsize, "HTTP and HTTPS should have same pool_maxsize"
        )

        # Both should have same max_retries
        self.assertEqual(
            http_adapter.max_retries.total,
            https_adapter.max_retries.total,
            "HTTP and HTTPS should have same max_retries",
        )

    def test_skip_http_mode_does_not_create_session(self):
        """RED→GREEN: skip_http mode should not create HTTP session"""
        client = MCPClient("http://localhost:8000", skip_http=True)

        # Session should be None in skip_http mode
        self.assertIsNone(client.session, "Session should be None when skip_http=True")

    def test_session_has_correct_headers(self):
        """RED→GREEN: Session should have correct default headers"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        headers = client.session.headers

        # Check required headers
        self.assertEqual(
            headers.get("Content-Type"),
            "application/json",
            "Content-Type should be application/json",
        )
        self.assertEqual(
            headers.get("Accept"),
            "application/json",
            "Accept should be application/json",
        )
        self.assertIn(
            "WorldArchitect",
            headers.get("User-Agent", ""),
            "User-Agent should identify as WorldArchitect",
        )

    def test_ssl_verification_enabled(self):
        """RED→GREEN: SSL verification should be enabled for security"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        self.assertTrue(
            client.session.verify,
            "SSL verification should be enabled (session.verify=True)",
        )

    def test_connection_pooling_improves_reuse(self):
        """RED→GREEN: Connection pooling should enable connection reuse"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")

        # pool_block should be False (don't block when pool is full)
        self.assertEqual(
            http_adapter._pool_block,
            False,
            "pool_block should be False to raise error instead of blocking",
        )

    def test_multiple_clients_have_independent_sessions(self):
        """RED→GREEN: Multiple MCPClient instances should have independent sessions"""
        client1 = MCPClient("http://localhost:8000", skip_http=False)
        client2 = MCPClient("http://localhost:9000", skip_http=False)

        # Sessions should be different objects
        self.assertIsNot(
            client1.session,
            client2.session,
            "Each MCPClient should have its own session",
        )

        # Base URLs should be different
        self.assertNotEqual(
            client1.base_url,
            client2.base_url,
            "Clients should have different base URLs",
        )

    def test_connection_pool_configuration_values(self):
        """RED→GREEN: Verify exact configuration values match implementation"""
        client = MCPClient("http://localhost:8000", skip_http=False)

        http_adapter = client.session.get_adapter("http://")

        # Verify exact values from implementation
        expected_config = {
            "pool_connections": 10,  # Cache pools for up to 10 hosts
            "pool_maxsize": 20,  # Max 20 connections per pool
            "max_retries": 3,  # Retry failed requests up to 3 times
            "pool_block": False,  # Don't block, raise error if pool full
        }

        self.assertEqual(
            http_adapter._pool_connections,
            expected_config["pool_connections"],
            f"pool_connections should be {expected_config['pool_connections']}",
        )

        self.assertEqual(
            http_adapter.poolmanager.connection_pool_kw.get("maxsize"),
            expected_config["pool_maxsize"],
            f"pool_maxsize should be {expected_config['pool_maxsize']}",
        )

        self.assertEqual(
            http_adapter.max_retries.total,
            expected_config["max_retries"],
            f"max_retries should be {expected_config['max_retries']}",
        )

        self.assertEqual(
            http_adapter._pool_block,
            expected_config["pool_block"],
            f"pool_block should be {expected_config['pool_block']}",
        )


if __name__ == "__main__":
    unittest.main()
