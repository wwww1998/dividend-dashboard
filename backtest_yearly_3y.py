# -*- coding: utf-8 -*-
"""
四大红利全收益指数 3年每年定投回测 + 真实回撤计算
规则: 每年年初(1月首个交易日)定投100000元, 2024-01 ~ 2026-07, 共3期, 总投入30万
输出: result_yearly_3y.json (供网页使用)
"""
import json, datetime, math

INDICES = [
    {"code": "H00015", "name": "上证红利全收益", "short": "上证红利", "otc": "华泰柏瑞红利ETF联接A(012761)/C(012762)"},
    {"code": "H00922", "name": "中证红利全收益", "short": "中证红利", "otc": "易方达中证红利ETF联接发起式A(009051)/C(009052)"},
    {"code": "H20269", "name": "红利低波全收益", "short": "红利低波", "otc": "华泰柏瑞中证红利低波动ETF联接A(007466)/C(007467)"},
    {"code": "H20955", "name": "红利低波100全收益", "short": "红利低波100", "otc": "景顺长城中证红利低波动100ETF联接A(016128)/C(016129)"},
]

AMOUNT = 100000.0
START, END = "2024-01", "2026-07"   # 定投区间(每年年初定投, 2024-2026 共3期)

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def xirr(cashflows, lo=-0.999, hi=10.0):
    """cashflows: [(date_str, amount)], 解年化收益率(复利)"""
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
    """返回 (最大回撤%, 峰值日期, 谷底日期, 恢复日期或None, 峰值value, 谷底value)"""
    peak = None; peak_d = None
    mdd = 0.0; mdd_peak_d = None; mdd_trough_d = None; mdd_peak_v = None; mdd_trough_v = None
    for p in series:
        v = p[value_key]
        if peak is None or v > peak:
            peak, peak_d = v, p["date"]
        dd = v / peak - 1
        if dd < mdd:
            mdd = dd; mdd_peak_d = peak_d; mdd_trough_d = p["date"]; mdd_peak_v = peak; mdd_trough_v = v
    # 找恢复日(峰值日之后第一次回到峰值)
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
    """按年取每年第一个交易日(1月首个交易日) {year: (date, close)}"""
    out = {}
    for p in series:
        y = p["date"][:4]
        if y not in out:
            out[y] = (p["date"], p["close"])
    return out

result = {"indices": [], "meta": {
    "amount": AMOUNT, "periods": None, "total_invest": None,
    "start": START, "end": END, "generated": "2026-08-26",
    "source": "中证指数官网 csindex.com.cn 日线(全收益指数)"
}}

for idx in INDICES:
    data = load(idx["code"])
    # 截取定投区间: 2024-01-01 ~ 2026-07-31
    seg = [p for p in data if START.replace("-", "")[:6] <= p["date"].replace("-", "")[:6] <= END.replace("-", "")[:6]]
    # 需要定投起点前一交易日(用于首次定投后市值)
    first = first_trading_days(seg)
    # 投入现金流
    cashflows = []          # [(date, amount)]
    shares = 0.0            # 累计份额
    invested = 0.0          # 累计投入
    port_series = []        # 逐日组合市值
    t0 = None
    for p in seg:
        d = p["date"]
        if d in [v[0] for v in first.values()]:   # 每年第一个交易日
            shares += AMOUNT / p["close"]
            invested += AMOUNT
            cashflows.append((d, -AMOUNT))
        port_series.append({"date": d, "close": p["close"], "shares": shares,
                            "value": shares * p["close"], "invested": invested})
    # 终值
    final = port_series[-1]
    periods = len([v for v in first.values() if v[0] <= seg[-1]["date"]])
    total_invest = invested
    total_ret = final["value"] / total_invest - 1
    # 年化(XIRR): 终值作为最后现金流入
    cf = cashflows + [(final["date"], final["value"])]
    cagr = xirr(cf)
    # 组合口径回撤
    mdd_p = max_drawdown(port_series, "value")
    # 组合浮亏金额 = 峰值市值-谷底市值
    # 指数口径回撤(定投区间内)
    idx_series = [{"date": p["date"], "close": p["close"]} for p in seg]
    mdd_i = max_drawdown(idx_series)
    # 全史口径回撤
    mdd_all = max_drawdown(data)
    # 年度表现
    years = {}
    for p in port_series:
        y = p["date"][:4]
        years[y] = p
    # 指数年度涨跌幅(全收益, 用全史数据)
    # 口径: 2016年为定投起点(2016-07-01)至年末, 其余年份为自然年(上年末→本年末)
    close_map = {p["date"]: p["close"] for p in data}
    by_yr = {}
    for p in data:
        by_yr[p["date"][:4]] = p["close"]
    yr_keys = sorted(by_yr)
    idx_rets = {}
    for i in range(1, len(yr_keys)):
        y = yr_keys[i]
        idx_rets[y] = round(by_yr[y] / by_yr[yr_keys[i-1]] - 1, 4)
    annual = []
    prev_yr_end = None
    for y in sorted(years):
        p = years[y]
        base = {"year": y, "invested": p["invested"], "value": p["value"],
                "profit": p["value"] - p["invested"],
                "idx_ret": idx_rets.get(y, 0)}
        if y == "2024":
            annual.append(base)
        else:
            prev = years[str(int(y) - 1)]
            base["yr_profit"] = (p["value"] - p["invested"]) - (prev["value"] - prev["invested"])
            annual.append(base)
    result["indices"].append({
        "code": idx["code"], "name": idx["name"], "short": idx["short"], "otc": idx["otc"],
        "final_date": final["date"], "final_value": round(final["value"], 2),
        "total_invest": round(total_invest, 2), "total_ret": round(total_ret, 4),
        "cagr": round(cagr, 4) if cagr else None,
        "periods": periods,
        "mdd_port": {"pct": round(mdd_p[0], 4), "peak_date": mdd_p[1], "trough_date": mdd_p[2],
                     "recover_date": mdd_p[3], "peak_value": round(mdd_p[4], 2), "trough_value": round(mdd_p[5], 2)},
        "mdd_index_10y": {"pct": round(mdd_i[0], 4), "peak_date": mdd_i[1], "trough_date": mdd_i[2],
                          "recover_date": mdd_i[3]},
        "mdd_index_all": {"pct": round(mdd_all[0], 4), "peak_date": mdd_all[1], "trough_date": mdd_all[2],
                          "recover_date": mdd_all[3]},
        "annual": annual,
        "port_series": port_series,   # 供绘图: date, value, invested
    })

