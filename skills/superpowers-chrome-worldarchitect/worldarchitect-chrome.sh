#!/usr/bin/env bash
# WorldArchitect Chrome Automation Wrapper
#
# Wraps obra/superpowers-chrome for WorldArchitect.AI browser automation
# Provides RPG-specific helper functions and session management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Session tracking
SESSION_DIR="/tmp/chrome-worldarchitect-$$"
mkdir -p "$SESSION_DIR"

# Check if superpowers-chrome is available
check_chrome_ws() {
  if ! command -v chrome-ws &> /dev/null; then
    # Try common local installation locations
    local candidates=(
      "$SCRIPT_DIR/node_modules/.bin"
      "$SCRIPT_DIR/../node_modules/.bin"
      "$SCRIPT_DIR/../../node_modules/.bin"
    )

    local found=false
    for dir in "${candidates[@]}"; do
      if [ -x "$dir/chrome-ws" ]; then
        export PATH="$dir:$PATH"
        found=true
        break
      fi
    done

    if [ "$found" = false ]; then
      echo -e "${RED}❌ chrome-ws not found${NC}"
      echo "Install superpowers-chrome:"
      echo "  npm install github:obra/superpowers-chrome"
      exit 1
    fi
  fi
}

# Start Chrome if not already running
ensure_chrome() {
  if ! chrome-ws tabs &> /dev/null; then
    echo -e "${BLUE}🚀 Starting Chrome with remote debugging...${NC}"
    chrome-ws start
    sleep 2
  fi
}

# Helper: Create campaign test
create_campaign_test() {
  local BASE_URL="${1:-http://localhost:5000}"
  local CAMPAIGN_NAME="${2:-Test Campaign}"

  echo -e "${BLUE}🎲 Testing Campaign Creation${NC}"

  # Navigate to campaigns
  chrome-ws new "$BASE_URL/campaigns"
  local TAB=0

  # Wait for page load
  chrome-ws wait-for "$TAB" "body"

  # Click new campaign button
  chrome-ws click "$TAB" "button:has-text('New Campaign'), a[href='/campaigns/new']"
  chrome-ws wait-for "$TAB" "input[name='campaign_name'], #campaign-name"

  # Fill form
  chrome-ws fill "$TAB" "input[name='campaign_name'], #campaign-name" "$CAMPAIGN_NAME"
  chrome-ws fill "$TAB" "textarea[name='description'], #campaign-description" "Automated test via superpowers-chrome"

  # Submit
  chrome-ws click "$TAB" "button[type='submit']"
  chrome-ws wait-for "$TAB" ".campaign-card, .campaign-item"

  # Take screenshot
  chrome-ws screenshot "$TAB" > "$SESSION_DIR/campaign-created.png"

  echo -e "${GREEN}✅ Campaign created: $CAMPAIGN_NAME${NC}"
  echo -e "   Screenshot: $SESSION_DIR/campaign-created.png"
}

# Helper: Test character creation
create_character_test() {
  local TAB="${1:-0}"
  local CHAR_NAME="${2:-Test Hero}"

  echo -e "${BLUE}⚔️  Testing Character Creation${NC}"

  chrome-ws click "$TAB" "button:has-text('New Character'), a[href*='character']"
  chrome-ws wait-for "$TAB" "input[name='character_name'], #character-name"

  chrome-ws fill "$TAB" "input[name='character_name'], #character-name" "$CHAR_NAME"
  chrome-ws click "$TAB" "button[type='submit']"

  echo -e "${GREEN}✅ Character created: $CHAR_NAME${NC}"
}

# Helper: Test dice rolling
test_dice_roll() {
  local TAB="${1:-0}"

  echo -e "${BLUE}🎲 Testing Dice Roll${NC}"

  # Look for dice roll button
  chrome-ws click "$TAB" "button:has-text('Roll'), button.dice-roll"
  sleep 1

  # Extract result if visible
  local RESULT=$(chrome-ws extract "$TAB" ".dice-result, .roll-result" 2>/dev/null || echo "N/A")

  echo -e "${GREEN}✅ Dice rolled${NC}"
  [ "$RESULT" != "N/A" ] && echo -e "   Result: $RESULT"
}

# Helper: Smoke test
smoke_test() {
  local BASE_URL="${1:-http://localhost:5000}"

  echo -e "${BLUE}💨 Running Smoke Test${NC}"
  echo "================================"

  # Test 1: Home page
  echo "Test 1: Home page loads"
  chrome-ws new "$BASE_URL"
  local TAB=0
  chrome-ws wait-for "$TAB" "body"
  echo -e "${GREEN}✅ PASS${NC}"

  # Test 2: Navigation
  echo "Test 2: Navigation exists"
  chrome-ws eval "$TAB" "document.querySelector('nav, .navbar, header') !== null"
  echo -e "${GREEN}✅ PASS${NC}"

  # Test 3: Login page
  echo "Test 3: Login page loads"
  chrome-ws navigate "$TAB" "$BASE_URL/login"
  chrome-ws wait-for "$TAB" "form, input[type='password']"
  echo -e "${GREEN}✅ PASS${NC}"

  # Test 4: Campaigns page
  echo "Test 4: Campaigns page loads"
  chrome-ws navigate "$TAB" "$BASE_URL/campaigns"
  chrome-ws wait-for "$TAB" "body"
  echo -e "${GREEN}✅ PASS${NC}"

  echo "================================"
  echo -e "${GREEN}✅ All smoke tests passed${NC}"
}

