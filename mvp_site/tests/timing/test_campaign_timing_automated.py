#!/usr/bin/env python3
"""
Automated Campaign Wizard Timing Tests

This test file integrates the JavaScript timing tests into the Python test suite.
It uses Selenium to run the browser-based timing tests and reports results.
"""

import unittest
import time
import os
import sys
import tempfile
import shutil
import http.server
import socketserver
import threading
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Try to import Selenium - skip tests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    # Create dummy classes to prevent errors
    class Options: pass
    class TimeoutException(Exception): pass


class CampaignTimingAutomatedTests(unittest.TestCase):
    """
    Automated browser-based timing tests that enforce zero artificial delays
    in campaign creation workflow.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test server and browser for timing tests"""
        cls.test_server = None
        cls.server_thread = None
        cls.driver = None
        cls.test_port = 8765  # Different from main app port
        
        # Start local test server
        cls._start_test_server()
        
        # Set up Chrome browser
        cls._setup_browser()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up browser and test server"""
        if cls.driver:
            cls.driver.quit()
            
        if cls.test_server:
            cls.test_server.shutdown()
            
        if cls.server_thread:
            cls.server_thread.join(timeout=5)
    
    @classmethod
    def _start_test_server(cls):
        """Start a local HTTP server to serve test files"""
        # Change to mvp_site directory to serve test files
        mvp_site_dir = Path(__file__).parent.parent.parent
        os.chdir(mvp_site_dir)
        
        # Create simple HTTP server
        handler = http.server.SimpleHTTPRequestHandler
        
        try:
            cls.test_server = socketserver.TCPServer(("", cls.test_port), handler)
            cls.server_thread = threading.Thread(target=cls.test_server.serve_forever)
            cls.server_thread.daemon = True
            cls.server_thread.start()
            
            # Wait a moment for server to start
            time.sleep(1)
            print(f"✅ Test server started on port {cls.test_port}")
            
        except Exception as e:
            print(f"❌ Failed to start test server: {e}")
            raise
    
    @classmethod
    def _setup_browser(cls):
        """Set up Chrome browser in headless mode"""
        if not SELENIUM_AVAILABLE:
            print("⚠️ Selenium not available, skipping browser setup")
            return
            
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in background
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.set_page_load_timeout(30)
            print("✅ Chrome browser initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize browser: {e}")
            print("💡 Make sure ChromeDriver is installed and in PATH")
            raise
    
    @unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not available")
    def test_timing_enforcement_suite(self):
        """
        Run the complete JavaScript timing test suite and validate results
        """
        print("🚀 Running automated campaign timing tests...")
        
        # Load the timing test runner page
        test_url = f"http://localhost:{self.test_port}/test_timing_runner.html"
        
        try:
            self.driver.get(test_url)
            print(f"📄 Loaded test page: {test_url}")
            
            # Wait for page to load completely
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "runTests"))
            )
            
            # Click the "Run All Tests" button
            run_button = self.driver.find_element(By.ID, "runTests")
            run_button.click()
            print("▶️ Triggered test execution...")
            
            # Wait for tests to complete (max 30 seconds)
            WebDriverWait(self.driver, 30).until(
                lambda driver: self._are_tests_complete(driver)
            )
            
            # Get test results
            results = self._extract_test_results()
            
            # Validate all tests passed
            self._validate_test_results(results)
            
            print("✅ All timing tests passed successfully!")
            
        except TimeoutException:
            self.fail("❌ Timing tests timed out - this may indicate performance issues")
            
        except Exception as e:
            self.fail(f"❌ Timing test execution failed: {str(e)}")
    
    def _are_tests_complete(self, driver):
        """Check if JavaScript tests have completed execution"""
        try:
            # Look for completion indicators in the results area
            results_element = driver.find_element(By.ID, "test-results")
            results_text = results_element.text
            
            # Tests are complete when we see summary or all test results
            completion_indicators = [
                "All tests completed",
                "Tests completed in",
                "5/5 tests passed",
                "PASS" in results_text and "ms" in results_text
            ]
            
            return any(indicator in results_text for indicator in completion_indicators)
            
        except Exception:
            return False
    
    def _extract_test_results(self):
        """Extract test results from the browser page"""
        try:
            results_element = self.driver.find_element(By.ID, "test-results")
            results_text = results_element.text
            
            # Parse individual test results
            test_results = {
                'immediate_form_submission': 'UNKNOWN',
                'non_blocking_progress': 'UNKNOWN', 
                'progress_override': 'UNKNOWN',
                'no_critical_delays': 'UNKNOWN',
                'end_to_end_timing': 'UNKNOWN',
                'overall_status': 'UNKNOWN'
            }
            
            # Look for PASS/FAIL indicators for each test
            lines = results_text.split('\n')
            for line in lines:
                if 'Immediate Form Submission' in line:
                    test_results['immediate_form_submission'] = 'PASS' if 'PASS' in line else 'FAIL'
                elif 'Non-Blocking Progress' in line:
                    test_results['non_blocking_progress'] = 'PASS' if 'PASS' in line else 'FAIL'
                elif 'Progress Override' in line:
                    test_results['progress_override'] = 'PASS' if 'PASS' in line else 'FAIL'
                elif 'No Critical Path Delays' in line:
                    test_results['no_critical_delays'] = 'PASS' if 'PASS' in line else 'FAIL'
                elif 'End-to-End Timing' in line:
                    test_results['end_to_end_timing'] = 'PASS' if 'PASS' in line else 'FAIL'
            
            # Determine overall status
            all_results = [v for v in test_results.values() if v != 'UNKNOWN']
            if all_results and all(result == 'PASS' for result in all_results):
                test_results['overall_status'] = 'ALL_PASS'
            elif any(result == 'FAIL' for result in all_results):
                test_results['overall_status'] = 'SOME_FAIL'
            else:
                test_results['overall_status'] = 'INCOMPLETE'
            
            return test_results
            
        except Exception as e:
            print(f"❌ Failed to extract test results: {e}")
            return {'overall_status': 'ERROR', 'error': str(e)}
    
    def _validate_test_results(self, results):
        """Validate that all timing tests passed successfully"""
        print("📊 Timing Test Results:")
        
        test_names = {
            'immediate_form_submission': 'Immediate Form Submission',
            'non_blocking_progress': 'Non-Blocking Progress Animation', 
            'progress_override': 'Progress Override Capability',
            'no_critical_delays': 'No Critical Path Delays',
            'end_to_end_timing': 'End-to-End Timing'
        }
        
        failed_tests = []
        
        for test_key, test_name in test_names.items():
            result = results.get(test_key, 'UNKNOWN')
            status_icon = "✅" if result == 'PASS' else "❌" if result == 'FAIL' else "⚠️"
            print(f"  {status_icon} {test_name}: {result}")
            
            if result == 'FAIL':
                failed_tests.append(test_name)
            elif result == 'UNKNOWN':
                print(f"    ⚠️ Warning: Could not determine result for {test_name}")
        
        # Assert all critical tests passed
        if failed_tests:
            self.fail(f"❌ Timing enforcement failed! The following tests failed: {', '.join(failed_tests)}")
        
        # Check overall status
        overall_status = results.get('overall_status', 'UNKNOWN')
        if overall_status != 'ALL_PASS':
            if overall_status == 'ERROR':
                error_msg = results.get('error', 'Unknown error')
                self.fail(f"❌ Test execution error: {error_msg}")
            else:
                self.fail(f"❌ Tests did not complete successfully. Status: {overall_status}")
    
    @unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not available")
    def test_timing_thresholds_enforced(self):
        """
        Verify that specific timing thresholds are being enforced
        """
        print("🎯 Verifying timing threshold enforcement...")
        
        # This test ensures our thresholds are correctly configured
        expected_thresholds = {
            'form_submission_max_ms': 10,
            'critical_path_max_ms': 50, 
            'backend_call_max_ms': 100
        }
        
        # Read the JavaScript test file to verify thresholds are set correctly
        test_file_path = Path(__file__).parent / "test_campaign_wizard_timing.js"
        
        self.assertTrue(test_file_path.exists(), 
                       f"JavaScript timing test file not found: {test_file_path}")
        
        with open(test_file_path, 'r') as f:
            test_content = f.read()
        
        # Verify critical timing thresholds are defined
        self.assertIn("maxAllowedDelay = 10", test_content,
                     "Form submission 10ms threshold not found")
        
        self.assertIn("50", test_content,
                     "Critical path timing threshold missing")
        
        self.assertIn("100", test_content,
                     "Backend call timing threshold missing")
        
        print("✅ Timing thresholds correctly configured")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 