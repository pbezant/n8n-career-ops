#!/usr/bin/env python3
import json
import urllib.request
import urllib.error
import sys

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI3NzY1YWIxZi1kM2QwLTQwN2QtOTVhZS1iODk5NWM1OWVlZmIiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzczODQ1NTkyLCJleHAiOjE3NzYzOTg0MDB9.p7-PIm4dh7SuAExRHqCtX7rUzUmDTPwTS7nEcN_OcZk"
BASE_URL = "http://localhost:5678/api/v1"

WORKFLOWS = [
    "/Users/prestonbezant/_Developement/n8n-career-ops/workflows/01-core-pipeline.json",
    "/Users/prestonbezant/_Developement/n8n-career-ops/workflows/02-adhoc-pipeline.json",
    "/Users/prestonbezant/_Developement/n8n-career-ops/workflows/03-interview-prep.json",
    "/Users/prestonbezant/_Developement/n8n-career-ops/workflows/04-comparison.json",
]

# Only these top-level keys are accepted by the n8n REST API
ALLOWED_KEYS = {"name", "nodes", "connections", "settings", "staticData", "pinData", "tags"}

# Only these node-level keys are accepted
ALLOWED_NODE_KEYS = {"id", "name", "type", "typeVersion", "position", "parameters", "credentials", "disabled", "continueOnFail", "webhookId", "notes", "alwaysOutputData", "executeOnce", "retryOnFail", "maxTries", "waitBetweenTries", "onError"}

def clean_node(node):
    return {k: v for k, v in node.items() if k in ALLOWED_NODE_KEYS}

def import_workflow(filepath):
    with open(filepath) as f:
        wf = json.load(f)
    
    stripped = {k: v for k, v in wf.items() if k in ALLOWED_KEYS}
    
    # Clean all nodes
    if "nodes" in stripped:
        stripped["nodes"] = [clean_node(n) for n in stripped["nodes"]]
    
    body = json.dumps(stripped).encode("utf-8")
    
    req = urllib.request.Request(
        f"{BASE_URL}/workflows",
        data=body,
        headers={
            "X-N8N-API-KEY": API_KEY,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        resp = urllib.request.urlopen(req)
        data = json.loads(resp.read())
        return {"success": True, "id": data.get("id"), "name": data.get("name")}
    except urllib.error.HTTPError as e:
        err_body = e.read()
        try:
            data = json.loads(err_body)
        except:
            data = {"raw": err_body.decode("utf-8", errors="replace")}
        return {"success": False, "error": data}

for path in WORKFLOWS:
    name = path.split("/")[-1]
    print(f"\n--- Importing {name} ---")
    result = import_workflow(path)
    if result["success"]:
        print(f"  SUCCESS: ID={result['id']} | Name={result['name']}")
    else:
        print(f"  ERROR: {json.dumps(result['error'], indent=2)}")
