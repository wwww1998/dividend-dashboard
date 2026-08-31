# -*- coding: utf-8 -*-
import json
hl = json.load(open("high_low_yearly_10y.json"))
r = json.load(open("result_yearly.json"))
# 比较第一个指数的日期范围
idx_hl = hl["indices"][0]
idx_r = r["indices"][0]
print("high_low dates:", idx_hl["high"]["plot"]["dates"][0], "...", idx_hl["high"]["plot"]["dates"][-1])
print("high_low count:", len(idx_hl["high"]["plot"]["dates"]))
print("result dates:", idx_r["plot"]["dates"][0], "...", idx_r["plot"]["dates"][-1])
print("result count:", len(idx_r["plot"]["dates"]))
print("dates match:", idx_hl["high"]["plot"]["dates"] == idx_r["plot"]["dates"])