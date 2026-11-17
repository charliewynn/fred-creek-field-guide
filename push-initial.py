#!/usr/bin/env python3
"""Initial push to an empty GitHub repo via the git-database API."""
import base64
import json
import os
import sys
import urllib.request

sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from dynamic_credentials import add_surrogate_to_request, read_response_body

API = "https://api.github.com"
REPO = "charliewynn/fred-creek-field-guide"
ROOT = os.path.expanduser("~/workspace/fred-creek-field-guide")


def api(method, path, payload=None):
    url = API + path
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Accept": "application/vnd.github+json",
                 "Content-Type": "application/json",
                 "User-Agent": "muse-agent"})
    add_surrogate_to_request(req, "custom.github", allowed_hosts=("api.github.com",))
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        raise SystemExit(f"GitHub API {exc.code} {method} {path}\n{body}")
    return json.loads(read_response_body(resp).decode("utf-8") or b"null")


entries = []
for dirpath, _dirs, files in os.walk(ROOT):
    for fn in sorted(files):
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        if rel.startswith(".git") or rel == "push-initial.py":
            continue
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs",
                   {"content": content, "encoding": "base64"})
        entries.append({"path": rel, "mode": "100644", "type": "blob",
                        "sha": blob["sha"]})
        print(f"blob {rel} -> {blob['sha'][:8]}")

tree = api("POST", f"/repos/{REPO}/git/trees", {"tree": entries})
print("tree", tree["sha"])
person = {"name": "Charlie Wynn", "email": "charlie@cwynn.com",
          "date": "2026-11-17T13:50:00-06:00"}
commit = api("POST", f"/repos/{REPO}/git/commits",
             {"message": "Fred Creek Field Guide — static site for GitHub Pages",
              "tree": tree["sha"], "parents": [],
              "author": person, "committer": person})
print("commit", commit["sha"])
ref = api("POST", f"/repos/{REPO}/git/refs",
          {"ref": "refs/heads/main", "sha": commit["sha"]})
print("ref", ref["ref"], ref["object"]["sha"])
