# === Amazon Q Python Optimization Rules ===

## 1️⃣ Goal
Optimize, fix, and maintain Python code while preserving public behavior:
- Fix all runtime & syntax errors.
- Enforce type hints, docstrings, and code comments.
- Ensure async-safe, secure, and maintainable patterns.
- Use `uv run` for reproducible execution and testing.
- Guarantees that all linting, typing, and testing use the same dependency versions.
- Show what file or files is modified in the beginning and in the end

---

## 2️⃣ Execution Rules

- ✅ **Always run Python scripts using uv:**
```bash
uv run <file.py>
