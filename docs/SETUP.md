# Setup Guide

## Prerequisites

- n8n running at `http://localhost:5678` (self-hosted Docker recommended)
- Google account with Sheets and Drive access
- Gemini, Discord already configured (see [CREDENTIALS.md](CREDENTIALS.md))

---

## Step 1: Run the Google Sheet Setup Script

```bash
cd scripts
cp .env.example .env
# Edit .env: add your service account key path
npm install
npm run setup-sheet
```

Copy the printed **Spreadsheet ID** — you'll need it in every workflow's Google Sheets nodes.

---

## Step 2: Configure SerpAPI (or Google CSE)

Follow [CREDENTIALS.md](CREDENTIALS.md) to add the SerpAPI credential. Then in the Config tab of your sheet, add a row:
- Key: `cse_engine_id` | Value: your Google CSE engine ID (if using CSE)

---

## Step 3: Import Workflows into n8n

**Already done!** Workflows were imported via the API and are live at:

| Workflow | n8n ID | URL |
|---------|--------|-----|
| 01 - Core Pipeline | `u1bV8KbKeXtNM8Xa` | http://localhost:5678/workflow/u1bV8KbKeXtNM8Xa |
| 02 - Ad-Hoc Pipeline | `vEkezsBAtnIZu2lx` | http://localhost:5678/workflow/vEkezsBAtnIZu2lx |
| 03 - Interview Prep | `i0jSDZ7RUx4b2ZqW` | http://localhost:5678/workflow/i0jSDZ7RUx4b2ZqW |
| 04 - Comparison | `kxMTsL7S1BpDWTn0` | http://localhost:5678/workflow/kxMTsL7S1BpDWTn0 |

To re-import from scratch: `python3 scripts/import-workflows.py`

---

## Step 4: Update Spreadsheet ID in Each Workflow

After importing, open each workflow and find every Google Sheets node. Set the `documentId` to your Career-Ops Dashboard spreadsheet ID.

---

## Step 5: Paste Prompts into AI Agent Nodes

For each workflow, open each AI Agent node → "System Message" tab → paste the content from the matching `prompts/*.md` file.

| Workflow | Node | Prompt File |
|---------|------|------------|
| 01 | Pre-Screen AI Agent | `prompts/pre-screen-system.md` |
| 01 | Evaluator AI Agent | `prompts/evaluator-system.md` |
| 01 | CV Generator AI Agent | `prompts/cv-generator-system.md` |
| 01 | Cover Letter AI Agent | `prompts/cover-letter-system.md` |
| 01 | Apply Prep AI Agent | `prompts/apply-assistant-system.md` |
| 02 | Evaluator AI Agent | `prompts/evaluator-system.md` |
| 02 | CV Generator AI Agent | `prompts/cv-generator-system.md` |
| 02 | Cover Letter AI Agent | `prompts/cover-letter-system.md` |
| 03 | Deep Research AI Agent | `prompts/deep-research-system.md` |
| 03 | Interview Prep AI Agent | `prompts/interview-prep-system.md` |
| 04 | Comparison AI Agent | `prompts/comparison-system.md` |

---

## Step 6: Credential Verification Checklist

Run each of these test checks in n8n before activating workflows:

- [ ] **Google Sheets:** Create a test workflow → Sheets read node → read Config tab → verify rows returned
- [ ] **Gemini:** Create a test workflow → AI Agent → Gemini Flash Lite sub-node → send "Respond with OK" → verify response
- [ ] **SerpAPI/CSE:** Test HTTP Request node → call SerpAPI with query `"Product Designer" site:greenhouse.io` → verify JSON results with organic results
- [ ] **Discord:** Test Discord node → post a test message to your job-alerts channel → verify it appears
- [ ] **Webhook Auth:** `curl -X POST http://localhost:5678/webhook/adhoc-eval -H "X-API-Key: YOUR_KEY" -H "Content-Type: application/json" -d '{"url":"https://example.com"}'` → should return 200 (or processing response)

---

## Step 7: Configure Config Tab

Open the Career-Ops Dashboard spreadsheet → Config tab. Verify these rows are present and correct:

| Key | Default Value | Notes |
|-----|--------------|-------|
| `job_titles` | `Product Designer,UX Designer,IoT Engineer,Creative Technologist,Front End Developer` | Comma-separated |
| `locations` | `remote,Austin TX` | Comma-separated |
| `salary_min` | `120000` | Annual USD |
| `salary_max` | `180000` | Annual USD |
| `remote_preference` | `remote_first` | remote_first \| hybrid \| onsite |
| `score_threshold` | `4.0` | Min score to generate CV (1-5 scale) |
| `scan_budget_daily` | `200` | Max CSE/SerpAPI queries per day |
| `generate_pdf` | `false` | true if html2pdf.app is configured |
| `scan_frequency` | `daily` | daily \| twice_daily |
| `cse_engine_id` | `YOUR_CSE_ID` | Google Custom Search engine ID |

---

## Webhook URL Reference

| Webhook | URL | Payload |
|---------|-----|---------|
| Ad-Hoc Eval | `http://localhost:5678/webhook/adhoc-eval` | `{"url": "https://job-url"}` |
| Interview Prep | `http://localhost:5678/webhook/interview-prep` | `{"job_id": "greenhouse_20260318_a1b2"}` |
| Comparison | `http://localhost:5678/webhook/compare` | `{"job_ids": ["id1", "id2", "id3"]}` |

All webhooks require header: `X-API-Key: YOUR_WEBHOOK_AUTH_KEY`

### iOS Shortcut Example (Ad-Hoc Eval)
```
URL: http://localhost:5678/webhook/adhoc-eval
Method: POST
Headers: X-API-Key: YOUR_KEY, Content-Type: application/json
Body: {"url": "[Shortcut Input URL]"}
```

---

## n8n Environment Variables (self-hosted)

Add to your n8n Docker `.env` or compose file:

```
EXECUTIONS_TIMEOUT=3600
EXECUTIONS_TIMEOUT_MAX=3600
N8N_PAYLOAD_SIZE_MAX=16
```

---

## Update Workflow: Prompt Sync Procedure

When you edit a `prompts/*.md` file:
1. Edit the `.md` file
2. Copy full content
3. Open the matching AI Agent node in n8n → System Message tab → paste
4. Save the workflow
5. Re-export: n8n → Workflow menu → Download → save to `workflows/`
