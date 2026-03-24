Evaluate a single job URL using the ad-hoc pipeline (Workflow 02).

## Instructions

1. The user will provide a job posting URL
2. Ensure the SSH tunnel is active (test with `curl -s http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data | length'`)
3. POST the URL to the ad-hoc webhook:

```bash
curl -s -X POST http://localhost:5678/webhook/adhoc-eval \
  -H "Content-Type: application/json" \
  -d '{"url": "$ARGUMENTS"}'
```

4. Parse the response and present the evaluation:
   - Overall score and grade (A-F)
   - 10-dimension breakdown
   - Role archetype match
   - Key strengths and gaps
   - Recommendation (apply / skip / maybe)

5. If the webhook returns an error, check n8n execution logs:
```bash
curl -s "http://localhost:5678/api/v1/executions?workflowId=vEkezsBAtnIZu2lx&limit=1" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.data[0].status'
```

## Input
- `$ARGUMENTS`: A job posting URL (e.g., `https://boards.greenhouse.io/company/jobs/12345`)
