#!/usr/bin/env python3
"""
Claude Code Custom Metrics Hook
Detects configurable events in Claude responses and sends metrics to GCP Cloud Monitoring
"""

import asyncio
import json
import os
import re
import sys
import time
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

try:
    from google.cloud import monitoring_v3
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False


class CustomMetricsHook:
    """Custom metrics monitoring hook for Claude Code CLI"""

    def __init__(self, config_path: Optional[str] = None):
        self.start_time = time.time()

        # Find project root and config
        self.project_root = self._find_project_root()
        self.config_path = config_path or os.path.join(self.project_root, 'config', 'custom_metrics_config.yaml')

        # Load configuration
        self.config = self._load_config()
        if not self.config:
            return

        # Initialize GCP client if available
        self.monitoring_client = None
        if GCP_AVAILABLE and self.config.get('features', {}).get('enable_gcp_metrics', False):
            self._init_gcp_client()

    def _find_project_root(self) -> str:
        """Find the project root by looking for CLAUDE.md"""
        current = Path.cwd()
        for parent in [current] + list(current.parents):
            if (parent / 'CLAUDE.md').exists():
                return str(parent)
        return str(Path.cwd())

    def _load_config(self) -> Optional[Dict]:
        """Load configuration from YAML file"""
        try:
            if not os.path.exists(self.config_path):
                return None

            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception:
            return None

    def _init_gcp_client(self):
        """Initialize GCP monitoring client"""
        try:
            gcp_config = self.config.get('gcp', {})
            credentials_file = os.path.expanduser(gcp_config.get('credentials_file', ''))

            if os.path.exists(credentials_file):
                credentials = service_account.Credentials.from_service_account_file(credentials_file)
                self.monitoring_client = monitoring_v3.MetricServiceClient(credentials=credentials)
        except Exception:
            self.monitoring_client = None

    def detect_patterns(self, content: str) -> List[Tuple[str, str, int, str]]:
        """Detect configured patterns in content"""
        detections = []

        if not self.config:
            return detections

        event_types = self.config.get('event_types', {})

        for event_type, event_config in event_types.items():
            if not event_config.get('enabled', False):
                continue

            patterns = event_config.get('patterns', [])
            for pattern_config in patterns:
                pattern = pattern_config.get('pattern', '')
                weight = pattern_config.get('weight', 0)
                name = pattern_config.get('name', '')

                try:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    if matches:
                        detections.append((event_type, name, weight, pattern))
                except re.error:
                    continue

        return detections

    def send_metric_to_gcp(self, event_type: str, pattern_name: str, weight: float, actions_triggered: bool):
        """Send metric to GCP Cloud Monitoring"""
        if not self.monitoring_client:
            return False

        try:
            gcp_config = self.config.get('gcp', {})
            project_id = gcp_config.get('project_id')
            if not project_id:
                return False

            # Get git branch for labeling
            try:
                import subprocess
                branch = subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=self.project_root,
                    stderr=subprocess.DEVNULL
                ).decode().strip()
            except:
                branch = 'unknown'

            # Create metric data
            series = monitoring_v3.TimeSeries()
            series.metric.type = gcp_config.get('metric_type', 'custom.googleapis.com/claude_custom_metrics')
            series.metric.labels['event_type'] = event_type
            series.metric.labels['pattern'] = pattern_name
            series.metric.labels['actions_triggered'] = str(actions_triggered).lower()
            series.metric.labels['branch'] = branch
            series.metric.labels['project'] = 'worldarchitect'

            series.resource.type = gcp_config.get('resource_type', 'global')

            # Add data point
            now = time.time()
            interval = monitoring_v3.TimeInterval({
                'end_time': {'seconds': int(now)}
            })
            point = monitoring_v3.Point({
                'interval': interval,
                'value': {'double_value': float(weight)}
            })
            series.points = [point]

            # Send to GCP
            project_name = f"projects/{project_id}"
            self.monitoring_client.create_time_series(
                name=project_name,
                time_series=[series],
                timeout=gcp_config.get('api_timeout', 5.0)
            )

            return True

        except Exception:
            return False

    def trigger_actions(self, event_type: str) -> bool:
        """Trigger configured actions for event type"""
        if not self.config:
            return False

        try:
            event_config = self.config.get('event_types', {}).get(event_type, {})
            actions = event_config.get('actions', [])

            for action in actions:
                if action.get('type') == 'trigger_command':
                    command = action.get('command', [])
                    if command:
                        # Trigger command asynchronously
                        import subprocess
                        subprocess.Popen(
                            command,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            cwd=self.project_root
                        )

            return len(actions) > 0

        except Exception:
            return False

    def process_content(self, content: str):
        """Main processing function"""
        if not self.config:
            return

        # Check if metrics are enabled
        if not self.config.get('features', {}).get('enable_event_detection', True):
            return

        # Detect patterns
        detections = self.detect_patterns(content)

        if not detections:
            return

        # Process each detection
        for event_type, pattern_name, weight, pattern in detections:
            # Trigger actions
            actions_triggered = False
            if self.config.get('features', {}).get('enable_actions', True):
                actions_triggered = self.trigger_actions(event_type)

            # Send metrics
            if self.config.get('features', {}).get('enable_gcp_metrics', True):
                self.send_metric_to_gcp(event_type, pattern_name, weight, actions_triggered)

        # Performance check
        elapsed = time.time() - self.start_time
        timeout = self.config.get('performance', {}).get('total_hook_timeout', 200) / 1000.0

        if elapsed > timeout:
            return  # Timeout to prevent blocking


def main():
    """Main entry point for hook"""
    if len(sys.argv) < 2:
        return

    content = ' '.join(sys.argv[1:])

    try:
        hook = CustomMetricsHook()
        hook.process_content(content)
    except Exception:
        pass  # Fail silently to not disrupt Claude Code


if __name__ == '__main__':
    main()
