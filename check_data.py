import json
hl = json.load(open("high_low_yearly_10y.json"))
r = json.load(open("result_yearly.json"))
print("high_low meta:", hl["meta"])
print()
print("result_yearly indices:")
for idx in r["indices"]:
    print(f"  {idx['code']}: final={idx['final_value']:,.0f} invest={idx['total_invest']:,.0f}")
print()
print("high_low indices:")
for idx in hl["indices"]:
    print(f"  {idx['code']}: high_final={idx['high']['final_value']:,.0f} low_final={idx['low']['final_value']:,.0f}")