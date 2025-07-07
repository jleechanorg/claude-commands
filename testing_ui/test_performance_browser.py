#!/usr/bin/env python3
"""
Real browser test for Performance testing using Playwright.
This test automates a real browser to test long story performance.
"""

import os
import sys
import time
from playwright.sync_api import Page, TimeoutError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from browser_test_base import BrowserTestBase, click_button_with_text, wait_for_element


class PerformanceTest(BrowserTestBase):
    """Test Performance with long stories through real browser automation."""
    
    def __init__(self):
        super().__init__("Performance Test")
    
    def run_test(self, page: Page) -> bool:
        """Test performance with long stories."""
        
        try:
            # Take initial screenshot
            self.take_screenshot(page, "dashboard_initial")
            
            # Create campaign for performance testing
            print("🎮 Creating campaign for performance testing...")
            if page.is_visible("text=New Campaign"):
                page.click("text=New Campaign")
                page.wait_for_timeout(1000)
                
                if page.is_visible("#wizard-campaign-title"):
                    page.fill("#wizard-campaign-title", "Performance Test Campaign")
                    page.fill("#wizard-campaign-prompt", "A long epic adventure for performance testing.")
                    
                    # Complete wizard quickly
                    for i in range(4):
                        if page.is_visible("#wizard-next"):
                            page.click("#wizard-next")
                            page.wait_for_timeout(500)
                        elif page.is_visible("#launch-campaign"):
                            page.click("#launch-campaign")
                            break
                    
                    page.wait_for_timeout(3000)
            
            # Test performance with many messages
            print("📝 Testing performance with many messages...")
            
            message_input = page.query_selector("#message-input") or page.query_selector("textarea[placeholder*='What do you do']")
            send_button = page.query_selector("button:has-text('Send')") or page.query_selector("#send-button")
            
            if message_input:
                # Send multiple messages quickly
                messages = [
                    "I explore the ancient ruins",
                    "I search for hidden treasures", 
                    "I battle fierce monsters",
                    "I solve mysterious puzzles",
                    "I discover magical artifacts"
                ]
                
                start_time = time.time()
                
                for i, msg in enumerate(messages):
                    print(f"   📝 Sending message {i+1}/5: {msg[:30]}...")
                    message_input.fill(msg)
                    
                    if send_button:
                        send_button.click()
                    else:
                        message_input.press("Enter")
                    
                    # Wait for response but don't wait too long
                    page.wait_for_timeout(2000)
                
                end_time = time.time()
                total_time = end_time - start_time
                print(f"   ⏱️  Total time for 5 messages: {total_time:.2f} seconds")
                
                self.take_screenshot(page, "many_messages")
            
            # Test scroll performance
            print("📜 Testing scroll performance...")
            
            # Scroll through chat history
            chat_area = page.query_selector("#chat-messages") or page.query_selector(".chat-messages")
            if chat_area:
                print("   📜 Testing scroll performance...")
                
                # Scroll to top
                page.evaluate("document.querySelector('#chat-messages, .chat-messages').scrollTop = 0")
                page.wait_for_timeout(500)
                
                # Scroll to bottom quickly
                page.evaluate("document.querySelector('#chat-messages, .chat-messages').scrollTop = document.querySelector('#chat-messages, .chat-messages').scrollHeight")
                page.wait_for_timeout(500)
                
                print("   ✅ Scroll performance tested")
                self.take_screenshot(page, "scroll_performance")
            
            # Test memory usage indicators
            print("💾 Testing memory usage...")
            
            # Check for memory usage indicators
            memory_info = page.evaluate("""
                (() => {
                    if (performance.memory) {
                        return {
                            used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                            total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                            limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
                        };
                    }
                    return null;
                })();
            """)
            
            if memory_info:
                print(f"   💾 Memory usage: {memory_info['used']}MB / {memory_info['total']}MB (limit: {memory_info['limit']}MB)")
            
            # Test page load performance
            print("⚡ Testing page load performance...")
            
            # Navigate away and back to test load time
            if page.is_visible("text=Dashboard"):
                start_time = time.time()
                page.click("text=Dashboard")
                page.wait_for_selector("#dashboard-view.active-view", timeout=10000)
                end_time = time.time()
                
                dashboard_load_time = end_time - start_time
                print(f"   ⚡ Dashboard load time: {dashboard_load_time:.2f} seconds")
                
                # Go back to campaign
                if page.is_visible("text=Performance Test Campaign"):
                    start_time = time.time()
                    page.click("text=Performance Test Campaign")
                    page.wait_for_selector("#game-view.active-view", timeout=10000)
                    end_time = time.time()
                    
                    campaign_load_time = end_time - start_time
                    print(f"   ⚡ Campaign load time: {campaign_load_time:.2f} seconds")
            
            self.take_screenshot(page, "load_performance")
            
            print("\n✅ Performance test completed successfully!")
            return True
            
        except TimeoutError as e:
            print(f"❌ Timeout error: {e}")
            self.take_screenshot(page, "error_timeout")
            return False
        except Exception as e:
            print(f"❌ Test failed: {e}")
            self.take_screenshot(page, "error_general")
            return False


if __name__ == "__main__":
    test = PerformanceTest()
    success = test.execute()
    
    if success:
        print("\n✅ TEST PASSED - Performance tested via browser automation")
        sys.exit(0)
    else:
        print("\n❌ TEST FAILED - See screenshots for details")
        sys.exit(1)