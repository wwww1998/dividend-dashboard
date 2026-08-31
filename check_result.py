# -*- coding: utf-8 -*-
"""检查result.json中的首日定投数据"""
import json
r = json.load(open("result.json"))
for idx in r["indices"]:
    cagr = idx["cagr"] * 100
    fv = idx["final_value"]
    ti = idx["total_invest"]
    print(f"{idx['short']:<8} cagr={cagr:.2f}%  final={fv:,.0f}  invest={ti:,.0f}  profit={fv-ti:,.0f}")

print()
print("=== 对比 high_low_10y.json ===")
hl = json.load(open("high_low_10y.json"))
for ih in hl["indices"]:
    hc = ih["high"]["cagr"] * 100
    lc = ih["low"]["cagr"] * 100
    hf = ih["high"]["final_value"]
    lf = ih["low"]["final_value"]
    # result.json中对应
    idx = [i for i in r["indices"] if i["code"] == ih["code"]][0]
    dc = idx["cagr"] * 100
    df = idx["final_value"]
    print(f"{ih['short']:<8} 首日={dc:.2f}%  最高价={hc:.2f}%  最低价={lc:.2f}%  |  首日终值={df:,.0f}  最高价终值={hf:,.0f}  最低价终值={lf:,.0f}")
    print(f"  {'首日>最高价' if dc > hc else '首日<最高价'}  {'首日<最低价' if dc < lc else '首日>最低价'}")