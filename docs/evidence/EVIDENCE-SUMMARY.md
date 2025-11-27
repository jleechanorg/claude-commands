# Gemini 2.5 Compatibility Fix - Evidence Summary

## Problem
All 30 parallel campaign creation requests failed (0% success) with error:
```
"Tool use with a response mime type: 'application/json' is unsupported"
```

## Root Cause
Test user `jleechantest@gmail.com` had `gemini-2.5-flash` in settings.
Gemini 2.5 models do NOT support `code_execution` + JSON response mode together.

## Fix Applied
1. Removed Gemini 2.5 models from `ALLOWED_GEMINI_MODELS` in `constants.py`
2. Added auto-redirect mappings for legacy users (2.5 → gemini-3-pro-preview)
3. Updated all UI components and test fixtures

## Files Modified
- mvp_site/constants.py
- mvp_site/templates/settings.html
- mvp_site/frontend_v2/src/pages/SettingsPage.tsx
- mvp_site/frontend_v1/js/settings.js
- mvp_site/world_logic.py
- mvp_site/gemini_response.py
- Multiple test files

## Test Results

### Before Fix (2-minute timeout)
- **Success Rate**: 0% (0/30)
- **Error**: "Tool use with response mime type: 'application/json' is unsupported"
- **Wall Time**: 4.84s

### After Fix (2-minute timeout)
- **Success Rate**: 86.7% (26/30)
- **Failures**: 4 client-side timeouts (expected under heavy load)
- **Wall Time**: 120.46s

### After Fix (10-minute timeout)
- **Success Rate**: 100% (30/30)
- **Failures**: 0
- **Wall Time**: 141.00s (2.4 min)
- **Average request time**: 65.5s

## True Parallelism Analysis

### Client-Side Timing Evidence
| Metric | Value |
|--------|-------|
| Total requests | 30 |
| Wall time | 141.0s |
| If serial (sum of durations) | 1965.2s |
| **Parallelism factor** | **13.9x speedup** |
| Parallelism efficiency | 92.8% overlap |
| Wall/Max ratio | 1.00x (1.0 = perfect parallelism) |

### Request Duration Distribution
```
 20- 40s: # (1)
 40- 60s: ################## (18)
 60- 80s: # (1)
 80-100s: ####### (7)
100-120s: # (1)
140-160s: ## (2)
```

### Verdict: TRUE PARALLELISM CONFIRMED
- 30 requests completed in 141.0s
- Would take 1965.2s (32.8 min) if serial
- Wall time equals max request duration (proves all requests ran concurrently)
- ThreadPoolExecutor successfully parallelizes Firestore I/O

## Conclusion
The Gemini 2.5 model compatibility issue is **fully resolved**.
All 30 parallel campaign creation requests now succeed when given adequate timeout.

## Deployed
Commit `73af9085` deployed to:

| Environment | URL | Description |
|-------------|-----|-------------|
| **PR #2116 Preview (s9)** | https://mvp-site-app-s9-i6xf2p72ka-uc.a.run.app | Primary validation target |
| DEV | https://mvp-site-app-dev-i6xf2p72ka-uc.a.run.app | Backup/secondary |

**Note**: s9 IS the PR preview server (from rotating pool). The fix is deployed to both environments.

## Evidence Files
- `parallel_write_30_10min.json` - Detailed test results with 30/30 success
- `parallel_write_30_fixed.json` - 2-min timeout test (26/30, 4 timeouts)
- `parallelism_analysis.json` - True parallelism analysis metrics
- `campaign_timestamp_analysis.json` - Server-side campaign timestamps
- `EVIDENCE-SUMMARY.md` - This summary
