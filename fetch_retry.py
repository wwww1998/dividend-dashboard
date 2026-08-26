# -*- coding: utf-8 -*-
"""串行+重试拉取，避免并发超时"""
import sys, json, urllib.request, time

API = "https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}&startDate={sd}&endDate={ed}&pageNum=1&pageSize=20000"

def fetch(code, sd, ed, tries=5):
    url = API.format(code=code, sd=sd, ed=ed)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            data = d.get("data") or []
            if data: return data
        except Exception as e:
            print(f"  retry {i+1}: {e}", flush=True)
            time.sleep(3 + i*2)
    return []

code, out = sys.argv[1], sys.argv[2]
parts = []
parts.append(fetch(code, "20050101", "20251231"))
parts.append(fetch(code, "20260101", "20260731"))
m = {}
for p in parts:
    for r in p:
        m[r["tradeDate"]] = float(r["close"])
items = sorted(m.items())
series = [{"tradeDate": d, "close": v} for d, v in items]
json.dump({"indexCode": code, "data": series}, open(out, "w", encoding="utf-8"), ensure_ascii=False)
if items:
    v0, v1 = series[0]["close"], series[-1]["close"]
    print(f"{code}: {len(series)} 条  {series[0]['tradeDate']}={v0:.2f} -> {series[-1]['tradeDate']}={v1:.2f}")
else:
    print(f"{code}: 无数据")
