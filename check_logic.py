# -*- coding: utf-8 -*-
"""独立交叉验证：用与 backtest.py 不同的实现抽查核心数字"""
import json, math, datetime

# ---------- 1. 验证期数与定投日 ----------
d = json.load(open("H20269.json", encoding="utf-8"))
dates = [str(r["tradeDate"]).replace("-", "") for r in d["data"]]
dates = [x for x in dates if "201607" <= x[:6] <= "202607"]
# 每月首个交易日
firsts = {}
for x in dates:
    firsts.setdefault(x[:6], x)
print(f"[1] 期数 = {len(firsts)} (应为121)")
print(f"    首期 {min(firsts.values())}  末期 {max(firsts.values())}  首末 = {list(firsts.values())[:2]} ... {list(firsts.values())[-2:]}")

# ---------- 2. 独立重算红利低波终值(年金近似粗验) ----------
closes = {x: v for x, v in [(str(r["tradeDate"]).replace("-", ""), r["close"]) for r in d["data"]]}
shares = 0.0
for ym, dt in sorted(firsts.items()):
    shares += 10000 / closes[dt]
final_val = shares * closes["20260731"]
print(f"[2] 红利低波终值(独立重算) = ¥{final_val:,.0f} (backtest: ¥1,993,148)")

# ---------- 3. 独立验证XIRR ----------
def xirr_newton(cfs, guess=0.08):
    t0 = datetime.date(2016, 7, 1)
    r = guess
    for _ in range(200):
        f = 0.0; df = 0.0
        for dt, cf in cfs:
            y = (datetime.date(int(dt[:4]), int(dt[4:6]), int(dt[6:8])) - t0).days / 365.25
            f += cf / (1 + r) ** y
            df += -y * cf / (1 + r) ** (y + 1)
        r -= f / df
        if abs(f) < 1e-6: break
    return r
cfs = [(dt, -10000) for ym, dt in sorted(firsts.items())] + [("20260731", final_val)]
xirr = xirr_newton(cfs)
print(f"[3] XIRR(牛顿法独立实现) = {xirr*100:.2f}% (backtest二分法: 9.57%)")

# ---------- 4. 独立验证中证红利股息率(对数差法) ----------
def load(fn, key="tradeDate"):
    dd = json.load(open(fn, encoding="utf-8"))
    out = {}
    for r in dd["data"]:
        k = str(r.get(key) or r.get("date")).replace("-", "")
        out[k] = r["close"]
    return out
tr = load("H00922.json"); pr = load("price_000922.json")
days = [x for x in sorted(tr) if "20250731" <= x <= "20260731"]
# 对数差法
logsum = 0.0
for i in range(1, len(days)):
    x = days[i]
    logsum += math.log(tr[x] / tr[days[i-1]]) - math.log(pr[x] / pr[days[i-1]])
print(f"[4] 中证红利股息率(对数差) = {logsum*100:.2f}% (逐日法: 4.12%, 首尾法: 4.28%, Wind TTM: 4.24%)")

# ---------- 5. 验证恢复日天数 ----------
mdd = json.load(open("result.json", encoding="utf-8"))
for it in mdd["indices"]:
    m = it["mdd_port"]
    d1 = datetime.date(*map(int, m["peak_date"].split("-")))
    d2 = datetime.date(*map(int, m["recover_date"].split("-")))
    print(f"[5] {it['short']}: 峰值{m['peak_date']} 谷底{m['trough_date']} 恢复{m['recover_date']} ({(d2-d1).days}天)")

# ---------- 6. 验证当年盈亏口径: 红利低波2024 ----------
it = [x for x in mdd["indices"] if x["code"] == "H20269"][0]
a24 = [a for a in it["annual"] if a["year"] == "2024"][0]
a23 = [a for a in it["annual"] if a["year"] == "2023"][0]
calc = (a24["value"] - a24["invested"]) - (a23["value"] - a23["invested"])
print(f"[6] 红利低波2024 当年盈亏 = {calc:,.0f} (annual表: {a24.get('yr_profit',0):,.0f})")
