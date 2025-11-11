import csv
import sys

from django.core.management.base import BaseCommand
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'List all tenants and their status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active tenants'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information'
        )
        parser.add_argument(
            '--format',
            choices=['table', 'json', 'csv'],
            default='table',
            help='Output format (default: table)'
        )

    def handle(self, *args, **options):
        active_only = options['active_only']
        detailed = options['detailed']
        output_format = options['format']

        # Query tenants
        tenants = Tenant.objects.select_related('owner').prefetch_related('users')
        if active_only:
            tenants = tenants.filter(is_active=True)

        if not tenants.exists():
            self.stdout.write('No tenants found.')
            return

        if output_format == 'json':
            self.output_json(tenants, detailed)
        elif output_format == 'csv':
            self.output_csv(tenants, detailed)
        else:
            self.output_table(tenants, detailed)

    def output_table(self, tenants, detailed):
        """Output tenants in table format."""
        if detailed:
            # Detailed table
            self.stdout.write(
                f"{'Name':<20} {'Schema':<20} {'Owner':<15} {'Users':<6} {'Status':<8} {'Created':<12} {'Domain':<30}"
            )
            self.stdout.write("-" * 120)

            for tenant in tenants:
                status = "Active" if tenant.is_active else "Inactive"
                created = tenant.created_at.strftime("%Y-%m-%d")
                domain = tenant.domain or tenant.subdomain or "-"

                self.stdout.write(
                    f"{tenant.name:<20} {tenant.schema_name:<20} {tenant.owner.username:<15} "
                    f"{tenant.user_count:<6} {status:<8} {created:<12} {domain:<30}"
                )
        else:
            # Simple table
            self.stdout.write(f"{'Name':<25} {'Schema':<25} {'Status':<10} {'Users':<6}")
            self.stdout.write("-" * 70)

            for tenant in tenants:
                status = "Active" if tenant.is_active else "Inactive"
                self.stdout.write(
                    f"{tenant.name:<25} {tenant.schema_name:<25} {status:<10} {tenant.user_count:<6}"
                )

        self.stdout.write(f"\nTotal tenants: {tenants.count()}")

    def output_json(self, tenants, detailed):
        """Output tenants in JSON format."""
        import json

        tenant_data = []
        for tenant in tenants:
            data = {
                'name': tenant.name,
                'schema_name': tenant.schema_name,
                'is_active': tenant.is_active,
                'user_count': tenant.user_count,
                'owner': tenant.owner.username,
                'created_at': tenant.created_at.isoformat(),
            }

            if detailed:
                data.update({
                    'id': str(tenant.id),
                    'domain': tenant.domain,
                    'subdomain': tenant.subdomain,
                    'max_users': tenant.max_users,
                    'storage_limit_gb': tenant.storage_limit_gb,
                    'updated_at': tenant.updated_at.isoformat(),
                    'is_over_user_limit': tenant.is_over_user_limit,
                })

            tenant_data.append(data)

        self.stdout.write(json.dumps(tenant_data, indent=2))

    def output_csv(self, tenants, detailed):
        """Output tenants in CSV format."""

        writer = csv.writer(sys.stdout)

        if detailed:
            headers = [
                'Name', 'Schema Name', 'Owner', 'Users', 'Max Users', 'Status',
                'Domain', 'Subdomain', 'Storage Limit GB', 'Created At', 'Updated At'
            ]
        else:
            headers = ['Name', 'Schema Name', 'Owner', 'Users', 'Status', 'Created At']

        writer.writerow(headers)

        for tenant in tenants:
            if detailed:
                row = [
                    tenant.name,
                    tenant.schema_name,
                    tenant.owner.username,
                    tenant.user_count,
                    tenant.max_users,
                    'Active' if tenant.is_active else 'Inactive',
                    tenant.domain or '',
                    tenant.subdomain or '',
                    tenant.storage_limit_gb,
                    tenant.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    tenant.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]
            else:
                row = [
                    tenant.name,
                    tenant.schema_name,
                    tenant.owner.username,
                    tenant.user_count,
                    'Active' if tenant.is_active else 'Inactive',
                    tenant.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                ]

            writer.writerow(row)
