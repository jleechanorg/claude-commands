# Dynamic World State UI Mockups

This directory contains interactive HTML/CSS mockups for the Dynamic World State feature of WorldArchitect.AI.

## Viewing the Mockups

1. Open `index.html` in a web browser to see the mockup directory
2. Click on individual mockups to explore each UI component

## Mockup Components

### 1. Timeline View (`timeline_view.html`)
- Interactive campaign timeline showing events across sessions
- Visual representation of world state changes
- Event tooltips with cascading consequences
- Zoomable interface for different time scales

### 2. NPC Relationships (`relationships.html`)
- Network graph visualization of NPC relationships
- Trust meters and relationship status indicators
- Faction standing displays
- Recent relationship change timeline

### 3. In-Game Panel (`ingame_panel.html`)
- Collapsible side panel for gameplay
- Minimal, non-intrusive design
- Recent events feed
- Active world effects display
- Mobile-responsive bottom bar variant

### 4. Session Recap (`session_recap.html`)
- Post-session summary screen
- Key moments highlighting
- World impact visualization with Chart.js
- Cascading consequences flow diagram
- Social sharing preview

## Technical Details

### CSS Architecture
- `styles.css` - Common styles and design tokens
- `relationships.css` - Relationship graph specific styles
- `ingame.css` - In-game panel styles
- `recap.css` - Session recap styles

### Design System
- **Colors**: Primary (#6366f1), Secondary (#8b5cf6), Success (#10b981), Danger (#ef4444)
- **Typography**: System font stack for optimal readability
- **Spacing**: 8px grid system
- **Shadows**: Consistent elevation system

### Responsive Breakpoints
- Mobile: < 768px
- Tablet: 768px - 1024px
- Desktop: > 1024px

## Implementation Notes

### Frontend Technologies
- **React/Vue** for component architecture
- **D3.js** for timeline and data visualizations
- **React Flow** for relationship graphs
- **Chart.js** for impact metrics
- **Framer Motion** for animations
- **WebSocket** for real-time updates

### Performance Considerations
- Virtual scrolling for long event lists
- Progressive data loading
- Client-side caching for visualizations
- Lazy loading for off-screen components

### Accessibility
- ARIA labels for interactive elements
- Keyboard navigation support
- High contrast mode compatibility
- Screen reader announcements for updates

## Next Steps

1. Convert static mockups to React components
2. Implement D3.js visualizations
3. Add WebSocket integration for real-time updates
4. Create unit tests for UI components
5. Implement progressive disclosure for free/premium features

## File Structure
```
dynamic_world_state/
├── index.html           # Mockup directory
├── timeline_view.html   # Campaign timeline
├── relationships.html   # NPC relationship graph
├── ingame_panel.html    # In-game side panel
├── session_recap.html   # Post-session summary
├── styles.css          # Common styles
├── relationships.css   # Graph-specific styles
├── ingame.css         # Panel-specific styles
├── recap.css          # Recap-specific styles
└── README.md          # This file
```