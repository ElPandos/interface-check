> Here's what I found:

I've researched current Python patterns and anti-patterns, then updated the existing steering document with comprehensive anti-patterns coverage. The research revealed significant evolution toward prevention-focused approaches and systematic quality practices.

Key findings:
- **Mutable default arguments** remain the most dangerous Python anti-pattern, causing shared state bugs
- **Exception handling anti-patterns** like bare except clauses and exception swallowing are still prevalent  
- **Performance anti-patterns** including inefficient list operations and string concatenation in loops continue to impact applications
- **Modern type hint usage** is essential, with Any overuse defeating the purpose of type safety
- **Async/await anti-patterns** like blocking operations in async functions are becoming more common as async adoption grows

The steering document now includes a comprehensive anti-patterns section covering the 10 most critical Python anti-patterns to avoid, with practical examples of both problematic and correct implementations based on current 2025 research.

## Synchronization Report (Tier 2)

### Primary File Updated
- Path: .kiro/steering/python_patterns.md
- Change type: content enhancement with anti-patterns section
- Impact: additive

### Related Files Identified
- .kiro/steering/python_best-practices.md - reviewed (complementary focus on patterns vs best practices)
- .kiro/steering/code-quality_patterns.md - no change needed (general code quality vs Python-specific patterns)
- .kiro/steering/error-handling_patterns.md - no change needed (general error handling vs Python-specific patterns)

References:
[1] Improving Python Code: Learning "Pythonic" Writing from Anti-Patterns - https://morinokabu.com/2025/12/04/improving-python-code-learning-pythonic-writing-from-anti-patterns/
[2] Common Anti-Patterns in Python: Avoiding Pitfalls for Better Code Quality - https://softwarepatternslexicon.com/python/anti-patterns/common-anti-patterns-in-python/
[3] Python Code Review Checklist: Pythonic Code and Best Practices - https://pullpanda.io/blog/python-code-review-checklist
[4] 18 Common Python Anti-Patterns I Wish I Had Known Before - https://readmedium.com/18-common-python-anti-patterns-i-wish-i-had-known-before-44d983805f0f
[5] Anti-Patterns in Python - https://useful.codes/anti-patterns-in-python/