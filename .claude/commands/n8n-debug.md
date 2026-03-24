Debug n8n workflow execution failures.

## Instructions

1. If `$ARGUMENTS` provides an execution ID, fetch that specific execution:
```bash
curl -s "http://localhost:5678/api/v1/executions/$ARGUMENTS" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.'
```

2. If no execution ID, find recent failures:
```bash
curl -s "http://localhost:5678/api/v1/executions?status=error&limit=10" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data[] | {id, workflow: .workflowData.name, startedAt, stoppedAt}'
```

3. For each failed execution, examine:
   - Which node failed (look at `data.resultData.error`)
   - Error message and stack trace
   - Input data to the failed node
   - Previous node outputs

4. Common failure patterns:
   - **Gemini 429**: Rate limited — check daily usage against 1,500 req/day free tier
   - **Gemini 500**: Transient — retry once
   - **Google Sheets 403**: OAuth token expired — re-auth in n8n credentials
   - **SerpAPI/CSE 403**: Quota exceeded — check daily budget
   - **Webhook timeout**: Workflow took too long — check Split-in-Batches batch size

5. Suggest fixes based on the error pattern and offer to apply them.

## Input
- `$ARGUMENTS`: Optional — an execution ID to inspect. If omitted, shows recent failures.
