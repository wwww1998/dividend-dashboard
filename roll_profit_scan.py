# -*- coding: utf-8 -*-
"""
扫描: 定投期数 N 变化 (N=1..120期), 对每个 N 扫描所有起点(每月首个交易日)
统计: 盈利窗口占比(期末市值>累计投入), 中位/最差期末收益, 中位回撤, 最长/未修复
目标: 找出最早使"任意起点 100%盈利"的最小期数 N*
"""
import json, datetime

INDICES = [
    {"code": "H00015", "short": "上证红利"},
    {"code": "H00922", "short": "中证红利"},
    {"code": "H20269", "short": "红利低波"},
    {"code": "H20955", "short": "红利低波100"},
]
AMOUNT = 10000.0

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def first_days(data):
    out = {}
    for p in data:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = p["date"]
    return out

DATA = {i["code"]: load(i["code"]) for i in INDICES}
FIRST = {i["code"]: first_days(DATA[i["code"]]) for i in INDICES}

# 所有可用起点月份: 需起点后至少120个月有数据 => 2016-08 ~ 2016-08 (数据到2026-07)。为公平, 起点范围取 2016-08 ~ 2025-08(所有长度为1年的起点), 但做满n期需要数据足够, 这里对每个起点在数据范围内取能定投的最大期数。
# 为统一口径研究"任意起点定投N期", 只分析有完整 N 期数据的起点。
def inv_invest_days(code, start_ym, n):
    """返回某起点起连续 n 期的定投日列表(每个月的首个交易日)"""
    first = FIRST[code]
    days = []
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    for _ in range(n):
        ym2 = f"{y:04d}-{m:02d}"
        d = first.get(ym2)
        if d is None:
            return None
        days.append(d)
        y, m = (y+1, 1) if m == 12 else (y, m+1)
    return days

# 起点范围: 2016-08 起, 每个起点能扩展到最大 N。为研究方便, 固定起点集合 = 2016-08 ~ 2025-08 (109个)
STARTS = []
for y in range(2016, 2026):
    for m in range(1, 13):
        ym = f"{y:04d}-{m:02d}"
        if "2016-08" <= ym <= "2025-08":
            STARTS.append(ym)

# 每个起点定投 N 期后, 期末市值/回撤
def run(code, start_ym, n, data):
    inv = inv_invest_days(code, start_ym, n)
    if inv is None:
        return None
    inv_set = set(inv)
    d0, d_last = inv[0], inv[-1]
    # 窗口 = d0 起到 第n期所在月月末
    last_ym = d_last[:7]
    last_day = max(p["date"] for p in data if p["date"][:7] == last_ym)
    shares = 0.0; invested = 0.0
    port = []
    for p in data:
        if p["date"] < d0: continue
        if p["date"] > last_day: break
        if p["date"] in inv_set:
            shares += AMOUNT / p["close"]
            invested += AMOUNT
        port.append({"date": p["date"], "value": shares*p["close"], "invested": invested})
    if not port: return None
    final = port[-1]
    total_ret = final["value"]/final["invested"] - 1
    # 最大回撤与修复
    peak=None; peak_d=None; mdd=0.0; mdd_peak_d=None; mdd_trough_d=None; mdd_peak_v=None
    for q in port:
        if peak is None or q["value"] > peak:
            peak=q["value"]; peak_d=q["date"]
        dd = q["value"]/peak - 1
        if dd < mdd:
            mdd=dd; mdd_peak_d=peak_d; mdd_trough_d=q["date"]; mdd_peak_v=peak
    recover=None; rec_days=None
    if mdd_peak_d:
        started=False
        for q in port:
            if q["date"]==mdd_trough_d: started=True; continue
            if started and q["value"]>=mdd_peak_v: recover=q["date"]; break
    if recover:
        rec_days = sum(1 for q in port if mdd_trough_d < q["date"] <= recover)
    return {"ret": total_ret, "mdd": mdd, "rec_days": rec_days, "unrec": recover is None}

# 扫描 N=1..120（或到数据支持上限）
results = []
for n in range(1, 121):
    row = {"n": n}
    for idx in INDICES:
        code, short = idx["code"], idx["short"]
        data = DATA[code]
        rets=[]; mdds=[]; recs=[]; n_unrec=0; n_ok=0
        for sm in STARTS:
            r = run(code, sm, n, data)
            if r is None: continue
            n_ok += 1
            rets.append(r["ret"]); mdds.append(r["mdd"])
            if r["unrec"]: n_unrec += 1
            else: recs.append(r["rec_days"])
        rets.sort(); mdds.sort(); recs.sort()
        def pct(a,p): return a[min(len(a)-1,int(len(a)*p))] if a else None
        win = sum(1 for x in rets if x>0)/len(rets)*100 if rets else 0
        row[short] = {
            "win_pct": win, "n_ok": n_ok,
            "ret_min": rets[0], "ret_med": pct(rets,.5), "ret_p10": pct(rets,.1),
            "mdd_med": pct(mdds,.5), "mdd_min": mdds[0],
            "rec_med": pct(recs,.5) if recs else None, "rec_max": recs[-1] if recs else None,
            "n_unrec": n_unrec,
        }
    results.append(row)
    # 打印关键: 红利低波的盈利概率与最差收益
    hl = row["红利低波"]
    print(f"N={n:>3}期: 盈利概率 上证{row['上证红利']['win_pct']:.0f}% 中证{row['中证红利']['win_pct']:.0f}% 低波{hl['win_pct']:.0f}% 低波100{row['红利低波100']['win_pct']:.0f}%  | 最差期末收益 低波{hl['ret_min']*100:.1f}% | 未修复 低波{hl['n_unrec']}")

json.dump({"results": results, "starts_n": len(STARTS), "amount": AMOUNT},
          open("roll_profit_scan.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)

print("\n=== 找出'任意起点100%盈利'的最小期数 N* (盈利概率=100% 的最早N) ===")
for idx in INDICES:
    short = idx["short"]
    for row in results:
        if row[short]["win_pct"] >= 100:
            print(f"{short}: N* = {row['n']} 期 (盈利概率 {row[short]['win_pct']:.0f}%, 最差期末收益 {row[short]['ret_min']*100:.1f}%)")
            break
    else:
        print(f"{short}: 120期内未达100%")