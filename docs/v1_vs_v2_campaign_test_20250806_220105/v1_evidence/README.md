# V1 Evidence Collection Directory

**Purpose**: Screenshots and evidence from V1 (Flask) campaign creation testing

## Expected Evidence Types

### Authentication & Landing
- Unauthenticated landing page state
- Authenticated user dashboard
- Login/logout flows

### Campaign Creation Workflow
- Step 1: Campaign basics (name, type selection)
- Step 2: AI style configuration  
- Step 3: Launch confirmation
- Post-creation: Planning block display

### API Integration Evidence
- Console network logs
- API response data
- Error handling flows
- Success confirmations

### User Experience Evidence  
- Loading states
- Transition animations
- Form validation
- Success/error messages

## File Naming Convention
`v1_{feature}_{step}_{variant}_{timestamp}.png`

Examples:
- `v1_landing_page_unauthenticated_20250806_220105.png`
- `v1_campaign_creation_step1_basics_20250806_220105.png`
- `v1_planning_block_dragon_knight_success_20250806_220105.png`

## Path Label Format
Include navigation context in screenshot descriptions:
- "V1: Landing → Authenticated Dashboard"
- "V1: Campaign Creation → Step 1 → Dragon Knight Selected"
- "V1: Post-Creation → Planning Block Visible"