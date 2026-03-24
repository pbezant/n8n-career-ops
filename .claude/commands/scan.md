Trigger or check the core pipeline scan (Workflow 01).

## Instructions

1. Ensure the SSH tunnel is active
2. Check the workflow status:
```bash
curl -s "http://localhost:5678/api/v1/workflows/u1bV8KbKeXtNM8Xa" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '{name: .name, active: .active}'
```

3. To manually trigger (activate if not active):
```bash
# Activate the workflow
curl -s -X POST "http://localhost:5678/api/v1/workflows/u1bV8KbKeXtNM8Xa/activate" \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

4. Check recent executions:
```bash
curl -s "http://localhost:5678/api/v1/executions?workflowId=u1bV8KbKeXtNM8Xa&limit=5" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data[] | {id, status: .status, startedAt: .startedAt, stoppedAt: .stoppedAt}'
```

5. Report:
   - Whether the workflow is active/inactive
   - Last execution time and status
   - Any errors from recent runs

## Input
- `$ARGUMENTS`: Optional — "status" (default), "activate", "deactivate", or "history"
