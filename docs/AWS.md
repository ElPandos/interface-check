# Automated Reasoning Policy APIs and Workflows

## Table of Contents

### Core APIs
- Policy Management
- Policy Versions
- Build Workflows
- Test Management
- Annotations & Scenarios

### Build Workflow Types
- INGEST_CONTENT Workflow
- REFINE_POLICY Workflow
- IMPORT_POLICY Workflow

### Annotation Type Reference
- Type Management Annotations
- Variable Management Annotations
- Rule Management Annotations
- Natural Language Rule Creation
- Feedback-Based Updates

### Common Workflows
1. Getting Started (New Policy)
2. Building Policy from Document
3. Policy Development Cycle
4. REFINE_POLICY Workflow (Annotation-Based)

### Testing Workflow
1. Primary Approach: Scenarios API (Recommended)
2. Secondary Approach: Test Cases (User Experience)
3. Test Result Analysis and Troubleshooting

### Build Workflow Monitoring
- Check Build Status
- List Build History
- Best Practice: Clean Build Management
- Troubleshooting Build Failures

### Build Workflow Assets
- Asset Types
- Understanding Conflicting Rules
- Understanding Disjoint Rule Sets
- Advanced Quality Report Analysis

### Additional Topics
- Policy Version Export
- Key Concepts
- Important Format Requirements
- Policy Modeling Best Practices
- ARN Formats

## Core APIs

### Policy Management
- `create-automated-reasoning-policy` - Create initial policy (returns policy ARN)
- `get-automated-reasoning-policy` - Retrieve policy (DRAFT version by default with unversioned ARN)
- `update-automated-reasoning-policy` - Update DRAFT policy with new definition
- `delete-automated-reasoning-policy` - Delete policy
- `list-automated-reasoning-policies` - List all policies

### Policy Versions
- `create-automated-reasoning-policy-version` - Snapshot DRAFT into numbered version
- `export-automated-reasoning-policy-version` - Export specific policy version

### Build Workflows
- `start-automated-reasoning-policy-build-workflow` - Start build process
- `get-automated-reasoning-policy-build-workflow` - Get build workflow status
- `cancel-automated-reasoning-policy-build-workflow` - Cancel running build
- `delete-automated-reasoning-policy-build-workflow` - Delete build workflow
- `list-automated-reasoning-policy-build-workflows` - List build workflows
- `get-automated-reasoning-policy-build-workflow-result-assets` - Get compiled policy assets

### Test Management
- `create-automated-reasoning-policy-test-case` - Create test case
- `get-automated-reasoning-policy-test-case` - Get test case details
- `update-automated-reasoning-policy-test-case` - Update test case
- `delete-automated-reasoning-policy-test-case` - Delete test case
- `list-automated-reasoning-policy-test-cases` - List test cases
- `start-automated-reasoning-policy-test-workflow` - Run tests
- `get-automated-reasoning-policy-test-result` - Get test results
- `list-automated-reasoning-policy-test-results` - List test results

### Annotations & Scenarios
- `get-automated-reasoning-policy-annotations` - Get policy annotations
- `get-automated-reasoning-policy-next-scenario` - Get next test scenario

**Important**: Do NOT use `get-automated-reasoning-policy-annotations` or 
`update-automated-reasoning-policy-annotations` for the `REFINE_POLICY` workflow. Annotations are passed directly in the `start-automated-reasoning-policy-build-workflow` call.

## Build Workflow Types

1. **INGEST_CONTENT** - Process documents to create/extract policy rules
2. **REFINE_POLICY** - Refine and improve existing policies using annotations
3. **IMPORT_POLICY** - Import policies from external sources

### INGEST_CONTENT Workflow
- **Purpose**: Extract policy rules from documents (PDF/TXT)
- **Input**: Documents + optional existing policy definition
- **Use Cases**: Document-to-policy conversion, incremental policy building
- **Content Structure**: `workflowContent.documents[]`

**CRITICAL: Complete Policy Definition for Incremental Building**

When adding documents to an existing policy, you must include the complete current policy definition:

```json
// CORRECT - Incremental policy building
{
  "policyDefinition": {
    "version": "1.0",
    "types": [/* ALL existing types */],
    "rules": [/* ALL existing rules */],
    "variables": [/* ALL existing variables */]
  },
  "workflowContent": {
    "documents": [/* New documents to process */]
  }
}
```

