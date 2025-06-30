#!/usr/bin/env python3
"""
Minimal test to verify file operations
"""

from pathlib import Path

mvp_site_path = Path(__file__).parent

def test_file_exists():
    """Test that files exist"""
    files_to_check = [
        "static/js/interface-manager.js",
        "static/js/campaign-wizard.js", 
        "static/js/enhanced-search.js",
        "static/styles/interactive-features.css",
        "static/index.html"
    ]
    
    for file_path in files_to_check:
        full_path = mvp_site_path / file_path
        if full_path.exists():
            print(f"✅ {file_path} exists ({full_path.stat().st_size} bytes)")
        else:
            print(f"❌ {file_path} missing")

def test_content_snippets():
    """Test that expected content snippets exist"""
    checks = [
        ("static/js/interface-manager.js", "class InterfaceManager"),
        ("static/js/campaign-wizard.js", "class CampaignWizard"),
        ("static/js/enhanced-search.js", "class EnhancedSearch"),
        ("static/styles/interactive-features.css", ".campaign-wizard"),
        ("static/index.html", "interface-manager.js")
    ]
    
    for file_path, expected_content in checks:
        full_path = mvp_site_path / file_path
        try:
            content = full_path.read_text()
            if expected_content in content:
                print(f"✅ {file_path} contains '{expected_content}'")
            else:
                print(f"❌ {file_path} missing '{expected_content}'")
        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")

if __name__ == "__main__":
    print("🔍 Minimal File Check")
    print("=" * 40)
    test_file_exists()
    print()
    test_content_snippets() 