import unittest

from django.conf import settings
from django.test import TestCase, override_settings


class SettingsTestCase(TestCase):
    """
    Test suite for Django settings configuration
    Tests all critical settings with proper validation
    """

    def test_secret_key_required(self):
        """Test that SECRET_KEY is properly configured"""
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, '')
        # In production, should not use default insecure key
        if not settings.DEBUG:
            self.assertNotIn('django-insecure', settings.SECRET_KEY)

    def test_debug_setting(self):
        """Test DEBUG setting configuration"""
        # DEBUG should be boolean
        self.assertIsInstance(settings.DEBUG, bool)

    def test_allowed_hosts_configuration(self):
        """Test ALLOWED_HOSTS configuration"""
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        # Should contain at least one host
        self.assertGreater(len(settings.ALLOWED_HOSTS), 0)

    def test_database_config(self):
        """Test database configuration"""
        db_config = settings.DATABASES['default']
        self.assertEqual(db_config['ENGINE'], 'django.db.backends.postgresql')
        self.assertIn('OPTIONS', db_config)
        self.assertIn('options', db_config['OPTIONS'])
        self.assertIn('search_path=public', db_config['OPTIONS']['options'])

        # Required fields should be present
        required_fields = ['NAME', 'USER', 'PASSWORD', 'HOST', 'PORT']
        for field in required_fields:
            self.assertIn(field, db_config)
            self.assertIsNotNone(db_config[field])

    def test_installed_apps(self):
        """Test required Django apps are installed"""
        required_apps = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'graphene_django',
        ]
        for app in required_apps:
            self.assertIn(app, settings.INSTALLED_APPS)

    def test_middleware_config(self):
        """Test middleware stack is properly configured"""
        required_middleware = [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'app.middleware.TenantMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        ]

        for middleware in required_middleware:
            self.assertIn(middleware, settings.MIDDLEWARE)

        # TenantMiddleware should be positioned correctly (after session, before common)
        tenant_pos = settings.MIDDLEWARE.index('app.middleware.TenantMiddleware')
        session_pos = settings.MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware')
        common_pos = settings.MIDDLEWARE.index('django.middleware.common.CommonMiddleware')

        self.assertGreater(tenant_pos, session_pos)
        self.assertLess(tenant_pos, common_pos)

    def test_tenant_configuration(self):
        """Test multi-tenant specific settings"""
        # Tenant schema prefix should be configured
        self.assertTrue(hasattr(settings, 'TENANT_SCHEMA_PREFIX'))
        self.assertIsInstance(settings.TENANT_SCHEMA_PREFIX, str)
        self.assertEqual(settings.TENANT_SCHEMA_PREFIX, 'tenant_')

    def test_graphql_config(self):
        """Test GraphQL configuration"""
        self.assertTrue(hasattr(settings, 'GRAPHENE'))
        self.assertEqual(settings.GRAPHENE['SCHEMA'], 'app.schema.schema')

    def test_aws_config_defaults(self):
        """Test AWS S3 configuration defaults"""
        self.assertEqual(settings.AWS_STORAGE_BUCKET_NAME, 'your-bucket-name')
        self.assertEqual(settings.AWS_S3_REGION_NAME, 'us-east-1')

        # AWS settings should exist
        aws_settings = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_STORAGE_BUCKET_NAME',
            'AWS_S3_REGION_NAME',
        ]

        for setting in aws_settings:
            self.assertTrue(hasattr(settings, setting))

    def test_static_files_config(self):
        """Test static files configuration"""
        self.assertIsNotNone(settings.STATIC_URL)
        self.assertTrue(settings.STATIC_URL.startswith('/'))
        self.assertIsNotNone(settings.STATIC_ROOT)
        self.assertIsInstance(settings.STATICFILES_DIRS, list)

    def test_media_files_configuration(self):
        """Test media files settings"""
        self.assertIsNotNone(settings.MEDIA_URL)
        self.assertTrue(settings.MEDIA_URL.startswith('/'))
        self.assertIsNotNone(settings.MEDIA_ROOT)

    def test_template_configuration(self):
        """Test template engine configuration"""
        templates = settings.TEMPLATES
        self.assertIsInstance(templates, list)
        self.assertGreater(len(templates), 0)

        # First template should be Django template backend
        django_template = templates[0]
        self.assertEqual(django_template['BACKEND'], 'django.template.backends.django.DjangoTemplates')

    def test_wsgi_application_setting(self):
        """Test WSGI application is properly configured"""
        self.assertEqual(settings.WSGI_APPLICATION, 'app.wsgi.application')

    def test_root_urlconf_setting(self):
        """Test ROOT_URLCONF is properly configured"""
        self.assertEqual(settings.ROOT_URLCONF, 'app.urls')

    @override_settings(TENANT_SCHEMA_PREFIX='custom_')
    def test_tenant_prefix_override(self):
        """Test tenant prefix can be overridden"""
        self.assertEqual(settings.TENANT_SCHEMA_PREFIX, 'custom_')


if __name__ == '__main__':
    unittest.main()
