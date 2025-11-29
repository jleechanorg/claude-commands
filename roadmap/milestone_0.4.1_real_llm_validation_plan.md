# Milestone 0.4.1: Real LLM Integration Plan

## Overview
Add real Gemini API integration to the Milestone 0.4 test framework to validate results with actual LLM responses.

## Key Learnings from Existing Code
From `mvp_site/llm_service.py`:
- Uses `google.genai` SDK (not `google.generativeai`)
- Models: `gemini-2.5-flash` (default), `gemini-2.5-pro` (large), `gemini-1.5-flash` (test)
- Safety settings configured to BLOCK_NONE
- Uses `TESTING=true` environment variable for model selection

## Phase 1: Environment Setup (0.5 days)

### Step 1.1: API Configuration
- [ ] Create `prototype/tests/milestone_0.4/config.py`
  - API key management from `GOOGLE_API_KEY` or `GEMINI_API_KEY` env var
  - Add explicit check and setup instructions
  - Model selection (use TEST_MODEL for cost, but consider DEFAULT_MODEL test)
  - Safety settings matching production
  - Timeout configuration (30s max)

### Step 1.2: Dependencies
- [ ] Update requirements or check if google-genai is available
- [ ] Create setup script for API credentials
- [ ] Document cost expectations

## Phase 2: Gemini Service Wrapper (1 day)

### Step 2.1: Create Real API Client
- [ ] Create `prototype/tests/milestone_0.4/gemini_client.py`
  - Wrap google.genai.Client()
  - Handle authentication with proper error messages
  - Implement retry logic with exponential backoff
  - Add rate limiting
  - Handle specific errors:
    ```python
    # google.genai.errors.QuotaExceededError
    # google.genai.errors.InvalidRequestError
    # google.genai.errors.AuthenticationError
    ```

### Step 2.2: Response Parsing
- [ ] Parse structured responses (JSON/XML)
- [ ] Handle malformed responses with fallback strategies:
  - Try JSON first, then regex extraction
  - Multiple parsing attempts
  - Default to plain text extraction
- [ ] Extract narrative text
- [ ] Log API calls (sanitized, no sensitive data)

### Step 2.3: Cost Tracking
- [ ] Count actual tokens using API response
- [ ] Calculate real costs with model-specific pricing
- [ ] Add budget limits with hard stop:
  ```python
  if total_cost >= 0.80:  # 80% of budget
      logger.warning("Approaching budget limit, stopping tests")
      break
  ```
- [ ] Generate cost report
- [ ] Track token usage variance from estimates

## Phase 3: Test Framework Integration (1 day)

### Step 3.1: Update Test Harness
- [ ] Add `use_real_api` flag to TestHarness
- [ ] Create `_generate_real_narrative()` method
- [ ] Keep mock as fallback option
- [ ] Add API error handling

### Step 3.2: Prompt Integration
- [ ] Use prompt_templates.py templates
- [ ] Add system instructions for each approach
- [ ] Include personality/style guidance
- [ ] Test prompt token counts

### Step 3.3: Modify Test Approaches
```python
def _run_validation_only_real(self, campaign_id, scenario):
    # Use baseline prompt
    # Call real Gemini API
    # Validate with NarrativeSyncValidator

def _run_pydantic_only_real(self, campaign_id, scenario):
    # Use structured prompt with manifest
    # Call real Gemini API
    # Parse structured response

def _run_combined_real(self, campaign_id, scenario):
    # Use structured prompt + validation hints
    # Call real Gemini API
    # Validate response
```

## Phase 4: Limited Test Suite (0.5 days)

### Step 4.1: Sampling Strategy
- [ ] Select 2 campaigns with criteria:
  - Sariel (required - real data)
  - One with highest mock desync rate
- [ ] Select 3 scenarios based on:
  - multi_character (baseline complexity)
  - Worst performing from mock tests
  - Most complex (npc_heavy or combat)
- [ ] Total: 6 tests per approach = 18 API calls

### Step 4.2: Create Test Runners
- [ ] `run_real_baseline_tests.py` - Limited set
- [ ] `run_real_pydantic_tests.py` - Limited set
- [ ] `run_real_combined_tests.py` - Limited set
- [ ] `run_real_comparison.py` - All 3 approaches

