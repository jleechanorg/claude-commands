#!/usr/bin/env python3
"""
Rigorous parallel concurrency test with proper validation.

Addresses all methodological concerns:
1. Response body validation (not just status codes)
2. Per-request start/end timestamps with true overlap calculation
3. Warmup phase before measurement
4. Minimum success threshold for PASS (95%)
5. Only valid campaign IDs (auto-fetched)
6. Separate success vs error analysis
"""

import argparse
import concurrent.futures
import contextlib
import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import requests

DEFAULT_URL = "https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app"
LOCAL_URL = "http://localhost:8080"

# Minimum success rate to consider test valid (100% = zero errors allowed)
MIN_SUCCESS_RATE = 1.0


def is_token_expired(token_file: str, buffer_minutes: int = 5) -> bool:
    """Check if token is expired or will expire within buffer_minutes."""
    if not os.path.exists(token_file):
        return True
    try:
        with open(token_file) as f:
            data = json.load(f)
        expires_at = data.get("expiresAt")
        if not expires_at:
            return True
        # Parse ISO format expiry time
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        now = datetime.now(UTC)
        # Consider expired if within buffer_minutes of expiry
        return now >= (expiry - timedelta(minutes=buffer_minutes))
    except Exception:
        return True


def refresh_token() -> bool:
    """Refresh the auth token using auth-cli.mjs."""
    # Find the auth-cli.mjs script relative to this script
    script_dir = Path(__file__).parent.parent / ".claude" / "scripts"
    auth_cli = script_dir / "auth-cli.mjs"

    if not auth_cli.exists():
        print("   ⚠️  auth-cli.mjs not found, cannot refresh token")
        return False

    try:
        # S603/S607: Trusted internal call to our own auth script
        result = subprocess.run(  # noqa: S603
            ["node", str(auth_cli), "refresh"],  # noqa: S607
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            print("   ✅ Token refreshed automatically")
            return True
        print(f"   ⚠️  Token refresh failed: {result.stderr}")
        return False
    except Exception as e:
        print(f"   ⚠️  Token refresh error: {e}")
        return False


def load_token(token_file: str, auto_refresh: bool = True) -> str | None:
    """Load Firebase ID token from auth-cli token file.

    If auto_refresh is True (default), will automatically refresh
    the token if it's expired or about to expire.
    """
    if not os.path.exists(token_file):
        return None

    # Check if token needs refresh
    if auto_refresh and is_token_expired(token_file):
        print("   🔄 Token expired or expiring soon, refreshing...")
        if not refresh_token():
            print("   ⚠️  Could not refresh token, trying with existing")

    try:
        with open(token_file) as f:
            data = json.load(f)
        return data.get("idToken")
    except Exception:
        return None


def get_valid_campaign_info(base_url: str, token: str) -> tuple[str, str] | None:
    """Fetch a valid campaign ID and title owned by the authenticated user."""
    try:
        resp = requests.get(
            f"{base_url}/api/campaigns",
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        if resp.status_code == 200:
            campaigns = resp.json()
            if isinstance(campaigns, list) and len(campaigns) > 0:
                campaign = campaigns[0]
                return campaign["id"], campaign.get("title", "")
        return None
    except Exception:
        return None


def make_request_with_validation(
    base_url: str,
    endpoint: str,
    token: str,
    request_id: int,
    expected_title: str | None = None,
) -> dict:
    """
    Make authenticated request with full response validation.

    Returns detailed timing and validation info.
    Validates title match if expected_title is provided.
    """
    url = f"{base_url}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}

    # Record absolute start time for overlap calculation
    abs_start = time.time()
    start = time.perf_counter()

    try:
        response = requests.get(url, headers=headers, timeout=60)
        end = time.perf_counter()
        abs_end = time.time()

        # Validate response body
        body_valid = False
        body_size = 0
        title_match = False
        content_hash = ""
        actual_title = ""

        if response.status_code == 200:
            try:
                body = response.json()
                body_size = len(response.content)
                # Compute content hash for consistency validation
                import hashlib

                content_hash = hashlib.md5(  # noqa: S324 - MD5 for fingerprint only
                    response.content
                ).hexdigest()[:8]
                # API returns {campaign: {...}, game_state: {...}, story: {...}}
                body_valid = (
                    isinstance(body, dict)
                    and "campaign" in body
                    and isinstance(body.get("campaign"), dict)
                )
                # Validate campaign title matches expected
                campaign = body.get("campaign", {})
                actual_title = campaign.get("title", "")
                if expected_title:
                    title_match = actual_title == expected_title
                else:
                    # No expected title provided, just check title exists
                    title_match = bool(actual_title)
            except Exception:  # noqa: S110 - JSON parse failure means invalid body
                body_valid = False

        return {
            "request_id": request_id,
            "status_code": response.status_code,
            "duration_ms": (end - start) * 1000,
            "abs_start": abs_start,
            "abs_end": abs_end,
            "start_perf": start,
            "end_perf": end,
            "success": response.status_code == 200 and body_valid and title_match,
            "body_valid": body_valid,
            "body_size": body_size,
            "title_match": title_match,
            "actual_title": actual_title,
            "content_hash": content_hash,
            "error": None,
        }
    except Exception as e:
        end = time.perf_counter()
        abs_end = time.time()
        return {
            "request_id": request_id,
            "status_code": 0,
            "duration_ms": (end - start) * 1000,
            "abs_start": abs_start,
            "abs_end": abs_end,
            "start_perf": start,
            "end_perf": end,
            "success": False,
            "body_valid": False,
            "body_size": 0,
            "title_match": False,
            "actual_title": "",
            "content_hash": "",
            "error": str(e),
        }


def calculate_overlap_percentage(results: list) -> float:
    """
    Calculate true overlap percentage from per-request timestamps.

    Overlap = (sum of individual durations) / (wall clock time * num_requests)
    If overlap > 1.0, requests were truly concurrent.

    Also calculates what % of time had multiple requests in flight.
    """
    if not results:
        return 0.0

    # Get absolute time bounds
    min_start = min(r["abs_start"] for r in results)
    max_end = max(r["abs_end"] for r in results)
    wall_time = max_end - min_start

    if wall_time <= 0:
        return 0.0

    # Create timeline of concurrent request counts
    events = []
    for r in results:
        events.append((r["abs_start"], 1))  # request starts
        events.append((r["abs_end"], -1))  # request ends

    events.sort(key=lambda x: (x[0], -x[1]))  # sort by time, starts before ends

    concurrent_count = 0
    last_time = min_start
    overlap_time = 0.0  # time with >1 concurrent request

    for event_time, delta in events:
        if concurrent_count > 1:
            overlap_time += event_time - last_time
        concurrent_count += delta
        last_time = event_time

    # Overlap percentage = % of wall time with multiple requests in flight
    return (overlap_time / wall_time) * 100 if wall_time > 0 else 0


def calculate_max_concurrent(results: list) -> int:
    """Calculate maximum number of requests in flight simultaneously."""
    if not results:
        return 0

    events = []
    for r in results:
        events.append((r["abs_start"], 1))
        events.append((r["abs_end"], -1))

    events.sort(key=lambda x: (x[0], -x[1]))

    concurrent = 0
    max_concurrent = 0
    for _, delta in events:
        concurrent += delta
        max_concurrent = max(max_concurrent, concurrent)

    return max_concurrent


def run_warmup(base_url: str, endpoint: str, token: str, num_warmup: int = 5) -> None:
    """Run warmup requests to prime caches and connections."""
    print(f"🔥 Running {num_warmup} warmup requests...")
    for _ in range(num_warmup):
        with contextlib.suppress(Exception):
            requests.get(
                f"{base_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
    print("   Warmup complete")


def run_rigorous_test(  # noqa: PLR0912,PLR0915 - complexity needed for detailed reporting
    base_url: str,
    campaign_id: str,
    expected_title: str,
    token: str,
    num_concurrent: int,
    skip_warmup: bool = False,
) -> dict:
    """Run rigorous concurrent request test with full validation."""

    endpoint = f"/api/campaigns/{campaign_id}"

    print(f"\n{'=' * 60}")
    print("🔬 RIGOROUS PARALLEL CONCURRENCY TEST")
    print(f"{'=' * 60}")
    print(f"Target: {base_url}{endpoint}")
    print(f"Expected title: {expected_title}")
    print(f"Concurrent requests: {num_concurrent}")
    print("Validation: Response body + title match + content hash")
    print(f"Min success rate for PASS: {MIN_SUCCESS_RATE * 100:.0f}%")
    print(f"Started at: {datetime.now(tz=UTC).isoformat()}")

    # Warmup phase
    if not skip_warmup:
        print()
        run_warmup(base_url, endpoint, token)

    # Single baseline (post-warmup)
    print("\n📊 Measuring warmed-up baseline...")
    baseline = make_request_with_validation(
        base_url, endpoint, token, -1, expected_title
    )
    print(
        f"   Baseline: {baseline['duration_ms']:.1f}ms (status: {baseline['status_code']}, body_valid: {baseline['body_valid']}, title_match: {baseline['title_match']})"
    )

    if not baseline["success"]:
        print("   ⚠️  Baseline request failed - test may be invalid")

    # Concurrent test
    print(f"\n📊 Making {num_concurrent} concurrent requests...")

    perf_start = time.perf_counter()

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = [
            executor.submit(
                make_request_with_validation,
                base_url,
                endpoint,
                token,
                i,
                expected_title,
            )
            for i in range(num_concurrent)
        ]
        results = [f.result() for f in futures]

    perf_end = time.perf_counter()

    wall_time_ms = (perf_end - perf_start) * 1000

    # Analyze results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    success_rate = len(successful) / num_concurrent if num_concurrent > 0 else 0

    # Timing analysis (successful requests only for accuracy)
    if successful:
        durations = [r["duration_ms"] for r in successful]
        avg_duration = sum(durations) / len(durations)
        min_duration = min(durations)
        max_duration = max(durations)
    else:
        durations = [r["duration_ms"] for r in results]
        avg_duration = sum(durations) / len(durations) if durations else 0
        min_duration = min(durations) if durations else 0
        max_duration = max(durations) if durations else 0

    # Overlap analysis
    overlap_pct = calculate_overlap_percentage(results)
    max_concurrent = calculate_max_concurrent(results)

    # Parallelism ratio
    expected_parallel_ms = max_duration
    parallelism_ratio = (
        wall_time_ms / expected_parallel_ms if expected_parallel_ms > 0 else 0
    )

    # Print results
    print(f"\n{'=' * 60}")
    print("📈 RESULTS")
    print(f"{'=' * 60}")

    print("\n🎯 Success Metrics:")
    print(
        f"   Successful requests: {len(successful)}/{num_concurrent} ({success_rate * 100:.1f}%)"
    )
    print(f"   Failed requests: {len(failed)}")
    print(f"   Body validated: {sum(1 for r in results if r['body_valid'])}")
    print(f"   Title matched: {sum(1 for r in results if r['title_match'])}")

    # Content hash consistency check
    hashes = [r["content_hash"] for r in results if r["content_hash"]]
    unique_hashes = set(hashes)
    print(f"   Content hashes: {len(unique_hashes)} unique (1 = all identical)")
    if unique_hashes:
        print(f"   Hash sample: {list(unique_hashes)[:3]}")

    print("\n⏱️  Timing (successful requests only):")
    print(f"   Min: {min_duration:.1f}ms")
    print(f"   Avg: {avg_duration:.1f}ms")
    print(f"   Max: {max_duration:.1f}ms")
    print(f"   Wall clock: {wall_time_ms:.1f}ms")

    print("\n🔀 Parallelism Evidence:")
    print(f"   Max concurrent in-flight: {max_concurrent}")
    print(f"   Overlap percentage: {overlap_pct:.1f}%")
    print(f"   Parallelism ratio: {parallelism_ratio:.2f}x (1.0 = perfect)")

    # Verdict - requires BOTH success rate AND parallelism
    print(f"\n{'=' * 60}")
    print("🏆 VERDICT")
    print(f"{'=' * 60}")

    passed = True
    reasons = []

    if success_rate < MIN_SUCCESS_RATE:
        passed = False
        reasons.append(
            f"Success rate {success_rate * 100:.1f}% < {MIN_SUCCESS_RATE * 100:.0f}% threshold"
        )

    if parallelism_ratio > 1.5:
        passed = False
        reasons.append(f"Parallelism ratio {parallelism_ratio:.2f}x > 1.5x threshold")

    if overlap_pct < 50 and num_concurrent > 2:
        passed = False
        reasons.append(f"Overlap {overlap_pct:.1f}% < 50% threshold")

    if max_concurrent < num_concurrent * 0.5:
        passed = False
        reasons.append(
            f"Max concurrent {max_concurrent} < 50% of requested {num_concurrent}"
        )

    if passed:
        print("✅ PASS: Parallel execution verified")
        print(f"   - {success_rate * 100:.1f}% success rate")
        print(f"   - {overlap_pct:.1f}% time with concurrent requests")
        print(f"   - {max_concurrent} requests in-flight simultaneously")
        verdict = "PASS"
    else:
        print("❌ FAIL: Parallel execution NOT verified")
        for reason in reasons:
            print(f"   - {reason}")
        verdict = "FAIL"

    # Error breakdown
    if failed:
        print("\n⚠️  Error Breakdown:")
        by_status = {}
        for r in failed:
            status = r["status_code"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(r)

        for status, reqs in sorted(by_status.items()):
            print(f"   Status {status}: {len(reqs)} requests")
            if reqs[0].get("error"):
                print(f"      Error: {reqs[0]['error'][:80]}")

    print()

    return {
        "verdict": verdict,
        "success_rate": success_rate,
        "successful": len(successful),
        "failed": len(failed),
        "wall_time_ms": wall_time_ms,
        "parallelism_ratio": parallelism_ratio,
        "overlap_pct": overlap_pct,
        "max_concurrent": max_concurrent,
        "avg_duration_ms": avg_duration,
        "baseline_ms": baseline["duration_ms"],
        "baseline_success": baseline["success"],
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Rigorous parallel concurrency test with validation"
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Server URL")
    parser.add_argument("--local", action="store_true", help="Use localhost:8080")
    parser.add_argument(
        "--concurrent", "-n", type=int, default=100, help="Concurrent requests"
    )
    parser.add_argument(
        "--token-file",
        default=os.path.expanduser("~/.worldarchitect-ai/auth-token.json"),
    )
    parser.add_argument(
        "--campaign-id", help="Specific campaign ID (auto-fetched if omitted)"
    )
    parser.add_argument("--skip-warmup", action="store_true", help="Skip warmup phase")
    parser.add_argument("--output", "-o", help="Output JSON file for results")

    args = parser.parse_args()

    base_url = LOCAL_URL if args.local else args.url

    # Load token
    token = load_token(args.token_file)
    if not token:
        # In CI environment (GitHub Actions), skip gracefully instead of failing
        is_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
        if is_ci:
            print(f"⏭️  Skipping test - no auth token available in CI environment")
            print(f"   Token file: {args.token_file}")
            print("   This test requires local authentication")
            sys.exit(0)  # Exit with success to not block CI
        print(f"❌ Could not load token from {args.token_file}")
        print("   Run: node .claude/scripts/auth-worldai.mjs")
        sys.exit(1)

    print(f"✅ Token loaded from {args.token_file}")

    # Health check
    try:
        resp = requests.get(f"{base_url}/health", timeout=10)
        if resp.status_code != 200:
            print(f"❌ Health check failed: {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot reach {base_url}: {e}")
        sys.exit(1)

    print(f"✅ Server healthy at {base_url}")

    # Get valid campaign ID and title
    campaign_id = args.campaign_id
    expected_title = ""
    if not campaign_id:
        print("🔍 Fetching valid campaign info...")
        campaign_info = get_valid_campaign_info(base_url, token)
        if not campaign_info:
            print("❌ No campaigns found for authenticated user")
            sys.exit(1)
        campaign_id, expected_title = campaign_info
        print(f"   Using campaign: {campaign_id}")
        print(f"   Expected title: {expected_title}")
    else:
        # If campaign_id provided, fetch title for validation
        campaign_info = get_valid_campaign_info(base_url, token)
        if campaign_info:
            expected_title = campaign_info[1] if campaign_info[0] == campaign_id else ""

    # Run test
    results = run_rigorous_test(
        base_url=base_url,
        campaign_id=campaign_id,
        expected_title=expected_title,
        token=token,
        num_concurrent=args.concurrent,
        skip_warmup=args.skip_warmup,
    )

    # Save output
    if args.output:
        # Remove raw results for file output (too large)
        output_data = {k: v for k, v in results.items() if k != "results"}
        output_data["timestamp"] = datetime.now(tz=UTC).isoformat()
        output_data["config"] = {
            "url": base_url,
            "concurrent": args.concurrent,
            "campaign_id": campaign_id,
            "skip_warmup": args.skip_warmup,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"📄 Results saved to {args.output}")

    sys.exit(0 if results["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
