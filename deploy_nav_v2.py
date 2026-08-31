# -*- coding: utf-8 -*-
"""更新 gh-pages 根 index.html 为修正后的导航页(2列, 无主站标签), 并同步 dashboard/副本"""
import json, base64, urllib.request, sys, os

TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO = "wwww1998/dividend-dashboard"
BASE = "https://api.github.com/repos/" + REPO
HDR = {"Authorization": "Bearer " + TOKEN, "User-Agent": "curl", "Accept": "application/vnd.github+json"}

def call(method, url, data=None):
    req = urllib.request.Request(url, method=method, headers=HDR)
    if data is not None:
        req.data = json.dumps(data).encode("utf-8")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print("HTTP ERROR", method, url, e.code, e.read().decode("utf-8")[:500]); sys.exit(1)

branch = call("GET", BASE + "/branches/gh-pages")
tree_sha = branch["commit"]["sha"]
print("base tree:", tree_sha)

def blob(fn):
    c = open(fn, "rb").read()
    return call("POST", BASE + "/git/blobs", {"content": base64.b64encode(c).decode(), "encoding": "base64"})["sha"]

nav = blob("publish_dashboard.html")
print("nav blob ok")

tree = call("POST", BASE + "/git/trees", {"base_tree": tree_sha, "tree": [
    {"path": "index.html", "mode": "100644", "type": "blob", "sha": nav},
    {"path": "dashboard/index.html", "mode": "100644", "type": "blob", "sha": nav},
]})
print("new tree:", tree["sha"][:8])
commit = call("POST", BASE + "/git/commits",
              {"message": "deploy: nav two-col layout, remove 'main site' tags from root & /dashboard/",
               "tree": tree["sha"], "parents": [tree_sha]})
print("commit:", commit["sha"][:8])
call("PATCH", BASE + "/git/refs/heads/gh-pages", {"sha": commit["sha"], "force": True})
print("gh-pages updated OK")