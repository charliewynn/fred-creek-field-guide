#!/usr/bin/env python3
"""Push to fred-creek-field-guide: init via Contents API (empty-repo quirk),
then one git-database commit with all site files."""
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


# 1. Init commit via Contents API (git-database API refuses empty repos)
readme = ("# Fred Creek Field Guide\n\n"
          "A backyard field guide for young naturalists — trees, invasives, "
          "mushrooms and animal signs of the Fred Creek woods in Tulsa, "
          "Oklahoma.\n\nStatic site, published with GitHub Pages.\n")
init = api("PUT", f"/repos/{REPO}/contents/README.md",
           {"message": "Initial commit",
            "content": base64.b64encode(readme.encode()).decode()})
parent_sha = init["commit"]["sha"]
parent_tree = init["commit"]["tree"]["sha"]
print("init commit", parent_sha)

# 2. Blobs + tree for all site files
entries = []
for dirpath, _dirs, files in os.walk(ROOT):
    for fn in sorted(files):
        full = os.path.join(dirpath, fn)
        rel = os.path.relpath(full, ROOT)
        if rel.startswith(".git") or rel.startswith("push-initial") or rel == "README.md":
            continue
        with open(full, "rb") as fh:
            content = base64.b64encode(fh.read()).decode()
        blob = api("POST", f"/repos/{REPO}/git/blobs",
                   {"content": content, "encoding": "base64"})
        entries.append({"path": rel, "mode": "100644", "type": "blob",
                        "sha": blob["sha"]})
        print("blob", rel)
tree = api("POST", f"/repos/{REPO}/git/trees",
           {"base_tree": parent_tree, "tree": entries})
person = {"name": "Charlie Wynn", "email": "charlie@cwynn.com",
          "date": "2026-11-17T14:45:00-06:00"}
commit = api("POST", f"/repos/{REPO}/git/commits",
             {"message": "Fred Creek Field Guide — static site for GitHub Pages",
              "tree": tree["sha"], "parents": [parent_sha],
              "author": person, "committer": person})
api("PATCH", f"/repos/{REPO}/git/refs/heads/main", {"sha": commit["sha"]})
print("pushed commit", commit["sha"])
