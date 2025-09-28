from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Tenant, TenantMembership, TenantConfiguration


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'schema_name', 'domain', 'owner', 'user_count_display',
        'is_active', 'storage_usage', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'max_users']
    search_fields = ['name', 'schema_name', 'domain', 'subdomain']
    readonly_fields = ['id', 'created_at', 'updated_at', 'user_count_display']
    raw_id_fields = ['owner']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'schema_name', 'owner', 'is_active')
        }),
        ('Domain Configuration', {
            'fields': ('domain', 'subdomain')
        }),
        ('Limits & Quotas', {
            'fields': ('max_users', 'storage_limit_gb', 'user_count_display')
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def user_count_display(self, obj):
        count = obj.user_count
        if count > obj.max_users:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}/{} (Over Limit!)</span>',
                count, obj.max_users
            )
        return f"{count}/{obj.max_users}"
    user_count_display.short_description = "Users"

    def storage_usage(self, obj):
        # This would be calculated based on actual usage
        usage_gb = 0.5  # Placeholder
        percentage = (usage_gb / obj.storage_limit_gb) * 100

        color = 'green'
        if percentage > 80:
            color = 'red'
        elif percentage > 60:
            color = 'orange'

        return format_html(
            '<span style="color: {};">{:.1f}/{} GB ({:.1f}%)</span>',
            color, usage_gb, obj.storage_limit_gb, percentage
        )
    storage_usage.short_description = "Storage"


@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'tenant', 'role', 'is_active', 'joined_at', 'last_accessed']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'user__email', 'tenant__name']
    raw_id_fields = ['user', 'tenant']
    readonly_fields = ['joined_at']

    fieldsets = (
        ('Membership Details', {
            'fields': ('tenant', 'user', 'role', 'is_active')
        }),
        ('Activity', {
            'fields': ('joined_at', 'last_accessed')
        })
    )


@admin.register(TenantConfiguration)
class TenantConfigurationAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'enable_graphql', 'enable_api_access', 'api_rate_limit', 'updated_at']
    list_filter = ['enable_graphql', 'enable_api_access', 'enable_file_uploads']
    search_fields = ['tenant__name']
    raw_id_fields = ['tenant']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Feature Flags', {
            'fields': (
                'enable_graphql', 'enable_api_access',
                'enable_file_uploads', 'enable_notifications'
            )
        }),
        ('Customization', {
            'fields': ('theme_color', 'logo_url', 'custom_css')
        }),
        ('Integration Settings', {
            'fields': ('webhook_url', 'api_rate_limit')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tenant')
