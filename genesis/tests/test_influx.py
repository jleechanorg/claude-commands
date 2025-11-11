import os
import unittest
from unittest.mock import MagicMock, patch

from influx import get_query_api, get_tenant_bucket, get_write_api


class TestInfluxDBClient(unittest.TestCase):
    def setUp(self):
        self.tenant_id = "test-tenant-123"
        self.org_id = "test-org-456"
        self.token = "test-token-789"
        self.url = "http://localhost:8086"

        # Set environment variables for testing
        os.environ["INFLUXDB_URL"] = self.url
        os.environ["INFLUXDB_TOKEN"] = self.token
        os.environ["INFLUXDB_ORG"] = self.org_id

    def tearDown(self):
        # Clean up environment variables
        if "INFLUXDB_URL" in os.environ:
            del os.environ["INFLUXDB_URL"]
        if "INFLUXDB_TOKEN" in os.environ:
            del os.environ["INFLUXDB_TOKEN"]
        if "INFLUXDB_ORG" in os.environ:
            del os.environ["INFLUXDB_ORG"]

    @patch('influx.InfluxDBClient')
    def test_client_initialization_success(self, mock_client):
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance

        client = get_influx_client()

        mock_client.assert_called_once_with(url=self.url, token=self.token, org=self.org_id)
        self.assertEqual(client, mock_instance)

    @patch('influx.InfluxDBClient')
    def test_client_initialization_failure(self, mock_client):
        mock_client.side_effect = Exception("Connection failed")

        with self.assertRaises(Exception) as context:
            get_influx_client()

        self.assertTrue("Failed to initialize InfluxDB client: Connection failed" in str(context.exception))

    @patch('influx.get_influx_client')
    def test_get_tenant_bucket_success(self, mock_get_client):
        mock_instance = MagicMock()
        mock_buckets_api = MagicMock()
        mock_get_client.return_value = mock_instance
        mock_instance.buckets_api.return_value = mock_buckets_api

        mock_bucket = MagicMock()
        mock_bucket.name = f"tenant-{self.tenant_id}"
        mock_buckets_api.find_bucket_by_name.return_value = mock_bucket

        bucket = get_tenant_bucket(self.tenant_id)

        mock_instance.buckets_api.assert_called_once()
        mock_buckets_api.find_bucket_by_name.assert_called_once_with(f"tenant-{self.tenant_id}")
        self.assertEqual(bucket, mock_bucket)

    @patch('influx.get_influx_client')
    def test_get_tenant_bucket_not_found_creates_new(self, mock_get_client):
        mock_instance = MagicMock()
        mock_buckets_api = MagicMock()
        mock_get_client.return_value = mock_instance
        mock_instance.buckets_api.return_value = mock_buckets_api

        mock_buckets_api.find_bucket_by_name.return_value = None
        mock_new_bucket = MagicMock()
        mock_new_bucket.name = f"tenant-{self.tenant_id}"
        mock_buckets_api.create_bucket.return_value = mock_new_bucket

        bucket = get_tenant_bucket(self.tenant_id)

        mock_buckets_api.create_bucket.assert_called_once()
        self.assertEqual(bucket.name, f"tenant-{self.tenant_id}")

    @patch('influx.get_influx_client')
    def test_get_tenant_bucket_creation_failure(self, mock_get_client):
        mock_instance = MagicMock()
        mock_buckets_api = MagicMock()
        mock_get_client.return_value = mock_instance
        mock_instance.buckets_api.return_value = mock_buckets_api

        mock_buckets_api.find_bucket_by_name.return_value = None
        mock_buckets_api.create_bucket.side_effect = Exception("Bucket creation failed")

        with self.assertRaises(Exception) as context:
            get_tenant_bucket(self.tenant_id)

        self.assertTrue("Failed to get or create bucket for tenant" in str(context.exception))

    @patch('influx.get_influx_client')
    def test_write_api_success(self, mock_get_client):
        mock_instance = MagicMock()
        mock_write_api = MagicMock()
        mock_get_client.return_value = mock_instance
        mock_instance.write_api.return_value = mock_write_api

        write_api = get_write_api()

        mock_instance.write_api.assert_called_once()
        self.assertEqual(write_api, mock_write_api)

    @patch('influx.get_influx_client')
    def test_query_api_success(self, mock_get_client):
        mock_instance = MagicMock()
        mock_query_api = MagicMock()
        mock_get_client.return_value = mock_instance
        mock_instance.query_api.return_value = mock_query_api

        query_api = get_query_api()

        mock_instance.query_api.assert_called_once()
        self.assertEqual(query_api, mock_query_api)

if __name__ == '__main__':
    unittest.main()
