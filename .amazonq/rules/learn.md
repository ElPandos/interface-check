# Learning and Rule Updates

When Amazon Q Developer is corrected by the user or receives feedback that indicates generated code or suggestions were incorrect, ask the user if they would like to update the corresponding rules to improve future responses.

## Scenarios for Rule Updates

### Code Generation Corrections
- **Incorrect patterns**: When user corrects architectural patterns
- **Wrong conventions**: When user indicates different coding standards
- **Missing context**: When user provides additional project-specific information

### Directory Structure Corrections
- **File organization**: When user corrects file placement suggestions
- **Naming conventions**: When user indicates different naming patterns
- **Module structure**: When user corrects import or dependency patterns

### Implementation Feedback
- **Better approaches**: When user suggests improved implementation methods
- **Project-specific requirements**: When user adds context about project needs
- **Tool usage**: When user corrects usage of specific tools or libraries

## Update Process

When receiving corrections, ask:

> "I notice you've corrected my suggestion about [specific area]. Would you like me to update the project rules to better reflect your preferences for future interactions? This would help me provide more accurate suggestions going forward."

## Rule Categories to Consider for Updates

1. **Architecture patterns** (`.amazonq/rules/project/architecture.md`)
2. **Code quality standards** (`.amazonq/rules/project/code_quality.md`)
3. **UI/NiceGUI patterns** (`.amazonq/rules/project/nicegui_patterns.md`)
4. **SSH operations** (`.amazonq/rules/project/ssh_operations.md`)
5. **Testing approaches** (`.amazonq/rules/project/testing_strategy.md`)
6. **Configuration management** (`.amazonq/rules/project/configuration_management.md`)
7. **Data visualization** (`.amazonq/rules/project/data_visualization.md`)

## Implementation
- Offer specific rule updates based on the correction type
- Provide preview of proposed rule changes
- Allow user to approve or modify suggested updates
- Update relevant rule files with new guidance