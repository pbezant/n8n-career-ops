Sync prompt files from `prompts/*.md` into n8n AI Agent nodes via the n8n API.

## Instructions

This skill automates the most painful manual step: keeping `prompts/*.md` in sync with n8n AI Agent node system messages.

1. If `$ARGUMENTS` specifies a prompt file, sync only that one. Otherwise sync all.

2. The prompt-to-workflow mapping:

| Prompt File | Workflow | Workflow ID | Agent Node Name |
|-------------|----------|-------------|-----------------|
| `pre-screen-system.md` | 01 Core | `u1bV8KbKeXtNM8Xa` | Pre-Screen Agent |
| `evaluator-system.md` | 01 Core | `u1bV8KbKeXtNM8Xa` | Evaluator Agent |
| `cv-generator-system.md` | 01 Core | `u1bV8KbKeXtNM8Xa` | CV Generator Agent |
| `cover-letter-system.md` | 01 Core | `u1bV8KbKeXtNM8Xa` | Cover Letter Agent |
| `apply-assistant-system.md` | 01 Core | `u1bV8KbKeXtNM8Xa` | Apply Prep Agent |
| `evaluator-system.md` | 02 Ad-Hoc | `vEkezsBAtnIZu2lx` | Evaluator Agent |
| `cv-generator-system.md` | 02 Ad-Hoc | `vEkezsBAtnIZu2lx` | CV Generator Agent |
| `cover-letter-system.md` | 02 Ad-Hoc | `vEkezsBAtnIZu2lx` | Cover Letter Agent |
| `deep-research-system.md` | 03 Prep | `i0jSDZ7RUx4b2ZqW` | Deep Research Agent |
| `interview-prep-system.md` | 03 Prep | `i0jSDZ7RUx4b2ZqW` | Interview Prep Agent |
| `comparison-system.md` | 04 Compare | `kxMTsL7S1BpDWTn0` | Comparison Agent |

3. For each prompt to sync:
   a. Read the prompt file content
   b. GET the workflow JSON from n8n API
   c. Find the matching AI Agent node by name
   d. Update the node's `parameters.text` or `parameters.systemMessage` field
   e. PUT the updated workflow back

4. Use `scripts/sync-prompts.py` if available, otherwise do it manually via curl:

```bash
# Get workflow
WF=$(curl -s "http://localhost:5678/api/v1/workflows/WORKFLOW_ID" \
  -H "X-N8N-API-KEY: $N8N_API_KEY")

# Update with jq and PUT back
echo "$WF" | jq '.nodes |= map(if .name == "AGENT_NAME" then .parameters.systemMessage = "NEW_CONTENT" else . end)' | \
curl -s -X PUT "http://localhost:5678/api/v1/workflows/WORKFLOW_ID" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @-
```

5. Report which prompts were synced and verify the update.

## Input
- `$ARGUMENTS`: Optional — a specific prompt filename (e.g., `evaluator-system.md`). If omitted, syncs all.