### Step 4.3: Safety Controls
- [ ] Max budget: $1.00
- [ ] Dry run mode
- [ ] Confirmation before running
- [ ] Emergency stop capability
- [ ] Pre-flight checklist:
  ```markdown
  - [ ] API key configured and tested
  - [ ] Budget alerts set up
  - [ ] Backup of current test results
  - [ ] Dry run with 1 API call
  - [ ] Success rate calculation bug fixed
  ```

## Phase 5: Analysis & Reporting (0.5 days)

### Step 5.1: Real vs Mock Comparison
- [ ] Compare success rates
- [ ] Analyze response patterns
- [ ] Document unexpected behaviors
- [ ] Validate mock accuracy

### Step 5.2: Cost-Benefit Analysis
- [ ] Actual costs per approach
- [ ] Token usage patterns
- [ ] Performance metrics (p50, p95, p99)
- [ ] ROI calculation
- [ ] Prompt compliance rate analysis
- [ ] Temperature testing (0.7 vs 0.9)

### Step 5.3: Final Report
- [ ] Update `approach_comparison.md` with real results
- [ ] Create `real_llm_validation.md` report
- [ ] Document any surprises
- [ ] Recommendations for production

## Implementation Order

1. **Start Small**: Single test with real API
2. **Validate Setup**: Ensure auth, parsing, costs work
3. **Run Limited Suite**: 18 total API calls
4. **Analyze Results**: Compare to mock predictions
5. **Document Findings**: Update reports

## Risk Mitigation

1. **Cost Control**:
   - Use TEST_MODEL (gemini-1.5-flash)
   - Limit to 18 API calls
   - Set hard budget limit with 80% warning
   - Monitor in real-time
   - Consider 1-2 DEFAULT_MODEL tests for comparison

2. **API Failures**:
   - Implement exponential backoff
   - Cache successful responses
   - Fallback to mock on errors
   - Log all failures

3. **Response Quality**:
   - May need prompt tuning
   - Handle non-compliant responses
   - Multiple attempts if needed

4. **Security Considerations**:
   - Never commit API keys - use .env file
   - Add .env to .gitignore
   - Sanitize all prompts before sending
   - Don't log full responses (may contain game data)
   - Use structured logging with PII filtering

## Success Criteria

1. **Technical Success**:
   - Real API integration working
   - All 3 approaches tested
   - Costs under $1.00
   - No API errors

2. **Validation Success**:
   - Real results match mock trends
   - Combined approach still best
   - Structured prompts help
   - Entity tracking improves

3. **Documentation Success**:
   - Clear setup instructions
   - Reproducible results
   - Cost transparency
   - Production readiness

## Next Steps After Completion

1. **Production Integration**:
   - Port validated approach to llm_service.py
   - Add to game_state.py narrative generation
   - Enable for all campaigns

2. **Monitoring**:
   - Track entity mention rates
   - Monitor API costs
   - Collect user feedback
   - Iterate on prompts

3. **Optimization**:
   - Cache common patterns
   - Batch API calls
   - Optimize prompt length
   - Reduce token usage

## Estimated Timeline

- Phase 1: 4 hours (setup)
- Phase 2: 8 hours (API wrapper)
- Phase 3: 8 hours (integration)
- Phase 4: 4 hours (testing)
- Phase 5: 4 hours (analysis)

**Total: 28 hours (3.5 days)**

## Budget Estimate

- 18 API calls × ~500 tokens each = 9,000 tokens
- Using gemini-1.5-flash: ~$0.00035/1K tokens
- Estimated cost: $0.01 - $0.10
- Budget limit: $1.00 (10x safety margin)

## Critical Bug Fix Required

**BEFORE RUNNING ANY TESTS**, fix the success rate calculation bug:

```python
# Current (BROKEN):
@property
def success_rate(self) -> float:
    if not self.entities_expected:
        return 1.0
    found_count = len(self.entities_found) if self.entities_found else 0
    expected_count = len(self.entities_expected)
    return found_count / expected_count if expected_count > 0 else 0

# Should be:
@property
def success_rate(self) -> float:
    if not self.entities_expected:
        return 1.0
    # When validation works perfectly, both lists are empty
    if not self.entities_found and not self.entities_missing:
        return 1.0 if self.entities_expected else 0.0
    # Otherwise calculate based on what was found
    found_count = len(self.entities_expected) - len(self.entities_missing)
    return found_count / len(self.entities_expected)
```

This bug makes the combined approach appear to have 0% success when it actually has 100%.
