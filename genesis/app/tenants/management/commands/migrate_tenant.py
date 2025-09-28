from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from tenants.models import Tenant
from django.core.management import call_command
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run migrations for specific tenant schemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Tenant name or schema name (if not provided, migrates all active tenants)'
        )
        parser.add_argument(
            '--app',
            type=str,
            help='Specific app to migrate'
        )
        parser.add_argument(
            '--fake',
            action='store_true',
            help='Mark migrations as run without actually running them'
        )
        parser.add_argument(
            '--fake-initial',
            action='store_true',
            help='Mark initial migrations as run'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what migrations would be applied'
        )

    def handle(self, *args, **options):
        tenant_identifier = options.get('tenant')
        app_label = options.get('app')
        fake = options['fake']
        fake_initial = options['fake_initial']
        dry_run = options['dry_run']

        try:
            if tenant_identifier:
                # Migrate specific tenant
                tenant = self.get_tenant(tenant_identifier)
                self.migrate_tenant_schema(tenant, app_label, fake, fake_initial, dry_run)
            else:
                # Migrate all active tenants
                tenants = Tenant.objects.filter(is_active=True)
                if not tenants.exists():
                    self.stdout.write('No active tenants found.')
                    return

                self.stdout.write(f'Migrating {tenants.count()} active tenant(s)...')

                for tenant in tenants:
                    try:
                        self.migrate_tenant_schema(tenant, app_label, fake, fake_initial, dry_run)
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'Failed to migrate tenant "{tenant.name}": {str(e)}'
                            )
                        )
                        continue

                self.stdout.write(
                    self.style.SUCCESS('Completed migration for all active tenants')
                )

        except Exception as e:
            raise CommandError(f'Error during migration: {str(e)}')

    def get_tenant(self, identifier):
        """Get tenant by name or schema name."""
        try:
            return Tenant.objects.get(name=identifier)
        except Tenant.DoesNotExist:
            try:
                return Tenant.objects.get(schema_name=identifier)
            except Tenant.DoesNotExist:
                raise CommandError(f'Tenant "{identifier}" not found')

    def migrate_tenant_schema(self, tenant, app_label=None, fake=False, fake_initial=False, dry_run=False):
        """Run migrations for a specific tenant schema."""
        schema_name = tenant.schema_name

        self.stdout.write(f'Migrating schema: {schema_name} (tenant: {tenant.name})')

        try:
            # Set search path to tenant schema
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{schema_name}", public')

            # Build migration command arguments
            migrate_args = []
            migrate_kwargs = {
                'verbosity': 1,
                'interactive': False,
            }

            if app_label:
                migrate_args.append(app_label)

            if fake:
                migrate_kwargs['fake'] = True

            if fake_initial:
                migrate_kwargs['fake_initial'] = True

            if dry_run:
                migrate_kwargs['plan'] = True

            # Run migrations
            call_command('migrate', *migrate_args, **migrate_kwargs)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully migrated schema: {schema_name}'
                )
            )

        except Exception as e:
            logger.error(f"Failed to migrate schema {schema_name}: {str(e)}")
            raise CommandError(f'Failed to migrate schema {schema_name}: {str(e)}')

        finally:
            # Reset search path
            with connection.cursor() as cursor:
                cursor.execute('SET search_path TO public')
