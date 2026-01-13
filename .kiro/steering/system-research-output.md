---
title:        Research Output Steering & Configuration
inclusion:    always
version:      1.3
last-updated: 2026-01-12
status:       active
---

# Research Output Steering & Configuration

## 1. Purpose
Automatically archive **complete** AI-generated research outputs in a structured, traceable Markdown format for long-term knowledge base, reproducibility, audit trail, historical comparison, and compliance.

## 2. Scope – Activation Triggers

**MUST** activate when **any** of these is true (case-insensitive):

- Prompt contains "research" or research-oriented intent: investigate · analyze in depth · look into · examine · study · find sources on · compare · evaluate · deep dive · survey · review
- Agent uses non-trivial external tools: ≥3 web_search / browse_page calls, web_search for factual claims, code_execution for analysis/modeling
- Output includes citations, multiple sources, confidence levels, or limitations

**Agent discretion**: If research intent is clearly absent despite a trigger keyword, deactivate and justify in ≤1 sentence (e.g., "Casual lookup only – no full research archive needed").

## 3. Mandatory Behavior

1. Produce a **complete, self-contained research response** (full reasoning, findings, sources, confidence, limitations)
2. **Save** the entire response as the canonical `.md` file
3. In chat response provide **only**:
   - Short summary (max 3–5 sentences)
   - Exact file path/name
   - Urgent caveats or recommended follow-ups
   - Optional: include Key Findings bullets or small table if they clarify value

**Forbidden**: Outputting the full response (or large excerpts) in chat unless user explicitly asks.

## 4. File Storage Rules

- **Directory**: `.kiro/research/YYYY-MM-DD/[category]/`
- **Categories** (subfolders): `best-practices/`, `patterns/`, `analyze/`, `surveys/`, `general/` (use `general/` as fallback)
- **Naming pattern**: `topic-name.md` (strict kebab-case: lowercase, hyphens only, no spaces)
  - Default: base topic name only (e.g. `quantum-cryptography.md`)
  - On collision: auto-append date prefix or version suffix:
    - `quantum-cryptography-v2.md`
  - **Strict rules**:
    - No suffixes like `-research`, `-output`, `-best-practices`
    - No timestamps in name unless used as prefix
    - No uppercase, spaces, or underscores (except rare cases)

**Examples valid**:
- `.kiro/research/2026-01-12/best-practices/quantum-cryptography.md`
- `.kiro/research/2026-01-12/analyze/security-vulnerabilities-v2.md`

## 5. Required File Structure

Every saved file **must** include these sections in order:

```markdown
# Research Output – 2026-01-12 14:30 CET

## Original Prompt
> [Exact user prompt — preserve formatting]

## Complete Response
[Full AI-generated answer — all markdown, tables, code, citations preserved]

## Key Findings
- Primary conclusion 1
- Primary conclusion 2
- [Speculative → clearly marked]

## Sources & References
- [Title](URL) — brief description + access date

## Tools & Methods Used
- web_search: "query"
- browse_page: URL → instructions

## Metadata
- Generated: 2026-01-12T14:30:22+01:00
- Model: [if known]
- Tags: keyword1, keyword2, keyword3
- Confidence: High/Medium/Low + one-sentence rationale
- Version: 1 (increment on meaningful revisions)

## Limitations & Confidence Notes
- Data current as of [date]
- Next steps: [if applicable]
```

## 6. Collision & Overwrite Handling

- Never silently overwrite
- On collision → auto-create with -v2, -v3, or date prefix
- User must explicitly say "yes overwrite" to replace existing file

## 7. Failure & Error Handling
If save fails:
```
Error: Failed to save research output
Path attempted: .kiro/research/2026-01-12/analyze/topic.md
Reason: [specific error]
Fallback: Full content copied below for manual save.
----------------------------------------
[full markdown content]
```

## 8. Integrity Rules & Prohibited Behaviors
Unchanged from v1.2 — full content saved, no redaction, no other formats, etc.

## 9. Rationale & Benefits
Unchanged

## Version History

- v1.0–1.2: Previous versions
- v1.3 (2026-01-12): Added collision handling, expanded categories, optional Key Findings in chat, tags/confidence in metadata, agent discretion for triggers
