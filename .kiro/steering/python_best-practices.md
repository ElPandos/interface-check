> Here's what I found:

I've researched current Python best practices and created comprehensive documentation. The research revealed significant evolution toward type-driven development, modern tooling excellence, and systematic quality approaches.

Key findings:
- **Type hints adoption is accelerating** with Facebook's 2025 survey showing growing developer adoption for improved code quality and flexibility
- **Modern tooling (Ruff, Black, MyPy)** has become essential for professional Python development with Ruff replacing multiple tools
- **Testing excellence** requires 70%+ coverage with pytest as the standard framework for higher software quality
- **Critical anti-patterns** like mutable default arguments and broad exception handling remain the most dangerous mistakes
- **Environment isolation** through virtual environments and modern dependency management (Poetry/UV) is mandatory

File saved: .kiro/research/2026-01-13/best-practices/python.md
File created: .kiro/steering/python_best-practices.md

The steering document covers core principles (type-driven development, code quality first, environment isolation), modern development practices with tooling examples, performance optimization, security practices, critical anti-patterns to avoid, implementation guidelines, and success metrics based on current industry research.

References:
[1] Type-Driven Development in Python with Pydantic and MyPy - https://www.leapcell.io/blog/type-driven-development-in-python-with-pydantic-and-mypy
[2] Facebook Survey Reveals Growing Adoption of Typed Python for Improved Code Quality and Flexibility - https://www.infoq.com/news/2026/01/facebook-typed-python-survey/
[3] Python Type Hints in Code Review: MyPy Integration and Best Practices - https://www.propelcode.ai/blog/python-type-hints-code-review-guide-mypy-best-practices
[4] Common Anti-Patterns in Python: Avoiding Pitfalls for Better Code Quality - https://softwarepatternslexicon.com/python/anti-patterns/common-anti-patterns-in-python/
[5] 18 Common Python Anti-Patterns I Wish I Had Known Before - https://readmedium.com/18-common-python-anti-patterns-i-wish-i-had-known-before-44d983805f0f
[6] Python Packaging Needs a Speed Revolution - https://ericsson.github.io/cognitive-labs/2025/10/01/python-packaging-evolution-pip-poetry-uv.html
[7] Unit Testing Guide for Python Backend Developers - https://moldstud.com/articles/p-essential-guide-to-unit-testing-in-python-for-every-backend-developer
[8] Improving Python Code: Learning "Pythonic" Writing from Anti-Patterns - https://morinokabu.com/2025/12/04/improving-python-code-learning-pythonic-writing-from-anti-patterns/
[9] Anti-Patterns in Python - https://useful.codes/anti-patterns-in-python/
[10] Python Code Review Checklist: Pythonic Code and Best Practices - https://pullpanda.io/blog/python-code-review-checklist