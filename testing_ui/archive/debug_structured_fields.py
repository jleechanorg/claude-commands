#!/usr/bin/env python3
"""Debug test to check JavaScript loading"""
import os
from playwright.sync_api import sync_playwright

def debug_js_loading():
    """Debug what JavaScript functions are available"""
    screenshot_dir = "/tmp/structured_response_debug"
    os.makedirs(screenshot_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Loading app...")
            page.goto("http://localhost:8080")
            page.wait_for_load_state('networkidle', timeout=15000)
            
            # Check if app.js loaded
            js_loaded = page.evaluate("""
                () => {
                    const scripts = Array.from(document.querySelectorAll('script[src]'));
                    return scripts.map(s => s.src);
                }
            """)
            print(f"Loaded scripts: {js_loaded}")
            
            # Check all global functions
            global_functions = page.evaluate("""
                () => {
                    const funcs = [];
                    for (let prop in window) {
                        if (typeof window[prop] === 'function' && !prop.startsWith('_')) {
                            funcs.push(prop);
                        }
                    }
                    return funcs.slice(0, 20); // First 20 functions
                }
            """)
            print(f"Global functions found: {global_functions}")
            
            # Check if functions are in different scope
            has_dom_loaded = page.evaluate("""
                () => {
                    return document.readyState === 'complete';
                }
            """)
            print(f"DOM loaded: {has_dom_loaded}")
            
            # Look for the actual text in the page source
            page_content = page.content()
            has_generate_function = "generateStructuredFieldsHTML" in page_content
            has_append_function = "appendToStory" in page_content
            
            print(f"generateStructuredFieldsHTML in source: {has_generate_function}")
            print(f"appendToStory in source: {has_append_function}")
            
            # Take screenshot
            page.screenshot(path=f"{screenshot_dir}/debug.png", full_page=True)
            print(f"Screenshot: {screenshot_dir}/debug.png")
            
        except Exception as e:
            print(f"Debug failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_js_loading() 