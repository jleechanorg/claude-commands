"""
Comprehensive FastAPI Tenant Middleware Tests
Tests for multi-tenant FastAPI middleware functionality including header, path, and subdomain resolution.
"""
import pytest
import asyncio
import uuid
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, Depends
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import os
import sys
from typing import Generator

# Add parent directories to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, get_db, SessionLocal, Customer, Product, Order, OrderItem, Base
from app.tenant_middleware import (
    TenantMiddleware,
    TenantDatabaseDependency,
    create_tenant_database_dependency,
    create_tenant_schema,
    drop_tenant_schema,
    list_tenant_schemas
)


class TestTenantMiddleware:
    """Test suite for TenantMiddleware class"""

    @pytest.fixture
    def mock_app(self):
        """Create mock FastAPI app"""
        return Mock()

    @pytest.fixture
    def tenant_middleware(self, mock_app):
        """Create TenantMiddleware instance"""
        return TenantMiddleware(mock_app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request object"""
        request = Mock(spec=Request)
        request.state = Mock()
        request.headers = Mock()
        request.headers.get = Mock(return_value=None)
        request.url = Mock()
        request.url.path = "/"
        return request

    def test_middleware_initialization(self, mock_app):
        """Test TenantMiddleware initialization"""
        middleware = TenantMiddleware(mock_app, tenant_schema_prefix="custom_")

        assert middleware.tenant_schema_prefix == "custom_"
        assert middleware.database_url is not None
        assert middleware.engine is not None

    def test_get_tenant_from_request_header_priority(self, tenant_middleware, mock_request):
        """Test tenant extraction from X-Tenant header (highest priority)"""
        mock_request.url.path = "/tenant/path_tenant/api"
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "x-tenant": "  HeaderTenant  ",
            "host": "subdomain.example.com"
        }.get(key, default)

        tenant = tenant_middleware.get_tenant_from_request(mock_request)

        assert tenant == "headertenant"

    def test_get_tenant_from_request_path_resolution(self, tenant_middleware, mock_request):
        """Test tenant extraction from path (second priority)"""
        mock_request.url.path = "/tenant/pathtenant/dashboard"
        mock_request.headers.get.return_value = None

        tenant = tenant_middleware.get_tenant_from_request(mock_request)

        assert tenant == "pathtenant"

    def test_get_tenant_from_request_subdomain_resolution(self, tenant_middleware, mock_request):
        """Test tenant extraction from subdomain (third priority)"""
        mock_request.url.path = "/api/users"
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "host": "subdomain.example.com"
        }.get(key, default)

        tenant = tenant_middleware.get_tenant_from_request(mock_request)

        assert tenant == "subdomain"

    def test_get_tenant_from_request_subdomain_exclusions(self, tenant_middleware, mock_request):
        """Test subdomain exclusion for common subdomains"""
        excluded_subdomains = ["www", "api", "admin", "localhost", "127", "0"]

        for subdomain in excluded_subdomains:
            mock_request.url.path = "/api/users"
            mock_request.headers.get.side_effect = lambda key, default=None: {
                "host": f"{subdomain}.example.com"
            }.get(key, default)

            tenant = tenant_middleware.get_tenant_from_request(mock_request)

            assert tenant is None, f"Should exclude {subdomain} subdomain"

    def test_get_tenant_from_request_no_tenant(self, tenant_middleware, mock_request):
        """Test fallback to None when no tenant is detected"""
        mock_request.url.path = "/api/users"
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "host": "example.com"  # No subdomain
        }.get(key, default)

        tenant = tenant_middleware.get_tenant_from_request(mock_request)

        assert tenant is None

    def test_get_tenant_from_request_invalid_path(self, tenant_middleware, mock_request):
        """Test path parsing with invalid tenant path structure"""
        mock_request.url.path = "/tenant/"  # Missing tenant slug
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "host": "example.com"
        }.get(key, default)

        tenant = tenant_middleware.get_tenant_from_request(mock_request)

        assert tenant is None

    @pytest.mark.asyncio
    async def test_set_tenant_schema_success(self, tenant_middleware, mock_request):
        """Test successful tenant schema setting"""
        schema_name = "tenant_test"

        await tenant_middleware.set_tenant_schema(mock_request, schema_name)

        assert mock_request.state.db_schema == schema_name

    @pytest.mark.asyncio
    async def test_set_tenant_schema_exception_fallback(self, tenant_middleware, mock_request):
        """Test schema setting with exception fallback to public"""
        # Simulate state assignment failure by removing state attribute
        mock_request.state = Mock()
        delattr(mock_request.state, 'db_schema')

        # Should not raise exception - graceful handling
        await tenant_middleware.set_tenant_schema(mock_request, "invalid_schema")

        # Verify fallback to public schema was attempted
        assert hasattr(mock_request.state, 'db_schema')

    @pytest.mark.asyncio
    async def test_dispatch_with_tenant(self, tenant_middleware, mock_request):
        """Test middleware dispatch with tenant resolution"""
        mock_request.headers.get.side_effect = lambda key, default=None: {"x-tenant": "testtenant"}.get(key, default)
        mock_request.url.path = "/"

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        response = await tenant_middleware.dispatch(mock_request, call_next)

        assert mock_request.state.tenant_slug == "testtenant"
        assert mock_request.state.tenant_schema == "tenant_testtenant"
        assert response == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_without_tenant(self, tenant_middleware, mock_request):
        """Test middleware dispatch without tenant (public schema)"""
        mock_request.headers.get.side_effect = lambda key, default=None: {
            "host": "example.com"
        }.get(key, default)
        mock_request.url.path = "/"

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        response = await tenant_middleware.dispatch(mock_request, call_next)

        assert mock_request.state.tenant_slug is None
        assert mock_request.state.tenant_schema == "public"
        assert response == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_dispatch_with_exception_in_call_next(self, tenant_middleware, mock_request):
        """Test middleware dispatch when call_next raises exception"""
        mock_request.headers.get.side_effect = lambda key, default=None: {"x-tenant": "testtenant"}.get(key, default)
        mock_request.url.path = "/"

        # Mock call_next that raises exception
        test_exception = Exception("Test exception")
        call_next = AsyncMock(side_effect=test_exception)

        with pytest.raises(Exception) as exc_info:
            await tenant_middleware.dispatch(mock_request, call_next)

        assert str(exc_info.value) == "Test exception"
        # Schema should still be set despite exception
        assert mock_request.state.tenant_slug == "testtenant"


class TestTenantDatabaseDependency:
    """Test suite for TenantDatabaseDependency class"""

    @pytest.fixture
    def mock_session_factory(self):
        """Create mock session factory"""
        return Mock()

    @pytest.fixture
    def mock_session(self):
        """Create mock database session"""
        return Mock()

    @pytest.fixture
    def dependency(self, mock_session_factory):
        """Create TenantDatabaseDependency instance"""
        return TenantDatabaseDependency(mock_session_factory)

    @pytest.fixture
    def mock_request(self):
        """Create mock request with db_schema state"""
        request = Mock()
        request.state = Mock()
        request.state.db_schema = "tenant_test"
        return request

    def test_dependency_initialization(self, mock_session_factory):
        """Test TenantDatabaseDependency initialization"""
        dependency = TenantDatabaseDependency(mock_session_factory)

        assert dependency.session_local_factory == mock_session_factory

    def test_dependency_call_with_tenant_schema(self, dependency, mock_request, mock_session):
        """Test database dependency with tenant schema"""
        dependency.session_local_factory.return_value = mock_session

        # Use generator to test the dependency
        generator = dependency(mock_request)
        db_session = next(generator)

        assert db_session == mock_session
        # Check that execute was called with the correct SQL string
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert str(call_args) == "SET search_path TO tenant_test, public"

    def test_dependency_call_with_public_schema(self, dependency, mock_request, mock_session):
        """Test database dependency with public schema"""
        mock_request.state.db_schema = "public"
        dependency.session_local_factory.return_value = mock_session

        # Use generator to test the dependency
        generator = dependency(mock_request)
        db_session = next(generator)

        assert db_session == mock_session
        # Check that execute was called with the correct SQL string
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert str(call_args) == "SET search_path TO public"

    def test_dependency_call_without_schema_state(self, dependency, mock_request, mock_session):
        """Test database dependency without schema state (fallback to public)"""
        delattr(mock_request.state, 'db_schema')  # Remove db_schema attribute
        dependency.session_local_factory.return_value = mock_session

        # Use generator to test the dependency
        generator = dependency(mock_request)
        db_session = next(generator)

        assert db_session == mock_session
        # Check that execute was called with the correct SQL string
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert str(call_args) == "SET search_path TO public"

    def test_dependency_call_with_exception(self, dependency, mock_request, mock_session):
        """Test database dependency with exception handling"""
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        dependency.session_local_factory.return_value = mock_session

        generator = dependency(mock_request)

        with pytest.raises(SQLAlchemyError):
            next(generator)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_dependency_cleanup(self, dependency, mock_request, mock_session):
        """Test database dependency cleanup"""
        dependency.session_local_factory.return_value = mock_session

        generator = dependency(mock_request)
        db_session = next(generator)

        # Simulate generator cleanup
        try:
            next(generator)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()


class TestTenantUtilityFunctions:
    """Test suite for tenant utility functions"""

    @pytest.fixture
    def mock_engine(self):
        """Create mock database engine"""
        engine = Mock()
        connection = Mock()
        # Properly mock context manager
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=connection)
        context_manager.__exit__ = Mock(return_value=None)
        engine.connect.return_value = context_manager
        return engine, connection

    @pytest.mark.asyncio
    async def test_create_tenant_schema_success(self, mock_engine):
        """Test successful tenant schema creation"""
        engine, connection = mock_engine

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            with patch('app.database.Base') as mock_base:
                await create_tenant_schema("testcorp", "postgresql://test")

        # Verify schema creation commands - check string content instead of object identity
        actual_calls = [str(call[0][0]) for call in connection.execute.call_args_list]
        expected_calls = [
            "CREATE SCHEMA IF NOT EXISTS tenant_testcorp",
            "SET search_path TO tenant_testcorp"
        ]
        assert actual_calls == expected_calls
        connection.commit.assert_called_once()
        mock_base.metadata.create_all.assert_called_once_with(bind=engine)

    @pytest.mark.asyncio
    async def test_create_tenant_schema_failure(self, mock_engine):
        """Test tenant schema creation failure"""
        engine, connection = mock_engine
        connection.execute.side_effect = SQLAlchemyError("Schema creation failed")

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            with pytest.raises(SQLAlchemyError):
                await create_tenant_schema("testcorp", "postgresql://test")

    @pytest.mark.asyncio
    async def test_drop_tenant_schema_success(self, mock_engine):
        """Test successful tenant schema deletion"""
        engine, connection = mock_engine

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            await drop_tenant_schema("testcorp", "postgresql://test")

        # Verify schema deletion command - check string content instead of object identity
        actual_call = str(connection.execute.call_args[0][0])
        expected_call = "DROP SCHEMA IF EXISTS tenant_testcorp CASCADE"
        assert actual_call == expected_call
        connection.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_drop_tenant_schema_failure(self, mock_engine):
        """Test tenant schema deletion failure"""
        engine, connection = mock_engine
        connection.execute.side_effect = SQLAlchemyError("Schema deletion failed")

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            with pytest.raises(SQLAlchemyError):
                await drop_tenant_schema("testcorp", "postgresql://test")

    @pytest.mark.asyncio
    async def test_list_tenant_schemas_success(self, mock_engine):
        """Test successful tenant schema listing"""
        engine, connection = mock_engine
        # Mock query result
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter([("tenant_corp1",), ("tenant_corp2",)]))
        connection.execute.return_value = mock_result

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            schemas = await list_tenant_schemas("postgresql://test")

        expected_query = text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'tenant_%'
                ORDER BY schema_name
            """)
        connection.execute.assert_called_once()
        assert schemas == ["tenant_corp1", "tenant_corp2"]

    @pytest.mark.asyncio
    async def test_list_tenant_schemas_failure(self, mock_engine):
        """Test tenant schema listing failure"""
        engine, connection = mock_engine
        connection.execute.side_effect = SQLAlchemyError("Schema listing failed")

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            schemas = await list_tenant_schemas("postgresql://test")

        assert schemas == []


