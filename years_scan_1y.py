# -*- coding: utf-8 -*-
"""
近1年定投(每月首个交易日 ¥10,000) · 滚动年度窗口逐份测算
窗口: 2025-08~2026-07, 2024-08~2025-07, ... 往前推至 2016-08~2017-07
输出: 每个窗口 4 指数的 终值/总收益/年化/组合MDD
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

def max_drawdown(series, value_key="close"):
    peak = None
    mdd = 0.0
    for p in series:
        v = p[value_key]
        if peak is None or v > peak:
            peak = v
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd
    return mdd

def first_trading_days(series):
    out = {}
    for p in series:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = (p["date"], p["close"])
    return out

def run_year(start, end):
    """一个年度窗口: start='YYYY-MM' end='YYYY-MM'"""
    sm, em = start.replace("-", "")[:6], end.replace("-", "")[:6]
    row = {}
    for idx in INDICES:
        data = load(idx["code"])
        seg = [p for p in data if sm <= p["date"].replace("-", "")[:6] <= em]
        first = first_trading_days(seg)
        shares = 0.0; invested = 0.0
        port = []
        for p in seg:
            d = p["date"]
            if d in [v[0] for v in first.values()]:
                shares += AMOUNT / p["close"]
                invested += AMOUNT
            port.append({"date": d, "value": shares * p["close"], "invested": invested})
        final = port[-1]
        periods = len([v for v in first.values() if v[0] <= seg[-1]["date"]])
        total_ret = final["value"] / final["invested"] - 1
        # XIRR: 每月投入-10000, 期末终值+
        cashflows = []
        prev_d = None
        for p in seg:
            d = p["date"]
            if d in [v[0] for v in first.values()]:
                cashflows.append((d, -AMOUNT))
        cashflows.append((final["date"], final["value"]))
        cagr = xirr(cashflows)
        mdd_port = max_drawdown(port, "value")
        row[idx["short"]] = {
            "periods": periods, "invested": final["invested"],
            "final": final["value"], "ret": total_ret, "cagr": cagr, "mdd": mdd_port,
        }
    return row

# 年度窗口: 从当前 2025-08~2026-07 往前推到 2016-08~2017-07
windows = []
for y in range(2025, 2015, -1):
    windows.append((f"{y}-08", f"{y+1}-07"))

print(f"{'窗口':<22}{'指数':<10}{'期数':>4}{'总投入':>8}{'终值':>10}{'总收益':>9}{'年化':>8}{'组合MDD':>9}")
for start, end in windows:
    r = run_year(start, end)
    for idx in INDICES:
        d = r[idx["short"]]
        cagr = f"{d['cagr']*100:.2f}%" if d["cagr"] else "N/A"
        print(f"{start}~{end:<11}{idx['short']:<10}{d['periods']:>4}{d['invested']:>8,.0f}"
              f"{d['final']:>10,.0f}{d['ret']*100:>8.2f}%{cagr:>8}{d['mdd']*100:>8.2f}%")
    print()
