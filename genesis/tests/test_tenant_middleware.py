import unittest
from unittest.mock import patch, MagicMock, call
from django.http import HttpResponse, HttpRequest
from django.test import TestCase, override_settings
from django.db import connection
from django.conf import settings
from django.test.utils import setup_test_environment, teardown_test_environment
from app.middleware import TenantMiddleware
import logging
import os

# Configure Django settings for testing
if not settings.configured:
    settings.configure(
        DEBUG=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.contenttypes',
            'django.contrib.auth',
            'app',
        ],
        SECRET_KEY='test-key-for-testing-only',
        TENANT_SCHEMA_PREFIX='tenant_',
        USE_TZ=True,
    )


class MockTenant:
    def __init__(self, schema_name):
        self.schema_name = schema_name


class TenantMiddlewareTestCase(TestCase):
    """
    Comprehensive test suite for TenantMiddleware
    Tests all methods with complete scenario coverage
    """

    def setUp(self):
        """Setup test fixtures and mocks"""
        self.get_response = MagicMock(return_value=HttpResponse())
        self.middleware = TenantMiddleware(self.get_response)

        # Create test request
        self.request = HttpRequest()
        self.request.META = {}
        self.request.path = '/'
        self.request.method = 'GET'
        self.request.GET = {}

        # Mock database connection
        self.db_patcher = patch('app.middleware.connection')
        self.mock_connection = self.db_patcher.start()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value.__enter__.return_value = self.mock_cursor
        self.mock_connection.cursor.return_value.__exit__.return_value = None

        # Mock logger
        self.logger_patcher = patch('app.middleware.logger')
        self.mock_logger = self.logger_patcher.start()

    def tearDown(self):
        """Clean up mocks"""
        self.db_patcher.stop()
        self.logger_patcher.stop()

    def test_init_method(self):
        """Test middleware constructor"""
        middleware = TenantMiddleware(self.get_response)
        self.assertEqual(middleware.get_response, self.get_response)

    @override_settings(TENANT_SCHEMA_PREFIX='tenant_')
    def test_call_with_header_tenant(self):
        """Test middleware execution with X-Tenant header"""
        self.request.META['HTTP_X_TENANT'] = 'testcorp'

        response = self.middleware(self.request)

        # Verify tenant attributes set on request
        self.assertEqual(self.request.tenant_slug, 'testcorp')
        self.assertEqual(self.request.tenant_schema, 'tenant_testcorp')

        # Verify schema switching calls
        expected_calls = [
            call('SET search_path TO tenant_testcorp, public'),
            call('SET search_path TO public')
        ]
        self.mock_cursor.execute.assert_has_calls(expected_calls)

        # Verify get_response called
        self.get_response.assert_called_once_with(self.request)
        self.assertEqual(response, self.get_response.return_value)

    def test_call_with_subdomain_tenant(self):
        """Test middleware execution with subdomain detection"""
        self.request.META['HTTP_HOST'] = 'testcorp.example.com'

        with patch.object(self.middleware, 'get_tenant_from_request', return_value='testcorp'):
            response = self.middleware(self.request)

        self.assertEqual(self.request.tenant_slug, 'testcorp')

    def test_call_with_no_tenant_fallback(self):
        """Test middleware execution with fallback to public schema"""
        response = self.middleware(self.request)

        # Verify fallback to public schema
        self.assertIsNone(self.request.tenant_slug)
        self.assertEqual(self.request.tenant_schema, 'public')

        # Verify schema calls (set public, then reset to public)
        expected_calls = [
            call('SET search_path TO public'),
            call('SET search_path TO public')
        ]
        self.mock_cursor.execute.assert_has_calls(expected_calls)

    def test_get_tenant_from_request_header(self):
        """Test tenant extraction from HTTP_X_TENANT header"""
        self.request.META['HTTP_X_TENANT'] = '  TESTCORP  '

        tenant = self.middleware.get_tenant_from_request(self.request)

        self.assertEqual(tenant, 'testcorp')  # Should be lowercase and stripped

    def test_get_tenant_from_request_subdomain(self):
        """Test tenant extraction from subdomain"""
        # Mock get_host method
        self.request.get_host = MagicMock(return_value='testcorp.example.com')

        tenant = self.middleware.get_tenant_from_request(self.request)

        self.assertEqual(tenant, 'testcorp')

    def test_get_tenant_from_request_subdomain_excluded(self):
        """Test subdomain exclusion for common subdomains"""
        excluded_subdomains = ['www', 'api', 'admin']

        for subdomain in excluded_subdomains:
            self.request.get_host = MagicMock(return_value=f'{subdomain}.example.com')
            tenant = self.middleware.get_tenant_from_request(self.request)
            self.assertIsNone(tenant, f'Should exclude {subdomain} subdomain')

    def test_get_tenant_from_request_path(self):
        """Test tenant extraction from URL path"""
        self.request.path = '/tenant/testcorp/dashboard/'
        self.request.get_host = MagicMock(return_value='example.com')

        tenant = self.middleware.get_tenant_from_request(self.request)

        self.assertEqual(tenant, 'testcorp')

    def test_get_tenant_from_request_path_invalid(self):
        """Test path parsing with invalid tenant path"""
        self.request.path = '/api/v1/users/'
        self.request.get_host = MagicMock(return_value='example.com')

        tenant = self.middleware.get_tenant_from_request(self.request)

        self.assertIsNone(tenant)

    def test_get_tenant_from_request_priority(self):
        """Test tenant extraction priority: header > subdomain > path"""
        # Set up all three methods
        self.request.META['HTTP_X_TENANT'] = 'header_tenant'
        self.request.get_host = MagicMock(return_value='subdomain_tenant.example.com')
        self.request.path = '/tenant/path_tenant/'

        tenant = self.middleware.get_tenant_from_request(self.request)

        # Should prioritize header
        self.assertEqual(tenant, 'header_tenant')

    def test_set_tenant_schema_success(self):
        """Test successful schema switching"""
        self.middleware.set_tenant_schema('test_schema')

        self.mock_cursor.execute.assert_called_once_with('SET search_path TO test_schema, public')
        self.mock_logger.debug.assert_called_once_with('Switched to schema: test_schema')

    def test_set_tenant_schema_error_fallback(self):
        """Test schema switching error handling with fallback"""
        # First call raises exception, second succeeds
        self.mock_cursor.execute.side_effect = [Exception('Database error'), None]

        self.middleware.set_tenant_schema('invalid_schema')

        # Verify error logged and fallback executed
        self.mock_logger.error.assert_called_once()
        expected_calls = [
            call('SET search_path TO invalid_schema, public'),
            call('SET search_path TO public')
        ]
        self.mock_cursor.execute.assert_has_calls(expected_calls)

    def test_process_exception(self):
        """Test exception processing resets to public schema"""
        exception = Exception('Test exception')

        result = self.middleware.process_exception(self.request, exception)

        # Should reset to public schema
        self.mock_cursor.execute.assert_called_once_with('SET search_path TO public')

        # Should return None (doesn't handle the exception)
        self.assertIsNone(result)

    @override_settings(TENANT_SCHEMA_PREFIX='custom_')
    def test_schema_prefix_setting(self):
        """Test custom tenant schema prefix setting"""
        self.request.META['HTTP_X_TENANT'] = 'test'

        self.middleware(self.request)

        self.assertEqual(self.request.tenant_schema, 'custom_test')

    def test_middleware_integration_flow(self):
        """Test complete middleware integration flow"""
        self.request.META['HTTP_X_TENANT'] = 'integration_test'

        with override_settings(TENANT_SCHEMA_PREFIX='tenant_'):
            response = self.middleware(self.request)

        # Verify complete flow
        self.assertEqual(self.request.tenant_slug, 'integration_test')
        self.assertEqual(self.request.tenant_schema, 'tenant_integration_test')

        # Verify schema switching sequence
        expected_calls = [
            call('SET search_path TO tenant_integration_test, public'),  # Set tenant schema
            call('SET search_path TO public')  # Reset after response
        ]
        self.mock_cursor.execute.assert_has_calls(expected_calls)

        # Verify response chain
        self.get_response.assert_called_once_with(self.request)
        self.assertIsInstance(response, HttpResponse)


if __name__ == '__main__':
    unittest.main()
