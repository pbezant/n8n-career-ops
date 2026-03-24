#!/usr/bin/env python3
"""
sync-prompts.py — Push prompts/*.md content into n8n AI Agent node systemMessage fields.

Usage:
  python3 scripts/sync-prompts.py              # sync all prompts
  python3 scripts/sync-prompts.py evaluator    # sync only evaluator prompt

Requires:
  N8N_API_KEY env var (or set in scripts/.env)
  SSH tunnel active: ssh -L 5678:localhost:5678 root@192.168.1.243
"""
import json
import os
import sys
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

API_KEY = os.environ.get("N8N_API_KEY", "")
BASE_URL = os.environ.get("N8N_BASE_URL", "http://localhost:5678/api/v1")

if not API_KEY:
    print("Error: N8N_API_KEY environment variable is not set.")
    print("  export N8N_API_KEY='your-key'  OR  edit scripts/.env")
    sys.exit(1)

# Map: prompt filename stem -> (workflow_id, node_name)
# Workflow 01 agents don't use systemMessage (prompts are inline in text expressions).
# Workflows 02-04 use systemMessage on the AI Agent nodes.
PROMPT_MAP = {
    "evaluator-system":    ("vEkezsBAtnIZu2lx", "Evaluator AI Agent"),
    "cv-generator-system": ("vEkezsBAtnIZu2lx", "CV Generator AI Agent"),
    "cover-letter-system": ("vEkezsBAtnIZu2lx", "Cover Letter AI Agent"),
    "deep-research-system":("i0jSDZ7RUx4b2ZqW", "Deep Research AI Agent"),
    "interview-prep-system":("i0jSDZ7RUx4b2ZqW", "Interview Prep AI Agent"),
    "comparison-system":   ("kxMTsL7S1BpDWTn0", "Comparison AI Agent"),
}

# Prompts only present in workflow 01 (inline — no systemMessage to sync)
INLINE_PROMPTS = {
    "pre-screen-system",
    "apply-assistant-system",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def api_get(path):
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        headers={"X-N8N-API-KEY": API_KEY},
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def api_put(path, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"},
        method="PUT",
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def read_prompt(stem):
    path = os.path.join(PROJECT_DIR, "prompts", f"{stem}.md")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return f.read()


def sync_prompt(stem, workflow_id, node_name):
    content = read_prompt(stem)
    if content is None:
        print(f"  SKIP  {stem}.md — file not found")
        return False

    # Fetch current workflow JSON
    try:
        wf = api_get(f"/workflows/{workflow_id}")
    except urllib.error.URLError as e:
        print(f"  ERROR fetching workflow {workflow_id}: {e}")
        return False

    # Find the target node
    updated = False
    for node in wf.get("nodes", []):
        if node.get("name") == node_name:
            node.setdefault("parameters", {})["systemMessage"] = content
            updated = True
            break

    if not updated:
        print(f"  ERROR  Node '{node_name}' not found in workflow {workflow_id}")
        return False

    # Only send the keys the API accepts (tags/pinData cause 400 if present)
    ALLOWED_KEYS = {"name", "nodes", "connections", "settings"}
    payload = {k: v for k, v in wf.items() if k in ALLOWED_KEYS}

    try:
        api_put(f"/workflows/{workflow_id}", payload)
        char_count = len(content)
        print(f"  OK    {stem}.md → [{workflow_id}] '{node_name}' ({char_count} chars)")
        return True
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"  ERROR updating workflow {workflow_id}: {e.code} {err[:200]}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    filter_stem = sys.argv[1] if len(sys.argv) > 1 else None

    # Verify connectivity
    try:
        workflows = api_get("/workflows")
        wf_names = [w.get("name", w.get("id")) for w in workflows.get("data", [])]
        print(f"Connected to n8n — {len(wf_names)} workflows: {wf_names}\n")
    except urllib.error.URLError as e:
        print(f"Cannot reach n8n at {BASE_URL}")
        print("Is the SSH tunnel active?  ssh -L 5678:localhost:5678 root@192.168.1.243")
        print(f"Error: {e}")
        sys.exit(1)

    success = 0
    skipped = 0
    errors = 0

    for stem, (wf_id, node_name) in PROMPT_MAP.items():
        if filter_stem and filter_stem not in stem:
            continue
        result = sync_prompt(stem, wf_id, node_name)
        if result:
            success += 1
        else:
            errors += 1

    # Report inline prompts
    for stem in INLINE_PROMPTS:
        if filter_stem and filter_stem not in stem:
            continue
        print(f"  SKIP  {stem}.md — inline prompt (edit directly in n8n workflow 01 text field)")
        skipped += 1

    print(f"\nDone — {success} synced, {skipped} skipped (inline), {errors} errors")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
