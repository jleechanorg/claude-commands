#!/usr/bin/env python3
"""
Parallel test execution for PR #3491
Runs tests against both GCP preview server and local server
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Change to project root for imports
original_cwd = os.getcwd()
os.chdir(PROJECT_ROOT)

from testing_mcp.lib.server_utils import pick_free_port, start_local_mcp_server, LocalServer

PR_NUMBER = 3491
TEST_DIR = Path("testing_mcp")
EVIDENCE_BASE = Path("/tmp/worldarchitect.ai/gemini/intent-classifier")

# GCP Preview Server URL (fetched from PR #3491 comments)
# Latest preview: https://mvp-site-app-s1-i6xf2p72ka-uc.a.run.app
GCP_PREVIEW_URL = os.environ.get(
    "GCP_PREVIEW_SERVER_URL", 
    "https://mvp-site-app-s1-i6xf2p72ka-uc.a.run.app"
)
GCP_MCP_URL = f"{GCP_PREVIEW_URL}/mcp"

# Tests to run
TESTS = [
    "test_classifier_model_loading_failure.py",
    "test_agent_selection_classifier.py", 
    "test_json_parsing_failure.py",
]


def run_test(test_file: str, server_url: str, server_type: str, evidence_dir: Path) -> dict:
    """Run a single test against a server."""
    test_path = TEST_DIR / test_file
    if not test_path.exists():
        return {
            "test": test_file,
            "server": server_type,
            "status": "skipped",
            "reason": "Test file not found"
        }
    
    print(f"  🧪 Running {test_file} against {server_type}...")
    
    # Run test with evidence capture
    env = os.environ.copy()
    env["TESTING"] = "true"
    
    # Build command args - evidence is enabled by default for most tests
    # Only add --no-evidence if we want to disable it (we don't)
    cmd_args = [
        sys.executable,
        str(test_path),
        "--server-url", server_url,
    ]
    # Note: Evidence capture is enabled by default in test_agent_selection_classifier.py
    # Other tests use --evidence flag, but we'll let them handle defaults
    # Check if test supports --evidence flag (for backward compatibility)
    try:
        help_result = subprocess.run(
            [sys.executable, str(test_path), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        # If test has --evidence flag, add it (some tests may still require explicit flag)
        if "--evidence" in help_result.stdout and "--no-evidence" not in help_result.stdout:
            cmd_args.append("--evidence")
    except:
        pass
    
    # test_agent_selection_classifier.py is a comprehensive test with many real LLM calls
    # It tests all 7 agents with multiple phrases each, so it needs more time
    timeout_seconds = 1200 if "test_agent_selection_classifier" in test_file else 600  # 20 min for classifier test, 10 min for others
    
    try:
        result = subprocess.run(
            cmd_args,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        
        # Save output
        output_file = evidence_dir / f"{test_file}.log"
        output_file.write_text(result.stdout + result.stderr)
        
        return {
            "test": test_file,
            "server": server_type,
            "status": "passed" if result.returncode == 0 else "failed",
            "returncode": result.returncode,
            "output_file": str(output_file)
        }
    except subprocess.TimeoutExpired:
        timeout_minutes = timeout_seconds // 60
        return {
            "test": test_file,
            "server": server_type,
            "status": "timeout",
            "reason": f"Test exceeded {timeout_minutes} minute timeout"
        }
    except Exception as e:
        return {
            "test": test_file,
            "server": server_type,
            "status": "error",
            "error": str(e)
        }


def main():
    print("=" * 70)
    print(f"PR #3491 Parallel Test Execution")
    print("=" * 70)
    print(f"GCP Preview: {GCP_MCP_URL}")
    print(f"Evidence Base: {EVIDENCE_BASE}")
    print()
    
    # Create evidence directories
    gcp_evidence = EVIDENCE_BASE / "gcp_preview"
    local_evidence = EVIDENCE_BASE / "local_server"
    gcp_evidence.mkdir(parents=True, exist_ok=True)
    local_evidence.mkdir(parents=True, exist_ok=True)
    
    # Start local server
    print("🚀 Starting local server...")
    local_port = pick_free_port()
    local_server: Optional[LocalServer] = None
    
    try:
        env_overrides = {
            "ENABLE_SEMANTIC_ROUTING": "true",
            "WORLDAI_DEV_MODE": "true",
        }
        local_server = start_local_mcp_server(local_port, env_overrides=env_overrides)
        local_mcp_url = f"{local_server.base_url}/mcp"
        
        print(f"✅ Local server started: {local_mcp_url}")
        print(f"   PID: {local_server.pid}")
        print(f"   Log: {local_server.log_path}")
        
        # Wait for server to be ready
        print("⏳ Waiting for server to be ready...")
        time.sleep(5)
        
        # Test server health
        import requests
        try:
            health_url = local_server.base_url.replace("/mcp", "/health")
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                print("✅ Local server is healthy")
            else:
                print(f"⚠️ Local server health check returned {response.status_code}")
        except Exception as e:
            print(f"⚠️ Could not verify local server health: {e}")
        
        print()
        print("=" * 70)
        print("Running Tests in Parallel")
        print("=" * 70)
        print()
        
        # Prepare test tasks
        tasks = []
        for test_file in TESTS:
            # GCP preview task
            tasks.append((test_file, GCP_MCP_URL, "GCP Preview", gcp_evidence))
            # Local server task
            tasks.append((test_file, local_mcp_url, "Local Server", local_evidence))
        
        # Run tests in parallel
        results = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(run_test, test_file, server_url, server_type, evidence_dir): 
                (test_file, server_type)
                for test_file, server_url, server_type, evidence_dir in tasks
            }
            
            for future in as_completed(futures):
                test_file, server_type = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    status_emoji = "✅" if result["status"] == "passed" else "❌"
                    print(f"{status_emoji} {result['test']} ({result['server']}): {result['status']}")
                except Exception as e:
                    print(f"❌ {test_file} ({server_type}): Error - {e}")
                    results.append({
                        "test": test_file,
                        "server": server_type,
                        "status": "error",
                        "error": str(e)
                    })
        
        print()
        print("=" * 70)
        print("Test Results Summary")
        print("=" * 70)
        
        # Group results by server
        gcp_results = [r for r in results if r["server"] == "GCP Preview"]
        local_results = [r for r in results if r["server"] == "Local Server"]
        
        print("\nGCP Preview Results:")
        for result in gcp_results:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            print(f"  {status_emoji} {result['test']}: {result['status']}")
        
        print("\nLocal Server Results:")
        for result in local_results:
            status_emoji = "✅" if result["status"] == "passed" else "❌"
            print(f"  {status_emoji} {result['test']}: {result['status']}")
        
        # Create evidence summary
        summary_file = EVIDENCE_BASE / "test_summary.md"
        with open(summary_file, "w") as f:
            f.write(f"# PR #3491 Parallel Test Results\n\n")
            f.write(f"**Test Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Test Configuration\n\n")
            f.write(f"- GCP Preview URL: {GCP_MCP_URL}\n")
            f.write(f"- Local Server URL: {local_mcp_url}\n")
            f.write(f"- Local Server PID: {local_server.pid}\n\n")
            f.write(f"## Results\n\n")
            f.write(f"### GCP Preview\n\n")
            for result in gcp_results:
                f.write(f"- **{result['test']}**: {result['status']}\n")
            f.write(f"\n### Local Server\n\n")
            for result in local_results:
                f.write(f"- **{result['test']}**: {result['status']}\n")
            f.write(f"\n## Evidence Locations\n\n")
            f.write(f"- GCP Preview: {gcp_evidence}\n")
            f.write(f"- Local Server: {local_evidence}\n")
        
        print(f"\n📦 Evidence summary saved to: {summary_file}")
        print(f"📁 Evidence bundles:")
        print(f"   - GCP Preview: {gcp_evidence}")
        print(f"   - Local Server: {local_evidence}")
        
    finally:
        # Cleanup local server
        if local_server:
            print("\n🛑 Stopping local server...")
            local_server.stop()
            print("✅ Local server stopped")


if __name__ == "__main__":
    try:
        main()
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
