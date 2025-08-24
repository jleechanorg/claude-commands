#!/usr/bin/env vpython
"""Test headless browser with Figma site to verify backdrop-filter support."""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_figma_site():
    """Take screenshots of Figma site using headless Chrome."""

    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,800")
    # Add flags that might help with rendering
    chrome_options.add_argument("--enable-features=WebRTCPipeWireCapturer")
    chrome_options.add_argument("--disable-gpu-sandbox")
    chrome_options.add_argument("--enable-webgl")
    chrome_options.add_argument("--use-gl=swiftshader")

    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to the Figma site
        print("Navigating to Figma site...")
        driver.get("https://queue-person-81886387.figma.site/")

        # Wait for page to load
        time.sleep(5)

        # Take initial screenshot
        print("Taking screenshot of Figma site...")
        driver.save_screenshot("figma_site_headless.png")

        # Try to find any campaign wizard or similar elements
        print("Looking for interactive elements...")
        try:
            # Click on any "Start" or "Create" buttons if present
            buttons = driver.find_elements(By.TAG_NAME, "button")
            print(f"Found {len(buttons)} buttons on the page")

            # Take another screenshot
            driver.save_screenshot("figma_site_headless_full.png")

        except Exception as e:
            print(f"No specific elements found: {e}")

        # Also save the page source for inspection
        with open("figma_site_source.html", "w") as f:
            f.write(driver.page_source)
        print("Saved page source to figma_site_source.html")

        print("Screenshots saved!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_figma_site()