result["meta"]["periods"] = periods
result["meta"]["total_invest"] = total_invest

# 提取绘图序列(轻量化)
for idx in result["indices"]:
    idx["plot"] = {
        "dates": [p["date"] for p in idx["port_series"]],
        "value": [round(p["value"], 2) for p in idx["port_series"]],
        "invested": [round(p["invested"], 2) for p in idx["port_series"]],
    }
    idx["port_series"] = None
    # 指数回撤水下序列(定投区间)
    peak = None; underwater = []
    for p in idx["plot"]["dates"] and []:
        pass
    # 用 seg 数据重算水下
    data = load(idx["code"])  # 每个指数各自的原始日线(这里不能沿用外层第一个循环残留的 data)
    seg2 = [p for p in data if START.replace("-", "")[:6] <= p["date"].replace("-", "")[:6] <= END.replace("-", "")[:6]]
    peak = None; dd_list = []
    for p in seg2:
        peak = p["close"] if peak is None else max(peak, p["close"])
        dd_list.append(round(p["close"] / peak - 1, 4))
    idx["underwater_index"] = {"dates": [p["date"] for p in seg2], "dd": dd_list}
    # 组合市值回撤水下序列
    peak = None; dd_list = []
    for p in [q for q in idx["plot"]["dates"]]:
        pass
    peak = None; dd_list = []; dates2 = idx["plot"]["dates"]
    for k, v in enumerate(idx["plot"]["value"]):
        peak = v if peak is None else max(peak, v)
        dd_list.append(round(v / peak - 1, 4))
    idx["underwater_port"] = {"dates": dates2, "dd": dd_list}

json.dump(result, open("result_yearly_3y.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 打印摘要
print(f"{'指数':<12}{'终值':>10}{'总收益':>10}{'年化':>8}{'组合MDD':>9}{'指数3yMDD':>11}{'指数全史MDD':>12}")
for idx in result["indices"]:
    md = idx["mdd_port"]["pct"]
    mi = idx["mdd_index_10y"]["pct"]
    ma = idx["mdd_index_all"]["pct"]
    print(f"{idx['short']:<12}{idx['final_value']:>10,.0f}{idx['total_ret']*100:>9.2f}%{idx['cagr']*100:>7.2f}%"
          f"{md*100:>8.2f}%{mi*100:>10.2f}%{ma*100:>11.2f}%")
print()
print("=== 组合口径回撤明细(定投者实际浮亏) ===")
for idx in result["indices"]:
    m = idx["mdd_port"]
    print(f"{idx['short']}: {m['pct']*100:.2f}%  峰值{m['peak_date']}({m['peak_value']:,.0f}) -> 谷底{m['trough_date']}({m['trough_value']:,.0f})  浮亏{m['peak_value']-m['trough_value']:,.0f}元  恢复:{m['recover_date'] or '未恢复'}")
print()
print("=== 指数口径回撤明细(定投区间3年) ===")
for idx in result["indices"]:
    m = idx["mdd_index_10y"]
    print(f"{idx['short']}: {m['pct']*100:.2f}%  {m['peak_date']} -> {m['trough_date']}  恢复:{m['recover_date'] or '未恢复'}")
print()
print("=== 指数全史最大回撤 ===")
for idx in result["indices"]:
    m = idx["mdd_index_all"]
    print(f"{idx['short']}: {m['pct']*100:.2f}%  {m['peak_date']} -> {m['trough_date']}  恢复:{m['recover_date'] or '未恢复'}")
