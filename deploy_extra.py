# -*- coding: utf-8 -*-
"""通过 GitHub API 将 7 个新文件推送到 gh-pages 分支（独立子目录）"""
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
        print("HTTP ERROR", method, url, e.code, e.read().decode("utf-8")[:500])
        sys.exit(1)

# 1. 当前 gh-pages 树
branch = call("GET", BASE + "/branches/gh-pages")
tree_sha = branch["commit"]["sha"]
print("base tree:", tree_sha)

# 2. 创建 blob 准备
FILES = {
    "dashboard/index.html": "publish_dashboard.html",
    "monthly/5y/index.html": "dividend_dashboard_5y.html",
    "monthly/3y/index.html": "dividend_dashboard_3y.html",
    "monthly/1y/index.html": "dividend_dashboard_1y.html",
    "yearly/5y/index.html": "dividend_dashboard_yearly_5y.html",
    "yearly/3y/index.html": "dividend_dashboard_yearly_3y.html",
    "yearly/1y/index.html": "dividend_dashboard_yearly_1y.html",
}
blobs = []
for path, fn in FILES.items():
    content = open(fn, "rb").read()
    j = call("POST", BASE + "/git/blobs",
             {"content": base64.b64encode(content).decode("ascii"), "encoding": "base64"})
    blobs.append({"path": path, "mode": "100644", "type": "blob", "sha": j["sha"]})
    print("blob:", path, j["sha"][:8])

# 3. 创建 tree
tree = call("POST", BASE + "/git/trees", {"base_tree": tree_sha, "tree": blobs})
print("new tree:", tree["sha"][:8])

# 4. 创建 commit
now = "2026-08-26"
commit = call("POST", BASE + "/git/commits",
              {"message": f"deploy: add 6 dashboard sub-pages + nav dashboard ({now})",
               "tree": tree["sha"], "parents": [tree_sha]})
print("commit:", commit["sha"][:8])

# 5. 更新 gh-pages 引用
call("PATCH", BASE + "/git/refs/heads/gh-pages", {"sha": commit["sha"], "force": True})
print("gh-pages updated OK")