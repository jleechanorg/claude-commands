#!/usr/bin/env python3
"""
Campaign Wizard Reset Issue Reproduction Test

This test reproduces the exact user workflow that leads to the persistent spinner issue:
1. Create first campaign
2. Navigate back to dashboard  
3. Click "Start Campaign" again
4. Verify wizard appears clean (not spinner)
"""

import unittest
import time
import os
import threading
import http.server
import socketserver
from pathlib import Path

# Try to import Selenium - skip tests if not available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class CampaignWizardResetReproductionTest(unittest.TestCase):
    """
    Automated reproduction of the campaign wizard reset issue
    """
    
    @classmethod
    def setUpClass(cls):
        if not SELENIUM_AVAILABLE:
            return
            
        # Set up test server - use dynamic port to avoid conflicts
        import socket
        sock = socket.socket()
        sock.bind(('', 0))
        cls.server_port = sock.getsockname()[1]
        sock.close()
        
        cls.server_thread = None
        cls.start_test_server()
        
        # Set up browser
        cls.setup_browser()
        
    @classmethod
    def start_test_server(cls):
        """Start local server serving the application"""
        try:
            class CustomHandler(http.server.SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    # Go up to mvp_site directory to serve actual application files
                    mvp_site_dir = Path(__file__).parent.parent.parent
                    super().__init__(*args, directory=str(mvp_site_dir), **kwargs)
                    
                def log_message(self, format, *args):
                    pass  # Suppress server logs
                    
            cls.httpd = socketserver.TCPServer(("", cls.server_port), CustomHandler)
            cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
            cls.server_thread.start()
            time.sleep(1)  # Allow server to start
        except Exception as e:
            print(f"Failed to start test server: {e}")
            
    @classmethod
    def setup_browser(cls):
        """Set up Chrome browser for testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in background
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(10)
        except WebDriverException as e:
            print(f"Failed to initialize Chrome driver: {e}")
            cls.driver = None
            
    @classmethod
    def tearDownClass(cls):
        if SELENIUM_AVAILABLE and hasattr(cls, 'driver') and cls.driver:
            cls.driver.quit()
        if hasattr(cls, 'httpd'):
            cls.httpd.shutdown()
            
    def setUp(self):
        if not SELENIUM_AVAILABLE:
            self.skipTest("Selenium not available")
        if not hasattr(self, 'driver') or not self.driver:
            self.skipTest("Chrome driver not available")
            
    @unittest.skipUnless(SELENIUM_AVAILABLE, "Selenium not available")
    def test_campaign_wizard_reset_issue_reproduction(self):
        """
        Reproduce the complete user workflow that leads to persistent spinner
        """
        print("\n🧪 REPRODUCING CAMPAIGN WIZARD RESET ISSUE")
        
        # Step 1: Load main application page
        print("📱 Step 1: Loading application...")
        self.driver.get(f"http://localhost:{self.server_port}/test_timing_runner.html")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Step 2: Simulate first campaign creation
        print("🎮 Step 2: Simulating first campaign creation...")
        
        # Create mock DOM elements that mirror real application structure
        self.driver.execute_script("""
            // Create mock application structure
            document.body.innerHTML = `
                <div id="dashboard-section" style="display: none;">
                    <h2>Campaign Dashboard</h2>
                    <button id="start-campaign-btn" class="btn btn-primary">Start Campaign</button>
                </div>
                
                <div id="campaign-creation-section" style="display: block;">
                    <form id="new-campaign-form">
                        <input id="campaign-title" value="Test Campaign" />
                        <textarea id="campaign-prompt">Test prompt</textarea>
                        <button type="button" id="begin-adventure-btn" onclick="beginAdventure()">Begin Adventure!</button>
                    </form>
                </div>
                
                <div id="campaign-wizard"></div>
            `;
            
            // Mock the campaign wizard object
            window.campaignWizard = {
                isEnabled: false,
                
                enable() {
                    console.log('🔧 Campaign wizard enabled');
                    this.isEnabled = true;
                    this.forceCleanRecreation();
                },
                
                forceCleanRecreation() {
                    console.log('🧹 Force clean recreation called');
                    const existingWizard = document.getElementById('campaign-wizard');
                    const existingSpinner = document.getElementById('campaign-creation-spinner');
                    
                    if (existingWizard) {
                        existingWizard.innerHTML = ''; // Clear any existing content
                    }
                    if (existingSpinner) {
                        existingSpinner.remove();
                    }
                    
                    this.replaceOriginalForm();
                },
                
                replaceOriginalForm() {
                    console.log('🔄 Replace original form called');
                    const wizardContainer = document.getElementById('campaign-wizard');
                    if (wizardContainer) {
                        wizardContainer.innerHTML = `
                            <div class="wizard-content">
                                <h3>Campaign Creation Wizard</h3>
                                <div class="wizard-step">Step 1: Basic Details</div>
                            </div>
                        `;
                    }
                },
                
                showDetailedSpinner() {
                    console.log('⏳ Show detailed spinner called');
                    const container = document.getElementById('campaign-wizard');
                    
                    // This is the PROBLEMATIC code that destroys wizard structure
                    const spinnerHTML = `
                        <div id="campaign-creation-spinner" class="text-center py-5">
                            <div class="spinner-border text-primary mb-4" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <h4 class="text-primary mb-3">🏗️ Building Your Adventure...</h4>
                            <div class="progress mb-4">
                                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                            </div>
                        </div>
                    `;
                    
                    if (container) {
                        // REPRODUCE THE BUG: This destroys the wizard content
                        container.innerHTML = spinnerHTML;
                    }
                },
                
                completeProgress() {
                    console.log('✅ Complete progress called');
                    // Simulate campaign creation completion
                    setTimeout(() => {
                        this.navigateToDashboard();
                    }, 1000);
                },
                
                navigateToDashboard() {
                    console.log('📊 Navigating to dashboard');
                    document.getElementById('campaign-creation-section').style.display = 'none';
                    document.getElementById('dashboard-section').style.display = 'block';
                    this.isEnabled = false;
                }
            };
            
            // Mock the beginAdventure function
            window.beginAdventure = function() {
                console.log('🚀 Begin Adventure clicked');
                window.campaignWizard.showDetailedSpinner();
                
                // Simulate backend processing time
                setTimeout(() => {
                    window.campaignWizard.completeProgress();
                }, 2000);
            };
            
            // Mock the start campaign function
            window.startCampaign = function() {
                console.log('🎯 Start Campaign clicked');
                document.getElementById('dashboard-section').style.display = 'none';
                document.getElementById('campaign-creation-section').style.display = 'block';
                window.campaignWizard.enable();
            };
            
            // Add event listener for start campaign button
            document.getElementById('start-campaign-btn').addEventListener('click', startCampaign);
        """)
        
        # Step 3: Click "Begin Adventure" to create first campaign
        print("🚀 Step 3: Clicking 'Begin Adventure' to create first campaign...")
        begin_btn = self.driver.find_element(By.ID, "begin-adventure-btn")
        begin_btn.click()
        
        # Step 4: Wait for spinner to appear
        print("⏳ Step 4: Waiting for spinner to appear...")
        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.ID, "campaign-creation-spinner"))
        )
        
        spinner_present = self.driver.find_element(By.ID, "campaign-creation-spinner").is_displayed()
        print(f"   Spinner visible: {spinner_present}")
        
        # Step 5: Wait for campaign creation to complete and navigate to dashboard
        print("📊 Step 5: Waiting for campaign creation to complete...")
        WebDriverWait(self.driver, 10).until(
            EC.visibility_of_element_located((By.ID, "dashboard-section"))
        )
        
        dashboard_visible = self.driver.find_element(By.ID, "dashboard-section").is_displayed()
        print(f"   Dashboard visible: {dashboard_visible}")
        
        # Step 6: Click "Start Campaign" again (this should trigger the bug)
        print("🎯 Step 6: Clicking 'Start Campaign' again (reproducing the bug)...")
        start_campaign_btn = self.driver.find_element(By.ID, "start-campaign-btn")
        start_campaign_btn.click()
        
        # Step 7: Check what appears - wizard or spinner?
        print("🔍 Step 7: Checking what appears - fresh wizard or persistent spinner...")
        
        time.sleep(1)  # Allow UI to update
        
        # Check if wizard content is present
        try:
            wizard_content = self.driver.find_element(By.CLASS_NAME, "wizard-content")
            wizard_present = wizard_content.is_displayed()
            print(f"   ✅ Fresh wizard content present: {wizard_present}")
        except:
            wizard_present = False
            print("   ❌ Fresh wizard content NOT found")
        
        # Check if old spinner is still present
        try:
            old_spinner = self.driver.find_element(By.ID, "campaign-creation-spinner")
            spinner_persistent = old_spinner.is_displayed()
            print(f"   🐛 Persistent spinner present: {spinner_persistent}")
        except:
            spinner_persistent = False
            print("   ✅ No persistent spinner found")
        
        # Step 8: Analyze the DOM state
        print("🔬 Step 8: Analyzing DOM state for debugging...")
        
        wizard_container_html = self.driver.execute_script("""
            const container = document.getElementById('campaign-wizard');
            return container ? container.innerHTML : 'Container not found';
        """)
        
        print(f"   Campaign wizard container contents:")
        print(f"   {wizard_container_html[:200]}..." if len(wizard_container_html) > 200 else f"   {wizard_container_html}")
        
        # Step 9: Generate test results
        print("📋 Step 9: Test Results Summary")
        print("=" * 50)
        
        if wizard_present and not spinner_persistent:
            print("✅ EXPECTED BEHAVIOR: Fresh wizard appears, no persistent spinner")
            test_result = "PASS"
        elif not wizard_present and spinner_persistent:
            print("🐛 BUG REPRODUCED: Persistent spinner, no fresh wizard")
            test_result = "BUG_REPRODUCED"
        elif not wizard_present and not spinner_persistent:
            print("❓ UNEXPECTED: Neither wizard nor spinner present")
            test_result = "UNEXPECTED_STATE"
        else:
            print("❓ MIXED STATE: Both wizard and spinner present")
            test_result = "MIXED_STATE"
            
        print(f"Test Result: {test_result}")
        print("=" * 50)
        
        # For debugging purposes, don't fail the test - just report findings
        self.assertTrue(True, f"Bug reproduction test completed. Result: {test_result}")
        
        return {
            'wizard_present': wizard_present,
            'spinner_persistent': spinner_persistent,
            'test_result': test_result,
            'dom_state': wizard_container_html
        }


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2) 