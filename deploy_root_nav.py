# -*- coding: utf-8 -*-
"""导航页作为主站: 根 index.html=导航, 月投10年移到 monthly/10y/"""
import json, base64, urllib.request, sys

TOKEN = "REPLACED"
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

# blob: 根导航页 + 月投10年(移到 monthly/10y/)
def blob(fn):
    c = open(fn, "rb").read()
    return call("POST", BASE + "/git/blobs", {"content": base64.b64encode(c).decode(), "encoding": "base64"})["sha"]

nav = blob("publish_dashboard.html")          # -> index.html (根, 导航主站)
m10 = blob("dividend_dashboard.html")         # -> monthly/10y/index.html  (月投10年, 原根)
print("nav blob ok, m10 blob ok")

# 需要删除原根 index.html 旧blob：直接在新tree里提供 index.html=导航、monthly/10y/index.html=月投10年
tree = call("POST", BASE + "/git/trees", {"base_tree": tree_sha, "tree": [
    {"path": "index.html", "mode": "100644", "type": "blob", "sha": nav},
    {"path": "monthly/10y/index.html", "mode": "100644", "type": "blob", "sha": m10},
]})
print("new tree:", tree["sha"][:8])

commit = call("POST", BASE + "/git/commits",
              {"message": "deploy: nav dashboard as root site, move monthly-10y to /monthly/10y/",
               "tree": tree["sha"], "parents": [tree_sha]})
print("commit:", commit["sha"][:8])
call("PATCH", BASE + "/git/refs/heads/gh-pages", {"sha": commit["sha"], "force": True})
print("gh-pages updated OK")