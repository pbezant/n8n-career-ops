View the current status of the job search pipeline and evaluations.

## Instructions

1. Check n8n connectivity first:
```bash
curl -s "http://localhost:5678/api/v1/workflows" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data | length'
```

2. Get recent execution history across all workflows:
```bash
curl -s "http://localhost:5678/api/v1/executions?limit=20" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data[] | {id, workflowId: .workflowData.name, status, startedAt, stoppedAt}'
```

3. Check which workflows are active:
```bash
for id in u1bV8KbKeXtNM8Xa vEkezsBAtnIZu2lx i0jSDZ7RUx4b2ZqW kxMTsL7S1BpDWTn0; do
  curl -s "http://localhost:5678/api/v1/workflows/$id" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '{name: .name, active: .active}'
done
```

4. Present a summary dashboard:
   - Active/inactive workflow status
   - Last scan time and result
   - Recent execution success/failure counts
   - Any errors that need attention

## Input
- `$ARGUMENTS`: Optional — "executions", "workflows", or "errors" to focus the report. Default shows all.
