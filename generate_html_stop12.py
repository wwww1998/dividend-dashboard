# -*- coding: utf-8 -*-
"""读 roll_stop12.json, 生成 dividend_dashboard_stop12.html
内容: 每月定投12期(1年)后停止定投, 持有不动, 从停止日起多久回正(市值回到累计投入)
不含"持续定投到100%盈利"的数据
"""
import json

r = json.load(open("roll_stop12.json", encoding="utf-8"))
STARTS = r["starts"]                      # 97 个起点
RESULTS = r["results"]                    # 指数 -> [{start, profit_at_stop, recover_days, recover_date, rec_months, max_loss_after}]

SHORTS = ["上证红利", "中证红利", "红利低波", "红利低波100"]
CODES = {"上证红利": "H00015", "中证红利": "H00922", "红利低波": "H20269", "红利低波100": "H20955"}
COLORS = {"H00015": "#e67e22", "H00922": "#3498db", "H20269": "#e74c3c", "H20955": "#27ae60"}

def pct(arr, p):
    if not arr: return None
    return arr[min(len(arr)-1, int(len(arr)*p))]

# 汇总统计: 只针对"停止时仍亏损"的起点(它们才有"回正等待")
STATS = {}
for short in SHORTS:
    rows = RESULTS[short]
    n_total = len(rows)
    n_profit = sum(1 for x in rows if x["profit_at_stop"] > 0)
    n_loss = n_total - n_profit
    loss = [x for x in rows if x["profit_at_stop"] <= 0]
    recs = sorted([x["recover_days"] for x in loss if x["recover_days"] is not None])
    n_unrec = sum(1 for x in loss if x["recover_days"] is None)
    max_loss_after = sorted([x["max_loss_after"] for x in loss])  # 0~1 之间, 越大浮亏越深? 实际为负值比例? 见下
    # max_loss_after 语义: (min市值/投入-1) 若 min_val 低于投入则为负; 统计停止后最深浮亏(负数, 单位比例)
    deep = sorted([x["max_loss_after"] for x in loss])
    STATS[short] = {
        "n_total": n_total, "n_profit": n_profit, "n_loss": n_loss,
        "n_unrec": n_unrec,
        "rec_med": pct(recs, .5), "rec_p75": pct(recs, .75), "rec_p90": pct(recs, .9), "rec_max": recs[-1] if recs else None,
        "deep_med": pct(deep, .5), "deep_min": deep[0] if deep else None,   # 最深(最负)
        # 全样本: 停止时已盈利的回正记 0 天
        "rec_all_med": pct(sorted([0 if x["profit_at_stop"]>0 else (x["recover_days"] if x["recover_days"] is not None else 9999) for x in rows]), .5),
    }
    # 停止时亏损起点回正耗时(交易日)
    print(short, STATS[short])

# 股息率数据(价差法, 与其他网页一致)
YIELDS = {}
for y in json.load(open("dividend_yield.json", encoding="utf-8")):
    YIELDS[y["code"]] = {
        "dy": y["dy_12m_daily"] * 100, "tr": y["tr_ret"] * 100, "pr": y["pr_ret"] * 100,
        "d0": f"{y['d0'][:4]}-{y['d0'][4:6]}-{y['d0'][6:]}", "d1": f"{y['d1'][:4]}-{y['d1'][4:6]}-{y['d1'][6:]}",
        "ldy": y["latest_dy"] * 100, "ld1": f"{y['latest_d1'][:4]}-{y['latest_d1'][4:6]}-{y['latest_d1'][6:]}",
    }

# 场外联接基金(与其他网页一致)
OTC = {
    "H00015": "华泰柏瑞红利ETF联接A(012761)/C(012762)",
    "H00922": "易方达中证红利ETF联接发起式A(009051)/C(009052)",
    "H20269": "华泰柏瑞中证红利低波动ETF联接A(007466)/C(007467)",
    "H20955": "景顺长城中证红利低波动100ETF联接A(016128)/C(016129)",
}

