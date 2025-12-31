---
title: UI Development Patterns
inclusion: fileMatch
fileMatchPattern: 'src/ui/**/*.py'
---

# UI Development Patterns

## NiceGUI Patterns
- **Component Hierarchy**: Logical nesting of UI components with proper classes
- **Styling**: Consistent CSS classes using Tailwind-style utilities
- **Event Handling**: Proper event binding with error handling
- **Dynamic Updates**: Refresh patterns for live data updates

## User Experience
- **Loading States**: Visual feedback during long operations
- **Error Notifications**: User-friendly error messages with color coding
- **Input Validation**: Real-time validation with helpful error messages
- **Responsive Design**: Proper spacing and sizing for different screen sizes

## State Management
- **Component State**: Local state management within components
- **Global State**: Shared state through dependency injection
- **State Persistence**: Save/restore application state to files
- **State Synchronization**: Keep UI in sync with underlying data

## UI Component Structure
- **Handler Pattern**: Separate UI logic from business logic using handler classes
- **Component Composition**: Build complex UI from reusable components
- **Event Callbacks**: Use lambda functions with closures for event handling
- **State Management**: Centralized state with clear update patterns

## Tab-based Interface
- **Modular Design**: Each tab handles specific functionality
- **Shared Components**: Reuse connection selectors and status indicators
- **Context Switching**: Maintain state when switching between tabs
- **Resource Management**: Proper cleanup when tabs are destroyed
