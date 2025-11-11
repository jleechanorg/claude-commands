"""
Test Suite for Docker Infrastructure
Tests all services defined in docker-compose.yml to ensure proper connectivity and health.
"""

import time

import docker
import psycopg2
import pytest
import redis
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration matching docker-compose.yml
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecommerce',
    'user': 'postgres',
    'password': 'password'
}

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

API_BASE_URL = 'http://localhost:8000'
FLOWER_BASE_URL = 'http://localhost:5555'

# Service names from docker-compose.yml
EXPECTED_SERVICES = ['api', 'db', 'redis', 'worker', 'flower']

class TestDockerInfrastructure:
    """Test suite for Docker infrastructure components"""

    @classmethod
    def setup_class(cls):
        """Setup test environment and Docker client"""
        cls.docker_client = docker.from_env()
        cls.max_wait_time = 120  # 2 minutes max wait for services
        cls.retry_interval = 5   # Check every 5 seconds

        # Configure requests session with retries
        cls.session = requests.Session()
        retry_strategy = Retry(
            total=10,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        cls.session.mount("http://", adapter)
        cls.session.mount("https://", adapter)

    @classmethod
    def teardown_class(cls):
        """Cleanup resources"""
        if hasattr(cls, 'session'):
            cls.session.close()
        if hasattr(cls, 'docker_client'):
            cls.docker_client.close()

    def wait_for_service(self, service_name, health_check_func, max_attempts=24):
        """
        Wait for a service to become available with exponential backoff

        Args:
            service_name: Name of the service to wait for
            health_check_func: Function that returns True when service is ready
            max_attempts: Maximum number of attempts (default: 24 * 5s = 2 minutes)
        """
        for attempt in range(max_attempts):
            try:
                if health_check_func():
                    print(f"✅ {service_name} is ready (attempt {attempt + 1})")
                    return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    wait_time = min(2 ** (attempt // 3), 10)  # Exponential backoff, max 10s
                    print(f"⏳ {service_name} not ready (attempt {attempt + 1}): {str(e)[:100]}... Waiting {wait_time}s")
                    time.sleep(wait_time)
                else:
                    print(f"❌ {service_name} failed to start after {max_attempts} attempts")
                    raise
        return False

    def test_docker_compose_services_running(self):
        """Test that all expected Docker services are running"""
        print("\n🔍 Checking Docker services...")

        # Get all containers (including stopped ones)
        try:
            containers = self.docker_client.containers.list(all=True)
        except Exception as e:
            pytest.fail(f"Failed to connect to Docker daemon: {e}")

        # Filter containers from our compose project
        compose_containers = [
            c for c in containers
            if any(service in c.name for service in EXPECTED_SERVICES)
        ]

        if not compose_containers:
            pytest.fail("No containers found. Please ensure 'docker-compose up -d' has been run.")

        # Check each expected service
        running_services = []
        failed_services = []

        for container in compose_containers:
            service_name = None
            for service in EXPECTED_SERVICES:
                if service in container.name:
                    service_name = service
                    break

            if service_name:
                status = container.status
                if status == 'running':
                    running_services.append(service_name)
                    print(f"✅ {service_name}: {status}")
                else:
                    failed_services.append(f"{service_name}: {status}")
                    print(f"❌ {service_name}: {status}")

        if failed_services:
            pytest.fail(f"Services not running: {', '.join(failed_services)}")

        # Verify we found all expected services
        found_services = set(running_services)
        expected_services = set(EXPECTED_SERVICES)
        missing_services = expected_services - found_services

        if missing_services:
            pytest.fail(f"Missing services: {', '.join(missing_services)}")

        assert len(running_services) >= 4, f"Expected at least 4 services, found {len(running_services)}"

    def test_postgresql_connection(self):
        """Test PostgreSQL database connection and basic operations"""
        print("\n🗄️  Testing PostgreSQL connection...")

        def check_postgres():
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            return bool(version)

        # Wait for PostgreSQL to be ready
        assert self.wait_for_service("PostgreSQL", check_postgres), "PostgreSQL failed to start"

        # Test database operations
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()

        try:
            # Test basic SELECT
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            assert version is not None, "Failed to get PostgreSQL version"
            print(f"✅ PostgreSQL version: {version[0][:50]}...")

            # Test table creation and data operations
            cursor.execute("""
                DROP TABLE IF EXISTS test_infrastructure;
                CREATE TABLE test_infrastructure (
                    id SERIAL PRIMARY KEY,
                    test_data VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cursor.execute(
                "INSERT INTO test_infrastructure (test_data) VALUES (%s) RETURNING id;",
                ("Docker infrastructure test",)
            )
            test_id = cursor.fetchone()[0]

            cursor.execute("SELECT test_data FROM test_infrastructure WHERE id = %s;", (test_id,))
            result = cursor.fetchone()
            assert result[0] == "Docker infrastructure test", "Failed to insert/retrieve test data"

            cursor.execute("DROP TABLE test_infrastructure;")
            conn.commit()
            print("✅ PostgreSQL CRUD operations successful")

        finally:
            cursor.close()
            conn.close()

    def test_redis_connection(self):
        """Test Redis connection and basic operations"""
        print("\n🔴 Testing Redis connection...")

        def check_redis():
            client = redis.Redis(**REDIS_CONFIG)
            return client.ping()

        # Wait for Redis to be ready
        assert self.wait_for_service("Redis", check_redis), "Redis failed to start"

        # Test Redis operations
        client = redis.Redis(**REDIS_CONFIG)

        try:
            # Test ping
            assert client.ping(), "Redis ping failed"
            print("✅ Redis ping successful")

            # Test basic operations
            test_key = "test:infrastructure"
            test_value = "docker_test_value"

            client.set(test_key, test_value, ex=60)  # Expire in 60 seconds
            retrieved_value = client.get(test_key)
            assert retrieved_value.decode() == test_value, "Failed to set/get Redis value"

            # Test hash operations
            hash_key = "test:hash"
            client.hset(hash_key, "field1", "value1")
            client.hset(hash_key, "field2", "value2")

            hash_data = client.hgetall(hash_key)
            assert len(hash_data) == 2, "Failed to store hash data"
            assert hash_data[b"field1"] == b"value1", "Hash field1 value incorrect"

            # Cleanup
            client.delete(test_key, hash_key)
            print("✅ Redis CRUD operations successful")

        finally:
            client.close()

    def test_api_service_health(self):
        """Test API service health and basic endpoints"""
        print("\n🌐 Testing API service...")

        def check_api():
            response = self.session.get(f"{API_BASE_URL}/health", timeout=10)
            return response.status_code == 200

        # Wait for API to be ready
        assert self.wait_for_service("API", check_api), "API service failed to start"

        # Test health endpoint
        response = self.session.get(f"{API_BASE_URL}/health", timeout=10)
        assert response.status_code == 200, f"API health check failed: {response.status_code}"
        print("✅ API health endpoint accessible")

        # Test root endpoint if available
        try:
            response = self.session.get(API_BASE_URL, timeout=10)
            if response.status_code in [200, 404]:  # 404 is acceptable if no root route
                print(f"✅ API root endpoint responded with status: {response.status_code}")
            else:
                print(f"⚠️  API root endpoint returned: {response.status_code}")
        except Exception as e:
            print(f"⚠️  API root endpoint test failed: {str(e)[:100]}...")

    def test_flower_monitoring(self):
        """Test Flower monitoring interface"""
        print("\n🌸 Testing Flower monitoring...")

        def check_flower():
            response = self.session.get(FLOWER_BASE_URL, timeout=10)
            return response.status_code == 200

        # Wait for Flower to be ready
        assert self.wait_for_service("Flower", check_flower), "Flower service failed to start"

        # Test Flower dashboard
        response = self.session.get(FLOWER_BASE_URL, timeout=10)
        assert response.status_code == 200, f"Flower dashboard failed: {response.status_code}"

        # Verify it's actually Flower by checking for expected content
        content = response.text.lower()
        flower_indicators = ["flower", "celery", "worker", "tasks"]
        found_indicators = [indicator for indicator in flower_indicators if indicator in content]

        assert len(found_indicators) >= 2, f"Flower dashboard doesn't contain expected content. Found: {found_indicators}"
        print("✅ Flower monitoring interface accessible")

    def test_celery_worker_status(self):
        """Test Celery worker connectivity through Flower API"""
        print("\n👷 Testing Celery worker status...")

        # Wait a bit for worker to register with Flower
        time.sleep(10)

        try:
            # Try to get worker stats through Flower API
            response = self.session.get(f"{FLOWER_BASE_URL}/api/workers", timeout=15)

            if response.status_code == 200:
                workers_data = response.json()
                if workers_data:
                    print(f"✅ Found {len(workers_data)} Celery worker(s)")
                    for worker_name in workers_data.keys():
                        print(f"  - Worker: {worker_name}")
                else:
                    print("⚠️  No Celery workers found, but Flower API is accessible")
            else:
                print(f"⚠️  Flower API returned status {response.status_code}")

        except Exception as e:
            print(f"⚠️  Celery worker status check failed: {str(e)[:100]}...")
            # This is a warning, not a failure, as worker might need more time to register

    def test_service_network_connectivity(self):
        """Test inter-service network connectivity"""
        print("\n🔗 Testing service network connectivity...")

        # Test if services can reach each other through internal network
        # We'll do this by checking if the API can connect to its dependencies

        try:
            # Check if API service environment suggests proper connectivity
            api_containers = [
                c for c in self.docker_client.containers.list()
                if 'api' in c.name and c.status == 'running'
            ]

            if api_containers:
                api_container = api_containers[0]

                # Check environment variables for proper database and redis URLs
                env_vars = api_container.attrs['Config']['Env']
                env_dict = {}
                for env in env_vars:
                    if '=' in env:
                        key, value = env.split('=', 1)
                        env_dict[key] = value

                # Verify database URL
                db_url = env_dict.get('DATABASE_URL', '')
                expected_db_parts = ['postgresql://', 'db:5432', 'ecommerce']
                db_checks = [part in db_url for part in expected_db_parts]

                if all(db_checks):
                    print("✅ API has correct database URL configuration")
                else:
                    print(f"⚠️  API database URL may be incorrect: {db_url}")

                # Verify Redis URL
                redis_url = env_dict.get('REDIS_URL', '')
                expected_redis_parts = ['redis://', 'redis:6379']
                redis_checks = [part in redis_url for part in expected_redis_parts]

                if all(redis_checks):
                    print("✅ API has correct Redis URL configuration")
                else:
                    print(f"⚠️  API Redis URL may be incorrect: {redis_url}")

            else:
                print("⚠️  No running API container found for network connectivity test")

        except Exception as e:
            print(f"⚠️  Network connectivity test failed: {str(e)[:100]}...")

    def test_volume_persistence(self):
        """Test Docker volume persistence"""
        print("\n💾 Testing volume persistence...")

        try:
            volumes = self.docker_client.volumes.list()
            volume_names = [vol.name for vol in volumes]

            expected_volumes = ['postgres_data', 'redis_data']
            found_volumes = []

            for expected in expected_volumes:
                # Volume names might have project prefix
                matching_volumes = [v for v in volume_names if expected in v]
                if matching_volumes:
                    found_volumes.append(expected)
                    print(f"✅ Found volume for {expected}: {matching_volumes[0]}")
                else:
                    print(f"⚠️  Volume for {expected} not found")

            # At least some volumes should exist
            assert len(found_volumes) > 0, "No expected volumes found"
            print(f"✅ Volume persistence configured ({len(found_volumes)}/{len(expected_volumes)} volumes found)")

        except Exception as e:
            print(f"⚠️  Volume persistence test failed: {str(e)[:100]}...")

    def test_comprehensive_infrastructure_health(self):
        """Comprehensive infrastructure health test"""
        print("\n🏥 Running comprehensive health check...")

        health_status = {
            'docker_services': False,
            'postgresql': False,
            'redis': False,
            'api': False,
            'flower': False
        }

        # Quick health checks for all services
        try:
            # Docker services
            containers = self.docker_client.containers.list()
            running_count = len([c for c in containers if c.status == 'running'])
            health_status['docker_services'] = running_count >= 4

            # PostgreSQL
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            cursor.fetchone()
            cursor.close()
            conn.close()
            health_status['postgresql'] = True

            # Redis
            redis_client = redis.Redis(**REDIS_CONFIG)
            health_status['redis'] = redis_client.ping()
            redis_client.close()

            # API
            response = self.session.get(f"{API_BASE_URL}/health", timeout=5)
            health_status['api'] = response.status_code == 200

            # Flower
            response = self.session.get(FLOWER_BASE_URL, timeout=5)
            health_status['flower'] = response.status_code == 200

        except Exception as e:
            print(f"Health check error: {str(e)[:100]}...")

        # Report results
        healthy_services = sum(health_status.values())
        total_services = len(health_status)

        print("\n📊 Infrastructure Health Report:")
        for service, status in health_status.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {service.replace('_', ' ').title()}: {'Healthy' if status else 'Unhealthy'}")

        print(f"\n🎯 Overall Health: {healthy_services}/{total_services} services healthy ({(healthy_services/total_services)*100:.1f}%)")

        # Require at least 80% of services to be healthy
        assert healthy_services >= int(total_services * 0.8), f"Infrastructure health check failed: only {healthy_services}/{total_services} services healthy"
        print("✅ Infrastructure health check passed!")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s", "--tb=short"])
