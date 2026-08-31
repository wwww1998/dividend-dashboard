# -*- coding: utf-8 -*-
"""
关键核对: 对每个起点,
  A) 持续定投(每月1万, 不停): 第一次"市值>=累计投入"发生在起点的第几个定投月? (最大值=持续定投回正最慢)
  B) 停止定投(定投12期后停): 从停止日起, 多久回正(已有结果: 最长224交易日)
对比两者, 解释"为什么停止后最长224交易日回正, 但持续定投100%盈利需45-48期"
"""
import json, datetime

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

STARTS=[]
for y in range(2016,2025):
    for m in range(1,13):
        ym=f"{y:04d}-{m:02d}"
        if "2016-08"<=ym<="2024-08": STARTS.append(ym)

def continuous_first_recover(code, start_ym):
    """持续定投: 返回 (首次市值>=累计投入的相对期数(约月), 该期数所在日期) 或 (None,None) 若到数据末未回正"""
    data=DATA[code]; first=FIRST[code]
    # 定投日列表
    days=[]; y,m=int(start_ym[:4]),int(start_ym[5:7])
    while True:
        ym2=f"{y:04d}-{m:02d}"
        d=first.get(ym2)
        if d is None: break
        days.append(d)
        y,m=(y+1,1) if m==12 else (y,m+1)
    inv_set=set(days)
    d0=days[0]
    shares=0.0; invested=0.0
    n=0  # 当前定投期数
    for p in data:
        if p["date"]<d0: continue
        if p["date"] in inv_set:
            shares+=AMOUNT/p["close"]; invested+=AMOUNT
            n+=1
        if n>=2 and shares*p["close"] > invested + 1e-6:   # 首次回正(严格大于, 首期不算)
            return n, p["date"]
    return None, None

# 统计
print("=== 持续定投: 首次回正所需期数(相对起点) ===")
for idx in INDICES:
    code,short=idx["code"],idx["short"]
    res=[]
    for sm in STARTS:
        n,d=continuous_first_recover(code,sm)
        res.append((sm,n,d))
    # 只统计数据完整的起点
    rec=[(sm,n) for sm,n,_ in res if n is not None]
    unrec=[(sm,n) for sm,n,_ in res if n is None]
    nvals=sorted(x[1] for x in rec)
    def pct(a,p): return a[min(len(a)-1,int(len(a)*p))] if a else None
    print(f"\n{short} (起点n={len(res)}):")
    print(f"  持续定投首次回正期数: 中位 {pct(nvals,.5)}期 | P75 {pct(nvals,.75)} | P90 {pct(nvals,.9)} | 最大 {nvals[-1]}期")
    print(f"  到数据末仍未回正: {len(unrec)}个")
    # 最慢5个
    slow=sorted(rec,key=lambda x:x[1],reverse=True)[:5]
    print(f"  最慢回正起点: " + ", ".join(f"{sm}起->第{n}期" for sm,n in slow))
