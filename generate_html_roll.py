# -*- coding: utf-8 -*-
"""读 roll_1y.json, 生成 dividend_dashboard_roll.html 网页看板(任意时点滚动12个月定投)"""
import json

r = json.load(open("roll_1y.json", encoding="utf-8"))
WINDOWS = r["windows"]  # 109个起点窗口

# 起点列表(按月)
STARTS = [w["start"] for w in WINDOWS]
SHORTS = ["上证红利", "中证红利", "红利低波", "红利低波100"]
CODES = {"上证红利": "H00015", "中证红利": "H00922", "红利低波": "H20269", "红利低波100": "H20955"}
COLORS = {"H00015": "#27ae60", "H00922": "#3498db", "H20269": "#e74c3c", "H20955": "#e67e22"}

# 每个起点 -> 各指数数据
def wdata(w, short):
    d = w["indices"].get(short, {})
    return {
        "cagr": round((d.get("cagr") or 0) * 100, 2),
        "total_ret": round((d.get("total_ret") or 0) * 100, 2),
        "mdd": round((d.get("mdd") or 0) * 100, 2),
        "mdd_amt": round(d.get("mdd_amt") or 0),
        "peak": d.get("peak_date"), "trough": d.get("trough_date"),
        "recover": d.get("recover_date"), "rec_days": d.get("rec_days"),
        "end": d.get("end"),
    }

# 系列: 每个指数一条滚动年化曲线(按起点) + 回撤 + 修复天数
SERIES = {}
for short in SHORTS:
    SERIES[short] = {
        "cagr": [wdata(w, short)["cagr"] for w in WINDOWS],
        "mdd": [wdata(w, short)["mdd"] for w in WINDOWS],
        "rec_days": [wdata(w, short)["rec_days"] for w in WINDOWS],
    }

# 汇总统计
STATS = {}
for short in SHORTS:
    c = sorted(SERIES[short]["cagr"])
    m = sorted(SERIES[short]["mdd"])
    rd = [x for x in SERIES[short]["rec_days"] if x is not None]
    rd_sorted = sorted(rd)
    def pct(arr, p):
        if not arr: return None
        return arr[min(len(arr)-1, int(len(arr)*p))]
    neg = sum(1 for x in c if x < 0)
    STATS[short] = {
        "n": len(c),
        "cagr_min": c[0], "cagr_p10": pct(c, .1), "cagr_p25": pct(c, .25),
        "cagr_med": pct(c, .5), "cagr_p75": pct(c, .75), "cagr_p90": pct(c, .9), "cagr_max": c[-1],
        "win_pct": (len(c)-neg)/len(c)*100,
        "mdd_min": m[0], "mdd_med": pct(m, .5), "mdd_max": m[-1],
        "rec_med": pct(rd_sorted, .5), "rec_p75": pct(rd_sorted, .75), "rec_p90": pct(rd_sorted, .9),
        "rec_max": rd_sorted[-1], "n_rec_fail": len(rd)-len(rd_sorted), "n_unrecover": sum(1 for x in SERIES[short]["rec_days"] if x is None),
    }

