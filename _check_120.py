# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
h = open("dividend_dashboard.html", encoding="utf-8").read()
keys = [
    "2016.08 - 2026.07",
    "共 120 期",
    "总投入 ¥1,200,000（120 期）",
    "2016-08 首期至 2026-07 末期",
    "累计投入 ¥1,200,000",
    "2016-08-01",
    "逐日复算 2016-08 至 2026-07",
]
for k in keys:
    print(("OK  " if k in h else "MISS"), k)
