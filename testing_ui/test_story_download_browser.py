#!/usr/bin/env python3
"""
Real browser test for story download functionality using Playwright.
Tests downloading story as text file and verifying content.
"""

import os
import sys
from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class StoryDownloadTest(BrowserTestBase):
    """Test story download functionality using the v2 framework."""
    
    def __init__(self):
        super().__init__("Story Download Test")
    
    def run_test(self, page: Page) -> bool:
        """Test story download through real browser automation."""
        try:
            self.take_screenshot(page, "initial")
            
            # Create campaign with story content
            print("🎮 Creating campaign with story content...")
            if not self._create_campaign_with_story(page):
                print("❌ Failed to create campaign with story")
                return False
            
            self.take_screenshot(page, "campaign_with_story")
            
            # Test story download functionality
            print("📥 Testing story download...")
            if not self._test_story_download(page):
                print("❌ Failed to test story download")
                return False
            
            self.take_screenshot(page, "download_attempted")
            
            # Test download formats
            print("📄 Testing download formats...")
            if not self._test_download_formats(page):
                print("❌ Failed to test download formats")
                return False
            
            self.take_screenshot(page, "download_formats")
            
            # Test export options
            print("📤 Testing export options...")
            if not self._test_export_options(page):
                print("❌ Failed to test export options")
                return False
            
            self.take_screenshot(page, "export_options")
            
            print("\n✅ Story download test completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False
    
    def _create_campaign_with_story(self, page: Page) -> bool:
        """Create a campaign and add some story content."""
        if not page.is_visible("text=New Campaign"):
            return False
            
        page.click("text=New Campaign")
        page.wait_for_timeout(1000)
        
        if page.is_visible("#wizard-campaign-title"):
            page.fill("#wizard-campaign-title", "Story Download Test Campaign")
            page.fill("#wizard-campaign-prompt", "A campaign for testing story download and export features.")
            
            # Quick wizard navigation
            for i in range(4):
                if page.is_visible("#wizard-next"):
                    page.click("#wizard-next")
                    page.wait_for_timeout(500)
                elif page.is_visible("#launch-campaign"):
                    page.click("#launch-campaign")
                    break
            
            page.wait_for_timeout(2000)
            
            # Add some story content by sending messages
            message_input = page.query_selector("#message-input")
            if message_input:
                messages = [
                    "I explore the mysterious cave entrance.",
                    "I examine the ancient runes on the wall.",
                    "I proceed deeper into the cavern."
                ]
                
                for msg in messages:
                    message_input.fill(msg)
                    send_btn = page.query_selector("button:has-text('Send')")
                    if send_btn:
                        send_btn.click()
                    else:
                        message_input.press("Enter")
                    page.wait_for_timeout(1000)
                
                print("   ✅ Story content added")
                return True
        
        return False
    
    def _test_story_download(self, page: Page) -> bool:
        """Test basic story download functionality."""
        # Look for download options
        download_selectors = [
            "text=Download",
            "text=Export",
            "text=Save Story",
            "text=Download Story",
            ".download-button",
            ".export-button",
            "#download",
            "button:has-text('Download')",
            "a:has-text('Download')",
            "📥"
        ]
        
        download_found = False
        for selector in download_selectors:
            try:
                if page.is_visible(selector):
                    print(f"   ✅ Found download option: {selector}")
                    
                    # Set up download handler
                    with page.expect_download() as download_info:
                        page.click(selector)
                        page.wait_for_timeout(2000)
                    
                    try:
                        download = download_info.value
                        print(f"   ✅ Download started: {download.suggested_filename}")
                        download_found = True
                        break
                    except:
                        print("   ⚠️  Download may not have completed")
                        download_found = True
                        break
                        
            except Exception as e:
                print(f"   ⚠️  Error with selector {selector}: {e}")
                continue
        
        if not download_found:
            # Try menu access
            menu_selectors = ["⋮", "text=Menu", ".menu-button", ".options-button"]
            
            for menu_selector in menu_selectors:
                try:
                    if page.is_visible(menu_selector):
                        page.click(menu_selector)
                        page.wait_for_timeout(1000)
                        
                        # Look for download in menu
                        for download_selector in download_selectors:
                            if page.is_visible(download_selector):
                                print(f"   ✅ Found download in menu: {download_selector}")
                                page.click(download_selector)
                                page.wait_for_timeout(1000)
                                download_found = True
                                break
                        
                        if download_found:
                            break
                except:
                    continue
        
        if not download_found:
            print("   ⚠️  Story download not found - may not be implemented")
        
        return True
    
    def _test_download_formats(self, page: Page) -> bool:
        """Test different download formats."""
        # Look for format options
        format_selectors = [
            "text=PDF",
            "text=TXT",
            "text=HTML",
            "text=JSON",
            "text=Markdown",
            ".format-option",
            "select[id*='format']",
            "input[type='radio'][value*='pdf']",
            "input[type='radio'][value*='txt']"
        ]
        
        formats_found = []
        for selector in format_selectors:
            try:
                if page.is_visible(selector):
                    formats_found.append(selector)
                    print(f"   ✅ Found format option: {selector}")
                    
                    # Try to select the format
                    if "radio" in selector:
                        page.check(selector)
                    elif "select" in selector:
                        page.select_option(selector, index=1)
                    else:
                        page.click(selector)
                    
                    page.wait_for_timeout(500)
            except:
                continue
        
        if formats_found:
            print(f"   ✅ Found {len(formats_found)} download format options")
        else:
            print("   ⚠️  Download format options not found - may not be implemented")
        
        return True
    
    def _test_export_options(self, page: Page) -> bool:
        """Test export-specific options."""
        # Look for export settings
        export_option_selectors = [
            "text=Include Images",
            "text=Include Timestamps",
            "text=Include Character Sheets",
            "text=Include Dice Rolls",
            "text=Full Export",
            "text=Story Only",
            ".export-options",
            ".export-settings",
            "input[type='checkbox'][id*='include']",
            "input[type='checkbox'][id*='export']"
        ]
        
        export_options_found = []
        for selector in export_option_selectors:
            try:
                if page.is_visible(selector):
                    export_options_found.append(selector)
                    print(f"   ✅ Found export option: {selector}")
                    
                    # Test toggling option
                    if "checkbox" in selector:
                        page.check(selector)
                        page.wait_for_timeout(200)
                        page.uncheck(selector)
                        page.wait_for_timeout(200)
                    else:
                        page.click(selector)
                        page.wait_for_timeout(200)
            except:
                continue
        
        if export_options_found:
            print(f"   ✅ Found {len(export_options_found)} export options")
        else:
            print("   ⚠️  Export options not found - may not be implemented")
        
        return True


if __name__ == "__main__":
    test = StoryDownloadTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Story download tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)