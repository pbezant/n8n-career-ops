# Career-Ops — n8n Multi-Agent Job Search Pipeline

Automated job search pipeline on n8n + Gemini 2.0 Flash Lite. Scans 40+ ATS platforms, evaluates across 10 dimensions, generates tailored CVs/cover letters. HITL before every submission.

## n8n Connectivity

The n8n instance runs on a home server. To access from localhost:

```bash
ssh -L 5678:localhost:5678 root@192.168.1.243
```

- **UI:** http://localhost:5678
- **API Base:** http://localhost:5678/api/v1
- **Auth Header:** `X-N8N-API-KEY` (value in env var `N8N_API_KEY`)

## Workflow Map

| # | Workflow | n8n ID | Trigger | Agents |
|---|---------|--------|---------|--------|
| 01 | Core Pipeline | `u1bV8KbKeXtNM8Xa` | Cron 7am daily | Pre-Screen → Evaluator → CV Gen → Cover Letter → Apply Prep |
| 02 | Ad-Hoc Pipeline | `vEkezsBAtnIZu2lx` | Webhook `POST /webhook/adhoc-eval` | Evaluator → CV Gen → Cover Letter |
| 03 | Interview Prep | `i0jSDZ7RUx4b2ZqW` | Webhook `POST /webhook/interview-prep` | Deep Research → Interview Prep |
| 04 | Comparison | `kxMTsL7S1BpDWTn0` | Webhook `POST /webhook/compare` | Comparison Agent |

## Credentials (in n8n)

| Credential | n8n ID | Status |
|------------|--------|--------|
| Google Gemini API | `T6vrBWXANAVPKppK` | Configured |
| Google Sheets OAuth2 | `ng8zlg2pDNctkqmp` | Configured |
| Discord Bot | `PeIukwvkJqSyArKV` | Configured |
| SerpAPI | — | **Needed** |
| html2pdf.app | — | **Needed** (optional) |

## File Conventions

### Source of Truth
- `prompts/*.md` — Agent system prompts. Edit here FIRST, then sync to n8n.
- `Full CV.md` — Preston's CV, used by all CV-aware agents.
- `workflows/*.json` — Importable workflow definitions.

### Prompt Sync (Critical)
Prompts do NOT auto-sync to n8n. Use the `/prompt-sync` skill or manually:
1. Edit the `prompts/*.md` file
2. Use n8n API to update the matching AI Agent node's `systemMessage`
3. Or: paste into n8n UI → Save → Re-export JSON

### File Ownership
| Files | Edited by | Notes |
|-------|-----------|-------|
| `prompts/*.md` | Claude Code / human | Source of truth for agent behavior |
| `workflows/*.json` | n8n export | Don't hand-edit; export from n8n after changes |
| `scripts/*.py` | Claude Code / human | Utilities for n8n API interaction |
| `Full CV.md` | Human | Preston's master CV |
| `docs/*` | Claude Code / human | Architecture and setup docs |

## Claude Code Skills

Available skills (invoke via `/skill-name`):
- `/eval` — Evaluate a single job URL via ad-hoc webhook
- `/scan` — Trigger or check core pipeline scan results
- `/compare` — Compare multiple jobs side-by-side
- `/interview-prep` — Generate interview prep for a job
- `/cv-tailor` — Re-generate tailored CV for a specific job
- `/prompt-sync` — Push prompt files into n8n AI Agent nodes via API
- `/workflow-export` — Export workflow from n8n to `workflows/` JSON
- `/workflow-import` — Import workflow JSONs into n8n
- `/dashboard` — View pipeline and evaluation status
- `/n8n-debug` — Check execution logs and diagnose failures

## Testing Webhooks

```bash
# Ad-hoc evaluate a job
curl -X POST http://localhost:5678/webhook/adhoc-eval \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/job-posting"}'

# Interview prep
curl -X POST http://localhost:5678/webhook/interview-prep \
  -H "Content-Type: application/json" \
  -d '{"jobId": "JOB_ID_HERE"}'

# Compare offers
curl -X POST http://localhost:5678/webhook/compare \
  -H "Content-Type: application/json" \
  -d '{"jobIds": ["ID1", "ID2", "ID3"]}'
```

## Architecture

- 4 n8n workflows with inline AI agents (no sub-workflow calls)
- Google Sheets as runtime dashboard (7 tabs: Pipeline, Evaluations, Applications, Config, Comparisons, Archive, Logs)
- 10-dimension scoring: Role Match, Skills, Seniority, Comp, Geographic, Company Stage, PMF, Growth, Interview Likelihood, Timeline
- Gate-pass: Role Match or Skills ≤ 1 → grade capped at D
- Dedup: `company|title|domain` string keys
- Freshness boost: <6h +0.3, 6-24h +0.2

See `docs/ARCHITECTURE.md` for full data flow diagrams.
