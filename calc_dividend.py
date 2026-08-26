# -*- coding: utf-8 -*-
"""用价差法计算四个红利指数近12个月股息率
dy ≈ 近12个月全收益指数涨幅 - 近12个月价格指数涨幅 = 分红收益率
"""
import json
from datetime import date, timedelta

PAIRS = [
    ("H00015", "000015", "上证红利"),
    ("H00922", "000922", "中证红利"),
    ("H20269", "H30269", "红利低波"),
    ("H20955", "930955", "红利低波100"),
]

def load(fn):
    d = json.load(open(fn, encoding="utf-8"))
    out = {}
    for r in d["data"]:
        key = r.get("tradeDate") or r.get("date")
        s = str(key).replace("-", "")
        out[s] = r["close"]
    return out

# 近12个月区间: 2025-07-31 -> 2026-07-31 (含首日作为基期)
results = []
for tr_code, pr_code, name in PAIRS:
    tr = load(f"{tr_code}.json")     # 全收益(含分红再投)
    pr = load(f"price_{pr_code}.json")  # 价格
    dates = sorted(d for d in tr if d >= "20250731" and d <= "20260731")

    # 用区间首尾做累计收益差
    d0 = dates[0]; d1 = dates[-1]
    tr0, tr1 = tr[d0], tr[d1]
    pr0, pr1 = pr[d0], pr[d1]
    tr_ret = tr1 / tr0 - 1
    pr_ret = pr1 / pr0 - 1
    dy = tr_ret - pr_ret
    # 逐日累加价差法(页面主口径, 全收益/价格/股息率三者一致自洽)
    tr_daily = 0.0; pr_daily = 0.0; dy_daily = 0.0
    prev_t = prev_p = None
    for d in dates:
        t, p = tr[d], pr[d]
        if prev_t:
            dt = t / prev_t - 1; dp = p / prev_p - 1
            tr_daily += dt; pr_daily += dp; dy_daily += dt - dp
        prev_t, prev_p = t, p

    # 最新股息率: 截止最新交易日的滚动近12个月逐日价差法
    all_dates = sorted(d for d in tr if d in pr)
    last = all_dates[-1]
    y, m_, dd = int(last[:4]), int(last[4:6]), int(last[6:8])
    start = (date(y, m_, dd) - timedelta(days=365)).strftime("%Y%m%d")
    w = [d for d in all_dates if d >= start]
    ldy = 0.0
    prev_t = prev_p = None
    for d in w:
        t, p = tr[d], pr[d]
        if prev_t:
            dt = t / prev_t - 1; dp = p / prev_p - 1
            ldy += dt - dp
        prev_t, prev_p = t, p

    results.append({
        "code": tr_code, "name": name, "d0": d0, "d1": d1,
        "tr_ret": tr_daily, "pr_ret": pr_daily,
        "dy_12m_headtail": dy, "dy_12m_daily": dy_daily,
        "latest_dy": ldy, "latest_d0": w[0], "latest_d1": last,
        "close_tr": tr1, "close_pr": pr1,
    })
    print(f"{name:<10} 近12个月(逐日法): 全收益 {tr_daily*100:6.2f}% | 价格 {pr_daily*100:6.2f}% | "
          f"股息率≈{dy_daily*100:5.2f}%  (首尾法参考 {dy*100:5.2f}%)")
    print(f"       最新({start}~{last})股息率≈{ldy*100:.2f}%")

json.dump(results, open("dividend_yield.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
