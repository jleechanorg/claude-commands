# Vulture Dead Code Analysis

This analysis was run after the initial dead code removal to verify our work.

## Command Used
```bash
./mvp_site/venv/bin/vulture mvp_site --min-confidence 90 --exclude="*/venv/*,*/tests/*,*/__pycache__/*,*/test_integration/*,*/mocks/*"
```

## Key Finding: Vulture Correctly Handles Callbacks

**`json_datetime_serializer` was NOT flagged as dead code!**

This confirms that vulture understands callback usage patterns and would have prevented our false positive. The function is used as:
```python
json.dumps(data, default=json_datetime_serializer)
```

## Additional Dead Code Found (All Unused Imports)

1. **mvp_site/gemini_service.py:25** - `unused import 'EntityManifest'` (90% confidence)
   - Imported as alias: `from entity_tracking import SceneManifest as EntityManifest`
   - Never used in the file

2. **mvp_site/main.py:3** - `unused import 'io'` (90% confidence)
   - The `io` module is imported but never used

3. **mvp_site/narrative_sync_validator.py:8** - `unused import 'Set'` (90% confidence)
   - `Set` from typing is imported but not used

4. **mvp_site/schemas/entities_pydantic.py:6** - `unused import 'Union'` (90% confidence)
   - `Union` from typing is imported but not used

5. **mvp_site/schemas/entities_simple.py:6** - `unused import 'Union'` (90% confidence)
   - `Union` from typing is imported but not used

## Comparison with Our Manual Analysis

### What We Caught That Vulture Didn't
- Backup files (`*_original.py`) - Vulture doesn't analyze file-level dead code
- Entire unused files (like `ai_token_discovery.py`) - Vulture analyzes within files, not between them
- Functions only used in tests - Vulture doesn't distinguish test-only usage

### What Vulture Caught That We Missed
- 5 unused imports that our grep-based approach didn't catch
- These are minor but still contribute to code cleanliness

## Conclusion

1. **Vulture would have prevented our false positive** - It correctly identifies `json_datetime_serializer` as used
2. **Vulture complements manual analysis** - It's better at finding unused imports and understanding callback patterns
3. **Manual analysis still needed** - For finding entire dead files and test-only functions
4. **Best approach**: Combine both methods for comprehensive dead code removal