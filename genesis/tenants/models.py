import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    schema_name = models.CharField(max_length=63, unique=True, help_text="Database schema name (max 63 characters)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tenants_tenant'

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        if not self.name:
            raise ValidationError({'name': 'Tenant name is required.'})
        if not self.slug:
            raise ValidationError({'slug': 'Tenant slug is required.'})
        if not self.schema_name:
            raise ValidationError({'schema_name': 'Schema name is required.'})
        if len(self.schema_name) > 63:
            raise ValidationError({'schema_name': 'Schema name cannot exceed 63 characters.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def domain_url(self):
        return f"https://{self.slug}.{getattr(settings, 'TENANT_DOMAIN', 'localhost')}"