### REFINE_POLICY Workflow
- **Purpose**: Iteratively improve policies with targeted modifications
- **Input**: Policy definition + annotations for specific changes
- **Use Cases**: Kiro CLI suggestions, test-driven improvements, feedback-based refinement
- **Content Structure**: `workflowContent.policyRepairAssets.annotations[]`

**CRITICAL: Complete Policy Definition Required**

ALL build workflows require the COMPLETE existing policy definition in the `policyDefinition` section, not just the changes you want to make.

**REFINE_POLICY Annotation Types:**

**Top-Level Annotations:**
- **Type Management**: `addType`, `updateType`, `deleteType`
- **Variable Management**: `addVariable`, `updateVariable`, `deleteVariable`
- **Rule Management**: `addRule`, `updateRule`, `deleteRule`
- **Natural Language Rules**: `addRuleFromNaturalLanguage`
- **Feedback-Based Updates**: `updateFromRulesFeedback`, `updateFromScenarioFeedback`

**Sub-Operations (only within `updateType`):**
- `addTypeValue`, `updateTypeValue`, `deleteTypeValue` - Used to modify values within an existing custom type

**important**: Only create rules in if/then format.

## Annotation Type Reference

### Type Management Annotations

#### `addType` - Create New Custom Type
```json
{
  "addType": {
    "name": "ApprovalStatus",
    "description": "Status values for approval requests",
    "values": [
      {
        "value": "PENDING",
        "description": "Request is awaiting approval"
      },
      {
        "value": "APPROVED",
        "description": "Request has been approved"
      },
      {
        "value": "REJECTED",
        "description": "Request has been rejected"
      }
    ]
  }
}
```

#### `updateType` - Modify Existing Custom Type
```json
{
  "updateType": {
    "name": "ApprovalStatus",
    "newName": "RequestStatus",
    "description": "Updated status values for all request types",
    "values": [
      {
        "addTypeValue": {
          "value": "ESCALATED",
          "description": "Request escalated to higher authority"
        }
      },
      {
        "updateTypeValue": {
          "value": "PENDING",
          "newValue": "WAITING",
          "description": "Request is waiting for review"
        }
      },
      {
        "deleteTypeValue": {
          "value": "REJECTED"
        }
      }
    ]
  }
}
```

#### `deleteType` - Remove Custom Type
```json
{
  "deleteType": {
    "name": "ObsoleteType"
  }
}
```

### Variable Management Annotations

#### `addVariable` - Create New Variable
```json
{
  "addVariable": {
    "name": "requestAmount",
    "type": "real",
    "description": "The monetary amount of the approval request in USD"
  }
}
```

#### `updateVariable` - Modify Existing Variable
```json
{
  "updateVariable": {
    "name": "requestAmount",
    "newName": "approvalAmount",
    "description": "The monetary amount requiring approval in USD (updated description)"
  }
}
```

#### `deleteVariable` - Remove Variable
```json
{
  "deleteVariable": {
    "name": "obsoleteVariable"
  }
}
```

### Rule Management Annotations

#### `addRule` - Create New Rule (SMT-LIB)
```json
{
  "addRule": {
    "expression": "(=> (and (= userRole MANAGER) (< requestAmount 10000)) (not approvalRequired))"
  }
}
```

#### `updateRule` - Modify Existing Rule
```json
{
  "updateRule": {
    "ruleId": "A1B2C3D4E5F6",
    "expression": "(=> (and (= userRole MANAGER) (< requestAmount 5000)) (not approvalRequired))"
  }
}
```

#### `deleteRule` - Remove Rule
```json
{
  "deleteRule": {
    "ruleId": "G7H8I9J0K1L2"
  }
}
```

### Natural Language Rule Creation

#### `addRuleFromNaturalLanguage` - Convert Natural Language to Rule
```json
{
  "addRuleFromNaturalLanguage": {
    "naturalLanguage": "Managers can approve expense requests up to $5,000 without additional authorization. Senior managers can approve up to $25,000."
  }
}
```

### Feedback-Based Updates

