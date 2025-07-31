#!/usr/bin/env python3
"""
PR Comment Formatter - Structured comment formatting system for PR replies with status indicators.

This utility generates structured responses for PR comments with consistent formatting,
status indicators, and table layouts for comprehensive comment tracking.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CommentStatus(Enum):
    """Status indicators for PR comment responses."""

    RESOLVED = "✅ RESOLVED"
    FIXED = "✅ FIXED"
    VALIDATED = "✅ VALIDATED"
    ADDRESSED = "✅ ADDRESSED"
    ACKNOWLEDGED = "🔄 ACKNOWLEDGED"
    CLARIFICATION = "📝 CLARIFICATION"
    REJECTED = "❌ REJECTED"
    SKIPPED = "❌ SKIPPED"
    DECLINED = "❌ DECLINED"
    PENDING = "⏳ PENDING"

    @classmethod
    def from_string(cls, status_str: str) -> "CommentStatus":
        """Convert string to CommentStatus enum."""
        status_map = {
            "resolved": cls.RESOLVED,
            "fixed": cls.FIXED,
            "validated": cls.VALIDATED,
            "addressed": cls.ADDRESSED,
            "acknowledged": cls.ACKNOWLEDGED,
            "clarification": cls.CLARIFICATION,
            "rejected": cls.REJECTED,
            "skipped": cls.SKIPPED,
            "declined": cls.DECLINED,
            "pending": cls.PENDING,
        }
        return status_map.get(status_str.lower(), cls.PENDING)


@dataclass
class UserComment:
    """Represents a user comment with response details."""

    line_number: int | None = None
    text: str = ""
    response: str = ""
    status: CommentStatus = CommentStatus.PENDING

    def format_line_ref(self) -> str:
        """Format line number reference."""
        return f"Line {self.line_number}" if self.line_number else "General"


@dataclass
class CopilotComment:
    """Represents a Copilot comment with status and reasoning."""

    description: str = ""
    status: CommentStatus = CommentStatus.PENDING
    reason: str = ""

    def is_positive_status(self) -> bool:
        """Check if status is positive (resolved, fixed, validated)."""
        return self.status in [
            CommentStatus.RESOLVED,
            CommentStatus.FIXED,
            CommentStatus.VALIDATED,
        ]


@dataclass
class TaskItem:
    """Represents a completed task with description and status."""

    description: str = ""
    details: list[str] = field(default_factory=list)
    status: CommentStatus = CommentStatus.RESOLVED

    def format_task(self) -> str:
        """Format task with status indicator."""
        result = f"{self.status.value} {self.description}"
        if self.details:
            for detail in self.details:
                result += f"\n- {detail}"
        return result


@dataclass
class PRCommentResponse:
    """Complete PR comment response structure."""

    summary_title: str = ""
    tasks: list[TaskItem] = field(default_factory=list)
    user_comments: list[UserComment] = field(default_factory=list)
    copilot_comments: list[CopilotComment] = field(default_factory=list)
    final_status: str = ""

    def add_task(
        self,
        description: str,
        details: list[str] = None,
        status: CommentStatus = CommentStatus.RESOLVED,
    ) -> None:
        """Add a task to the response."""
        self.tasks.append(
            TaskItem(description=description, details=details or [], status=status)
        )

    def add_user_comment(
        self,
        line_number: int | None,
        text: str,
        response: str,
        status: CommentStatus = CommentStatus.RESOLVED,
    ) -> None:
        """Add a user comment to the response."""
        self.user_comments.append(
            UserComment(
                line_number=line_number, text=text, response=response, status=status
            )
        )

    def add_copilot_comment(
        self, description: str, status: CommentStatus, reason: str
    ) -> None:
        """Add a Copilot comment to the response."""
        self.copilot_comments.append(
            CopilotComment(description=description, status=status, reason=reason)
        )

    def format_response(self) -> str:
        """Format the complete PR comment response."""
        lines = []

        # Summary header
        lines.append(f"Summary: {self.summary_title}")
        lines.append("")

        # Tasks section
        for task in self.tasks:
            lines.append(task.format_task())
            lines.append("")

        # User comments section
        if self.user_comments:
            lines.append("✅ User Comments Addressed")
            for i, comment in enumerate(self.user_comments, 1):
                lines.append(f'{i}. {comment.format_line_ref()} - "{comment.text}"')
                lines.append(f"   - {comment.status.value} {comment.response}")
            lines.append("")

        # Copilot comments section
        if self.copilot_comments:
            lines.append("✅ Copilot Comments Status")

            # Table header
            lines.append(
                "| Comment               | Status      | Reason                                             |"
            )
            lines.append(
                "|-----------------------|-------------|----------------------------------------------------|"
            )

            # Table rows
            for comment in self.copilot_comments:
                # Truncate long descriptions and reasons for table formatting
                desc = (
                    comment.description[:20] + "..."
                    if len(comment.description) > 20
                    else comment.description
                )
                reason = (
                    comment.reason[:50] + "..."
                    if len(comment.reason) > 50
                    else comment.reason
                )
                status_display = comment.status.value.split()[
                    1
                ]  # Remove emoji for table
                lines.append(f"| {desc:<21} | {status_display:<11} | {reason:<50} |")
            lines.append("")

        # Final status
        if self.final_status:
            lines.append("✅ Final Status")
            lines.append(self.final_status)

        return "\n".join(lines)


class PRCommentFormatter:
    """Main formatter class for PR comment responses."""

    @staticmethod
    def create_response(summary_title: str) -> PRCommentResponse:
        """Create a new PR comment response."""
        return PRCommentResponse(summary_title=summary_title)

    @staticmethod
    def from_json(json_data: str | dict[str, Any]) -> PRCommentResponse:
        """Create PR comment response from JSON data."""
        data = json.loads(json_data) if isinstance(json_data, str) else json_data

        response = PRCommentResponse(summary_title=data.get("summary_title", ""))

        # Load tasks
        for task_data in data.get("tasks", []):
            response.add_task(
                description=task_data.get("description", ""),
                details=task_data.get("details", []),
                status=CommentStatus.from_string(task_data.get("status", "resolved")),
            )

        # Load user comments
        for comment_data in data.get("user_comments", []):
            response.add_user_comment(
                line_number=comment_data.get("line_number"),
                text=comment_data.get("text", ""),
                response=comment_data.get("response", ""),
                status=CommentStatus.from_string(
                    comment_data.get("status", "resolved")
                ),
            )

        # Load copilot comments
        for comment_data in data.get("copilot_comments", []):
            response.add_copilot_comment(
                description=comment_data.get("description", ""),
                status=CommentStatus.from_string(comment_data.get("status", "pending")),
                reason=comment_data.get("reason", ""),
            )

        response.final_status = data.get("final_status", "")

        return response

    @staticmethod
    def generate_template() -> str:
        """Generate a template for PR comment responses."""
        response = PRCommentResponse(summary_title="PR Updated & Comments Addressed")

        # Add example tasks
        response.add_task(
            "GitHub PR Description Updated",
            [
                "Comprehensive overview of changes",
                "Technical details showing before/after code",
                "Testing improvements explained",
            ],
        )

        # Add example user comments
        response.add_user_comment(
            486,
            "Why not delete this and rely on fakes?",
            "Added comment explaining unit test performance needs",
        )

        response.add_user_comment(
            507,
            "what about this (async sleep suggestion)",
            "Added comment explaining Flask synchronous architecture",
        )

        # Add example copilot comments
        response.add_copilot_comment(
            "Firestore tuple index",
            CommentStatus.VALIDATED,
            "Code is correct, Copilot was wrong",
        )

        response.add_copilot_comment(
            "Async sleep suggestion",
            CommentStatus.REJECTED,
            "Flask is synchronous, major refactor not justified",
        )

        response.final_status = (
            "All comments addressed, tests passing, ready for review"
        )

        return response.format_response()


def main():
    """Demo/test function showing usage examples."""
    # Example 1: Create response programmatically
    print("=== Example 1: Programmatic Creation ===")
    response = PRCommentFormatter.create_response("Bug Fix & Comment Resolution")

    response.add_task(
        "Fixed critical bug",
        ["Root cause identified", "Tests added", "Edge cases covered"],
    )
    response.add_user_comment(
        123, "Is this thread-safe?", "Added synchronization locks"
    )
    response.add_copilot_comment(
        "Dead code removal", CommentStatus.FIXED, "Cleaned up unused variables"
    )
    response.final_status = "Ready for merge"

    print(response.format_response())
    print("\n" + "=" * 60 + "\n")

    # Example 2: Generate template
    print("=== Example 2: Template Generation ===")
    template = PRCommentFormatter.generate_template()
    print(template)

    # Example 3: JSON input/output
    print("\n" + "=" * 60 + "\n")
    print("=== Example 3: JSON Integration ===")
    json_data = {
        "summary_title": "Security Fix Implementation",
        "tasks": [
            {
                "description": "Security vulnerability patched",
                "details": ["Input validation added", "SQL injection prevented"],
                "status": "fixed",
            }
        ],
        "user_comments": [
            {
                "line_number": 42,
                "text": "What about XSS protection?",
                "response": "HTML escaping implemented",
                "status": "resolved",
            }
        ],
        "copilot_comments": [
            {
                "description": "Sanitize inputs",
                "status": "fixed",
                "reason": "All user inputs now validated",
            }
        ],
        "final_status": "Security audit complete",
    }

    response_from_json = PRCommentFormatter.from_json(json_data)
    print(response_from_json.format_response())


if __name__ == "__main__":
    main()