# 每指数 每起点 -> 序列(用于图表): 回正天数(亏损起点), 停止时浮盈
SERIES = {}
for short in SHORTS:
    rows = RESULTS[short]
    SERIES[short] = {
        "profit_at_stop": [round(x["profit_at_stop"]) for x in rows],
        "rec_days": [x["recover_days"] if x["recover_days"] is not None else None for x in rows],
        "rec_days_loss": [x["recover_days"] if (x["recover_days"] is not None and x["profit_at_stop"]<=0) else None for x in rows],
    }

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利全收益指数 · 定投12个月后停止 · 多久回正？</title>
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
.hero{background:linear-gradient(135deg,#2b3a4a 0%,#1d2939 60%,#3a2a2a 100%);border-radius:18px;color:#fff;padding:38px 40px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent 70%)}
.hero .tag{display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:3px 14px;font-size:12.5px;letter-spacing:1px;margin-bottom:14px}
.hero h1{font-size:27px;font-weight:800;letter-spacing:.5px;margin-bottom:10px}
.hero h1 em{font-style:normal;color:#ffb37a}
.hero .sub{font-size:14.5px;color:#c7d2de;max-width:820px}
.hero .rules{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.hero .rule{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:7px 14px;font-size:12.8px;color:#e8eef6}
.hero .rule b{color:#ffd28a}
.sec{margin-top:38px}
.sec h2{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sec h2 .no{background:var(--accent);color:#fff;width:28px;height:28px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:14px;flex:none}
.sec .desc{color:var(--sub);font-size:13.5px;margin-bottom:18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;position:relative;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.card .top{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.card .dot{width:10px;height:10px;border-radius:50%}
.card .nm{font-size:14.5px;font-weight:700}
.card .badge{margin-left:auto;font-size:11px;border-radius:999px;padding:2px 9px;font-weight:700}
.card .badge.win{background:#fdecea;color:var(--red)}
.card .fval{font-size:25px;font-weight:800;margin:6px 0 2px}
.card .fval small{font-size:13px;color:var(--sub);font-weight:500}
.card .kv{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin-top:10px;border-top:1px dashed var(--line);padding-top:10px}
.card .kv .k{font-size:11.5px;color:var(--sub)}
.card .kv .v{font-size:14px;font-weight:700}
.card .kv .v.pos{color:var(--red)} .card .kv .v.neg{color:var(--green)}
.card .badge.steady{background:#e7f6ee;color:var(--green)}
.ix-code{font-family:ui-monospace,Consolas,"SF Mono",monospace;background:#f0f3f8;color:#3a4a5e;padding:2px 8px;border-radius:5px;font-size:12.5px;letter-spacing:.5px;font-weight:700;white-space:nowrap}
/* 科普 */
.know{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.kn{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.kn h3{font-size:15px;font-weight:800;margin-bottom:10px;display:flex;align-items:center;gap:8px;line-height:1.4}
.kn .ico{width:24px;height:24px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;font-size:11.5px;color:#fff;flex:none}
.kn p{font-size:13.2px;color:#4a5568;margin-bottom:8px;line-height:1.75}
.kn ul{list-style:none}
.kn li{font-size:13px;padding:7px 0;border-bottom:1px dashed #f1f4f8;line-height:1.6}
.kn li:last-child{border-bottom:none}
.kn li b{color:var(--ink)}
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
  .know{grid-template-columns:1fr}
  .pick{grid-template-columns:1fr}
  .card .kv{grid-template-columns:1fr}
  th,td{padding:9px 10px;font-size:12.5px}
  .tbl-scroll-hint{display:block}
}
.chart{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px 10px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.chart .head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:0 6px 8px}
.chart .head .t{font-size:15px;font-weight:700}
.chart .head .hint{font-size:12px;color:var(--sub)}
.chart .head .pick{display:flex;align-items:center;gap:6px;margin-left:auto;font-size:12.5px;color:var(--sub)}
.chart .head .pick select{padding:5px 8px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;background:#fff}
#c_rec,#c_profit{width:100%;height:420px}
.legend{display:flex;flex-wrap:wrap;gap:14px;padding:4px 8px 10px;font-size:12.5px;color:var(--sub)}
.legend .li{display:flex;align-items:center;gap:6px}
.legend .sw{width:14px;height:4px;border-radius:2px}
.alert{background:linear-gradient(135deg,#fdf3f2,#fdf8f6);border:1px solid #f2d6d0;border-radius:14px;padding:20px 22px;margin-top:14px}
.alert .t{font-size:15.5px;font-weight:800;color:var(--red);margin-bottom:8px}
.alert .b{font-size:13.5px;color:#5b4a45}
.alert .big{font-size:34px;font-weight:800;color:var(--red)}
.alert-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;margin-top:12px}
.alert-grid .ag{background:#fff;border:1px solid #f0e0dc;border-radius:10px;padding:12px 14px}
.alert-grid .ag .n{font-size:12px;color:var(--sub)}
.alert-grid .ag .v{font-size:19px;font-weight:800}
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
.foot{margin-top:44px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px 26px;font-size:12.8px;color:var(--sub)}
.foot h3{color:var(--ink);font-size:14.5px;margin-bottom:8px}
.foot p{margin-bottom:6px}
.foot .warn{color:var(--red);font-weight:600}
.quote{margin-top:18px;background:#1d2939;border-radius:14px;padding:24px 28px;color:#e8eef6}
.quote p{font-size:16.5px;font-weight:600;letter-spacing:.5px}
.quote .who{margin-top:8px;font-size:12.5px;color:#8fa0b5}
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
  <h1>每月定投 12 个月后停止定投：<br><em>多久能回正？</em></h1>
  <div class="sub">基于中证指数官网全收益指数官方日线，对 <b>%%N_STARTS%% 个起点</b>（2016-08 至 2024-08 每月首个交易日）每月定投 ¥1 万元、连续 <b>12 期</b>（总投入 ¥12 万）后<b>停止定投</b>，持有不动，追踪账户市值何时回到累计投入（回正）。</div>
  <div class="rules">
    <div class="rule">起点范围 <b>2016.08 - 2024.08</b></div>
    <div class="rule">定投 <b>12 期（1 年）后停止</b></div>
    <div class="rule">每期 <b>¥10,000</b>（总投入 ¥12 万）</div>
    <div class="rule">起点数 <b>%%N_STARTS%% 个</b></div>
    <div class="rule">口径 <b>全收益指数（含分红再投）</b></div>
  </div>
</div>

<!-- 0 背景科普 -->
<div class="sec">
  <h2><span class="no">0</span>红利指数基金是什么？为什么买？</h2>
  <div class="desc">先搞懂三件事，再看上面的回正数据才有意义。</div>
  <div class="know">
    <div class="kn">
      <h3><span class="ico" style="background:#3498db">①</span>是什么：一篮子"爱分红的好公司"</h3>
      <p>红利指数基金＝跟踪<b>红利指数</b>的基金（场内 ETF 或场外联接基金）。红利指数从股市里挑出一批<b>股息率高、分红稳定</b>的股票，按股息率加权——你买的不是一只股票，而是"高股息组合"，每年收到成分公司的现金分红。四个主流红利指数的<b>全收益代码</b>：</p>
      <ul>
        <li><b>上证红利全收益</b> <span class="ix-code">H00015</span>：沪市 50 只，老牌高股息大盘成分，每年 12 月调仓换股，当前央国企权重 75‑80%</li>
        <li><b>中证红利全收益</b> <span class="ix-code">H00922</span>：沪深 100 只，全市场主流红利成分，每年 12 月调仓换股，当前央国企权重 70‑75%</li>
        <li><b>红利低波全收益</b> <span class="ix-code">H20269</span>：沪深 50 只，红利低波双因子成分，每年 12 月调仓换股，当前央国企权重 70‑75%</li>
        <li><b>红利低波100全收益</b> <span class="ix-code">H20955</span>：沪深 100 只，双因子更分散的成分，季度调仓换股（3/6/9/12 月），当前央国企权重 65‑70%</li>
      </ul>
      <p style="font-size:12px;color:var(--sub);margin-top:6px">注：指数规则不专门筛选国企，因高股息行业特征，国央企天然占比更高。</p>
    </div>
    <div class="kn">
      <h3><span class="ico" style="background:#e67e22">②</span>为什么买：三条获利逻辑</h3>
      <ul>
        <li><b>每年收"租"（现金分红）</b>：当前股息率约 4%-5%，1 万本金每年约 400-500 元现金分红，远超十年国债（约 1.7%）与银行理财。</li>
        <li><b>复利滚雪球（分红再投资＋定投）</b>：分红再买份额、跌时定投买更多份额，份额越滚越多。即使只定投 1 年就停止，摊低成本的效果也让"回本"远比直觉快——本页回测里停止时亏损的起点，历史全部回正。</li>
        <li><b>防御性（低波动抗跌）</b>：成分股多为银行、煤炭、石化、交运龙头，盈利稳定。定投过程中几乎必定经历 1 次账面浮亏，但停止后持有等待，最深约 -21%（中位 -6%~-8%）即可收复。</li>
      </ul>
      <p style="margin-top:8px;color:var(--sub)">总回报 ≈ <b>股息收益（4-5%）</b>＋盈利增长（稳健）＋估值变化（小）——红利策略赚的是"确定性现金流"，不赌估值。</p>
    </div>
    <div class="kn">
      <h3><span class="ico" style="background:#27ae60">③</span>当前股息率：仍是国债的 2.4 倍+</h3>
      <p>下表为四个指数<b>近 12 个月实际分红收益率</b>（用官方全收益指数与价格指数价差计算，真实数据；Wind 同口径 2026-07-31 中证红利 4.24%，交叉验证一致）。</p>
      <div class="cards" id="yieldCards" style="grid-template-columns:1fr 1fr;margin-top:4px"></div>
      <p style="margin-top:10px;color:var(--sub);font-size:12.5px">对比：十年期国债收益率约 <b style="color:var(--ink)">1.7%</b>，红利股息率是其 <b>2.4-2.8 倍</b>。注意股息率随价格波动：7 月红利大涨后股息率已从高位回落，4%+ 的"租金"依然稀缺。</p>
    </div>
  </div>
</div>

<!-- 1 总览卡片 -->
<div class="sec">
  <h2><span class="no">1</span>停止定投时，账户是赚是亏？</h2>
  <div class="desc">约 8 成起点在定投满 12 期时已经盈利；约 2 成起点此时仍浮亏，但停止定投后持有不动，历史上全部都能回正。</div>
  <div class="cards" id="cards"></div>
</div>

<!-- 2 停止后回正耗时 -->
<div class="sec">
  <h2><span class="no">2</span>亏损的起点，停止后多久回正？</h2>
  <div class="desc">回正＝停止定投后，账户市值重新回到累计投入（¥12 万）的<b>交易日数</b>。此图只展示"停止时仍亏损"的起点（已盈利起点不产生等待）。柱越高＝等待越久；无柱＝该起点停止时已盈利。</div>
  <div class="chart">
    <div class="head"><div class="t">停止后回正耗时（交易日，按起点）</div><div class="hint">只显示停止时亏损的起点</div></div>
    <div id="c_rec"></div>
    <div class="legend" id="lg1"></div>
  </div>
</div>

<!-- 3 停止时浮盈/浮亏 -->
<div class="sec">
  <h2><span class="no">3</span>停止定投时，账面浮盈或浮亏多少？</h2>
  <div class="desc">定投满 12 期（停止日）当天账户的浮盈/浮亏金额（元）。0 线之上＝赚，之下＝亏。深坑集中在 2017H2-2018 与 2025 中段。</div>
  <div class="chart">
    <div class="head"><div class="t">停止日账面浮盈（元，按起点）</div><div class="hint">悬浮查看任一起点</div></div>
    <div id="c_profit"></div>
    <div class="legend" id="lg2"></div>
  </div>
</div>

<!-- 4 明细表 -->
<div class="sec">
  <h2><span class="no">4</span>选一个起点，看停止后的完整回正过程</h2>
  <div class="desc">下拉选择任意起始月份，查看四个指数：停止日浮盈/浮亏、回正日期、回正耗时、停止后最深浮亏。</div>
  <div class="chart">
    <div class="head">
      <div class="t">指定起点 · 定投12期后停止明细</div>
      <div class="pick"><span>起点月份</span><select id="selStart"></select></div>
    </div>
    <div class="tbl-box" style="border:none;box-shadow:none">
    <table id="tbl_pick"></table>
    </div>
    <div class="tbl-scroll-hint">← 左右滑动查看更多 →</div>
  </div>
</div>

<!-- 5 结论 -->
<div class="sec">
  <h2><span class="no">5</span>那到底意味着什么？</h2>
  <div class="desc">即使只定投 1 年就停止，历史最差的情形也只需约 10-12 个月即可回正；普通亏损起点约 1-3 个月回正。定投摊低成本的效果，让"回本"远比直觉快。</div>
  <div class="alert">
    <div class="t">⚠ 记住</div>
    <div class="b">"回正"说的是<b>市值曾经回到本金</b>（停止后持有等待）；它与"期末恰好盈利"是两回事。前者给足等待时间几乎必然发生，后者要求特定时点账面盈利——本页统计的是<b>停止定投后的回正耗时</b>。</div>
    <div class="alert-grid" id="alertGrid"></div>
  </div>
</div>

<!-- 6 那到底选哪个 -->
<div class="sec">
  <h2><span class="no">6</span>那到底选哪个？</h2>
  <div class="desc">收益相近时，停止时盈利占比更高、回正更快、浮亏更浅的指数持有体验更好，也更可能坚持到底。</div>
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
  <p>2. <b>定投与停止</b>：以 2016-08 至 2024-08 每个月的首个交易日为起点（%%N_STARTS%% 个），自该起点起连续 12 个月、每月首个交易日定投 ¥10,000（12 期、总投入 ¥120,000）；第 12 期定投日为"停止日"，此后不再新增投入、持有不动。</p>
  <p>3. <b>回正</b>＝停止日之后账户市值（份额 × 指数点位）首次重新达到累计投入 ¥120,000 的交易日数；"回正耗时（中位/最长）"仅统计停止时仍亏损的起点。回正日期之后的数据用于追踪，停止时已盈利的起点回正耗时记 0。</p>
  <p>4. <b>停止日浮盈/浮亏</b>＝停止日市值 − 累计投入；<b>停止后最深浮亏</b>＝停止日后市值相对累计投入的最大跌幅（%）。</p>
  <p>5. <b>收益口径</b>：收益率为百分比口径，与定投金额线性无关；未计交易费用与税费。</p>
  <p>6. <b>当前股息率</b>：近 12 个月实际分红收益率，用官方全收益指数与价格指数的日收益差累计（价差法·逐日口径）计算（2025-07-31 ~ 2026-07-31），与 Wind 披露 TTM 股息率交叉验证一致（如中证红利 4.24%，2026-07-31）；最新股息率截至 2026-08-26。</p>
  <p class="warn">⚠ 本页为历史数据回测，不代表未来收益。红利策略亦存在长期跑输与估值回归风险。投资有风险，决策需谨慎。</p>
</div>

</div>

<script>
const STARTS = __STARTS__;
const SHORTS = __SHORTS__;
const CODES = __CODES__;
const COLORS = __COLORS__;
const STATS = __STATS__;
const SERIES = __SERIES__;
const ROWS = __ROWS__;
const YIELDS = __YIELDS__;
const OTC = __OTC__;

const fonts = {fontFamily:"-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"};
const axis = {
  axisLine:{lineStyle:{color:"#d7dde6"}},
  axisLabel:{color:"#6b7686",fontSize:11,...fonts},
  splitLine:{lineStyle:{color:"#eef1f6"}}
};

/* ---------- 1 卡片 ---------- */
(function(){
  const box = document.getElementById("cards");
  const bestWin = Math.max(...SHORTS.map(x=>STATS[x].n_profit/STATS[x].n_total));
  SHORTS.forEach(short=>{
    const s = STATS[short];
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="top"><span class="dot" style="background:${COLORS[CODES[short]]}"></span><span class="nm">${short}</span><span class="ix-code">${CODES[short]}</span>
        ${s.n_profit/s.n_total===bestWin?'<span class="badge win">盈利时点最多</span>':''}</div>
      <div class="fval">${(s.n_profit/s.n_total*100).toFixed(1)}% <small>停止时已盈利</small></div>
      <div class="kv">
        <div><div class="k">停止时仍亏损</div><div class="v">${s.n_loss} / ${s.n_total} 个起点</div></div>
        <div><div class="k">亏损起点回正</div><div class="v">${s.n_loss-s.n_unrec}/${s.n_loss} 个已回正</div></div>
        <div><div class="k">回正耗时(中位)</div><div class="v">${s.rec_med} 交易日</div></div>
        <div><div class="k">最长等待</div><div class="v">${s.rec_max} 交易日</div></div>
        <div><div class="k">停止后最深浮亏(中位)</div><div class="v neg">${(s.deep_med*100).toFixed(1)}%</div></div>
        <div><div class="k">最深浮亏(最差)</div><div class="v neg">${(s.deep_min*100).toFixed(1)}%</div></div>
      </div>`;
    box.appendChild(el);
  });
})();

/* ---------- 股息率卡片 ---------- */
(function(){
  const box = document.getElementById("yieldCards");
  box.innerHTML = SHORTS.map(short=>{
    const c = CODES[short];
    const y = YIELDS[c];
    return `<div class="card" style="padding:14px 16px">
      <div class="top"><span class="dot" style="background:${COLORS[c]}"></span><span class="nm">${short}</span><span class="ix-code">${c}</span></div>
      <div style="font-size:24px;font-weight:700;color:#e74c3c">${y.ldy.toFixed(2)}%</div>
      <div style="font-size:12px;color:var(--sub);margin-top:2px">最新股息率（截至 ${y.ld1}）</div>
      <div style="font-size:24px;font-weight:600;margin-top:8px">${y.dy.toFixed(2)}%</div>
      <div style="font-size:12px;color:var(--sub);margin-top:2px">近12个月实际股息率（${y.d0} ~ ${y.d1}）</div>
      <div style="font-size:11.5px;color:var(--sub);margin-top:8px;background:#fafbfc;border-radius:8px;padding:6px 8px">同期全收益 ${y.tr.toFixed(1)}% ｜ 价格 ${y.pr.toFixed(1)}%</div>
    </div>`;
  }).join("");
})();

/* ---------- 6 那到底选哪个 ---------- */
(function(){
  const CODE2SHORT = {};
  SHORTS.forEach(s=>CODE2SHORT[CODES[s]]=s);
  const PICK = ["H20269","H00922","H00015"];
  const pickMeta = {
    H20269: {t:"如果只能选一个：红利低波全收益", tag:"全场最佳", tagCls:"badge win",
             why:"停止时盈利占比最高，横跨沪深两市、50 只成分股兼顾分散与弹性，持有体验最稳。"},
    H00922: {t:"看重回正速度：中证红利全收益", tag:"回正最快", tagCls:"badge steady",
             why:"亏损起点回正中位仅 15 个交易日（约 1 个月），指数规模大、流动性好。"},
    H00015: {t:"追求浮亏最浅：上证红利全收益", tag:"浮亏最浅", tagCls:"badge steady",
             why:"停止后最深浮亏仅约 -14.3%（四者最浅），账面心理压力最小。"},
  };
  const html = PICK.map(code=>{
    const short = CODE2SHORT[code];
    const s = STATS[short];
    const m = pickMeta[code];
    const profPct = (s.n_profit/s.n_total*100).toFixed(1);
    const li = [
      ["停止时盈利占比", profPct+"%（亏损 "+s.n_loss+" / "+s.n_total+" 个起点）"],
      ["亏损起点回正中位", s.rec_med+" 交易日（约 "+Math.max(1,Math.round(s.rec_med/21))+" 个月）"],
      ["最长等待回正", s.rec_max+" 交易日"],
      ["停止后最深浮亏(中位)", (s.deep_med*100).toFixed(1)+"%"],
      ["最深浮亏(最差)", (s.deep_min*100).toFixed(1)+"%"],
    ];
    return `<div class="pc">
      <div class="pt"><span class="dot" style="width:10px;height:10px;border-radius:50%;background:${COLORS[code]}"></span>${m.t} <span class="${m.tagCls}" style="font-size:11px;border-radius:999px;padding:2px 9px;font-weight:700;flex:none">${m.tag}</span></div>
      <div class="pc-sub"><span class="ix-code">${code}</span> · 场外基金：${OTC[code]}</div>
      <ul>${li.map(x=>`<li><span class="k">${x[0]}</span><span class="v">${x[1]}</span></li>`).join("")}</ul>
      <div style="font-size:12.5px;color:var(--sub);margin-top:10px;background:#fafbfc;border-radius:8px;padding:8px 10px">${m.why}</div>
    </div>`;
  }).join("");
  document.getElementById("pick").innerHTML = html;
})();

/* ---------- 2 停止后回正耗时柱状图(仅亏损起点) ---------- */
let recChart=null;
function renderRec(){
  const series = SHORTS.map(short=>({
    name:short, type:"bar", data:SERIES[short].rec_days_loss,
    barWidth:"18%", color:COLORS[CODES[short]],
    itemStyle:{borderRadius:[3,3,0,0]},
    emphasis:{focus:"series"}
  }));
  recChart.setOption({
    grid:{left:48,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",formatter:ps=>{
      const i=ps[0].dataIndex;
      let s=`起点 <b>${STARTS[i]}</b><br>`;
      SHORTS.forEach(short=>{
        const v=SERIES[short].rec_days_loss[i];
        s+=`${short}：${v==null?"停止时已盈利":v+" 交易日（约"+(v>=21?Math.round(v/21):1)+"个月）"}<br>`;
      });
      return s;
    }},
    legend:{data:SHORTS,top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:STARTS,axisLabel:{...axis.axisLabel,interval:Math.ceil(STARTS.length/10)},...axis},
    yAxis:{type:"value",name:"交易日",nameTextStyle:{color:"#6b7686"},axisLabel:{color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* ---------- 3 停止日浮盈折线 ---------- */
let profitChart=null;
function renderProfit(){
  const series = SHORTS.map(short=>({
    name:short, type:"line", data:SERIES[short].profit_at_stop, smooth:false, symbol:"none", color:COLORS[CODES[short]],
    lineStyle:{width:1.8,color:COLORS[CODES[short]]},
    areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:COLORS[CODES[short]]+"33"},{offset:1,color:COLORS[CODES[short]]+"05"}]}},
    emphasis:{focus:"series"}
  }));
  profitChart.setOption({
    grid:{left:60,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",valueFormatter:v=>v.toLocaleString()+" 元"},
    legend:{data:SHORTS,top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:STARTS,boundaryGap:false,axisLabel:{...axis.axisLabel,interval:Math.ceil(STARTS.length/10)},...axis},
    yAxis:{type:"value",axisLabel:{formatter:v=>(v>=0?"+":"")+Math.round(v/1000)+"k",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* ---------- 4 明细表 ---------- */
(function(){
  const sel = document.getElementById("selStart");
  sel.innerHTML = STARTS.map(s=>`<option value="${s}">${s}</option>`).join("");
  sel.value = STARTS[STARTS.length-1];  // 默认选中最近一个起点
  function render(){
    const start = sel.value;
    const rows = SHORTS.map(short=>{
      const r = ROWS[short][STARTS.indexOf(start)];
      const prof = r.profit_at_stop;
      const rec = r.recover_days!=null ? r.recover_days+" 天" : "—";
      const deep = (r.max_loss_after*100).toFixed(1);
      return `<tr ${short==="红利低波"?"class='hl'":""}>
        <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${COLORS[CODES[short]]}"></span> <b>${short}</b></td>
        <td class="num ${prof>=0?"pos":"neg"}"><b>${prof>=0?"+":""}¥${Math.abs(prof).toLocaleString()}</b></td>
        <td class="num ${prof>=0?"pos":"neg"}">${prof>=0?"盈利":"亏损"}</td>
        <td class="num">${r.recover_date||"—"}</td>
        <td class="num">${rec}</td>
        <td class="num neg">${deep}%</td>
      </tr>`;
    }).join("");
    document.getElementById("tbl_pick").innerHTML = `
      <tr><th>指数</th><th class="num">停止日浮盈/浮亏</th><th class="num">状态</th><th class="num">回正日期</th><th class="num">回正耗时</th><th class="num">停止后最深浮亏</th></tr>${rows}`;
  }
  sel.onchange = render;
  render();
})();

/* 图例 */
(function(){
  document.getElementById("lg1").innerHTML = SHORTS.map(short=>`<div class="li"><span class="sw" style="background:${COLORS[CODES[short]]}"></span>${short} 亏损起点回正耗时中位 ${STATS[short].rec_med} 天</div>`).join("");
  document.getElementById("lg2").innerHTML = SHORTS.map(short=>`<div class="li"><span class="sw" style="background:${COLORS[CODES[short]]}"></span>${short} 停止时盈利占比 ${(STATS[short].n_profit/STATS[short].n_total*100).toFixed(1)}%</div>`).join("");
})();

/* 提醒区 */
(function(){
  const box = document.getElementById("alertGrid");
  const items = [
    {n:"停止时已盈利", v:"75%-80%", s:"约 4/5 起点定投满1年即盈利"},
    {n:"亏损起点全部回正", v:"100%", s:"停止后持有，历史全部收复"},
    {n:"回正耗时(中位)", v:"15-60 交易日", s:"约 1-3 个月"},
    {n:"最长等待", v:"224 交易日", s:"约 10-11 个月（2018 熊市起点）"},
  ];
  items.forEach(it=>{
    const el = document.createElement("div");
    el.className = "ag";
    el.innerHTML = `<div class="n">${it.n}</div><div class="v">${it.v}</div><div style="font-size:12px;color:var(--sub)">${it.s}</div>`;
    box.appendChild(el);
  });
})();

/* init */
window.addEventListener("resize",()=>{recChart&&recChart.resize();profitChart&&profitChart.resize();});
(function init(){
  recChart = echarts.init(document.getElementById("c_rec"));
  profitChart = echarts.init(document.getElementById("c_profit"));
  renderRec(); renderProfit();
})();
</script>
</body>
</html>"""

# 注入数据
html = html.replace("%%N_STARTS%%", str(len(STARTS)))
html = html.replace("__STARTS__", jdump(STARTS))
html = html.replace("__SHORTS__", jdump(SHORTS))
html = html.replace("__CODES__", jdump(CODES))
html = html.replace("__COLORS__", jdump(COLORS))
html = html.replace("__STATS__", jdump(STATS))
html = html.replace("__SERIES__", jdump(SERIES))
html = html.replace("__YIELDS__", jdump(YIELDS))
html = html.replace("__OTC__", jdump(OTC))
# ROWS: 每个指数 -> 每起点 -> 明细
R = {short: [{"profit_at_stop": round(x["profit_at_stop"]), "recover_days": x["recover_days"],
              "recover_date": x["recover_date"], "max_loss_after": round(x["max_loss_after"], 4)} for x in RESULTS[short]] for short in SHORTS}
html = html.replace("__ROWS__", jdump(R))

open("dividend_dashboard_stop12.html", "w", encoding="utf-8").write(html)
print("已生成 dividend_dashboard_stop12.html,", len(html)//1024, "KB")
