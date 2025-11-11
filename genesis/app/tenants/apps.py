from django.apps import AppConfig


class TenantsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenants'
    verbose_name = 'Multi-Tenant Management'

    def ready(self):
        """Initialize tenant-specific configurations when app starts."""
