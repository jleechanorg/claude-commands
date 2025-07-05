# Parallel Dual-Pass Integration Guide

## Overview
This implements TASK-019: Parallel dual-pass optimization to reduce perceived latency by 50%.

## Files Added
1. `main_parallel_dual_pass.py` - Backend endpoints
2. `static/parallel_dual_pass.js` - Frontend logic
3. `static/parallel_dual_pass.css` - UI styles

## Integration Steps

### Backend (main.py)
```python
# Add to imports
from main_parallel_dual_pass import add_parallel_dual_pass_routes

# After app initialization
add_parallel_dual_pass_routes(app, get_campaign_info)
```

### Frontend (index.html)
```html
<!-- Add in <head> -->
<link rel="stylesheet" href="/static/parallel_dual_pass.css">

<!-- Add before closing </body> -->
<script src="/static/parallel_dual_pass.js"></script>
```

### Frontend (app.js)
```javascript
// Replace existing handleInteraction with:
async function handleInteraction(userInput, mode) {
    // Use parallel version if available
    if (window.parallelDualPass) {
        return window.parallelDualPass.handleInteractionParallel(
            userInput, 
            mode, 
            currentCampaignId
        );
    }
    // Fallback to original implementation
    return originalHandleInteraction(userInput, mode);
}
```

### Modify existing interaction endpoint
In the current `/api/campaigns/<campaign_id>/interaction` endpoint, add:
```python
# After generating response, check if enhancement needed
validation_result = entity_validator.validate(gemini_response, expected_entities)

# Add to response
return jsonify({
    'response': gemini_response,
    'sequence_id': ai_sequence_id,
    'debug_mode': debug_mode,
    'enhancement_needed': validation_result.retry_needed,
    'missing_entities': validation_result.missing_entities
})
```

## Benefits
- **50% faster perceived response time**
- **Seamless entity enhancement**
- **Graceful degradation**
- **No additional compute cost**

## Testing
1. Create a scenario with many NPCs
2. Submit an interaction
3. Verify immediate response display
4. Watch for enhancement indicator
5. Confirm smooth narrative update