# 最差/最好起点(按红利低波 or 各指数合并)
WORST = []
BEST = []
for short in SHORTS:
    ws = sorted([(w["start"], wdata(w, short)["cagr"]) for w in WINDOWS], key=lambda x: x[1])[:3]
    bs = sorted([(w["start"], wdata(w, short)["cagr"]) for w in WINDOWS], key=lambda x: x[1], reverse=True)[:3]
    WORST.append({"short": short, "list": [f"{s} 起：{v:.1f}%" for s, v in ws]})
    BEST.append({"short": short, "list": [f"{s} 起：{v:.1f}%" for s, v in bs]})

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利全收益指数 · 任意时点滚动12个月定投回测</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<script>window.echarts||document.write('<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.5.0/echarts.min.js"><\\/script>');</script>
<style>
:root{
  --bg:#f4f6fa; --card:#ffffff; --ink:#1a2332; --sub:#6b7686; --line:#e6eaf0;
  --red:#c0392b; --green:#1e8e5a; --accent:#b3372c;
  --c1:#e67e22; --c2:#3498db; --c3:#e74c3c; --c4:#27ae60;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.wrap{max-width:1120px;margin:0 auto;padding:32px 20px 80px}
/* Hero */
.hero{background:linear-gradient(135deg,#2b3a4a 0%,#1d2939 60%,#3a2a2a 100%);border-radius:18px;color:#fff;padding:38px 40px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent 70%)}
.hero .tag{display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:3px 14px;font-size:12.5px;letter-spacing:1px;margin-bottom:14px}
.hero h1{font-size:27px;font-weight:800;letter-spacing:.5px;margin-bottom:10px}
.hero h1 em{font-style:normal;color:#ffb37a}
.hero .sub{font-size:14.5px;color:#c7d2de;max-width:800px}
.hero .rules{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.hero .rule{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:7px 14px;font-size:12.8px;color:#e8eef6}
.hero .rule b{color:#ffd28a}
/* Section */
.sec{margin-top:38px}
.sec h2{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sec h2 .no{background:var(--accent);color:#fff;width:28px;height:28px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:14px;flex:none}
.sec .desc{color:var(--sub);font-size:13.5px;margin-bottom:18px}
/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;position:relative;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.card .top{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.card .dot{width:10px;height:10px;border-radius:50%}
.card .nm{font-size:14.5px;font-weight:700}
.card .badge{margin-left:auto;font-size:11px;border-radius:999px;padding:2px 9px;font-weight:700}
.card .badge.win{background:#fdecea;color:var(--red)}
.card .badge.steady{background:#e7f6ee;color:var(--green)}
.card .fval{font-size:25px;font-weight:800;margin:6px 0 2px}
.card .fval small{font-size:13px;color:var(--sub);font-weight:500}
.card .kv{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin-top:10px;border-top:1px dashed var(--line);padding-top:10px}
.card .kv .k{font-size:11.5px;color:var(--sub)}
.card .kv .v{font-size:14px;font-weight:700}
.card .kv .v.pos{color:var(--red)} .card .kv .v.neg{color:var(--green)}
.ix-code{font-family:ui-monospace,Consolas,"SF Mono",monospace;background:#f0f3f8;color:#3a4a5e;padding:2px 8px;border-radius:5px;font-size:12.5px;letter-spacing:.5px;font-weight:700;white-space:nowrap}
/* Table */
.tbl-box{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow-x:auto;overflow-y:hidden;box-shadow:0 1px 3px rgba(20,30,50,.05);-webkit-overflow-scrolling:touch}
table{width:100%;border-collapse:collapse;font-size:13.5px;min-width:600px}
th{background:#f8fafc;color:var(--sub);font-weight:600;text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 14px;border-bottom:1px solid #f1f4f8;white-space:nowrap}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
td b{font-weight:700}
.pos{color:var(--red)} .neg{color:var(--green)}
tr.hl td{background:#fffaf7}
.tbl-scroll-hint{display:none;color:var(--sub);font-size:12px;margin:6px 2px 0;text-align:right}
@media(max-width:760px){
  .hero h1{font-size:22px}.hero{padding:28px 22px}
  .cards{grid-template-columns:1fr}
  .card .kv{grid-template-columns:1fr}
  th,td{padding:9px 10px;font-size:12.5px}
  .tbl-scroll-hint{display:block}
}
/* chart */
.chart{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px 10px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.chart .head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:0 6px 8px}
.chart .head .t{font-size:15px;font-weight:700}
.chart .head .hint{font-size:12px;color:var(--sub)}
.chart .head .pick{display:flex;align-items:center;gap:6px;margin-left:auto;font-size:12.5px;color:var(--sub)}
.chart .head .pick select{padding:5px 8px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;background:#fff}
#c_roll,#c_mdd,#c_rec{width:100%;height:420px}
.legend{display:flex;flex-wrap:wrap;gap:14px;padding:4px 8px 10px;font-size:12.5px;color:var(--sub)}
.legend .li{display:flex;align-items:center;gap:6px}
.legend .sw{width:14px;height:4px;border-radius:2px}
/* alert */
.alert{background:linear-gradient(135deg,#fdf3f2,#fdf8f6);border:1px solid #f2d6d0;border-radius:14px;padding:20px 22px;margin-top:14px}
.alert .t{font-size:15.5px;font-weight:800;color:var(--red);margin-bottom:8px}
.alert .b{font-size:13.5px;color:#5b4a45}
.alert .big{font-size:34px;font-weight:800;color:var(--red)}
.alert-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:12px}
.alert-grid .ag{background:#fff;border:1px solid #f0e0dc;border-radius:10px;padding:12px 14px}
.alert-grid .ag .n{font-size:12px;color:var(--sub)}
.alert-grid .ag .v{font-size:19px;font-weight:800}
/* pick(结论) */
.pick{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.pick .pc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.pick .pc .pt{display:flex;align-items:center;gap:8px;font-weight:800;font-size:15.5px;margin-bottom:4px}
.pick .pc .pc-tag{font-size:11px;background:#fdecea;color:var(--red);border-radius:999px;padding:2px 9px;font-weight:700}
.pick .pc .pc-sub{color:var(--sub);font-size:12.8px;margin-bottom:12px}
.pick .pc ul{list-style:none}
.pick .pc li{font-size:13.2px;padding:6px 0;border-bottom:1px dashed #f1f4f8;display:flex;gap:8px}
.pick .pc li:last-child{border-bottom:none}
.pick .pc li .k{color:var(--sub);flex:none}
.pick .pc li .v{font-weight:700}
/* foot */
.foot{margin-top:44px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 26px;font-size:12.8px;color:var(--sub)}
.foot h3{color:var(--ink);font-size:14.5px;margin-bottom:8px}
.foot p{margin-bottom:6px}
.foot .warn{color:var(--red);font-weight:600}
/* quote */
.quote{margin-top:18px;background:#1d2939;border-radius:14px;padding:24px 28px;color:#e8eef6}
.quote p{font-size:16.5px;font-weight:600;letter-spacing:.5px}
.quote .who{margin-top:8px;font-size:12.5px;color:#8fa0b5}
/* CTA */
.cta{margin-top:18px;background:linear-gradient(135deg,#fdf3f2 0%,#fbe9e7 100%);border:1px solid #f3d9d5;border-radius:14px;padding:24px 30px;text-align:center;box-shadow:0 1px 6px rgba(192,57,43,.06)}
.cta p{font-size:16px;font-weight:700;color:#8c2f28;letter-spacing:.5px;line-height:1.8}
.cta p b{color:#b3372c;font-weight:800}
.cta .sub{font-size:12px;color:#8b7a77;margin-top:8px;letter-spacing:.3px;line-height:1.7}
@media(max-width:720px){.hero h1{font-size:22px}.hero{padding:28px 22px}}
</style>
</head>
<body>
<div class="wrap">

<!-- HERO -->
<div class="hero">
  <h1>任意时点开始，滚动定投 12 个月：<br><em>你能赚多少、亏多少、多久回本？</em></h1>
  <div class="sub">基于中证指数官网全收益指数官方日线（csindex.com.cn），对 2016-08 至 2025-08 之间<b>任意月份首个交易日</b>作为起点、连续 12 个月每月定投 ¥1 万元（共 12 期）逐窗复算。覆盖 <b>%%N_WINDOWS%% 个起点窗口</b>，完整还原每个时点的年化收益率、最大回撤与回撤修复耗时。</div>
  <div class="rules">
    <div class="rule">起点范围 <b>2016.08 - 2025.08</b></div>
    <div class="rule">窗口 <b>起点起连续 12 个月</b></div>
    <div class="rule">每期 <b>¥10,000</b>（共 12 期）</div>
    <div class="rule">窗口数 <b>%%N_WINDOWS%% 个</b></div>
    <div class="rule">口径 <b>全收益指数（含分红再投）</b></div>
  </div>
</div>

<!-- 1 总览卡片 -->
<div class="sec">
  <h2><span class="no">1</span>109 个时点开始定投 1 年，结果分布</h2>
  <div class="desc">年化收益率中位数约 7%-11%；约 8 成时点盈利，2 成时点亏损；任意时刻开始都会经历约 -7%~-8% 的账面浮亏（中位），最深约 -13%。</div>
  <div class="cards" id="cards"></div>
</div>

<!-- 2 起点选择器 -->
<div class="sec">
  <h2><span class="no">2</span>选一个起点，看这一年的完整测算</h2>
  <div class="desc">下拉选择任意起始月份，下方实时显示：该窗口 12 个月的年化收益率、总收益、最大回撤、浮亏金额与回撤收复耗时。</div>
  <div class="chart">
    <div class="head">
      <div class="t">指定起点 · 滚动12个月定投明细</div>
      <div class="pick">
        <span>起点月份</span>
        <select id="selStart"></select>
      </div>
    </div>
    <div class="tbl-box" style="border:none;box-shadow:none">
    <table id="tbl_pick"></table>
    </div>
    <div class="tbl-scroll-hint">← 左右滑动查看更多 →</div>
  </div>
</div>

<!-- 3 滚动年化曲线 -->
<div class="sec">
  <h2><span class="no">3</span>任意起点 · 滚动12个月年化收益率</h2>
  <div class="desc">横轴为定投起点月份，纵轴为该窗口 12 个月的年化收益率（XIRR）。曲线在 0% 线之上的部分＝该时点开始定投 1 年能赚钱；之下＝亏钱。红涨绿跌（A 股习惯）。</div>
  <div class="chart">
    <div class="head"><div class="t">滚动12个月年化收益率（按起点）</div><div class="hint">悬浮查看任一起点</div></div>
    <div id="c_roll"></div>
    <div class="legend" id="lg1"></div>
  </div>
</div>

<!-- 4 回撤深度 -->
<div class="sec">
  <h2><span class="no">4</span>任意起点 · 12个月内最大回撤</h2>
  <div class="desc">组合市值口径：从每月扣款后的账户市值峰值回落到谷底的最大幅度（定投者真实的浮亏深度）。曲线越深＝该时点开始定投的浮亏越深。</div>
  <div class="chart">
    <div class="head"><div class="t">滚动12个月组合最大回撤（按起点）</div><div class="hint">负值表示浮亏幅度</div></div>
    <div id="c_mdd"></div>
    <div class="legend" id="lg2"></div>
  </div>
</div>

<!-- 5 回撤修复 -->
<div class="sec">
  <h2><span class="no">5</span>回撤多久能修复？</h2>
  <div class="desc">回撤修复＝从最大回撤谷底到首次收复峰值市值的<b>交易日数</b>。定投持续买入使市值中枢上移，多数时点的回撤在 <b>1 个月内（约 5 个交易日）</b>即修复；但约 20% 的时点在 12 个月结束时仍未完全修复（对应单边回调期）。</div>
  <div class="chart">
    <div class="head"><div class="t">回撤修复耗时（交易日，按起点）</div><div class="hint">柱高＝修复天数；标"未修复"＝12个月窗口内未收复</div></div>
    <div id="c_rec"></div>
    <div class="legend" id="lg3"></div>
  </div>
  <div class="alert">
    <div class="t">⚠ 记住：回撤是红利策略的固有属性</div>
    <div class="b">10 年数据里，任意时点开始定投 1 年：<b>盈利概率约 8 成</b>，中位数年化 7%-11%，但过程中<b>几乎必定经历 1 次约 -7%~-8% 的账面浮亏</b>。最深的坑集中在 <b>2017H2-2018（2018 熊市）与 2025 年中段</b>——那正是"打折进货"的时点，坚持定投摊低成本才是关键。</div>
    <div class="alert-grid" id="alertGrid"></div>
  </div>
</div>

<!-- 6 结论 -->
<div class="sec">
  <h2><span class="no">6</span>那到底选哪个？</h2>
  <div class="desc">收益相近时，回撤更小、恢复更快的指数持有体验更好：红利低波盈利概率最高（81.7%）、中位数年化最高（10.6%）；红利低波100 回撤最浅。</div>
  <div class="pick" id="pick"></div>
  <div class="quote">
    <p>「10 年定投的最大考验从来不是选哪个指数，而是在账面浮亏的那几个月里，你能不能继续投下去。定投最大的敌人不是市场，是你自己。」</p>
    <div class="who">回撤是权益策略固有特征，坚持是关键。对比 10 年期缴年金险，其保证回本周期约 8‑12 年，中途退保会亏损本金。红利定投波动直观可见，但保留资金流动性，长期具备更高收益的可能性。</div>
  </div>
</div>

<!-- CTA -->
<div class="cta">
  <p>如需获取更多定投策略参考、同步市场变化相关观察，<b>欢迎和我进一步交流，落地你的定投计划</b>。您的支持是我继续研究的动力。以上内容仅供学习参考，不构成投资建议，投资有风险，入市需谨慎。</p>
</div>

<!-- foot -->
<div class="foot">
  <h3>口径与方法说明</h3>
  <p>1. <b>数据源</b>：中证指数官网（csindex.com.cn）官方日线行情，全收益指数（含分红再投资），四个指数：H00015 上证红利、H00922 中证红利、H20269 红利低波、H20955 红利低波100 全收益。</p>
  <p>2. <b>滚动口径</b>：以 2016-08 至 2025-08 每个月的首个交易日为起点（%%N_WINDOWS%% 个），自该起点起连续 12 个月、每月首个交易日定投 ¥10,000（12 期、总投入 ¥120,000）；以第 12 期所在月的最后一个交易日为窗口结束日，共 12 个自然月。</p>
  <p>3. <b>年化收益率</b>：按逐笔现金流 XIRR（资金时间价值口径）计算；<b>总收益</b>＝期末市值/累计投入−1。</p>
  <p>4. <b>组合市值回撤</b>＝每日（累计份额 × 指数点位）从历史峰值回落的最大幅度；<b>浮亏金额</b>＝峰值市值−谷底市值；<b>回撤修复</b>＝自谷底首次收复峰值市值的交易日数，未在 12 个月窗口内收复则记"未修复"。</p>
  <p>5. <b>收益口径</b>：收益率为百分比口径，与定投金额线性无关；未计交易费用与税费。</p>
  <p class="warn">⚠ 本页为历史数据回测，不代表未来收益。红利策略亦存在长期跑输与估值回归风险。投资有风险，决策需谨慎。</p>
</div>

</div>

<script>
const STARTS = __STARTS__;
const SHORTS = __SHORTS__;
const CODES = __CODES__;
const COLORS = __COLORS__;
const SERIES = __SERIES__;
const STATS = __STATS__;
const WORST = __WORST__;
const BEST = __BEST__;
const WINDOWS = __WINDOWS__;

const fonts = {fontFamily:"-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"};
const axis = {
  axisLine:{lineStyle:{color:"#d7dde6"}},
  axisLabel:{color:"#6b7686",fontSize:11,...fonts},
  splitLine:{lineStyle:{color:"#eef1f6"}}
};

/* ---------- 1 卡片 ---------- */
(function(){
  const box = document.getElementById("cards");
  SHORTS.forEach(short=>{
    const s = STATS[short];
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="top"><span class="dot" style="background:${COLORS[CODES[short]]}"></span><span class="nm">${short}</span><span class="ix-code">${CODES[short]}</span>
        ${s.win_pct===Math.max(...SHORTS.map(x=>STATS[x].win_pct))?'<span class="badge win">盈利概率最高</span>':''}</div>
      <div class="fval">${s.cagr_med.toFixed(1)}% <small>中位年化</small></div>
      <div class="kv">
        <div><div class="k">盈利窗口占比</div><div class="v pos">${s.win_pct.toFixed(1)}%</div></div>
        <div><div class="k">年化范围</div><div class="v">${s.cagr_min.toFixed(1)}% ~ +${s.cagr_max.toFixed(1)}%</div></div>
        <div><div class="k">中位最大回撤</div><div class="v neg">${s.mdd_med.toFixed(1)}%</div></div>
        <div><div class="k">最深回撤</div><div class="v neg">${s.mdd_min.toFixed(1)}%</div></div>
        <div><div class="k">回撤修复(中位)</div><div class="v">${s.rec_med} 交易日</div></div>
        <div><div class="k">未修复窗口</div><div class="v">${s.n_unrecover}/${s.n}</div></div>
      </div>`;
    box.appendChild(el);
  });
})();

/* ---------- 2 起点选择表 ---------- */
(function(){
  const sel = document.getElementById("selStart");
  sel.innerHTML = STARTS.map(s=>`<option value="${s}">${s}</option>`).join("");
  sel.value = "2025-08";
  function render(){
    const start = sel.value;
    const wi = STARTS.indexOf(start);
    const w = WINDOWS[wi];
    const rows = SHORTS.map(short=>{
      const d = w.indices[short];
      const cagr = ((d.cagr||0)*100).toFixed(2);
      const ret = ((d.total_ret||0)*100).toFixed(2);
      const mdd = ((d.mdd||0)*100).toFixed(2);
      const rec = d.rec_days!=null ? d.rec_days+" 天" : "未修复";
      const recDay = d.recover_date || "—";
      return `<tr ${short==="红利低波"?"class='hl'":""}>
        <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${COLORS[CODES[short]]}"></span> <b>${short}</b></td>
        <td class="num ${cagr>=0?"pos":"neg"}"><b>${cagr}%</b></td>
        <td class="num ${ret>=0?"pos":"neg"}">${ret}%</td>
        <td class="num neg"><b>${mdd}%</b></td>
        <td class="num neg">-¥${Math.round(d.mdd_amt||0).toLocaleString()}</td>
        <td class="num">${d.peak}</td>
        <td class="num">${d.trough}</td>
        <td class="num">${recDay}</td>
        <td class="num">${rec}</td>
      </tr>`;
    }).join("");
    document.getElementById("tbl_pick").innerHTML = `
      <tr><th>指数</th><th class="num">年化(XIRR)</th><th class="num">12个月总收益</th><th class="num">组合最大回撤</th><th class="num">最大浮亏</th><th class="num">峰值日</th><th class="num">谷底日</th><th class="num">收复日</th><th class="num">修复耗时</th></tr>${rows}`;
  }
  sel.onchange = render;
  render();
})();

/* ---------- 3 滚动年化曲线 ---------- */
let rollChart=null;
function renderRoll(){
  const series = SHORTS.map(short=>({
    name:short, type:"line", data:SERIES[short].cagr, smooth:false, symbol:"none", color:COLORS[CODES[short]],
    lineStyle:{width:1.8,color:COLORS[CODES[short]]},
    areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:COLORS[CODES[short]]+"44"},{offset:1,color:COLORS[CODES[short]]+"06"}]}},
    emphasis:{focus:"series"}
  }));
  rollChart.setOption({
    grid:{left:56,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",valueFormatter:v=>v.toFixed(2)+"%"},
    legend:{data:SHORTS,top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:STARTS,boundaryGap:false,axisLabel:{...axis.axisLabel,interval:Math.ceil(STARTS.length/10)},...axis},
    yAxis:{type:"value",axisLabel:{formatter:v=>v.toFixed(0)+"%",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}},
      markLine:undefined,
      splitLine:{show:true,lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* ---------- 4 回撤深度 ---------- */
let mddChart=null;
function renderMdd(){
  const series = SHORTS.map(short=>({
    name:short, type:"line", data:SERIES[short].mdd, smooth:false, symbol:"none", color:COLORS[CODES[short]],
    lineStyle:{width:1.8,color:COLORS[CODES[short]]},
    emphasis:{focus:"series"}
  }));
  mddChart.setOption({
    grid:{left:56,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",valueFormatter:v=>v.toFixed(2)+"%"},
    legend:{data:SHORTS,top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:STARTS,boundaryGap:false,axisLabel:{...axis.axisLabel,interval:Math.ceil(STARTS.length/10)},...axis},
    yAxis:{type:"value",max:0,axisLabel:{formatter:v=>v.toFixed(0)+"%",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* ---------- 5 修复耗时 ---------- */
let recChart=null;
function renderRec(){
  const series = SHORTS.map(short=>({
    name:short, type:"bar", data:SERIES[short].rec_days.map(v=>v==null?null:v),
    barWidth:"18%", color:COLORS[CODES[short]],
    itemStyle:{borderRadius:[3,3,0,0],color:COLORS[CODES[short]]},
    label:{show:false},
    emphasis:{focus:"series"}
  }));
  recChart.setOption({
    grid:{left:48,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",formatter:ps=>{
      const i=ps[0].dataIndex;
      let s=`起点 <b>${STARTS[i]}</b><br>`;
      SHORTS.forEach(short=>{
        const v=SERIES[short].rec_days[i];
        s+=`${short}：${v==null?"未修复（12个月内未收复）":v+" 交易日（约"+(v>=21?Math.round(v/21):1)+"个月）"}<br>`;
      });
      return s;
    }},
    legend:{data:SHORTS,top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:STARTS,axisLabel:{...axis.axisLabel,interval:Math.ceil(STARTS.length/10)},...axis},
    yAxis:{type:"value",name:"交易日",nameTextStyle:{color:"#6b7686"},axisLabel:{color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* 图例 */
(function(){
  document.getElementById("lg1").innerHTML = SHORTS.map(short=>`<div class="li"><span class="sw" style="background:${COLORS[CODES[short]]}"></span>${short} 中位 ${STATS[short].cagr_med.toFixed(1)}%</div>`).join("");
  document.getElementById("lg2").innerHTML = SHORTS.map(short=>`<div class="li"><span class="sw" style="background:${COLORS[CODES[short]]}"></span>${short} 中位 ${STATS[short].mdd_med.toFixed(1)}%</div>`).join("");
  document.getElementById("lg3").innerHTML = SHORTS.map(short=>`<div class="li"><span class="sw" style="background:${COLORS[CODES[short]]}"></span>${short} 修复中位 ${STATS[short].rec_med} 天</div>`).join("");
})();

/* 提醒区 */
(function(){
  const box = document.getElementById("alertGrid");
  const items = [
    {n:"任意起点盈利概率", v:"78.9% - 81.7%", s:"红利低波最高，低波100 次之"},
    {n:"中位年化收益率", v:"7.5% - 10.6%", s:"红利低波最高（10.6%）"},
    {n:"中位最大回撤", v:"-6.5% ~ -7.9%", s:"低波100 最浅（-6.5%）"},
    {n:"最差时点", v:"2017H2-2018", s:"2018 熊市，年化最低 -17%~-24%"},
  ];
  items.forEach(it=>{
    const el = document.createElement("div");
    el.className = "ag";
    el.innerHTML = `<div class="n">${it.n}</div><div class="v">${it.v}</div><div style="font-size:12px;color:var(--sub)">${it.s}</div>`;
    box.appendChild(el);
  });
})();

/* ---------- 6 结论 ---------- */
(function(){
  const PICK = ["红利低波","红利低波100","中证红利"];
  const pickMeta = {
    "红利低波": {t:"如果只能选一个：红利低波全收益",tag:"全场最佳",why:"盈利概率最高（81.7%）、中位数年化最高（10.6%），横跨沪深两市、50 只成分股兼顾分散与弹性。"},
    "红利低波100": {t:"追求极致稳定：红利低波100全收益",why:"100 只成分股足够分散；组合回撤最浅（中位 -6.5%），持有最安心。"},
    "中证红利": {t:"看重体验与配置：中证红利全收益",why:"全市场主流红利成分，回撤控制好、恢复快；ETF 规模大、流动性好。"}
  };
  const html = PICK.map(short=>{
    const s = STATS[short];
    const m = pickMeta[short];
    const li = [
      ["盈利窗口占比", s.win_pct.toFixed(1)+"%"],
      ["中位年化收益率", s.cagr_med.toFixed(2)+"%"],
      ["年化区间", s.cagr_min.toFixed(1)+"% ~ +"+s.cagr_max.toFixed(1)+"%"],
      ["中位最大回撤", s.mdd_med.toFixed(2)+"%"],
      ["回撤修复(中位)", s.rec_med+" 交易日"],
      ["未修复窗口", s.n_unrecover+" 个 / "+s.n],
    ];
    return `<div class="pc">
      <div class="pt"><span class="dot" style="width:10px;height:10px;border-radius:50%;background:${COLORS[CODES[short]]}"></span>${m.t} ${m.tag?'<span class="pc-tag">'+m.tag+'</span>':''}</div>
      <div class="pc-sub"><span class="ix-code">${CODES[short]}</span> · 任意起点滚动12个月</div>
      <ul>${li.map(x=>`<li><span class="k">${x[0]}</span><span class="v">${x[1]}</span></li>`).join("")}</ul>
      <div style="font-size:12.5px;color:var(--sub);margin-top:10px;background:#fafbfc;border-radius:8px;padding:8px 10px">${m.why}</div>
    </div>`;
  }).join("");
  document.getElementById("pick").innerHTML = html;
})();

/* init */
window.addEventListener("resize",()=>{rollChart&&rollChart.resize();mddChart&&mddChart.resize();recChart&&recChart.resize();});
(function init(){
  rollChart = echarts.init(document.getElementById("c_roll"));
  mddChart = echarts.init(document.getElementById("c_mdd"));
  recChart = echarts.init(document.getElementById("c_rec"));
  renderRoll(); renderMdd(); renderRec();
})();
</script>
</body>
</html>"""

# 注入数据
reps = {"%%N_WINDOWS%%": str(len(WINDOWS))}
for k, v in reps.items():
    html = html.replace(k, v)

html = html.replace("__STARTS__", jdump(STARTS))
html = html.replace("__SHORTS__", jdump(SHORTS))
html = html.replace("__CODES__", jdump(CODES))
html = html.replace("__COLORS__", jdump(COLORS))
html = html.replace("__SERIES__", jdump(SERIES))
html = html.replace("__STATS__", jdump(STATS))
html = html.replace("__WORST__", jdump(WORST))
html = html.replace("__BEST__", jdump(BEST))
# WINDOWS 用于起点选择表(取各窗口的 indices)
W = [{ "start": w["start"], "indices": {short: w["indices"].get(short) for short in SHORTS} } for w in WINDOWS]
html = html.replace("__WINDOWS__", jdump(W))

open("dividend_dashboard_roll.html", "w", encoding="utf-8").write(html)
print("已生成 dividend_dashboard_roll.html,", len(html)//1024, "KB")
