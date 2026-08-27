# -*- coding: utf-8 -*-
"""120期月投版独立复核: 期数/终值/XIRR/回撤/年度 (与backtest.py不同实现)"""
import json, datetime

# ---------- 1. 期数与定投日 ----------
d = json.load(open("H20269.json", encoding="utf-8"))
def fmt(s):
    s = str(s).replace("-", "")
    return f"{s[:4]}-{s[4:6]}-{s[6:]}"
closes = {fmt(r["tradeDate"]): r["close"] for r in d["data"]}
dates = sorted(x for x in closes if "2016-08" <= x <= "2026-07")
firsts = {}
for x in dates:
    firsts.setdefault(x[:7], x)   # 每月首个交易日
print(f"[1] 期数 = {len(firsts)} (应120) | 首期 {min(firsts.values())} 末期 {max(firsts.values())}")

# ---------- 2. 独立重算红利低波终值 ----------
shares = 0.0
for ym, dt in sorted(firsts.items()):
    shares += 10000 / closes[dt]
final = shares * closes["2026-07-31"]
print(f"[2] 红利低波终值独立重算 = ¥{final:,.0f} (回测: ¥1,967,153)")

# ---------- 3. XIRR(牛顿法) ----------
def xirr(cfs, guess=0.08):
    t0 = datetime.date(2016, 8, 1)
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
cfs = [(dt, -10000) for ym, dt in sorted(firsts.items())] + [("2026-07-31", final)]
print(f"[3] XIRR独立实现 = {xirr(cfs)*100:.2f}% (回测: 9.56%)")

# ---------- 4. 组合回撤独立复算(红利低波) ----------
first_dates = set(firsts.values())
sh = 0.0; peak = None; mdd = 0.0; pk_d = tr_d = None
for x in dates:
    if x in first_dates:
        sh += 10000 / closes[x]
    val = sh * closes[x]
    if peak is None or val > peak:
        peak, pk_d = val, x
    dd = val / peak - 1
    if dd < mdd:
        mdd, tr_d = dd, x
print(f"[4] 红利低波组合回撤独立复算 = {mdd*100:.2f}% ({pk_d} -> {tr_d}) (回测: -14.79%)")

# ---------- 5. result.json meta 与四指数关键值 ----------
r = json.load(open("result.json", encoding="utf-8"))
m = r["meta"]
print(f"[5] meta: 期数{m['periods']} 总投入{m['total_invest']:,} 区间{m['start']}~{m['end']}")
assert m["periods"] == 120 and m["total_invest"] == 1200000, "meta错误"
exp = {"H00015": (1837767, -17.06), "H00922": (1834922, -13.40), "H20269": (1967153, -14.79), "H20955": (1848858, -11.53)}
for it in r["indices"]:
    fv, mddp = exp[it["code"]]
    ok_fv = abs(it["final_value"] - fv) < 1
    ok_mdd = abs(round(it["mdd_port"]["pct"]*100, 2) - mddp) < 0.02
    print(f"    {it['short']}: 终值{it['final_value']:,.0f}({'✓' if ok_fv else '✗'}) MDD {round(it['mdd_port']['pct']*100,2)}%({'✓' if ok_mdd else '✗'})")
    assert ok_fv and ok_mdd

# ---------- 6. 年度行与首年 ----------
it = [x for x in r["indices"] if x["code"] == "H20269"][0]
years = [a["year"] for a in it["annual"]]
print(f"[6] 年度行: {years[0]}~{years[-1]} 共{len(years)}行 (首年{it['annual'][0]['invested']:,} = 5期×1万)")
assert years[0] == "2016" and len(years) == 11

# ---------- 7. 年度涨跌矩阵2016(定投起点8月) ----------
a16 = [a for a in it["annual"] if a["year"] == "2016"][0]
print(f"[7] 红利低波2016: 指数涨幅{a16['idx_ret']*100:+.2f}% (起点2016-08-01) 投入{a16['invested']:,} 市值{a16['value']:,.0f}")
print("\n=== 全部通过 ✓ ===")
