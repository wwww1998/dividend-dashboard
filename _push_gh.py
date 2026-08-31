# -*- coding: utf-8 -*-
import json, urllib.request, base64, time, subprocess
TOKEN = "REPLACED"
API = "https://api.github.com/repos/wwww1998/dividend-dashboard"
def api(method, path, data=None, tries=5):
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{API}{path}", data=body, method=method,
                                         headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                                                  "User-Agent": "wb", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:300]
            if e.code == 422:  # 需要sha等, 不重试
                return {"_err": 422, "_msg": err}
            print(f"  重试{i+1}: HTTP{e.code}", flush=True); time.sleep(5+i*4)
        except Exception as e:
            print(f"  重试{i+1}: {type(e).__name__}", flush=True); time.sleep(5+i*4)
    return {"_err": "failed"}

# ===== 1. main 分支全量推送 =====
files = subprocess.run(['git','ls-files'], capture_output=True, text=True, check=True).stdout.split()
print(f"[main] 推送 {len(files)} 个文件")
blobs = []
for f in files:
    with open(f,'rb') as fh: c = fh.read()
    sha = api('POST','/git/blobs',{'content':base64.b64encode(c).decode(),'encoding':'base64'})['sha']
    blobs.append({'path':f,'mode':'100644','type':'blob','sha':sha})
tree = api('POST','/git/trees',{'tree':blobs})['sha']
head = api('GET','/git/refs/heads/main')['object']['sha']
commit = api('POST','/git/commits',{'message':'新增指数走势图板块+两走势图颜色统一(全部8版本)', 'tree':tree,'parents':[head]})['sha']
api('PATCH','/git/refs/heads/main',{'sha':commit,'force':True})
print(f"[main] 更新 -> {commit[:7]}")

# ===== 2. gh-pages 更新 8 个版本 =====
MAP = {
    "monthly/10y/index.html": "dividend_dashboard.html",
    "monthly/5y/index.html": "dividend_dashboard_5y.html",
    "monthly/3y/index.html": "dividend_dashboard_3y.html",
    "monthly/1y/index.html": "dividend_dashboard_1y.html",
    "yearly/index.html": "dividend_dashboard_yearly.html",
    "yearly/5y/index.html": "dividend_dashboard_yearly_5y.html",
    "yearly/3y/index.html": "dividend_dashboard_yearly_3y.html",
    "yearly/1y/index.html": "dividend_dashboard_yearly_1y.html",
}
for path, local in MAP.items():
    cur = api('GET', f'/contents/{path}?ref=gh-pages')
    sha = cur.get('sha')
    if not sha:
        print(f"  {path}: 读取sha失败 {cur.get('_msg','')}"); continue
    c = open(local,'rb').read()
    r = api('PUT', f'/contents/{path}', {'message':'update: 指数走势板块', 'content':base64.b64encode(c).decode(), 'sha':sha, 'branch':'gh-pages'})
    cid = r.get('commit',{}).get('sha','')[:7] if isinstance(r,dict) else '?'
    print(f"  gh-pages {path} -> {cid} {r.get('_msg','') if isinstance(r,dict) else ''}")
print("完成 ✓")
