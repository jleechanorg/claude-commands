"""
Analysis tools for captured data and mock validation.
Compares captured real service interactions with mock responses.
"""

import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Any

import time


class CaptureAnalyzer:
    """Analyzes captured service interactions and compares with mock data."""

    def __init__(self, capture_dir: str):
        self.capture_dir = capture_dir

    def analyze_captures(self, days_back: int = 7) -> dict:
        """Analyze all captures from the last N days."""
        capture_files = self._get_recent_capture_files(days_back)
        if not capture_files:
            return {"error": "No capture files found"}

        all_interactions = []
        for filepath in capture_files:
            try:
                with open(filepath) as f:
                    data = json.load(f)
                    all_interactions.extend(data.get("interactions", []))
            except Exception as e:
                print(f"Warning: Failed to load {filepath}: {e}")

        return self._analyze_interactions(all_interactions)

    def _get_recent_capture_files(self, days_back: int) -> list[str]:
        """Get capture files from the last N days."""
        if not os.path.exists(self.capture_dir):
            return []



        cutoff_time = time.time() - (days_back * 24 * 3600)
        recent_files = []

        for filename in os.listdir(self.capture_dir):
            if filename.startswith("capture_") and filename.endswith(".json"):
                filepath = os.path.join(self.capture_dir, filename)
                if os.path.getmtime(filepath) >= cutoff_time:
                    recent_files.append(filepath)

        return sorted(recent_files)

    def _analyze_interactions(self, interactions: list[dict]) -> dict:
        """Analyze a list of interactions."""
        if not interactions:
            return {"total_interactions": 0}

        analysis = {
            "total_interactions": len(interactions),
            "by_service": defaultdict(
                lambda: {
                    "count": 0,
                    "operations": defaultdict(int),
                    "avg_duration": 0,
                    "errors": 0,
                }
            ),
            "performance": {
                "total_duration": 0,
                "avg_duration": 0,
                "slowest_operations": [],
                "fastest_operations": [],
            },
            "errors": [],
            "patterns": {},
        }

        total_duration = 0
        operation_times = []

        for interaction in interactions:
            service = interaction.get("service", "unknown")
            operation = interaction.get("operation", "unknown")
            duration = interaction.get("duration_ms", 0)

            # Service analysis
            analysis["by_service"][service]["count"] += 1
            analysis["by_service"][service]["operations"][operation] += 1

            # Performance analysis
            total_duration += duration
            operation_times.append(
                {
                    "service": service,
                    "operation": operation,
                    "duration": duration,
                    "timestamp": interaction.get("timestamp"),
                }
            )

            # Error analysis
            if interaction.get("status") == "error":
                analysis["by_service"][service]["errors"] += 1
                analysis["errors"].append(
                    {
                        "service": service,
                        "operation": operation,
                        "error": interaction.get("error"),
                        "timestamp": interaction.get("timestamp"),
                    }
                )

        # Calculate averages
        analysis["performance"]["total_duration"] = total_duration
        analysis["performance"]["avg_duration"] = total_duration / len(interactions)

        # Sort operations by duration
        operation_times.sort(key=lambda x: x["duration"])
        analysis["performance"]["fastest_operations"] = operation_times[:5]
        analysis["performance"]["slowest_operations"] = operation_times[-5:]

        # Calculate service averages
        for service_data in analysis["by_service"].values():
            if service_data["count"] > 0:
                service_duration = sum(
                    op["duration"] for op in operation_times if op["service"] == service
                )
                service_data["avg_duration"] = service_duration / service_data["count"]

        return dict(analysis)

    def compare_with_mock(self, capture_file: str, mock_responses: dict) -> dict:
        """Compare captured real responses with mock responses."""
        try:
            with open(capture_file) as f:
                capture_data = json.load(f)
        except Exception as e:
            return {"error": f"Failed to load capture file: {e}"}

        interactions = capture_data.get("interactions", [])
        comparison_results = {
            "total_comparisons": 0,
            "matches": 0,
            "differences": [],
            "missing_mocks": [],
            "accuracy_score": 0.0,
        }

        for interaction in interactions:
            if interaction.get("status") != "success":
                continue

            service = interaction.get("service")
            operation = interaction.get("operation")
            real_response = interaction.get("response")

            if not real_response:
                continue

            # Find corresponding mock response
            mock_key = f"{service}.{operation}"
            mock_response = mock_responses.get(mock_key)

            comparison_results["total_comparisons"] += 1

            if not mock_response:
                comparison_results["missing_mocks"].append(
                    {
                        "service": service,
                        "operation": operation,
                        "real_response_sample": self._truncate_data(real_response),
                    }
                )
                continue

            # Compare responses
            diff_result = self._compare_responses(real_response, mock_response)
            if diff_result["is_match"]:
                comparison_results["matches"] += 1
            else:
                comparison_results["differences"].append(
                    {
                        "service": service,
                        "operation": operation,
                        "differences": diff_result["differences"],
                        "real_sample": self._truncate_data(real_response),
                        "mock_sample": self._truncate_data(mock_response),
                    }
                )

        # Calculate accuracy score
        if comparison_results["total_comparisons"] > 0:
            comparison_results["accuracy_score"] = (
                comparison_results["matches"] / comparison_results["total_comparisons"]
            )

        return comparison_results

    def _compare_responses(self, real_response: Any, mock_response: Any) -> dict:
        """Compare real and mock responses for differences."""
        differences = []

        if type(real_response) != type(mock_response):
            differences.append(
                {
                    "type": "type_mismatch",
                    "real_type": str(type(real_response)),
                    "mock_type": str(type(mock_response)),
                }
            )
            return {"is_match": False, "differences": differences}

        if isinstance(real_response, dict):
            return self._compare_dicts(real_response, mock_response)
        if isinstance(real_response, list):
            return self._compare_lists(real_response, mock_response)
        is_match = real_response == mock_response
        if not is_match:
            differences.append(
                {
                    "type": "value_mismatch",
                    "real": str(real_response),
                    "mock": str(mock_response),
                }
            )
        return {"is_match": is_match, "differences": differences}

    def _compare_dicts(self, real_dict: dict, mock_dict: dict) -> dict:
        """Compare dictionary responses."""
        differences = []

        # Check for missing keys in mock
        for key in real_dict:
            if key not in mock_dict:
                differences.append(
                    {
                        "type": "missing_key_in_mock",
                        "key": key,
                        "real_value": str(real_dict[key]),
                    }
                )

        # Check for extra keys in mock
        for key in mock_dict:
            if key not in real_dict:
                differences.append(
                    {
                        "type": "extra_key_in_mock",
                        "key": key,
                        "mock_value": str(mock_dict[key]),
                    }
                )

        # Compare common keys
        for key in set(real_dict.keys()) & set(mock_dict.keys()):
            nested_result = self._compare_responses(real_dict[key], mock_dict[key])
            if not nested_result["is_match"]:
                for diff in nested_result["differences"]:
                    diff["path"] = f"{key}.{diff.get('path', '')}"
                    differences.append(diff)

        return {"is_match": len(differences) == 0, "differences": differences}

    def _compare_lists(self, real_list: list, mock_list: list) -> dict:
        """Compare list responses."""
        differences = []

        if len(real_list) != len(mock_list):
            differences.append(
                {
                    "type": "length_mismatch",
                    "real_length": len(real_list),
                    "mock_length": len(mock_list),
                }
            )

        # Compare elements up to the shorter length
        min_length = min(len(real_list), len(mock_list))
        for i in range(min_length):
            nested_result = self._compare_responses(real_list[i], mock_list[i])
            if not nested_result["is_match"]:
                for diff in nested_result["differences"]:
                    diff["path"] = f"[{i}].{diff.get('path', '')}"
                    differences.append(diff)

        return {"is_match": len(differences) == 0, "differences": differences}

    def _truncate_data(self, data: Any, max_length: int = 200) -> str:
        """Truncate data for display."""
        data_str = str(data)
        if len(data_str) <= max_length:
            return data_str
        return data_str[:max_length] + "..."

    def generate_report(self, analysis: dict, output_file: str = None) -> str:
        """Generate a human-readable analysis report."""
        report_lines = [
            "# Capture Analysis Report",
            f"Generated: {datetime.now().isoformat()}",
            "",
            "## Summary",
            f"Total Interactions: {analysis.get('total_interactions', 0)}",
            "",
        ]

        # Service breakdown
        if "by_service" in analysis:
            report_lines.extend(["## Service Breakdown", ""])

            for service, data in analysis["by_service"].items():
                report_lines.extend(
                    [
                        f"### {service}",
                        f"- Total calls: {data['count']}",
                        f"- Average duration: {data['avg_duration']:.2f}ms",
                        f"- Errors: {data['errors']}",
                        f"- Operations: {dict(data['operations'])}",
                        "",
                    ]
                )

        # Performance analysis
        if "performance" in analysis:
            perf = analysis["performance"]
            report_lines.extend(
                [
                    "## Performance Analysis",
                    f"- Total duration: {perf['total_duration']:.2f}ms",
                    f"- Average duration: {perf['avg_duration']:.2f}ms",
                    "",
                ]
            )

            if perf.get("slowest_operations"):
                report_lines.extend(["### Slowest Operations", ""])
                for op in perf["slowest_operations"]:
                    report_lines.append(
                        f"- {op['service']}.{op['operation']}: {op['duration']:.2f}ms"
                    )
                report_lines.append("")

        # Error analysis
        if analysis.get("errors"):
            report_lines.extend(["## Errors", ""])
            for error in analysis["errors"]:
                report_lines.append(
                    f"- {error['service']}.{error['operation']}: {error['error']}"
                )
            report_lines.append("")

        report_content = "\n".join(report_lines)

        if output_file:
            with open(output_file, "w") as f:
                f.write(report_content)

        return report_content


def create_mock_baseline(capture_file: str, output_file: str):
    """Create a mock response baseline from captured real data."""
    try:
        with open(capture_file) as f:
            capture_data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load capture file: {e}")

    mock_responses = {}

    for interaction in capture_data.get("interactions", []):
        if interaction.get("status") != "success" or not interaction.get("response"):
            continue

        service = interaction.get("service")
        operation = interaction.get("operation")
        response = interaction.get("response")

        mock_key = f"{service}.{operation}"

        # Use the first successful response as the mock baseline
        if mock_key not in mock_responses:
            mock_responses[mock_key] = response

    with open(output_file, "w") as f:
        json.dump(mock_responses, f, indent=2, default=str)

    return len(mock_responses)
