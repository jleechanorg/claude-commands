from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from tenants.models import Tenant


class Command(BaseCommand):
    help = 'Delete database schema for a tenant'

    def add_arguments(self, parser):
        parser.add_argument('tenant_slug', type=str, help='Slug of the tenant')

    def handle(self, *args, **options):
        tenant_slug = options['tenant_slug']

        try:
            tenant = Tenant.objects.get(slug=tenant_slug)
        except Tenant.DoesNotExist:
            raise CommandError(f'Tenant with slug "{tenant_slug}" does not exist')

        # Drop schema using raw SQL
        with connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {tenant.schema_name} CASCADE")

        self.stdout.write(
            self.style.SUCCESS(f"Schema '{tenant.schema_name}' deleted successfully")
        )
