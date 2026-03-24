# Architecture

## Overview

4 n8n workflows with AI agents chained inline. All agent-to-agent data transfer happens via Code nodes on the canvas — no Execute Workflow calls, no file I/O, no external queues.

```
Workflow 01: Core Pipeline    (Cron trigger, daily)
Workflow 02: Ad-Hoc Pipeline  (Webhook, single job URL)
Workflow 03: Interview Prep   (Webhook, job ID)
Workflow 04: Comparison       (Webhook, array of job IDs)
```

---

## Data Flow: Workflow 01 (Core Pipeline)

```
[Schedule Trigger: 7am daily]
  → [Config Loader: Sheets Read → Config tab]
  → [Code: ATS Site List (hardcoded JSON array)]
  → [Code: Build Query Combos (titles × sites)]
  → [Loop: HTTP Request → SerpAPI/CSE per combo]
     → [Code: Parse Results + Dedup + Collect]
  → [Google Sheets: Append new listings → Pipeline tab]
  → [Google Sheets: Read new listings]
  → [Split In Batches: 5 jobs/batch]
     → [AI Agent: Pre-Screen] ← Gemini Flash Lite
        → [Code: Filter pass/fail]
        → [Google Sheets: Update status]
        → [HTTP Request: Fetch JD HTML]
        → [Code: Extract JD text]
        → [AI Agent: Evaluator] ← Gemini Flash Lite
           → [Code: Apply gate-pass + freshness boost]
           → [Google Sheets: Write evaluation]
           → [IF: score >= threshold]
              → TRUE: [AI Agent: CV Generator] ← Gemini Flash Lite
                        → [Code: Template inject → HTML]
                        → [AI Agent: Cover Letter] ← Gemini Flash Lite
                           → [AI Agent: Apply Prep] ← Gemini Flash Lite
                              → [Google Sheets: Write application row]
              → FALSE: [No Op: pass through]
           → [Merge]
  → [Discord: Daily digest notification]
  → [Code: Cleanup stale rows]
```

## Data Flow: Workflow 02 (Ad-Hoc Pipeline)

```
[Webhook: POST /webhook/adhoc-eval {"url": "..."}]
  → [Respond to Webhook: {"status": "processing", "message": "..."}]
  → [Config Loader: Sheets Read → Config tab]
  → [HTTP Request: Fetch JD from URL]
  → [Code: Extract JD text + JS fallback detection]
  → [AI Agent: Evaluator] ← Gemini Flash Lite
     → [Code: Apply gate-pass + freshness boost]
     → [Google Sheets: Write to Pipeline + Evaluations tabs]
     → [IF: score >= threshold]
        → TRUE: [AI Agent: CV Generator]
                  → [Code: Template inject]
                  → [AI Agent: Cover Letter]
                     → [Google Sheets: Write application row]
        → FALSE: [No Op]
     → [Merge]
  → [Discord: Score + grade + summary alert]
```

## Data Flow: Workflow 03 (Interview Prep)

```
[Webhook: POST /webhook/interview-prep {"job_id": "..."}]
  → [Respond to Webhook: {"status": "processing"}]
  → [Google Sheets: Read job from Pipeline tab by ID]
  → [Google Sheets: Read evaluation from Evaluations tab by ID]
  → [AI Agent: Deep Research] ← Gemini Flash Lite + HTTP Tool
     (researches company: funding, news, Glassdoor, tech stack)
     → [AI Agent: Interview Prep] ← Gemini Flash Lite
        (generates Q&A, STAR answers, questions to ask)
        → [Google Sheets: Write prep doc to Applications tab]
  → [Discord: Prep doc ready notification]
```

## Data Flow: Workflow 04 (Comparison)

```
[Webhook: POST /webhook/compare {"job_ids": ["id1", "id2", "id3"]}]
  → [Respond to Webhook: {"status": "processing"}]
  → [Google Sheets: Read all evaluations for given IDs]
  → [Code: Format side-by-side comparison data]
  → [AI Agent: Comparison] ← Gemini Flash Lite
     (rankings, trade-offs, recommendation, timeline urgency)
     → [Google Sheets: Write to Comparisons tab]
  → [Discord: Comparison ready notification]
```

---

## Google Sheets Dashboard Structure

### Pipeline tab
| Column | Description |
|--------|-------------|
| ID | `{source}_{YYYYMMDD}_{4char}` e.g. `greenhouse_20260318_a1b2` |
| Source | ATS platform name |
| Company | Company name |
| Title | Job title |
| URL | Full job posting URL |
| JD Snippet | First 500 chars of job description from search result |
| Date Found | ISO timestamp |
| Freshness Hours | Age in hours at time of scan |
| Status | New → Pre-Screened/Pre-Rejected → Evaluated → Prepped → Applied → Interview → Rejected → Stale |
| Dedup Key | `company\|title\|domain` lowercase string |

