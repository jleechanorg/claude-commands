# WorldArchitect.AI Style Guide

This guide provides comprehensive styling conventions and design patterns for creating pages and components that match the WorldArchitect.AI aesthetic.

## 🎨 Design Philosophy

WorldArchitect.AI embraces a **fantasy-themed dark aesthetic** with rich purple gradients, magical lighting effects, and immersive visual storytelling. The design creates an epic, mystical atmosphere perfect for tabletop RPG adventures.

## 🌈 Color Palette & Theme System

### Primary Theme: Fantasy Dark
The application primarily uses a dark fantasy theme with the following characteristics:

```css
/* Main Background Gradient */
bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900

/* Magical Lighting Effects */
bg-purple-500/20 rounded-full blur-3xl animate-pulse
bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000
```

### Color Usage Guidelines

**Text Colors:**
- Primary text: `text-white`
- Secondary text: `text-purple-200`
- Tertiary text: `text-purple-300`
- Muted text: `text-purple-400`
- Success: `text-green-300`
- Warning: `text-yellow-300`
- Error: `text-red-300`

**Background Colors:**
- Page backgrounds: `bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900`
- Card backgrounds: `bg-black/60 backdrop-blur-sm`
- Overlay backgrounds: `bg-black/40`
- Selected states: `bg-purple-500/20`

**Border Colors:**
- Default borders: `border-purple-500/30`
- Hover borders: `border-purple-400/50`
- Active borders: `border-purple-400`
- Success borders: `border-green-500/30`

## 🃏 Card Component Patterns

### Standard Card
```jsx
<Card className="bg-black/60 backdrop-blur-sm border border-purple-500/30 hover:bg-black/70 transition-all duration-200">
  <CardContent className="p-4 md:p-6">
    {/* Content */}
  </CardContent>
</Card>
```

### Interactive Card (Clickable)
```jsx
<Card className="bg-black/60 backdrop-blur-sm border border-purple-500/30 hover:bg-black/70 hover:border-purple-400/50 transition-all duration-200 cursor-pointer">
```

### Selected/Active Card
```jsx
<Card className="bg-black/60 backdrop-blur-sm border-2 border-purple-400 bg-gradient-to-br from-purple-500/20 to-pink-600/20">
```

### Themed Feature Cards
Different themes for different features:
- **Narrative/World**: `from-cyan-500/20 to-blue-600/20 border-cyan-500/30`
- **Mechanics**: `from-purple-500/20 to-pink-600/20 border-purple-500/30`
- **Companions**: `from-green-500/20 to-emerald-600/20 border-green-500/30`

## 📝 Form Component Styling

### Input Fields
```jsx
<Input className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400" />
```

### Textarea Fields
```jsx
<Textarea className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400 min-h-[120px]" />
```

### Labels
```jsx
<label className="block text-purple-200 mb-2">
  Field Name <span className="text-purple-300">(Optional helper text)</span>
</label>
```

## 🔘 Button Styling Patterns

### Primary Button (Main Actions)
```jsx
<Button className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white shadow-lg hover:shadow-xl transition-all duration-300">
```

### Secondary Button
```jsx
<Button className="bg-purple-600 hover:bg-purple-700 text-white">
```

### Ghost Button
```jsx
<Button variant="ghost" className="text-purple-200 hover:text-white hover:bg-purple-500/20">
```

### Success Button
```jsx
<Button className="bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white">
```

## 🏷️ Badge Component Patterns

### Themed Badges
```jsx
/* Narrative/World */
<Badge className="bg-cyan-500/20 text-cyan-300 border-cyan-500/30">

/* Mechanics */
<Badge className="bg-purple-500/20 text-purple-300 border-purple-500/30">

/* Companions */
<Badge className="bg-green-500/20 text-green-300 border-green-500/30">

/* General Info */
<Badge className="bg-yellow-500/20 text-yellow-300 border-yellow-500/30">
```

## 📐 Layout Patterns

### Page Structure
```jsx
<div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
  {/* Magical background effects */}
  <div className="absolute inset-0 opacity-30">
    <div className="absolute top-20 right-20 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
    <div className="absolute bottom-20 left-20 w-72 h-72 bg-pink-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
  </div>

  <div className="relative z-10 min-h-screen py-8 px-4">
    <div className="max-w-4xl mx-auto">
      {/* Page content */}
    </div>
  </div>
</div>
```

### Container Sizing
- Standard pages: `max-w-4xl mx-auto`
- Wide layouts: `max-w-6xl mx-auto`
- Full width: `container mx-auto`

### Spacing Conventions
- Page padding: `py-8 px-4`
- Card padding: `p-4 md:p-6`
- Section margins: `mb-8 md:mb-12`
- Element spacing: `space-y-4` or `space-y-6`

