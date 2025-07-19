import logging
import os

import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Constants
BASE_URL = "https://personalitypage.com/html/"
PERSONALITY_TYPES = [
    "ISTJ",
    "ISFJ",
    "INFJ",
    "INTJ",
    "ISTP",
    "ISFP",
    "INFP",
    "INTP",
    "ESTP",
    "ESFP",
    "ENFP",
    "ENTP",
    "ESTJ",
    "ESFJ",
    "ENFJ",
    "ENTJ",
]
# The "growth" pages have a different URL structure
GROWTH_SUFFIX = "-per.html"

TARGET_DIR = os.path.join("mvp_site", "prompts", "personalities")

# Mimic a browser user-agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def download_and_save(ptype, page_type):
    """Downloads content for a given personality type and page type ('portrait' or 'growth')."""
    if page_type == "portrait":
        url = f"{BASE_URL}{ptype}.html"
        filename = f"{ptype}_portrait.md"
    elif page_type == "growth":
        # Growth pages for all types seem to be at the root html directory
        url = f"{BASE_URL}{ptype}{GROWTH_SUFFIX}"
        filename = f"{ptype}_growth.md"
    else:
        logging.error(f"Unknown page type: {page_type}")
        return

    filepath = os.path.join(TARGET_DIR, filename)

    try:
        logging.info(f"Requesting URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.content, "html.parser")

        # The content is within the <body> tag, but we want to remove the header and footer.
        # Let's find a more specific container. The main content seems to be inside
        # a <div class="content-main">, but let's try a broader search within the body
        # and then filter out unwanted elements.
        body_content = soup.body
        if not body_content:
            logging.warning(f"No <body> tag found in {url}. File not created.")
            return

        # Remove nav and footer elements to isolate main content
        for nav in body_content.find_all("nav"):
            nav.decompose()
        for footer in body_content.find_all("footer"):
            footer.decompose()
        # Also remove the top menu div
        for menu in body_content.find_all("div", id="main-nav"):
            menu.decompose()
        for menu in body_content.find_all("div", class_="nav-main"):
            menu.decompose()

        if body_content:
            # Extract text and clean it up
            text = body_content.get_text(separator="\\n", strip=True)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text)
            logging.info(f"Successfully created: {filepath}")
        else:
            logging.warning(f"Could not find content div in {url}. File not created.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {url}: {e}")
    except Exception as e:
        logging.error(f"An error occurred while processing {ptype} ({page_type}): {e}")


def main():
    """Main function to download all personality profiles."""
    if not os.path.exists(TARGET_DIR):
        logging.info(f"Creating target directory: {TARGET_DIR}")
        os.makedirs(TARGET_DIR)

    for ptype in PERSONALITY_TYPES:
        download_and_save(ptype, "portrait")
        download_and_save(ptype, "growth")

    logging.info("All downloads complete.")


if __name__ == "__main__":
    main()
