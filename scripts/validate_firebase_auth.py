#!/usr/bin/env python3
"""
Firebase Authentication Configuration Validator for Milestone 2.
Focuses on identifying and fixing Firebase auth configuration issues.
"""

import os
import sys
import requests
import json
import time
from typing import Dict, Any, List

class FirebaseAuthValidator:
    """Validate Firebase authentication configuration."""

    def __init__(self):
        self.frontend_url = "http://localhost:3002"
        self.results = []

    def log_result(self, test_name: str, success: bool, message: str, details: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.time()
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")

    def test_firebase_config_files(self) -> bool:
        """Test Firebase configuration files exist and are valid."""
        env_file = "/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/frontend_v2/.env"
        service_account = "/home/jleechan/projects/worldarchitect.ai/serviceAccountKey.json"

        # Check .env file
        if not os.path.exists(env_file):
            self.log_result("Firebase Config Files", False, ".env file missing")
            return False

        # Check service account
        if not os.path.exists(service_account):
            self.log_result("Firebase Config Files", False, "serviceAccountKey.json missing")
            return False

        self.log_result("Firebase Config Files", True, "Both .env and serviceAccountKey.json exist")
        return True

    def test_firebase_env_variables(self) -> bool:
        """Test Firebase environment variables are properly configured."""
        env_file = "/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/frontend_v2/.env"

        try:
            with open(env_file, 'r') as f:
                content = f.read()

            required_vars = [
                'VITE_FIREBASE_API_KEY',
                'VITE_FIREBASE_AUTH_DOMAIN',
                'VITE_FIREBASE_PROJECT_ID',
                'VITE_FIREBASE_STORAGE_BUCKET',
                'VITE_FIREBASE_MESSAGING_SENDER_ID',
                'VITE_FIREBASE_APP_ID'
            ]

            config_values = {}
            for line in content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    config_values[key.strip()] = value.strip()

            missing_vars = []
            invalid_vars = []

            for var in required_vars:
                if var not in config_values:
                    missing_vars.append(f"{var} (not found)")
                elif not config_values[var] or config_values[var].startswith('your-'):
                    invalid_vars.append(f"{var} (placeholder value)")

            # Check API key format specifically
            api_key = config_values.get('VITE_FIREBASE_API_KEY', '')
            if api_key and not api_key.startswith('AIza'):
                invalid_vars.append('VITE_FIREBASE_API_KEY (invalid format - should start with AIza)')
            elif api_key and len(api_key) != 39:
                invalid_vars.append(f'VITE_FIREBASE_API_KEY (invalid length - should be 39 chars, got {len(api_key)})')

            if missing_vars or invalid_vars:
                issues = missing_vars + invalid_vars
                self.log_result("Firebase Environment Variables", False,
                              f"Configuration issues found: {', '.join(issues)}")
                return False

            self.log_result("Firebase Environment Variables", True, "All required variables present and valid")
            return True

        except Exception as e:
            self.log_result("Firebase Environment Variables", False, "Error reading .env file", str(e))
            return False

    def test_project_id_consistency(self) -> bool:
        """Test project ID consistency between frontend and backend."""
        env_file = "/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/frontend_v2/.env"
        service_account = "/home/jleechan/projects/worldarchitect.ai/serviceAccountKey.json"

        try:
            # Get project ID from .env
            with open(env_file, 'r') as f:
                env_content = f.read()

            env_project_id = None
            for line in env_content.split('\n'):
                if line.strip().startswith('VITE_FIREBASE_PROJECT_ID='):
                    env_project_id = line.split('=', 1)[1].strip()
                    break

            # Get project ID from service account
            with open(service_account, 'r') as f:
                service_data = json.load(f)
                service_project_id = service_data.get('project_id', '')

            if not env_project_id:
                self.log_result("Project ID Consistency", False, "Project ID not found in .env file")
                return False

            if not service_project_id:
                self.log_result("Project ID Consistency", False, "Project ID not found in service account")
                return False

            if env_project_id != service_project_id:
                self.log_result("Project ID Consistency", False,
                              f"Project ID mismatch: .env='{env_project_id}', service='{service_project_id}'")
                return False

            self.log_result("Project ID Consistency", True, f"Project IDs match: {env_project_id}")
            return True

        except Exception as e:
            self.log_result("Project ID Consistency", False, "Error checking project ID consistency", str(e))
            return False

    def test_firebase_api_key_validity(self) -> bool:
        """Test Firebase API key validity by making a request to Firebase REST API."""
        env_file = "/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/frontend_v2/.env"

        try:
            with open(env_file, 'r') as f:
                content = f.read()

            # Extract API key
            api_key = None
            for line in content.split('\n'):
                if line.strip().startswith('VITE_FIREBASE_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break

            if not api_key:
                self.log_result("Firebase API Key Validity", False, "API key not found in .env file")
                return False

            # Test API key with Firebase Identity Toolkit API
            # This endpoint should respond with specific errors that indicate API key validity
            test_url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
            test_payload = {"idToken": "invalid-token-for-testing"}

            response = requests.post(test_url, json=test_payload, timeout=10)

            # Analyze response to determine API key validity
            if response.status_code == 400:
                # 400 with INVALID_ID_TOKEN means API key works but token is invalid (expected)
                try:
                    error_data = response.json()
                    if "INVALID_ID_TOKEN" in str(error_data) or "error" in error_data:
                        self.log_result("Firebase API Key Validity", True, "API key is valid (Firebase accepted the request)")
                        return True
                except:
                    pass
                self.log_result("Firebase API Key Validity", True, "API key appears valid (400 response from Firebase)")
                return True
            elif response.status_code == 403:
                # 403 means API key is invalid or restricted
                try:
                    error_data = response.json()
                    if "API key not valid" in str(error_data):
                        self.log_result("Firebase API Key Validity", False, "API key is invalid", str(error_data))
                        return False
                    elif "restricted" in str(error_data).lower():
                        self.log_result("Firebase API Key Validity", False, "API key is restricted", str(error_data))
                        return False
                except:
                    pass
                self.log_result("Firebase API Key Validity", False, "API key validation failed (403 Forbidden)")
                return False
            else:
                self.log_result("Firebase API Key Validity", False,
                              f"Unexpected response status: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            self.log_result("Firebase API Key Validity", False, "Network error during API key validation", str(e))
            return False
        except Exception as e:
            self.log_result("Firebase API Key Validity", False, "Error validating API key", str(e))
            return False

    def test_frontend_firebase_config(self) -> bool:
        """Test frontend Firebase configuration file syntax."""
        firebase_config_file = "/home/jleechan/projects/worldarchitect.ai/worktree_human/mvp_site/frontend_v2/src/lib/firebase.ts"

        if not os.path.exists(firebase_config_file):
            self.log_result("Frontend Firebase Config", False, "firebase.ts file missing")
            return False

        try:
            with open(firebase_config_file, 'r') as f:
                content = f.read()

            # Check for required imports and configurations
            required_patterns = [
                'import { initializeApp }',
                'import { getAuth',
                'GoogleAuthProvider',
                'import.meta.env.VITE_FIREBASE_API_KEY',
                'initializeApp(firebaseConfig)'
            ]

            missing_patterns = []
            for pattern in required_patterns:
                if pattern not in content:
                    missing_patterns.append(pattern)

            if missing_patterns:
                self.log_result("Frontend Firebase Config", False,
                              f"Missing required patterns: {', '.join(missing_patterns)}")
                return False

            # Check for proper error handling
            if 'Missing required Firebase environment variables' not in content:
                self.log_result("Frontend Firebase Config", False, "Missing environment variable validation")
                return False

            self.log_result("Frontend Firebase Config", True, "Firebase configuration file is properly structured")
            return True

        except Exception as e:
            self.log_result("Frontend Firebase Config", False, "Error reading firebase.ts file", str(e))
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Generate final validation report."""
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - passed_tests

        report = {
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.1f}%" if total_tests > 0 else "0%"
            },
            "results": self.results,
            "timestamp": time.time(),
            "focus": "Firebase Authentication Configuration Validation"
        }

        return report

    def run_validation(self) -> bool:
        """Run complete Firebase authentication validation."""
        print("🔥 Firebase Authentication Configuration Validator")
        print("=" * 60)

        # Run all tests
        tests = [
            self.test_firebase_config_files,
            self.test_firebase_env_variables,
            self.test_project_id_consistency,
            self.test_firebase_api_key_validity,
            self.test_frontend_firebase_config
        ]

        overall_success = True
        for test in tests:
            try:
                result = test()
                if not result:
                    overall_success = False
            except Exception as e:
                self.log_result(test.__name__, False, "Test execution failed", str(e))
                overall_success = False

        # Generate and display report
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("🔥 FIREBASE AUTH VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {report['summary']['total_tests']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']}")

        if overall_success:
            print("\n🎉 Firebase authentication configuration is VALID!")
            print("✅ Ready for Milestone 2 testing")
        else:
            print("\n⚠️  Firebase authentication configuration has ISSUES")
            print("🔧 Fixes needed before Milestone 2 testing:")
            for result in self.results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
                    if result['details']:
                        print(f"    Details: {result['details']}")

        # Save report to file
        report_file = "/tmp/firebase_auth_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n📄 Detailed report saved to: {report_file}")

        return overall_success


def main():
    """Run Firebase authentication validation."""
    validator = FirebaseAuthValidator()
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
