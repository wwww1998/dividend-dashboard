# -*- coding: utf-8 -*-
"""
加速定投 vs 基线: 12期投完(停止日)盈利概率 + 未盈利起点停止后的回正耗时(最大/中位)
规则A: 峰值回撤>=10% 加投3倍
规则B: 相对起点跌幅>=15% 加投5倍
"""
import json

INDICES = [
    {"code": "H00015", "short": "上证红利"},
    {"code": "H00922", "short": "中证红利"},
    {"code": "H20269", "short": "红利低波"},
    {"code": "H20955", "short": "红利低波100"},
]
BASE = 10000.0
N = 12

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def first_days(data):
    out = {}
    for p in data:
        ym = p["date"][:7]
        if ym not in out:
            out[ym] = p["date"]
    return out

DATA = {i["code"]: load(i["code"]) for i in INDICES}
FIRST = {i["code"]: first_days(DATA[i["code"]]) for i in INDICES}

STARTS = []
for y in range(2016, 2026):
    for m in range(1, 13):
        ym = f"{y:04d}-{m:02d}"
        if "2016-08" <= ym <= "2024-08":
            STARTS.append(ym)

def inv_days(code, start_ym, n):
    first = FIRST[code]
    days = []
    y, m = int(start_ym[:4]), int(start_ym[5:7])
    for _ in range(n):
        ym2 = f"{y:04d}-{m:02d}"
        d = first.get(ym2)
        if d is None: return None
        days.append(d)
        y, m = (y+1,1) if m==12 else (y,m+1)
    return days

def backtest(code, start_ym, rule, data):
    """rule: None(基线) 或 (mode, threshold, mult)"""
    inv = inv_days(code, start_ym, N)
    if inv is None: return None
    inv_set = set(inv)
    d0, d_stop = inv[0], inv[-1]
    shares = 0.0; invested = 0.0
    peak = None; start_close = None; prev_close = None
    stop_day = None
    for p in data:
        if p["date"] < d0: continue
        if peak is None or p["close"] > peak:
            peak = p["close"]
        if p["date"] in inv_set:
            close = p["close"]
            if start_close is None: start_close = close
            if rule:
                mode, threshold, mult = rule
                if mode == "peak":
                    dd = close/peak - 1
                else:
                    dd = close/start_close - 1
                amt = BASE*mult if dd <= -threshold else BASE
            else:
                amt = BASE
            shares += amt/close
            invested += amt
        if p["date"] == d_stop:
            stop_day = p["date"]
            break
    value_at_stop = shares*p["close"]
    profit_at_stop = value_at_stop - invested
    # 停止后持有, 找回正日(市值回到累计投入)
    recover_days = None; recover_date = None
    if profit_at_stop <= 0:
        for p in data:
            if p["date"] <= d_stop: continue
            if shares*p["close"] > invested + 1e-6:
                recover_days = (__import__("datetime").date(*map(int,p["date"].split("-")))
                                - __import__("datetime").date(*map(int,d_stop.split("-")))).days
                recover_date = p["date"]
                break
    return {"profit_at_stop": profit_at_stop, "recover_days": recover_days, "recover_date": recover_date}

def analyze(code, rule):
    data = DATA[code]
    rows = [r for sm in STARTS if (r:=backtest(code, sm, rule, data)) is not None]
    n = len(rows)
    n_profit = sum(1 for r in rows if r["profit_at_stop"]>0)
    rec_days = [r["recover_days"] for r in rows if r["recover_days"] is not None]
    unrec = [r for r in rows if r["profit_at_stop"]<=0 and r["recover_days"] is None]
    return {
        "n_profit": n_profit, "n": n,
        "rec_med": sorted(rec_days)[len(rec_days)//2] if rec_days else None,
        "rec_max": max(rec_days) if rec_days else None,
        "unrec": unrec,
    }

RULES = {
    "基线(不加速)": None,
    "峰值回撤10%×3倍": ("peak", 0.10, 3),
    "相对起点15%×5倍": ("start", 0.15, 5),
}
for idx in INDICES:
    short = idx["short"]
    print(f"\n=== {short} ===")
    print(f"{'规则':<18}{'停止日盈利':>10}{'亏损起点回正':>12}{'最长等待':>10}")
    for name, rule in RULES.items():
        a = analyze(idx["code"], rule)
        print(f"{name:<18}{a['n_profit']:>6}/{a['n']}{'':>3}{a['rec_med'] if a['rec_med'] is not None else '-':>9}天{str(a['rec_max'])+'天' if a['rec_max'] else '-':>10}")
        if a["unrec"]:
            print(f"  未回正起点: {[(sm,) for sm in STARTS if False]}")
