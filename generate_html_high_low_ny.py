# -*- coding: utf-8 -*-
"""读 high_low_Ny.json, 生成网页看板：每月最高价/最低价定投对比"""
import json, datetime, sys

if len(sys.argv) != 2:
    print("Usage: python generate_html_high_low_ny.py N")
    print("N: 1, 3, 5, 10")
    sys.exit(1)

years = int(sys.argv[1])
fn = f"high_low_{years}y.json"
r = json.load(open(fn, encoding="utf-8"))
idx = r["indices"]

# 股息率数据(价差法, 近12个月)
YIELDS = {}
for y in json.load(open("dividend_yield.json", encoding="utf-8")):
    YIELDS[y["code"]] = {
        "dy": y["dy_12m_daily"] * 100, "tr": y["tr_ret"] * 100, "pr": y["pr_ret"] * 100,
        "d0": f"{y['d0'][:4]}-{y['d0'][4:6]}-{y['d0'][6:]}", "d1": f"{y['d1'][:4]}-{y['d1'][4:6]}-{y['d1'][6:]}",
        "ldy": y["latest_dy"] * 100, "ld1": f"{y['latest_d1'][:4]}-{y['latest_d1'][4:6]}-{y['latest_d1'][6:]}",
    }

meta = r["meta"]
amount = meta["amount"]
periods = meta["periods"]
total_invest = meta["total_invest"]
start = meta["start"]
end = meta["end"]

amount_wan = int(amount / 10000)
total_invest_wan = int(total_invest / 10000)

