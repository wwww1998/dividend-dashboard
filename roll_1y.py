# -*- coding: utf-8 -*-
"""
滚动测算: 最近10年任意月度起点, 滚动12个月每月定投 ¥10,000(共12期)
对每个起点(每月首个交易日), 计算该12个月窗口的: 年化收益率(XIRR), 组合最大回撤
输出: roll_1y.json (供网页/绘图) + 打印分位数统计
起点: 2016-08 ~ 2025-08 (最后起点 2025-08~2026-07), 共109个起点
"""
import json, datetime

INDICES = [
    {"code": "H00015", "short": "上证红利"},
    {"code": "H00922", "short": "中证红利"},
    {"code": "H20269", "short": "红利低波"},
    {"code": "H20955", "short": "红利低波100"},
]
AMOUNT = 10000.0
N_PERIODS = 12  # 滚动12个月, 12期

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def xirr(cashflows, lo=-0.999, hi=10.0):
    def npv(r):
        t0 = datetime.date(*map(int, cashflows[0][0].split("-")))
        return sum(cf / (1 + r) ** ((datetime.date(*map(int, d.split("-"))) - t0).days / 365.25)
                   for d, cf in cashflows)
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        if npv(mid) == 0: break
        if npv(mid) * f_lo < 0: hi = mid
        else: lo = mid; f_lo = npv(mid)
    return (lo + hi) / 2

def max_drawdown(series):
    peak = None; mdd = 0.0
    for v in series:
        if peak is None or v > peak:
            peak = v
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd
    return mdd

def monthly_first_days(data):
    """data: 全史日线列表(升序). 返回 {ym: date} 每月首个交易日"""
    out = {}
    for p in data:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = p["date"]
    return out

# 数据加载
DATA = {i["code"]: load(i["code"]) for i in INDICES}
FIRST = {i["code"]: monthly_first_days(DATA[i["code"]]) for i in INDICES}
# 各指数交易日集合(用于查某日起点后第N个月的定投日)
DATESET = {i["code"]: set(p["date"] for p in DATA[i["code"]]) for i in INDICES}

# 所有可能的起点月份: 2016-08 ~ 2025-08 (滚动12个月, 需起点+11个月都有数据)
start_months = []
for y in range(2016, 2026):
    for m in range(1, 13):
        ym = f"{y:04d}-{m:02d}"
        if "2016-08" <= ym <= "2025-08":
            start_months.append(ym)

# 统一以"任意指数"为准的起点日 = 该月的首个交易日(用上证红利日历, 各指数交易日基本一致)
def window_for(short_code, start_ym):
    """返回该起点下, 某指数的12期定投窗口序列"""
    first = FIRST[short_code]
    days = DATESET[short_code]
    # 该月首个交易日作为第1期
    seg = []
    d0 = first.get(start_ym)
    if not d0:
        return None
    cur = d0
    # 收集从起点起12个月的每个月的首个交易日
    invest_days = []
    for k in range(N_PERIODS):
        # 计算 start_ym 之后的第 k 个月
        y, m = int(start_ym[:4]), int(start_ym[5:7])
        ym2 = f"{y:04d}-{m:02d}"
        d = first.get(ym2)
        if d is None:
            return None
        invest_days.append(d)
        # 下个月
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        start_ym = f"{y:04d}-{m:02d}"
    # 截取从第1期到第12期之后的数据(到窗口结束, 第12期定投日后至其自然月末)
    data = DATA[short_code]
    idx_start = next(i for i, p in enumerate(data) if p["date"] == invest_days[0])
    # 结束: 第12期定投日所在月之后的最后交易日(取第12期定投日之后一个月的月末, 简化取第12期定投日所在月末尾)
    # 更稳妥: 取 invest_days[-1] 所在月之后, 下一个定投日之前的所有交易日
    # 定投窗口 = 从第1个定投日 到 第12个定投日所在月的最后一个交易日
    last_ym = invest_days[-1][:7]
    # 该月最后一个交易日
    last_day = max(p["date"] for p in data if p["date"][:7] == last_ym)
    seg = [p for p in data if invest_days[0] <= p["date"] <= last_day]
    return seg, invest_days

result = {"windows": [], "meta": {"amount": AMOUNT, "periods": N_PERIODS, "start_range": "2016-08 ~ 2025-08(起点), 窗口=起点起12个月", "generated": "2026-08-26"}}

