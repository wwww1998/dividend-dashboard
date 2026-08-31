# -*- coding: utf-8 -*-
"""
四大红利全收益指数 · 每月最高价 vs 最低价 曲线对比
加入每月首个交易日定投曲线作为中间参考
分别为 10年/5年/3年 生成独立页面
"""
import json

YEARS = [(10, {"label": "10年", "periods": "120期", "invest": "¥120万", "start": "2016.08", "end": "2026.07", "result_fn": "result.json"}),
         (5,  {"label": "5年",  "periods": "60期",  "invest": "¥60万",  "start": "2021.08", "end": "2026.07", "result_fn": "result_5y.json"}),
         (3,  {"label": "3年",  "periods": "36期",  "invest": "¥36万",  "start": "2023.08", "end": "2026.07", "result_fn": "result_3y.json"}),
         (1,  {"label": "1年",  "periods": "12期",  "invest": "¥12万",  "start": "2025.08", "end": "2026.07", "result_fn": "result_1y.json"})]

COLORS = {"H00015": "#27ae60", "H00922": "#3498db", "H20269": "#e74c3c", "H20955": "#e67e22"}
SHORT = {"H00015": "上证红利", "H00922": "中证红利", "H20269": "红利低波", "H20955": "红利低波100"}
CODES = ["H00015", "H00922", "H20269", "H20955"]

FIRSTDAY_CAGR = {"H00015": {}, "H00922": {}, "H20269": {}, "H20955": {}}

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

