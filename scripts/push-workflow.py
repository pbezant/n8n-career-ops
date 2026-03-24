#!/usr/bin/env python3
"""
push-workflow.py — Fetch live workflow, embed prompts, push back via PUT.

Usage:
  python3 scripts/push-workflow.py [workflow_id]

Always re-embeds prompts/*.md so system messages are never wiped.
"""
import json, os, sys, urllib.request, urllib.error

API_KEY  = os.environ.get("N8N_API_KEY", "")
BASE_URL = os.environ.get("N8N_BASE_URL", "http://localhost:5678/api/v1")
if not API_KEY:
    sys.exit("Error: N8N_API_KEY not set")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
PROMPTS_DIR = os.path.join(PROJECT_DIR, "prompts")

WORKFLOW_ID = sys.argv[1] if len(sys.argv) > 1 else "u1bV8KbKeXtNM8Xa"

AGENT_PROMPT_MAP = {
    "Pre-Screen AI Agent":   "pre-screen-system.md",
    "Evaluator AI Agent":    "evaluator-system.md",
    "CV Generator AI Agent": "cv-generator-system.md",
    "Cover Letter AI Agent": "cover-letter-system.md",
    "Apply Prep AI Agent":   "apply-assistant-system.md",
}

SETTINGS_KEYS = {
    "executionOrder", "saveManualExecutions", "callerPolicy",
    "errorWorkflow", "timezone", "saveDataSuccessExecution", "saveDataErrorExecution"
}

# LLM sub-node → Agent connections (ai_languageModel port)
# These are ALWAYS re-established to prevent them from being wiped by API pushes
GEMINI_TO_AGENT = {
    "Gemini Flash Lite - PreScreen":   "Pre-Screen AI Agent",
    "Gemini Flash - Evaluator":        "Evaluator AI Agent",
    "Gemini Flash Lite - CV Gen":      "CV Generator AI Agent",
    "Gemini Flash Lite - Cover Letter": "Cover Letter AI Agent",
    "Gemini Flash Lite - Apply Prep":  "Apply Prep AI Agent",
}

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", headers={"X-N8N-API-KEY": API_KEY})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def put(path, payload):
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}", data=body, method="PUT",
        headers={"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read()), None
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read())

def embed_prompts(nodes):
    for node in nodes:
        fname = AGENT_PROMPT_MAP.get(node["name"])
        if fname:
            fpath = os.path.join(PROMPTS_DIR, fname)
            if os.path.exists(fpath):
                with open(fpath) as f:
                    content = f.read().strip()
                # Strip markdown code fences — model mimics them and output parsers choke on them
                import re
                content = re.sub(r'```[a-z]*\n?', '', content).replace('```', '')
                # Escape curly braces so LangChain doesn't interpret {..} as template variables
                content = content.replace('{', '{{').replace('}', '}}')
                # systemMessage lives in parameters.options.systemMessage for langchain agents
                if "options" not in node["parameters"]:
                    node["parameters"]["options"] = {}
                node["parameters"]["options"]["systemMessage"] = content
                print(f"  ✓ {node['name']}: {len(content)} chars")
            else:
                print(f"  ⚠ Missing prompt file: {fpath}")

def restore_ai_connections(connections, node_names):
    """Re-establish ai_languageModel connections which get wiped by API pushes."""
    for gemini_name, agent_name in GEMINI_TO_AGENT.items():
        if gemini_name in node_names and agent_name in node_names:
            connections[gemini_name] = {
                "ai_languageModel": [[{"node": agent_name, "type": "ai_languageModel", "index": 0}]]
            }
            print(f"  ✓ {gemini_name} →[ai_languageModel]→ {agent_name}")

print(f"Fetching workflow {WORKFLOW_ID}...")
wf = get(f"/workflows/{WORKFLOW_ID}")
print(f"  Got {len(wf['nodes'])} nodes")

print("Embedding prompts...")
embed_prompts(wf["nodes"])

print("Restoring AI connections...")
node_names = {n["name"] for n in wf["nodes"]}
restore_ai_connections(wf["connections"], node_names)

payload = {
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": {k: v for k, v in wf.get("settings", {}).items() if k in SETTINGS_KEYS}
}

print("Pushing...")
result, err = put(f"/workflows/{WORKFLOW_ID}", payload)
if result:
    print(f"  ✓ Pushed — {len(result['nodes'])} nodes, active={result.get('active')}")
else:
    print(f"  ✗ Error: {json.dumps(err, indent=2)}")
    sys.exit(1)
