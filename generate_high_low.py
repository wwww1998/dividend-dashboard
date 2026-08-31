# -*- coding: utf-8 -*-
"""
四大红利全收益指数 · 每月最高/最低价格定投回测
规则: 每月首个交易日定投10000元, 但分别用当月最高价/最低价买入
输出: high_low_10y.json (供网页使用)
"""
import json, datetime, math

INDICES = [
    {"code": "H00015", "name": "上证红利全收益", "short": "上证红利", "otc": "华泰柏瑞红利ETF联接A(012761)/C(012762)"},
    {"code": "H00922", "name": "中证红利全收益", "short": "中证红利", "otc": "易方达中证红利ETF联接发起式A(009051)/C(009052)"},
    {"code": "H20269", "name": "红利低波全收益", "short": "红利低波", "otc": "华泰柏瑞中证红利低波动ETF联接A(007466)/C(007467)"},
    {"code": "H20955", "name": "红利低波100全收益", "short": "红利低波100", "otc": "景顺长城中证红利低波动100ETF联接A(016128)/C(016129)"},
]

AMOUNT = 10000.0
START, END = "2016-08", "2026-07"

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

def monthly_high_low(series):
    """按年月返回 {ym: (high_date, high_close, low_date, low_close)}"""
    out = {}
    for p in series:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = [p["date"], p["close"], p["date"], p["close"]]
        else:
            if p["close"] > out[ym][1]:
                out[ym][0] = p["date"]; out[ym][1] = p["close"]
            if p["close"] < out[ym][3]:
                out[ym][2] = p["date"]; out[ym][3] = p["close"]
    return out

def yearly_high_low(series):
    """按年返回 {y: (high_date, high_close, low_date, low_close)}"""
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

def compute(seg, start, end, amount, mode="monthly"):
    """mode: 'monthly' or 'yearly'
    seg: 定投区间日线
    """
    first = first_trading_days(seg)
    hl = monthly_high_low(seg) if mode == "monthly" else yearly_high_low(seg)

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
        ym = d[:7] if mode == "monthly" else d[:4]
        is_buy = (d in [v[0] for v in first.values()]) if mode == "monthly" else (d[:4] != (seg[0]["date"][:4]) and d == seg[0]["date"][:4] and False)
        # For yearly: buy on first trading day of year
        if mode == "yearly":
            is_buy = ym in hl and d == hl[ym][0]  # use high date as buy trigger
            # Actually, buy on first trading day of the year
            is_buy = d in [v[0] for v in first.values() if v[0][:4] == ym]

        if is_buy and ym in hl:
            h_date, h_close, l_date, l_close = hl[ym]
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

def compute_result(seg, all_data, start, end, amount, mode="monthly"):
    port_high, port_low, cf_high, cf_low = compute(seg, start, end, amount, mode)

    def make_result(port, cf, label):
        final = port[-1]
        periods = 0
        for p in port:
            if p["invested"] > 0 and p["date"] == port[0]["date"]:
                pass
        # Count periods
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
        # 指数口径
        mdd_i = max_drawdown(seg, "close")
        # 全史
        mdd_all = max_drawdown(all_data)

        # 年度
        years = {}
        for p in port:
            y = p["date"][:4]
            years[y] = p

        close_map = {p["date"]: p["close"] for p in all_data}
        by_yr = {}
        for p in all_data:
            by_yr[p["date"][:4]] = p["close"]
        yr_keys = sorted(by_yr)
        idx_rets = {}
        if "2016" in by_yr:
            base_2016 = close_map.get(start, by_yr.get("2015", by_yr["2016"]))
            idx_rets["2016"] = round(by_yr["2016"] / base_2016 - 1, 4)
        for i in range(1, len(yr_keys)):
            y = yr_keys[i]
            if y <= "2016":
                continue
            idx_rets[y] = round(by_yr[y] / by_yr[yr_keys[i-1]] - 1, 4)

        annual = []
        for y in sorted(years):
            p = years[y]
            base = {"year": y, "invested": p["invested"], "value": p["value"],
                    "profit": p["value"] - p["invested"],
                    "idx_ret": idx_rets.get(y, 0)}
            if y == port[0]["date"][:4]:
                annual.append(base)
            else:
                prev = years[str(int(y) - 1)]
                base["yr_profit"] = (p["value"] - p["invested"]) - (prev["value"] - prev["invested"])
                annual.append(base)

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
            "annual": annual,
        }

    high_r = make_result(port_high, cf_high, "最高价")
    low_r = make_result(port_low, cf_low, "最低价")

    # 提取绘图序列
    for r in [high_r, low_r]:
        port = port_high if r["label"] == "最高价" else port_low
        r["plot"] = {
            "dates": [p["date"] for p in port],
            "value": [round(p["value"], 2) for p in port],
            "invested": [round(p["invested"], 2) for p in port],
        }
        # 组合市值回撤水下
        peak = None; dd_list = []
        for v in r["plot"]["value"]:
            peak = v if peak is None else max(peak, v)
            dd_list.append(round(v / peak - 1, 4))
        r["underwater_port"] = {"dates": r["plot"]["dates"], "dd": dd_list}
        # 指数回撤水下
        peak = None; dd_list = []
        for p in seg:
            peak = p["close"] if peak is None else max(peak, p["close"])
            dd_list.append(round(p["close"] / peak - 1, 4))
        r["underwater_index"] = {"dates": [p["date"] for p in seg], "dd": dd_list}

    return high_r, low_r, port_high, port_low

# ========== 主计算 ==========
result = {"indices": [], "meta": {
    "amount": AMOUNT, "periods": None, "total_invest": None,
    "start": START, "end": END, "generated": "2026-08-26",
    "source": "中证指数官网 csindex.com.cn 日线(全收益指数)"
}}

for idx in INDICES:
    data = load(idx["code"])
    seg = [p for p in data if START.replace("-", "")[:6] <= p["date"].replace("-", "")[:6] <= END.replace("-", "")[:6]]
    high_r, low_r, ph, pl = compute_result(seg, data, "2016-08-01", "2026-07-31", AMOUNT, "monthly")

    result["indices"].append({
        "code": idx["code"], "name": idx["name"], "short": idx["short"], "otc": idx["otc"],
        "high": high_r,
        "low": low_r,
    })

result["meta"]["periods"] = result["indices"][0]["high"]["periods"]
result["meta"]["total_invest"] = result["indices"][0]["high"]["total_invest"]

json.dump(result, open("high_low_10y.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("已生成 high_low_10y.json")

# 打印摘要
print(f"{'指数':<12}{'策略':<6}{'终值':>10}{'总收益':>10}{'年化':>8}{'组合MDD':>9}")
for idx in result["indices"]:
    for s in [idx["high"], idx["low"]]:
        md = s["mdd_port"]["pct"]
        print(f"{idx['short']:<12}{s['label']:<6}{s['final_value']:>10,.0f}{s['total_ret']*100:>9.2f}%{s['cagr']*100:>7.2f}%{md*100:>8.2f}%")