# 对每个起点, 逐指数计算
for sm in start_months:
    win = {"start": sm, "indices": {}}
    for idx in INDICES:
        code = idx["code"]
        w = window_for(code, sm)
        if w is None:
            continue
        seg, invest_days = w
        # 定投
        shares = 0.0; invested = 0.0
        port = []
        inv_set = set(invest_days)
        for p in seg:
            if p["date"] in inv_set:
                shares += AMOUNT / p["close"]
                invested += AMOUNT
            port.append({"date": p["date"], "value": shares * p["close"], "invested": invested})
        final = port[-1]
        total_ret = final["value"] / final["invested"] - 1
        cf = [(d, -AMOUNT) for d in invest_days] + [(final["date"], final["value"])]
        cagr = xirr(cf)
        mdd = max_drawdown([p["value"] for p in port])
        # 最大回撤: 记录 峰值/谷底/恢复日 及 修复时长(交易日数)
        peak = None; peak_d = None; mdd_val = 0.0; mdd_peak_d = None; mdd_trough_d = None; mdd_trough_v = None; mdd_peak_v = None
        mdd_amt = 0.0
        for p in port:
            v = p["value"]
            if peak is None or v > peak:
                peak = v; peak_d = p["date"]
            amt = peak - v
            if amt > mdd_amt:
                mdd_amt = amt; mdd_peak_d = peak_d; mdd_trough_d = p["date"]; mdd_trough_v = v; mdd_peak_v = peak; mdd_val = v/peak-1
        # 找恢复日: 谷底之后第一个回到峰值市值(max值)的交易日
        recover_d = None
        if mdd_peak_d:
            started = False
            for p in port:
                if p["date"] == mdd_trough_d:
                    started = True
                    continue
                if started and p["value"] >= mdd_peak_v:
                    recover_d = p["date"]; break
        # 恢复所需交易日数(从谷底到恢复 或 到期末/未恢复)
        rec_days = None
        if recover_d:
            rec_days = sum(1 for p in port if mdd_trough_d < p["date"] <= recover_d)
        win["indices"][idx["short"]] = {
            "final": round(final["value"], 2), "total_ret": round(total_ret, 4),
            "cagr": round(cagr, 4) if cagr else None,
            "mdd": round(mdd_val, 4), "mdd_amt": round(mdd_amt, 2),
            "peak_date": mdd_peak_d, "trough_date": mdd_trough_d,
            "recover_date": recover_d, "rec_days": rec_days,
            "end": final["date"],
        }
    result["windows"].append(win)

json.dump(result, open("roll_1y.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 打印统计
print(f"起点数量: {len(result['windows'])} 个 (2016-08 ~ 2025-08)")
for idx in INDICES:
    cagrs = [w["indices"][idx["short"]]["cagr"] for w in result["windows"] if idx["short"] in w["indices"] and w["indices"][idx["short"]]["cagr"] is not None]
    mdds = [w["indices"][idx["short"]]["mdd"] for w in result["windows"] if idx["short"] in w["indices"]]
    cagrs.sort(); mdds.sort()
    def pct(arr, p):
        if not arr: return None
        return arr[min(len(arr)-1, int(len(arr)*p))]
    print(f"\n=== {idx['short']} (n={len(cagrs)}) ===")
    print(f"  年化收益: 最低 {pct(cagrs,0)*100:.2f}% | P10 {pct(cagrs,0.1)*100:.2f}% | P25 {pct(cagrs,0.25)*100:.2f}% | 中位 {pct(cagrs,0.5)*100:.2f}% | P75 {pct(cagrs,0.75)*100:.2f}% | P90 {pct(cagrs,0.9)*100:.2f}% | 最高 {pct(cagrs,1)*100:.2f}%")
    neg = sum(1 for c in cagrs if c < 0)
    print(f"  盈利窗口占比: {len(cagrs)-neg}/{len(cagrs)} = {(len(cagrs)-neg)/len(cagrs)*100:.1f}%")
    print(f"  组合最大回撤: 最深 {pct(mdds,0)*100:.2f}% | 中位 {pct(mdds,0.5)*100:.2f}% | 最浅 {pct(mdds,1)*100:.2f}%")
    # 回撤修复时长(交易日 -> 约数月)
    recs = [w["indices"][idx["short"]]["rec_days"] for w in result["windows"] if idx["short"] in w["indices"] and w["indices"][idx["short"]]["rec_days"] is not None]
    nrec = [w for w in result["windows"] if idx["short"] in w["indices"] and w["indices"][idx["short"]]["rec_days"] is None]
    if recs:
        recs.sort()
        print(f"  回撤修复: 中位 {pct(recs,0.5)} 交易日 (约{pct(recs,0.5)//21}个月) | P75 {pct(recs,0.75)}天 | P90 {pct(recs,0.9)}天 | 最长 {pct(recs,1)}天 | 未修复窗口 {len(nrec)}个")

# 最差/最好窗口
print("\n=== 各指数最差(最低年化)5个窗口 ===")
for idx in INDICES:
    ws = sorted([w for w in result["windows"] if idx["short"] in w["indices"] and w["indices"][idx["short"]]["cagr"] is not None],
                key=lambda w: w["indices"][idx["short"]]["cagr"])[:5]
    s = ", ".join(f"{w['start']}~{w['indices'][idx['short']]['end']}: {w['indices'][idx['short']]['cagr']*100:.1f}%" for w in ws)
    print(f"{idx['short']}: {s}")

print("\n=== 各指数最好(最高年化)5个窗口 ===")
for idx in INDICES:
    ws = sorted([w for w in result["windows"] if idx["short"] in w["indices"] and w["indices"][idx["short"]]["cagr"] is not None],
                key=lambda w: w["indices"][idx["short"]]["cagr"], reverse=True)[:5]
    s = ", ".join(f"{w['start']}~{w['indices'][idx['short']]['end']}: {w['indices'][idx['short']]['cagr']*100:.1f}%" for w in ws)
    print(f"{idx['short']}: {s}")
