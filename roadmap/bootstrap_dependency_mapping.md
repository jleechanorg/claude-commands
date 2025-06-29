# Bootstrap Dependency Mapping Document

## Overview
This document maps all Bootstrap classes currently used in WorldArchitect.AI to their modern CSS replacements as part of the frontend modernization effort.

## Bootstrap Class Usage Analysis

### Layout & Grid System
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `container` | base.css:2, style.css | CSS Grid container with max-width |
| `container-fluid` | index.html | Full-width container with padding |
| `row` | style.css:multiple | CSS Grid or Flexbox row |
| `col-*` | Not found in scan | N/A - No column classes in use |

### Navigation Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `navbar` | style.css:46-73 | Custom nav with flexbox |
| `navbar-expand-lg` | index.html | Media query for responsive nav |
| `navbar-dark` | index.html | CSS custom properties for theming |
| `navbar-brand` | style.css:50, themes | Custom logo/brand styling |
| `navbar-nav` | style.css:54 | Flexbox nav list |
| `nav-link` | style.css:58 | Custom link styling |
| `navbar-toggler` | style.css:66 | Custom hamburger menu |
| `navbar-toggler-icon` | style.css:70 | SVG or CSS hamburger icon |

### Dropdown Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `dropdown` | style.css:76 | Custom dropdown container |
| `dropdown-toggle` | style.css:80 | Custom toggle button |
| `dropdown-menu` | style.css:84-104 | Custom menu with positioning |
| `dropdown-item` | style.css:108-122 | Custom menu item styling |
| `dropdown-header` | style.css:126 | Custom header styling |
| `dropdown-divider` | style.css:131 | HR or border styling |

### Modal Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `modal` | style.css:136 | Custom modal with backdrop |
| `modal-dialog` | style.css:140 | Centered dialog container |
| `modal-content` | style.css:144 | Modal box styling |
| `modal-header` | style.css:148 | Header section flexbox |
| `modal-title` | style.css:152 | Custom title styling |
| `modal-body` | style.css:156 | Body section with padding |
| `modal-footer` | style.css:160 | Footer section flexbox |

### Form Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `form-control` | style.css:164-178 | Custom input styling |
| `form-label` | style.css:182 | Custom label styling |
| `form-text` | style.css:186 | Helper text styling |
| `form-select` | style.css:190 | Custom select styling |
| `form-check` | style.css:194 | Custom checkbox/radio container |
| `form-check-input` | style.css:198 | Custom checkbox/radio input |
| `form-check-label` | style.css:202 | Custom checkbox/radio label |

### List Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `list-group` | style.css:206 | Custom list container |
| `list-group-item` | style.css:210-221 | Custom list item styling |
| `list-group-item-action` | style.css:224 | Interactive list item |

### Button Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `btn` | base.css:83-102 | Custom button base class |
| `btn-primary` | base.css:96 | Primary button variant |
| `btn-secondary` | base.css:100 | Secondary button variant |
| `btn-success` | Referenced | Success button variant |
| `btn-danger` | Referenced | Danger button variant |
| `btn-sm` | style.css | Small button modifier |
| `btn-lg` | Referenced | Large button modifier |

### Alert Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `alert` | style.css:228 | Custom alert container |
| `alert-danger` | style.css:232 | Danger alert variant |
| `alert-warning` | style.css:236 | Warning alert variant |
| `alert-success` | style.css:240 | Success alert variant |
| `alert-info` | style.css:244 | Info alert variant |

### Badge Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `badge` | style.css:248 | Custom badge styling |
| `badge-primary` | style.css:252 | Primary badge variant |
| `badge-secondary` | style.css:256 | Secondary badge variant |

### Card Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `card` | style.css:260 | Custom card container |
| `card-header` | style.css:264 | Card header section |
| `card-body` | style.css:268 | Card body section |
| `card-footer` | style.css:272 | Card footer section |
| `card-title` | style.css:276 | Card title styling |
| `card-text` | style.css:280 | Card text styling |

### Table Components
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `table` | style.css:284 | Custom table styling |
| `table-striped` | style.css:288 | Alternating row colors |
| `table-hover` | style.css:292 | Row hover effects |
| `table-bordered` | style.css:296 | Table borders |

