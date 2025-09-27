from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from tenants.models import Tenant
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete a tenant and its associated schema'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Tenant name or schema name'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation'
        )
        parser.add_argument(
            '--keep-schema',
            action='store_true',
            help='Keep the database schema (only delete tenant record)'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']
        force = options['force']
        keep_schema = options['keep_schema']

        try:
            # Find tenant by name or schema_name
            try:
                tenant = Tenant.objects.get(name=identifier)
            except Tenant.DoesNotExist:
                try:
                    tenant = Tenant.objects.get(schema_name=identifier)
                except Tenant.DoesNotExist:
                    raise CommandError(f'Tenant "{identifier}" not found')

            # Confirmation prompt
            if not force:
                confirm = input(
                    f'Are you sure you want to delete tenant "{tenant.name}" '
                    f'with schema "{tenant.schema_name}"? '
                    f'This action cannot be undone. [y/N]: '
                )
                if confirm.lower() not in ['y', 'yes']:
                    self.stdout.write('Operation cancelled.')
                    return

            schema_name = tenant.schema_name

            with transaction.atomic():
                # Delete the tenant record (this will cascade to related objects)
                tenant.delete()

                # Drop the database schema if requested
                if not keep_schema:
                    self.drop_tenant_schema(schema_name)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully deleted tenant "{tenant.name}"'
                        f'{" and its schema" if not keep_schema else ""}'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error deleting tenant: {str(e)}')

    def drop_tenant_schema(self, schema_name):
        """Drop the PostgreSQL schema for the tenant."""
        try:
            with connection.cursor() as cursor:
                # Drop the schema and all its contents
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')

                self.stdout.write(
                    self.style.SUCCESS(f'Dropped database schema: {schema_name}')
                )

        except Exception as e:
            logger.error(f"Failed to drop schema {schema_name}: {str(e)}")
            raise CommandError(f'Failed to drop database schema: {str(e)}')
