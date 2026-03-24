Import workflow JSON files into n8n via the REST API.

## Instructions

1. Determine which workflow to import. If `$ARGUMENTS` is provided, match it:
   - `01` or `core` → `workflows/01-core-pipeline.json`
   - `02` or `adhoc` → `workflows/02-adhoc-pipeline.json`
   - `03` or `interview` or `prep` → `workflows/03-interview-prep.json`
   - `04` or `compare` or `comparison` → `workflows/04-comparison.json`
   - If omitted, import all 4.

2. Use the existing import script:
```bash
python3 scripts/import-workflows.py
```

Or import individually via API:
```bash
# Read workflow JSON, strip to allowed keys, POST
cat workflows/FILENAME.json | \
  jq '{name, nodes, connections, settings, staticData, pinData, tags}' | \
  curl -s -X POST "http://localhost:5678/api/v1/workflows" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

3. To UPDATE an existing workflow (instead of creating new):
```bash
cat workflows/FILENAME.json | \
  jq '{name, nodes, connections, settings, staticData, pinData, tags}' | \
  curl -s -X PUT "http://localhost:5678/api/v1/workflows/WORKFLOW_ID" \
    -H "X-N8N-API-KEY: $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @-
```

4. Report success/failure for each workflow and the assigned n8n IDs.

## Input
- `$ARGUMENTS`: Optional — workflow number (`01`-`04`) or name. If omitted, imports all.
