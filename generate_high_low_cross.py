# -*- coding: utf-8 -*-
"""
四大红利全收益指数 · 跨时间维度对比（10年/5年/3年）
每月最高价 vs 最低价定投，在同一张图上展示
"""
import json

# 加载三个时间维度的数据
data = {}
for y in [10, 5, 3]:
    fn = f"high_low_{y}y.json"
    r = json.load(open(fn, encoding="utf-8"))
    data[y] = r

COLORS = {"H00015": "#27ae60", "H00922": "#3498db", "H20269": "#e74c3c", "H20955": "#e67e22"}
SHORT = {"H00015": "上证红利", "H00922": "中证红利", "H20269": "红利低波", "H20955": "红利低波100"}
CODES = ["H00015", "H00922", "H20269", "H20955"]

YEARS_META = {10: {"label": "10年", "periods": "120期", "invest": "¥120万", "start": "2016.08"},
              5: {"label": "5年", "periods": "60期", "invest": "¥60万", "start": "2021.08"},
              3: {"label": "3年", "periods": "36期", "invest": "¥36万", "start": "2023.08"}}

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

# 构建绘图数据
chart_data = {}
for c in CODES:
    chart_data[c] = {"series": []}
    for y in [10, 5, 3]:
        idx = [i for i in data[y]["indices"] if i["code"] == c][0]
        h = idx["high"]
        l = idx["low"]
        # 归一化到100
        base_h = h["plot"]["value"][0]
        base_l = l["plot"]["value"][0]
        years_label = YEARS_META[y]["label"]
        chart_data[c]["series"].append({
            "name": f"{years_label}最高价",
            "type": "line",
            "data": [round(v / base_h * 100, 1) for v in h["plot"]["value"]],
            "lineStyle": {"width": 1.6, "type": "solid"},
            "color": COLORS[c],
            "opacity": 0.8
        })
        chart_data[c]["series"].append({
            "name": f"{years_label}最低价",
            "type": "line",
            "data": [round(v / base_l * 100, 1) for v in l["plot"]["value"]],
            "lineStyle": {"width": 1.6, "type": "dashed"},
            "color": COLORS[c],
            "opacity": 0.8
        })

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利 · 跨时间维度高低价对比</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<script>window.echarts||document.write('<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.5.0/echarts.min.js"><\\/script>');</script>
<style>
:root{--bg:#f4f6fa;--card:#ffffff;--ink:#1a2332;--sub:#6b7686;--line:#e6eaf0}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.wrap{max-width:1120px;margin:0 auto;padding:32px 20px 80px}
.hero{background:linear-gradient(135deg,#2b3a4a 0%,#1d2939 60%,#3a2a2a 100%);border-radius:18px;color:#fff;padding:38px 40px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent 70%)}
.hero h1{font-size:28px;font-weight:800;margin-bottom:10px}
.hero h1 em{font-style:normal;color:#ffb37a}
.hero .sub{font-size:14px;color:#c7d2de;max-width:760px;margin-bottom:14px}
.hero .rules{display:flex;flex-wrap:wrap;gap:10px}
.hero .rule{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:6px 13px;font-size:12.5px;color:#e8eef6}
.hero .rule b{color:#ffd28a}
.sec{margin-top:32px}
.sec h2{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sec .desc{color:var(--sub);font-size:13.5px;margin-bottom:16px}
.chart{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px 10px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.chart .head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:0 6px 8px}
.chart .head .t{font-size:15px;font-weight:700}
.chart .head .hint{font-size:12px;color:var(--sub)}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.cards{grid-template-columns:1fr}}
.legend{display:flex;flex-wrap:wrap;gap:10px;padding:4px 8px 6px;font-size:12px;color:var(--sub)}
.legend .li{display:flex;align-items:center;gap:5px}
.legend .sw{width:16px;height:0;border-top:3px solid}
.legend .sw.dash{border-top-style:dashed}
.legend .sw.solid{border-top-style:solid}
.foot{margin-top:40px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 24px;font-size:12.5px;color:var(--sub)}
.foot h3{color:var(--ink);font-size:14px;margin-bottom:8px}
.foot p{margin-bottom:6px}
.foot .warn{color:#c0392b;font-weight:600}
.cta{margin-top:16px;background:linear-gradient(135deg,#fdf3f2 0%,#fbe9e7 100%);border:1px solid #f3d9d5;border-radius:14px;padding:20px 26px;text-align:center}
.cta p{font-size:15px;font-weight:700;color:#8c2f28;line-height:1.8}
.num{text-align:right;font-variant-numeric:tabular-nums}
td.num{padding:9px 14px}
th.num{padding:9px 14px}
@media(max-width:720px){.hero h1{font-size:23px}.hero{padding:28px 22px}}
</style>
</head>
<body>
<div class="wrap">

<div class="hero">
  <h1>四大红利·跨时间维度对比<br><em>每月最高价 vs 最低价 · 10年/5年/3年同图归一化</em></h1>
  <div class="sub">每张图内，每个时间维度分别用实线（最高价买入）和虚线（最低价买入）表示，颜色按指数区分。所有曲线从起点归一化为100，观察不同时间维度下择时的影响。</div>
  <div class="rules">
    <div class="rule">10年 <b>2016.08 - 2026.07</b> 120期</div>
    <div class="rule">5年 <b>2021.08 - 2026.07</b> 60期</div>
    <div class="rule">3年 <b>2023.08 - 2026.07</b> 36期</div>
    <div class="rule">口径 <b>全收益指数（含分红再投）</b></div>
  </div>
</div>

<div class="sec">
  <h2>各指数 · 跨时间维度归一化对比</h2>
  <div class="desc">每个指数一张图，展示10年/5年/3年三个时间维度下，最高价买入（实线）与最低价买入（虚线）的归一化走势。曲线从起点归一化为100，观察不同时间跨度的择时收益差异。</div>
  <div class="cards" id="chartCards"></div>
</div>

<div class="sec">
  <h2>关键数据对比</h2>
  <div class="desc">10年/5年/3年三个时间维度下，最高价买入 vs 最低价买入的年化收益对比。</div>
  <div class="chart">
    <div class="head"><div class="t">年化收益对比表</div></div>
    <div style="overflow-x:auto">
    <table style="width:100%;border-collapse:collapse;font-size:13.5px;min-width:600px" id="dataTable"></table>
    </div>
  </div>
</div>

<div class="sec">
  <h2>总结：择时时间越短，影响越大</h2>
  <div class="desc">10年期限下，每月买在最高点 vs 最低点的年化差仅约1%，但3年/5年维度下差距可达2-5%以上。</div>
  <div class="cards" id="summaryCards" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr))"></div>
</div>

<div class="cta">
  <p>以上内容仅供学习参考，不构成投资建议。投资有风险，入市需谨慎。</p>
</div>

<div class="foot">
  <h3>口径与方法说明</h3>
  <p>1. <b>数据源</b>：中证指数官网（csindex.com.cn）官方日线行情，全收益指数（含分红再投资）。</p>
  <p>2. <b>定投规则</b>：每月固定投入10,000元，分别在当月最高价买入 vs 当月最低价买入；未计交易费用与税费。</p>
  <p>3. <b>年化收益率</b>：按逐笔现金流 XIRR（资金时间价值口径）计算。</p>
  <p>4. <b>归一化处理</b>：所有曲线均从起点设为100，后续值按比例缩放，便于不同时间维度直接对比。</p>
  <p class="warn">⚠ 本页为历史数据回测，不代表未来收益。投资有风险，决策需谨慎。</p>
</div>

</div>

<script>
const CHART_DATA = __CHART_DATA__;
const COLORS = __COLORS__;
const SHORT = __SHORT__;
const CODES = __CODES__;
const META = __META__;
const fonts = {color: "#6b7686", fontFamily: "inherit"};

/* ---------- 4张图 ---------- */
(function(){
  const box = document.getElementById("chartCards");
  CODES.forEach(c => {
    const cd = CHART_DATA[c];
    const color = COLORS[c];
    const name = SHORT[c];
    const card = document.createElement("div");
    card.className = "chart";
    card.innerHTML = `<div class="head"><div class="t"><span style="color:${color}">●</span> ${name}</div><div class="hint">实线=最高价 虚线=最低价</div></div><div id="ch_${c}" style="width:100%;height:400px"></div>`;
    box.appendChild(card);

    const chart = echarts.init(document.getElementById("ch_"+c));
    const series = cd.series.map(s => ({
      name: s.name,
      type: "line",
      data: s.data,
      smooth: false,
      symbol: "none",
      lineStyle: {width: s.lineStyle.width, type: s.lineStyle.type, color: s.color},
      itemStyle: {color: s.color},
      opacity: s.opacity
    }));

    const option = {
      tooltip: {
        trigger: "axis",
        backgroundColor: "rgba(29,41,57,.92)",
        borderWidth: 0,
        textStyle: {color: "#fff", fontSize: 12},
        valueFormatter: v => v == null ? "-" : v.toFixed(1)
      },
      legend: {
        data: series.map(s => s.name),
        top: 0,
        textStyle: {...fonts, fontSize: 11, color: "#6b7686"},
        icon: "roundRect",
        itemWidth: 18,
        itemHeight: 6
      },
      xAxis: {
        type: "category",
        data: cd.series[0].data.map((_, i) => i + "月"),
        axisLine: {lineStyle: {color: "#ccd4de"}},
        axisLabel: {color: "#6b7686", fontSize: 10},
        axisTick: {show: false}
      },
      yAxis: {
        type: "value",
        scale: true,
        axisLabel: {formatter: "{value}", color: "#6b7686", fontSize: 10},
        splitLine: {lineStyle: {color: "#eef2f7"}}
      },
      series: series,
      grid: {top: 42, bottom: 20, left: 46, right: 16}
    };
    chart.setOption(option);
    window.addEventListener("resize", () => chart.resize());
  });
})();

/* ---------- 数据表 ---------- */
(function(){
  const tbl = document.getElementById("dataTable");
  tbl.innerHTML = '<!--ROWS_HTML-->';
})();

/* ---------- 总结卡片 ---------- */
(function(){
  const box = document.getElementById("summaryCards");
  CODES.forEach(c => {
    const color = COLORS[c];
    const name = SHORT[c];
    const diffs = [];
    [10, 5, 3].forEach(y => {
      const s = CHART_DATA[c].series;
      const high = s.filter(x => x.name === META[y].label + "最高价")[0];
      const low = s.filter(x => x.name === META[y].label + "最低价")[0];
      if (high && low) {
        const hLast = high.data[high.data.length - 1];
        const lLast = low.data[low.data.length - 1];
        diffs.push({y: y, diff: (lLast / hLast - 1) * 100});
      }
    });
    const el = document.createElement("div");
    el.className = "chart";
    el.style.padding = "14px 16px";
    const maxDiff = Math.max(...diffs.map(d => d.diff));
    el.innerHTML = `
      <div style="font-weight:700;font-size:15px;margin-bottom:8px"><span style="color:${color}">●</span> ${name}</div>
      <div style="font-size:12px;color:var(--sub);margin-bottom:6px">最低价vs最高价终值超额</div>
      ${diffs.sort((a,b)=>b.y-a.y).map(d => `<div style="display:flex;justify-content:space-between;font-size:13px;padding:4px 0;border-bottom:1px dashed #f1f4f8"><span>${META[d.y].label}（${META[d.y].start}）</span><span style="font-weight:700;color:#c0392b">+${d.diff.toFixed(1)}%</span></div>`).join("")}
      <div style="margin-top:8px;font-size:12px;color:#c0392b;font-weight:600">最大超额：+${maxDiff.toFixed(1)}%</div>
    `;
    box.appendChild(el);
  });
})();
</script>
</body>
</html>
"""

# 构建Python端数据
ROWS = []
for c in CODES:
    for y in [10, 5, 3]:
        idx = [i for i in data[y]["indices"] if i["code"] == c][0]
        h = idx["high"]
        l = idx["low"]
        ROWS.append({
            "code": c, "short": SHORT[c], "years": y, "label": YEARS_META[y]["label"],
            "h_cagr": f"{h['cagr']*100:.2f}%" if h['cagr'] else "N/A",
            "l_cagr": f"{l['cagr']*100:.2f}%" if l['cagr'] else "N/A",
            "diff": f"+{(l['cagr']-h['cagr'])*100:.2f}%" if h['cagr'] and l['cagr'] else "N/A",
            "h_final": f"¥{h['final_value']:,.0f}",
            "l_final": f"¥{l['final_value']:,.0f}",
        })

ROWS_HTML = '<thead><tr><th>指数</th><th>维度</th><th>最高价年化</th><th>最低价年化</th><th>年化差</th><th>最高价终值</th><th>最低价终值</th></tr></thead><tbody>'
for r in ROWS:
    ROWS_HTML += f'<tr><td><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{COLORS[r["code"]]}"></span> <b>{r["short"]}</b></td><td>{r["label"]}</td><td class="num">{r["h_cagr"]}</td><td class="num">{r["l_cagr"]}</td><td class="num" style="color:#c0392b;font-weight:700">{r["diff"]}</td><td class="num">{r["h_final"]}</td><td class="num">{r["l_final"]}</td></tr>'
ROWS_HTML += '</tbody>'

html = html.replace("__CHART_DATA__", jdump(chart_data))
html = html.replace("__COLORS__", jdump(COLORS))
html = html.replace("__SHORT__", jdump(SHORT))
html = html.replace("__CODES__", jdump(CODES))
html = html.replace("__META__", jdump({k: {"label": v["label"], "start": v["start"]} for k, v in YEARS_META.items()}))
html = html.replace("ROWS_HTML", ROWS_HTML)

outname = "dividend_high_low_cross_time.html"
with open(outname, "w", encoding="utf-8") as f:
    f.write(html)
print(f"已生成 {outname}")