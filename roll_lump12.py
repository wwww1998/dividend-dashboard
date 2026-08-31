# -*- coding: utf-8 -*-
"""
任意时点一次性买入, 持有12个月(365天): 盈利概率与收益分布
规则: 每个交易日收盘买入, 365个自然日后按最近交易日收盘卖出(全收益指数, 含分红再投)
对4个红利全收益指数分别统计: 盈利概率 / 收益分位 / 最差最好
"""
import json, bisect, datetime

INDICES = [
    {"code": "H00015", "short": "上证红利"},
    {"code": "H00922", "short": "中证红利"},
    {"code": "H20269", "short": "红利低波"},
    {"code": "H20955", "short": "红利低波100"},
]

def load(code):
    d = json.load(open(f"{code}.json", encoding="utf-8"))
    def fmt(s):
        s = s.replace("-", "")
        return f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    return [{"date": fmt(r["tradeDate"]), "close": r["close"]} for r in d["data"]]

def analyze(code):
    data = load(code)
    dates = [p["date"] for p in data]
    closes = [p["close"] for p in data]
    d2i = {dt: i for i, dt in enumerate(dates)}
    rets = []
    for i, dt in enumerate(dates):
        t0 = datetime.date(*map(int, dt.split("-")))
        t1 = t0 + datetime.timedelta(days=365)
        target = t1.strftime("%Y-%m-%d")
        # 找 <= target 的最后一个交易日
        j = bisect.bisect_right(dates, target) - 1
        if j - i < 240:   # 不足约12个月交易日, 跳过(数据不够)
            continue
        rets.append(closes[j]/closes[i] - 1)
    return dates[0], dates[-1], rets

def pct(arr, p):
    if not arr: return None
    return arr[min(len(arr)-1, int(len(arr)*p))]

print(f"{'指数':<10}{'窗口数':>7}{'盈利概率':>9}{'中位':>8}{'P25':>8}{'P75':>8}{'最差':>8}{'最好':>8}")
results = {}
for idx in INDICES:
    d0, d1, rets = analyze(idx["code"])
    s = sorted(rets)
    win = sum(1 for x in rets if x > 0)/len(rets)*100
    results[idx["short"]] = rets
    print(f"{idx['short']:<10}{len(rets):>7}{win:>8.1f}%{pct(s,.5)*100:>7.1f}%{pct(s,.25)*100:>7.1f}%{pct(s,.75)*100:>7.1f}%{s[0]*100:>7.1f}%{s[-1]*100:>7.1f}%")
    print(f"  数据范围: {d0} ~ {d1} (最后一笔卖出于 {d1})")

print("\n=== 仅最近10年 (2016-08-01 起买入, 与定投页同口径) ===")
print(f"{'指数':<10}{'窗口数':>7}{'盈利概率':>9}{'中位':>8}{'P25':>8}{'P75':>8}{'最差':>8}{'最好':>8}")
for idx in INDICES:
    data = load(idx["code"])
    dates = [p["date"] for p in data]
    closes = [p["close"] for p in data]
    start_i = bisect.bisect_left(dates, "2016-08-01")
    rets = []
    for k in range(start_i, len(dates)):
        target = (datetime.date(*map(int, dates[k].split("-"))) + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        j = bisect.bisect_right(dates, target) - 1
        if j - k < 240: continue
        rets.append(closes[j]/closes[k] - 1)
    s = sorted(rets)
    win = sum(1 for x in rets if x > 0)/len(rets)*100
    print(f"{idx['short']:<10}{len(rets):>7}{win:>8.1f}%{pct(s,.5)*100:>7.1f}%{pct(s,.25)*100:>7.1f}%{pct(s,.75)*100:>7.1f}%{s[0]*100:>7.1f}%{s[-1]*100:>7.1f}%")

# 汇总: 最差的起点(哪些时点买入会亏)
print("\n=== 各指数亏损概率最高/最差时段(按年统计买入持有12个月盈利概率) ===")
for idx in INDICES:
    d0, d1, rets = analyze(idx["code"])
    data = load(idx["code"])
    dates = [p["date"] for p in data]
    # 按买入年份分组
    by_year = {}
    for k, dt in enumerate(dates):
        target = (datetime.date(*map(int, dt.split("-"))) + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
        j = bisect.bisect_right(dates, target) - 1
        if j - k < 240: continue
        ret = data[j]["close"]/data[k]["close"] - 1
        by_year.setdefault(dt[:4], []).append(ret)
    line = f"{idx['short']}: "
    for y in sorted(by_year):
        r = by_year[y]
        w = sum(1 for x in r if x>0)/len(r)*100
        line += f"{y}年{w:.0f}% "
    print(line)
