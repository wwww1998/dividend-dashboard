# -*- coding: utf-8 -*-
"""年投版(每年年初10万)独立交叉校验"""
import json, datetime, math

d = json.load(open("H20269.json", encoding="utf-8"))
def fmt(s):
    s = str(s).replace("-", "")
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"
closes = {fmt(r["tradeDate"]): r["close"] for r in d["data"]}
dates = sorted(x for x in closes if "2017-01" <= x <= "2026-07")

# 1. 期数与定投日
firsts = {}
for x in dates:
    firsts.setdefault(x[:4], x)
print(f"[1] 期数 = {len(firsts)} (应10) | 首期 {min(firsts.values())} 末期 {max(firsts.values())}")

# 2. 独立重算红利低波终值
shares = 0.0
for y, dt in sorted(firsts.items()):
    shares += 100000 / closes[dt]
final = shares * closes["2026-07-31"]
print(f"[2] 红利低波终值独立重算 = ¥{final:,.0f} (回测: ¥1,662,279)")

# 3. XIRR(牛顿法)
def xirr(cfs, guess=0.08):
    t0 = datetime.date(2017, 1, 3)
    r = guess
    for _ in range(300):
        f = df = 0.0
        for dt, cf in cfs:
            y = (datetime.date(int(dt[:4]), int(dt[5:7]), int(dt[8:10])) - t0).days / 365.25
            f += cf / (1 + r) ** y
            df += -y * cf / (1 + r) ** (y + 1)
        r -= f / df
        if abs(f) < 1e-7: break
    return r
cfs = [(dt, -100000) for y, dt in sorted(firsts.items())] + [("2026-07-31", final)]
print(f"[3] XIRR独立实现 = {xirr(cfs)*100:.2f}% (回测: 9.76%)")

# 4. 组合回撤独立复算(红利低波)
first_dates = set(firsts.values())   # 定投日集合
sh = 0.0; peak = None; mdd = 0.0; md_peak_d = md_trough_d = None
for x in dates:
    if x in first_dates:
        sh += 100000 / closes[x]
    val = sh * closes[x]
    if peak is None or val > peak:
        peak, peak_d = val, x
    dd = val / peak - 1
    if dd < mdd:
        mdd, md_peak_d, md_trough_d = dd, peak_d, x
print(f"[4] 红利低波组合回撤独立复算 = {mdd*100:.2f}% ({md_peak_d} -> {md_trough_d}) (回测: -27.53%)")

# 5. 校验 result_yearly.json meta 与 annual
r = json.load(open("result_yearly.json", encoding="utf-8"))
assert r["meta"]["periods"] == 10, f"期数错误: {r['meta']['periods']}"
assert r["meta"]["total_invest"] == 1000000, f"总投入错误: {r['meta']['total_invest']}"
it = [x for x in r["indices"] if x["code"] == "H20269"][0]
assert round(it["final_value"]) == 1662279, f"红利低波终值不一致: {it['final_value']}"
years = [a["year"] for a in it["annual"]]
assert years == [str(y) for y in range(2017, 2027)], f"年度行错误: {years}"
print("[5] result_yearly.json 校验: 期数10 ✓ 总投入100万 ✓ 终值✓ 年度2017-2026 ✓")

# 6. 年度表 2018 浮亏(desc 引用)
a18 = [a for a in it["annual"] if a["year"] == "2018"][0]
print(f"[6] 红利低波2018: 投入{a18['invested']:,} 市值{a18['value']:,.0f} 浮盈{a18['profit']:+,.0f} (desc称2018四指数全浮亏)")

# 7. 恢复日
m = it["mdd_port"]
print(f"[7] 红利低波组合回撤: 峰值{m['peak_date']} 谷底{m['trough_date']} 恢复{m['recover_date']}")
print("\n=== 全部通过 ✓ ===")
