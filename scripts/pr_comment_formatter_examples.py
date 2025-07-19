#!/usr/bin/env python3
"""
PR Comment Formatter Examples - Comprehensive usage examples for the PR comment formatter.

This file demonstrates various usage patterns and provides real-world examples
of how to use the PR comment formatting system.
"""

import json

from pr_comment_formatter import CommentStatus, PRCommentFormatter


def example_firestore_bug_fix():
    """Example response for a Firestore bug fix PR."""
    response = PRCommentFormatter.create_response(
        "Firestore Bug Fix & Comment Resolution"
    )

    # Add tasks
    response.add_task(
        "Fixed Firestore transaction bug",
        [
            "Identified race condition in document updates",
            "Implemented proper transaction retry logic",
            "Added comprehensive error handling",
            "Updated all affected test cases",
        ],
        CommentStatus.FIXED,
    )

    response.add_task(
        "Enhanced test coverage",
        [
            "Added unit tests for transaction scenarios",
            "Implemented integration tests with real Firestore",
            "Added performance benchmarks",
            "Verified edge case handling",
        ],
        CommentStatus.RESOLVED,
    )

    # Add user comments
    response.add_user_comment(
        486,
        "Why not delete this and rely on fakes?",
        "Added comment explaining unit test performance needs - even perfect fakes add 0.9s latency per test, bypassing is correct for unit tests",
        CommentStatus.RESOLVED,
    )

    response.add_user_comment(
        507,
        "what about this (async sleep suggestion)",
        "Added comment explaining Flask synchronous architecture - async sleep would require major refactor not justified for this fix",
        CommentStatus.ADDRESSED,
    )

    response.add_user_comment(
        622,
        "Should the fallback just be None?",
        "Added comment explaining verification logic requirement - None would cause immediate verification failure",
        CommentStatus.RESOLVED,
    )

    # Add copilot comments
    response.add_copilot_comment(
        "Firestore tuple index",
        CommentStatus.VALIDATED,
        "Code is correct, Copilot was wrong about tuple syntax",
    )

    response.add_copilot_comment(
        "Docstring update",
        CommentStatus.FIXED,
        "Updated to match actual implementation",
    )

    response.add_copilot_comment(
        "Async sleep suggestion",
        CommentStatus.REJECTED,
        "Flask is synchronous, major refactor not justified",
    )

    response.add_copilot_comment(
        "Debug log level",
        CommentStatus.FIXED,
        "Changed to debug level for better production logs",
    )

    response.add_copilot_comment(
        "Dead code removal",
        CommentStatus.FIXED,
        "Cleaned up unused variables and imports",
    )

    response.add_copilot_comment(
        "Boolean parsing",
        CommentStatus.SKIPPED,
        "Consistent pattern across codebase, no change needed",
    )

    response.add_copilot_comment(
        "Test assertion improvement",
        CommentStatus.FIXED,
        "Test rewritten with FakeFirestoreClient for better isolation",
    )

    response.final_status = (
        "All comments addressed, tests passing (94/94), ready for review"
    )

    return response


def example_security_fix():
    """Example response for a security vulnerability fix."""
    response = PRCommentFormatter.create_response("Security Vulnerability Fix")

    response.add_task(
        "Fixed SQL injection vulnerability",
        [
            "Replaced string concatenation with parameterized queries",
            "Added input validation and sanitization",
            "Implemented proper error handling for malformed inputs",
            "Added security tests for all endpoints",
        ],
        CommentStatus.FIXED,
    )

    response.add_task(
        "Enhanced authentication system",
        [
            "Implemented JWT token validation",
            "Added rate limiting to prevent brute force attacks",
            "Enhanced session management",
            "Added audit logging for security events",
        ],
        CommentStatus.RESOLVED,
    )

    response.add_user_comment(
        234,
        "What about XSS protection?",
        "Implemented HTML escaping for all user inputs and added Content Security Policy headers",
        CommentStatus.RESOLVED,
    )

    response.add_user_comment(
        456,
        "Are we sanitizing file uploads?",
        "Added file type validation, size limits, and virus scanning for all uploads",
        CommentStatus.ADDRESSED,
    )

    response.add_copilot_comment(
        "Input validation",
        CommentStatus.FIXED,
        "All user inputs now validated against whitelist patterns",
    )

    response.add_copilot_comment(
        "SQL injection risk",
        CommentStatus.FIXED,
        "Replaced all dynamic SQL with parameterized queries",
    )

    response.add_copilot_comment(
        "Password hashing",
        CommentStatus.VALIDATED,
        "Already using bcrypt with proper salt rounds",
    )

    response.final_status = "Security audit complete, all vulnerabilities addressed"

    return response


