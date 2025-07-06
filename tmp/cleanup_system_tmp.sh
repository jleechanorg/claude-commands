#!/bin/bash
# Script to identify WorldArchitect.AI files in system /tmp that should be cleaned up

echo "WorldArchitect.AI files found in system /tmp:"
echo "============================================"

echo -e "\n1. Combat/Debug logs:"
ls -la /tmp/combat* /tmp/test_combat* 2>/dev/null || echo "None found"

echo -e "\n2. World files (should be in mvp_site/world/):"
ls -la /tmp/world_assiah* 2>/dev/null || echo "None found"

echo -e "\n3. Campaign exports:"
ls -la /tmp/campaign_exports/ 2>/dev/null || echo "None found"

echo -e "\n4. Monitored server logs:"
ls -la /tmp/monitored_server.log 2>/dev/null || echo "None found"

echo -e "\nTo clean up, run:"
echo "rm -f /tmp/combat* /tmp/test_combat* /tmp/world_assiah* /tmp/monitored_server.log"
echo "rm -rf /tmp/campaign_exports"

echo -e "\nNOTE: Going forward, use project tmp/ directory instead of system /tmp/"