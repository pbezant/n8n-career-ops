# Fix Pipeline — Autonomous n8n Debug Loop

Autonomously run Workflow 01 (Core Pipeline), diagnose failures, apply fixes, and repeat until the workflow succeeds end-to-end or a stopping condition is met.

## What this skill does

1. Fetches the latest workflow state from n8n
2. Triggers a test execution via the n8n UI (browser click) or monitors latest execution
3. Polls until the execution completes
4. Reads per-node results and identifies the first failing node
5. Diagnoses the error using the node's code, parameters, and error message
6. Applies a targeted fix via the n8n PUT API
7. Repeats from step 2, up to 10 iterations

## Instructions

You are an autonomous n8n pipeline debugger. Follow this loop:

### Environment
- n8n API base: `http://localhost:5678/api/v1`
- Auth: `X-N8N-API-KEY: $N8N_API_KEY`
- Workflow ID: `u1bV8KbKeXtNM8Xa`
- Working file: `/tmp/wf01_fixed.json`

### Loop steps

**Step 1 — Get baseline execution ID**
```bash
curl -s "http://localhost:5678/api/v1/executions?workflowId=u1bV8KbKeXtNM8Xa&limit=1" -H "X-N8N-API-KEY: $N8N_API_KEY"
```
Record the latest execution ID.

**Step 2 — Trigger execution**
Tell the user: "Please click 'Execute workflow' in the n8n UI now." Then poll for a new execution ID > the baseline.

**Step 3 — Poll until done**
```bash
curl -s "http://localhost:5678/api/v1/executions?workflowId=u1bV8KbKeXtNM8Xa&limit=1" -H "X-N8N-API-KEY: $N8N_API_KEY"
```
Poll every 5s. Wait for status != "running".

**Step 4 — Read results**
```bash
curl -s "http://localhost:5678/api/v1/executions/{ID}?includeData=true" -H "X-N8N-API-KEY: $N8N_API_KEY"
```
Extract: `lastNodeExecuted`, per-node item counts, per-node error messages.

**Step 5 — If success**: STOP. Report which nodes ran and how many items flowed through.

**Step 6 — If error**:
- Identify the failing node and its exact error message
- Fetch the current workflow JSON and inspect that node's parameters and code
- Apply the minimal fix needed (edit jsCode, fix field names, fix connections, etc.)
- Push via PUT (use ALLOWED_KEYS: name, nodes, connections, settings; filter settings to: executionOrder, saveManualExecutions, callerPolicy, errorWorkflow, timezone)
- Report what was fixed
- Loop back to Step 2

### Known issues and fixes

| Error | Node | Fix |
|-------|------|-----|
| "No prompt specified" (chatInput/guardrailsInput) | Any Agent | Set `promptType: "define"` in parameters |
| "No prompt specified" after UI save | Any Agent | Re-push systemMessage from `prompts/*.md` |
| "WorkflowHasIssuesError" | — | Check node.issues in UI; common cause: invalid credential or bad parameter |
| "Cannot read properties of undefined" | Code node | Node reference `$('NodeName')` — check node name matches exactly |
| Port wiring wrong (0 items to agent) | splitInBatches | Items on port 1, done on port 0 — check main[0] vs main[1] |
| Field not found (`$json.Title` undefined) | Agent text | Sheet columns are lowercase — use `$json.title` not `$json.Title` |
| Dedup not working | Dedup Filter | Column name mismatch — `dedupKey` vs `'Dedup Key'` |

### Important rules
- ALWAYS fetch the live workflow before editing (never edit stale `/tmp/wf01_fixed.json` blindly)
- ALWAYS preserve user's model names (e.g. `gemini-flash-lite-latest`) — don't overwrite them
- After any agent systemMessage push, verify with a GET that chars > 0
- If the Pipeline sheet has > 200 rows with status "New", alert the user — data has accumulated from failed runs
- Never edit the sheet directly; fix the code to prevent re-accumulation

### Stopping conditions
- Workflow completes with `status: success` and all expected nodes ran ✓
- Same error repeats 3 times after attempted fixes (escalate to user)
- 10 iterations reached without success (report all attempted fixes)

$input
