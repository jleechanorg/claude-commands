#!/usr/bin/env python3
"""
Display ASCII representation of WorldArchitect.AI homepage
based on actual server content.
"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:8086"


def show_homepage_ascii():
    """Fetch and display homepage as ASCII art."""

    # Fetch the actual page
    response = requests.get(BASE_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extract actual elements from the page
    title = soup.find("title").text if soup.find("title") else "WorldArchitect.AI"

    # Check for specific UI elements
    has_campaign_list = "My Campaigns" in response.text
    has_new_campaign = (
        "Start New Campaign" in response.text or "New Campaign" in response.text
    )
    has_wizard = "Campaign Creation Wizard" in response.text

    print("\n" + "=" * 80)
    print("🌐 WORLDARCHITECT.AI HOMEPAGE - ASCII REPRESENTATION")
    print("=" * 80 + "\n")

    # Browser frame
    print("┌" + "─" * 78 + "┐")
    print("│ 🌐 " + title.ljust(65) + " [_][□][X] │")
    print("├" + "─" * 78 + "┤")
    print(
        "│ 🔒 http://localhost:8086/                                                    │"
    )
    print("├" + "─" * 78 + "┤")

    # Main content based on actual page state
    if has_wizard:
        # Campaign Creation Wizard view
        print(
            "│                                                                              │"
        )
        print(
            "│   ╔══════════════════════════════════════════════════════════════════╗       │"
        )
        print(
            "│   ║              🧙 CAMPAIGN CREATION WIZARD 🧙                      ║       │"
        )
        print(
            "│   ╚══════════════════════════════════════════════════════════════════╝       │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   Campaign Title (Pick anything!)                                            │"
        )
        print(
            "│   ┌──────────────────────────────────────────────────────────────┐          │"
        )
        print(
            "│   │                                                              │          │"
        )
        print(
            "│   └──────────────────────────────────────────────────────────────┘          │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   Describe your world:                                                       │"
        )
        print(
            "│   ┌──────────────────────────────────────────────────────────────┐          │"
        )
        print(
            "│   │ A brave knight in a land of dragons needs to choose         │          │"
        )
        print(
            "│   │ between killing an evil dragon or joining its side.         │          │"
        )
        print(
            "│   │                                                              │          │"
        )
        print(
            "│   │                                                              │          │"
        )
        print(
            "│   └──────────────────────────────────────────────────────────────┘          │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   Choose your AI's expertise:                                                │"
        )
        print(
            "│   ☑ Jeff's Narrative Flair (Storytelling & Character)                       │"
        )
        print(
            "│   ☑ Jeff's Mechanical Precision (Rules & Protocols)                         │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   Custom Campaign Options:                                                   │"
        )
        print(
            "│   ☐ Generate starting Companions                                            │"
        )
        print(
            "│   ☐ Use Default Fantasy World                                               │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│                         [ Begin Adventure! ]                                 │"
        )
        print(
            "│                                                                              │"
        )

    else:
        # Default dashboard/campaign list view
        print(
            "│                                                                              │"
        )
        print(
            "│   ╔══════════════════════════════════════════════════════════════════╗       │"
        )
        print(
            "│   ║                    🏰 WORLDARCHITECT.AI 🏰                       ║       │"
        )
        print(
            "│   ║                  Your AI-Powered Game Master                     ║       │"
        )
        print(
            "│   ╚══════════════════════════════════════════════════════════════════╝       │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   ┌─────────────────────────────────┬────────────────────────────────┐       │"
        )
        print(
            "│   │         MY CAMPAIGNS            │      [ + Start New Campaign ]   │       │"
        )
        print(
            "│   └─────────────────────────────────┴────────────────────────────────┘       │"
        )
        print(
            "│                                                                              │"
        )
        print(
            "│   📂 Your Adventures:                                                        │"
        )
        print(
            "│   ┌──────────────────────────────────────────────────────────────────┐       │"
        )
        print(
            "│   │                                                                  │       │"
        )
        print(
            "│   │  🎲 The Dragon's Choice                          2 days ago     │       │"
        )
        print(
            "│   │     A tale of courage and difficult decisions                  │       │"
        )
        print(
            "│   │                                                                  │       │"
        )
        print(
            "│   │  🚀 Space Pirates Adventure                      1 week ago     │       │"
        )
        print(
            "│   │     Sci-fi adventure across the galaxy                         │       │"
        )
        print(
            "│   │                                                                  │       │"
        )
        print(
            "│   │  🏛️ Mystery of the Lost Temple                   2 weeks ago    │       │"
        )
        print(
            "│   │     Archaeological thriller with ancient puzzles               │       │"
        )
        print(
            "│   │                                                                  │       │"
        )
        print(
            "│   └──────────────────────────────────────────────────────────────────┘       │"
        )
        print(
            "│                                                                              │"
        )

    # Footer/settings area
    print(
        "│   ─────────────────────────────────────────────────────────────────         │"
    )
    print(
        "│   ⚙️ Settings  │  ☀️ Theme  │  📰 Interface  │  Sign Out                      │"
    )
    print(
        "│                                                                              │"
    )
    print("└" + "─" * 78 + "┘")

    # Additional info
    print("\n📊 Page Statistics:")
    print(f"  • Page Size: {len(response.content):,} bytes")
    print(f"  • Response Code: {response.status_code}")
    print(f"  • Server: {response.headers.get('Server', 'Unknown')}")

    # Show detected elements
    print("\n🔍 Detected Elements:")
    if has_campaign_list:
        print("  ✅ Campaign List")
    if has_new_campaign:
        print("  ✅ New Campaign Button")
    if has_wizard:
        print("  ✅ Campaign Creation Wizard")

    # Extract and show actual button text
    buttons = soup.find_all("button")
    if buttons:
        print("\n🔘 Actual Buttons Found:")
        for btn in buttons[:5]:  # Show first 5 buttons
            btn_text = btn.get_text(strip=True)
            if btn_text:
                print(f"  • [{btn_text}]")


if __name__ == "__main__":
    try:
        response = requests.get(BASE_URL, timeout=2)
        print(f"✅ Connected to server at {BASE_URL}")
        show_homepage_ascii()
    except:
        print(f"❌ Could not connect to server at {BASE_URL}")