title_suffix = f"{years}年回测 · 每月最高价vs最低价定投" if years > 1 else "近1年回测 · 每月最高价vs最低价定投"

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利全收益指数 · TITLE_SUFFIX</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
<script>window.echarts||document.write('<script src="https://cdn.bootcdn.net/ajax/libs/echarts/5.5.0/echarts.min.js"><\\/script>');</script>
<style>
:root{
  --bg:#f4f6fa; --card:#ffffff; --ink:#1a2332; --sub:#6b7686; --line:#e6eaf0;
  --red:#c0392b; --green:#1e8e5a; --accent:#b3372c;
}
*{margin:0;padding:0;box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6}
.wrap{max-width:1120px;margin:0 auto;padding:32px 20px 80px}
/* Hero */
.hero{background:linear-gradient(135deg,#2b3a4a 0%,#1d2939 60%,#3a2a2a 100%);border-radius:18px;color:#fff;padding:38px 40px;position:relative;overflow:hidden}
.hero::after{content:"";position:absolute;right:-60px;top:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.08),transparent 70%)}
.hero .tag{display:inline-block;background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);border-radius:999px;padding:3px 14px;font-size:12.5px;letter-spacing:1px;margin-bottom:14px}
.hero h1{font-size:29px;font-weight:800;letter-spacing:.5px;margin-bottom:10px}
.hero h1 em{font-style:normal;color:#ffb37a}
.hero .sub{font-size:14.5px;color:#c7d2de;max-width:760px}
.hero .rules{display:flex;flex-wrap:wrap;gap:10px;margin-top:20px}
.hero .rule{background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.16);border-radius:10px;padding:7px 14px;font-size:12.8px;color:#e8eef6}
.hero .rule b{color:#ffd28a}
/* Section */
.sec{margin-top:38px}
.sec h2{font-size:21px;font-weight:800;display:flex;align-items:center;gap:10px;margin-bottom:6px}
.sec h2 .no{background:var(--accent);color:#fff;width:28px;height:28px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-size:14px;flex:none}
.sec .desc{color:var(--sub);font-size:13.5px;margin-bottom:18px}
/* Cards */
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}
.cards-2col{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:760px){.cards-2col{grid-template-columns:1fr}}
/* Cards */
.know{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.kn{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.kn h3{font-size:15px;font-weight:800;margin-bottom:10px;display:flex;align-items:center;gap:8px;line-height:1.4}
.kn .ico{width:24px;height:24px;border-radius:7px;display:inline-flex;align-items:center;justify-content:center;font-size:11.5px;color:#fff;flex:none}
.kn p{font-size:13.2px;color:#4a5568;margin-bottom:8px;line-height:1.75}
.kn ul{list-style:none}
.kn li{font-size:13px;padding:7px 0;border-bottom:1px dashed #f1f4f8;line-height:1.6}
.kn li:last-child{border-bottom:none}
.kn li b{color:var(--ink)}
.ix-code{font-family:ui-monospace,Consolas,"SF Mono",monospace;background:#f0f3f8;color:#3a4a5e;padding:2px 8px;border-radius:5px;font-size:12.5px;letter-spacing:.5px;font-weight:700;white-space:nowrap}
.card .top{flex-wrap:wrap;gap:6px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;position:relative;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.card .top{display:flex;align-items:center;gap:8px;margin-bottom:4px}
.card .dot{width:10px;height:10px;border-radius:50%}
.card .nm{font-size:14.5px;font-weight:700}
.card .badge{margin-left:auto;font-size:11px;border-radius:999px;padding:2px 9px;font-weight:700}
.card .badge.win{background:#fdecea;color:var(--red)}
.card .badge.steady{background:#e7f6ee;color:var(--green)}
.card .fval{font-size:27px;font-weight:800;margin:6px 0 2px}
.card .fval small{font-size:13px;color:var(--sub);font-weight:500}
.card .kv{display:grid;grid-template-columns:1fr 1fr;gap:6px 12px;margin-top:10px;border-top:1px dashed var(--line);padding-top:10px}
.card .kv .k{font-size:11.5px;color:var(--sub)}
.card .kv .v{font-size:14px;font-weight:700}
.card .kv .v.pos{color:var(--red)} .card .kv .v.neg{color:var(--green)}
.card .mdd{font-size:12.5px;color:var(--sub);margin-top:10px;background:#fafbfc;border-radius:8px;padding:7px 10px}
/* Table */
.tbl-box{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow-x:auto;overflow-y:hidden;box-shadow:0 1px 3px rgba(20,30,50,.05)}
table{width:100%;border-collapse:collapse;font-size:13.5px;min-width:480px}
th{background:#f8fafc;color:var(--sub);font-weight:600;text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 14px;border-bottom:1px solid #f1f4f8;white-space:nowrap}
.tbl-scroll-hint{display:none;color:var(--sub);font-size:12px;margin:6px 2px 0;text-align:right}
@media(max-width:760px){
  .hero h1{font-size:23px}.hero{padding:28px 22px}
  .know{grid-template-columns:1fr}
  .cards{grid-template-columns:1fr}
  .cards-2col{grid-template-columns:1fr}
  .card .kv{grid-template-columns:1fr}
  th,td{padding:9px 10px;font-size:12.5px}
  .tbl-scroll-hint{display:block}
}
tr:last-child td{border-bottom:none}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
td b{font-weight:700}
.pos{color:var(--red)} .neg{color:var(--green)}
tr.hl td{background:#fffaf7}
.etf{font-size:12px;color:var(--sub)}
/* chart */
.chart{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 14px 10px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.chart .head{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:0 6px 8px}
.chart .head .t{font-size:15px;font-weight:700}
.chart .head .hint{font-size:12px;color:var(--sub)}
.seg{display:inline-flex;background:#eef1f6;border-radius:9px;padding:3px;margin-left:auto}
.seg button{border:none;background:transparent;padding:5px 14px;border-radius:7px;font-size:12.5px;color:var(--sub);cursor:pointer;font-weight:600}
.seg button.on{background:#fff;color:var(--ink);box-shadow:0 1px 3px rgba(20,30,50,.15)}
#c_trend, #c_growth_high, #c_growth_low{width:100%;height:430px}
#c_under_high, #c_under_low{width:100%;height:460px}
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
/* pick */
.pick{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px}
.pick .pc{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 1px 3px rgba(20,30,50,.05)}
.pick .pc .pt{display:flex;align-items:center;gap:8px;font-weight:800;font-size:15.5px;margin-bottom:4px}
.pick .pc .pt .dot{width:10px;height:10px;border-radius:50%}
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
@media(max-width:720px){.hero h1{font-size:23px}.hero{padding:28px 22px}}
</style>
</head>
<body>
<div class="wrap">

<!-- HERO -->
<div class="hero">
  <h1>每月最高价 vs 最低价定投 · 四大红利指数<br><em>TITLE_SUFFIX · 含分红再投 · 真实回撤计算</em></h1>
  <div class="sub">基于中证指数官网全收益指数官方日线（csindex.com.cn），逐日复算 START 至 END  YEARS年定投：每月定投固定金额，分别在当月最高价买入 vs 当月最低价买入，对比终值和年化差异。</div>
  <div class="rules">
    <div class="rule">周期 <b>START - END</b></div>
    <div class="rule">频率 <b>每月定投</b></div>
    <div class="rule">每期 <b>¥AMOUNT</b></div>
    <div class="rule">总投入 <b>¥TOTAL_INVEST_WAN万</b>（PERIODS 期）</div>
    <div class="rule">口径 <b>全收益指数（含分红再投）</b></div>
  </div>
</div>

<!-- 0 背景科普 -->
<div class="sec">
  <h2><span class="no">0</span>为什么比较最高价/最低价定投？</h2>
  <div class="desc">择时定投"等跌了再买"，本质就是想尽量买在当月偏低位置。回测告诉你：YEARS年累计下来影响有多大。</div>
  <div class="know">
    <div class="kn">
      <h3><span class="ico" style="background:#e74c3c">①</span>研究问题</h3>
      <p>同一个月里，你坚定定投 vs 等待下跌再买，<b>最终收益差多少？</b></p>
      <ul>
        <li><b>最高价买入策略</b>：每月定投不等待，不管涨跌都买，永远买在当月最高点</li>
        <li><b>最低价买入策略</b>：每月一直等到最低点才买入，完美择时</li>
        <li>计算YEARS年后的收益、年化、回撤对比</li>
      </ul>
    </div>
    <div class="kn">
      <h3><span class="ico" style="background:#3498db">②</span>结论意义</h3>
      <p>结果告诉我们：<b>"等到跌了再买"这个习惯，长期能多赚多少？</b></p>
      <ul>
        <li>如果价差很大，说明择时确实有价值，值得等</li>
        <li>如果价差很小，说明早点买安心持有更省心</li>
        <li>所有计算基于<b>全收益指数真实日线</b>，不是模拟</li>
      </ul>
    </div>
    <div class="kn">
      <h3><span class="ico" style="background:#27ae60">③</span>四个对比指数</h3>
      <ul>
        <li><b>上证红利全收益</b> <span class="ix-code">H00015</span>：沪市 50 只老牌高股息</li>
        <li><b>中证红利全收益</b> <span class="ix-code">H00922</span>：沪深 100 只主流红利</li>
        <li><b>红利低波全收益</b> <span class="ix-code">H20269</span>：红利低波双因子 50 只</li>
        <li><b>红利低波100全收益</b> <span class="ix-code">H20955</span>：双因子更分散 100 只</li>
      </ul>
      <p style="margin-top:8px;color:var(--sub);font-size:12px">注：都是中证指数官方全收益指数，含分红再投资</p>
    </div>
  </div>
</div>

<!-- 1 总账对比 -->
<div class="sec">
  <h2><span class="no">1</span>总账：最高价 vs 最低价，YEARS年后差多少</h2>
  <div class="desc">每个指数分别展示最高价买入和最低价买入的终值、收益、年化、回撤对比。</div>
  <div class="cards" id="cards"></div>
</div>

<!-- 2 指数走势对比 -->
<div class="sec">
  <h2><span class="no">2</span>指数走势：归一化对比</h2>
  <div class="desc">四个指数从定投起点 START 归一化为 100，走势对比一目了然。颜色统一：红利低波=红、中证红利=蓝、红利低波100=橙、上证红利=绿。</div>
  <div class="card">
    <div id="c_trend"></div>
    <div class="legend" id="lg_trend"></div>
  </div>
</div>

<!-- 3 市值走势：最高价 -->
<div class="sec">
  <h2><span class="no">3</span>定投市值走势（每月最高价买入）</h2>
  <div class="desc">灰线为累计投入本金（阶梯递增）。曲线在大部分年份都压在投入线上方，但 2018 年与 2020 年初会短暂跌破。</div>
  <div class="chart">
    <div class="head"><div class="t">组合市值 vs 累计投入</div><div class="hint">悬浮查看任一时点浮盈/浮亏</div></div>
    <div id="c_growth_high"></div>
    <div class="legend" id="lg_growth_high"></div>
  </div>
</div>

<!-- 4 市值走势：最低价 -->
<div class="sec">
  <h2><span class="no">4</span>定投市值走势（每月最低价买入）</h2>
  <div class="desc">同样显示累计投入本金（灰线阶梯）。可以和最高价走势对比看差异。</div>
  <div class="chart">
    <div class="head"><div class="t">组合市值 vs 累计投入</div><div class="hint">悬浮查看任一时点浮盈/浮亏</div></div>
    <div id="c_growth_low"></div>
    <div class="legend" id="lg_growth_low"></div>
  </div>
</div>

<!-- 4.5 各指数高低价对比 -->
<div class="sec">
  <h2><span class="no">4.5</span>各指数：最高价 vs 最低价 买入曲线对比</h2>
  <div class="desc">每个指数单独展示：蓝色线 = 每月按最低价买入（理想择时），红色线 = 每月按最高价买入（最差择时）。灰线为累计投入本金。</div>
  <div class="cards" id="compareCards" style="grid-template-columns:1fr 1fr;"></div>
</div>

<!-- 5 回撤对比 -->
<div class="sec">
  <h2><span class="no">5</span>真实回撤对比：最高价 vs 最低价</h2>
  <div class="desc">两条口径都要看：① <b>定投组合市值回撤</b>＝每月扣款后账户市值从峰值回落的最大幅度，是定投者真实的浮亏体验；② <b>指数点位回撤</b>＝一次性买入持有的最大跌幅。可点击切换。</div>
  <div class="cards-2col">
    <div class="chart">
      <div class="head">
        <div class="t">最高价买入：水下回撤曲线</div>
        <div class="seg">
          <button id="segPortHigh" class="on">组合市值口径</button>
          <button id="segIdxHigh">指数点位口径</button>
        </div>
      </div>
      <div id="c_under_high"></div>
      <div class="legend" id="lg_under_high"></div>
    </div>
    <div class="chart">
      <div class="head">
        <div class="t">最低价买入：水下回撤曲线</div>
        <div class="seg">
          <button id="segPortLow" class="on">组合市值口径</button>
          <button id="segIdxLow">指数点位口径</button>
        </div>
      </div>
      <div id="c_under_low"></div>
      <div class="legend" id="lg_under_low"></div>
    </div>
  </div>

  <div class="chart" style="margin-top:16px">
    <div class="head"><div class="t">最大回撤对比明细表（组合市值口径）</div></div>
    <div class="tbl-box" style="border:none;box-shadow:none">
    <table id="tbl_mdd"></table>
    </div>
    <div class="tbl-scroll-hint">← 左右滑动查看更多 →</div>
  </div>
</div>

<!-- 6 当前股息率 -->
<div class="sec">
  <h2><span class="no">6</span>当前股息率：仍是国债的 2.4 倍+</h2>
  <div class="desc">下表为四个指数<b>近 12 个月实际分红收益率</b>（用官方全收益指数与价格指数价差计算，真实数据；Wind 同口径 2026-07-31 中证红利 4.24%，交叉验证一致）。</div>
  <div class="cards" id="yieldCards" style="grid-template-columns:1fr 1fr;margin-top:4px"></div>
  <p style="margin-top:10px;color:var(--sub);font-size:12.5px;padding:0 4px">对比：十年期国债收益率约 <b style="color:var(--ink)">1.7%</b>，红利股息率是其 <b>2.4-2.8 倍</b>。注意股息率随价格波动：7 月红利大涨后股息率已从高位回落，4%+ 的"租金"依然稀缺。</p>
</div>

<!-- 7 结论 -->
<div class="sec">
  <h2><span class="no">7</span>结论：择时"等低点"长期效果有多大</h2>
  <div class="desc">YEARS年回测告诉你，每月都能买到最低点这种完美择时，长期到底能多赚多少。</div>
  <div class="pick" id="pick"></div>
  <div class="quote">
    <p>「长期来看，就算你每次都能精准买在当月最低点，比"闭着眼睛买在第一个交易日"年化收益也只高不到 1-6 个百分点。定投最大的收益来自「坚持买入」，而非「买在最低点」。」</p>
    <div class="who">—— 基于中证指数官方全收益日线YEARS年回测</div>
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
  <p>2. <b>定投规则</b>：每月固定投入 AMOUNT 元，分别在当月最高价买入 vs 当月最低价买入；START 首期至 END 末期为 PERIODS 期、总投入 ¥TOTAL_INVEST_WAN万；未计交易费用与税费。</p>
  <p>3. <b>年化收益率</b>：按逐笔现金流 XIRR（资金时间价值口径）计算。</p>
  <p>4. <b>组合市值回撤</b>＝每日（累计份额 × 指数点位）从历史峰值回落的最大幅度；<b>指数点位回撤</b>＝指数点位本身从峰值的最大跌幅；<b>恢复日</b>＝回撤区间内首次收复峰值的日期。</p>
  <p>5. <b>本页对比</b>：同一个定投区间，同一投入金额，只有买入价格不同（最高价 vs 最低价），其余规则一致。收益率与回撤均为百分比口径，与定投金额大小无关（线性缩放）。</p>
  <p class="warn">⚠ 本页为历史数据回测，不代表未来收益。红利策略亦存在长期跑输与估值回归风险。投资有风险，决策需谨慎。</p>
</div>

</div>

<script>
const INDICES = __INDICES__;
const COLORS = {H00015:"#27ae60", H00922:"#3498db", H20269:"#e74c3c", H20955:"#e67e22"};
const SHORT  = {H00015:"上证红利", H00922:"中证红利", H20269:"红利低波", H20955:"红利低波100"};
const CODES  = ["H00015","H00922","H20269","H20955"];
const YIELDS = __YIELDS__;

const fonts = {color: "#6b7686", fontFamily: "inherit"};

/* ---------- 延迟顺序渲染队列 ---------- */
const __chartTasks = [];
setTimeout(function(){
	  function __run(i){ if(i < __chartTasks.length) { try{ __chartTasks[i](); }catch(e){} setTimeout(()=>__run(i+1), 80); } }
	  __run(0);
	}, 100);

/* ---------- 趋势图 ---------- */
(function(){
  const box = document.getElementById("cards");
  INDICES.forEach((it)=>{
    const h = it.high;
    const l = it.low;
    const diff = (l.cagr - h.cagr) * 100;
    const c = COLORS[it.code];
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="top"><span class="dot" style="background:${c}"></span><span class="nm">${it.name}</span><span class="ix-code">${it.code}</span></div>
      <div class="cards-2col" style="gap:10px">
        <div>
          <div class="fval">¥${h.final_value.toLocaleString()} <small>最高价买入终值</small></div>
          <div class="kv">
            <div><div class="k">总投入</div><div class="v">¥${h.total_invest.toLocaleString()}</div></div>
            <div><div class="k">总收益</div><div class="v pos">${(h.total_ret*100).toFixed(2)}%</div></div>
            <div><div class="k">年化</div><div class="v pos">${(h.cagr*100).toFixed(2)}%</div></div>
            <div><div class="k">最大回撤</div><div class="v pos">${(h.mdd_port.pct*100).toFixed(2)}%</div></div>
          </div>
        </div>
        <div>
          <div class="fval">¥${l.final_value.toLocaleString()} <small>最低价买入终值</small></div>
          <div class="kv">
            <div><div class="k">年化差</div><div class="v pos">+${diff.toFixed(2)}%</div></div>
            <div><div class="k">总收益</div><div class="v pos">${(l.total_ret*100).toFixed(2)}%</div></div>
            <div><div class="k">年化</div><div class="v pos">${(l.cagr*100).toFixed(2)}%</div></div>
            <div><div class="k">最大回撤</div><div class="v pos">${(l.mdd_port.pct*100).toFixed(2)}%</div></div>
          </div>
        </div>
      </div>
      <div class="mdd">最大回撤（组合市值口径）：最高价 ${(h.mdd_port.pct*100).toFixed(2)}% / 最低价 ${(l.mdd_port.pct*100).toFixed(2)}%</div>
    `;
    box.appendChild(el);
  });
})();

/* ---------- 股息率卡片 ---------- */
(function(){
  const box = document.getElementById("yieldCards");
  CODES.forEach(c=>{
    const y = YIELDS[c];
    const color = COLORS[c];
    const name = SHORT[c];
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="top"><span class="dot" style="background:${color}"></span><span class="nm">${name}</span><span class="ix-code">${c}</span></div>
      <div style="font-size:24px;font-weight:700;color:#e74c3c">${y.ldy.toFixed(2)}%</div>
      <div style="font-size:12px;color:var(--sub);margin-top:2px">最新股息率（截至 ${y.ld1}）</div>
      <div style="font-size:12px;color:var(--sub);margin-top:2px">近12个月实际分红收益率（${y.d0} ~ ${y.d1}）</div>
      <div style="font-size:11.5px;color:var(--sub);margin-top:8px;background:#fafbfc;border-radius:8px;padding:6px 8px">同期全收益 ${y.tr.toFixed(1)}% ｜ 价格 ${y.pr.toFixed(1)}%</div>
    `;
    box.appendChild(el);
  });
})();

/* ---------- 趋势图 (延迟渲染) ---------- */
__chartTasks.push(function(){
  const chart = echarts.init(document.getElementById('c_trend'));
  const baseMap = {};
  INDICES.forEach(it=>{
    const first = it.high.plot.value[0];
    baseMap[it.code] = first;
  });
  const option = {
    animation: false,
    tooltip:{trigger:"axis",backgroundColor:"rgba(29,41,57,.92)",borderWidth:0,textStyle:{color:"#fff",fontSize:12},valueFormatter:v=>v==null?"-":v.toFixed(1)},
    legend:{data:CODES.map(c=>SHORT[c]),top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:INDICES[0].high.plot.dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:11},axisTick:{show:false}},
    yAxis:{type:"value",scale:true,axisLabel:{formatter:"{value}",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef2f7"}}},
    series:CODES.map(c=>{
      const idx = INDICES.find(x=>x.code===c);
      const data = idx.high.plot.value.map((v,i)=>(v / baseMap[c] * 100).toFixed(1));
      return {name:SHORT[c],type:"line",showSymbol:false,smooth:false,data,lineStyle:{width:2,color:COLORS[c]},itemStyle:{color:COLORS[c]}};
    }),
  };
  chart.setOption(option);
  window.addEventListener('resize', ()=>chart.resize());
  document.getElementById("lg_trend").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]}</div>`).join("");
});

/* ---------- 市值走势: 最高价 (延迟渲染) ---------- */
__chartTasks.push(function(){
  const chart = echarts.init(document.getElementById('c_growth_high'));
  const series = INDICES.map(it=>({
    name:SHORT[it.code] + "(最高价)", type:"line", data:it.high.plot.value, smooth:false, symbol:"none", lineStyle:{width:2,color:COLORS[it.code]}, itemStyle:{color:COLORS[it.code]}
  }));
  series.push({name:"累计投入",type:"line",data:INDICES[0].high.plot.invested,smooth:false,symbol:"none",lineStyle:{width:1.6,type:"dashed",color:"#9aa7b8"},itemStyle:{color:"#9aa7b8",opacity:.55}});
  const option = {
    animation: false,
    tooltip:{trigger:"axis",backgroundColor:"rgba(29,41,57,.92)",borderWidth:0,textStyle:{color:"#fff",fontSize:12},valueFormatter:v=>v==null?"-":"¥"+Math.round(v).toLocaleString()},
    legend:{data:[...INDICES.map(it=>SHORT[it.code]+"(最高价)"),"累计投入"],top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect",itemWidth:18,itemHeight:8},
    xAxis:{type:"category",data:INDICES[0].high.plot.dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:11},axisTick:{show:false}},
    yAxis:{type:"value",axisLabel:{formatter:v=>v>=10000?(v/10000).toFixed(1)+"万":v,color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  };
  chart.setOption(option);
  window.addEventListener('resize', ()=>chart.resize());
  document.getElementById("lg_growth_high").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]}（最高价）（终值 ¥${INDICES.find(i=>i.code===c).high.final_value.toLocaleString()}）</div>`).join("");
});

/* ---------- 市值走势: 最低价 (延迟渲染) ---------- */
__chartTasks.push(function(){
  const chart = echarts.init(document.getElementById('c_growth_low'));
  const series = INDICES.map(it=>({
    name:SHORT[it.code] + "(最低价)", type:"line", data:it.low.plot.value, smooth:false, symbol:"none", lineStyle:{width:2,color:COLORS[it.code]}, itemStyle:{color:COLORS[it.code]}
  }));
  series.push({name:"累计投入",type:"line",data:INDICES[0].low.plot.invested,smooth:false,symbol:"none",lineStyle:{width:1.6,type:"dashed",color:"#9aa7b8"},itemStyle:{color:"#9aa7b8",opacity:.55}});
  const option = {
    animation: false,
    tooltip:{trigger:"axis",backgroundColor:"rgba(29,41,57,.92)",borderWidth:0,textStyle:{color:"#fff",fontSize:12},valueFormatter:v=>v==null?"-":"¥"+Math.round(v).toLocaleString()},
    legend:{data:[...INDICES.map(it=>SHORT[it.code]+"(最低价)"),"累计投入"],top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect",itemWidth:18,itemHeight:8},
    xAxis:{type:"category",data:INDICES[0].low.plot.dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:11},axisTick:{show:false}},
    yAxis:{type:"value",axisLabel:{formatter:v=>v>=10000?(v/10000).toFixed(1)+"万":v,color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  };
  chart.setOption(option);
  window.addEventListener('resize', ()=>chart.resize());
  document.getElementById("lg_growth_low").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]}（最低价）（终值 ¥${INDICES.find(i=>i.code===c).low.final_value.toLocaleString()}）</div>`).join("");
});

/* ---------- 各指数高低价对比图 (延迟渲染) ---------- */
__chartTasks.push(function(){
  const box = document.getElementById("compareCards");
  CODES.forEach(c=>{
    const idx = INDICES.find(x=>x.code===c);
    const color = COLORS[c];
    const name = SHORT[c];
    const card = document.createElement("div");
    card.className = "card";
    card.style.padding = "14px 14px 10px";
    card.innerHTML = `<div class="top"><span class="dot" style="background:${color}"></span><span class="nm">${name}</span><span class="ix-code">${c}</span></div><div id="cmp_${c}" style="width:100%;height:320px"></div>`;
    box.appendChild(card);

    const chart = echarts.init(document.getElementById("cmp_"+c));
    const dates = idx.high.plot.dates;
    const hData = idx.high.plot.value;
    const lData = idx.low.plot.value;
    const invested = idx.high.plot.invested;

    // 年化差
    const diff = ((idx.low.cagr - idx.high.cagr) * 100).toFixed(2);

    const option = {
      animation: false,
      tooltip:{
        trigger:"axis",
        backgroundColor:"rgba(29,41,57,.92)",
        borderWidth:0,
        textStyle:{color:"#fff",fontSize:12},
        valueFormatter:v=>v==null?"-":"¥"+Math.round(v).toLocaleString()
      },
      legend:{data:["最高价买入","最低价买入","累计投入"],top:0,textStyle:{fontSize:11,color:"#6b7686"},icon:"roundRect",itemWidth:14,itemHeight:6},
      xAxis:{type:"category",data:dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:10},axisTick:{show:false}},
      yAxis:{type:"value",axisLabel:{formatter:v=>v>=10000?(v/10000).toFixed(0)+"万":v,color:"#6b7686",fontSize:10},splitLine:{lineStyle:{color:"#eef1f6"}}},
      series:[
        {name:"最高价买入",type:"line",data:hData,smooth:false,symbol:"none",lineStyle:{width:1.8,color:"#e74c3c"},itemStyle:{color:"#e74c3c"}},
        {name:"最低价买入",type:"line",data:lData,smooth:false,symbol:"none",lineStyle:{width:1.8,color:"#3498db"},itemStyle:{color:"#3498db"}},
        {name:"累计投入",type:"line",data:invested,smooth:false,symbol:"none",lineStyle:{width:1.3,type:"dashed",color:"#9aa7b8"},itemStyle:{color:"#9aa7b8",opacity:.5}}
      ],
      grid:{top:36,bottom:20,left:50,right:16}
    };
    chart.setOption(option);
    window.addEventListener('resize', ()=>chart.resize());
  });
});

/* ---------- 回撤图: 最高价 (延迟渲染) ---------- */
__chartTasks.push(function(){
  let underMode = "port";
  const chart = echarts.init(document.getElementById('c_under_high'));

  function render(){
    const series = CODES.map(c=>{
      const idx = INDICES.find(x=>x.code===c);
      const data = underMode === "port" ? idx.high.underwater_port.dd : idx.high.underwater_index.dd;
      const dates = underMode === "port" ? idx.high.underwater_port.dates : idx.high.underwater_index.dates;
      return {
        name:SHORT[c], type:"line", data:data, smooth:false, symbol:"none", color:COLORS[c],
        lineStyle:{width:1.8,color:COLORS[c]},
        areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:COLORS[c]+"55"},{offset:1,color:COLORS[c]+"08"}]}},
        emphasis:{focus:"series"},
        markPoint:{symbol:"pin",symbolSize:44,symbolOffset:[c==="H00015"?-14:(c==="H20269"?14:0),0],
          data:[{coord:[data.indexOf(Math.min(...data)), Math.min(...data)],value:(Math.min(...data)*100).toFixed(2)+"%",label:{fontSize:11,color:"#fff"}}],
          itemStyle:{color:COLORS[c]}
        }
      };
    });
    const option = {
      animation: false,
      tooltip:{trigger:"axis",backgroundColor:"rgba(29,41,57,.92)",borderWidth:0,textStyle:{color:"#fff",fontSize:12},valueFormatter:v=>v==null?"-":(v*100).toFixed(2)+"%"},
      legend:{data:CODES.map(c=>SHORT[c]),top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
      xAxis:{type:"category",data:INDICES[0].high[underMode === "port" ? "underwater_port" : "underwater_index"].dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:11},axisTick:{show:false}},
      yAxis:{type:"value",max:0,min:underMode==="port"?-0.20:-0.32,axisLabel:{formatter:v=>(v*100).toFixed(0)+"%",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
      series
    };
    chart.setOption(option);
    document.getElementById("lg_under_high").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]} 最大回撤 ${(Math.min(...INDICES.find(i=>i.code===c).high[underMode === "port" ? "underwater_port" : "underwater_index"].dd)*100).toFixed(2)}%</div>`).join("");
  }
  render();
  window.addEventListener('resize', ()=>chart.resize());
  document.getElementById("segPortHigh").addEventListener("click", function(){
    underMode = "port"; this.classList.add("on"); document.getElementById("segIdxHigh").classList.remove("on"); render();
  });
  document.getElementById("segIdxHigh").addEventListener("click", function(){
    underMode = "idx"; this.classList.add("on"); document.getElementById("segPortHigh").classList.remove("on"); render();
  });
});

/* ---------- 回撤图: 最低价 (延迟渲染) ---------- */
__chartTasks.push(function(){
  let underMode = "port";
  const chart = echarts.init(document.getElementById('c_under_low'));

  function render(){
    const series = CODES.map(c=>{
      const idx = INDICES.find(x=>x.code===c);
      const data = underMode === "port" ? idx.low.underwater_port.dd : idx.low.underwater_index.dd;
      const dates = underMode === "port" ? idx.low.underwater_port.dates : idx.low.underwater_index.dates;
      return {
        name:SHORT[c], type:"line", data:data, smooth:false, symbol:"none", color:COLORS[c],
        lineStyle:{width:1.8,color:COLORS[c]},
        areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:COLORS[c]+"55"},{offset:1,color:COLORS[c]+"08"}]}},
        emphasis:{focus:"series"},
        markPoint:{symbol:"pin",symbolSize:44,symbolOffset:[c==="H00015"?-14:(c==="H20269"?14:0),0],
          data:[{coord:[data.indexOf(Math.min(...data)), Math.min(...data)],value:(Math.min(...data)*100).toFixed(2)+"%",label:{fontSize:11,color:"#fff"}}],
          itemStyle:{color:COLORS[c]}
        }
      };
    });
    const option = {
      animation: false,
      tooltip:{trigger:"axis",backgroundColor:"rgba(29,41,57,.92)",borderWidth:0,textStyle:{color:"#fff",fontSize:12},valueFormatter:v=>v==null?"-":(v*100).toFixed(2)+"%"},
      legend:{data:CODES.map(c=>SHORT[c]),top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
      xAxis:{type:"category",data:INDICES[0].low[underMode === "port" ? "underwater_port" : "underwater_index"].dates,axisLine:{lineStyle:{color:"#ccd4de"}},axisLabel:{color:"#6b7686",fontSize:11},axisTick:{show:false}},
      yAxis:{type:"value",max:0,min:underMode==="port"?-0.20:-0.32,axisLabel:{formatter:v=>(v*100).toFixed(0)+"%",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
      series
    };
    chart.setOption(option);
    document.getElementById("lg_under_low").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]} 最大回撤 ${(Math.min(...INDICES.find(i=>i.code===c).low[underMode === "port" ? "underwater_port" : "underwater_index"].dd)*100).toFixed(2)}%</div>`).join("");
  }
  render();
  window.addEventListener('resize', ()=>chart.resize());
  document.getElementById("segPortLow").addEventListener("click", function(){
    underMode = "port"; this.classList.add("on"); document.getElementById("segIdxLow").classList.remove("on"); render();
  });
  document.getElementById("segIdxLow").addEventListener("click", function(){
    underMode = "idx"; this.classList.add("on"); document.getElementById("segPortLow").classList.remove("on"); render();
  });
});

/* ---------- 回撤表格 ---------- */
(function(){
  const tbl = document.getElementById("tbl_mdd");
  let html = `<thead><tr>
    <th>指数</th><th>策略</th><th>最大回撤</th><th>峰值日期</th><th>谷底日期</th><th>峰值市值</th><th>谷底市值</th><th>浮亏金额</th><th>恢复日期</th>
  </tr></thead><tbody>`;
  INDICES.forEach(it=>{
    [it.high, it.low].forEach(s=>{
      const m = s.mdd_port;
      const loss = m.peak_value - m.trough_value;
      html += `<tr class="${m.pct < -0.15 ? 'hl' : ''}">
        <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${COLORS[it.code]}"></span> <b>${it.short}</b> <span style="color:var(--sub);font-size:11px">${it.code}</span></td>
        <td>${s.label}</td>
        <td class="num"><b>${(m.pct*100).toFixed(2)}%</b></td>
        <td>${m.peak_date}</td>
        <td>${m.trough_date}</td>
        <td class="num">¥${m.peak_value.toLocaleString()}</td>
        <td class="num">¥${m.trough_value.toLocaleString()}</td>
        <td class="num pos">¥${loss.toLocaleString()}</td>
        <td>${m.recover_date || '<span style="color:var(--sub)">未恢复</span>'}</td>
      </tr>`;
    });
  });
  html += `</tbody>`;
  tbl.innerHTML = html;
})();

/* ---------- 结论卡片 ---------- */
(function(){
  const box = document.getElementById("pick");
  INDICES.forEach(it=>{
    const h = it.high;
    const l = it.low;
    const diff = (l.cagr - h.cagr) * 100;
    const c = COLORS[it.code];
    const el = document.createElement("div");
    el.className = "pc";
    el.innerHTML = `
      <div class="pt"><span class="dot" style="background:${c};width:10px;height:10px;border-radius:50%"></span>${it.short} <span style="color:var(--sub);font-size:11px;font-weight:400">${it.code}</span> <span class="pc-tag">${diff>0?"+":""}${diff.toFixed(1)}%</span></div>
      <div class="pc-sub">年化差异（最低价买入 vs 最高价买入）</div>
      <ul>
        <li><div class="k">最高价买入年化</div><div class="v">${(h.cagr*100).toFixed(2)}%</div></li>
        <li><div class="k">最低价买入年化</div><div class="v">${(l.cagr*100).toFixed(2)}%</div></li>
        <li><div class="k">最高价终值</div><div class="v">¥${h.final_value.toLocaleString()}</div></li>
        <li><div class="k">最低价终值</div><div class="v">¥${l.final_value.toLocaleString()}</div></li>
        <li><div class="k">最高价最大回撤</div><div class="v">${(h.mdd_port.pct*100).toFixed(2)}%</div></li>
        <li><div class="k">最低价最大回撤</div><div class="v">${(l.mdd_port.pct*100).toFixed(2)}%</div></li>
      </ul>
    `;
    box.appendChild(el);
  });
})();
</script>
</body>
</html>
"""

# 替换占位符
html = html.replace("TITLE_SUFFIX", title_suffix)
html = html.replace("START", start)
html = html.replace("END", end)
html = html.replace("YEARS", str(years))
html = html.replace("AMOUNT", f"{amount:,}")
html = html.replace("PERIODS", str(periods))
html = html.replace("TOTAL_INVEST_WAN", str(total_invest_wan))

html = html.replace("__INDICES__", jdump(idx))
html = html.replace("__YIELDS__", jdump(YIELDS))

outname = f"dividend_high_low_monthly_{years}y.html"
with open(outname, "w", encoding="utf-8") as f:
    f.write(html)
print(f"已生成 {outname}")
