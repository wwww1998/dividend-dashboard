# -*- coding: utf-8 -*-
"""
任意月初买入, 持有12个月(365天): 盈利概率与收益分布
规则: 每月首个交易日收盘买入, 365个自然日后按最近交易日收盘卖出(全收益, 含分红再投)
对4个红利全收益指数分别统计: 盈利概率 / 收益分位 / 最差最好 / 按采购年份
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

def month_first_indexes(data):
    """连续几月首日的开盘索引(跳过缺口月份的小区间)"""
    dates = [p["date"] for p in data]
    idxs = []
    prev_ym = None
    for i, dt in enumerate(dates):
        ym = dt[:7]
        if ym != prev_ym:
            idxs.append(i)
            prev_ym = ym
    return idxs

def ret_series(data, start_i):
    dates = [p["date"] for p in data]
    closes = [p["close"] for p in data]
    t0 = datetime.date(*map(int, dates[start_i].split("-")))
    target = (t0 + datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    j = bisect.bisect_right(dates, target) - 1
    if j - start_i < 240:
        return None, None, None
    return closes[j]/closes[start_i] - 1, dates[start_i], dates[j]

def pct(arr, p):
    if not arr: return None
    return arr[min(len(arr)-1, int(len(arr)*p))]

print("=== 任意月初买入, 持有12个月 ===")
print(f"{'指数':<10}{'次数':>6}{'盈利概率':>9}{'中位':>8}{'P25':>8}{'P75':>8}{'最差':>8}{'最好':>8}")
for idx in INDICES:
    data = load(idx["code"])
    m = month_first_indexes(data)
    rows = []
    for i in m:
        r, d_buy, d_sell = ret_series(data, i)
        if r is not None:
            rows.append((d_buy, r))
    s = sorted(r for _, r in rows)
    win = sum(1 for _, r in rows if r > 0)/len(rows)*100
    print(f"{idx['short']:<10}{len(rows):>6}{win:>8.1f}%{pct(s,.5)*100:>7.1f}%{pct(s,.25)*100:>7.1f}%{pct(s,.75)*100:>7.1f}%{s[0]*100:>7.1f}%{s[-1]*100:>7.1f}%")

print("\n=== 仅最近10年 (2016-08 起买入, 与定投页同口径) ===")
print(f"{'指数':<10}{'次数':>6}{'盈利概率':>9}{'中位':>8}{'P25':>8}{'P75':>8}{'最差':>8}{'最好':>8}")
for idx in INDICES:
    data = load(idx["code"])
    m = month_first_indexes(data)
    rows = []
    for i in m:
        if data[i]["date"] < "2016-08-01": continue
        r, d_buy, d_sell = ret_series(data, i)
        if r is not None:
            rows.append((d_buy, r))
    s = sorted(r for _, r in rows)
    win = sum(1 for _, r in rows if r > 0)/len(rows)*100
    print(f"{idx['short']:<10}{len(rows):>6}{win:>8.1f}%{pct(s,.5)*100:>7.1f}%{pct(s,.25)*100:>7.1f}%{pct(s,.75)*100:>7.1f}%{s[0]*100:>7.1f}%{s[-1]*100:>7.1f}%")

print("\n=== 各指数按采购年份统计盈利概率(最近10年) ===")
for idx in INDICES:
    data = load(idx["code"])
    m = month_first_indexes(data)
    by_year = {}
    for i in m:
        if data[i]["date"] < "2016-08-01": continue
        r, d_buy, d_sell = ret_series(data, i)
        if r is None: continue
        by_year.setdefault(d_buy[:4], []).append(r)
    line = f"{idx['short']}: "
    for y in sorted(by_year):
        r = by_year[y]
        w = sum(1 for x in r if x > 0)/len(r)*100
        line += f"{y}年{w:.0f}% "
    print(line)