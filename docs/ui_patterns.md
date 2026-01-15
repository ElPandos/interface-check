---
title:        UI Patterns
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# UI Patterns

## Core Principles

### Systematic Design Excellence
- **Atomic Design**: Hierarchical component organization (atoms → molecules → organisms → templates → pages)
- **Component-Driven Development**: Reusable components with clear APIs and consistent behavior
- **Design Token Systems**: Centralized design decisions enabling consistent theming
- **Accessibility-First**: WCAG 2.2 compliance with 4.5:1 contrast ratios and semantic structure

### Modern Implementation
- **Living Design Systems**: AI-augmented ecosystems with real-time design-code sync
- **Container Queries**: Context-aware responsive design adapting to container size
- **Mobile-First Progressive Enhancement**: Start mobile, enhance for larger screens
- **Performance-Conscious**: Optimize for Core Web Vitals

## Essential Patterns

### 1. Atomic Design System Pattern
Organize components into hierarchical levels:
- **Atoms**: Basic building blocks (buttons, inputs, labels, icons)
- **Molecules**: Simple combinations (search forms, navigation items)
- **Organisms**: Complex UI sections (headers, product grids, footers)
- **Templates**: Page-level structures without specific content
- **Pages**: Specific instances with real content

### 2. Design Token System Pattern
Centralized design decisions as named entities:
- **Color Tokens**: `color-brand-primary`, `color-text-secondary`
- **Typography Tokens**: `font-size-heading-large`, `font-weight-bold`
- **Spacing Tokens**: `spacing-small`, `spacing-large`
- **Shadow/Border Tokens**: `shadow-elevated`, `border-radius-medium`

**Benefits**: Single source of truth, consistent theming, automated design-to-code workflows.

### 3. Component-Driven Development Pattern
High cohesion inside modules, low coupling across:
- **Reusable Components**: Standardized UI elements with consistent APIs
- **Variant Management**: Systematic handling of component states
- **Documentation Integration**: Clear usage guidelines
- **Version Control**: Proper lifecycle management and deprecation

**Impact**: 35% reduction in development time through systematic reuse.

### 4. Container Queries Pattern
Beyond traditional breakpoints:
- **Container-Aware**: Components adapt to container size, not viewport
- **Mobile-First Enhancement**: Progressive enhancement from mobile constraints
- **Touch-Friendly**: Minimum 44×44 point touch targets
- **Performance Optimization**: Lazy loading, efficient animations

### 5. Accessibility-First Pattern
WCAG 2.2 compliance as foundation:
- **Semantic Structure**: Proper heading hierarchy (H1-H6) and ARIA landmarks
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components
- **Keyboard Navigation**: Full functionality without mouse
- **Screen Reader Support**: Alt text, captions, descriptive labels

**Legal**: European Accessibility Act enforceable 2025, ADA applies to digital products.

## Critical Anti-Patterns

### 1. Dark Patterns (Illegal in EU)
Manipulative design exploiting cognitive biases:
- **Bait and Switch**: Misleading users about intended actions
- **Hidden Costs**: Revealing fees only at checkout
- **Forced Continuity**: Difficult cancellation processes
- **Fake Urgency**: Misleading countdown timers
- **Confirmshaming**: Guilt-inducing opt-out language

### 2. Accessibility Violations
96.3% of websites have violations:
- **Poor Color Contrast**: Below 4.5:1 ratio
- **Missing Alt Text**: Images without descriptions
- **Inaccessible Forms**: Missing labels, unclear errors
- **Keyboard Traps**: Elements preventing keyboard navigation
- **Missing Focus Indicators**: No visual keyboard focus

### 3. Navigation Anti-Patterns
70% of users abandon due to confusing navigation:
- **Hidden Navigation**: Hamburger menus on desktop
- **Inconsistent Labels**: Changing terms between pages
- **Deep Link Chains**: No breadcrumbs
- **Cluttered Menus**: Overwhelming options
- **Broken Mobile Navigation**: Poor touch targets

### 4. Form Design Failures
Complex forms cause 50% higher bounce rates:
- **Unclear Requirements**: Missing labels and validation rules
- **Poor Error Handling**: Vague error messages
- **Excessive Fields**: Requesting unnecessary information
- **No Progress Indicators**: Multi-step forms without status

### 5. Visual Design Problems
- **Inconsistent Typography**: Mixed font sizes, weights, spacing
- **Poor Visual Hierarchy**: Unclear information prioritization
- **Insufficient White Space**: Cluttered layouts
- **Color System Failures**: Inconsistent color usage

### 6. Performance Anti-Patterns
90% of web apps fail Core Web Vitals:
- **Unoptimized Images**: Large files without compression
- **Excessive HTTP Requests**: Multiple resource calls
- **Heavy JavaScript**: Blocking rendering
- **Animation Jank**: Poorly optimized animations
- **Third-Party Script Bloat**: External resources degrading performance

## Implementation Guidelines

### Pattern Selection
1. **User Research Foundation**: Base choices on user mental models
2. **Accessibility Requirements**: WCAG 2.2 compliance from design phase
3. **Technical Constraints**: Consider team capabilities
4. **Consistency Priority**: Established patterns over novel approaches
5. **Testing Validation**: Validate with real users

### Quality Assurance
1. **Automated Accessibility Testing**: Regular WCAG audits
2. **Cross-Device Testing**: Different screen sizes and input methods
3. **Performance Monitoring**: Track Core Web Vitals
4. **User Testing**: Include assistive technology users
5. **Design System Governance**: Maintain consistency

## Tools

### Design System Platforms
- **Figma Variables**: Design token management
- **Component Libraries**: Centralized, versioned collections
- **Design-to-Code Tools**: Automated synchronization

### Accessibility Tools
- **Automated Testing**: axe-core, WAVE, Lighthouse
- **Manual Testing**: Screen reader, keyboard navigation
- **Color Contrast Analyzers**: WCAG compliance checking

### Performance Optimization
- **Image Optimization**: WebP, lazy loading, responsive images
- **Code Splitting**: Load only necessary JavaScript
- **Performance Monitoring**: RUM and synthetic testing

## Success Metrics

- **Task Completion**: 90%+ success rate for primary flows
- **Accessibility**: 100% WCAG 2.2 AA compliance
- **Development Velocity**: 35% improvement through component reuse
- **Performance**: Core Web Vitals passing scores

## Version History

- v1.0 (2026-01-14 00:00:00): Consolidated from ui-development_patterns.md and ui-designer_patterns.md
