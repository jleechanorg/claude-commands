from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.core.management import call_command
from django.core.exceptions import ValidationError
from django.conf import settings
from io import StringIO
import uuid
from .models import Tenant

class TenantModelTest(TestCase):
    def test_tenant_creation(self):
        """Test that a tenant can be created with valid data"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            schema_name="test_tenant_schema"
        )
        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.slug, "test-tenant")
        self.assertEqual(tenant.schema_name, "test_tenant_schema")
        self.assertTrue(isinstance(tenant.id, uuid.UUID))

    def test_tenant_slug_uniqueness(self):
        """Test that tenant slugs must be unique"""
        Tenant.objects.create(name="Tenant 1", slug="tenant", schema_name="tenant1")
        with self.assertRaises(Exception):
            Tenant.objects.create(name="Tenant 2", slug="tenant", schema_name="tenant2")

    def test_tenant_schema_name_uniqueness(self):
        """Test that schema names must be unique"""
        Tenant.objects.create(name="Tenant 1", slug="tenant1", schema_name="tenant")
        with self.assertRaises(Exception):
            Tenant.objects.create(name="Tenant 2", slug="tenant2", schema_name="tenant")

    def test_tenant_string_representation(self):
        """Test the string representation of a tenant"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            schema_name="test_tenant_schema"
        )
        self.assertEqual(str(tenant), "Test Tenant")

    def test_tenant_validation(self):
        """Test tenant validation"""
        tenant = Tenant(name="", slug="", schema_name="")
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_tenant_domain_url_property(self):
        """Test the domain_url property"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            schema_name="test_tenant_schema"
        )
        expected_url = f"https://{tenant.slug}.{getattr(settings, 'TENANT_DOMAIN', 'localhost')}"
        self.assertEqual(tenant.domain_url, expected_url)

class CreateTenantSchemaCommandTest(TransactionTestCase):
    def test_create_tenant_schema_command(self):
        """Test the create_tenant_schema management command"""
        # Create a tenant
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            schema_name="test_tenant_schema"
        )

        # Capture command output
        out = StringIO()

        # Call the management command
        call_command('create_tenant_schema', tenant.slug, stdout=out)

        # Check that the command output contains success message
        self.assertIn(f"Schema '{tenant.schema_name}' created successfully", out.getvalue())

        # Verify schema exists by checking if we can connect to it
        with connection.cursor() as cursor:
            cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [tenant.schema_name])
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[0], tenant.schema_name)

class DeleteTenantSchemaCommandTest(TransactionTestCase):
    def test_delete_tenant_schema_command(self):
        """Test the delete_tenant_schema management command"""
        # Create a tenant
        tenant = Tenant.objects.create(
            name="Test Tenant",
            slug="test-tenant",
            schema_name="test_tenant_schema"
        )

        # First create the schema
        out = StringIO()
        call_command('create_tenant_schema', tenant.slug, stdout=out)

        # Then delete it
        out = StringIO()
        call_command('delete_tenant_schema', tenant.slug, stdout=out)

        # Check that the command output contains success message
        self.assertIn(f"Schema '{tenant.schema_name}' deleted successfully", out.getvalue())

        # Verify schema no longer exists
        with connection.cursor() as cursor:
            cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [tenant.schema_name])
            result = cursor.fetchone()
            self.assertIsNone(result)
