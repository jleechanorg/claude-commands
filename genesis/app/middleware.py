import logging

from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """
    Multi-tenant middleware that routes requests to appropriate PostgreSQL schemas
    based on subdomain or header-based tenant identification.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Determine tenant from request
        tenant_slug = self.get_tenant_from_request(request)

        if tenant_slug:
            # Set database schema for this tenant
            schema_name = f"{settings.TENANT_SCHEMA_PREFIX}{tenant_slug}"
            self.set_tenant_schema(schema_name)

            # Store tenant info in request for use in views
            request.tenant_slug = tenant_slug
            request.tenant_schema = schema_name
        else:
            # Default to public schema
            self.set_tenant_schema('public')
            request.tenant_slug = None
            request.tenant_schema = 'public'

        response = self.get_response(request)

        # Reset to public schema after request
        self.set_tenant_schema('public')

        return response

    def get_tenant_from_request(self, request):
        """
        Extract tenant identifier from request.
        Priority: 1) X-Tenant header, 2) path, 3) subdomain, 4) None (public)
        """
        # Method 1: Check for X-Tenant header
        tenant_header = request.META.get('HTTP_X_TENANT')
        if tenant_header:
            return tenant_header.strip().lower()

        # Method 2: Check for tenant in path (higher priority than subdomain)
        if request.path.startswith('/tenant/'):
            path_parts = request.path.strip('/').split('/')
            if len(path_parts) >= 2 and path_parts[0] == 'tenant':
                return path_parts[1].lower()

        # Method 3: Extract from subdomain
        try:
            host = request.get_host()
            if '.' in host:
                parts = host.split('.')
                # Only extract subdomain if there are at least 3 parts (subdomain.domain.tld)
                # This prevents extracting 'example' from 'example.com'
                if len(parts) >= 3:
                    subdomain = parts[0]
                    # Skip common subdomains
                    if subdomain not in ['www', 'api', 'admin']:
                        return subdomain.lower()
        except (KeyError, AttributeError):
            # If get_host() fails (e.g., in test environment), skip subdomain detection
            pass

        return None

    def set_tenant_schema(self, schema_name):
        """
        Set PostgreSQL search_path to the specified schema
        """
        try:
            if schema_name == 'public':
                with connection.cursor() as cursor:
                    cursor.execute("SET search_path TO public")
                    logger.debug(f"Switched to schema: {schema_name}")
            else:
                with connection.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {schema_name}, public")
                    logger.debug(f"Switched to schema: {schema_name}")
        except Exception as e:
            logger.error(f"Failed to set schema {schema_name}: {str(e)}")
            # Fall back to public schema
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")

    def process_exception(self, request, exception):
        """
        Reset to public schema if an exception occurs
        """
        self.set_tenant_schema('public')
