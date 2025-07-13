#!/usr/bin/env python3
"""
Save Puppeteer MCP screenshots to files for verification.
This script captures Puppeteer MCP screenshots and saves them as actual PNG files.
"""
import base64
import os
import json
from datetime import datetime
from typing import Optional

def save_screenshot_to_file(base64_data: str, name: str, output_dir: str = "/tmp/puppeteer_screenshots"):
    """
    Save a base64 encoded screenshot from Puppeteer MCP to a PNG file.
    
    Args:
        base64_data: Base64 encoded PNG data from Puppeteer MCP
        name: Name for the screenshot file
        output_dir: Directory to save screenshots
        
    Returns:
        str: Filepath of saved screenshot or None if failed
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Remove data URI prefix if present
        if base64_data.startswith('data:image/png;base64,'):
            base64_data = base64_data.split(',', 1)[1]
        
        # Decode base64 and save
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(base64_data))
        
        print(f"✅ Screenshot saved: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving screenshot: {e}")
        return None

def capture_and_save_screenshot(name: str, base64_data: Optional[str] = None):
    """
    Capture a screenshot with Puppeteer MCP and save it to a file.
    If base64_data is provided, save it using save_screenshot_to_file.
    Otherwise, print instructions for MCP usage.
    """
    print(f"📸 Capturing screenshot: {name}")
    if base64_data:
        return save_screenshot_to_file(base64_data, name)
    else:
        # This will be executed by calling the MCP function
        # The implementation will be done through actual MCP calls
        print(f"   Use: mcp__puppeteer-server__puppeteer_screenshot(name='{name}', encoded=True)")
        print(f"   Then: save_screenshot_to_file(base64_data, '{name}')")
        return f"/tmp/puppeteer_screenshots/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{name}.png"

if __name__ == "__main__":
    print("🤖 Puppeteer MCP Screenshot Saver")
    print("=" * 40)
    print("This script provides functions to save Puppeteer MCP screenshots to files.")
    print("Usage: import and call save_screenshot_to_file() with base64 data")