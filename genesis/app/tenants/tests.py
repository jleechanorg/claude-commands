import uuid
from io import StringIO

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase

from .models import Tenant, TenantMembership


class TenantModelTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )

    def test_tenant_creation(self):
        """Test that a tenant can be created with valid data"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user
        )
        self.assertEqual(tenant.name, "Test Tenant")
        self.assertEqual(tenant.schema_name, "test_tenant_schema")
        self.assertEqual(tenant.owner, self.user)
        self.assertTrue(isinstance(tenant.id, uuid.UUID))
        self.assertTrue(tenant.is_active)
        self.assertEqual(tenant.max_users, 100)
        self.assertEqual(tenant.storage_limit_gb, 10)

    def test_tenant_schema_name_uniqueness(self):
        """Test that schema names must be unique"""
        Tenant.objects.create(
            name="Tenant 1",
            schema_name="tenant_schema",
            owner=self.user
        )
        user2 = User.objects.create_user(
            username='testowner2',
            email='owner2@test.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            Tenant.objects.create(
                name="Tenant 2",
                schema_name="tenant_schema",
                owner=user2
            )

    def test_tenant_name_uniqueness(self):
        """Test that tenant names must be unique"""
        Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_schema_1",
            owner=self.user
        )
        user2 = User.objects.create_user(
            username='testowner2',
            email='owner2@test.com',
            password='testpass123'
        )
        with self.assertRaises(Exception):
            Tenant.objects.create(
                name="Test Tenant",
                schema_name="test_schema_2",
                owner=user2
            )

    def test_tenant_string_representation(self):
        """Test the string representation of a tenant"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user
        )
        self.assertEqual(str(tenant), "Test Tenant (test_tenant_schema)")

    def test_tenant_validation(self):
        """Test tenant validation"""
        tenant = Tenant(name="", schema_name="", owner=self.user)
        with self.assertRaises(ValidationError):
            tenant.full_clean()

    def test_tenant_auto_schema_generation(self):
        """Test auto-generation of schema_name from name"""
        tenant = Tenant(
            name="Test Tenant Name",
            owner=self.user
        )
        tenant.save()
        # Schema name should be auto-generated from name
        self.assertTrue(tenant.schema_name)
        self.assertIn("test", tenant.schema_name.lower())

    def test_tenant_domain_and_subdomain(self):
        """Test tenant domain and subdomain fields"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            domain="example.com",
            subdomain="test",
            owner=self.user
        )
        self.assertEqual(tenant.domain, "example.com")
        self.assertEqual(tenant.subdomain, "test")

    def test_tenant_status_fields(self):
        """Test tenant status and configuration fields"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user,
            is_active=False,
            max_users=50,
            storage_limit_gb=5
        )
        self.assertFalse(tenant.is_active)
        self.assertEqual(tenant.max_users, 50)
        self.assertEqual(tenant.storage_limit_gb, 5)

    def test_tenant_timestamps(self):
        """Test that timestamps are automatically set"""
        tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user
        )
        self.assertIsNotNone(tenant.created_at)
        self.assertIsNotNone(tenant.updated_at)


class TenantMembershipTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.owner = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )
        self.user = User.objects.create_user(
            username='testuser',
            email='user@test.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.owner
        )

    def test_tenant_membership_creation(self):
        """Test creating a tenant membership"""
        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantMembership.Role.VIEWER
        )
        self.assertEqual(membership.tenant, self.tenant)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, TenantMembership.Role.VIEWER)
        self.assertTrue(membership.is_active)


class CreateTenantCommandTest(TransactionTestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )

    def test_create_tenant_command(self):
        """Test the create_tenant management command"""
        out = StringIO()

        # Call the management command
        call_command(
            'create_tenant',
            'Test Tenant',
            '--schema-name', 'test_tenant_schema',
            '--owner', self.user.username,
            stdout=out
        )

        # Check that tenant was created
        tenant = Tenant.objects.get(schema_name='test_tenant_schema')
        self.assertEqual(tenant.name, 'Test Tenant')
        self.assertEqual(tenant.owner, self.user)

        # Check command output
        self.assertIn("created successfully", out.getvalue())


class DeleteTenantCommandTest(TransactionTestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user
        )

    def test_delete_tenant_command(self):
        """Test the delete_tenant management command"""
        out = StringIO()

        # Call the management command
        call_command(
            'delete_tenant',
            self.tenant.schema_name,
            '--confirm',
            stdout=out
        )

        # Check that tenant was deleted
        with self.assertRaises(Tenant.DoesNotExist):
            Tenant.objects.get(schema_name='test_tenant_schema')

        # Check command output
        self.assertIn("deleted successfully", out.getvalue())


class ListTenantsCommandTest(TestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )
        Tenant.objects.create(
            name="Tenant 1",
            schema_name="tenant1_schema",
            owner=self.user
        )
        Tenant.objects.create(
            name="Tenant 2",
            schema_name="tenant2_schema",
            owner=self.user,
            is_active=False
        )

    def test_list_tenants_command(self):
        """Test the list_tenants management command"""
        out = StringIO()

        # Call the management command
        call_command('list_tenants', stdout=out)

        output = out.getvalue()
        self.assertIn("Tenant 1", output)
        self.assertIn("Tenant 2", output)
        self.assertIn("tenant1_schema", output)
        self.assertIn("tenant2_schema", output)

    def test_list_tenants_active_only(self):
        """Test listing only active tenants"""
        out = StringIO()

        # Call the management command with active-only flag
        call_command('list_tenants', '--active-only', stdout=out)

        output = out.getvalue()
        self.assertIn("Tenant 1", output)
        self.assertNotIn("Tenant 2", output)


class MigrateTenantCommandTest(TransactionTestCase):
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testowner',
            email='owner@test.com',
            password='testpass123'
        )
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant_schema",
            owner=self.user
        )

    def test_migrate_tenant_command(self):
        """Test the migrate_tenant management command"""
        out = StringIO()

        # Call the management command
        call_command(
            'migrate_tenant',
            self.tenant.schema_name,
            stdout=out
        )

        # Check command output contains success indication
        output = out.getvalue()
        self.assertTrue(len(output) > 0)  # Command should produce some output