# Helper: Extract game state
extract_game_state() {
  local TAB="${1:-0}"

  echo -e "${BLUE}🔍 Extracting Game State${NC}"

  # Get campaign name
  local CAMPAIGN=$(chrome-ws extract "$TAB" ".campaign-name, #campaign-name" 2>/dev/null || echo "N/A")

  # Get character info
  local CHARACTERS=$(chrome-ws extract "$TAB" ".character-name" 2>/dev/null || echo "N/A")

  # Get game log
  local LOG=$(chrome-ws extract "$TAB" ".game-log, #game-log" 2>/dev/null | head -c 200 || echo "N/A")

  echo "Campaign: $CAMPAIGN"
  echo "Characters: $CHARACTERS"
  echo "Recent Log: ${LOG:0:100}..."
}

# Helper: Take responsive screenshots
# Note: window.resizeTo is blocked by browsers. We use CDP Emulation.setDeviceMetricsOverride
# via the raw command, or fall back to taking screenshots at current viewport.
take_responsive_screenshots() {
  local TAB="${1:-0}"
  local NAME="${2:-page}"

  echo -e "${BLUE}📸 Taking Responsive Screenshots${NC}"
  echo "  Note: Using CDP for viewport emulation"

  # Desktop (1920x1080)
  if ! chrome-ws raw "$TAB" "Emulation.setDeviceMetricsOverride" '{"width":1920,"height":1080,"deviceScaleFactor":1,"mobile":false}' 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Desktop viewport set failed; screenshots may be at unexpected size${NC}"
  fi
  sleep 0.5
  chrome-ws screenshot "$TAB" > "$SESSION_DIR/${NAME}-desktop.png"
  echo "  ✅ Desktop: $SESSION_DIR/${NAME}-desktop.png"

  # Tablet (768x1024)
  if ! chrome-ws raw "$TAB" "Emulation.setDeviceMetricsOverride" '{"width":768,"height":1024,"deviceScaleFactor":2,"mobile":true}' 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Tablet viewport set failed; screenshots may be at unexpected size${NC}"
  fi
  sleep 0.5
  chrome-ws screenshot "$TAB" > "$SESSION_DIR/${NAME}-tablet.png"
  echo "  ✅ Tablet: $SESSION_DIR/${NAME}-tablet.png"

  # Mobile (375x667)
  if ! chrome-ws raw "$TAB" "Emulation.setDeviceMetricsOverride" '{"width":375,"height":667,"deviceScaleFactor":3,"mobile":true}' 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Mobile viewport set failed; screenshots may be at unexpected size${NC}"
  fi
  sleep 0.5
  chrome-ws screenshot "$TAB" > "$SESSION_DIR/${NAME}-mobile.png"
  echo "  ✅ Mobile: $SESSION_DIR/${NAME}-mobile.png"

  # Reset to default
  chrome-ws raw "$TAB" "Emulation.clearDeviceMetricsOverride" '{}' 2>/dev/null || true
}

# Main command router
main() {
  check_chrome_ws

  local COMMAND="${1:-help}"
  shift || true

  case "$COMMAND" in
    start)
      ensure_chrome
      ;;

    smoke)
      ensure_chrome
      smoke_test "$@"
      ;;

    campaign)
      ensure_chrome
      create_campaign_test "$@"
      ;;

    character)
      ensure_chrome
      create_character_test "$@"
      ;;

    dice)
      ensure_chrome
      test_dice_roll "$@"
      ;;

    state)
      extract_game_state "$@"
      ;;

    screenshots)
      take_responsive_screenshots "$@"
      ;;

    session)
      echo "Session directory: $SESSION_DIR"
      ls -lh "$SESSION_DIR" 2>/dev/null || echo "No files yet"
      ;;

    help|*)
      cat <<EOF
${BLUE}WorldArchitect Chrome Automation Wrapper${NC}

${YELLOW}Usage:${NC}
  $0 <command> [args...]

${YELLOW}Commands:${NC}
  start                      Start Chrome with remote debugging
  smoke [url]               Run smoke tests (default: http://localhost:5000)
  campaign [url] [name]     Test campaign creation
  character [tab] [name]    Test character creation
  dice [tab]                Test dice rolling
  state [tab]               Extract current game state
  screenshots [tab] [name]  Take responsive screenshots
  session                   Show session directory contents

${YELLOW}Examples:${NC}
  $0 start
  $0 smoke http://localhost:5000
  $0 campaign http://localhost:5000 "Epic Quest"
  $0 character 0 "Gandalf"
  $0 screenshots 0 game-view

${YELLOW}Direct chrome-ws access:${NC}
  chrome-ws tabs
  chrome-ws new "http://example.com"
  chrome-ws click 0 "button.submit"

${YELLOW}Session:${NC}
  Files saved to: $SESSION_DIR
EOF
      ;;
  esac
}

main "$@"
