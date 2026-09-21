"""
Shared "dispatch a GitHub Actions workflow, wait for it, read its
committed output" helper — used by both `semantic_analysis.py` (text
analysis via `call-scene-semantic-analysis.yml`) and `illustration.py`
(image generation via the EXISTING `call-image-pipeline.yml`, not a
duplicate of it). Both need identical dispatch/poll/read-back logic,
differing only in workflow name, inputs, and which file lands in
`scratch/` — this module is that one implementation, not two copies.

Callable directly from Python with no Claude/human in the loop: uses the
`GITHUB_TOKEN` already present in this environment against the plain
GitHub REST API, which (unlike api.cometapi.com) is reachable directly
from this sandbox.
"""
import json
import os
import time
import urllib.error
import urllib.request

REPO = "aiaccess11gempro5693-alt/n8n"
API = "https://api.github.com"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _token():
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not tok:
        raise RuntimeError("GITHUB_TOKEN/GH_TOKEN not set in this environment")
    return tok


def _gh_request(method, path, body=None):
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode("utf-8") if body is not None else None,
        method=method,
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')[:500]}")


def dispatch_and_wait(workflow_file, inputs, ref="main", timeout_s=300, poll_s=6, label=""):
    """Dispatches `workflow_file` with `inputs`, waits for the resulting
    run to complete, and returns nothing itself — caller reads whatever
    file(s) that workflow committed to scratch/ after this returns (via
    `git pull`). Raises on timeout or non-success conclusion."""
    _, before = _gh_request("GET", f"/repos/{REPO}/actions/workflows/{workflow_file}/runs?per_page=1")
    before_id = (before.get("workflow_runs") or [{}])[0].get("id")

    _gh_request("POST", f"/repos/{REPO}/actions/workflows/{workflow_file}/dispatches", {"ref": ref, "inputs": inputs})
    print(f"[gh_bridge] dispatched {workflow_file}{' — ' + label if label else ''}")

    run_id = None
    deadline = time.time() + timeout_s
    while time.time() < deadline and run_id is None:
        time.sleep(poll_s)
        _, runs = _gh_request("GET", f"/repos/{REPO}/actions/workflows/{workflow_file}/runs?per_page=5")
        for r in runs.get("workflow_runs", []):
            if r["id"] != before_id:
                run_id = r["id"]
                break
    if run_id is None:
        raise RuntimeError(f"Timed out waiting for a new run of {workflow_file} to appear")

    while time.time() < deadline:
        _, run = _gh_request("GET", f"/repos/{REPO}/actions/runs/{run_id}")
        status, conclusion = run.get("status"), run.get("conclusion")
        print(f"[gh_bridge] run {run_id} ({workflow_file}): status={status} conclusion={conclusion}")
        if status == "completed":
            if conclusion != "success":
                raise RuntimeError(f"{workflow_file} run {run_id} finished with conclusion={conclusion}")
            return run_id
        time.sleep(poll_s)
    raise RuntimeError(f"Timed out waiting for {workflow_file} run {run_id} to complete")


def pull_and_read(relpath, as_json=True):
    """git pull main, then read a file the just-completed run committed
    (the project's established way to get results out of GitHub Actions —
    the alternative, actions artifacts, sit on Azure Blob, which this
    sandbox's proxy also blocks)."""
    exit_code = os.system(f"cd {REPO_ROOT} && git pull --quiet origin main") >> 8
    full = f"{REPO_ROOT}/{relpath}"
    if not os.path.exists(full):
        raise RuntimeError(f"Expected file not found after run: {relpath} (git pull exit={exit_code})")
    if as_json:
        with open(full, encoding="utf-8") as f:
            return json.load(f)
    return full
