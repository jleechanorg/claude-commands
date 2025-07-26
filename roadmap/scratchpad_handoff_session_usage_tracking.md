# Handoff Scratchpad: Session Usage Tracking

## Problem Statement
The current git-header.sh script shows API request rate limits (1000 requests) but user expects to see Claude Pro session limits (X out of 50 sessions per month). Need to implement session tracking that shows monthly usage in the expected format.

## Research Findings

### Claude Pro Session Limits (from web search)
- **Claude Pro ($20/month)**: ~45 messages every 5 hours
- **Claude Max ($200/month)**: ~900 messages every 5 hours
- **Max Plan Specific**: "50 sessions per month" guideline (flexible benchmark)
- **Session Definition**: 5-hour segments starting from first message

### API Headers Available
- `anthropic-ratelimit-requests-*` - Request-based rate limits
- `anthropic-ratelimit-tokens-*` - Token-based rate limits
- `anthropic-ratelimit-sessions` - Session tracking (mentioned but details unclear)
- `retry-after` - For 429 errors
- `anthropic-organization-id` - Organization ID

### Current Implementation Gap
The git-header.sh script only tracks:
- Request rate limits (1000 requests, resets hourly/daily)
- NOT session limits (50 sessions, resets monthly)

## Implementation Plan

### Phase 1: Research Session Headers
1. **Test Session Header**: Make API calls to check if `anthropic-ratelimit-sessions` exists
2. **Extract Session Data**: Parse session-related headers from API responses
3. **Document Header Format**: Determine if session limits are exposed via API

### Phase 2: Implement Session Tracking
1. **Modify git-header.sh**: Add session tracking alongside request tracking
2. **Create Session Parser**: Extract session count/limit/reset from headers
3. **Format Output**: Show "X/50 sessions (Y% remaining)" format
4. **Handle Fallbacks**: Graceful degradation if session headers unavailable

### Phase 3: Enhanced Display
1. **Dual Display**: Show both request limits AND session limits
2. **Priority Alerts**: Focus on session limits for monthly planning
3. **Reset Timing**: Show when session limits reset (monthly cycle)

### Phase 4: Testing & Validation
1. **Test Against Max Plan**: Verify 50 session limit detection
2. **Test Against Pro Plan**: Verify different session limits
3. **Edge Cases**: Handle missing headers, API errors, etc.

## Files to Modify

### Primary Files
- `claude_command_scripts/git-header.sh` - Main script to enhance

### Supporting Files
- `claude_command_scripts/session_tracker.sh` - New helper script (optional)
- `CLAUDE.md` - Update documentation about session tracking

## Technical Implementation Details

### API Call Enhancement
```bash
# Current API call (line 145-153)
response=$(curl -s -D /tmp/claude_headers.tmp https://api.anthropic.com/v1/messages \
  --header "x-api-key: $CLAUDE_API_KEY" \
  --header "anthropic-version: 2023-06-01" \
  --header "content-type: application/json" \
  --data '{"model": "claude-opus-4-20250514", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}')
```

### Header Parsing Addition
```bash
# Add after line 167
sessions_reset=$(grep -i 'anthropic-ratelimit-sessions-reset:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
sessions_remaining=$(grep -i 'anthropic-ratelimit-sessions-remaining:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
sessions_limit=$(grep -i 'anthropic-ratelimit-sessions-limit:' /tmp/claude_headers.tmp | cut -d' ' -f2- | tr -d '\r')
```

### Output Format Enhancement
```bash
# Current format (line 185)
echo "[API: ${requests_remaining:-?}/${requests_limit:-50} requests (${remaining_percent:-?}% remaining) | Reset: $(format_time "$requests_reset")]"

# Enhanced format
echo "[API: ${requests_remaining:-?}/${requests_limit:-1000} requests | Sessions: ${sessions_remaining:-?}/${sessions_limit:-50} (${session_percent:-?}% remaining)]"
echo "[Reset: Requests $(format_time "$requests_reset") | Sessions $(format_time "$sessions_reset")]"
```

## Testing Requirements

### Unit Tests
1. **Header Parsing**: Test extraction of session headers
2. **Fallback Handling**: Test behavior when headers missing
3. **Format Validation**: Test output format matches expected

### Integration Tests
1. **API Response**: Test with real API responses
2. **Different Plans**: Test Pro vs Max plan differences
3. **Edge Cases**: Test with expired sessions, API errors

### User Acceptance
1. **Expected Format**: User sees "X/50 sessions" as requested
2. **Accurate Data**: Session count reflects actual usage
3. **Reliable Updates**: Data refreshes correctly

## Success Criteria

### Primary Goals
- [ ] Display shows "X/50 sessions (Y% remaining)" format
- [ ] Session data comes from actual API headers
- [ ] Monthly reset timing is accurate
- [ ] Graceful fallback when session headers unavailable

### Secondary Goals
- [ ] Maintain existing request limit display
- [ ] Add session usage alerts/warnings
- [ ] Improve header caching efficiency
- [ ] Document session tracking approach

## Timeline Estimate
- **Research & Testing**: 2-3 hours
- **Implementation**: 2-4 hours
- **Testing & Validation**: 1-2 hours
- **Documentation**: 1 hour
- **Total**: 6-10 hours

## Key Considerations

### Technical Challenges
1. **Header Availability**: Session headers might not exist in API
2. **Plan Differences**: Pro vs Max plans have different limits
3. **Reset Timing**: Monthly vs hourly reset cycles
4. **Error Handling**: API failures, auth errors, etc.

### User Experience
1. **Information Density**: Balance detail vs readability
2. **Priority Display**: Sessions more important than requests
3. **Alert Thresholds**: When to warn about session usage

### Future Enhancements
1. **Usage History**: Track session consumption over time
2. **Predictive Alerts**: Warn before hitting monthly limits
3. **Plan Optimization**: Suggest plan changes based on usage

## Repository Context
- **Branch**: handoff-session-usage-tracking
- **Base**: dev1752770985
- **Working Directory**: /home/jleechan/projects/worldarchitect.ai/worktree_roadmap
- **Primary Script**: claude_command_scripts/git-header.sh (194 lines)

## Implementation Notes

### Current Script Analysis
The existing script successfully:
- ✅ Parses request-based rate limits
- ✅ Handles authentication errors
- ✅ Formats timestamps properly
- ✅ Provides percentage calculations
- ✅ Shows warning/alert mechanisms

### Required Enhancements
The script needs:
- 🔲 Session header parsing
- 🔲 Monthly reset handling
- 🔲 Session percentage calculations
- 🔲 Dual display format
- 🔲 Session-specific alerts

### Risk Mitigation
- **Fallback Display**: Show "sessions: unknown" if headers missing
- **Backward Compatibility**: Preserve existing request display
- **Error Handling**: Graceful degradation for API failures
- **Testing**: Thorough testing across different plan types
