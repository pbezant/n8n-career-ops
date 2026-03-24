# Plan: n8n Career-Ops Multi-Agent System

## TL;DR
Build an automated job search pipeline in n8n replicating and improving on santifer.io's Career-Ops system. Uses n8n AI Agent nodes powered by **Gemini Flash Lite** to: scan job boards (using briansjobsearch.com's Google `site:` search strategy across ~40 ATS platforms) → evaluate listings across 10 dimensions → generate personalized CVs → prepare applications. Google Sheets as central dashboard, HITL review before every submission.

**Key improvements over the original Career-Ops:**
- Original is CLI-only (Claude Code in terminal). Ours runs on n8n: visual workflows, scheduled automation, webhook triggers, accessible from any device
- Original uses expensive Claude API. Ours uses Gemini Flash Lite (free/cheap tier)
- Original scans manually. Ours uses briansjobsearch.com's proven Google `site:` strategy across 40+ ATS platforms, automated on a schedule
- Original tracks in TSV files. Ours uses Google Sheets as a live, filterable dashboard

---

## Architecture Overview

### Scanning Strategy (from briansjobsearch.com)
briansjobsearch.com's core trick: it doesn't scrape job boards directly. It generates **Google Search queries using `site:` operators** targeting specific ATS platforms. Example:
- `"Product Designer" site:greenhouse.io remote` (tbs=qdr:d for past 24h)
- `"UX Designer" site:lever.co remote`

This is brilliant because Google has already crawled and indexed these pages. We replicate this in n8n using **SerpAPI** or **Google Custom Search API** to get structured JSON results instead of scraping Google HTML.

