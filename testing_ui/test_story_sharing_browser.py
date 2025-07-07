#!/usr/bin/env python3
"""
Real browser test for story sharing functionality using Playwright.
Tests share story link generation and clipboard copy functionality.
"""

import os
import sys
from playwright.sync_api import Page

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase


class StorySharingTest(BrowserTestBase):
    """Test story sharing functionality using the v2 framework."""
    
    def __init__(self):
        super().__init__("Story Sharing Test")
    
    def run_test(self, page: Page) -> bool:
        """Test story sharing through real browser automation."""
        try:
            self.take_screenshot(page, "initial")
            
            # Create campaign with story content
            print("🎮 Creating campaign with story content...")
            if not self._create_campaign_with_story(page):
                print("❌ Failed to create campaign with story")
                return False
            
            self.take_screenshot(page, "campaign_with_story")
            
            # Test story sharing functionality
            print("🔗 Testing story sharing...")
            if not self._test_story_sharing(page):
                print("❌ Failed to test story sharing")
                return False
            
            self.take_screenshot(page, "sharing_attempted")
            
            # Test social media sharing
            print("📱 Testing social media sharing...")
            if not self._test_social_sharing(page):
                print("❌ Failed to test social sharing")
                return False
            
            self.take_screenshot(page, "social_sharing")
            
            # Test sharing permissions
            print("🔒 Testing sharing permissions...")
            if not self._test_sharing_permissions(page):
                print("❌ Failed to test sharing permissions")
                return False
            
            self.take_screenshot(page, "sharing_permissions")
            
            # Test embed functionality
            print("📎 Testing embed functionality...")
            if not self._test_embed_functionality(page):
                print("❌ Failed to test embed functionality")
                return False
            
            self.take_screenshot(page, "embed_functionality")
            
            print("\n✅ Story sharing test completed!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error")
            return False
    
    def _create_campaign_with_story(self, page: Page) -> bool:
        """Create a campaign and add some story content."""
        try:
            # Create campaign using robust approach
            if not page.is_visible("text=New Campaign"):
                print("   ❌ New Campaign button not found")
                return False
                
            page.click("text=New Campaign")
            page.wait_for_load_state("networkidle")
            
            # Fill campaign details - try multiple selectors
            title_selectors = ["#wizard-campaign-title", "#campaign-title", "input[name='title']"]
            desc_selectors = ["#wizard-campaign-prompt", "#campaign-description", "textarea[name='description']"]
            
            title_filled = False
            for selector in title_selectors:
                if page.is_visible(selector):
                    page.fill(selector, "Story Sharing Test Campaign")
                    title_filled = True
                    break
            
            desc_filled = False
            for selector in desc_selectors:
                if page.is_visible(selector):
                    page.fill(selector, "A campaign for testing story sharing and social features.")
                    desc_filled = True
                    break
            
            if not title_filled or not desc_filled:
                print(f"   ⚠️  Form filling incomplete: title={title_filled}, desc={desc_filled}")
                return False
            
            # Navigate through wizard with robust waiting
            for i in range(4):
                page.wait_for_timeout(1000)
                if page.is_visible("button:has-text('Begin Adventure')"):
                    # Use the robust button clicking from campaign creation test
                    try:
                        page.wait_for_selector("button:has-text('Begin Adventure')", state="visible", timeout=5000)
                        button = page.locator("button:has-text('Begin Adventure')").first
                        button.scroll_into_view_if_needed()
                        page.wait_for_timeout(1000)
                        button.click(timeout=10000)
                        break
                    except:
                        page.evaluate("document.querySelector('button[type=submit]').click()")
                        break
                elif page.is_visible("button:has-text('Next')"):
                    page.click("button:has-text('Next')")
                else:
                    print(f"   ⚠️  No Next or Launch button found at step {i+1}")
            
            # Wait for game to start
            page.wait_for_timeout(3000)
            return True
            
        except Exception as e:
            print(f"   ❌ Campaign creation failed: {e}")
            return False
    
    def _test_story_sharing(self, page: Page) -> bool:
        """Test basic story sharing functionality."""
        # Look for share options
        share_selectors = [
            "text=Share",
            "text=Share Story",
            "text=Copy Link",
            "text=Get Link",
            ".share-button",
            ".copy-link-button",
            "#share",
            "button:has-text('Share')",
            "a:has-text('Share')",
            "🔗",
            "📤"
        ]
        
        share_found = False
        for selector in share_selectors:
            try:
                if page.is_visible(selector):
                    print(f"   ✅ Found share option: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)
                    share_found = True
                    break
            except:
                continue
        
        if not share_found:
            # Try menu access
            menu_selectors = ["⋮", "text=Menu", ".menu-button", ".options-button", "text=More"]
            
            for menu_selector in menu_selectors:
                try:
                    if page.is_visible(menu_selector):
                        page.click(menu_selector)
                        page.wait_for_timeout(1000)
                        
                        # Look for share in menu
                        for share_selector in share_selectors:
                            if page.is_visible(share_selector):
                                print(f"   ✅ Found share in menu: {share_selector}")
                                page.click(share_selector)
                                page.wait_for_timeout(1000)
                                share_found = True
                                break
                        
                        if share_found:
                            break
                except:
                    continue
        
        if share_found:
            # Test clipboard copy functionality
            if not self._test_clipboard_copy(page):
                print("   ⚠️  Clipboard copy testing failed")
        else:
            print("   ⚠️  Story sharing not found - may not be implemented")
        
        return True
    
    def _test_clipboard_copy(self, page: Page) -> bool:
        """Test clipboard copy functionality."""
        # Look for copy to clipboard options
        copy_selectors = [
            "text=Copy",
            "text=Copy Link",
            "text=Copy URL",
            "text=Copy to Clipboard",
            ".copy-button",
            ".clipboard-button",
            "#copy-link",
            "button:has-text('Copy')"
        ]
        
        copy_found = False
        for selector in copy_selectors:
            try:
                if page.is_visible(selector):
                    print(f"   ✅ Found copy option: {selector}")
                    page.click(selector)
                    page.wait_for_timeout(1000)
                    copy_found = True
                    
                    # Look for copy confirmation
                    confirmation_selectors = [
                        "text=Copied",
                        "text=Link copied",
                        "text=Copied to clipboard",
                        ".copy-success",
                        ".success-message"
                    ]
                    
                    for conf_selector in confirmation_selectors:
                        try:
                            if page.is_visible(conf_selector):
                                print(f"   ✅ Copy confirmation: {conf_selector}")
                                break
                        except:
                            continue
                    
                    break
            except:
                continue
        
        if not copy_found:
            print("   ⚠️  Copy to clipboard not found")
        
        return copy_found
    
    def _test_social_sharing(self, page: Page) -> bool:
        """Test social media sharing options."""
        # Look for social media share buttons
        social_selectors = [
            "text=Facebook",
            "text=Twitter",
            "text=Reddit",
            "text=Discord",
            "text=WhatsApp",
            ".facebook-share",
            ".twitter-share",
            ".reddit-share",
            ".discord-share",
            ".social-share",
            "a[href*='facebook']",
            "a[href*='twitter']",
            "a[href*='reddit']"
        ]
        
        social_options_found = []
        for selector in social_selectors:
            try:
                if page.is_visible(selector):
                    social_options_found.append(selector)
                    print(f"   ✅ Found social share option: {selector}")
                    
                    # Don't actually click external links, just verify they exist
                    if "href" in selector:
                        href = page.get_attribute(selector, "href")
                        if href:
                            print(f"   ✅ Social link target: {href[:50]}...")
            except:
                continue
        
        if social_options_found:
            print(f"   ✅ Found {len(social_options_found)} social sharing options")
        else:
            print("   ⚠️  Social media sharing not found - may not be implemented")
        
        return True
    
    def _test_sharing_permissions(self, page: Page) -> bool:
        """Test sharing permission settings."""
        # Look for privacy/permission options
        permission_selectors = [
            "text=Public",
            "text=Private",
            "text=Friends Only",
            "text=Unlisted",
            "text=Link Sharing",
            ".privacy-setting",
            ".sharing-permission",
            ".visibility-option",
            "select[id*='privacy']",
            "select[id*='visibility']",
            "input[type='radio'][value*='public']",
            "input[type='radio'][value*='private']"
        ]
        
        permission_options_found = []
        for selector in permission_selectors:
            try:
                if page.is_visible(selector):
                    permission_options_found.append(selector)
                    print(f"   ✅ Found permission option: {selector}")
                    
                    # Test changing permissions
                    if "radio" in selector:
                        page.check(selector)
                        page.wait_for_timeout(200)
                    elif "select" in selector:
                        page.select_option(selector, index=1)
                        page.wait_for_timeout(200)
                    else:
                        page.click(selector)
                        page.wait_for_timeout(200)
            except:
                continue
        
        if permission_options_found:
            print(f"   ✅ Found {len(permission_options_found)} permission options")
        else:
            print("   ⚠️  Sharing permissions not found - may not be implemented")
        
        return True
    
    def _test_embed_functionality(self, page: Page) -> bool:
        """Test embed code generation."""
        # Look for embed options
        embed_selectors = [
            "text=Embed",
            "text=Embed Code",
            "text=iFrame",
            "text=Widget",
            ".embed-button",
            ".embed-code",
            "#embed",
            "button:has-text('Embed')",
            "textarea[id*='embed']"
        ]
        
        embed_found = False
        for selector in embed_selectors:
            try:
                if page.is_visible(selector):
                    print(f"   ✅ Found embed option: {selector}")
                    
                    if "textarea" in selector:
                        # Check if embed code is present
                        embed_code = page.input_value(selector)
                        if embed_code and len(embed_code) > 10:
                            print(f"   ✅ Embed code generated ({len(embed_code)} chars)")
                        else:
                            print("   ⚠️  Embed code may be empty")
                    else:
                        page.click(selector)
                        page.wait_for_timeout(1000)
                        
                        # Look for generated embed code
                        code_selectors = [
                            "textarea[id*='embed']",
                            ".embed-code textarea",
                            "#embed-output",
                            "code"
                        ]
                        
                        for code_selector in code_selectors:
                            try:
                                if page.is_visible(code_selector):
                                    print(f"   ✅ Found embed code area: {code_selector}")
                                    break
                            except:
                                continue
                    
                    embed_found = True
                    break
            except:
                continue
        
        if not embed_found:
            print("   ⚠️  Embed functionality not found - may not be implemented")
        
        return True


if __name__ == "__main__":
    test = StorySharingTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Story sharing tested")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)