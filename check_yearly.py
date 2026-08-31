# -*- coding: utf-8 -*-
import json
r = json.load(open("result_yearly.json"))
for idx in r["indices"]:
    cagr = idx["cagr"] * 100 if idx["cagr"] else 0
    fv = idx["final_value"]
    print(f"{idx['code']}: cagr={cagr:.2f}% final={fv:,.0f}")
    print(f"  plot dates: {idx['plot']['dates'][0]} ... {idx['plot']['dates'][-1]}")
    mdd = idx.get("mdd_port", {})
    if isinstance(mdd, dict) and "pct" in mdd:
        print(f"  mdd_port: {mdd['pct']*100:.2f}%")