#### `updateFromRulesFeedback` - Improve Rules Based on Performance
```json
{
  "updateFromRulesFeedback": {
    "ruleIds": ["A1B2C3D4E5F6", "G7H8I9J0K1L2"],
    "feedback": "These rules are too restrictive for emergency scenarios. Add exception handling for urgent requests with proper escalation paths."
  }
}
```

#### `updateFromScenarioFeedback` - Improve Based on Test Scenarios
```json
{
  "updateFromScenarioFeedback": {
    "ruleIds": ["A1B2C3D4E5F6"],
    "scenarioExpression": "(and (= requestType EMERGENCY) (= userRole MANAGER) (> requestAmount 10000))",
    "feedback": "Emergency requests should have different approval thresholds. Current rule blocks legitimate emergency expenses."
  }
}
```

**Important**: Do NOT use `get-automated-reasoning-policy-annotations` or `update-automated-reasoning-policy-annotations` for the `REFINE_POLICY` workflow. Annotations are passed directly in the `start-automated-reasoning-policy-build-workflow` call.

## Common Workflows

### 1. Getting Started (New Policy)

**CRITICAL: Always Create Policy First**

You must create a policy before starting any build workflows.

```bash
# Step 1: Create initial policy (REQUIRED FIRST STEP)
aws bedrock create-automated-reasoning-policy \
  --region us-west-2 \
  --name "YourPolicyName"

# Step 2: Extract the policyArn from the response above, then start build workflow
aws bedrock start-automated-reasoning-policy-build-workflow \
  --region us-west-2 \
  --policy-arn "arn:aws:bedrock:us-west-2:123456789012:automated-reasoning-policy/abcd1234efgh" \
  --build-workflow-type INGEST_CONTENT \
  --source-content <policy-definition>

# Step 3: Get build results
aws bedrock get-automated-reasoning-policy-build-workflow-result-assets \
  --region us-west-2 \
  --policy-arn "arn:aws:bedrock:us-west-2:123456789012:automated-reasoning-policy/abcd1234efgh" \
  --build-workflow-id <workflow-id>
```

### 2. Building Policy from Document

**RECOMMENDED: Using CLI Input JSON File**

```bash
# Step 1: Encode PDF to base64 and create JSON file with base64 content
PDF_BASE64=$(base64 -i your-policy.pdf | tr -d '\n')

cat > ingest-policy.json << EOF
{
  "policyArn": "arn:aws:bedrock:us-west-2:123456789012:automated-reasoning-policy/your-actual-policy-id",
  "buildWorkflowType": "INGEST_CONTENT",
  "sourceContent": {
    "policyDefinition": {
      "version": "1.0",
      "types": [],
      "rules": [],
      "variables": []
    },
    "workflowContent": {
      "documents": [
        {
          "document": "$PDF_BASE64",
          "documentContentType": "pdf",
          "documentName": "Company Policy Document",
          "documentDescription": "Main policy document containing business rules and organizational guidelines."
        }
      ]
    }
  }
}
EOF

# Step 2: Use the JSON file
aws bedrock start-automated-reasoning-policy-build-workflow \
  --region us-west-2 \
  --cli-input-json file://ingest-policy.json
```

### 3. Policy Development Cycle

```bash
# 1. Import/process policy definition
aws bedrock start-automated-reasoning-policy-build-workflow \
  --build-workflow-type IMPORT_POLICY

# 2. Update DRAFT with processed definition
aws bedrock update-automated-reasoning-policy \
  --policy-arn <unversioned-arn> \
  --policy-definition <build-output>

# 3. Create versioned snapshot of DRAFT
aws bedrock create-automated-reasoning-policy-version \
  --policy-arn <unversioned-arn>
```

## Testing Workflow

### Primary Approach: Scenarios API (Recommended)

Use `get-automated-reasoning-policy-next-scenario` for comprehensive policy validation.

The Scenarios API is superior for testing because it:
- Tests formal logic directly - Validates policy rules work correctly
- AI-generated scenarios - Comprehensive coverage of edge cases and rule interactions
- Targets specific rules - Tests individual rules and combinations
- Always works - No natural language translation issues
- Intelligent test generation - AI understands policy logic deeply

