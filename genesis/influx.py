import os
from influxdb_client import InfluxDBClient, BucketRetentionRules
from influxdb_client.client.write_api import WriteApi
from influxdb_client.client.query_api import QueryApi

def get_influx_client() -> InfluxDBClient:
    """
    Initialize and return an InfluxDB client instance.

    Returns:
        InfluxDBClient: Configured client instance

    Raises:
        Exception: If client initialization fails
    """
    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")

    if not url or not token or not org:
        raise Exception("Missing required InfluxDB environment variables")

    try:
        client = InfluxDBClient(url=url, token=token, org=org)
        return client
    except Exception as e:
        raise Exception(f"Failed to initialize InfluxDB client: {str(e)}")

def get_tenant_bucket(tenant_id: str):
    """
    Get or create a tenant-specific bucket.

    Args:
        tenant_id (str): Unique identifier for the tenant

    Returns:
        Bucket: Tenant-specific bucket object

    Raises:
        Exception: If bucket operations fail
    """
    client = get_influx_client()
    buckets_api = client.buckets_api()

    bucket_name = f"tenant-{tenant_id}"

    try:
        # Try to find existing bucket
        bucket = buckets_api.find_bucket_by_name(bucket_name)

        if bucket is None:
            # Create new bucket with 30-day retention
            retention_rules = BucketRetentionRules(type="expire", every_seconds=2592000)
            bucket = buckets_api.create_bucket(
                bucket_name=bucket_name,
                org_id=os.getenv("INFLUXDB_ORG"),
                retention_rules=retention_rules
            )

        return bucket
    except Exception as e:
        raise Exception(f"Failed to get or create bucket for tenant {tenant_id}: {str(e)}")
    finally:
        client.close()

def get_write_api() -> WriteApi:
    """
    Get a write API instance for InfluxDB.

    Returns:
        WriteApi: Write API instance
    """
    client = get_influx_client()
    return client.write_api()

def get_query_api() -> QueryApi:
    """
    Get a query API instance for InfluxDB.

    Returns:
        QueryApi: Query API instance
    """
    client = get_influx_client()
    return client.query_api()
