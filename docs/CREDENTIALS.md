# Credentials Guide

All API keys used by workflows live in n8n's encrypted Credentials store. The `.env` file is only for the one-off sheet setup script.

---

## n8n Credentials to Configure

### ✅ Already Configured (found in existing workflows)

| Credential Name | Type | n8n Credential ID | Used By |
|----------------|------|------------|---------|
| Google Gemini(PaLM) Api account | `googlePalmApi` | `T6vrBWXANAVPKppK` | All AI Agent nodes |
| Google Sheets account | `googleSheetsOAuth2Api` | `ng8zlg2pDNctkqmp` | All 4 workflows |
| Discord Bot account | `discordBotApi` | `PeIukwvkJqSyArKV` | Notification nodes |

### ❌ Still Needed

| Credential Name | Type | Used By |
|----------------|------|---------|
| SerpAPI (or Google CSE API) | HTTP Header Auth | Scanner HTTP Request (Workflow 01) |
| html2pdf.app (optional) | HTTP Header Auth | CV/Cover Letter PDF generation |
| Webhook Auth | Header Auth | Inbound webhook X-API-Key validation |

---

## How to Obtain Each

### Google Gemini API ✅ Already configured
1. [aistudio.google.com](https://aistudio.google.com) → Get API Key
2. n8n → Settings → Credentials → New → "Google Gemini(PaLM) API" → paste key

### Google Sheets ✅ Already configured
OAuth2 account already linked. The setup script uses a service account key (separate from the OAuth2 account used by n8n workflows).

### Discord Bot ✅ Already configured
Discord bot already set up. For webhook notifications, the bot posts to a channel — ensure it has MESSAGE permissions in the target channel.

### SerpAPI ❌ Needed for scanner
1. [serpapi.com](https://serpapi.com) → Sign up → Dashboard → API Key
2. Free tier: 100 searches/month. Paid: $50/mo for 5,000 searches
3. n8n → Settings → Credentials → New → "Header Auth" → Name: `SerpAPI`
   - Header Name: `X-API-KEY` (or use query param `api_key` in URL)
4. Alternative to SerpAPI: Google Custom Search JSON API (100 free/day, $5/1000 after)
   - [console.cloud.google.com](https://console.cloud.google.com) → Custom Search JSON API → Enable → Create key
   - [cse.google.com](https://cse.google.com) → New search engine → copy Search Engine ID
   - Store engine ID in Google Sheets Config tab key: `cse_engine_id`

### html2pdf.app (optional) ❌ Needed only if generating PDFs
1. [html2pdf.app](https://html2pdf.app) → Sign up → API key from dashboard
2. n8n → Settings → Credentials → New → "Header Auth" → Name: `html2pdf.app`
   - Header Name: `X-API-Key`

### Webhook Auth ❌ Needed for inbound webhook security
1. Generate a random string (e.g., `openssl rand -hex 32`)
2. n8n → Settings → Credentials → New → "Header Auth" → Name: `Career-Ops Webhook Auth`
   - Header Name: `X-API-Key`
   - Header Value: your random string
3. Use this same value in iOS Shortcuts or curl commands when calling webhooks

---

## Google Sheets Setup Script Credentials

The `scripts/setup-google-sheet.js` script runs once outside n8n to create the dashboard. It needs a service account JSON key (different from the OAuth2 account used at runtime):

1. [console.cloud.google.com](https://console.cloud.google.com) → IAM & Admin → Service Accounts → Create
2. Grant it "Editor" role on Google Sheets
3. Create key (JSON) → download
4. Copy to `scripts/` directory
5. Set `GOOGLE_SERVICE_ACCOUNT_KEY_PATH=./your-key.json` in `scripts/.env`