def example_performance_optimization():
    """Example response for performance optimization PR."""
    response = PRCommentFormatter.create_response(
        "Performance Optimization Implementation"
    )

    response.add_task(
        "Optimized database queries",
        [
            "Added proper indexes for frequently queried fields",
            "Implemented query result caching",
            "Reduced N+1 query problems with eager loading",
            "Added query performance monitoring",
        ],
        CommentStatus.RESOLVED,
    )

    response.add_task(
        "Frontend optimization",
        [
            "Implemented code splitting for faster initial load",
            "Added image lazy loading",
            "Compressed and minified assets",
            "Added service worker for offline capability",
        ],
        CommentStatus.FIXED,
    )

    response.add_user_comment(
        123,
        "Why not use Redis for caching?",
        "Added Redis caching layer for session data and frequently accessed content",
        CommentStatus.RESOLVED,
    )

    response.add_user_comment(
        789,
        "Are we monitoring these performance improvements?",
        "Added comprehensive performance metrics and alerting dashboard",
        CommentStatus.ADDRESSED,
    )

    response.add_copilot_comment(
        "Database connection pooling",
        CommentStatus.FIXED,
        "Implemented connection pooling with proper lifecycle management",
    )

    response.add_copilot_comment(
        "Memory leak in event handlers",
        CommentStatus.FIXED,
        "Fixed event listener cleanup in component unmount",
    )

    response.add_copilot_comment(
        "Bundle size optimization",
        CommentStatus.ADDRESSED,
        "Reduced bundle size by 40% through tree shaking and dependency audit",
    )

    response.final_status = (
        "Performance improved by 60%, all optimization goals achieved"
    )

    return response


def example_api_refactor():
    """Example response for API refactoring PR."""
    response = PRCommentFormatter.create_response("API Refactor & Modernization")

    response.add_task(
        "Migrated to RESTful API design",
        [
            "Restructured endpoints to follow REST conventions",
            "Implemented proper HTTP status codes",
            "Added versioning support",
            "Updated all client code to use new endpoints",
        ],
        CommentStatus.RESOLVED,
    )

    response.add_task(
        "Enhanced API documentation",
        [
            "Generated OpenAPI/Swagger specification",
            "Added interactive API documentation",
            "Created usage examples for all endpoints",
            "Added rate limiting documentation",
        ],
        CommentStatus.FIXED,
    )

    response.add_user_comment(
        345,
        "What about backward compatibility?",
        "Implemented API versioning with /v1/ and /v2/ endpoints, v1 will be deprecated in 6 months",
        CommentStatus.ADDRESSED,
    )

    response.add_user_comment(
        567,
        "Are we handling API rate limits properly?",
        "Added rate limiting middleware with different tiers for authenticated vs anonymous users",
        CommentStatus.RESOLVED,
    )

    response.add_copilot_comment(
        "Error response format",
        CommentStatus.FIXED,
        "Standardized error responses with consistent JSON structure",
    )

    response.add_copilot_comment(
        "Authentication middleware",
        CommentStatus.VALIDATED,
        "JWT implementation is correct and secure",
    )

    response.add_copilot_comment(
        "Request validation",
        CommentStatus.FIXED,
        "Added comprehensive input validation with detailed error messages",
    )

    response.final_status = "API refactor complete, all endpoints tested and documented"

    return response


def export_examples_as_json():
    """Export all examples as JSON files for easy reuse."""
    examples = {
        "firestore_bug_fix": example_firestore_bug_fix(),
        "security_fix": example_security_fix(),
        "performance_optimization": example_performance_optimization(),
        "api_refactor": example_api_refactor(),
    }

    for name, response in examples.items():
        # Convert to JSON-serializable format
        json_data = {
            "summary_title": response.summary_title,
            "tasks": [
                {
                    "description": task.description,
                    "details": task.details,
                    "status": task.status.name.lower(),
                }
                for task in response.tasks
            ],
            "user_comments": [
                {
                    "line_number": comment.line_number,
                    "text": comment.text,
                    "response": comment.response,
                    "status": comment.status.name.lower(),
                }
                for comment in response.user_comments
            ],
            "copilot_comments": [
                {
                    "description": comment.description,
                    "status": comment.status.name.lower(),
                    "reason": comment.reason,
                }
                for comment in response.copilot_comments
            ],
            "final_status": response.final_status,
        }

        filename = f"/tmp/pr_example_{name}.json"
        with open(filename, "w") as f:
            json.dump(json_data, f, indent=2)
        print(f"✅ Exported example to {filename}")


def main():
    """Main function demonstrating all examples."""
    print("=== PR Comment Formatter Examples ===\n")

    examples = [
        ("Firestore Bug Fix", example_firestore_bug_fix()),
        ("Security Fix", example_security_fix()),
        ("Performance Optimization", example_performance_optimization()),
        ("API Refactor", example_api_refactor()),
    ]

    for title, response in examples:
        print(f"=== {title} ===")
        print(response.format_response())
        print("\n" + "=" * 60 + "\n")

    # Export JSON examples
    print("Exporting JSON examples...")
    export_examples_as_json()

    print("\n✅ All examples generated successfully!")
    print("\nTo use these examples:")
    print("1. Copy the formatted text directly into your PR comment")
    print(
        "2. Use the JSON files with: ./claude_command_scripts/pr-comment-format.sh json <filename>"
    )
    print("3. Modify the examples to match your specific PR needs")


if __name__ == "__main__":
    main()
