# -*- coding: utf-8 -*-
"""
核对: "定投12期后停止, 最长224交易日回正" vs "任意起点100%盈利需45-48期"
对每个起点, 找出"持续定投到第几期才首次盈利(期末市值>累计投入)", 看最大/分布, 定位钉子户起点
"""
import json

data = json.load(open("roll_profit_scan.json", encoding="utf-8"))
results = data["results"]  # [{n, 指数:{win_pct, ret_min,...}}]

# 每个起点持续定投N期在第N期末的收益ret是负数时 = 该N期未盈利
# 但我们没存每起点每N的ret... 需要重算。这里直接用回测重算: 起点固定, 持续定投, 看每年末
# 简化: 对关键起点(2017-07,2017-11,2019-04,2020-08,2021-01), 计算逐年期末收益

import datetime
INDICES = [{"code":"H00015","short":"上证红利"},{"code":"H00922","short":"中证红利"},{"code":"H20269","short":"红利低波"},{"code":"H20955","short":"红利低波100"}]
AMOUNT = 10000.0
def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s=s.replace("-",""); return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date":fmt(r["tradeDate"]),"close":r["close"]} for r in d["data"]]
DATA = {i["code"]: load(i["code"]) for i in INDICES}
def first_days(d):
    o={}
    for p in d:
        ym=p["date"][:7]
        if ym not in o: o[ym]=p["date"]
    return o
FIRST = {i["code"]: first_days(DATA[i["code"]]) for i in INDICES}

# 对起点, 持续定投到每个月末(第N期所在月末), 记录每个N期末收益
def profile(code, start_ym, maxn=120):
    data=DATA[code]; first=FIRST[code]
    days=[]
    y,m=int(start_ym[:4]),int(start_ym[5:7])
    for _ in range(maxn):
        ym2=f"{y:04d}-{m:02d}"
        d=first.get(ym2)
        if d is None: break
        days.append(d)
        y,m=(y+1,1) if m==12 else (y,m+1)
    inv_set=set(days)
    d0=days[0]
    shares=0.0; invested=0.0
    # 每个定投日当天的市值快照
    snaps={}
    for p in data:
        if p["date"]<d0: continue
        if p["date"] in inv_set:
            shares+=AMOUNT/p["close"]; invested+=AMOUNT
            # 当月最后一天? 用当月月末
        # 记录每月末: 简化用每个定投日所在月之后的下一个定投日前一天? 直接用每个定投日当天市值作为"N期末"
        if p["date"] in inv_set:
            snaps[p["date"]] = (shares*p["close"], invested)
    # N期末 = 第N个定投日(近似第N期末)
    out={}
    for i,d in enumerate(days, start=1):
        if d in snaps:
            v,inv = snaps[d]
            out[i] = v/inv-1
    return out

# 找每个起点"首次盈利的期数"
print("=== 各起点 首次盈利期数 (找出最晚盈利的钉子户) ===")
for idx in INDICES:
    code,short=idx["code"],idx["short"]
    first_profit=[]
    for y in range(2016,2025):
        for m in range(1,13):
            sm=f"{y:04d}-{m:02d}"
            if not ("2016-08"<=sm<="2024-08"): continue
            prof=profile(code,sm)
            fp=None
            for n in range(1,121):
                if n in prof and prof[n]>0:
                    fp=n; break
            if fp is not None:
                first_profit.append((sm,fp))
    first_profit.sort(key=lambda x:x[1], reverse=True)
    print(f"\n{short}: 最晚盈利需 {first_profit[0][1]}期 (起点 {first_profit[0][0]}); 前10钉子户:")
    for sm,fp in first_profit[:10]:
        print(f"   {sm}起 -> 第{fp}期才盈利")
    fpr=[fp for _,fp in first_profit]
    fpr_s=sorted(fpr)
    med=fpr_s[len(fpr_s)//2]
    print(f"   中位首次盈利期数={med}")
