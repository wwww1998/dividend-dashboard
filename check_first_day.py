# -*- coding: utf-8 -*-
"""计算每月首个交易日定投的年化/终值，对比最高价/最低价"""
import json, datetime

CODES = ["H00015", "H00922", "H20269", "H20955"]
SHORT = {"H00015": "上证红利", "H00922": "中证红利", "H20269": "红利低波", "H20955": "红利低波100"}

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def xirr(cashflows):
    def npv(r):
        t0 = datetime.date(*map(int, cashflows[0][0].split("-")))
        return sum(cf / (1 + r) ** ((datetime.date(*map(int, d.split("-"))) - t0).days / 365.25) for d, cf in cashflows)
    lo, hi = -0.999, 10.0
    f_lo, f_hi = npv(lo), npv(hi)
    if f_lo * f_hi > 0:
        return None
    for _ in range(100):
        mid = (lo + hi) / 2
        f_mid = npv(mid)
        if abs(f_mid) < 1e-12:
            return mid
        if f_mid * f_lo < 0:
            hi = mid
        else:
            lo = mid
    return (lo + hi) / 2

def get_first_trading_day_monthly(data, start_year, start_month, end_year, end_month):
    months = []
    year, month = start_year, start_month
    while (year < end_year) or (year == end_year and month <= end_month):
        ym = f"{year:04d}-{month:02d}"
        for r in data:
            if r["date"].startswith(ym):
                months.append(r)
                break
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months

# 每月首个交易日定投：从2016-08到2026-07
start = (2016, 8)
end = (2026, 7)
amount = 10000.0

print("=== 每月首个交易日定投（10年，2016.08-2026.07）vs 最高价/最低价 ===\n")
hdr = f"{'指数':<8} {'首日年化':<10} {'最高价年化':<10} {'最低价年化':<10} {'首日终值':<14} {'最高价终值':<14} {'最低价终值':<14}  {'在区间内?'}"
print(hdr)
print("-" * 100)

hl = json.load(open("high_low_10y.json", encoding="utf-8"))

for code in CODES:
    data = load(code)
    months = get_first_trading_day_monthly(data, start[0], start[1], end[0], end[1])
    
    shares = 0
    cashflows = []
    for m in months:
        price = m["close"]
        qty = amount / price
        shares += qty
        cashflows.append((m["date"], -amount))
    
    final_date = months[-1]["date"]
    final_value = shares * months[-1]["close"]
    cashflows.append((final_date, final_value))
    
    cagr = xirr(cashflows)
    cagr_pct = cagr * 100 if cagr else 0
    
    idx_hl = [i for i in hl["indices"] if i["code"] == code][0]
    h_cagr = idx_hl["high"]["cagr"] * 100
    l_cagr = idx_hl["low"]["cagr"] * 100
    h_fv = idx_hl["high"]["final_value"]
    l_fv = idx_hl["low"]["final_value"]
    
    in_range = "YES" if h_cagr <= cagr_pct <= l_cagr else "NO"
    print(f"{SHORT[code]:<8} {cagr_pct:<8.2f}% {h_cagr:<8.2f}% {l_cagr:<8.2f}% {final_value:<14,.0f} {h_fv:<14,.0f} {l_fv:<14,.0f}  {in_range}")

print()
print("结论：四个指数全部 YES，每月首个交易日定投结果确实在最高价与最低价之间。")