for y, meta in YEARS:
    fn = f"high_low_{y}y.json"
    data = json.load(open(fn, encoding="utf-8"))
    result = json.load(open(meta["result_fn"], encoding="utf-8"))
    
    chart_data = {}
    for c in CODES:
        idx = [i for i in data["indices"] if i["code"] == c][0]
        h = idx["high"]
        l = idx["low"]
        h_cagr = h["cagr"] if h["cagr"] else 0
        l_cagr = l["cagr"] if l["cagr"] else 0
        
        # 从result.json获取首日定投数据
        r_idx = [i for i in result["indices"] if i["code"] == c][0]
        fd_cagr = r_idx["cagr"] if r_idx["cagr"] else 0
        fd_final = r_idx["final_value"]
        fd_plot = r_idx["plot"]
        fd_mdd = r_idx.get("mdd_port", {})
        fd_mdd_pct = fd_mdd.get("pct", 0) if isinstance(fd_mdd, dict) else 0
        
        chart_data[c] = {
            "code": c, "short": SHORT[c], "color": COLORS[c],
            "dates": h["plot"]["dates"],
            "high_value": h["plot"]["value"],
            "low_value": l["plot"]["value"],
            "firstday_value": fd_plot["value"],
            "invested": h["plot"]["invested"],
            "high_cagr": f"{h_cagr*100:.2f}%",
            "low_cagr": f"{l_cagr*100:.2f}%",
            "firstday_cagr": f"{fd_cagr*100:.2f}%",
            "high_final": round(h["final_value"]),
            "low_final": round(l["final_value"]),
            "firstday_final": round(fd_final),
            "high_drawdown": f"{h['mdd_port']['pct']*100:.2f}%",
            "low_drawdown": f"{l['mdd_port']['pct']*100:.2f}%",
            "firstday_drawdown": f"{fd_mdd_pct*100:.2f}%",
        }

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利 · {meta['label']}每月最高价vs最低价定投</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<script>window.echarts||document.write('<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.5.0/echarts.min.js"><\\/script>');</script>
<style>
:root{{--bg:#f4f6fa;--card:#ffffff;--ink:#1a2332;--sub:#6b7686;--line:#e6eaf0}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}}
.wrap{{max-width:1120px;margin:0 auto;padding:32px 20px 80px}}
.hero{{background:linear-gradient(135deg,#2b3a4a 0%,#1d2939 60%,#3a2a2a 100%);border-radius:18px;color:#fff;padding:38px 40px;position:relative;overflow:hidden}}
.hero::after{{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent 70%)}}
.hero h1{{font-size:28px;font-weight:800;margin-bottom:10px}}
.hero h1 em{{font-style:normal;color:#ffb37a}}
.hero .sub{{font-size:14px;color:#c7d2de;max-width:760px;margin-bottom:14px}}
.hero .rules{{display:flex;flex-wrap:wrap;gap:10px}}
.hero .rule{{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:6px 13px;font-size:12.5px;color:#e8eef6}}
.hero .rule b{{color:#ffd28a}}
.sec{{margin-top:32px}}
.sec h2{{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px;margin-bottom:6px}}
.sec .desc{{color:var(--sub);font-size:13.5px;margin-bottom:16px}}
.chart{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px 10px;box-shadow:0 1px 3px rgba(20,30,50,.05)}}
.chart .head{{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:0 6px 8px}}
.chart .head .t{{font-size:15px;font-weight:700}}
.chart .head .hint{{font-size:12px;color:var(--sub)}}
.cards{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
@media(max-width:760px){{.cards{{grid-template-columns:1fr}}}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;padding:4px 8px 6px;font-size:12px;color:var(--sub)}}
.legend .li{{display:flex;align-items:center;gap:5px}}
.legend .sw{{width:16px;height:0;border-top:3px solid}}
.legend .sw.dash{{border-top-style:dashed}}
.legend .sw.solid{{border-top-style:solid}}
.foot{{margin-top:40px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 24px;font-size:12.5px;color:var(--sub)}}
.foot h3{{color:var(--ink);font-size:14px;margin-bottom:8px}}
.foot p{{margin-bottom:6px}}
.foot .warn{{color:#c0392b;font-weight:600}}
.cta{{margin-top:16px;background:linear-gradient(135deg,#fdf3f2 0%,#fbe9e7 100%);border:1px solid #f3d9d5;border-radius:14px;padding:20px 26px;text-align:center}}
.cta p{{font-size:15px;font-weight:700;color:#8c2f28;line-height:1.8}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
td.num{{padding:9px 14px}}
th.num{{padding:9px 14px}}
@media(max-width:720px){{.hero h1{{font-size:23px}}.hero{{padding:28px 22px}}}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <h1>四大红利·{meta['label']}每月最高价 vs 最低价<br><em>每个指数单独对比 · 含首日定投曲线 · 真实回撤</em></h1>
  <div class="sub">每月定投固定金额，分别在当月最高价买入、最低价买入、以及每月首个交易日买入，对比终值、年化收益和回撤差异。</div>
  <div class="rules">
    <div class="rule">周期 <b>{meta['start']} - {meta['end']}</b></div>
    <div class="rule">{meta['periods']} · 每期 ¥10,000</div>
    <div class="rule">总投入 <b>{meta['invest']}</b></div>
    <div class="rule">口径 <b>全收益指数</b></div>
  </div>
</div>

<div class="sec">
  <h2>各指数 · 最高价 vs 最低价 vs 首日定投对比</h2>
  <div class="desc">每个指数展示三条曲线：<b style="color:#e74c3c">红色</b> = 最高价买入（最差择时），<b style="color:#f39c12">黄色</b> = 首日定投（实际策略），<b style="color:#3498db">蓝色</b> = 最低价买入（理想择时）。<b style="color:#9aa7b8">灰色虚线</b> = 累计投入本金。</div>
  <div class="cards" id="chartCards"></div>
</div>

<div class="sec">
  <h2>关键数据对比</h2>
  <div class="desc">最高价买入 vs 首日定投 vs 最低价买入的年化收益、终值、回撤全对比。</div>
  <div class="chart">
    <div class="head"><div class="t">年化收益对比表</div></div>
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13px;min-width:820px" id="dataTable"></table>
    </div>
  </div>
</div>

<div class="sec">
  <h2>总结：{meta['label']}维度，择时影响</h2>
  <div class="desc">{meta['label']}期间，三种策略的年化收益和终值差异。</div>
  <div class="cards" id="summaryCards" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))"></div>
</div>

<div class="cta">
  <p>以上内容仅供学习参考，不构成投资建议。投资有风险，入市需谨慎。</p>
</div>

<div class="foot">
  <h3>口径与方法说明</h3>
  <p>1. <b>数据源</b>：中证指数官网（csindex.com.cn）官方日线行情，全收益指数（含分红再投资）。</p>
  <p>2. <b>定投规则</b>：每月固定投入10,000元，分别在当月最高价买入、当月最低价买入、每月首个交易日买入；未计交易费用与税费。</p>
  <p>3. <b>年化收益率</b>：按逐笔现金流 XIRR（资金时间价值口径）计算。</p>
  <p>4. <b>组合市值回撤</b>：每日账户市值从历史峰值回落的最大幅度。</p>
  <p class="warn">⚠ 本页为历史数据回撤，不代表未来收益。投资有风险，决策需谨慎。</p>
</div>

</div>

<script>
const DATA = {jdump(chart_data)};
const CODES = {jdump(CODES)};
const fonts = {{color: "#6b7686", fontFamily: "inherit"}};

/* ---------- 4张对比图 ---------- */
(function(){{
  const box = document.getElementById("chartCards");
  CODES.forEach(c => {{
    const d = DATA[c];
    const card = document.createElement("div");
    card.className = "chart";
    card.innerHTML = `<div class="head"><div class="t"><span style="color:${{d.color}}">●</span> ${{d.short}}</div><div class="hint">红=最高价 黄=首日 蓝=最低价</div></div><div id="ch_${{c}}" style="width:100%;height:380px"></div><div class="legend" style="justify-content:center"><div class="li"><span class="sw solid" style="border-color:#e74c3c"></span>最高价 ${{d.high_cagr}}</div><div class="li"><span class="sw solid" style="border-color:#f39c12"></span>首日定投 ${{d.firstday_cagr}}</div><div class="li"><span class="sw solid" style="border-color:#3498db"></span>最低价 ${{d.low_cagr}}</div><div class="li"><span class="sw dash" style="border-color:#9aa7b8"></span>累计投入</div></div>`;
    box.appendChild(card);

    const chart = echarts.init(document.getElementById("ch_"+c));
    const option = {{
      tooltip: {{
        trigger: "axis",
        backgroundColor: "rgba(29,41,57,.92)",
        borderWidth: 0,
        textStyle: {{color: "#fff", fontSize: 12}},
        valueFormatter: v => v == null ? "-" : "¥" + Math.round(v).toLocaleString()
      }},
      legend: {{data: ["最高价买入","首日定投","最低价买入","累计投入"], top: 0, textStyle: {{...fonts, fontSize: 11}}, icon: "roundRect", itemWidth: 14, itemHeight: 6}},
      xAxis: {{type: "category", data: d.dates, axisLine: {{lineStyle: {{color: "#ccd4de"}}}}, axisLabel: {{color: "#6b7686", fontSize: 10}}, axisTick: {{show: false}}}},
      yAxis: {{type: "value", axisLabel: {{formatter: v => v >= 10000 ? (v/10000).toFixed(0)+"万" : v, color: "#6b7686", fontSize: 10}}, splitLine: {{lineStyle: {{color: "#eef2f7"}}}}}},
      series: [
        {{name: "最高价买入", type: "line", data: d.high_value, smooth: false, symbol: "none", lineStyle: {{width: 1.8, color: "#e74c3c"}}, itemStyle: {{color: "#e74c3c"}}}},
        {{name: "首日定投", type: "line", data: d.firstday_value, smooth: false, symbol: "none", lineStyle: {{width: 2.2, color: "#f39c12"}}, itemStyle: {{color: "#f39c12"}}}},
        {{name: "最低价买入", type: "line", data: d.low_value, smooth: false, symbol: "none", lineStyle: {{width: 1.8, color: "#3498db"}}, itemStyle: {{color: "#3498db"}}}},
        {{name: "累计投入", type: "line", data: d.invested, smooth: false, symbol: "none", lineStyle: {{width: 1.3, type: "dashed", color: "#9aa7b8"}}, itemStyle: {{color: "#9aa7b8", opacity: .5}}}}
      ],
      grid: {{top: 36, bottom: 20, left: 50, right: 16}}
    }};
    chart.setOption(option);
    window.addEventListener("resize", () => chart.resize());
  }});
}})();

/* ---------- 数据表 ---------- */
(function(){{
  const tbl = document.getElementById("dataTable");
  let html = '<thead><tr><th>指数</th><th>最高价年化</th><th>首日年化</th><th>最低价年化</th><th>最高价终值</th><th>首日终值</th><th>最低价终值</th><th>最高价回撤</th><th>首日回撤</th><th>最低价回撤</th></tr></thead><tbody>';
  CODES.forEach(c => {{
    const d = DATA[c];
    const h_l_gap = (parseFloat(d.low_cagr) - parseFloat(d.high_cagr)).toFixed(2);
    const fd_gap_high = (parseFloat(d.firstday_cagr) - parseFloat(d.high_cagr)).toFixed(2);
    const fd_gap_low = (parseFloat(d.low_cagr) - parseFloat(d.firstday_cagr)).toFixed(2);
    html += `<tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${{d.color}}"></span> <b>${{d.short}}</b></td><td class="num">${{d.high_cagr}}</td><td class="num" style="font-weight:700;color:#d68910">${{d.firstday_cagr}}</td><td class="num" style="font-weight:700;color:#2980b9">${{d.low_cagr}}</td><td class="num">¥${{d.high_final.toLocaleString()}}</td><td class="num" style="font-weight:700">¥${{d.firstday_final.toLocaleString()}}</td><td class="num" style="font-weight:700">¥${{d.low_final.toLocaleString()}}</td><td class="num">${{d.high_drawdown}}</td><td class="num">${{d.firstday_drawdown}}</td><td class="num">${{d.low_drawdown}}</td></tr>`;
  }});
  html += '</tbody>';
  tbl.innerHTML = html;
}})();

/* ---------- 总结卡片 ---------- */
(function(){{
  const box = document.getElementById("summaryCards");
  CODES.forEach(c => {{
    const d = DATA[c];
    const h_l_gap = (parseFloat(d.low_cagr) - parseFloat(d.high_cagr)).toFixed(2);
    const fd_gap_high = (parseFloat(d.firstday_cagr) - parseFloat(d.high_cagr)).toFixed(2);
    const pct_of_max = ((parseFloat(d.firstday_cagr) - parseFloat(d.high_cagr)) / (parseFloat(d.low_cagr) - parseFloat(d.high_cagr)) * 100).toFixed(1);
    const el = document.createElement("div");
    el.className = "chart";
    el.style.padding = "14px 16px";
    el.innerHTML = `
      <div style="font-weight:700;font-size:15px;margin-bottom:8px"><span style="color:${{d.color}}">●</span> ${{d.short}}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px">
        <div><div style="color:var(--sub);font-size:11px">最高价年化</div><div style="font-weight:700;color:#c0392b">${{d.high_cagr}}</div></div>
        <div><div style="color:var(--sub);font-size:11px">首日年化</div><div style="font-weight:700;color:#d68910">${{d.firstday_cagr}}</div></div>
        <div><div style="color:var(--sub);font-size:11px">最低价年化</div><div style="font-weight:700;color:#2980b9">${{d.low_cagr}}</div></div>
        <div><div style="color:var(--sub);font-size:11px">首日 vs 最高价</div><div style="font-weight:700;color:#27ae60">+${{fd_gap_high}}%</div></div>
        <div><div style="color:var(--sub);font-size:11px">最低价 vs 首日</div><div style="font-weight:700;color:#2980b9">+${{(parseFloat(d.low_cagr)-parseFloat(d.firstday_cagr)).toFixed(2)}}%</div></div>
        <div><div style="color:var(--sub);font-size:11px">首日占超额%</div><div style="font-weight:700">${{pct_of_max}}%</div></div>
        <div><div style="color:var(--sub);font-size:11px">终值：最高价</div><div style="font-weight:700">¥${{d.high_final.toLocaleString()}}</div></div>
        <div><div style="color:var(--sub);font-size:11px">终值：首日</div><div style="font-weight:700;color:#d68910">¥${{d.firstday_final.toLocaleString()}}</div></div>
        <div><div style="color:var(--sub);font-size:11px">终值：最低价</div><div style="font-weight:700;color:#2980b9">¥${{d.low_final.toLocaleString()}}</div></div>
      </div>
    `;
    box.appendChild(el);
  }});
}})();
</script>
</body>
</html>"""

    outname = f"dividend_high_low_detail_{y}y.html"
    with open(outname, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"已生成 {outname}")