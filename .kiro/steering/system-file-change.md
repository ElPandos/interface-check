---
title: System File Change Synchronization
inclusion: always
version: 1.0
last-updated: 2026-01-12
status: active
---

# File Change Synchronization Policy

## Purpose
Ensure consistency across related files by enforcing **explicit detection, evaluation, and synchronization** of dependent or referenced content whenever a file is modified.  
Silent divergence is **not permitted**.

## Mandatory Behavior
When updating or generating any file, the agent **MUST**:

1. Identify all potentially related files.
2. Evaluate whether synchronization is required (using Synchronization Tiers below).
3. Either:
   - Update the related files, or
   - Explicitly justify why no update is needed (level of justification depends on tier).
4. Produce a Synchronization Report (format & detail level depends on tier).

## Synchronization Tiers
Use the **lowest** tier that fully matches the change.

| Tier | When it applies                                      | Required Actions                                                                 | Report Detail Level          | Justification Style       |
|------|-------------------------------------------------------|-----------------------------------------------------------------------------------|------------------------------|---------------------------|
| 0    | Purely cosmetic / non-semantic<br>(typos, grammar, formatting, date-only header, comment-only, reordering non-normative sections) | No related-file checks needed                                                     | No report required           | —                         |
| 1    | Low impact<br>(local cosmetic edits that indirectly touch meaning, small clarifications) | Check only files already open / in immediate context                              | Very brief (1–2 lines total) | Short sentence            |
| 2    | Medium impact<br>(cross-file references, examples, terminology, config keys, identifiers) | Check all explicitly referenced files + known peer patterns                      | Structured, per-file         | One-liner per file        |
| 3    | High impact<br>(behavior change, deprecation, removal, default-value change, version bump, breaking change) | Check references + documentation + examples + usage/CLI + README + tests if exist | Full structured report       | Clear reasoning per file  |
| 4    | Breaking / global impact<br>(same as Tier 3 + wide downstream consequences likely) | Tier 3 scope + consider adding warning banner or note for downstream consumers    | Full + optional risk note    | Detailed + risk call-out  |

## Synchronization Scope (unchanged from v1.1 – still fully apply)

### 1. Cross-Referenced Files
- All referenced files **MUST be reviewed**
- Version headers, dates, and terminology **MUST remain consistent**
- Breaking changes **MUST be reflected everywhere**

### 2. Pattern / Best-Practice Pairs
For known paired documents (e.g. `*_patterns.md` ↔ `*_best-practices.md` ↔ `*_guidelines.md`):
- Changes to one **require review of all peers**
- Conflicting guidance **MUST NOT exist**
- Shared examples **MUST remain identical**

### 3. Configuration & Usage Coupling
When modifying configuration files, environment files, tool/CLI flags:
- Update all documentation referencing them
- Update usage examples and READMEs
- Note behavioral changes explicitly

### 4. Script ↔ Documentation Synchronization
When scripts or automation change:
- Corresponding documentation **MUST be updated**
- CLI examples **MUST reflect actual behavior**
- Deprecated options **MUST be marked or removed**

## Required Synchronization Report
**Tier 0** → no report  
**Tier 1** → short free-form note at bottom of change (1–2 lines)  
**Tier 2–4** → use this exact structure (omit empty sections):

```markdown
## Synchronization Report (Tier X)

### Primary File Updated
- Path: [file path]
- Change type: [semantic / identifier / example / version / deprecation / behavior / other]
- Impact: [breaking / additive / none]

### Related Files Identified
- [path] – **updated** (brief reason)
- [path] – **no change needed** (example still valid / already aligned / out of scope)
- [path] – **reviewed** (no divergence introduced)

### Files Intentionally Not Checked
- [path] (reason: deprecated / legacy / irrelevant module)

### Justification / Risk Notes (Tier 3+ or when relevant)
[Only include when there is actual risk or non-obvious reasoning]

## Version History

- v1.0 (2026-01-12): Initial version
