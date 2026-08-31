# -*- coding: utf-8 -*-
"""
数据核验脚本
1. 验证每月定投 10年数据一致性
2. 验证每年定投 10年数据一致性
3. 验证首日定投数据是否合理落在最高vs最低之间
"""
import json

def check_monthly_data():
    print("=" * 70)
    print("1. 每月定投 10年 数据核验")
    print("=" * 70)
    
    hl = json.load(open("high_low_10y.json"))
    result = json.load(open("result.json"))
    
    for idx in hl["indices"]:
        code = idx["code"]
        h = idx["high"]
        l = idx["low"]
        
        # 获取首日数据
        r_idx = [i for i in result["indices"] if i["code"] == code][0]
        
        print(f"\n--- {code} ---")
        print(f"  总投入: {h['total_invest']:>10,.0f} 元, {h['periods']} 期 × 10,000")
        print(f"  dates: {h['plot']['dates'][0]} ~ {h['plot']['dates'][-1]} ({len(h['plot']['dates'])} 天)")
        
        # 验证最高价终值 > 首日终值 > 最低价终值
        hv = h["final_value"]
        fv = r_idx["final_value"]
        lv = l["final_value"]
        print(f"  终值: 最高价={hv:>10,.0f}  首日={fv:>10,.0f}  最低价={lv:>10,.0f}")
        if hv < fv < lv:
            print(f"  ✅ 顺序正确: 最高价({hv:,.0f}) < 首日({fv:,.0f}) < 最低价({lv:,.0f})")
        else:
            print(f"  ❌ 顺序异常!")
        
        # 验证年化收益率
        hc = h["cagr"] * 100
        fc = r_idx["cagr"] * 100
        lc = l["cagr"] * 100
        print(f"  年化: 最高价={hc:.2f}%  首日={fc:.2f}%  最低价={lc:.2f}%")
        if hc < fc < lc:
            print(f"  ✅ 年化顺序正确: {hc:.2f}% < {fc:.2f}% < {lc:.2f}%")
        else:
            print(f"  ❌ 年化顺序异常!")
        
        # 验证回撤
        hm = h["mdd_port"]["pct"] * 100
        r_mdd = r_idx.get("mdd_port", {})
        rm = r_mdd.get("pct", 0) * 100 if isinstance(r_mdd, dict) else 0
        lm = l["mdd_port"]["pct"] * 100
        # 回撤通常是负值，所以回撤最大值（最接近0）通常是最低价的
        print(f"  回撤: 最高价={hm:.2f}%  首日={rm:.2f}%  最低价={lm:.2f}%")
        
        # 验证plot数据长度
        print(f"  plot数据点数: 最高价={len(h['plot']['value'])}  首日={len(r_idx['plot']['value'])}  最低价={len(l['plot']['value'])}")


def check_yearly_data():
    print("\n" + "=" * 70)
    print("2. 每年定投 10年 数据核验")
    print("=" * 70)
    
    hl = json.load(open("high_low_yearly_10y.json"))
    result = json.load(open("result_yearly.json"))
    
    for idx in hl["indices"]:
        code = idx["code"]
        h = idx["high"]
        l = idx["low"]
        
        r_idx = [i for i in result["indices"] if i["code"] == code][0]
        
        print(f"\n--- {code} ---")
        print(f"  总投入(high_low): {h['total_invest']:>10,.0f} 元, {h['periods']} 期")
        print(f"  总投入(result):   {r_idx['total_invest']:>10,.0f} 元")
        print(f"  dates: {h['plot']['dates'][0]} ~ {h['plot']['dates'][-1]} ({len(h['plot']['dates'])} 天)")
        
        # 验证终值顺序
        hv = h["final_value"]
        fv = r_idx["final_value"]
        lv = l["final_value"]
        
        # 计算缩放因子
        scale = h["total_invest"] / r_idx["total_invest"] if r_idx["total_invest"] > 0 else 1
        fv_scaled = fv * scale
        
        print(f"  终值: 最高价={hv:>12,.0f}  首日(缩放后)={fv_scaled:>12,.0f}  最低价={lv:>12,.0f}")
        print(f"  首日原始终值={fv:>10,.0f}  缩放因子={scale:.2f}")
        if hv < fv_scaled < lv:
            print(f"  ✅ 终值顺序正确")
        else:
            print(f"  ❌ 终值顺序异常!")
        
        # 验证年化
        hc = h["cagr"] * 100
        fc = r_idx["cagr"] * 100
        lc = l["cagr"] * 100
        print(f"  年化: 最高价={hc:.2f}%  首日={fc:.2f}%  最低价={lc:.2f}%")
        if hc < fc < lc:
            print(f"  ✅ 年化顺序正确")
        else:
            print(f"  ❌ 年化顺序异常!")


