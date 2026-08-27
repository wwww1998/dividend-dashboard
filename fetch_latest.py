# -*- coding: utf-8 -*-
"""增量抓取八个指数日线 2026-08-01~最新, 合并进既有 json (供计算最新股息率)"""
import json, urllib.request, time

API = "https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode={code}&startDate={sd}&endDate={ed}&pageNum=1&pageSize=20000"

def fetch(code, sd, ed, tries=6):
    url = API.format(code=code, sd=sd, ed=ed)
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            data = d.get("data") or []
            if data:
                return data
        except Exception as e:
            print(f"  retry {i+1}: {e}", flush=True)
            time.sleep(3 + i*2)
    return []

PAIRS = [
    ("H00015", "H00015.json"),
    ("H00922", "H00922.json"),
    ("H20269", "H20269.json"),
    ("H20955", "H20955.json"),
    ("000015", "price_000015.json"),
    ("000922", "price_000922.json"),
    ("H30269", "price_H30269.json"),
    ("930955", "price_930955.json"),
]

for code, fn in PAIRS:
    d = json.load(open(fn, encoding="utf-8"))
    key = "date" if "date" in d["data"][0] else "tradeDate"
    m = {str(r[key]).replace("-", ""): r["close"] for r in d["data"]}
    new = fetch(code, "20260801", "20261231")
    for r in new:
        k = str(r["tradeDate"]).replace("-", "")
        m[k] = float(r["close"])
    items = sorted(m.items())
    d["data"] = [{key: s, "close": v} for s, v in items]
    json.dump(d, open(fn, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{fn:<22} n={len(items):5d}  last={items[-1][0]}  close={items[-1][1]:.2f}", flush=True)