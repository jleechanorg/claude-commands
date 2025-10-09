# Python Modules: testing_ui

> Auto-generated overview of module docstrings and public APIs. Enhance descriptions as needed.
> Updated: 2025-10-08

## `testing_ui/archive/take_campaign_screenshots.py`

**Role:** Take screenshots of the campaign wizard in headless mode.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `take_campaign_screenshots` – Take screenshots of all 3 steps of the campaign wizard. (Status: Keep).

---

## `testing_ui/test_campaign_wizard_screenshots.py`

**Role:** Take screenshots of the campaign wizard in headless mode.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `take_campaign_screenshots` – Take screenshots of all 3 steps of the campaign wizard. (Status: Keep).

---

## `testing_ui/test_display_logged_in.py`

**Role:** Test UI display assuming we're already logged in. This test navigates directly to a campaign URL.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_display_fields` – Test that all structured fields are displayed in the UI. (Status: Keep).

---

## `testing_ui/test_format_mismatch_simple.py`

**Role:**
- Simple RED-GREEN test for field format mismatch.
- Tests the core issue: story entries with {"story": content} vs expected {"text": content}.
- NOTE: Updated to comply with coding guidelines requiring Playwright MCP usage instead of direct playwright imports for the `testing_ui/` directory.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_format_mismatch` – Test that should FAIL due to field format mismatch. This test has been updated to remove direct Playwright usage in favor of Playwright MCP functions available in Claude Code CLI environment. (Status: Keep).

---

## `testing_ui/test_full_campaign_creation_real_apis.py`

**Role:** COMPLETE END-TO-END CAMPAIGN CREATION TEST WITH REAL APIS ========================================================= This test validates the COMPLETE user journey: 1. Start with real Firebase + Gemini APIs (NO MOCKS) 2. Go through full campaign creation wizard (steps 1-3) 3. Land on chat interface 4. Send message and get REAL AI response 5. Screenshot the actual chat functionality This test costs money (Gemini API calls) but validates the core product.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_complete_campaign_creation_real_apis` – Complete end-to-end campaign creation with real APIs. (Status: Keep).

---

## `testing_ui/test_mobile_responsive.py`

**Role:** Mobile responsive tests for planning block choice ID font sizes. Tests .choice-id element scaling at mobile breakpoints (320px, 768px).

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_choice_id_mobile_responsive` – Test that .choice-id font-size scales properly on mobile breakpoints. (Status: Keep).
- `test_choice_button_mobile_layout` – Test that choice buttons adapt properly to mobile layout. (Status: Keep).

---

## `testing_ui/test_settings_ui_http.py`

**Role:** TDD HTTP tests for settings page UI functionality. Tests settings page using HTTP requests against a real prod server. This simulates user interactions via HTTP calls rather than browser automation.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestSettingsUIHTTP` – HTTP tests for settings page UI. (Status: Keep).
  - `setUp` – Set up HTTP client with test mode headers. (Status: Keep).
  - `test_settings_button_in_homepage` – 🔴 RED: Homepage should contain settings button. (Status: Keep).
  - `test_settings_page_loads` – 🔴 RED: Settings page should load with proper content. (Status: Keep).
  - `test_settings_api_get_empty_default` – 🔴 RED: Settings API should return empty default for new user. (Status: Keep).
  - `test_settings_api_post_valid_model` – 🔴 RED: Settings API should accept valid model selection. (Status: Keep).
  - `test_settings_api_post_invalid_model` – 🔴 RED: Settings API should reject invalid model selection. (Status: Keep).
  - `test_settings_persistence` – 🔴 RED: Settings should persist across requests. (Status: Keep).
  - `test_settings_page_javascript_functionality` – 🔴 RED: Settings page should include required JavaScript. (Status: Keep).
  - `test_settings_unauthorized_access` – 🔴 RED: Settings endpoints should require authentication. (Status: Keep).

---

## `testing_ui/test_ui_all_elements_debug.py`

**Role:** Comprehensive test to verify ALL UI elements are displayed correctly in debug mode. This test takes screenshots of each structured field to prove the UI fix works.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_all_ui_elements_debug_mode` – Test and screenshot all UI elements in debug mode. (Status: Keep).

---

## `testing_ui/test_ui_display_fix.py`

**Role:** Test the UI display fix for structured response fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_ui_displays_all_fields` – Test that the UI properly displays all structured response fields. (Status: Keep).

---

## `testing_ui/test_ui_display_simple.py`

**Role:** Simple test to verify structured fields display in UI. Focuses on the core issue: are planning blocks and other fields showing up?

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_structured_display` – Simple test to check if structured fields are displayed. (Status: Keep).

---

## `testing_ui/test_ui_simple.py`

**Role:** Simple test to check UI display of structured fields.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_simple_ui_check` – Simple test to see what's displayed in the UI. (Status: Keep).

---

## `testing_ui/test_ui_with_api_campaign.py`

**Role:** Test UI elements by creating a campaign via API first, then using browser to interact. This bypasses UI form issues and focuses on testing the display elements.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `create_campaign_via_api` – Create a campaign using the API with test headers. (Status: Keep).
- `test_ui_elements_with_api_campaign` – Test UI elements using a campaign created via API. (Status: Keep).

---

## `testing_ui/test_ui_with_test_mode.py`

**Role:** Test UI display of structured fields using proper test mode. This test uses the ?test_mode=true URL parameter to bypass authentication.

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `test_structured_fields_display` – Test that planning_block, session_header, dice_rolls, and resources are displayed. (Status: Keep).
- `test_mobile_responsive_choice_id_sizing` – Test that choice-id elements have proper font-size on mobile breakpoints. (Status: Keep).
- `test_campaign_wizard_functionality` – Test campaign wizard input functionality, focusing on wizard-setting-input field. (Status: Keep).

---

## `testing_ui/test_v2_campaign_display_logic.py`

**Role:** Test V2 Campaign Display Logic - Red/Green Test Verifies V2 shows campaigns dashboard when campaigns exist (not landing page)

**Status:** Keep (critical to existing implementation unless noted otherwise).

**Public API:**
- `class TestV2CampaignDisplayLogic` – Test V2 properly displays campaigns dashboard when campaigns exist (Status: Keep).
  - `test_v2_shows_campaigns_when_they_exist` – RED/GREEN Test: V2 should show campaigns dashboard, not landing page EXPECTED BEHAVIOR: 1. User has existing campaigns (confirmed via API: 503 campaigns) 2. V2 should show campaigns dashboard with campaign list 3. V2 should NOT show "Create Your First Campaign" landing page CURRENT BROKEN BEHAVIOR (RED): - V2 API fetches 503 campaigns successfully - V2 still shows landing page instead of campaigns dashboard - This breaks user experience for existing users (Status: Keep).
- `run_red_green_test` – Run the red-green test for V2 campaign display logic (Status: Keep).

---

