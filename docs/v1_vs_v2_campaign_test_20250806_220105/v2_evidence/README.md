# V2 Evidence Collection Directory

**Purpose**: Screenshots and evidence from V2 (React) campaign creation testing

## Expected Evidence Types

### Dashboard & Navigation
- Initial dashboard state
- Campaign list display
- Navigation between sections
- Authentication states

### Campaign Creation Workflow
- Step 1: Campaign configuration
- Step 2: Advanced settings
- Step 3: Creation confirmation
- Post-creation: Expected vs actual behavior

### API Integration Evidence
- Network tab console logs
- API request/response data  
- Integration success/failure states
- Error handling and recovery

### React-Specific Evidence
- Component state updates
- Form validation behavior
- Loading states and transitions
- Error boundaries activation

## File Naming Convention
`v2_{feature}_{step}_{variant}_{timestamp}.png`

Examples:
- `v2_dashboard_initial_state_20250806_220105.png`
- `v2_campaign_creation_step1_form_20250806_220105.png`
- `v2_api_integration_success_response_20250806_220105.png`

## Path Label Format
Include React navigation context:
- "V2: Dashboard → Campaign Creation → Step 1"
- "V2: Creation Form → API Call → Success State"  
- "V2: Post-Creation → Expected Planning Block Location"

## Critical Evidence Areas
- Planning block integration (known gap)
- API response handling
- Form data persistence
- Error state management
- Navigation flow consistency