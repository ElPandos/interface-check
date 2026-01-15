---
title:        UI Best Practices
inclusion:    always
version:      1.0
last-updated: 2026-01-15 10:01:33
status:       active
---

# UI Best Practices

## Core Principles

### Accessibility-First Design
- **Legal Compliance**: WCAG 2.2 mandatory with European Accessibility Act enforcement in 2025
- **Color Contrast**: Minimum 4.5:1 for text, 3:1 for UI components
- **Semantic Structure**: Proper heading hierarchy (H1-H6) and ARIA landmarks
- **Interactive Elements**: Minimum 48px tap targets with adequate spacing
- **Business Impact**: Access to $13 trillion market with disability-inclusive design

### Performance as Design Constraint
- **Core Web Vitals**: 90% of web apps fail in 2025 - prioritize LCP, FID, CLS
- **Lazy Loading**: Defer non-critical resources
- **Image Optimization**: WebP format, responsive images, compression
- **Code Splitting**: Load only necessary JavaScript per page

### Component-Driven Architecture
- **Design Tokens**: Centralized colors, typography, spacing, animations
- **Reusable Components**: 30-35% faster development through systematic reuse
- **Cross-Platform Consistency**: Unified design language across touchpoints
- **Documentation**: Clear guidelines for component usage

## Design Workflow

### User-Centered Process
- **Research-Driven**: 20% increase in satisfaction with user feedback integration
- **Design Thinking**: Empathize → Define → Ideate → Prototype → Test
- **Continuous Testing**: Regular usability testing throughout, not just at end
- **Data-Informed**: Analytics and behavior data guide decisions

### Design Token Workflow
- **Centralized Decisions**: Tokens over hardcoded values
- **Design-to-Code Sync**: Single update ripples through Figma, React, CSS
- **Theming**: Easy theme switching through token management
- **Version Control**: Track design system changes

### Figma Best Practices
- **Variable Grouping**: Forward slash naming (bg/bg-primary)
- **Component Variants**: Proper variants and properties
- **Auto Layout**: Responsive, flexible designs
- **Style Management**: Consistent colors, typography, effects

## Responsive Design

### Mobile-First Approach
- **Progressive Enhancement**: Start mobile, enhance for larger screens
- **Touch-Friendly**: Adequate spacing for finger navigation
- **Container Queries**: Components adapt to container size, not viewport
- **Cross-Device Testing**: Validate on actual devices

### Performance Optimization
- **Minimize HTTP Requests**: Bundle and optimize assets
- **Efficient Animations**: GPU-accelerated, avoid layout thrashing
- **Accessible Media Queries**: Respect reduced motion preferences

## Quality Assurance

### Design Validation
- **Accessibility Audits**: Automated (axe-core, WAVE) + manual testing
- **Usability Testing**: Include assistive technology users
- **Cross-Browser**: Consistent experience across browsers
- **Performance Testing**: Validate load times and responsiveness

### Iterative Improvement
- **A/B Testing**: Validate decisions with real user data
- **Analytics Integration**: Monitor behavior, identify pain points
- **Feedback Loops**: Continuous user and stakeholder feedback
- **Post-Launch Monitoring**: Track performance and satisfaction

## Team Collaboration

### Designer-Developer Handoff
- **Comprehensive Specs**: Spacing, typography, interaction details
- **Asset Preparation**: Optimized images in appropriate formats
- **Interactive Prototypes**: Demonstrate complex interactions
- **Regular Communication**: Ongoing collaboration

### Stakeholder Management
- **Design Rationale**: Explain decisions based on research
- **Business Alignment**: Connect design to business goals
- **Change Management**: Structured process for feedback

## Anti-Patterns to Avoid

### Design Failures
- **Inconsistent Implementation**: Different interpretations across teams
- **Over-Engineering**: Overly complex systems difficult to maintain
- **Poor Documentation**: Inadequate guidelines for components
- **Tool Fragmentation**: Multiple disconnected tools

### UX Mistakes
- **Overloading Interfaces**: Cluttered designs without hierarchy
- **Ignoring Accessibility**: Failing to meet WCAG standards
- **Inconsistent Patterns**: Different interactions for similar functions
- **Dark Patterns**: Deceptive designs (illegal in EU)

### Workflow Issues
- **Skipping Research**: Decisions without user validation
- **Late-Stage Testing**: Testing only after development complete
- **Poor Communication**: Inadequate designer-developer collaboration

## Success Metrics

- **Accessibility**: 100% WCAG 2.2 AA compliance
- **Performance**: Core Web Vitals passing scores
- **Development Velocity**: 30-35% improvement through component reuse
- **User Satisfaction**: 50% increase through user-centered practices
- **Task Completion**: 90%+ success rate for primary flows

## Version History

- v1.0 (2026-01-14 00:00:00): Consolidated from ui-development_best-practices.md and ui-designer_best-practices.md
