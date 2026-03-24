Compare multiple job offers side-by-side using the Comparison workflow (Workflow 04).

## Instructions

1. The user provides job IDs or URLs to compare
2. Ensure SSH tunnel is active
3. POST to the comparison webhook:

```bash
curl -s -X POST http://localhost:5678/webhook/compare \
  -H "Content-Type: application/json" \
  -d '{"jobIds": $ARGUMENTS}'
```

4. Parse and present the comparison:
   - Side-by-side scoring table
   - Trade-offs between offers
   - Ranked recommendation
   - Timeline considerations

5. On error, check execution logs for workflow `kxMTsL7S1BpDWTn0`

## Input
- `$ARGUMENTS`: JSON array of job IDs, e.g., `["ID1", "ID2", "ID3"]`
