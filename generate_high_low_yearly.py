# -*- coding: utf-8 -*-
"""
四大红利全收益指数 · 每年最高/最低价格定投回测
规则: 每年年初首个交易日定投100000元, 分别用当年最高价/最低价买入
"""
import json, datetime, math, sys

INDICES = [
    {"code": "H00015", "name": "上证红利全收益", "short": "上证红利", "otc": "华泰柏瑞红利ETF联接A(012761)/C(012762)"},
    {"code": "H00922", "name": "中证红利全收益", "short": "中证红利", "otc": "易方达中证红利ETF联接发起式A(009051)/C(009052)"},
    {"code": "H20269", "name": "红利低波全收益", "short": "红利低波", "otc": "华泰柏瑞中证红利低波动ETF联接A(007466)/C(007467)"},
    {"code": "H20955", "name": "红利低波100全收益", "short": "红利低波100", "otc": "景顺长城中证红利低波动100ETF联接A(016128)/C(016129)"},
]

AMOUNT = 100000.0

def get_start_end(years):
    end_y = 2026
    end_m = 7
    if years == 10:
        start_y = 2017; start_m = 1
    elif years == 5:
        start_y = 2022; start_m = 1
    elif years == 3:
        start_y = 2024; start_m = 1
    elif years == 1:
        start_y = 2025; start_m = 1
    start = f"{start_y:04d}-{start_m:02d}"
    end = f"{end_y:04d}-{end_m:02d}"
    return start, end

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
    peak = None; peak_d = None
    mdd = 0.0; mdd_peak_d = None; mdd_trough_d = None; mdd_peak_v = None; mdd_trough_v = None
    for p in series:
        v = p[value_key]
        if peak is None or v > peak:
            peak, peak_d = v, p["date"]
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd; mdd_peak_d = peak_d; mdd_trough_d = p["date"]; mdd_peak_v = peak; mdd_trough_v = v
    recover = None
    if mdd_peak_d:
        started = False
        for p in series:
            if p["date"] == mdd_peak_d:
                started = True
                continue
            if started and p[value_key] >= mdd_peak_v:
                recover = p["date"]; break
    return mdd, mdd_peak_d, mdd_trough_d, recover, mdd_peak_v, mdd_trough_v

def first_trading_days(series):
    out = {}
    for p in series:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = (p["date"], p["close"])
    return out

def yearly_high_low(series):
    out = {}
    for p in series:
        y = p["date"][:4]
        if y not in out:
            out[y] = [p["date"], p["close"], p["date"], p["close"]]
        else:
            if p["close"] > out[y][1]:
                out[y][0] = p["date"]; out[y][1] = p["close"]
            if p["close"] < out[y][3]:
                out[y][2] = p["date"]; out[y][3] = p["close"]
    return out

def compute(seg, start, end, amount):
    first = first_trading_days(seg)
    hl = yearly_high_low(seg)

    shares_high = 0.0
    shares_low = 0.0
    invested_high = 0.0
    invested_low = 0.0
    cashflows_high = []
    cashflows_low = []
    port_high = []
    port_low = []

    for p in seg:
        d = p["date"]
        y = d[:4]
        # 每年首个交易日买入
        first_dates = [v[0] for v in first.values() if v[0][:4] == y]
        is_buy = d in first_dates

        if is_buy and y in hl:
            h_date, h_close, l_date, l_close = hl[y]
            shares_high += amount / h_close
            invested_high += amount
            shares_low += amount / l_close
            invested_low += amount
            cashflows_high.append((d, -amount))
            cashflows_low.append((d, -amount))

        port_high.append({"date": d, "close": p["close"], "shares": shares_high,
                          "value": shares_high * p["close"], "invested": invested_high})
        port_low.append({"date": d, "close": p["close"], "shares": shares_low,
                         "value": shares_low * p["close"], "invested": invested_low})

    return port_high, port_low, cashflows_high, cashflows_low

