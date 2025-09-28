from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
import uuid


class Tenant(models.Model):
    """
    Multi-tenant model for schema isolation and tenant management.
    Each tenant represents an isolated environment with its own schema.
    """

    # Core identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Human-readable tenant name"
    )
    schema_name = models.CharField(
        max_length=63,  # PostgreSQL identifier limit
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z][a-z0-9_]*$',
                message='Schema name must start with a letter and contain only lowercase letters, numbers, and underscores'
            )
        ],
        help_text="Database schema name for this tenant"
    )

    # Tenant metadata
    domain = models.CharField(
        max_length=253,  # DNS limit
        unique=True,
        null=True,
        blank=True,
        help_text="Primary domain for this tenant"
    )
    subdomain = models.CharField(
        max_length=63,
        unique=True,
        null=True,
        blank=True,
        help_text="Subdomain identifier"
    )

    # Status and configuration
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this tenant is active and accessible"
    )
    max_users = models.PositiveIntegerField(
        default=100,
        help_text="Maximum number of users allowed for this tenant"
    )
    storage_limit_gb = models.PositiveIntegerField(
        default=10,
        help_text="Storage limit in gigabytes"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='owned_tenants',
        help_text="Primary owner/administrator of this tenant"
    )
    users = models.ManyToManyField(
        User,
        through='TenantMembership',
        related_name='tenant_memberships',
        blank=True
    )

    class Meta:
        db_table = 'public_tenant'  # Store in public schema
        ordering = ['name']
        indexes = [
            models.Index(fields=['schema_name']),
            models.Index(fields=['domain']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} ({self.schema_name})"

    def save(self, *args, **kwargs):
        """Auto-generate schema_name from name if not provided."""
        if not self.schema_name and self.name:
            # Convert name to valid schema name
            self.schema_name = self.name.lower().replace(' ', '_').replace('-', '_')
            # Remove special characters
            import re
            self.schema_name = re.sub(r'[^a-z0-9_]', '', self.schema_name)
            # Ensure it starts with a letter
            if self.schema_name and not self.schema_name[0].isalpha():
                self.schema_name = f"tenant_{self.schema_name}"
        super().save(*args, **kwargs)

    @property
    def user_count(self):
        """Get current number of users in this tenant."""
        return self.users.filter(tenantmembership__is_active=True).count()

    @property
    def is_over_user_limit(self):
        """Check if tenant has exceeded user limit."""
        return self.user_count > self.max_users


class TenantMembership(models.Model):
    """
    Through model for Tenant-User relationship with additional metadata.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Administrator'
        MANAGER = 'manager', 'Manager'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('tenant', 'user')
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.tenant.name} ({self.role})"


class TenantConfiguration(models.Model):
    """
    Tenant-specific configuration settings.
    """
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name='configuration'
    )

    # Feature flags
    enable_graphql = models.BooleanField(default=True)
    enable_api_access = models.BooleanField(default=True)
    enable_file_uploads = models.BooleanField(default=True)
    enable_notifications = models.BooleanField(default=True)

    # Customization
    theme_color = models.CharField(
        max_length=7,
        default='#007bff',
        help_text="Primary theme color (hex)"
    )
    logo_url = models.URLField(blank=True, null=True)
    custom_css = models.TextField(blank=True)

    # Integration settings
    webhook_url = models.URLField(blank=True, null=True)
    api_rate_limit = models.PositiveIntegerField(
        default=1000,
        help_text="API requests per hour"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'public_tenant_configuration'

    def __str__(self):
        return f"Config for {self.tenant.name}"
