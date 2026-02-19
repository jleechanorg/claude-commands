#!/usr/bin/env python3
"""
Request Optimization Utility

Prevents API timeouts by managing request sizes, implementing smart batching,
and providing timeout mitigation strategies.
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class RequestMetrics:
    """Track request performance metrics"""

    size_chars: int
    timeout_count: int
    retry_count: int
    success: bool
    duration_ms: int
    operation_type: str


class RequestSizeEstimator:
    """Estimates request sizes to prevent timeouts"""

    # Size limits (in characters)
    MAX_FILE_READ_SIZE = 100000  # ~2000 lines
    MAX_CONTEXT_SIZE = 50000  # Total context per request
    MAX_MULTIEDIT_OPS = 4  # Operations per MultiEdit
    MAX_TOOLS_PER_REQUEST = 6  # Tool calls per message

    def __init__(self):
        self.request_history = []

    def estimate_file_read_size(self, filepath: str) -> Tuple[int, bool]:
        """Estimate file read size and whether it needs splitting"""
        try:
            file_size = os.path.getsize(filepath)
            # Rough estimate: 80 chars per line average
            estimated_chars = file_size * 1.2  # Add overhead for formatting

            needs_split = estimated_chars > self.MAX_FILE_READ_SIZE
            return int(estimated_chars), needs_split

        except OSError:
            return 0, False

    def calculate_multiedit_size(self, edits: List[Dict]) -> Tuple[int, bool]:
        """Calculate MultiEdit request size"""
        total_size = 0

        for edit in edits:
            total_size += len(edit.get("old_string", ""))
            total_size += len(edit.get("new_string", ""))

        # Add overhead for JSON structure
        total_size = int(total_size * 1.3)

        needs_split = (
            len(edits) > self.MAX_MULTIEDIT_OPS or total_size > self.MAX_CONTEXT_SIZE
        )
        return total_size, needs_split

    def estimate_tool_request_size(
        self, tools: List[Dict], context: str = ""
    ) -> Tuple[int, str]:
        """Estimate total request size and recommend action"""
        total_size = len(context)

        for tool in tools:
            # Estimate tool call size
            tool_size = len(json.dumps(tool, separators=(",", ":")))
            total_size += tool_size

        if total_size > self.MAX_CONTEXT_SIZE:
            return total_size, "split_required"
        elif total_size > self.MAX_CONTEXT_SIZE * 0.8:
            return total_size, "warning"
        else:
            return total_size, "ok"

    def suggest_file_read_params(self, filepath: str) -> Dict[str, Any]:
        """Suggest optimal file read parameters"""
        estimated_size, needs_split = self.estimate_file_read_size(filepath)

        if not needs_split:
            return {"file_path": filepath}

        # Calculate optimal offset/limit
        max_lines = self.MAX_FILE_READ_SIZE // 80  # Estimate lines

        return {
            "file_path": filepath,
            "limit": max_lines,
            "offset": 0,  # Start from beginning
            "note": f"File is large ({estimated_size} chars), reading first {max_lines} lines",
        }

    def split_multiedit(
        self, file_path: str, edits: List[Dict]
    ) -> List[Tuple[str, List[Dict]]]:
        """Split large MultiEdit into smaller chunks"""
        size, needs_split = self.calculate_multiedit_size(edits)

        if not needs_split:
            return [(file_path, edits)]

        chunks = []
        current_chunk = []
        current_size = 0

        for edit in edits:
            edit_size = len(edit.get("old_string", "")) + len(
                edit.get("new_string", "")
            )

            if (
                len(current_chunk) >= self.MAX_MULTIEDIT_OPS
                or current_size + edit_size > self.MAX_CONTEXT_SIZE * 0.7
            ):
                if current_chunk:
                    chunks.append((file_path, current_chunk))
                    current_chunk = []
                    current_size = 0

            current_chunk.append(edit)
            current_size += edit_size

        if current_chunk:
            chunks.append((file_path, current_chunk))

        return chunks


class TimeoutHandler:
    """Handles API timeouts with smart retry logic"""

    def __init__(self):
        self.timeout_counts = {}
        self.last_timeout_time = {}

    def should_retry(self, operation_type: str, attempt: int) -> bool:
        """Determine if operation should be retried"""

        # Critical operations: allow more retries
        critical_ops = ["commit", "push", "deploy", "test"]
        max_retries = 5 if operation_type in critical_ops else 3

        # Non-critical operations: fewer retries
        non_critical_ops = ["analysis", "review", "format", "lint"]
        if operation_type in non_critical_ops and attempt >= 2:
            return False

        return attempt < max_retries

    def get_timeout_delay(self, attempt: int) -> float:
        """Calculate progressive timeout delay"""
        base_delays = [1, 2, 4, 8, 16, 32]  # seconds
        return base_delays[min(attempt - 1, len(base_delays) - 1)]

    def record_timeout(self, operation_type: str):
        """Record timeout for monitoring"""
        self.timeout_counts[operation_type] = (
            self.timeout_counts.get(operation_type, 0) + 1
        )
        self.last_timeout_time[operation_type] = time.time()

    def get_timeout_stats(self) -> Dict[str, Any]:
        """Get timeout statistics"""
        return {
            "timeout_counts": self.timeout_counts,
            "last_timeouts": self.last_timeout_time,
            "total_timeouts": sum(self.timeout_counts.values()),
        }


class RequestBatcher:
    """Batches related operations to reduce API calls"""

    def __init__(self):
        self.pending_operations = []

    def add_operation(self, op_type: str, op_data: Dict):
        """Add operation to batch"""
        self.pending_operations.append(
            {"type": op_type, "data": op_data, "timestamp": time.time()}
        )

    def should_flush_batch(self) -> bool:
        """Determine if batch should be executed"""
        if not self.pending_operations:
            return False

        # Flush if batch is large enough
        if len(self.pending_operations) >= 3:
            return True

        # Flush if oldest operation is getting stale
        oldest_time = min(op["timestamp"] for op in self.pending_operations)
        if time.time() - oldest_time > 5:  # 5 seconds
            return True

        return False

    def get_batched_operations(self) -> List[Dict]:
        """Get operations ready for batching"""
        batch = self.pending_operations.copy()
        self.pending_operations.clear()
        return batch

    def can_batch_together(self, op1: Dict, op2: Dict) -> bool:
        """Check if two operations can be batched"""
        # Same file operations can be batched
        if (
            op1["type"] in ["read", "edit"]
            and op2["type"] in ["read", "edit"]
            and op1["data"].get("file_path") == op2["data"].get("file_path")
        ):
            return True

        # Analysis operations can be batched
        if op1["type"] in ["analyze", "review"] and op2["type"] in [
            "analyze",
            "review",
        ]:
            return True

        return False


class RequestOptimizer:
    """Main request optimization coordinator"""

    def __init__(self):
        self.size_estimator = RequestSizeEstimator()
        self.timeout_handler = TimeoutHandler()
        self.batcher = RequestBatcher()
        self.metrics = []

    def optimize_file_read(self, filepath: str) -> Dict[str, Any]:
        """Optimize file read request"""
        return self.size_estimator.suggest_file_read_params(filepath)

    def optimize_multiedit(
        self, file_path: str, edits: List[Dict]
    ) -> List[Tuple[str, List[Dict]]]:
        """Optimize MultiEdit request"""
        return self.size_estimator.split_multiedit(file_path, edits)

    def check_request_size(
        self, tools: List[Dict], context: str = ""
    ) -> Tuple[bool, str]:
        """Check if request size is acceptable"""
        size, status = self.size_estimator.estimate_tool_request_size(tools, context)

        if status == "split_required":
            return (
                False,
                f"Request too large ({size} chars). Split into smaller requests.",
            )
        elif status == "warning":
            return True, f"Request is large ({size} chars). Consider splitting."
        else:
            return True, f"Request size OK ({size} chars)."

    def handle_timeout(self, operation_type: str, attempt: int) -> Tuple[bool, float]:
        """Handle API timeout"""
        self.timeout_handler.record_timeout(operation_type)

        should_retry = self.timeout_handler.should_retry(operation_type, attempt)
        delay = self.timeout_handler.get_timeout_delay(attempt)

        return should_retry, delay

    def record_success(self, operation_type: str, duration_ms: int, size_chars: int):
        """Record successful operation"""
        metric = RequestMetrics(
            size_chars=size_chars,
            timeout_count=0,
            retry_count=0,
            success=True,
            duration_ms=duration_ms,
            operation_type=operation_type,
        )
        self.metrics.append(metric)

    def get_optimization_report(self) -> str:
        """Generate optimization report"""
        stats = self.timeout_handler.get_timeout_stats()

        report = ["🚀 Request Optimization Report", ""]

        if stats["total_timeouts"] > 0:
            report.append(f"⚠️ Total Timeouts: {stats['total_timeouts']}")
            report.append("📊 Timeouts by Operation:")
            for op_type, count in stats["timeout_counts"].items():
                report.append(f"   - {op_type}: {count}")
        else:
            report.append("✅ No timeouts recorded")

        report.append("")
        report.append("📈 Recent Metrics:")
        if self.metrics:
            avg_duration = sum(m.duration_ms for m in self.metrics[-10:]) / min(
                len(self.metrics), 10
            )
            avg_size = sum(m.size_chars for m in self.metrics[-10:]) / min(
                len(self.metrics), 10
            )
            report.append(f"   - Average Duration: {avg_duration:.0f}ms")
            report.append(f"   - Average Size: {avg_size:.0f} chars")

        return "\n".join(report)


# Global optimizer instance
optimizer = RequestOptimizer()


# Convenience functions
def optimize_file_read(filepath: str) -> Dict[str, Any]:
    """Quick function to optimize file read"""
    return optimizer.optimize_file_read(filepath)


def optimize_multiedit(
    file_path: str, edits: List[Dict]
) -> List[Tuple[str, List[Dict]]]:
    """Quick function to optimize MultiEdit"""
    return optimizer.optimize_multiedit(file_path, edits)


def check_request_size(tools: List[Dict], context: str = "") -> Tuple[bool, str]:
    """Quick function to check request size"""
    return optimizer.check_request_size(tools, context)


def handle_timeout(operation_type: str, attempt: int) -> Tuple[bool, float]:
    """Quick function to handle timeout"""
    return optimizer.handle_timeout(operation_type, attempt)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        print(optimizer.get_optimization_report())
    else:
        print(
            "Request Optimizer - Use import for functionality or pass any arg for report"
        )
