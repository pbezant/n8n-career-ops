# Career-Ops Dashboard — n8n Multi-Agent Job Search Pipeline

Automated job search pipeline built on n8n, powered by Gemini 2.0 Flash Lite. Scans 40+ ATS platforms daily using Google's `site:` search strategy, evaluates listings across 10 dimensions, and generates personalized CVs and cover letters — with human-in-the-loop review before every submission.

Inspired by [Career-Ops (santifer.io)](https://github.com/santifer-io/career-ops) and [briansjobsearch.com](https://briansjobsearch.com).

---

## Quick Start

1. **Set up n8n** (self-hosted Docker recommended)
2. **Configure credentials** → See [docs/CREDENTIALS.md](docs/CREDENTIALS.md)
3. **Run the Sheet setup script** → `cd scripts && npm install && npm run setup-sheet`
4. **Import workflows** → Import each JSON from `workflows/` into n8n
5. **Paste prompts** → Copy each `prompts/*.md` into the matching AI Agent node's System Message field
6. **Verify** → Follow the checklist in [docs/SETUP.md](docs/SETUP.md)

---

## Architecture

4 n8n workflows, each triggered differently, with AI agents chained inline:

| # | Workflow | Trigger | Purpose |
|---|---------|---------|---------|
| 01 | Core Pipeline | Cron (daily) | Scan → Pre-Screen → Evaluate → Generate CV + Cover Letter → Notify |
| 02 | Ad-Hoc Pipeline | Webhook | Evaluate any single job URL on demand |
| 03 | Interview Prep | Webhook | Research company + generate interview Q&A |
| 04 | Comparison | Webhook | Side-by-side comparison of multiple job offers |

Full design details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## n8n Instance

- **URL:** `http://localhost:5678`
- **Credentials:** See [docs/CREDENTIALS.md](docs/CREDENTIALS.md)

---

## ⚠️ Important: Prompts Do NOT Auto-Sync

The `prompts/*.md` files are the **source of truth** for editing agent behavior. They are NOT read by n8n at runtime. After editing any prompt:

1. Open the matching AI Agent node in n8n
2. Paste the updated content into the "System Message" field
3. Save the workflow
4. Re-export the workflow JSON to `workflows/`

---

## Structure

```
n8n-career-ops/
├── Full CV.md                    # CV source of truth
├── README.md
├── .gitignore
├── workflows/                    # Import these into n8n
│   ├── 01-core-pipeline.json
│   ├── 02-adhoc-pipeline.json
│   ├── 03-interview-prep.json
│   └── 04-comparison.json
├── prompts/                      # Paste into AI Agent System Message fields
│   ├── pre-screen-system.md
│   ├── evaluator-system.md
│   ├── cv-generator-system.md
│   ├── cover-letter-system.md
│   ├── apply-assistant-system.md
│   ├── deep-research-system.md
│   ├── interview-prep-system.md
│   └── comparison-system.md
├── scripts/
│   ├── setup-google-sheet.js     # One-off script to create the Google Sheet
│   ├── package.json
│   └── .env.example
└── docs/
    ├── SETUP.md
    ├── CREDENTIALS.md
    └── ARCHITECTURE.md
```