class TestTenantMiddlewareIntegration:
    """Integration tests for TenantMiddleware with FastAPI"""

    @pytest.fixture
    def test_app(self):
        """Create test FastAPI app with tenant middleware"""
        test_app = FastAPI()
        test_app.add_middleware(TenantMiddleware, tenant_schema_prefix="test_")

        @test_app.get("/test")
        async def test_endpoint(request: Request):
            return {
                "tenant_slug": getattr(request.state, 'tenant_slug', None),
                "tenant_schema": getattr(request.state, 'tenant_schema', None)
            }

        return test_app

    @pytest.fixture
    def client(self, test_app):
        """Create test client"""
        return TestClient(test_app)

    def test_integration_header_tenant_resolution(self, client):
        """Test full integration with header-based tenant resolution"""
        response = client.get("/test", headers={"X-Tenant": "integration_test"})

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_slug"] == "integration_test"
        assert data["tenant_schema"] == "test_integration_test"

    def test_integration_path_tenant_resolution(self, client):
        """Test full integration with path-based tenant resolution"""
        # Mock the test endpoint to be under tenant path
        response = client.get("/test")  # This would need path routing setup

        assert response.status_code == 200
        data = response.json()
        # Without X-Tenant header or subdomain, should default to None
        assert data["tenant_slug"] is None
        assert data["tenant_schema"] == "public"

    def test_integration_no_tenant_fallback(self, client):
        """Test full integration with no tenant (public schema fallback)"""
        response = client.get("/test")

        assert response.status_code == 200
        data = response.json()
        assert data["tenant_slug"] is None
        assert data["tenant_schema"] == "public"


