#!/usr/bin/env python3
"""
Example demonstrating the capture framework for real service interactions.
Shows how to use capture mode to record API calls and analyze the data.
"""

import json
import os
import sys
import tempfile

# Add project root to path
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, project_root)

from mvp_site.testing_framework.capture_analysis import CaptureAnalyzer
from mvp_site.testing_framework.factory import get_service_provider


def demo_capture_mode():
    """Demonstrate capture mode functionality."""
    print("=== Capture Framework Demo ===\n")

    # Set up environment for capture mode
    os.environ["TEST_MODE"] = "capture"
    os.environ["TEST_CAPTURE_DIR"] = "/tmp/test_captures_demo"

    # Ensure capture directory exists
    os.makedirs("/tmp/test_captures_demo", exist_ok=True)

    print("1. Getting service provider in capture mode...")
    try:
        provider = get_service_provider("capture")
        print(f"✓ Created provider: {type(provider).__name__}")
        print(f"✓ Capture mode enabled: {provider.capture_mode}")
    except Exception as e:
        print(f"✗ Error creating provider: {e}")
        print(
            "Note: This demo requires real service configuration for full functionality"
        )
        return demo_mock_capture()

    print("\n2. Simulating service interactions...")

    try:
        # These would normally make real API calls if configured
        print("   - Getting Firestore client...")
        firestore = provider.get_firestore()

        print("   - Getting Gemini client...")
        gemini = provider.get_gemini()

        print("   - Getting auth service...")
        auth = provider.get_auth()

        print("✓ All services initialized")

        # Try some basic operations (these will fail without real config but demonstrate structure)
        print("\n3. Attempting service operations...")

        try:
            # This would be captured if real services were configured
            collection = firestore.collection("test_collection")
            print("   - Created collection reference")

            # This would make a real API call and be captured
            # docs = collection.get()
            # print(f"   - Retrieved {len(docs)} documents")

        except Exception as e:
            print(f"   - Service operation failed (expected without real config): {e}")

        print("\n4. Getting capture summary...")
        summary = provider.get_capture_summary()
        print(f"✓ Capture summary: {json.dumps(summary, indent=2)}")

        print("\n5. Saving capture data...")
        if hasattr(provider, "_capture_manager") and provider._capture_manager:
            try:
                capture_file = provider.save_capture_data()
                print(f"✓ Capture data saved to: {capture_file}")
                return capture_file
            except Exception as e:
                print(f"✗ Error saving capture data: {e}")

    except Exception as e:
        print(f"✗ Error during service operations: {e}")
        print("This is expected without real service configuration")

    finally:
        print("\n6. Cleaning up...")
        provider.cleanup()
        print("✓ Cleanup completed")


