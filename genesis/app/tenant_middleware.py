"""
FastAPI Tenant-Aware Middleware
Multi-tenant middleware for FastAPI that routes requests to appropriate PostgreSQL schemas
based on subdomain, header, or path-based tenant identification.
"""
from fastapi import Request, HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
import os
from typing import Optional
from types import SimpleNamespace
from .database import Base

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Multi-tenant middleware that routes requests to appropriate PostgreSQL schemas
    based on subdomain, header, or path-based tenant identification.
    """

    def __init__(self, app, tenant_schema_prefix: str = "tenant_"):
        super().__init__(app)
        self.tenant_schema_prefix = tenant_schema_prefix
        # Use the same database URL as main app
        self.database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ecommerce")
        self.engine = create_engine(self.database_url)

    async def dispatch(self, request: Request, call_next):
        """
        Process request with tenant-aware database schema routing
        """
        # Determine tenant from request
        tenant_slug = self.get_tenant_from_request(request)

        if tenant_slug:
            # Set database schema for this tenant
            schema_name = f"{self.tenant_schema_prefix}{tenant_slug}"
            await self.set_tenant_schema(request, schema_name)

            # Store tenant info in request state for use in endpoints
            request.state.tenant_slug = tenant_slug
            request.state.tenant_schema = schema_name
        else:
            # Default to public schema
            await self.set_tenant_schema(request, 'public')
            request.state.tenant_slug = None
            request.state.tenant_schema = 'public'

        try:
            response = await call_next(request)
        finally:
            # Reset to public schema after request
            await self.set_tenant_schema(request, 'public')

        return response

    def get_tenant_from_request(self, request: Request) -> Optional[str]:
        """
        Extract tenant identifier from request.
        Priority: 1) X-Tenant header, 2) path-based, 3) subdomain, 4) None (public)
        """
        # Method 1: Check for X-Tenant header (highest priority for API calls)
        tenant_header = request.headers.get('x-tenant')  # lowercase key
        if tenant_header:
            return tenant_header.strip().lower()

        # Method 2: Check for tenant in path (second priority)
        if request.url.path.startswith('/tenant/'):
            path_parts = request.url.path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'tenant':
                return path_parts[1].lower()

        # Method 3: Extract from subdomain (third priority)
        try:
            host = request.headers.get('host')
            if host and '.' in host:
                parts = host.split('.')
                # Only consider it a subdomain if there are 3+ parts (subdomain.domain.tld)
                if len(parts) >= 3:
                    subdomain = parts[0]
                    # Skip common subdomains
                    if subdomain not in ['www', 'api', 'admin', 'localhost', '127', '0']:
                        return subdomain.lower()
        except (KeyError, AttributeError, IndexError):
            logger.debug("Failed to extract subdomain from host header")
            pass

        return None

    async def set_tenant_schema(self, request: Request, schema_name: str):
        """
        Set PostgreSQL search_path to the specified schema
        This method updates the connection for the current request context
        """
        try:
            # Ensure request.state exists
            if not hasattr(request, 'state') or request.state is None:
                request.state = SimpleNamespace()

            # Store the schema in request state for database dependency to use
            request.state.db_schema = schema_name

            # For logging purposes
            if schema_name == 'public':
                logger.debug(f"Request will use schema: {schema_name}")
            else:
                logger.debug(f"Request will use tenant schema: {schema_name}")

        except Exception as e:
            logger.error(f"Failed to set schema {schema_name}: {str(e)}")
            # Fall back to public schema - ensure state exists first
            try:
                if not hasattr(request, 'state') or request.state is None:
                    from unittest.mock import Mock
                    request.state = Mock()
                request.state.db_schema = 'public'
            except Exception:
                # If all else fails, just pass - the dependency will handle it
                pass


class TenantDatabaseDependency:
    """
    Database dependency that respects tenant context
    """

    def __init__(self, session_local_factory):
        self.session_local_factory = session_local_factory

    def __call__(self, request: Request):
        """
        Create database session with appropriate schema context
        """
        db = self.session_local_factory()
        try:
            # Get schema from request state (set by middleware)
            schema_name = getattr(request.state, 'db_schema', 'public')

            # Set the search path for this session
            if schema_name == 'public':
                db.execute(text("SET search_path TO public"))
            else:
                db.execute(text(f"SET search_path TO {schema_name}, public"))

            yield db
        except Exception as e:
            logger.error(f"Database session error: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()


def create_tenant_database_dependency(session_local):
    """
    Factory function to create tenant-aware database dependency
    """
    return TenantDatabaseDependency(session_local)


# Utility functions for tenant management
async def create_tenant_schema(tenant_slug: str, database_url: str):
    """
    Create a new tenant schema with all necessary tables
    """
    engine = create_engine(database_url)
    schema_name = f"tenant_{tenant_slug}"

    try:
        with engine.connect() as conn:
            # Create the schema
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))

            # Set search path and create tables
            conn.execute(text(f"SET search_path TO {schema_name}"))

            # Import and create tables (this would need to be adapted based on your models)
            # For now, we'll assume the Base metadata is available
            Base.metadata.create_all(bind=engine)

            conn.commit()
            logger.info(f"Created tenant schema: {schema_name}")

    except Exception as e:
        logger.error(f"Failed to create tenant schema {schema_name}: {str(e)}")
        raise


async def drop_tenant_schema(tenant_slug: str, database_url: str):
    """
    Drop a tenant schema and all its data (use with caution!)
    """
    engine = create_engine(database_url)
    schema_name = f"tenant_{tenant_slug}"

    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.commit()
            logger.info(f"Dropped tenant schema: {schema_name}")

    except Exception as e:
        logger.error(f"Failed to drop tenant schema {schema_name}: {str(e)}")
        raise


async def list_tenant_schemas(database_url: str) -> list:
    """
    List all tenant schemas in the database
    """
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name LIKE 'tenant_%'
                ORDER BY schema_name
            """))
            schemas = [row[0] for row in result]
            return schemas

    except Exception as e:
        logger.error(f"Failed to list tenant schemas: {str(e)}")
        return []
