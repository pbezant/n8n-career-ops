# Workflow Audit — n8n Logic & Quality Inspector

Deep-audit an n8n workflow for logic errors, broken loops, native node opportunities, portability issues, and best practices. Produces a prioritised report and optionally auto-fixes safe issues.

## Usage
```
/workflow-audit [workflow_id] [--fix]
```
- Default workflow: `u1bV8KbKeXtNM8Xa` (Core Pipeline)
- `--fix` flag: auto-apply safe fixes via PUT API after reporting

---

## What to audit

### 1. Loop integrity
For every `splitInBatches` node:
- ✅ Port 0 (items) must connect to the processing chain
- ✅ Port 1 (done) must connect to the NEXT phase, not back into the loop
- ✅ There MUST be a loop-back: the END of the processing chain must connect back to the splitInBatches node's INPUT (not port 0/1 — the main input)
- ✅ Every item that enters port 0 must eventually return (if some items can be dropped by a filter mid-chain, verify `continueOnFail` or alternate paths so the batch doesn't stall)
- ❌ Flag: done port → processing node (backwards)
- ❌ Flag: no loop-back connection from end of chain
- ❌ Flag: loop-back goes to port 0/1 instead of the node's main input

### 2. Dead ends & orphan nodes
- Every non-terminal node must have at least one outbound connection
- Terminal nodes: `noOp`, Discord send, Cleanup, `Merge`
- Flag any node with 0 outbound connections that isn't a recognised terminal
- Flag any node with 0 inbound connections that isn't a trigger

### 3. Native node opportunities
Scan for HTTP Request nodes and check if a native n8n node exists:
| HTTP target | Native node |
|-------------|-------------|
| `googleapis.com/drive` | `n8n-nodes-base.googleDrive` |
| `googleapis.com/sheets` | `n8n-nodes-base.googleSheets` |
| `googleapis.com/docs` | `n8n-nodes-base.googleDocs` |
| `discord.com/api` | `n8n-nodes-base.discord` |
| `api.slack.com` | `n8n-nodes-base.slack` |
| `api.notion.com` | `n8n-nodes-base.notion` |
| `api.airtable.com` | `n8n-nodes-base.airtable` |
| `api.github.com` | `n8n-nodes-base.github` |
| `serpapi.com` | `n8n-nodes-serpapi.serpApi` |
| `smtp` / email | `n8n-nodes-base.emailSend` |

### 4. Hardcoded values (portability)
Flag any node parameter containing:
- Hardcoded Sheet IDs, Doc IDs, Folder IDs (should come from Config sheet or env vars)
- Hardcoded API keys or tokens inline in parameters
- Hardcoded email addresses, channel IDs, or webhook URLs that aren't in config
- Personal names or contact info hardcoded in system prompts (should be parameterised)
- Hardcoded credential IDs in non-credential fields

### 5. AI Agent health checks
For every `@n8n/n8n-nodes-langchain.agent` node:
- `promptType` must be `"define"` (not `"auto"`)
- `systemMessage` must not be empty (> 100 chars)
- Must have a connected LLM sub-node (Gemini, OpenAI, etc.)
- Must have a `text` parameter with an expression referencing actual job data
- Output must be consumed by a downstream node (not a dead end)

### 6. Expression safety
Scan all `={{ }}` expressions for:
- `$json.field` references where `field` might not exist — suggest adding `|| ''` fallbacks
- `$('NodeName').item` cross-branch references — verify NodeName exists in the workflow
- `$('NodeName').first()` — verify the node actually runs before this one in the execution path
- `.map()` or `.filter()` on fields that might be undefined (missing null-check)

### 7. Google Sheets node hygiene
For every `googleSheets` node:
- `documentId` should use `mode: "id"` with the actual sheet ID, not a cached URL
- Update nodes must have `matchingColumns` set (not empty `[]`)
- `mappingMode: "autoMapInputData"` on update nodes often causes issues — flag and suggest `defineBelow` with explicit column mapping
- Append nodes: check `columns.schema` isn't stale (causes "column not found" errors)

### 8. Error handling
- Are there any nodes where failure would silently drop items? Check `continueOnFail`
- Do AI Agent nodes have fallback parsing in downstream Code nodes?
- Does the workflow have an error workflow configured in Settings?

### 9. Performance & cost
- Count total AI Agent invocations per run (agents × expected item count)
- Flag if an agent runs inside a loop with no batch control
- Flag if the same data is fetched multiple times (e.g. CV fetched once vs per-item)
- Flag large data stored in sheet cells (jdText > 2000 chars per row = slow sheets)
- Estimate SerpAPI calls per run

### 10. Usability for others (shareability score)
- Are all credentials referenced by name not hardcoded?
- Is there a Config sheet / node that centralises all settings?
- Are node names descriptive (not "HTTP Request", "Code", "Set")?
- Do nodes have notes/descriptions explaining what they do?
- Would a new user know what to configure to run this workflow?

---

## Output format

Produce a structured report:

```
═══════════════════════════════════════════
  n8n WORKFLOW AUDIT — [Workflow Name]
  [date] | [node count] nodes | [connection count] connections
═══════════════════════════════════════════

🔴 CRITICAL (breaks execution)
  [#] [Node Name] — [issue] — [fix]

🟡 WARNING (degrades quality or reliability)
  [#] [Node Name] — [issue] — [fix]

🔵 IMPROVEMENT (best practice / portability)
  [#] [Node Name] — [issue] — [fix]

📊 STATS
  AI Agent calls per run: ~[N]
  SerpAPI calls per run: ~[N]
  Loops: [N] (pre-screen, evaluation, cv-gen)
  Portability score: [X/10]
  Shareability score: [X/10]

✅ AUTO-FIXED (if --fix flag used)
  [list of changes applied]
```

---

## Instructions

1. Fetch the workflow: `GET /api/v1/workflows/{id}`
2. Build a graph: map every node's name → parameters, and every connection source[port] → target
3. Run each audit check (1–10 above) against the graph
4. For each issue found: categorise (critical/warning/improvement), name the node, describe the problem, suggest the exact fix
5. If `--fix` is passed:
   - Auto-fix CRITICAL loop issues (port swaps, missing loop-backs)
   - Auto-fix empty `systemMessage` (re-sync from `prompts/*.md`)
   - Auto-fix `promptType: "auto"` → `"define"`
   - Do NOT auto-fix portability issues (need human judgement)
   - Push via PUT, re-verify
6. Print the full report

## Environment
- n8n API: `http://localhost:5678/api/v1`
- Auth: `X-N8N-API-KEY: $N8N_API_KEY`
- Workflow ID (default): `u1bV8KbKeXtNM8Xa`
- Prompts dir: `prompts/*.md`

$input