```bash
# Generate intelligent test scenarios automatically
aws bedrock get-automated-reasoning-policy-next-scenario \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --build-workflow-id "workflow-123"
```

### Secondary Approach: Test Cases (User Experience)

Use manual test cases to validate natural language translation.

```bash
# Create test cases for natural language validation
aws bedrock create-automated-reasoning-policy-test-case \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --guard-content "It is 2:30 PM on a clear day" \
  --query-content "What color should the sky be?" \
  --expected-aggregated-findings-result "VALID"
```

### Test Result Analysis and Troubleshooting

**Understanding Test Results:**

**Scenarios API Results:**
- `expectedResult: SATISFIABLE` - Policy logic works correctly
- API errors or logic conflicts - Policy needs fixing with REFINE_POLICY

**Common Test Case Failure Modes:**

1. **TRANSLATION_AMBIGUOUS**
   - Problem: AI can't map natural language to policy variables
   - Solution: Improve variable descriptions with more natural language synonyms

2. **SATISFIABLE when expecting VALID**
   - Problem: Your expected result label is likely WRONG, not the policy
   - SATISFIABLE = "This scenario is logically consistent with the policy rules"
   - VALID = "This is the correct/expected answer according to the policy"
   - Solution: Change `expectedAggregatedFindingsResult` from `VALID` to `SATISFIABLE`

3. **Empty testFindings arrays**
   - Problem: Translation issues, not rule violations
   - Solution: Focus on improving natural language descriptions, not policy logic

## Build Workflow Monitoring

**Critical Build Limits**: The API supports maximum 2 total build workflows per policy, with only 1 allowed to be IN_PROGRESS at any time. When a build workflow completes, you can instruct the user to review the output using the console. 

### Check Build Status

```bash
aws bedrock get-automated-reasoning-policy-build-workflow \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --build-workflow-id "workflow-123"
```

### List Build History

```bash
aws bedrock list-automated-reasoning-policy-build-workflows \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --max-results 50
```

### Best Practice: Clean Build Management

```bash
# 1. Check existing builds before starting new ones
aws bedrock list-automated-reasoning-policy-build-workflows \
  --policy-arn <policy-arn> \
  --max-results 10

# 2. Delete old/completed builds if you have 2 already
aws bedrock delete-automated-reasoning-policy-build-workflow \
  --policy-arn <policy-arn> \
  --build-workflow-id "old-workflow-id" \
  --last-updated-at "2025-11-15T00:41:18.608000+00:00"

# 3. Now start your new build
aws bedrock start-automated-reasoning-policy-build-workflow \
  --policy-arn <policy-arn> \
  --build-workflow-type INGEST_CONTENT \
  --source-content <content>
```

## Build Workflow Assets

After a build workflow completes successfully, you can retrieve various assets. After you complete a build workflow, you can ask the user to check the build diff using the Automated Reasoning checks console.

### Asset Types

#### 1. POLICY_DEFINITION - The Main Output

```bash
aws bedrock get-automated-reasoning-policy-build-workflow-result-assets \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --build-workflow-id "workflow-123" \
  --asset-type "POLICY_DEFINITION"
```

**What it contains:**
- Compiled policy with extracted/refined rules, variables, and types
- SMT-LIB expressions for all rules
- Complete policy structure ready for deployment

#### 2. BUILD_LOG - Build Process Details

```bash
aws bedrock get-automated-reasoning-policy-build-workflow-result-assets \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --build-workflow-id "workflow-123" \
  --asset-type "BUILD_LOG"
```

**What it shows:**
- Document processing steps - What content was analyzed
- Extraction results - What rules, variables, and types were found
- Processing warnings - Content that couldn't be interpreted
- Success/failure status for each extraction step

#### 3. QUALITY_REPORT - Policy Quality Analysis

```bash
aws bedrock get-automated-reasoning-policy-build-workflow-result-assets \
  --policy-arn "arn:aws:bedrock:region:account:automated-reasoning-policy/policy-id" \
  --build-workflow-id "workflow-123" \
  --asset-type "QUALITY_REPORT"
```

**What it contains:**
- Conflicting rules - Rules that contradict each other
- Unused variables - Variables not referenced by any rules
- Unused type values - Enum values not used in rules
- Disjoint rule sets - Groups of rules that don't interact
