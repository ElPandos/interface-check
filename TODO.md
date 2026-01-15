---
title:        Project TODO and Code Quality Issues
inclusion:    always
version:      1.0
last-updated: 2026-01-15 15:25:00
status:       active
---

# TODO - Code Quality Issues

Generated on: 2026-01-12

## Ruff Linting Issues

### ARG002 - Unused method arguments
- [ ] **src/ui/tabs/agent.py:340** - Unused method argument: `screen_num` in `_add_task`
- [ ] **src/ui/tabs/agent.py:358** - Unused method argument: `screen_num` in `_add_custom_task`
- [ ] **src/ui/tabs/agent.py:590** - Unused method argument: `screen_num` in `_add_recommended_task`
- [ ] **src/ui/tabs/cable.py:106** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/chat.py:120** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/database.py:104** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/e2e.py:100** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/host.py:60** - Unused method argument: `classes` in `_build_single_screen_content`
- [ ] **src/ui/tabs/host_old.py:100** - Unused method argument: `classes` in `_build_single_screen_content`
- [ ] **src/ui/tabs/log.py:106** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/slx.py:146** - Unused method argument: `screen_num` in `build_content`
- [ ] **src/ui/tabs/slx.py:414** - Unused method argument: `port_id` in `run_eye_scan`
- [ ] **src/ui/tabs/system.py:104** - Unused method argument: `screen_num` in `build_content`

### RUF006 - Store asyncio.create_task reference
- [ ] **src/ui/tabs/agent.py:455** - Store a reference to the return value of `asyncio.create_task`
- [ ] **src/ui/tabs/log.py:179** - Store a reference to the return value of `asyncio.create_task`

### BLE001 - Blind exception catching
- [ ] **src/ui/tabs/agent.py:462** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:195** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:346** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:381** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:415** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:454** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:515** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/local.py:589** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/log.py:301** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/slx.py:210** - Do not catch blind exception: `Exception`
- [ ] **src/ui/tabs/system.py:193** - Do not catch blind exception: `Exception`

### SIM117 - Combine with statements
- [ ] **src/ui/tabs/agent.py:566** - Use a single `with` statement with multiple contexts instead of nested `with` statements

### FBT001/FBT002 - Boolean positional arguments
- [ ] **src/ui/tabs/database.py:19** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/e2e.py:17** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/ethtool_old.py:63** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/host.py:48** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/host.py:957** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/host_old.py:87** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/local.py:35** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/local.py:120** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/log.py:20** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/slx.py:25** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/system.py:19** - Boolean-typed positional argument in function definition
- [ ] **src/ui/tabs/toolbox.py:17** - Boolean-typed positional argument in function definition

### F821 - Undefined names
- [ ] **src/ui/tabs/host_old.py:20** - Undefined name `LogName`
- [ ] **src/ui/tabs/local.py:623** - Undefined name `LogName`

### RUF012 - Mutable class attributes
- [ ] **src/ui/tabs/host_old.py:33** - Mutable class attributes should be annotated with `typing.ClassVar`
- [ ] **src/ui/themes/style.py:62** - Mutable class attributes should be annotated with `typing.ClassVar`

### F841 - Unused variables
- [ ] **src/ui/tabs/host_old.py:1079** - Local variable `file_upload` is assigned to but never used

### PLR0912/PLR0915 - Function complexity
- [ ] **src/ui/tabs/host_old.py:1103** - Too many branches (15 > 12)
- [ ] **src/ui/tabs/host_old.py:1103** - Too many statements (55 > 50)
- [ ] **src/ui/tabs/local.py:206** - Too many branches (15 > 12)
- [ ] **src/ui/tabs/local.py:206** - Too many statements (134 > 50)

### SLF001 - Private member access
- [ ] **src/ui/tabs/slx.py:207** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:307** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:319** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:354** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:422** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:428** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:435** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:436** - Private member accessed: `_shell`
- [ ] **src/ui/tabs/slx.py:495** - Private member accessed: `_shell`

### ERA001 - Commented-out code
- [ ] **src/ui/tabs/slx.py:289** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:291** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:293** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:294** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:295** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:542** - Found commented-out code
- [ ] **src/ui/tabs/slx.py:548** - Found commented-out code

### C408 - Unnecessary dict() calls
- [ ] **src/ui/tabs/slx.py:528** - Unnecessary `dict()` call (rewrite as a literal)
- [ ] **src/ui/tabs/slx.py:538** - Unnecessary `dict()` call (rewrite as a literal)

### TRY300 - Move statement to else block
- [ ] **src/ui/tabs/slx.py:446** - Consider moving this statement to an `else` block

### T201 - Print statements in tests
- [ ] **tests/test_statistics.py:42** - `print` found
- [ ] **tests/test_time_parser.py:15** - `print` found
- [ ] **tests/test_time_parser.py:25** - `print` found
- [ ] **tests/test_time_parser.py:28** - `print` found

## Summary
- **Total Issues**: 344 remaining
- **Fixed**: 3 issues
- **Priority**: Focus on undefined names, blind exceptions, and unused arguments first

## Next Steps
1. Fix undefined LogName imports
2. Replace blind Exception catches with specific exceptions
3. Remove unused method arguments or mark with underscore
4. Store asyncio task references properly
5. Remove commented-out code
6. Replace print statements in tests with proper assertions

## Version History

- v1.0 (2026-01-15 15:25:00): Initial version with frontmatter
