---
title:        Research Output Steering & Configuration
inclusion:    always
version:      1.1
last-updated: 2026-01-12
status:       active
---

# Research Output Steering & Configuration

## 1. Purpose

Automatically archive **complete** AI-generated research outputs in a structured, traceable Markdown format.

Main goals:
- Long-term personal/team knowledge base
- Reproducibility of results
- Audit trail and methodology tracking
- Historical comparison of answers on the same topics
- Compliance & reference documentation

## 2. Scope – Activation Triggers

This policy **must** be followed whenever **any** of the following is true (case-insensitive):

- User prompt contains the word **research**
- Prompt contains research-oriented intent verbs/phrases:  
  investigate · analyze in depth · look into · examine · study · find sources on · compare · evaluate · deep dive · survey · review
- The agent uses one or more of the following tools in a non-trivial way:  
  web_search · web_fetch · code (for analysis) · execute_bash (for data processing)

Trivial or casual usage of search tools does **not** automatically trigger this rule.

## 3. Mandatory Behavior

For every qualifying task the agent **MUST**:

1. Produce a **complete, self-contained research response**  
   (full reasoning, findings, sources, confidence assessment, limitations, etc.)
2. **Save the entire response** as a Markdown file in the designated folder
3. Treat the saved `.md` file as the **canonical and authoritative version**
4. In the chat response **never** output the full research content. Instead provide **only**:
   - Very short summary (max 3–5 sentences)
   - Exact file path and name of the saved research output
   - Any urgent caveats, contradictions or recommended follow-up actions

## 4. File Storage Rules

- **Directory**: `.kiro/research/`
- **File extension**: `.md` (Markdown)
- **Naming pattern**: `YYYY-MM-DD_kebab-case-short-topic-description.md`  
  (strict kebab-case: lowercase, hyphens, no spaces, no special characters except underscore if needed)

**Examples of valid filenames:**
- `2026-01-12_quantum-resistant-cryptography-overview.md`
- `2026-01-12_llm-jailbreak-techniques-2025-2026.md`
- `2026-01-13_mcp-protocol-security-vulnerabilities.md`

**Forbidden in filenames**: timestamps in the name (HHMMSS), uppercase letters, spaces, underscores except as separator if absolutely necessary.

## 5. Required File Structure

Every saved file **must** contain **all** of these sections in exactly this order:

```markdown
# Research Output – 2026-01-12 14:30 CET

## Original Prompt
> [Exact user prompt — preserve line breaks, code blocks, formatting]

## Complete Response
[Full AI-generated answer — all markdown formatting, tables, code blocks, inline citations preserved]

## Key Findings
- Primary factual conclusion 1
- Primary factual conclusion 2
- [If applicable] Speculative/model-inferred point → clearly marked

## Sources & References
- [Source Title](URL) — description
- [Source Title](URL) — description

## Tools & Methods Used
- web_search: "search query used"
- web_fetch: URL accessed
- code: operation performed

## Metadata
- Generated: 2026-01-12T14:30:22+01:00
- Model: [model name & version – if known]
- Session ID: [if available]
- Tool calls total: N
- Approximate duration: ~X minutes

## Limitations & Confidence Notes
- Data current as of [date] – may become outdated quickly in fast-moving fields
- Recommended next steps: [if applicable]
```

## 6. Failure & Error Handling

If the file cannot be created or written (permission issues, disk full, path invalid, etc.):

- Do not display the full research content in chat
- Do not save partial/incomplete versions
- Immediately fail the task and return only a clear error message:

```
Error: Failed to save research output
Path attempted: .kiro/research/2026-01-12_example-topic.md
Reason: [specific error message if available]
Research task aborted – no output was generated or saved.
```

## 7. Integrity Rules & Prohibited Behaviors

The saved `.md` file is the sole canonical research output.

**Strictly forbidden:**
- Displaying the full research response (or large parts of it) in chat without saving
- Saving in any format except `.md`
- Using a different directory or deviating from the naming pattern
- Omitting any required section
- Shortening, redacting, or sanitizing content in the saved file
- Overwriting existing files without explicit user confirmation
- Silently dropping/skipping research tasks when saving fails

## 8. Rationale & Benefits

- Creates a growing, searchable, versionable research archive
- Enables reproducibility of AI-assisted work
- Allows tracking how answers evolve as models and knowledge update
- Supports post-hoc quality audits and methodology improvement
- Provides traceability for compliance-sensitive or professional use

## Version History

- 1.0 (2026-01): Initial version
- 1.1 (2026-01-12): Merged documents, improved structure, added failure handling
