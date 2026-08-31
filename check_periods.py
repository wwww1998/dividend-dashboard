import json
for y in [5, 3]:
    hl = json.load(open(f"high_low_{y}y.json"))
    result = json.load(open(f"result_{y}y.json"))
    meta = hl["meta"]
    print(f"=== {y}年 ===")
    print(f"  meta: {meta}")
    print(f"  日期范围: {hl['indices'][0]['high']['plot']['dates'][0]} ~ {hl['indices'][0]['high']['plot']['dates'][-1]}")
    print(f"  result 日期范围: {result['indices'][0]['plot']['dates'][0]} ~ {result['indices'][0]['plot']['dates'][-1]}")
    print()