def check_consistency():
    """检查不同时间维度的数据一致性"""
    print("\n" + "=" * 70)
    print("3. 跨时间维度一致性核验")
    print("=" * 70)
    
    for y in [10, 5, 3, 1]:
        hl = json.load(open(f"high_low_{y}y.json"))
        result = json.load(open(f"result_{y}y.json" if y != 10 else "result.json"))
        
        print(f"\n--- {y}年 每月定投 ---")
        for idx in hl["indices"]:
            code = idx["code"]
            h = idx["high"]
            l = idx["low"]
            r_idx = [i for i in result["indices"] if i["code"] == code][0]
            
            # 预期的期数: 10年=120, 5年=60, 3年=36, 1年=12
            expected_periods = {10: 120, 5: 60, 3: 36, 1: 12}
            expected_invest = expected_periods[y] * 10000
            
            # 日期范围
            start = h["plot"]["dates"][0]
            end = h["plot"]["dates"][-1]
            
            ok = True
            issues = []
            
            if h["periods"] != expected_periods[y]:
                ok = False
                issues.append(f"期数错误: {h['periods']} != {expected_periods[y]}")
            if h["total_invest"] != expected_invest:
                ok = False
                issues.append(f"总投资错误: {h['total_invest']} != {expected_invest}")
            
            # 验证年化顺序
            hc = h["cagr"] * 100 if h["cagr"] else 0
            fc = r_idx["cagr"] * 100 if r_idx["cagr"] else 0
            lc = l["cagr"] * 100 if l["cagr"] else 0
            
            if not (hc < fc < lc):
                ok = False
                issues.append(f"年化顺序异常: {hc:.2f}% < {fc:.2f}% < {lc:.2f}%")
            
            status = "✅" if ok else "❌"
            print(f"  {status} {code}: {start} ~ {end}  {h['periods']}期 ¥{h['total_invest']:,.0f}  | 年化 {hc:.2f}% < {fc:.2f}% < {lc:.2f}%")
            if issues:
                for iss in issues:
                    print(f"       {iss}")


def check_yearly_consistency():
    print("\n" + "=" * 70)
    print("4. 每年定投 跨时间维度一致性核验")
    print("=" * 70)
    
    for y in [10, 5, 3, 1]:
        hl = json.load(open(f"high_low_yearly_{y}y.json"))
        result = json.load(open(f"result_yearly_{y}y.json" if y != 10 else "result_yearly.json"))
        
        print(f"\n--- {y}年 每年定投 ---")
        for idx in hl["indices"]:
            code = idx["code"]
            h = idx["high"]
            l = idx["low"]
            r_idx = [i for i in result["indices"] if i["code"] == code][0]
            
            start = h["plot"]["dates"][0]
            end = h["plot"]["dates"][-1]
            
            hc = h["cagr"] * 100 if h["cagr"] else 0
            fc = r_idx["cagr"] * 100 if r_idx["cagr"] else 0
            lc = l["cagr"] * 100 if l["cagr"] else 0
            
            ok = hc < fc < lc
            status = "✅" if ok else "❌"
            print(f"  {status} {code}: {h['periods']}期 ¥{h['total_invest']:>10,.0f}  | 年化 {hc:.2f}% < {fc:.2f}% < {lc:.2f}%")
            
            if not ok:
                # 检查缩放是否有问题
                scale = h["total_invest"] / r_idx["total_invest"] if r_idx["total_invest"] > 0 else 1
                hv = h["final_value"]
                fv = r_idx["final_value"] * scale
                lv = l["final_value"]
                print(f"       终值: 最高价={hv:,.0f} 首日缩放={fv:,.0f} 最低价={lv:,.0f}")
                print(f"       缩放因子={scale:.2f}")


if __name__ == "__main__":
    check_monthly_data()
    check_yearly_data()
    check_consistency()
    check_yearly_consistency()