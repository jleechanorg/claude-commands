# V1 vs V2 Campaign Testing Evidence Collection

**Directory**: `v1_vs_v2_campaign_test_20250806_220105/`
**Created**: 2025-08-06 22:01:05
**Purpose**: Organized collection of fresh test evidence comparing V1 (Flask) and V2 (React) campaign creation systems

## Directory Structure

### `/v1_evidence/`
Screenshots and evidence from V1 (Flask) campaign creation testing:
- Landing page authentication states
- Campaign creation workflow steps
- Post-creation planning blocks
- API response evidence
- Console output captures

### `/v2_evidence/`  
Screenshots and evidence from V2 (React) campaign creation testing:
- Dashboard states
- Campaign creation workflow steps  
- API integration evidence
- Error states and debugging info
- Console output captures

### `/comparison_matrix/`
Organized comparison evidence:
- Side-by-side workflow comparisons
- Feature parity analysis
- Gap identification screenshots
- Test matrix completion evidence

### `/archive/`
Temporary storage for intermediate testing artifacts

## Testing Methodology

This directory structure supports the **MANDATORY QUALITY ASSURANCE PROTOCOL**:

1. **Pre-Testing Checklist**: All user paths documented before testing
2. **Evidence Requirements**: Screenshot for each test matrix cell with path labels  
3. **Completion Validation**: Adversarial testing completed with proper evidence
4. **Evidence Standards**: Each ✅ claim backed by specific screenshot references

## File Naming Convention

- `{version}_{feature}_{step}_{variant}_{timestamp}.png`
- Examples:
  - `v1_campaign_creation_step1_dragon_knight_20250806_220105.png`
  - `v2_landing_auth_success_20250806_220105.png`
  - `comparison_planning_block_side_by_side_20250806_220105.png`

## Evidence Collection Standards

- All screenshots saved to filesystem (not inline chat)
- Clear path labels for navigation context
- Console logs captured for API interactions  
- Error states documented with full context
- Success flows verified with end-to-end data validation

This structure ensures systematic, verifiable evidence collection for V1 vs V2 parity validation.