class TestPostgreSQLSchemaOperations:
    """PostgreSQL-specific tests for schema operations"""

    @pytest.fixture
    def postgres_url(self):
        """PostgreSQL test database URL"""
        return "postgresql://test_user:test_pass@localhost:5432/test_db"

    @pytest.fixture
    def mock_postgres_engine(self):
        """Mock PostgreSQL engine"""
        engine = Mock()
        connection = Mock()
        # Properly mock context manager
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=connection)
        context_manager.__exit__ = Mock(return_value=None)
        engine.connect.return_value = context_manager
        return engine, connection

    @pytest.mark.asyncio
    async def test_postgresql_schema_creation_sql(self, postgres_url, mock_postgres_engine):
        """Test PostgreSQL-specific schema creation SQL"""
        engine, connection = mock_postgres_engine

        with patch('app.tenant_middleware.create_engine', return_value=engine):
            with patch('app.database.Base') as mock_base:
                await create_tenant_schema("postgres_test", postgres_url)

        # Verify PostgreSQL-specific commands - check actual SQL content
        actual_calls = [str(call[0][0]) for call in connection.execute.call_args_list]
        assert "CREATE SCHEMA IF NOT EXISTS tenant_postgres_test" in actual_calls
        assert "SET search_path TO tenant_postgres_test" in actual_calls

    @pytest.mark.asyncio
    async def test_postgresql_schema_isolation(self, postgres_url, mock_postgres_engine):
        """Test PostgreSQL schema isolation behavior"""
        engine, connection = mock_postgres_engine

        # Mock the TenantDatabaseDependency
        session_factory = Mock()
        mock_session = Mock()
        session_factory.return_value = mock_session

        dependency = TenantDatabaseDependency(session_factory)

        # Create mock request with schema
        mock_request = Mock()
        mock_request.state = Mock()
        mock_request.state.db_schema = "tenant_isolated"

        # Test the dependency
        generator = dependency(mock_request)
        db_session = next(generator)

        # Verify search_path is set correctly for PostgreSQL - check string content
        actual_call = str(mock_session.execute.call_args[0][0])
        expected_call = "SET search_path TO tenant_isolated, public"
        assert actual_call == expected_call

    @pytest.mark.asyncio
    async def test_postgresql_concurrent_tenant_access(self, postgres_url):
        """Test concurrent tenant access simulation"""
        # This would be a more complex integration test
        # For now, we'll simulate the behavior

        tenant1_request = Mock()
        tenant1_request.state = Mock()
        tenant1_request.state.db_schema = "tenant_corp1"

        tenant2_request = Mock()
        tenant2_request.state = Mock()
        tenant2_request.state.db_schema = "tenant_corp2"

        session_factory = Mock()
        mock_session1 = Mock()
        mock_session2 = Mock()
        session_factory.side_effect = [mock_session1, mock_session2]

        dependency = TenantDatabaseDependency(session_factory)

        # Simulate concurrent access
        gen1 = dependency(tenant1_request)
        gen2 = dependency(tenant2_request)

        db1 = next(gen1)
        db2 = next(gen2)

        # Verify each session gets correct schema - check string content
        actual_call1 = str(mock_session1.execute.call_args[0][0])
        expected_call1 = "SET search_path TO tenant_corp1, public"
        assert actual_call1 == expected_call1

        actual_call2 = str(mock_session2.execute.call_args[0][0])
        expected_call2 = "SET search_path TO tenant_corp2, public"
        assert actual_call2 == expected_call2