## 📱 Responsive Design Patterns

### Breakpoint Usage
- Mobile-first approach
- Use `sm:`, `md:`, `lg:` prefixes
- Grid patterns: `grid-cols-1 md:grid-cols-2 lg:grid-cols-3`

### Mobile Optimizations
```jsx
/* Text sizing */
text-sm sm:text-base md:text-lg

/* Button sizing */
px-6 sm:px-8 md:px-12 py-3 sm:py-4

/* Spacing adjustments */
space-y-4 md:space-y-6

/* Grid responsiveness */
grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 md:gap-6
```

## ✨ Animation & Effects

### Transition Standards
```jsx
transition-all duration-200  // Fast interactions
transition-all duration-300  // Standard transitions
```

### Hover Effects
```jsx
hover:bg-black/70 hover:border-purple-400/50 hover:scale-105
```

### Magical Effects
```jsx
/* Pulsing orbs */
animate-pulse

/* Gradient shifts */
hover:from-purple-700 hover:to-pink-700

/* Shadow elevation */
shadow-lg hover:shadow-xl
```

## 🧩 Component-Specific Guidelines

### Progress Indicators
```jsx
/* Active state */
bg-purple-600 text-white

/* Inactive state */
bg-gray-600 text-gray-300

/* Progress bars */
bg-purple-600  // Active
bg-gray-600    // Inactive
```

### Navigation Elements
```jsx
/* Active nav item */
text-purple-300

/* Inactive nav item */
text-gray-400

/* Hover states */
hover:text-white hover:bg-purple-500/20
```

### Status Indicators
```jsx
/* Active/Success */
bg-green-500/20 text-green-300 border-green-500/30

/* Warning/Recruiting */
bg-yellow-500/20 text-yellow-300 border-yellow-500/30

/* Inactive/Completed */
bg-gray-500/20 text-gray-300 border-gray-500/30
```

## 🎯 Theme-Specific Customizations

The app supports multiple themes through CSS custom properties. When creating components, consider theme variations:

### Fantasy Theme (Primary)
- Deep purples and magentas
- Mystical lighting effects
- Rich, saturated colors

### Cyberpunk Theme
- Neon cyans and blues
- High contrast
- Electric color palette

### Dark Fantasy Theme
- Darker purples and reds
- Gothic atmosphere
- Muted, atmospheric colors

## 📋 Checklist for New Components

When creating new components, ensure they follow these patterns:

- [ ] Uses dark theme color palette (white text, purple accents)
- [ ] Cards use `bg-black/60 backdrop-blur-sm border border-purple-500/30`
- [ ] Proper hover states with `transition-all duration-200`
- [ ] Responsive design with appropriate breakpoints
- [ ] Form elements use dark styling with purple focus states
- [ ] Buttons follow established patterns (gradient primary, solid secondary)
- [ ] Text hierarchy uses white/purple-200/purple-300 progression
- [ ] Proper spacing using consistent margin/padding patterns
- [ ] Magical background effects for full-page layouts
- [ ] Themed badges and status indicators
- [ ] Accessibility considerations (proper contrast, focus states)

## 🚫 Anti-Patterns to Avoid

- **Don't use light backgrounds** - The app is consistently dark-themed
- **Don't use bright colors for large areas** - Keep bright colors for accents only
- **Don't mix color themes inconsistently** - Stick to the purple fantasy palette
- **Don't skip hover states** - All interactive elements should have hover feedback
- **Don't ignore mobile responsiveness** - Always consider mobile layouts
- **Don't use default border colors** - Always use themed purple borders
- **Don't forget backdrop blur on cards** - Cards should have the glassy effect
- **Don't use black text on dark backgrounds** - Always use white or light purple text

## 📖 Usage Examples

### Feature Section
```jsx
<div className="space-y-6">
  <div className="flex items-center space-x-3 mb-6">
    <div className="text-2xl">🎭</div>
    <div>
      <h2 className="text-2xl text-white mb-2">Section Title</h2>
      <p className="text-purple-200">Section description text.</p>
    </div>
  </div>

  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
    {/* Feature cards */}
  </div>
</div>
```

### Form Section
```jsx
<div className="space-y-4">
  <div>
    <label className="block text-purple-200 mb-2">
      Field Name <span className="text-purple-300">(Optional)</span>
    </label>
    <Input
      className="bg-black/40 border-purple-500/30 text-white placeholder-purple-300/50 focus:border-purple-400 focus:ring-purple-400"
      placeholder="Enter value..."
    />
    <p className="text-sm text-purple-300 mt-1">
      Helper text for the field.
    </p>
  </div>
</div>
```

This style guide ensures consistency across all components and pages in WorldArchitect.AI while maintaining the magical, immersive fantasy theme that defines the application's identity.
