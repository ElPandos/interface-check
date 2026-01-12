# Project Update: Refresh Research and Steering Documents

## Objective
Update all research files and their corresponding steering documents by re-executing original research prompts and comparing findings.

## Process

### 1. Discover Research Files
List all research files to process:
```bash
find .kiro/research -name "*.md" -type f | sort
```

### 2. Extract and Execute Original Prompts
For each research file found:

**Extract Original Prompt:**
```bash
# For each file, extract the original prompt section
grep -A 10 "## Original Prompt" [research-file] | grep "^>" | sed 's/^> //'
```

**Execute Research Update:**
```bash
# Run kiro-cli with the extracted prompt
kiro-cli chat --trust-all-tools --no-interactive "[extracted-prompt]"
```

### 3. Compare and Update Process
For each research file:

1. **Backup Current Research:**
   ```bash
   cp [research-file] [research-file].backup
   ```

2. **Identify Corresponding Steering File:**
   - Extract topic from research filename (e.g., `devcontainer-best-practices-research.md` → `devcontainer-best-practices.md`)
   - Locate in `.kiro/steering/[topic].md`

3. **Compare Content:**
   - Compare "Key Findings" sections
   - Compare "Sources & References" sections
   - Identify new practices or updated recommendations
   - Note deprecated or changed practices

4. **Update Steering Document:**
   - Incorporate new best practices
   - Update version number and last-updated date
   - Add new findings to appropriate sections
   - Update version history with changes made

### 4. Validation Steps
After each update:

1. **Verify File Integrity:**
   ```bash
   # Check that files are valid markdown
   grep -q "^# " [steering-file] && echo "Valid header found"
   ```

2. **Check Required Sections:**
   - Verify frontmatter exists and is properly formatted
   - Confirm version history is updated
   - Ensure all code examples are properly formatted

3. **Backup Management:**
   ```bash
   # Keep backups organized
   mkdir -p .kiro/backups/$(date +%Y-%m-%d)
   mv *.backup .kiro/backups/$(date +%Y-%m-%d)/
   ```

## Error Handling
- If original prompt extraction fails, skip that file and report
- If kiro-cli execution fails, log error and continue with next file
- If steering file doesn't exist, report missing file
- Create summary of successful updates and failures

## Output Report

### 📊 Update Summary
- **Files Processed:** [Number of research files found]
- **Successful Updates:** [Number of successful steering document updates]
- **Failures:** [Number of failed updates with reasons]
- **New Findings:** [Count of new practices discovered]

### 🔄 Changes Made
For each updated steering document:
- **File:** [steering-document-name]
- **Version:** [old-version] → [new-version]
- **Key Changes:** [Brief summary of major updates]
- **New Practices:** [List of newly added best practices]

### ⚠️ Issues Encountered
- **Missing Files:** [Research files without corresponding steering documents]
- **Failed Extractions:** [Files where prompt extraction failed]
- **Execution Errors:** [kiro-cli failures and reasons]

### 📋 Recommendations
- **Manual Review Needed:** [Files requiring human review]
- **Deprecated Practices:** [Practices that may need removal]
- **New Research Areas:** [Suggested topics for future research]

## Automation Notes
This process can be automated with a script that:
1. Iterates through all research files
2. Extracts original prompts using regex
3. Executes kiro-cli commands
4. Parses new research for key changes
5. Updates steering documents programmatically
6. Generates comprehensive update report

**Execute this prompt to refresh all project research and maintain current best practices.**

## Version History

- v1.0 (2026-01-12): Initial version
