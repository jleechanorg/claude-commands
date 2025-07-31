#!/usr/bin/env python3
"""
Health Check Service for MCP Architecture

Provides health checking functionality for all services in the MCP architecture.
Used by Docker Compose health checks and monitoring systems.
"""

import argparse
import json
import logging
import sys
import time
from typing import Any
from urllib.parse import urljoin

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for various MCP services."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def check_http_service(self, url: str, path: str = "/health") -> dict[str, Any]:
        """Check health of an HTTP service."""
        full_url = urljoin(url, path)

        try:
            response = requests.get(full_url, timeout=self.timeout)

            result = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'status_code': response.status_code,
                'response_time_ms': 0,  # Would measure in real implementation
                'url': full_url
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result['details'] = data
                except json.JSONDecodeError:
                    result['details'] = {'text': response.text}
            else:
                result['error'] = f"HTTP {response.status_code}"

            return result

        except requests.RequestException as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'url': full_url
            }

    def check_mcp_server(self, url: str) -> dict[str, Any]:
        """Check health of MCP server with additional MCP-specific checks."""
        # Basic HTTP health check
        basic_health = self.check_http_service(url, "/health")

        if basic_health['status'] != 'healthy':
            return basic_health

        # Additional MCP-specific checks
        try:
            # Test MCP protocol endpoint
            mcp_payload = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 1
            }

            response = requests.post(
                urljoin(url, "/mcp"),
                json=mcp_payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    basic_health['mcp_tools_count'] = len(data["result"]["tools"])
                    basic_health['mcp_protocol'] = 'working'
                else:
                    basic_health['mcp_protocol'] = 'invalid_response'
            else:
                basic_health['mcp_protocol'] = f'http_error_{response.status_code}'

        except Exception as e:
            basic_health['mcp_protocol'] = f'error_{str(e)}'

        return basic_health

    def check_translation_layer(self, url: str) -> dict[str, Any]:
        """Check health of translation layer with API endpoint tests."""
        # Basic HTTP health check
        basic_health = self.check_http_service(url, "/api/health")

        if basic_health['status'] != 'healthy':
            return basic_health

        # Test API endpoints are accessible
        test_endpoints = [
            "/api/campaigns",  # Should return 401 without auth
            "/static/css/styles.css",  # Should return 404 if file doesn't exist
        ]

        endpoint_status = {}
        for endpoint in test_endpoints:
            try:
                response = requests.get(
                    urljoin(url, endpoint),
                    timeout=self.timeout
                )
                endpoint_status[endpoint] = {
                    'status_code': response.status_code,
                    'accessible': True
                }
            except Exception as e:
                endpoint_status[endpoint] = {
                    'accessible': False,
                    'error': str(e)
                }

        basic_health['endpoints'] = endpoint_status
        return basic_health

    def check_firestore_emulator(self, host: str, port: int = 8080) -> dict[str, Any]:
        """Check Firestore emulator health."""
        url = f"http://{host}:{port}"

        try:
            # Firestore emulator doesn't have a standard health endpoint,
            # so we test basic connectivity
            response = requests.get(url, timeout=self.timeout)

            return {
                'status': 'healthy' if response.status_code in [200, 404] else 'unhealthy',
                'status_code': response.status_code,
                'service': 'firestore_emulator',
                'url': url
            }

        except requests.RequestException as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'service': 'firestore_emulator',
                'url': url
            }

    def check_redis(self, host: str, port: int = 6379) -> dict[str, Any]:
        """Check Redis health."""
        try:
            import redis

            client = redis.Redis(host=host, port=port, socket_timeout=self.timeout)
            response = client.ping()

            return {
                'status': 'healthy' if response else 'unhealthy',
                'service': 'redis',
                'ping_response': response
            }

        except ImportError:
            return {
                'status': 'unknown',
                'error': 'Redis client not available',
                'service': 'redis'
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'service': 'redis'
            }

    def comprehensive_health_check(self, services: dict[str, str]) -> dict[str, Any]:
        """Perform comprehensive health check of all services."""
        results = {}
        overall_status = 'healthy'

        for service_name, service_url in services.items():
            if service_name == 'mcp-server':
                result = self.check_mcp_server(service_url)
            elif service_name == 'translation-layer':
                result = self.check_translation_layer(service_url)
            else:
                result = self.check_http_service(service_url)

            results[service_name] = result

            if result['status'] != 'healthy':
                overall_status = 'unhealthy'

        return {
            'overall_status': overall_status,
            'services': results,
            'timestamp': time.time(),
            'checker_version': '1.0.0'
        }


def main():
    """Main health check CLI."""
    parser = argparse.ArgumentParser(description='Health check for MCP services')
    parser.add_argument('--service', required=True,
                       choices=['mcp-server', 'translation-layer', 'mock-server', 'all'],
                       help='Service to check')
    parser.add_argument('--port', type=int, default=8000, help='Service port')
    parser.add_argument('--host', default='localhost', help='Service host')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout')
    parser.add_argument('--format', choices=['json', 'text'], default='text',
                       help='Output format')

    args = parser.parse_args()

    checker = HealthChecker(timeout=args.timeout)

    if args.service == 'all':
        # Comprehensive check of all services
        services = {
            'mcp-server': f"http://{args.host}:8000",
            'translation-layer': f"http://{args.host}:8081",
            'mock-server': f"http://{args.host}:8001"
        }

        result = checker.comprehensive_health_check(services)

    else:
        # Single service check
        url = f"http://{args.host}:{args.port}"

        if args.service == 'mcp-server':
            result = checker.check_mcp_server(url)
        elif args.service == 'translation-layer':
            result = checker.check_translation_layer(url)
        elif args.service == 'mock-server':
            result = checker.check_http_service(url)
        else:
            result = {'status': 'unknown', 'error': f'Unknown service: {args.service}'}

    # Output result
    if args.format == 'json':
        print(json.dumps(result, indent=2))
    # Text format
    elif 'overall_status' in result:
        print(f"Overall Status: {result['overall_status'].upper()}")
        for service_name, service_result in result['services'].items():
            status = service_result['status'].upper()
            print(f"  {service_name}: {status}")
            if 'error' in service_result:
                print(f"    Error: {service_result['error']}")
    else:
        status = result['status'].upper()
        print(f"Service Status: {status}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        if 'mcp_tools_count' in result:
            print(f"MCP Tools Available: {result['mcp_tools_count']}")

    # Exit with appropriate code
    if 'overall_status' in result:
        exit_code = 0 if result['overall_status'] == 'healthy' else 1
    else:
        exit_code = 0 if result['status'] == 'healthy' else 1

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