### The 40+ ATS/Job Sites (from briansjobsearch.com)
1. Greenhouse (greenhouse.io)
2. Lever (lever.co)
3. Ashby (ashbyhq.com)
4. Pinpoint (pinpointhq.com)
5. Jobs Subdomains (jobs.*)
6. Careers Pages (careers.* OR /careers/ OR /career/)
7. People Subdomains (people.*)
8. Talent Subdomains (talent.*)
9. Paylocity (recruiting.paylocity.com)
10. Keka (keka.com)
11. Workable (jobs.workable.com)
12. BreezyHR (breezy.hr)
13. Wellfound (wellfound.com)
14. Y Combinator (workatastartup.com)
15. Oracle Cloud (oraclecloud.com)
16. Workday (myworkdayjobs.com)
17. Recruitee (recruitee.com)
18. Rippling (rippling.com / rippling-ats.com)
19. Gusto (jobs.gusto.com)
20. CareerPuck (careerpuck.com)
21. Teamtailor (teamtailor.com)
22. SmartRecruiters (jobs.smartrecruiters.com)
23. TalentReef (jobappnetwork.com)
24. Homerun (homerun.co)
25. Gem (gem.com)
26. Trakstar (trakstar.com)
27. Cats (catsone.com)
28. JazzHR (applytojob.com)
29. Jobvite (jobvite.com)
30. iCIMS (icims.com)
31. Dover (dover.io)
32. Notion (notion.site)
33. Builtin (builtin.com/job/)
34. ADP (workforcenow.adp.com / myjobs.adp.com)
35. LinkedIn (linkedin.com/jobs — direct link, not Google site:)
36. Glassdoor (glassdoor.com/job-listing/)
37. Factorial (factorialhr.com)
38. TriNet Hire (trinethire.com)
39. Remote Rocketship (remoterocketship.com)
40. Other Pages (*/employment/*, */opportunities/*, */openings/*, */join-us/*, */work-with-us/*)

### 10-Dimension Scoring (from Career-Ops)
| Dimension | Description | Weight |
|-----------|-------------|--------|
| Role Match | Alignment between JD requirements and CV proof points | Gate-pass |
| Skills Alignment | Tech stack overlap | Gate-pass |
| Seniority | Stretch level and negotiability | High |
| Compensation | Market rate vs. target | High |
| Geographic | Remote/hybrid/onsite feasibility | Medium |
| Company Stage | Startup/growth/enterprise fit | Medium |
| Product-Market Fit | Problem domain resonance | Medium |
| Growth Trajectory | Career ladder visibility | Medium |
| Interview Likelihood | Callback probability | High |
| Timeline | Closing speed and hiring urgency | Low |

Gate-pass means: if Role Match or Skills Alignment scores below 2, the final grade auto-caps at D regardless of other dimensions.

### Role Archetypes (derived from Preston's CV)
1. **Product Designer / UX Lead** — Lowe's Sr Product Designer, Visa UX, Verbosity Sr UX (lead proof point)
2. **IoT Systems Engineer** — StructureSense co-founder, RTLS, LoRaWAN, ESP32, embedded hardware
3. **Creative Technologist / Prototyper** — Bezant Solutions, V0→V1 product development, 3D printing + firmware
4. **Front-End / Web Developer** — BancVue, Gensuite, OSU, Walmart internship (JS/CSS/HTML history)
5. **Design Systems / UX Architect** — Harland Clarke, Lowe's design system work, atomic design

### LLM Choice
- **Primary: Gemini 2.0 Flash Lite** via Google AI Studio API (free tier: 1,500 req/day, paid is very cheap)
- Fallback: OpenAI GPT-4o-mini if needed
- Structured JSON output mode for scoring

### Workflow Architecture: Agent-to-Agent in 4 Workflows

Instead of 10 separate workflows calling each other, we use **4 workflows** with **multiple AI Agent nodes wired together inline**. Each agent's output feeds directly into the next agent's input on the n8n canvas — no Execute Workflow overhead, shared context, single execution log per run.

**Why 4 and not 1?** Each workflow needs a different trigger type. n8n workflows can only have one trigger node.

| # | Workflow | Trigger | Agents Inside (chained inline) |
|---|---------|---------|-------------------------------|
| 01 | **Core Pipeline** | Cron (1x/day) or manual | Scanner logic → Pre-Screen Agent → Evaluator Agent → CV Gen Agent → Cover Letter Agent → Apply Prep Agent → Discord Notify |
| 02 | **Ad-Hoc Pipeline** | Webhook (POST with URL) | Evaluator Agent → CV Gen Agent → Cover Letter Agent → Discord Notify |
| 03 | **Interview Prep** | Webhook (POST with job ID) | Deep Research Agent → Interview Prep Agent |
| 04 | **Comparison** | Webhook (POST with job IDs) | Comparison Agent |

**How agents connect on the canvas:**
- Each AI Agent is a separate **AI Agent node** in n8n with its own system prompt (pasted from `prompts/` drafts in the repo)
- Connected by wires: Agent A's output → Code node (parse/transform) → Agent B's input
- Non-AI steps (HTTP requests, Google Sheets reads/writes, dedup logic) are regular n8n nodes wired between agents
- The whole chain runs in a single execution — one log, one debug view

**Example: Core Pipeline canvas layout:**
```
[Cron Trigger]
  → [Config Loader (Sheets Read)]
  → [Scanner Loop: HTTP Request × Code node (no AI agent — pure logic)]
  → [Dedup Code Node]
  → [Sheets Write: new listings]
  → [Split-in-Batches]
    → [Pre-Screen AI Agent] → filter pass/reject
    → [Sheets Update: status]
    → [HTTP Request: fetch full JD]
    → [JS-rendering fallback Code Node]
    → [Evaluator AI Agent] → scores + report
    → [Freshness Boost Code Node]
    → [Sheets Write: evaluation]
    → [IF score >= threshold]
      → [CV Generator AI Agent] → content JSON
      → [Template Inject Code Node] → HTML
      → [Cover Letter AI Agent] → HTML
      → [Apply Prep AI Agent] → pre-filled answers
      → [Sheets Write: application row]
    → [Discord Webhook: daily digest + alerts]
    → [Cleanup Code Node: archive stale rows]
```

---

## n8n Instance

- **URL:** `http://localhost:5678`
- **API Key:** `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3NzY1YWIxZi1kM2QwLTQwN2QtOTVhZS1iODk5NWM1OWVlZmIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzczODQ1NTkyLCJleHAiOjE3NzYzOTg0MDB9.p7-PIm4dh7SuAExRHqCtX7rUzUmDTPwTS7nEcN_OcZk`
- **API Base:** `http://localhost:5678/api/v1`
- All workflow imports use the REST API: `POST /api/v1/workflows` with `X-N8N-API-KEY` header

---

## Phase 0: Environment Init (copilot-init)

**Goal:** All credentials configured in n8n, Google Sheet dashboard ready, prompt text drafted, and one test workflow verified — before building the real workflows.

### How n8n works (important context)
n8n workflows are built entirely in the n8n UI. At runtime, n8n has **no access to local files** — it can't read YAML, Markdown, or HTML from your project folder. Everything the workflow needs must be:
- **Embedded in workflow nodes** — prompts go in AI Agent node system prompt fields, templates go in Code nodes, site lists go in Code node arrays/objects
- **Stored in Google Sheets** — config values, job titles, thresholds, EEO fields
- **In n8n Credentials store** — all API keys

The **git repo** (`n8n-career-ops/`) is purely for **version control and documentation**:
- Exported workflow JSONs (the actual product — import these into n8n)
- Prompt drafts (source of truth for editing — content gets pasted into AI Agent nodes)
- Reference docs (setup guide, architecture notes)
- The one-off Sheet setup script

> **⚠️ CRITICAL: Prompt files do NOT auto-sync to n8n.**
> The `prompts/*.md` files in this repo are **not read by n8n at runtime**. They exist only for editing convenience and version control. When you change a prompt file, you **must also manually copy-paste** the updated content into the corresponding AI Agent node's "System Message" field in the n8n UI, then re-export the workflow JSON. Editing the `.md` file alone changes nothing in the running workflows.

### Step 0a: Project repo structure
```
n8n-career-ops/
├── Full CV.md                    # Already exists — CV source of truth
├── README.md                     # Project overview, setup instructions
├── .gitignore                    # node_modules/, .env
├── workflows/                    # n8n workflow JSON exports (import into n8n)
│   ├── 01-core-pipeline.json
│   ├── 02-adhoc-pipeline.json
│   ├── 03-interview-prep.json
│   └── 04-comparison.json
├── prompts/                      # Source-of-truth prompt drafts (pasted into AI Agent nodes)
│   ├── pre-screen-system.md
│   ├── evaluator-system.md
│   ├── cv-generator-system.md
│   ├── cover-letter-system.md
│   ├── apply-assistant-system.md
│   ├── deep-research-system.md
│   ├── interview-prep-system.md
│   └── comparison-system.md
├── scripts/
│   ├── setup-google-sheet.js     # One-off Node.js script to create the Google Sheet
│   ├── package.json
│   └── .env.example              # Only for the setup script
└── docs/
    ├── SETUP.md                  # Step-by-step setup guide
    ├── CREDENTIALS.md            # How to get each API key + add to n8n
    └── ARCHITECTURE.md           # System design, data flow diagrams
```

**What lives WHERE at runtime:**
| Data | Where it lives | How n8n accesses it |
|------|---------------|--------------------|
| API keys (Gemini, CSE, Discord, etc.) | n8n Credentials store | Node credential dropdown |
| Job titles, score threshold, salary, EEO | Google Sheets "Config" tab | Sheets Read node at start of each workflow |
| 40+ ATS site list (names, site: operators, tiers) | Code node array in Workflow 01 | Hardcoded JSON array in a Set/Code node |
| Agent system prompts | AI Agent node "System Message" field | Pasted directly into each node |
| CV/Cover Letter HTML templates | Code node string in Workflow 01/02 | Template literal in the Code node |
| Full CV text | AI Agent node system prompts | Pasted into each agent's system message |
| Scoring dimensions + weights | Evaluator AI Agent system prompt | Part of the prompt text |
| Archetype definitions | Evaluator + CV Gen AI Agent prompts | Part of the prompt text |
| EEO stored answers | Google Sheets Config tab | Sheets Read node |

### Step 0b: Credentials strategy

**n8n handles all runtime credentials.** Every API key used by workflows lives in n8n's built-in encrypted Credentials store — NOT in `.env` files. Workflows reference credentials by name (e.g., "Gemini API" or "Google Sheets Service Account"), and n8n injects them at execution time.

**The `.env` file is only for the one-off setup script** (`scripts/setup-google-sheet.js`) that runs outside n8n via Node.js:
```
# scripts/.env.example — ONLY used by scripts/setup-google-sheet.js
GOOGLE_SHEETS_CREDENTIALS_JSON=   # Path to service account JSON key
GOOGLE_SHEETS_SPREADSHEET_NAME=Career-Ops Dashboard
```

**n8n Credentials to configure (in the n8n UI → Settings → Credentials):**
| Credential Name | Type | Used By |
|----------------|------|--------|
| Google Sheets Service Account | Google Sheets OAuth2 / Service Account | All 4 workflows (read/write dashboard) |
| Gemini API | HTTP Header Auth (API key) | All AI Agent nodes |
| Google CSE API | HTTP Header Auth (API key) | Scanner HTTP Request nodes (Workflow 01) |
| SerpAPI (alternative) | HTTP Header Auth (API key) | Scanner HTTP Request nodes (Workflow 01) |
| Discord Webhook | Webhook URL | Notification nodes in all workflows |
| html2pdf.app (optional) | HTTP Header Auth (API key) | CV/Cover Letter PDF generation |
| Webhook Auth | Header Auth | Inbound webhook authentication (X-API-Key) |

Create `docs/CREDENTIALS.md` documenting how to obtain each:
- **Google Sheets:** console.cloud.google.com → Google Sheets API → enable → create service account → download JSON key → add as n8n credential
- **Gemini:** aistudio.google.com → Get API Key → add as n8n HTTP Header Auth credential
- **Google CSE:** console.cloud.google.com → Custom Search JSON API → enable → create key + search engine ID → add key as n8n credential, store engine ID in Config sheet
- **Discord:** Server Settings → Integrations → Webhooks → New Webhook → Copy URL → add as n8n credential
- **html2pdf.app:** html2pdf.app → sign up → free tier API key → add as n8n credential

### Step 0c: Google Sheet auto-setup script
Create `scripts/setup-google-sheet.js` (Node.js) that:
1. Creates a new Google Sheet named "Career-Ops Dashboard"
2. Creates 5 tabs with correct headers:
   - **Pipeline:** ID | Source | Company | Title | URL | JD Snippet | Date Found | Freshness Hours | Status | Dedup Key
   - **Evaluations:** Job ID | Overall Score | Grade | Role Match | Skills | Seniority | Compensation | Geographic | Company Stage | Product-Market | Growth | Interview Likelihood | Timeline | Executive Summary | CV Match | Gaps | Archetype | Full Report | Freshness Adjusted Score
   - **Applications:** Job ID | Applied Date | CV HTML Link | CV PDF Link | Cover Letter | Pre-filled Answers JSON | Status | Follow-up Date | Notes
   - **Config:** Key | Value (rows: job_titles, locations, salary_min, salary_max, remote_preference, score_threshold, notification_email, scan_frequency, generate_pdf, discord_webhook)
   - **Comparisons:** Comparison ID | Job IDs | Ranking | Analysis | Date
3. Populates Config tab with defaults (5 job titles, score threshold 4.0, etc.)
4. Applies formatting: header row bold, column widths, conditional formatting on Grade column (A=green, B=blue, C=yellow, D-F=red)
5. Returns the Sheet ID for use in n8n credentials

### Step 0c-ii: Project package.json
Create `scripts/package.json` with:
- `name`: `n8n-career-ops-scripts`
- `scripts`: `{ "setup-sheet": "node setup-google-sheet.js" }`
- `dependencies`: `{ "googleapis": "^130.0.0", "dotenv": "^16.4.0" }`
- Run `cd scripts && npm install` to generate lockfile

### Step 0d: Draft all data that will be embedded in workflow nodes
These are **drafts written in the repo** that get **pasted into n8n nodes** when building workflows. n8n can't read these files at runtime — they're your source of truth for editing.

> **⚠️ UPDATE WORKFLOW: Edit .md file → copy content → paste into the AI Agent node's System Message in n8n → save workflow → re-export JSON to `workflows/`.**
> Updating the `.md` file alone does NOT update the live workflow. Both must stay in sync manually.

Create and populate:
- `prompts/pre-screen-system.md` through `prompts/comparison-system.md` — 8 agent system prompts, each self-contained with its own context, rules, and output schema
  - Mirrors Career-Ops lesson: "Modes beat a long prompt — each loads only what it needs"
  - Each prompt includes the relevant sections of `Full CV.md` inline (not a file reference — the full text is pasted into the prompt)
- **ATS site list** — document the 40+ sites with site: operators, tiers, and rendering flags. This will be hardcoded as a JSON array in a Code node in Workflow 01
- **Scoring dimensions + weights + rubrics** — documented here, embedded in the evaluator prompt
- **Archetype definitions + proof points** — documented here, embedded in evaluator + CV gen prompts
- **EEO fields + profile defaults** — these go in the Google Sheets Config tab (Step 0c populates them)
- **CV HTML template** — ATS-safe, single-column, clean typography. Uses `{{token}}` placeholders ({{summary}}, {{experience}}, {{skills}}, {{education}}, {{contact}}). Will be a template literal string inside a Code node
- **Cover letter HTML template** — Professional header, `{{company}}`, `{{role}}`, `{{body}}`, `{{signature}}` tokens. Same approach — template literal in a Code node

### Step 0e: n8n credential verification
Document in `docs/SETUP.md` a verification checklist (user runs manually in n8n):
1. **Google Sheets:** Create a test n8n workflow with Google Sheets node → verify read/write to the Dashboard sheet
2. **Gemini:** Create a test workflow with AI Agent node → Gemini Flash Lite → send "Hello, respond with OK" → verify response
3. **Google Custom Search:** Create a test HTTP Request node → call CSE API with a sample query → verify JSON results returned
4. **Discord:** Create a test workflow with Discord Webhook node → send test message → verify it appears in channel
5. **html2pdf.app (if used):** POST a simple HTML snippet → verify PDF returned

### Step 0f: .gitignore and README
- `.gitignore`: `scripts/.env`, `scripts/node_modules/`, `*.pdf`, `temp/`
- `README.md`: Project overview, link to SETUP.md, architecture summary, link to the original Career-Ops and briansjobsearch.com for reference

---

## Phase 1: Foundation & Configuration

> **Note:** Phase 0 drafts all prompts and documents all config data; Phase 1 is about **reviewing those drafts and confirming the Google Sheet is correct** before building workflows.

### Step 1: Verify prompt drafts and config data
- Review all 8 prompt files in `prompts/` — confirm each has correct output schema, relevant CV sections, and clear instructions
- Review the ATS site list — confirm all 40+ sites have correct site: operators, each with:
  - name, site_operator (e.g., `greenhouse.io`), search_type (`google_site` or `direct_link`)
  - `rendering` field: `static` (default) or `js_spa` (for Workday, Oracle, iCIMS, ADP — see Step 7 fallback)
  - For LinkedIn: marked as `direct_link` (not Google site:)
- Review scoring dimensions — 10 dimensions, weights, gate-pass rules, rubrics
- Review archetypes — 5 role archetypes with summary templates and key proof points
- Review Google Sheets Config tab — job titles, locations, salary range, score threshold, EEO stored answers all populated correctly

### Step 2: Google Sheets dashboard (manual setup, documented)
- **Tab 1: "Pipeline"** — ID, Source Site, Company, Title, URL, JD Snippet, Date Found, Status (New → Evaluated → Prepped → Applied → Interview → Rejected), Dedup Key
- **Tab 2: "Evaluations"** — Job ID, Overall Score (1-5), Grade (A-F), 10 individual dimension scores, Executive Summary, CV Match, Gaps, Recommended Archetype, Full Report Link
- **Tab 3: "Applications"** — Job ID, Applied Date, CV HTML/PDF Link, Cover Letter, Pre-filled Answers, Status, Follow-up Date
- **Tab 4: "Config"** — Search terms (job titles), locations, salary range, score threshold, notification email, EEO fields — editable by user directly in the sheet

### Step 3: CV Knowledge Base
- `Full CV.md` already exists in project
- Full CV text gets pasted into each agent's system prompt (the relevant sections for that agent)
- Structured proof points per archetype are documented in the prompts themselves — no separate config file needed at runtime

---

## Phase 2: Core Pipeline — Workflow 01 (`01-core-pipeline`)

> All agents in this phase live inside **one n8n workflow**. They are wired together on the canvas — each agent node's output feeds into the next via Code nodes that parse/transform data between them.

**Trigger:** Cron (configurable, default 1x/day at 7am) or manual webhook at `/webhook/core-pipeline`
**First node:** Config Loader (Google Sheets Read → Config tab)

### Step 4: Scanner nodes (not an AI agent — pure logic)
- **n8n nodes:** Loop (for each title × site) → HTTP Request (Google CSE) → Code (parse results) → Code (dedup) → Sheets Append
- **Input:** Reads the hardcoded ATS site list (JSON array in a Code node) + Config tab for search terms
- **Core mechanism (replicating briansjobsearch.com):**
  - For each job title × each ATS site, construct a Google search query:
    - `"Product Designer" site:greenhouse.io remote`
    - Time filter: `tbs=qdr:d` (past 24h) or `tbs=qdr:w` (past week)
  - Execute via **SerpAPI** (100 free searches/mo) or **Google Custom Search JSON API** (100 free queries/day, $5/1000 after)
  - Parse structured results: title, URL, snippet, company name
  - **Pagination:** First page only (10 results per query) by default. Configurable `search_depth` in Config tab (1-3 pages). More pages = more quota consumed. First page captures the freshest listings which is what matters most
  - LinkedIn: **excluded from automated scanning** — LinkedIn blocks site: queries and JS-renders all content. Handle LinkedIn listings via the ad-hoc URL pipeline (Step 15) only. Disabled in the site list array with `enabled: false` and a comment explaining why
- **API Quota Rotation Strategy:**
  - 40 sites × 5 titles = 200 queries per full scan — exceeds free tier
  - **Tier system in the site list array:** Tag each site as `tier: 1` (top 15 highest-yield: Greenhouse, Lever, Ashby, Workday, etc.) or `tier: 2` (remaining 25)
  - **Daily rotation:** Scan all Tier 1 sites every run. Rotate Tier 2 sites in groups of 8, cycling through all 25 over ~3 days
  - This gives ~115 queries per scan (75 Tier 1 + 40 Tier 2), fitting comfortably in paid CSE ($0.58/scan) or 2 scans/day on paid tier
  - **Budget failsafe:** Code node tracks daily query count in Config tab. If > 90% of daily budget consumed, skip remaining Tier 2 sites and send Discord warning
  - Config tab key `scan_budget_daily` controls the ceiling (default: 200)
- **Process:**
  - Normalize results to common schema
  - Generate dedup key: `${company.toLowerCase()}|${title.toLowerCase()}|${domain}` (plain string — no crypto needed, readable for debugging)
  - Check against "Pipeline" sheet for existing keys
  - Write only new listings with status "New"
- **Rate limiting:** Batch Google queries with 1-2s delay between calls to stay within API limits
- **Google Sheets write batching:** Collect all new listings in an array, then write in a single `Sheets Append` call (not one row at a time). Google Sheets API allows ~60 writes/min; batching avoids hitting this limit during large scans
- **Output:** Count of new jobs found → logged, optional email notification

### Step 5: Dedup layer
- Hash-based dedup in Code node before writing to sheet
- Also checks URL substring matches (same job, different ATS URL)
- Runs inline within Step 4, wired directly after the scanner loop output

### Step 6: Pre-Screen Agent (AI Agent node #1 in Workflow 01)
- **Wired after:** Sheets Append from scanner → Split-in-Batches → this agent
- **Input:** Jobs with status "New" — receives title, company, snippet per item
- **Process (title + snippet only — no full JD fetch):**
  - Gemini Flash Lite receives ONLY: job title, company name, snippet (from search result), and a condensed list of Preston's key skills/titles
  - Quick yes/no/maybe classification:
    - **Pass** → status "Pre-Screened", moves to full evaluation
    - **Reject** → status "Pre-Rejected" with 1-line reason, never gets full eval
    - **Maybe** → status "Pre-Screened" (benefit of the doubt)
  - This eliminates ~60-70% of listings (Career-Ops: 74% scored below 4.0) before spending tokens on full JD fetch + evaluation
  - Cost savings: pre-screen uses ~100 tokens/job vs ~2,000 tokens for full eval

### Step 7: Evaluator Agent (AI Agent node #2 in Workflow 01)
- **Wired after:** Pre-Screen Agent → filter (pass only "Pre-Screened") → this agent
- **Input per job:** Jobs that passed pre-screen
- **Process per job:**
  1. HTTP Request node → fetch full JD page from the job URL
  2. **JS-rendering fallback for SPA-based ATS sites:**
     - Sites tagged `rendering: js_spa` in the site list: Workday, Oracle Cloud, iCIMS, ADP, Glassdoor
     - These render JD content client-side; a plain HTTP GET returns an empty shell
     - **Primary fallback:** Use the Google search snippet (already captured by scanner) as a lightweight JD substitute. Score with lower confidence flag
     - **Optional fallback:** Route through Browserless (same Docker container used in Step 13) to get JS-rendered HTML. Only enable if Browserless is already set up for the auto-fill feature
     - For static-rendered ATS sites (Greenhouse, Lever, Ashby, etc.): plain HTTP fetch works fine
  3. Code node → extract text from HTML (strip tags, extract structured content). For Greenhouse/Lever/Ashby, these have clean HTML with predictable structure
  4. **Evaluator AI Agent node** (Gemini Flash Lite) with system prompt (pasted from `prompts/evaluator-system.md`) containing:
     - The 10 scoring dimensions with rubrics and weights
     - Preston's full CV text
     - Archetype definitions
     - Instruction to output structured JSON:
       ```
       { scores: { role_match: 4, skills: 3, ... }, overall: 3.8, grade: "B",
         summary: "...", cv_match: [...], gaps: [...], archetype: "IoT Systems Engineer",
         key_keywords: ["LoRaWAN", "embedded", ...], freshness_hours: 12 }
       ```
  5. Code node (wired after AI Agent output) → calculate weighted score, apply gate-pass rules
  5. **Freshness boost:** Jobs < 24h old get a +0.2 score bump (briansjobsearch insight: "Applying fast matters more than you think"). Listings < 6h old get +0.3. This surfaces fresh listings to the top of the queue
  6. **Sheets batch write:** Collect evaluation results, write to "Evaluations" sheet in a single append call
  7. Update Pipeline sheet status → "Evaluated"
  8. If score >= threshold (default 4.0 from Config tab) → flag for CV generation
  9. **Priority sorting:** Within the "Ready" queue, sort by: freshness-adjusted score DESC, then posting date ASC (newest first)

### Step 8: Evaluation report generation
- For high-scoring jobs (>= 4.0), generate a detailed 6-block report (mirroring Career-Ops):
  - Block A: Executive Summary (role type, archetype, score)
  - Block B: CV Match (JD requirements ↔ CV proof points, strength rating)
  - Block C: Gaps + Mitigation (severity, how to address in interview)
  - Block D: Level & Strategy (seniority positioning, honest framing)
  - Block E: Compensation Analysis (market context)
  - Block F: Interview Probability + Personalization Hooks
- Store as Markdown in a Google Doc or directly in the Evaluations sheet "Full Report" column

### Step 9: Batch processing
- n8n Split-in-Batches node: process 5-10 jobs per batch
- Configurable delay between API calls to Gemini (rate limit: 1,500/day on free tier)
- Error handling: failed evals → status "Error", retry once on next run

---

## Phase 4: CV & Cover Letter Generator

### Step 10: CV Generator Agent (AI Agent node #3 in Workflow 01)
- **Wired after:** Evaluator Agent → Freshness Boost Code → Sheets Write → IF node (score >= threshold) → this agent
- **Only runs for jobs scoring >= threshold** (default 4.0). Below-threshold jobs skip to the notification nodes at the end of the workflow
- **Input:** Evaluation JSON + Full CV + detected archetype + JD keywords
- **AI Agent (Gemini Flash Lite):**
  - Extract 15-20 keywords from JD (already done in evaluation)
  - Select archetype framing (from archetype definitions embedded in the prompt)
  - Reorder experience: most relevant role/bullets move up
  - Inject JD keywords: into summary, first bullet of top roles, and skills section
  - Output: structured JSON with content blocks (summary, experience items, skills, education)
- **Template injection:** Code node takes AI output JSON and injects into the CV HTML template (stored as a template literal string in the Code node) via `{{token}}` replacement. This keeps formatting consistent and ATS-safe — the AI focuses on content, not HTML structure
- **PDF option:** Either:
  - (A) Serve the HTML directly (many ATS systems accept HTML/DOCX anyway)
  - (B) Send HTML to **html2pdf.app** API → receive PDF → store URL in Applications sheet
- **Versioning:** Append `_v{N}` to filename (e.g., `cv_greenhouse_acme_v2.html`). Store version count in Applications sheet. Keep last 3 versions; older ones auto-deleted by a cleanup step in the tracker workflow
- Store HTML/PDF link in Applications sheet

### Step 11: Cover Letter Agent (AI Agent node #4 in Workflow 01)
- **Wired after:** CV Generator Agent → Template Inject Code Node → this agent
- AI Agent generates personalized cover letter using:
  - Evaluation summary (why this is a good fit)
  - Top 3 CV match proof points
  - Company-specific hook (from JD or company name)
- Output: HTML cover letter
- Same PDF option as CV

---

## Phase 5: Application Assistant

### Step 12: Apply Prep Agent (AI Agent node #5 in Workflow 01)
- **Wired after:** Cover Letter Agent → this agent
- **Process:**
  - Receives evaluation report + tailored CV + cover letter context from upstream agents
  - AI Agent pre-generates answers to common form questions:
    - "Why do you want to work here?" (drawn from evaluation personalization hooks)
    - "Describe relevant experience" (drawn from CV match proof points)
    - Salary expectations (from Config tab)
    - Years of experience in X (computed from CV dates)
    - EEO fields (from Config tab in Google Sheets — stored once, reused always, like Career-Ops does)
  - Store all prepared answers in Applications sheet
- **HITL:** User reviews everything in the sheet, edits as needed, then applies manually or triggers auto-fill

### Step 13: Notification & Cleanup nodes (end of Workflow 01)
- **Wired after:** Apply Prep Agent → Sheets Write (application row) → these nodes
- Also receives the "below threshold" branch from the IF node after evaluator (so all evaluated jobs converge here)

**Discord notifications** via Discord Webhook node (inline at end of workflow):
- 🔥 **Real-time alert** when a new A or B grade job is found (especially < 24h old — urgency!)
- 📋 **Run summary** embed: X scanned, Y evaluated, Z ready to apply, top scores from this run

**Data retention & cleanup** (Code node at very end):
- "Pre-Rejected" rows: auto-delete after 7 days (low value, noise reduction)
- "Stale" rows (> 60 days with no activity): move to a hidden "Archive" tab
- Keep the Pipeline tab under ~500 active rows for sheet performance
- Old CV versions beyond the last 3 per job: delete HTML files, update Applications sheet links
- Updates job statuses based on time (e.g., "Applied" > 30 days → "Stale")

### Step 14: Auto-fill assistant (optional, build last — can be appended to Workflow 01 or kept separate)
- Uses **Browserless** (self-hosted Docker container) or n8n Execute Command with Playwright
- Opens application URL → reads form fields → maps to prepared answers → pre-fills
- Does NOT submit — pauses for user review
- *This is the most fragile component. Career-Ops OP notes: "Playwright with a real browser session, not headless." We'd do the same via Browserless in non-headless mode*

---

## Phase 3: Ad-Hoc Pipeline — Workflow 02 (`02-adhoc-pipeline`)

> Single workflow, webhook-triggered. Reuses the same Evaluator, CV Gen, and Cover Letter agent prompts as Workflow 01 — just different entry point and no scanner/pre-screen.

### Step 15: Ad-hoc evaluation pipeline (`02-adhoc-pipeline`)
- Mirroring Career-Ops `oferta` mode — evaluate any single URL on demand
- **Trigger:** n8n Webhook node at `/webhook/adhoc-eval` — POST with `{ "url": "https://..." }`
- Can also be triggered from a simple web form, Discord slash command, or iOS Shortcut
- **Canvas layout (all inline, single workflow):**
  ```
  [Webhook Trigger]
    → [HTTP Request: fetch JD from URL]
    → [JS-rendering fallback Code Node]
    → [Evaluator AI Agent] (same prompt as Workflow 01)
    → [Freshness Boost Code Node]
    → [Sheets Write: pipeline + evaluation]
    → [IF score >= threshold]
      → [CV Generator AI Agent]
      → [Template Inject Code Node]
      → [Cover Letter AI Agent]
      → [Sheets Write: application row]
    → [Discord Webhook: score, grade, summary]
  ```
- Skips pre-screen — user already decided it's worth looking at
- **Response:** Returns evaluation summary JSON to the caller
- **Use case:** You spot a listing on Twitter, a friend sends you a link, you see one on a company's blog — paste it in, get instant pipeline treatment

---

## Phase 4: Interview Prep — Workflow 03 (`03-interview-prep`)

> Two agents chained inline: Deep Research Agent feeds into Interview Prep Agent. One workflow, one webhook trigger.

### Step 16: Deep Research Agent (AI Agent node #1 in Workflow 03)
- **Trigger:** Webhook at `/webhook/interview-prep` — POST with `{ "job_id": "..." }`
- Mirroring Career-Ops `deep` mode
- First node loads job data from Pipeline + Evaluations sheets using the job_id
- AI Agent + web search tool (n8n's built-in HTTP tool or SerpAPI) researches: recent funding, product news, team growth, tech stack, Glassdoor sentiment
- Outputs structured company brief → passed directly to the next agent node

### Step 17: Interview Prep Agent (AI Agent node #2 in Workflow 03)
- **Wired after:** Deep Research Agent → this agent
- **Input:** Company research (from Step 16) + full evaluation report + CV + JD
- **AI Agent generates:**
  - 10-15 likely interview questions based on JD requirements and company context
  - Suggested answers using Preston's proof points (mapped from CV match analysis)
  - Behavioral (STAR) answers pre-drafted for top 5 questions
  - Technical questions specific to the role's tech stack
  - "Questions to ask them" — tailored to company stage, product, and gaps identified in research
  - Red flags to watch for (from evaluation gaps or company research)
- **Output:** Structured interview prep doc stored in Applications sheet or Google Doc
- End of workflow → Discord notification with link to prep doc

---

## Phase 5: Comparison — Workflow 04 (`04-comparison`)

> Single agent workflow. Simplest of the four.

### Step 18: Multi-Offer Comparison Agent (`04-comparison`)
- Mirroring Career-Ops `ofertas` mode
- **Trigger:** Webhook at `/webhook/compare` — POST with `{ "job_ids": ["id1", "id2", "id3"] }`
- First node loads all selected evaluations from the Evaluations sheet
- **Comparison AI Agent** receives all evaluations + scores side by side
- **Generates comparison matrix:**
  - Side-by-side dimension scores
  - Overall ranking with reasoning
  - Trade-off analysis: "Company A has better role fit but Company B has stronger growth trajectory"
  - Recommendation: which to prioritize and why
  - Timeline urgency: which to apply to first based on posting date + hiring speed signals
- **Output:** Comparison report stored in the "Comparisons" sheet tab
- End of workflow → Discord notification with link to comparison

---

## Cross-Cutting Concerns

### Webhook URL Structure & Authentication
- **Naming convention:** All webhook URLs follow: `{N8N_WEBHOOK_BASE_URL}/webhook/{name}`
  - `/webhook/adhoc-eval` — Ad-Hoc Pipeline (Workflow 02, Step 15)
  - `/webhook/interview-prep` — Interview Prep (Workflow 03, Step 16-17)
  - `/webhook/compare` — Comparison (Workflow 04, Step 18)
- **Core Pipeline (Workflow 01)** uses a Cron trigger — no webhook needed (can add a manual Webhook Trigger node as an alternative entry point)
- **Authentication:** n8n's built-in Header Auth on all webhooks. Require `X-API-Key` header matching a value stored in n8n Credentials
- **iOS Shortcut integration:** Each webhook accepts a simple JSON POST body. Document minimal payloads in `docs/SETUP.md` with curl examples

### Error Handling Strategy (applies to all 4 workflows)
- **Gemini 429 (rate limit):** Exponential backoff — wait 30s, then 60s, then 120s. After 3 retries, mark job as status "Error-RateLimit" and move to next. Retried on next scheduled run
- **Gemini 500/503 (service error):** Retry once after 10s. On second failure, mark "Error-LLM" and continue
- **Google CSE 403 (quota exceeded):** Stop remaining scanner queries for this run. Discord warning: "🚫 CSE quota hit — scan incomplete, {N} sites skipped." Resume next run
- **JD URL 404/timeout:** Mark job as "Dead-Link" in Pipeline sheet — stale listings are common, don't retry
- **JD URL returns empty/JS-only content:** Fall back to snippet-based evaluation with `confidence: low` flag
- **Google Sheets API errors:** Retry once after 5s. On persistent failure, buffer in n8n static data variable and write on next successful connection
- **Discord webhook failure:** Non-blocking. Log to n8n execution log but don't halt the pipeline
- **Accumulated errors alert:** If > 5 errors in a single run, Discord summary: "⚠️ {N} errors in last run — check Logs column in Config tab"
- **Implementation:** Each workflow uses n8n's Error Trigger node. On any unhandled error → log to Sheets "Logs" column + Discord alert

---

## Relevant Files

### n8n Workflows (the actual product — import into n8n)
- `workflows/01-core-pipeline.json` — Cron-triggered: Scanner → Pre-Screen Agent → Evaluator Agent → CV Gen Agent → Cover Letter Agent → Apply Prep Agent → Notify (all inline)
- `workflows/02-adhoc-pipeline.json` — Webhook: single URL → Evaluator Agent → CV Gen → Cover Letter → Notify
- `workflows/03-interview-prep.json` — Webhook: Deep Research Agent → Interview Prep Agent
- `workflows/04-comparison.json` — Webhook: Comparison Agent

### Prompt Drafts (source of truth — content pasted into AI Agent node system prompt fields)
> **⚠️ These files are NOT read by n8n at runtime.** After editing any prompt, you must re-paste the content into the matching AI Agent node in the n8n UI and re-export the workflow JSON.

- `prompts/pre-screen-system.md` — Quick pass/reject classification from title+snippet
- `prompts/evaluator-system.md` — 10D scoring with JSON output schema
- `prompts/cv-generator-system.md` — Keyword injection, archetype framing, HTML output rules
- `prompts/cover-letter-system.md` — Personalization from evaluation hooks
- `prompts/apply-assistant-system.md` — Common question answering rules
- `prompts/deep-research-system.md` — Company research structure
- `prompts/interview-prep-system.md` — Interview Q&A + STAR answer generation
- `prompts/comparison-system.md` — Multi-offer ranking and trade-off analysis

### Already Exists
- `Full CV.md` — CV source of truth, text pasted into agent system prompts

### Runtime Data (lives in Google Sheets, not in files)
- **Config tab** — Job titles, score threshold, salary, locations, EEO fields, feature flags
- **Pipeline tab** — Job listings found by scanner
- **Evaluations tab** — AI-generated scores and reports
- **Applications tab** — CVs, cover letters, pre-filled answers
- **Comparisons tab** — Multi-offer comparison reports

---

## Verification

1. **Scanner test:** 1 title × 3 ATS sites → verify listings in Sheet, re-run → zero dupes
2. **Pre-screen test:** Feed 10 listings (mix of relevant and irrelevant). Verify pre-screen agent rejects obvious mismatches (e.g., "Accounting Manager") and passes relevant ones
3. **Evaluator test:** 3 known jobs: (a) perfect-fit IoT role → >= 4.0, (b) mediocre UX role → ~3.0, (c) wrong accounting role → < 2.5. Verify gate-pass logic
4. **Freshness boost test:** Two identical-scoring jobs, one posted 6h ago, one posted 5 days ago. Verify the fresh one ranks higher
5. **CV generation test:** IoT role vs. Product Design role → verify different archetypes, keywords, bullet ordering. HTML renders cleanly
6. **Core Pipeline end-to-end:** Trigger Workflow 01 → scanner finds jobs → pre-screen filters → evaluator scores → CV gen for top scorers → Discord alert. All within one workflow execution
7. **Ad-hoc webhook test:** POST a single URL to `/webhook/adhoc-eval` → verify Workflow 02 runs full pipeline: eval + CV + Discord notification
8. **Comparison test:** POST 3 job IDs to `/webhook/compare` → verify Workflow 04 produces side-by-side matrix and ranking
9. **Interview prep test:** POST a job ID to `/webhook/interview-prep` → verify Workflow 03 generates role-specific questions, STAR answers reference real CV proof points
10. **Discord test:** Verify embeds render correctly: real-time alert for A-grade, daily digest, follow-up reminder
11. **Rate limit handling:** Batch of 15 evaluations → verify graceful 429 retry via backoff
12. **JS-rendering fallback test:** Feed a Workday URL (JS-rendered) → verify it falls back to snippet-based eval with `confidence: low` flag
13. **Data retention test:** Insert a "Pre-Rejected" row dated 8 days ago → run cleanup → verify it's deleted. Insert a "Stale" row dated 61 days ago → verify it moves to Archive tab
14. **Webhook auth test:** POST to `/webhook/adhoc-eval` without `X-API-Key` header → verify 401 response. With correct key → verify 200

---

## Decisions

- **4 workflows, agent-to-agent architecture** — All AI agents live as inline AI Agent nodes within their workflow. No Execute Workflow nodes. Workflows split by trigger type: Cron (core pipeline), Webhook (ad-hoc, interview prep, comparison)
- **Gemini 2.0 Flash Lite as primary LLM** — free tier (1,500 req/day), very fast, good at structured JSON output. Cheaper than Claude or GPT-4o
- **briansjobsearch.com's Google `site:` strategy** as the scanning approach — proven across 40+ ATS platforms, accesses jobs that never appear on aggregators
- **SerpAPI or Google Custom Search API** to execute the Google queries programmatically (need one of these since we can't scrape Google directly)
- **Google Sheets** as the dashboard — visual, filterable, shareable, excellent n8n integration
- **HTML as the primary CV format**, with optional html2pdf.app conversion — HTML is lighter, faster to generate, and many companies accept it. PDF via API when needed
- **No auto-submit by default** — prepare everything, user reviews and submits. Auto-fill is optional, built last
- **LinkedIn excluded from Google site: queries** (LinkedIn blocks this) — instead use LinkedIn's direct job search URL or skip
- **Dedup is critical** (Career-Ops lesson: "Dedup is more valuable than scoring") — hash-based dedup runs before every write

## Confirmed: 5 Job Titles
1. "Product Designer"
2. "UX Designer"
3. "IoT Engineer"
4. "Creative Technologist"
5. "Front End Developer"

Editable from the Google Sheet Config tab — no code changes needed to add/remove.

With 40 sites × 5 titles = 200 queries per scan. At 4 scans/day = 800 queries/day. Google CSE free tier (100/day) won't cover this → need SerpAPI or paid CSE tier, or reduce scan frequency to 1x/day (200 queries, fits paid CSE at $1/day).

## Config Node Pattern
Every n8n workflow starts with a **Config Loader node** (Google Sheets Read → Config tab) that pulls:
- Job titles to search
- Score threshold (default 4.0)
- Salary range, location preferences, remote preference
- Notification email address
- Scan frequency override
- Any feature flags (e.g., "generate_pdf: true/false")

API keys live in n8n's encrypted Credentials store — never in the sheet, never in `.env`. The sheet holds only non-secret configuration. This pattern makes the entire system data-driven — change behavior from the spreadsheet, never from inside n8n.
