Export a workflow from n8n and save it to the `workflows/` directory.

## Instructions

1. Determine which workflow to export. If `$ARGUMENTS` is provided, match it:
   - `01` or `core` → `u1bV8KbKeXtNM8Xa` → `workflows/01-core-pipeline.json`
   - `02` or `adhoc` → `vEkezsBAtnIZu2lx` → `workflows/02-adhoc-pipeline.json`
   - `03` or `interview` or `prep` → `i0jSDZ7RUx4b2ZqW` → `workflows/03-interview-prep.json`
   - `04` or `compare` or `comparison` → `kxMTsL7S1BpDWTn0` → `workflows/04-comparison.json`
   - If omitted, export all 4.

2. Fetch from n8n API:
```bash
curl -s "http://localhost:5678/api/v1/workflows/WORKFLOW_ID" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" | jq '.' > workflows/FILENAME.json
```

3. Verify the exported file is valid JSON and report:
   - Number of nodes
   - Workflow name
   - Whether it differs from the previous version (git diff)

## Input
- `$ARGUMENTS`: Optional — workflow number (`01`-`04`) or name. If omitted, exports all.