### Utility Classes
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `text-center` | style.css, base.css | `text-align: center` |
| `text-white` | style.css | `color: white` |
| `text-muted` | style.css | `color: var(--text-secondary)` |
| `bg-dark` | style.css | `background: var(--primary-bg)` |
| `bg-light` | style.css | `background: var(--secondary-bg)` |
| `border` | style.css | `border: 1px solid var(--border-color)` |
| `border-0` | style.css | `border: none` |
| `rounded` | style.css | `border-radius: var(--radius)` |
| `rounded-circle` | style.css | `border-radius: 50%` |
| `shadow` | style.css | Custom box-shadow |
| `shadow-sm` | style.css | Small box-shadow |

### Spacing Utilities
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `p-0` to `p-5` | style.css | CSS custom properties for padding |
| `m-0` to `m-5` | style.css | CSS custom properties for margin |
| `mt-*`, `mb-*`, `ms-*`, `me-*` | style.css | Directional spacing utilities |

### Display Utilities
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `d-none` | style.css | `display: none` |
| `d-block` | style.css | `display: block` |
| `d-flex` | style.css | `display: flex` |
| `d-inline` | style.css | `display: inline` |
| `d-inline-block` | style.css | `display: inline-block` |

### Flexbox Utilities
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `flex-row` | style.css | `flex-direction: row` |
| `flex-column` | style.css | `flex-direction: column` |
| `justify-content-center` | style.css | `justify-content: center` |
| `justify-content-between` | style.css | `justify-content: space-between` |
| `align-items-center` | style.css | `align-items: center` |

### Width/Height Utilities
| Bootstrap Class | Usage Location | Modern CSS Replacement |
|----------------|----------------|----------------------|
| `w-25`, `w-50`, `w-75`, `w-100` | style.css | Width percentage utilities |
| `h-25`, `h-50`, `h-75`, `h-100` | style.css | Height percentage utilities |

## Migration Strategy

### Phase 1: Core Component Replacement (High Priority)
1. **Navigation System** - Replace navbar classes with custom flexbox navigation
2. **Form Controls** - Implement custom form styling system
3. **Modals** - Create custom modal implementation with CSS animations
4. **Buttons** - Design custom button system with CSS variables

### Phase 2: Layout System (Medium Priority)
1. **Grid System** - Implement CSS Grid-based layout system
2. **Cards** - Create custom card components with modern styling
3. **Lists** - Design custom list components

### Phase 3: Utilities Migration (Low Priority)
1. **Spacing System** - Create CSS custom properties for consistent spacing
2. **Display Utilities** - Implement utility classes with modern naming
3. **Color System** - Migrate to CSS variables for all colors

## CSS Custom Properties Foundation

```css
:root {
  /* Spacing Scale */
  --space-0: 0;
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 1rem;
  --space-4: 1.5rem;
  --space-5: 3rem;
  
  /* Border Radius */
  --radius-sm: 0.25rem;
  --radius: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-full: 9999px;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
  
  /* Breakpoints */
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 992px;
  --breakpoint-xl: 1200px;
}
```

## Implementation Notes

1. **Gradual Migration**: Use feature flags to enable new components progressively
2. **Backward Compatibility**: Maintain Bootstrap classes during transition period
3. **Testing**: Verify each component replacement maintains functionality
4. **Performance**: Ensure custom CSS is optimized and doesn't increase bundle size significantly

## Critical Dependencies

### Must Replace First
- Modal system (used for campaign creation and alerts)
- Form controls (essential for all user inputs)
- Navigation (core UI element)
- Buttons (used throughout application)

### Can Migrate Later
- Utility classes (can coexist with custom utilities)
- Card components (limited usage)
- Table styling (minimal usage)

## Risks and Mitigation

1. **Modal Functionality**: Bootstrap modals have JavaScript dependencies
   - Mitigation: Implement custom modal manager with similar API

2. **Form Validation**: Bootstrap provides validation styles
   - Mitigation: Create custom validation styling system

3. **Responsive Navigation**: Bootstrap's navbar collapse is complex
   - Mitigation: Implement simpler mobile menu with CSS/minimal JS

4. **Dropdown Menus**: Require positioning logic
   - Mitigation: Use CSS-only dropdowns where possible, minimal JS for complex cases