### Evaluations tab
| Column | Description |
|--------|-------------|
| Job ID | FK to Pipeline.ID |
| Overall Score | 1.0–5.0 weighted average |
| Grade | A/B/C/D/F |
| Role Match | 1–5 (gate-pass: <2 caps grade at D) |
| Skills | 1–5 (gate-pass) |
| Seniority | 1–5 |
| Compensation | 1–5 |
| Geographic | 1–5 |
| Company Stage | 1–5 |
| Product-Market | 1–5 |
| Growth | 1–5 |
| Interview Likelihood | 1–5 |
| Timeline | 1–5 |
| Freshness Adjusted Score | Overall + freshness boost |
| Executive Summary | ~200 word summary |
| CV Match | Comma-separated matching proof points |
| Gaps | Comma-separated gaps with mitigations |
| Archetype | One of the 5 role archetypes |
| Full Report | 6-block full evaluation (may be truncated—full in Google Doc link) |
| Confidence | high/low (low = snippet-based eval, no full JD) |

### Applications tab
| Column | Description |
|--------|-------------|
| Job ID | FK to Pipeline.ID |
| Applied Date | ISO date |
| CV HTML | Full tailored CV HTML |
| CV PDF Link | html2pdf.app URL (if PDF enabled) |
| Cover Letter | HTML cover letter |
| Pre-filled Answers | JSON string of form Q&A |
| Interview Prep | Link or inline prep doc |
| Status | Prepped → Applied → Interview → Offer → Rejected |
| Follow-up Date | Date for next follow-up action |
| Notes | Manual notes |
| CV Version | Integer version counter |

### Config tab (Key/Value rows)
Core configuration editable from the spreadsheet — no code changes needed.

### Comparisons tab
Stores multi-offer comparison matrices generated by Workflow 04.

---

## Scanning Strategy

Replicates [briansjobsearch.com](https://briansjobsearch.com)'s approach:
- Google's index has already crawled ATS job pages
- `site:greenhouse.io "Product Designer" remote` returns fresh, structured results
- SerpAPI or Google CSE JSON API executes these queries programmatically
- `dateRestrict=d1` filters to past 24 hours (CSE) or `tbs=qdr:d` (SerpAPI)

### Tier System
- **Tier 1** (scan every run): Greenhouse, Lever, Ashby, Workday, Wellfound, SmartRecruiters, JazzHR, Jobvite, iCIMS, BreezyHR, Teamtailor, Recruitee, Rippling, Workable, Builtin
- **Tier 2** (rotate in groups of 8): All remaining sites
- 75 Tier-1 queries + 40 rotating Tier-2 = ~115 queries/scan

### JS-Rendered ATS Fallback
Sites that return empty HTML from plain HTTP GET:
- Workday, Oracle Cloud, iCIMS (classic), ADP, Glassdoor
- Fallback: use Google search snippet as JD substitute with `confidence: low` flag
- Optional: route through Browserless for full JS render

---

## LLM Usage

| Agent | Model | Avg Tokens/Call | Daily Volume |
|-------|-------|----------------|-------------|
| Pre-Screen | Gemini 2.0 Flash Lite | ~100 | 50–100 |
| Evaluator | Gemini 2.0 Flash Lite | ~2,000 | 15–30 |
| CV Generator | Gemini 2.0 Flash Lite | ~3,000 | 3–5 |
| Cover Letter | Gemini 2.0 Flash Lite | ~1,500 | 3–5 |
| Apply Prep | Gemini 2.0 Flash Lite | ~500 | 3–5 |
| Deep Research | Gemini 2.0 Flash Lite | ~2,000 | on-demand |
| Interview Prep | Gemini 2.0 Flash Lite | ~4,000 | on-demand |
| Comparison | Gemini 2.0 Flash Lite | ~2,000 | on-demand |

Free tier: 1,500 requests/day. Daily pipeline consumption: ~150–200 requests.

---

## Error Handling

| Error | Action |
|-------|--------|
| Gemini 429 | Exponential backoff: 30s → 60s → 120s, then mark Error-RateLimit |
| Gemini 500/503 | Retry once after 10s, then Error-LLM |
| CSE/SerpAPI 403 | Stop scan, Discord warning, resume next run |
| JD URL 404/timeout | Mark Dead-Link, skip |
| JD returns empty HTML | Use snippet fallback, confidence: low |
| Google Sheets API error | Retry once, buffer in static data |

Each workflow has an Error Trigger node → logs to Sheets Logs column + Discord alert.

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 4 separate workflows | Different trigger types (cron vs webhook) |
| Agents inline (not sub-workflows) | Single execution log, no inter-workflow overhead |
| Gemini 2.0 Flash Lite | Free tier (1,500 req/day), fast, good JSON output |
| Google Sheets as dashboard | Visual, filterable, n8n native integration |
| HTML-first CVs | Lighter, faster, most ATS accept it; PDF optional |
| No auto-submit | HITL required — apply prep only, user submits |
| String dedup keys | Readable, debuggable, no crypto dependency |
| Google `site:` via SerpAPI/CSE | Proven strategy, structured JSON, avoids scraping |
