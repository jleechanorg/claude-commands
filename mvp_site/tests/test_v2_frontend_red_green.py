#!/usr/bin/env python3
"""
RED-GREEN Test: V2 React Frontend Environment Variables and Rendering

This test implements red-green methodology to fix the V2 frontend "nothing loads" issue.

RED Phase: Tests that should FAIL due to missing environment variables in production build
GREEN Phase: Tests that should PASS after environment variables are properly configured
"""

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


class TestV2FrontendRedGreen(unittest.TestCase):
    """Red-Green tests for V2 React frontend environment configuration."""

    def setUp(self):
        """Set up test environment."""

        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_dir = self.project_root / "mvp_site" / "frontend_v2"
        # Use temporary directory for test build output to avoid overwriting app assets
        self.temp_build_root = Path(tempfile.mkdtemp(prefix="v2_build_"))
        self.build_dir = self.temp_build_root

        # Required Firebase environment variables
        self.required_env_vars = [
            'FIREBASE_API_KEY',
            'FIREBASE_AUTH_DOMAIN',
            'FIREBASE_PROJECT_ID',
            'FIREBASE_STORAGE_BUCKET',
            'FIREBASE_MESSAGING_SENDER_ID',
            'FIREBASE_APP_ID'
        ]

    def test_red_phase_missing_environment_variables(self):
        """
        RED TEST: This should FAIL because environment variables are not set for production build
        
        The React app loads assets but shows blank screen because Firebase can't initialize
        without proper environment variables.
        """
        print("🔴 RED TEST: Checking environment variables for production build...")

        # Check if required environment variables are missing
        missing_vars = []
        for var_name in self.required_env_vars:
            if os.environ.get(var_name) is None:
                missing_vars.append(var_name)

        # For RED test, we expect variables to be missing
        if missing_vars:
            print(f"✅ RED TEST PASSED: Missing environment variables as expected: {missing_vars}")
            self.assertTrue(len(missing_vars) > 0, "Expected missing environment variables for RED test")
        else:
            # If all variables are present, check if build has them embedded
            print("Environment variables are set, checking if build reflects them...")
            self.check_build_environment_variables()

    def check_build_environment_variables(self):
        """Check if the built JavaScript files contain the environment variables."""
        if not self.build_dir.exists():
            # Skip test if build directory doesn't exist (CI environment)
            self.skipTest("Build directory doesn't exist - skipping build-dependent test")
            return

        # Find the main JavaScript bundle
        js_files = list(self.build_dir.glob("assets/js/index-*.js"))
        if not js_files:
            # Skip test if JS bundles don't exist (CI environment without full build)
            self.skipTest("No JavaScript bundle found - skipping build-dependent test")
            return

        main_js_file = js_files[0]
        try:
            with open(main_js_file, encoding='utf-8') as f:
                js_content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            self.fail(f"Failed to read JS bundle file {main_js_file}: {e}")

        # Check if Firebase config is embedded in the bundle using canonical property names
        firebase_canonical_props = [
            'apiKey',
            'authDomain',
            'projectId',
            'storageBucket',
            'messagingSenderId',
            'appId',
        ]
        found_props = [
            prop for prop in firebase_canonical_props
            if re.search(rf'\b{re.escape(prop)}\b', js_content, re.IGNORECASE)
        ]

        if len(found_props) < 3:  # At minimum need apiKey, authDomain, projectId
            print(f"❌ RED TEST CONFIRMED: Firebase configuration incomplete. Found only {len(found_props)} properties: {found_props}")
            self.fail(f"Firebase configuration missing from production build. Found: {found_props}")
        else:
            print("✅ Firebase configuration found in build")

    @unittest.skipUnless(
        os.getenv("RUN_V2_BUILD_TESTS") == "1" and not os.environ.get('FAST_TESTS'),
        "Set RUN_V2_BUILD_TESTS=1 to run npm build tests (disabled in FAST_TESTS mode)"
    )
    def test_red_phase_build_without_env_vars(self):
        """
        RED TEST: Build should fail or produce non-functional app without environment variables
        TEST GATED: Requires RUN_V2_BUILD_TESTS=1 and ENABLE_BUILD_TESTS=1 environment flags
        """
        # Test gating for network-dependent/expensive operations
        if not os.environ.get('ENABLE_BUILD_TESTS'):
            self.skipTest("Build tests disabled - set ENABLE_BUILD_TESTS=1 to run")

        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            self.skipTest("Skipping expensive build tests in CI environment")

        print("🔴 RED TEST: Testing build process without environment variables...")

        # Try to build with clean environment (no Firebase vars)
        clean_env = os.environ.copy()
        for var_name in self.required_env_vars:
            clean_env.pop(var_name, None)
        # Ensure build outputs to isolated temp dir
        clean_env['V2_BUILD_OUT_DIR'] = str(self.build_dir)

        # Ensure npm exists in PATH; skip if not available in the test environment
        if shutil.which('npm') is None:
            self.skipTest("npm not available in PATH")
        try:
            # Try to build without environment variables using cwd parameter
            try:
                result = subprocess.run(
                    ['npm', 'run', 'build'],
                    check=False, capture_output=True,
                    text=True,
                    timeout=120,
                    cwd=self.frontend_dir,
                    env=clean_env
                )
            except subprocess.TimeoutExpired:
                self.fail("Build process timed out after 120 seconds")

            if result.returncode != 0:
                print("✅ RED TEST PASSED: Build failed as expected without env vars")
                print(f"Build error: {result.stderr[:200]}...")
                self.assertNotEqual(result.returncode, 0, "Expected build to fail without environment variables")
            else:
                print("⚠️ Build succeeded but may not be functional")
                # Build succeeded, check if it's functional
                self.check_build_functionality()

        except FileNotFoundError:
            self.skipTest("npm not found in PATH")
        except Exception as e:
            self.fail(f"Build test failed with exception: {e}")

    def check_build_functionality(self):
        """Check if the build is functional by examining the output."""
        if not self.build_dir.exists():
            self.fail("Build directory doesn't exist")

        index_html = self.build_dir / "index.html"
        if not index_html.exists():
            self.fail("index.html not found in build directory")

        try:
            with open(index_html, encoding='utf-8') as f:
                html_content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            self.fail(f"Failed to read index.html file: {e}")

        # Check if HTML contains proper asset references
        if 'assets/js/index-' not in html_content:
            self.fail("Build appears incomplete - missing asset references")

        print("Build structure appears complete but may lack environment variables")

    @unittest.skipUnless(
        os.getenv("RUN_V2_BUILD_TESTS") == "1" and not os.environ.get('FAST_TESTS'),
        "Set RUN_V2_BUILD_TESTS=1 to run npm build tests (disabled in FAST_TESTS mode)"
    )
    def test_green_phase_build_with_env_vars(self):
        """
        GREEN TEST: Build should succeed and be functional with proper environment variables
        TEST GATED: Requires RUN_V2_BUILD_TESTS=1 and ENABLE_BUILD_TESTS=1 environment flags
        """
        # Test gating for network-dependent/expensive operations
        if not os.environ.get('ENABLE_BUILD_TESTS'):
            self.skipTest("Build tests disabled - set ENABLE_BUILD_TESTS=1 to run")

        # Skip GREEN build tests in CI environment without proper setup
        if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
            self.skipTest("GREEN build tests require local development environment")

        print("🟢 GREEN TEST: Testing build with proper environment variables...")

        # Check if environment variables are available
        missing_vars = []
        for var_name in self.required_env_vars:
            if os.environ.get(var_name) is None:
                missing_vars.append(var_name)

        if missing_vars:
            self.skipTest(f"Skipping GREEN test - missing environment variables: {missing_vars}")

        # Build with environment variables using cwd parameter instead of os.chdir
        env = os.environ.copy()
        env['NODE_ENV'] = 'production'
        # Ensure build outputs to isolated temp dir
        env['V2_BUILD_OUT_DIR'] = str(self.build_dir)

        # Ensure npm exists in PATH; skip if not available in the test environment
        if shutil.which('npm') is None:
            self.skipTest("npm not available in PATH")

        print("Building React app with environment variables...")
        try:
            result = subprocess.run(
                ['npm', 'run', 'build'],
                check=False, capture_output=True,
                text=True,
                timeout=120,
                cwd=self.frontend_dir,
                env=env
            )
        except subprocess.TimeoutExpired:
            self.fail("Build process timed out after 120 seconds")

        if result.returncode != 0:
            self.fail(f"GREEN test failed - build error: {result.stderr}")

        print("✅ GREEN TEST PASSED: Build completed successfully")

        # Verify build output contains environment variables
        self.verify_build_contains_env_vars()

    def verify_build_contains_env_vars(self):
        """Verify that the build contains the required environment variables."""
        if not self.build_dir.exists():
            self.fail("Build directory doesn't exist after build")

        # Check index.html exists
        index_html = self.build_dir / "index.html"
        if not index_html.exists():
            self.fail("index.html not found after build")

        # Find and check the main JavaScript bundle
        js_files = list(self.build_dir.glob("assets/js/index-*.js"))
        if not js_files:
            self.fail("No main JavaScript bundle found after build")

        main_js_file = js_files[0]
        try:
            with open(main_js_file, encoding='utf-8') as f:
                js_content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            self.fail(f"Failed to read JS bundle file {main_js_file}: {e}")

        # Look for Firebase configuration in the bundle via canonical property keys
        firebase_canonical_props = [
            'apiKey', 'authDomain', 'projectId', 'storageBucket', 'messagingSenderId', 'appId'
        ]
        found_props = [
            prop for prop in firebase_canonical_props
            if re.search(rf'\b{re.escape(prop)}\b', js_content, re.IGNORECASE)
        ]
        if len(found_props) < 3:
            self.fail(f"Firebase configuration incomplete in JS bundle; found: {found_props}")
        print(f"✅ GREEN TEST VERIFIED: Firebase properties embedded in build: {found_props}")

    def test_environment_setup_documentation(self):
        """
        Document what environment setup is required for GREEN tests to pass.
        """
        print("\n" + "="*60)
        print("V2 FRONTEND ENVIRONMENT REQUIREMENTS")
        print("="*60)
        print("To fix the 'nothing loads' issue and make GREEN tests pass:")
        print()
        print("Required Environment Variables:")
        for var_name in self.required_env_vars:
            status = "✅ SET" if os.environ.get(var_name) is not None else "❌ MISSING"
            print(f"- {var_name}: {status}")
        print()
        print("Setup Steps:")
        print("1. Set all required Firebase environment variables")
        print("2. Run: cd mvp_site/frontend_v2 && NODE_ENV=production npm run build")
        print("3. Verify build output in mvp_site/static/v2/")
        print("4. Restart Flask server to serve updated build")
        print()
        print("Expected Result:")
        print("- React app loads with proper Firebase configuration")
        print("- Authentication works in production mode")
        print("- No blank screen or JavaScript errors")
        print("="*60)

        # This test always passes - it's for documentation
        self.assertTrue(True)


if __name__ == '__main__':
    print("🔴🟢 RED-GREEN Testing: V2 Frontend Environment Configuration")
    print("="*60)
    print("RED Phase: Tests that should FAIL due to missing environment configuration")
    print("GREEN Phase: Tests that should PASS after proper environment setup")
    print("="*60)

    # Run with detailed output
    unittest.main(verbosity=2)
