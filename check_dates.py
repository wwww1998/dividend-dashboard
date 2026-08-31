import json
for y in [5, 3]:
    hl = json.load(open(f"high_low_{y}y.json"))
    result = json.load(open(f"result_{y}y.json"))
    
    hl_dates = hl["indices"][0]["high"]["plot"]["dates"]
    r_dates = result["indices"][0]["plot"]["dates"]
    
    print(f"=== {y}年 ===")
    print(f"  high_low dates: {hl_dates[0]} ~ {hl_dates[-1]}  ({len(hl_dates)} 个)")
    print(f"  result dates:   {r_dates[0]} ~ {r_dates[-1]}  ({len(r_dates)} 个)")
    print(f"  日期匹配: {hl_dates == r_dates}")
    
    # 如果日期不匹配，检查是否有重叠
    common = set(hl_dates) & set(r_dates)
    print(f"  共同日期数: {len(common)}")
    print(f"  result多出的日期: {set(r_dates) - set(hl_dates)}")
    print(f"  hl多出的日期: {set(hl_dates) - set(r_dates)}")
    print()