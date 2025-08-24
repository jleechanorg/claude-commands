#!/usr/bin/env python3
"""Test if headless Chrome supports backdrop-filter."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os

# Set up Chrome options for headless mode
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=800,600")

# Create driver
driver = webdriver.Chrome(options=chrome_options)

try:
    # Navigate to test page
    test_file = f"file://{os.path.abspath('test_backdrop_support.html')}"
    driver.get(test_file)

    # Take screenshot
    driver.save_screenshot("test_backdrop_headless.png")
    print("Screenshot saved to test_backdrop_headless.png")

finally:
    driver.quit()