def demo_mock_capture():
    """Demonstrate capture analysis with mock data."""
    print("\n=== Mock Capture Analysis Demo ===\n")

    # Create temporary capture data for demonstration
    temp_dir = tempfile.mkdtemp()
    capture_file = os.path.join(temp_dir, "demo_capture.json")

    # Sample capture data
    sample_data = {
        "session_id": "demo_session_123",
        "timestamp": "2025-07-14T10:00:00Z",
        "total_interactions": 4,
        "interactions": [
            {
                "id": 0,
                "timestamp": "2025-07-14T10:00:01Z",
                "service": "firestore",
                "operation": "collection.get",
                "request": {"collection": "campaigns"},
                "response": {
                    "document_count": 2,
                    "documents": [
                        {
                            "id": "campaign1",
                            "data": {"name": "Adventure Quest", "status": "active"},
                        },
                        {
                            "id": "campaign2",
                            "data": {"name": "Dragon Hunt", "status": "completed"},
                        },
                    ],
                },
                "status": "success",
                "duration_ms": 145.2,
            },
            {
                "id": 1,
                "timestamp": "2025-07-14T10:00:02Z",
                "service": "gemini",
                "operation": "generate_content",
                "request": {"prompt": "Generate a dungeon description"},
                "response": {
                    "text": "A dark, twisting corridor stretches before you...",
                    "finish_reason": "STOP",
                    "usage_metadata": {"prompt_tokens": 15, "response_tokens": 87},
                },
                "status": "success",
                "duration_ms": 1250.8,
            },
            {
                "id": 2,
                "timestamp": "2025-07-14T10:00:03Z",
                "service": "firestore",
                "operation": "document.set",
                "request": {
                    "document": "campaigns/campaign1",
                    "data": {"last_played": "2025-07-14T10:00:00Z"},
                    "merge": True,
                },
                "response": {"write_result": "SUCCESS"},
                "status": "success",
                "duration_ms": 89.3,
            },
            {
                "id": 3,
                "timestamp": "2025-07-14T10:00:04Z",
                "service": "gemini",
                "operation": "generate_content",
                "request": {"prompt": "Roll initiative for 4 characters"},
                "response": {},
                "status": "error",
                "error": "Rate limit exceeded",
                "error_type": "RateLimitError",
                "duration_ms": 1205.1,
            },
        ],
    }

    # Save sample data
    with open(capture_file, "w") as f:
        json.dump(sample_data, f, indent=2)

    print(f"1. Created sample capture file: {capture_file}")

    # Analyze the capture data
    print("\n2. Analyzing capture data...")
    analyzer = CaptureAnalyzer(temp_dir)

    # Load and analyze the specific file
    with open(capture_file) as f:
        data = json.load(f)

    analysis = analyzer._analyze_interactions(data["interactions"])

    print("\n3. Analysis Results:")
    print(f"   Total interactions: {analysis['total_interactions']}")
    print(f"   Services used: {list(analysis['by_service'].keys())}")
    print(f"   Success rate: {analysis.get('success_rate', 0):.1%}")
    print(f"   Average duration: {analysis['performance']['avg_duration']:.1f}ms")
    print(f"   Errors: {len(analysis['errors'])}")

    # Show service breakdown
    print("\n4. Service Breakdown:")
    for service, stats in analysis["by_service"].items():
        print(f"   {service}:")
        print(f"     - Calls: {stats['count']}")
        print(f"     - Operations: {dict(stats['operations'])}")
        print(f"     - Avg duration: {stats['avg_duration']:.1f}ms")
        print(f"     - Errors: {stats['errors']}")

    # Generate a report
    print("\n5. Generating analysis report...")
    report = analyzer.generate_report(analysis)
    print("✓ Report generated (sample below):")
    print("-" * 50)
    print(report[:500] + "..." if len(report) > 500 else report)
    print("-" * 50)

    # Demonstrate mock comparison
    print("\n6. Mock comparison demo...")
    mock_responses = {
        "firestore.collection.get": {
            "document_count": 2,
            "documents": [
                {"id": "mock1", "data": {"name": "Mock Campaign"}},
                {"id": "mock2", "data": {"name": "Another Mock"}},
            ],
        },
        "gemini.generate_content": {
            "text": "Mock generated content",
            "finish_reason": "STOP",
        },
        # Missing firestore.document.set mock to show gap detection
    }

    comparison = analyzer.compare_with_mock(capture_file, mock_responses)

    print(f"   Mock accuracy: {comparison['accuracy_score']:.1%}")
    print(f"   Total comparisons: {comparison['total_comparisons']}")
    print(f"   Matches: {comparison['matches']}")
    print(f"   Differences: {len(comparison['differences'])}")
    print(f"   Missing mocks: {len(comparison['missing_mocks'])}")

    if comparison["differences"]:
        print("\n   Sample difference:")
        diff = comparison["differences"][0]
        print(f"     Service: {diff['service']}.{diff['operation']}")
        print(f"     Differences found: {len(diff['differences'])}")

    # Clean up
    import shutil

    shutil.rmtree(temp_dir)
    print("\n7. Cleaned up temporary files")

    return capture_file


def demo_cli_tools():
    """Demonstrate the CLI analysis tools."""
    print("\n=== CLI Tools Demo ===\n")

    print("Available CLI commands for capture analysis:")
    print()
    print("1. python -m mvp_site.testing_framework.capture_cli analyze")
    print("   - Analyze recent captures")
    print("   - Generate performance and error reports")
    print()
    print(
        "2. python -m mvp_site.testing_framework.capture_cli compare <capture_file> <mock_file>"
    )
    print("   - Compare captured data with mock responses")
    print("   - Identify mock accuracy gaps")
    print()
    print(
        "3. python -m mvp_site.testing_framework.capture_cli baseline <capture_file> <output_file>"
    )
    print("   - Create mock baseline from real capture data")
    print("   - Generate initial mock responses")
    print()
    print("4. python -m mvp_site.testing_framework.capture_cli list")
    print("   - List available capture files")
    print("   - Show file sizes and timestamps")
    print()
    print("5. python -m mvp_site.testing_framework.capture_cli cleanup --days 7")
    print("   - Clean up old capture files")
    print("   - Prevent disk space issues")

    print("\nExample usage:")
    print("  export TEST_MODE=capture")
    print("  export TEST_CAPTURE_DIR=/tmp/test_captures")
    print("  # Run tests with /testerc command")
    print("  python -m mvp_site.testing_framework.capture_cli analyze --days 1")


def main():
    """Main demo function."""
    print("Capture Framework Demonstration")
    print("=" * 50)
    print()
    print("This demo shows how to use the capture framework to:")
    print("- Record real service interactions during testing")
    print("- Analyze captured data for performance insights")
    print("- Compare real responses with mock data")
    print("- Generate mock baselines from real data")
    print()

    try:
        # Try real capture mode first
        capture_file = demo_capture_mode()

        # Always run mock analysis demo
        demo_mock_capture()

        # Show CLI tools
        demo_cli_tools()

        print("\n" + "=" * 50)
        print("Demo completed successfully!")
        print("\nNext steps:")
        print("1. Configure real service credentials for full functionality")
        print("2. Run tests with TEST_MODE=capture to record real interactions")
        print("3. Use analysis tools to improve mock accuracy")
        print("4. Set up automated capture cleanup in your CI/CD pipeline")

    except Exception as e:
        print(f"\nDemo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
