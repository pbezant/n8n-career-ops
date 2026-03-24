Generate interview preparation materials using the Interview Prep workflow (Workflow 03).

## Instructions

1. The user provides a job ID they want to prepare for
2. Ensure SSH tunnel is active
3. POST to the interview prep webhook:

```bash
curl -s -X POST http://localhost:5678/webhook/interview-prep \
  -H "Content-Type: application/json" \
  -d '{"jobId": "$ARGUMENTS"}'
```

4. Parse and present the prep materials:
   - Company research summary (funding, news, tech stack, Glassdoor)
   - 10-15 likely interview questions with STAR-format answers
   - Red flags to watch for
   - Talking points aligned to the role
   - Questions to ask the interviewer

5. On error, check execution logs for workflow `i0jSDZ7RUx4b2ZqW`

## Input
- `$ARGUMENTS`: A job ID from the Pipeline/Evaluations sheet
