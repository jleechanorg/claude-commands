from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'schema_name', 'created_at')
    search_fields = ('name', 'slug')
    readonly_fields = ('created_at', 'updated_at')
