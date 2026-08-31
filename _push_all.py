# -*- coding: utf-8 -*-
import json, urllib.request, base64, time, subprocess, os
TOKEN = os.getenv("GITHUB_TOKEN", "")
API = "https://api.github.com/repos/wwww1998/dividend-dashboard"
def api(method, path, data=None, tries=4):
    body = json.dumps(data).encode() if data is not None else None
    for i in range(tries):
        try:
            req = urllib.request.Request(f"{API}{path}", data=body, method=method,
                                         headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                                                  "User-Agent": "wb", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print(f"  重试{i+1}: {type(e).__name__}", flush=True)
            time.sleep(4 + i*3)
    return {"_err": "failed"}
files = subprocess.run(['git','ls-files'], capture_output=True, text=True, check=True).stdout.split()
print(f"推送 {len(files)} 个文件到 main")
blobs = []
for f in files:
    with open(f,'rb') as fh: c = fh.read()
    sha = api('POST','/git/blobs',{'content':base64.b64encode(c).decode(),'encoding':'base64'})['sha']
    blobs.append({'path':f,'mode':'100644','type':'blob','sha':sha})
tree = api('POST','/git/trees',{'tree':blobs})['sha']
head = api('GET','/git/refs/heads/main')['object']['sha']
commit = api('POST','/git/commits',{'message':'多版本定投看板: 月投/年投x1/3/5/10年 + 导航站', 'tree':tree,'parents':[head]})['sha']
api('PATCH','/git/refs/heads/main',{'sha':commit,'force':True})
print('main 更新:', commit[:7])