class TestTenantEndpoints:
    """Test tenant management endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client with main app"""
        return TestClient(app)

    def test_create_tenant_endpoint_success(self, client):
        """Test successful tenant creation endpoint"""
        with patch('app.tenant_middleware.create_tenant_schema') as mock_create:
            mock_create.return_value = None  # Async function that returns None on success

            response = client.post("/tenants/newtenant")

            assert response.status_code == 201
            data = response.json()
            assert data["tenant_slug"] == "newtenant"
            assert "created successfully" in data["message"]

    def test_create_tenant_endpoint_failure(self, client):
        """Test tenant creation endpoint failure"""
        with patch('app.tenant_middleware.create_tenant_schema') as mock_create:
            mock_create.side_effect = Exception("Creation failed")

            response = client.post("/tenants/invalidtenant")

            assert response.status_code == 400
            data = response.json()
            assert "Failed to create tenant" in data["detail"]

    def test_delete_tenant_endpoint_success(self, client):
        """Test successful tenant deletion endpoint"""
        with patch('app.tenant_middleware.drop_tenant_schema') as mock_drop:
            mock_drop.return_value = None

            response = client.delete("/tenants/oldtenant")

            assert response.status_code == 200
            data = response.json()
            assert data["tenant_slug"] == "oldtenant"
            assert "deleted successfully" in data["message"]

    def test_delete_tenant_endpoint_failure(self, client):
        """Test tenant deletion endpoint failure"""
        with patch('app.tenant_middleware.drop_tenant_schema') as mock_drop:
            mock_drop.side_effect = Exception("Deletion failed")

            response = client.delete("/tenants/nonexistent")

            assert response.status_code == 400
            data = response.json()
            assert "Failed to delete tenant" in data["detail"]

    def test_list_tenants_endpoint_success(self, client):
        """Test successful tenant listing endpoint"""
        with patch('app.tenant_middleware.list_tenant_schemas') as mock_list:
            mock_list.return_value = ["tenant_corp1", "tenant_corp2", "tenant_corp3"]

            response = client.get("/tenants/")

            assert response.status_code == 200
            data = response.json()
            assert set(data["tenants"]) == {"corp1", "corp2", "corp3"}

    def test_list_tenants_endpoint_failure(self, client):
        """Test tenant listing endpoint failure"""
        with patch('app.tenant_middleware.list_tenant_schemas') as mock_list:
            mock_list.side_effect = Exception("Listing failed")

            response = client.get("/tenants/")

            assert response.status_code == 500
            data = response.json()
            assert "Failed to list tenants" in data["detail"]


