from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.contrib.auth.models import User
from tenants.models import Tenant, TenantConfiguration
import logging


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create a new tenant with isolated schema'

    def add_arguments(self, parser):
        parser.add_argument(
            'name',
            type=str,
            help='Tenant name'
        )
        parser.add_argument(
            '--schema-name',
            type=str,
            help='Custom schema name (auto-generated if not provided)'
        )
        parser.add_argument(
            '--domain',
            type=str,
            help='Primary domain for the tenant'
        )
        parser.add_argument(
            '--subdomain',
            type=str,
            help='Subdomain identifier'
        )
        parser.add_argument(
            '--owner',
            type=str,
            help='Username of the tenant owner'
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=100,
            help='Maximum number of users (default: 100)'
        )
        parser.add_argument(
            '--storage-limit',
            type=int,
            default=10,
            help='Storage limit in GB (default: 10)'
        )
        parser.add_argument(
            '--skip-schema',
            action='store_true',
            help='Skip creating the database schema'
        )

    def handle(self, *args, **options):
        name = options['name']
        schema_name = options.get('schema_name')
        domain = options.get('domain')
        subdomain = options.get('subdomain')
        owner_username = options.get('owner')
        max_users = options['max_users']
        storage_limit = options['storage_limit']
        skip_schema = options['skip_schema']

        try:
            with transaction.atomic():
                # Get or create owner
                if owner_username:
                    try:
                        owner = User.objects.get(username=owner_username)
                    except User.DoesNotExist:
                        raise CommandError(f'User "{owner_username}" does not exist')
                else:
                    # Create a default admin user for the tenant
                    admin_username = f"{name.lower().replace(' ', '_')}_admin"
                    owner, created = User.objects.get_or_create(
                        username=admin_username,
                        defaults={
                            'email': f'{admin_username}@localhost',
                            'is_staff': True,
                            'is_active': True
                        }
                    )
                    if created:
                        owner.set_password('admin123')  # Default password
                        owner.save()
                        self.stdout.write(
                            self.style.WARNING(
                                f'Created admin user: {admin_username} with password: admin123'
                            )
                        )

                # Create tenant
                tenant = Tenant.objects.create(
                    name=name,
                    schema_name=schema_name,
                    domain=domain,
                    subdomain=subdomain,
                    owner=owner,
                    max_users=max_users,
                    storage_limit_gb=storage_limit
                )

                # Create tenant configuration
                TenantConfiguration.objects.create(tenant=tenant)

                # Create database schema if not skipped
                if not skip_schema:
                    self.create_tenant_schema(tenant.schema_name)

                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully created tenant "{tenant.name}" with schema "{tenant.schema_name}"'
                    )
                )

        except Exception as e:
            raise CommandError(f'Error creating tenant: {str(e)}')

    def create_tenant_schema(self, schema_name):
        """Create a new PostgreSQL schema for the tenant."""
        try:
            with connection.cursor() as cursor:
                # Create the schema
                cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')

                # Set search path to include the new schema
                cursor.execute(f'SET search_path TO "{schema_name}", public')

                # Run migrations for the tenant schema
                from django.core.management import call_command
                call_command('migrate', verbosity=0, interactive=False)

                self.stdout.write(
                    self.style.SUCCESS(f'Created database schema: {schema_name}')
                )

        except Exception as e:
            logger.error(f"Failed to create schema {schema_name}: {str(e)}")
            raise CommandError(f'Failed to create database schema: {str(e)}')
