#!/usr/bin/env vpython
"""Take screenshots of the campaign wizard in headless mode."""

import os
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


def take_campaign_screenshots():
    """Take screenshots of all 3 steps of the campaign wizard."""

    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1200,1600")

    # Create driver
    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to the app
        print("Navigating to app...")
        driver.get("http://localhost:3001/v2/?test_mode=true&test_user_id=test-123")
        time.sleep(3)

        # Click on Create Your First Campaign
        print("Clicking Create Campaign button...")
        create_btn = wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Create Your First Campaign')]")
            )
        )
        create_btn.click()
        time.sleep(2)

        # Click on Create V2 Campaign
        print("Clicking Create V2 Campaign...")
        v2_btn = wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Create V2 Campaign')]")
            )
        )
        v2_btn.click()
        time.sleep(2)

        # Take screenshot of Step 1
        print("Taking screenshot of Step 1 - Basics...")
        driver.save_screenshot("roadmap/screenshots/campaign-wizard-step1-basics.png")

        # Click Next to go to Step 2
        print("Going to Step 2...")
        next_btn = wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, "//button[text()='Next']")
            )
        )
        next_btn.click()
        time.sleep(2)

        # Take screenshot of Step 2
        print("Taking screenshot of Step 2 - AI Style...")
        driver.save_screenshot("roadmap/screenshots/campaign-wizard-step2-ai-style.png")

        # Click Next to go to Step 3
        print("Going to Step 3...")
        next_btn = wait.until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, "//button[text()='Next']")
            )
        )
        next_btn.click()
        time.sleep(2)

        # Take screenshot of Step 3
        print("Taking screenshot of Step 3 - Launch...")
        driver.save_screenshot("roadmap/screenshots/campaign-wizard-step3-launch.png")

        print("Screenshots saved!")

    finally:
        driver.quit()


if __name__ == "__main__":
    # Create screenshots directory if it doesn't exist
    os.makedirs("roadmap/screenshots", exist_ok=True)
    take_campaign_screenshots()