def make_result(port, cf, label):
    final = port[-1]
    periods = 0
    prev_inv = 0
    for p in port:
        if p["invested"] > prev_inv:
            periods += 1
            prev_inv = p["invested"]
    total_invest = final["invested"]
    total_ret = final["value"] / total_invest - 1 if total_invest > 0 else 0
    cf_final = cf + [(final["date"], final["value"])]
    cagr = xirr(cf_final)

    mdd_p = max_drawdown(port, "value")
    mdd_i = max_drawdown(seg, "close")

    return {
        "label": label,
        "final_date": final["date"], "final_value": round(final["value"], 2),
        "total_invest": round(total_invest, 2), "total_ret": round(total_ret, 4),
        "cagr": round(cagr, 4) if cagr else None,
        "periods": periods,
        "mdd_port": {"pct": round(mdd_p[0], 4), "peak_date": mdd_p[1], "trough_date": mdd_p[2],
                     "recover_date": mdd_p[3], "peak_value": round(mdd_p[4], 2), "trough_value": round(mdd_p[5], 2)},
        "mdd_index": {"pct": round(mdd_i[0], 4), "peak_date": mdd_i[1], "trough_date": mdd_i[2],
                      "recover_date": mdd_i[3]},
    }

if len(sys.argv) != 2:
    print("Usage: python generate_high_low_yearly.py N")
    print("N: 1, 3, 5, 10")
    sys.exit(1)

years = int(sys.argv[1])
start, end = get_start_end(years)
print(f"每年定投区间 {start} - {end}, 年限 {years} 年")

result = {"indices": [], "meta": {
    "amount": AMOUNT, "periods": None, "total_invest": None,
    "start": start, "end": end, "generated": "2026-08-31",
    "source": "中证指数官网 csindex.com.cn 日线(全收益指数)"
}}

for idx in INDICES:
    data = load(idx["code"])
    seg = [p for p in data if start.replace("-", "")[:6] <= p["date"].replace("-", "")[:6] <= end.replace("-", "")[:6]]
    port_high, port_low, cf_high, cf_low = compute(seg, start, end, AMOUNT)

    high_r = make_result(port_high, cf_high, "最高价")
    low_r = make_result(port_low, cf_low, "最低价")

    for r in [high_r, low_r]:
        port = port_high if r["label"] == "最高价" else port_low
        r["plot"] = {
            "dates": [p["date"] for p in port],
            "value": [round(p["value"], 2) for p in port],
            "invested": [round(p["invested"], 2) for p in port],
        }
        peak = None; dd_list = []
        for v in r["plot"]["value"]:
            peak = v if peak is None else max(peak, v)
            dd_list.append(round(v / peak - 1, 4))
        r["underwater_port"] = {"dates": r["plot"]["dates"], "dd": dd_list}
        peak = None; dd_list = []
        for p in seg:
            peak = p["close"] if peak is None else max(peak, p["close"])
            dd_list.append(round(p["close"] / peak - 1, 4))
        r["underwater_index"] = {"dates": [p["date"] for p in seg], "dd": dd_list}

    result["indices"].append({
        "code": idx["code"], "name": idx["name"], "short": idx["short"], "otc": idx["otc"],
        "high": high_r,
        "low": low_r,
    })

result["meta"]["periods"] = result["indices"][0]["high"]["periods"]
result["meta"]["total_invest"] = result["indices"][0]["high"]["total_invest"]

outfn = f"high_low_yearly_{years}y.json"
json.dump(result, open(outfn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"已生成 {outfn}")

print(f"{'指数':<12}{'策略':<6}{'终值':>10}{'总收益':>10}{'年化':>8}{'组合MDD':>9}")
for idx in result["indices"]:
    for s in [idx["high"], idx["low"]]:
        md = s["mdd_port"]["pct"]
        print(f"{idx['short']:<12}{s['label']:<6}{s['final_value']:>10,.0f}{s['total_ret']*100:>9.2f}%{s['cagr']*100:>7.2f}%{md*100:>8.2f}%")