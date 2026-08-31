# -*- coding: utf-8 -*-
"""
定投12期(1年)后停止定投, 持有不动: 从停止日起, 多久回正(市值>=累计投入)?
对每个起点统计: 12期末是否盈利; 若亏损, 停止后回正所需交易日/自然月; 及回正前最深浮亏
"""
import json, datetime

INDICES = [
    {"code": "H00015", "short": "上证红利"},
    {"code": "H00922", "short": "中证红利"},
    {"code": "H20269", "short": "红利低波"},
    {"code": "H20955", "short": "红利低波100"},
]
AMOUNT = 10000.0
N = 12  # 定投期数

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

STARTS = []
for y in range(2016, 2026):
    for m in range(1, 13):
        ym = f"{y:04d}-{m:02d}"
        if "2016-08" <= ym <= "2024-08":   # 需12期+停止后追踪至少一段时间; 起点到2024-08(2025-08停止)留出追踪期
            STARTS.append(ym)

def inv_days(code, start_ym, n):
    first = FIRST[code]
    days = []
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    for _ in range(n):
        ym2 = f"{y:04d}-{m:02d}"
        d = first.get(ym2)
        if d is None: return None
        days.append(d)
        y, m = (y+1,1) if m==12 else (y,m+1)
    return days

def run(code, start_ym, data):
    inv = inv_days(code, start_ym, N)
    if inv is None: return None
    inv_set = set(inv)
    d_start, d_stop = inv[0], inv[-1]   # d_stop = 第12期定投日
    # 窗口: d_start ~ 数据末尾(停止后继续持有, 追踪回正)
    shares = 0.0; invested = 0.0
    stop_idx = None
    port = []
    for i, p in enumerate(data):
        if p["date"] < d_start: continue
        if p["date"] in inv_set:
            shares += AMOUNT/p["close"]; invested += AMOUNT
        port.append({"date": p["date"], "value": shares*p["close"], "invested": invested})
        if p["date"] == d_stop:
            stop_idx = len(port)-1
    if stop_idx is None: return None
    # 停止日状态
    stop = port[stop_idx]
    profit_at_stop = stop["value"] - stop["invested"]  # 停止日浮盈(可能为负)
    invested_final = stop["invested"]                  # 总投入=12万
    # 停止后: 份额不变, 市值=shares*close, 回正=市值>=invested_final
    # 回正时间: 从 stop 日期之后第一个市值>=invested_final 的交易日
    recover_days = None; recover_date = None; rec_months = None
    min_val_after = None
    for q in port[stop_idx+1:]:
        if min_val_after is None or q["value"] < min_val_after:
            min_val_after = q["value"]
        if q["value"] >= invested_final:
            recover_date = q["date"]
            recover_days = sum(1 for x in port[stop_idx+1:] if x["date"] <= q["date"])
            break
    if recover_date:
        # 自然月差
        r0 = stop["date"]; r1 = recover_date
        rec_months = (int(r1[:4])-int(r0[:4]))*12 + (int(r1[5:7])-int(r0[5:7]))
        if rec_months <= 0: rec_months = 1  # 次月即回正算1个月
    # 停止后最深浮亏(相对投入)
    max_loss_after = (min_val_after/invested_final - 1) if min_val_after is not None else 0
    return {
        "profit_at_stop": profit_at_stop,
        "recover_days": recover_days, "recover_date": recover_date, "rec_months": rec_months,
        "max_loss_after": max_loss_after,
    }

results = {}
for idx in INDICES:
    code, short = idx["code"], idx["short"]
    data = DATA[code]
    rows = []
    for sm in STARTS:
        r = run(code, sm, data)
        if r: rows.append((sm, r))
    results[short] = rows

# 统计
print(f"起点数: {len(STARTS)} (2016-08 ~ 2024-08)")
for idx in INDICES:
    short = idx["short"]
    rows = results[short]
    n_total = len(rows)
    n_profit = sum(1 for _,r in rows if r["profit_at_stop"] > 0)   # 停止时已盈利
    n_loss = n_total - n_profit
    # 亏损者中回正的情况
    rec_days = [r["recover_days"] for _,r in rows if r["profit_at_stop"]<=0 and r["recover_days"] is not None]
    rec_days_s = sorted(rec_days)
    n_recover = len(rec_days)
    n_unrec = n_loss - n_recover   # 亏损且到数据末仍未回正
    def pct(a,p): return a[min(len(a)-1,int(len(a)*p))] if a else None
    # 全样本(含已盈利, 记回正0天)
    all_rec = sorted([0 if r["profit_at_stop"]>0 else (r["recover_days"] if r["recover_days"] is not None else 9999) for _,r in rows])
    print(f"\n=== {short} (n={n_total}) ===")
    print(f"  12期结束时已盈利: {n_profit}/{n_total} ({n_profit/n_total*100:.1f}%)")
    print(f"  12期结束时仍亏损: {n_loss}/{n_total}")
    if rec_days_s:
        print(f"  亏损者中已回正: {n_recover}/{n_loss}, 回正中位 {pct(rec_days_s,.5)} 交易日, P75 {pct(rec_days_s,.75)}, P90 {pct(rec_days_s,.9)}, 最长 {pct(rec_days_s,1)}")
    print(f"  仍未回正(数据末): {n_unrec} 个")
    print(f"  全部起点(含已盈利记0)回正中位: {pct(all_rec,.5)} 交易日 | P90 {pct(all_rec,.9)}")
    # 列出亏损但未回正的最大浮亏
    worst_unrec = sorted([(sm, r) for sm, r in rows if r["profit_at_stop"]<=0 and r["recover_days"] is None],
                         key=lambda x: x[1]["profit_at_stop"])[:5]
    if worst_unrec:
        print(f"  未回正的起点(最亏5个): " + ", ".join(f"{sm}起 停止时浮亏 ¥{round(-r['profit_at_stop']):,}" for sm,r in worst_unrec))

json.dump({"starts": STARTS, "results": {k:[{"start":sm, **r} for sm,r in v] for k,v in results.items()}},
          open("roll_stop12.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
