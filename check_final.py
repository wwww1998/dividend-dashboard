import json
hl = json.load(open("high_low_yearly_1y.json"))
result = json.load(open("result_yearly_1y.json"))
hl_dates = hl["indices"][0]["high"]["plot"]["dates"]
r_dates = result["indices"][0]["plot"]["dates"]
print(f"high_low: {hl_dates[0]} ~ {hl_dates[-1]}  ({len(hl_dates)} 天, {hl['meta']['periods']}期 ¥{hl['meta']['total_invest']:,.0f})")
print(f"result:   {r_dates[0]} ~ {r_dates[-1]}  ({len(r_dates)} 天, {result['meta']['periods']}期 ¥{result['meta']['total_invest']:,.0f})")
print(f"日期完全匹配: {hl_dates == r_dates}")

# 重新运行完整核验
import subprocess
subprocess.run(["python", "verify_data.py"])