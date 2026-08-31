import json
for y in [5, 3, 1]:
    hl = json.load(open(f"high_low_{y}y.json"))
    result = json.load(open(f"result_{y}y.json"))
    
    hl_dates = hl["indices"][0]["high"]["plot"]["dates"]
    r_dates = result["indices"][0]["plot"]["dates"]
    
    print(f"=== 每月定投 {y}年 ===")
    print(f"  high_low: {hl_dates[0]} ~ {hl_dates[-1]}  ({len(hl_dates)} 天, {hl['meta']['periods']}期 ¥{hl['meta']['total_invest']:,.0f})")
    print(f"  result:   {r_dates[0]} ~ {r_dates[-1]}  ({len(r_dates)} 天, {result['meta']['periods']}期 ¥{result['meta']['total_invest']:,.0f})")
    ok = hl_dates == r_dates
    print(f"  日期完全匹配: {ok}")
    if not ok:
        common = set(hl_dates) & set(r_dates)
        print(f"  共同日期: {len(common)}/{len(hl_dates)}")
    print()

for y in [10, 5, 3, 1]:
    hl = json.load(open(f"high_low_yearly_{y}y.json"))
    result = json.load(open(f"result_yearly_{y}y.json" if y != 10 else "result_yearly.json"))
    
    hl_dates = hl["indices"][0]["high"]["plot"]["dates"]
    r_dates = result["indices"][0]["plot"]["dates"]
    
    print(f"=== 每年定投 {y}年 ===")
    print(f"  high_low: {hl_dates[0]} ~ {hl_dates[-1]}  ({len(hl_dates)} 天, {hl['meta']['periods']}期 ¥{hl['meta']['total_invest']:,.0f})")
    print(f"  result:   {r_dates[0]} ~ {r_dates[-1]}  ({len(r_dates)} 天, {result['meta']['periods']}期 ¥{result['meta']['total_invest']:,.0f})")
    ok = hl_dates == r_dates
    print(f"  日期完全匹配: {ok}")
    if not ok:
        common = set(hl_dates) & set(r_dates)
        print(f"  共同日期: {len(common)}/{len(hl_dates)}")
    print()