#!/usr/bin/env python3
"""
Test script to verify UI bundle fixes are working properly.
Tests:
1. Campaign wizard has Dragon Knight radio buttons
2. Inline editing works on game page
3. Story reader controls are visible and functional
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_campaign_wizard_dragon_knight():
    """Test that campaign wizard includes Dragon Knight radio buttons."""
    print("\n🧪 Testing Campaign Wizard Dragon Knight Feature...")
    
    # Check if the campaign wizard JS has the new features
    wizard_path = "mvp_site/static/js/campaign-wizard.js"
    with open(wizard_path, 'r') as f:
        content = f.read()
        
    checks = [
        ("Dragon Knight radio button HTML", "wizard-dragonKnightCampaign" in content),
        ("Custom campaign radio button HTML", "wizard-customCampaign" in content),
        ("Campaign type change handler", "handleCampaignTypeChange" in content),
        ("Dragon Knight content loading", "campaign_module_dragon_knight.md" in content),
        ("Campaign type cards styling", "campaign-type-card" in content)
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    return all(result for _, result in checks)

def test_inline_editor_integration():
    """Test that inline editor is properly integrated."""
    print("\n🧪 Testing Inline Editor Integration...")
    
    # Check app.js for inline editor initialization
    app_path = "mvp_site/static/app.js"
    with open(app_path, 'r') as f:
        content = f.read()
        
    checks = [
        ("InlineEditor class check", "window.InlineEditor" in content),
        ("InlineEditor initialization in resumeCampaign", "new InlineEditor(gameTitleElement" in content),
        ("Save function for campaign title", "`/api/campaigns/${campaignId}`" in content),
        ("Error handling for inline edit", "onError:" in content)
    ]
    
    # Check if CSS is loaded
    css_path = "mvp_site/static/css/inline-editor.css"
    css_exists = os.path.exists(css_path)
    checks.append(("Inline editor CSS exists", css_exists))
    
    if css_exists:
        with open(css_path, 'r') as f:
            css_content = f.read()
        checks.append(("CSS has editable styles", ".inline-editable" in css_content))
        checks.append(("CSS has hover effects", ".inline-editable:hover" in css_content))
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    return all(result for _, result in checks)

def test_story_reader_controls():
    """Test that story reader controls are visible and functional."""
    print("\n🧪 Testing Story Reader Controls...")
    
    # Check index.html for story reader buttons
    index_path = "mvp_site/static/index.html"
    with open(index_path, 'r') as f:
        html_content = f.read()
        
    checks = [
        ("Read Story button in HTML", 'id="readStoryBtn"' in html_content),
        ("Pause Story button in HTML", 'id="pauseStoryBtn"' in html_content),
        ("Story reader controls container", 'story-reader-controls-inline' in html_content)
    ]
    
    # Check app.js for event listeners
    app_path = "mvp_site/static/app.js"
    with open(app_path, 'r') as f:
        app_content = f.read()
        
    checks.extend([
        ("Read button event listener", "getElementById('readStoryBtn')" in app_content),
        ("Pause button event listener", "getElementById('pauseStoryBtn')" in app_content),
        ("Story reader integration", "window.storyReader" in app_content)
    ])
    
    # Check CSS for inline controls
    css_path = "mvp_site/static/styles/story-reader.css"
    with open(css_path, 'r') as f:
        css_content = f.read()
        
    checks.extend([
        ("Inline controls CSS", ".story-reader-controls-inline" in css_content),
        ("Button styling", ".story-reader-controls-inline .btn" in css_content)
    ])
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    return all(result for _, result in checks)

def test_css_integration():
    """Test that all CSS files are properly integrated."""
    print("\n🧪 Testing CSS Integration...")
    
    # Check if CSS files are included in index.html
    index_path = "mvp_site/static/index.html"
    with open(index_path, 'r') as f:
        html_content = f.read()
        
    css_files = [
        ("Interactive features CSS", "interactive-features.css"),
        ("Story reader CSS", "story-reader.css"),
        ("Inline editor CSS", "inline-editor.css")
    ]
    
    checks = []
    for css_name, filename in css_files:
        checks.append((f"{css_name} linked", filename in html_content))
    
    # Check campaign type cards CSS
    features_css_path = "mvp_site/static/styles/interactive-features.css"
    with open(features_css_path, 'r') as f:
        features_content = f.read()
        
    checks.extend([
        ("Campaign type cards grid", ".campaign-type-cards" in features_content),
        ("Campaign type card styling", ".campaign-type-card" in features_content),
        ("Dark mode support for cards", "[data-theme=\"dark\"] .campaign-type-card" in features_content),
        ("Responsive design for cards", "grid-template-columns: 1fr;" in features_content)
    ])
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
    
    return all(result for _, result in checks)

def main():
    """Run all UI bundle tests."""
    print("=" * 60)
    print("UI Bundle Fix Verification")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        test_campaign_wizard_dragon_knight,
        test_inline_editor_integration,
        test_story_reader_controls,
        test_css_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ❌ Test failed with error: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("Summary:")
    print(f"  Total tests: {len(results)}")
    print(f"  Passed: {sum(results)}")
    print(f"  Failed: {len(results) - sum(results)}")
    
    if all(results):
        print("\n✅ All UI bundle fixes are properly implemented!")
        return 0
    else:
        print("\n❌ Some fixes are missing or incomplete.")
        return 1

if __name__ == "__main__":
    sys.exit(main())