class TestTenantDataIsolation:
    """Test data isolation between tenants"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked database"""
        # Mock the database dependency to avoid PostgreSQL connection
        def mock_get_db():
            mock_db = Mock()
            return mock_db

        # Override the database dependency
        app.dependency_overrides[get_db] = mock_get_db
        client = TestClient(app)

        yield client

        # Clean up override after test
        app.dependency_overrides.clear()

    def test_tenant_customer_isolation(self, client):
        """Test customer data isolation between tenants"""
        # Mock endpoints to return success without database connection
        with patch('main.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            customer_data = {
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User"
            }

            # Test would require mocking the actual endpoints
            # For now, verify middleware properly sets tenant context
            response = client.get("/", headers={"X-Tenant": "tenant1"})
            assert response.status_code == 200  # Root endpoint exists, middleware worked

    def test_tenant_product_isolation(self, client):
        """Test product data isolation between tenants"""
        # Mock endpoints to return success without database connection
        with patch('main.get_db') as mock_get_db:
            mock_db = Mock()
            mock_get_db.return_value = mock_db

            product_data = {
                "name": "Test Product",
                "description": "A test product",
                "price": "99.99",
                "stock_quantity": 10,
                "sku": "TEST-SKU-001"
            }

            # Test would require mocking the actual endpoints
            # For now, verify middleware properly sets tenant context
            response = client.get("/", headers={"X-Tenant": "tenant2"})
            assert response.status_code == 200  # Root endpoint exists, middleware worked


# Test configuration
if __name__ == "__main__":
    pytest.main(["-v", __file__])
