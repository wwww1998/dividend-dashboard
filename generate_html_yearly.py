# -*- coding: utf-8 -*-
"""读 result.json, 生成 dividend_dashboard.html 网页看板"""
import json, datetime

r = json.load(open("result_yearly.json", encoding="utf-8"))
idx = r["indices"]

# 股息率数据(价差法, 近12个月)
YIELDS = {}
for y in json.load(open("dividend_yield.json", encoding="utf-8")):
    YIELDS[y["code"]] = {
        "dy": y["dy_12m_daily"] * 100, "tr": y["tr_ret"] * 100, "pr": y["pr_ret"] * 100,
        "d0": f"{y['d0'][:4]}-{y['d0'][4:6]}-{y['d0'][6:]}", "d1": f"{y['d1'][:4]}-{y['d1'][4:6]}-{y['d1'][6:]}",
    }

# 年度涨跌对比矩阵(4指数 x 11年)
ANNUAL_GRID = {}
for it in idx:
    for a in it["annual"]:
        ANNUAL_GRID.setdefault(a["year"], {})[it["code"]] = a.get("idx_ret", 0)
DATES = idx[0]["plot"]["dates"]

# 精简序列
SERIES = {}
for it in idx:
    SERIES[it["code"]] = {
        "name": it["name"], "short": it["short"], "otc": it["otc"],
        "value": it["plot"]["value"],
        "invested": it["plot"]["invested"],
        "ddPort": it["underwater_port"]["dd"],
        "ddIdx": it["underwater_index"]["dd"],
    }

# 卡片/表格数据
CARDS = []
for it in idx:
    m = it["mdd_port"]
    mi = it["mdd_index_10y"]
    def days(a, b):
        if not a or not b: return None
        return (datetime.date(*map(int, b.split("-"))) - datetime.date(*map(int, a.split("-")))).days
    # 组合回撤: 峰值->谷底 天数; 峰值->恢复 天数
    trough_days = days(m["peak_date"], m["trough_date"])
    recover_days = days(m["peak_date"], m["recover_date"])
    index_recover_days = days(mi["peak_date"], mi["recover_date"])
    CARDS.append({
        "code": it["code"], "name": it["name"], "short": it["short"], "otc": it["otc"],
        "final_value": round(it["final_value"]), "total_ret": it["total_ret"] * 100,
        "cagr": it["cagr"] * 100, "profit": round(it["final_value"] - it["total_invest"]),
        # 组合口径回撤
        "mdd_p": m["pct"] * 100, "mdd_p_peak": m["peak_date"], "mdd_p_peak_v": round(m["peak_value"]),
        "mdd_p_trough": m["trough_date"], "mdd_p_trough_v": round(m["trough_value"]),
        "mdd_p_amt": round(m["peak_value"] - m["trough_value"]),
        "mdd_p_recover": m["recover_date"], "mdd_p_trough_days": trough_days, "mdd_p_recover_days": recover_days,
        # 指数口径10年
        "mdd_i": mi["pct"] * 100, "mdd_i_peak": mi["peak_date"], "mdd_i_trough": mi["trough_date"],
        "mdd_i_recover": mi["recover_date"], "mdd_i_recover_days": index_recover_days,
        # 当前股息率
        "dy": round(YIELDS[it["code"]]["dy"], 2),
        # 年度
        "annual": [{"y": a["year"], "inv": round(a["invested"]), "val": round(a["value"]),
                    "profit": round(a["profit"]), "yr": round(a.get("yr_profit") or 0),
                    "idx": a.get("idx_ret", 0)} for a in it["annual"]],
    })

def jdump(o):
    return json.dumps(o, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>四大红利全收益指数 · 10年定投真实回撤回测</title>
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
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
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
.tbl-box{background:var(--card);border:1px solid var(--line);border-radius:14px;overflow:hidden;box-shadow:0 1px 3px rgba(20,30,50,.05)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
th{background:#f8fafc;color:var(--sub);font-weight:600;text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:11px 14px;border-bottom:1px solid #f1f4f8;white-space:nowrap}
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
#c_under,#c_growth,#c_annual{width:100%;height:430px}
#c_under{height:460px}
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
  <div class="tag">真实数据复算 · 非转载</div>
  <h1>每年年初定投 %%AMOUNT%% 元红利指数，10 年后能赚多少？<br><em>四大红利全收益指数 · 真实回撤回测</em></h1>
  <div class="sub">基于中证指数官网全收益指数官方日线（csindex.com.cn），逐日复算 2017-01 至 2026-07 十年定投：每年年初（1 月首个交易日）买入 %%AMOUNT%% 元，共 %%PERIODS%% 期、累计投入 ¥%%TOTAL%%。重点还原每个指数的<b style="color:#ffb37a">真实回撤</b>——包括定投组合的实际浮亏与恢复耗时。</div>
  <div class="rules">
    <div class="rule">周期 <b>2016.07 - 2026.07</b></div>
    <div class="rule">频率 <b>每年年初（1 月首个交易日）</b></div>
    <div class="rule">每期 <b>¥%%AMOUNT%%</b></div>
    <div class="rule">总投入 <b>¥%%TOTAL%%</b>（%%PERIODS%% 期）</div>
    <div class="rule">口径 <b>全收益指数（含分红再投）</b></div>
  </div>
</div>

<!-- 0 背景科普 -->
<div class="sec">
  <h2><span class="no">0</span>红利指数基金是什么？为什么买？</h2>
  <div class="desc">先搞懂三件事，再看上面的回撤数据才有意义。</div>
  <div class="know">
    <div class="kn">
      <h3><span class="ico" style="background:#3498db">①</span>是什么：一篮子"爱分红的好公司"</h3>
      <p>红利指数基金＝跟踪<b>红利指数</b>的基金（场内 ETF 或场外联接基金）。红利指数从股市里挑出一批<b>股息率高、分红稳定</b>的股票，按股息率加权——你买的不是一只股票，而是"高股息组合"，每年收到成分公司的现金分红。四个主流红利指数的<b>全收益代码</b>：</p>
      <ul>
        <li><b>上证红利全收益</b> <span class="ix-code">H00015</span>：沪市 50 只，老牌</li>
        <li><b>中证红利全收益</b> <span class="ix-code">H00922</span>：沪深两市 100 只，最主流</li>
        <li><b>红利低波全收益</b> <span class="ix-code">H20269</span>：沪深 50 只，股息＋低波动双因子</li>
        <li><b>红利低波100全收益</b> <span class="ix-code">H20955</span>：沪深 100 只，双因子更分散</li>
      </ul>
    </div>
    <div class="kn">
      <h3><span class="ico" style="background:#e67e22">②</span>为什么买：三条获利逻辑</h3>
      <ul>
        <li><b>每年收"租"（现金分红）</b>：当前股息率约 4%-5%，1 万本金每年约 400-500 元现金分红，远超十年国债（约 1.7%）与银行理财。</li>
        <li><b>复利滚雪球（分红再投资＋定投）</b>：分红再买份额、跌时定投买更多份额，份额越滚越多。回测里 10 年 %%INVEST_WAN%% 变 %%FINAL_BEST_WAN%%（红利低波），一半收益来自"低点坚持买入积累的份额"。</li>
        <li><b>防御性（低波动抗跌）</b>：成分股多为银行、煤炭、石化、交运龙头，盈利稳定。10 年定投最大回撤仅 -11.6%~-17.1%，比大盘温和。</li>
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

<!-- 1 总账 -->
<div class="sec">
  <h2><span class="no">1</span>总账：四个指数全部盈利</h2>
  <div class="desc">年化 %%CAGR_RANGE%% 不等，最低也跑赢银行理财。但回撤差异显著——最大回撤（定投组合市值口径）从 %%MDD_RANGE%% 不等，这正是持有体验的分水岭。<span style="color:var(--sub)">（* 股息率为近 12 个月实际分红收益率，价差法计算，Wind 同口径交叉验证一致）</span></div>
  <div class="cards" id="cards"></div>
</div>

<!-- 2 真实回撤 -->
<div class="sec">
  <h2><span class="no">2</span>真实回撤：你实际会浮亏多少、亏多久</h2>
  <div class="desc">两条口径都要看：① <b>定投组合市值回撤</b>＝每年扣款后账户市值从峰值回落的最大幅度，是定投者真实的浮亏体验；② <b>指数点位回撤</b>＝一次性买入持有的最大跌幅。左图默认展示组合口径，可切换。</div>

  <div class="chart">
    <div class="head">
      <div class="t">水下回撤曲线（Underwater Chart）</div>
      <div class="hint">曲线越深＝浮亏越大；标注点为各自最大回撤谷底</div>
      <div class="seg">
        <button id="segPort" class="on">组合市值口径</button>
        <button id="segIdx">指数点位口径</button>
      </div>
    </div>
    <div id="c_under"></div>
    <div class="legend" id="lg1"></div>
  </div>

  <div class="chart" style="margin-top:16px">
    <div class="head"><div class="t">定投组合最大回撤明细（组合市值口径）</div></div>
    <div class="tbl-box" style="border:none;box-shadow:none">
    <table id="tbl_mdd"></table>
    </div>
  </div>

  <div class="alert">
    <div class="t">⚠ 持有体验提醒：2016 年以来最深的坑在哪</div>
    <div class="b">定投区间内最深的坑是 <b>2018 年熊市</b>（指数口径最大回撤 %%MDD_IDX_RANGE%%）与 <b>2021 年 9-11 月红利行情回落</b>（组合口径浮亏 %%MDD_AMT_RANGE%% 元）。定投通过持续买入摊低成本，把这些坑填浅了一大半——但请记住：回撤是红利策略的固有属性，不是 bug。</div>
    <div class="alert-grid" id="alertGrid"></div>
  </div>
</div>

<!-- 3 市值走势 -->
<div class="sec">
  <h2><span class="no">3</span>定投市值走势：%%INVEST_WAN%% 如何滚成 %%FINAL_WAN_RANGE%%</h2>
  <div class="desc">灰线为累计投入本金（阶梯至 %%TOTAL%%）。曲线在大部分年份都压在投入线上方，但 2018 年与 2020 年初会短暂跌破——"亏钱时咬牙继续投"正是收益的主要来源。</div>
  <div class="chart">
    <div class="head"><div class="t">组合市值 vs 累计投入</div><div class="hint">悬浮查看任一时点浮盈/浮亏</div></div>
    <div id="c_growth"></div>
    <div class="legend" id="lg2"></div>
  </div>
</div>

<!-- 4 年度 -->
<div class="sec">
  <h2><span class="no">4</span>年度表现：哪几年在"打折进货"</h2>
  <div class="desc">下拉切换指数。红色柱＝年末账户浮盈，绿色柱＝年末浮亏（2018 年四个指数全部浮亏，正是摊低成本的黄金期）。<b>「指数年度涨跌幅」＝该指数全收益口径自然年涨幅</b>，用来对照"账户当年盈亏有多少来自指数本身、多少来自定投摊低成本"。</div>
  <div class="chart">
    <div class="head">
      <div class="t">每年末：账户浮盈/浮亏</div>
      <div class="hint">口径＝年末市值 − 当年已投入本金（2026 行为截至 2026-07-31）</div>
      <select id="selYear" style="margin-left:auto;padding:5px 10px;border:1px solid var(--line);border-radius:8px;font-size:12.5px;background:#fff"></select>
    </div>
    <div id="c_annual"></div>
    <div class="tbl-box" style="border:none;box-shadow:none;margin-top:6px">
    <table id="tbl_annual"></table>
    </div>
  </div>
</div>

<!-- 5 结论 -->
<div class="sec">
  <!-- 5 指数年度涨跌幅 -->
<div class="sec">
  <h2><span class="no">5</span>指数年度涨跌幅：四指数横向对比</h2>
  <div class="desc">各指数年度涨跌幅（<b>全收益口径</b>，含分红再投）。自然年口径（上年末→本年末）；2026 行为截至 2026-07-31（非完整年度）。红涨绿跌（A 股习惯）。</div>
  <div class="tbl-box" style="overflow-x:auto">
    <table id="tbl_yoy" style="min-width:560px"></table>
  </div>
</div>

<!-- 6 那到底选哪个 -->
  <h2><span class="no">6</span>那到底选哪个？</h2>
  <div class="desc">回撤数据是选择的钥匙：收益相近时，回撤更小、恢复更快的指数持有体验更好，也更可能坚持到底。</div>
  <div class="pick" id="pick"></div>
  <div class="quote">
    <p>「10 年定投的最大考验从来不是选哪个指数，而是在账面浮亏十几万的那几个月里，你能不能继续投下去。定投最大的敌人不是市场，是你自己。」</p>
    <div class="who">—— 回撤是策略的属性，坚持是唯一的策略</div>
  </div>
</div>

<!-- foot -->
<div class="foot">
  <h3>口径与方法说明</h3>
  <p>1. <b>数据源</b>：中证指数官网（csindex.com.cn）官方日线行情，全收益指数（含分红再投资），四个指数：H00015 上证红利、H00922 中证红利、H20269 红利低波、H20955 红利低波100 全收益。页面推荐产品均为<b>场外联接基金（A/C 类）</b>，可定投：A 类收申购费（长期持有更省），C 类免申购费但按日计提销售服务费（短期持有更省）。</p>
  <p>2. <b>定投规则</b>：每年年初（1 月首个交易日）按当日收盘价买入 %%AMOUNT%% 元；2017-01 首期至 2026-01 末期为 %%PERIODS%% 期、总投入 ¥%%TOTAL%%；未计交易费用与税费。</p>
  <p>3. <b>年化收益率</b>：按逐笔现金流 XIRR（资金时间价值口径）计算。</p>
  <p>4. <b>组合市值回撤</b>＝每日（累计份额 × 指数点位）从历史峰值回落的最大幅度；<b>指数点位回撤</b>＝指数点位本身从峰值的最大跌幅；<b>恢复日</b>＝回撤区间内首次收复峰值的日期。</p>
  <p>5. <b>口径说明</b>：本页按月定投 ¥%%AMOUNT%% 复算，共 %%PERIODS%% 期、总投入 ¥%%TOTAL%%；收益率与回撤均为百分比口径，与定投金额大小无关（线性缩放）。回测采用中证指数官网全收益指数真实日线、精确到每年年初（1 月首个交易日）收盘价买入，未计交易费用与税费。<b>组合市值口径最大回撤四项：%%MDD_LIST%%</b>。</p>
  <p>6. <b>当前股息率</b>：近 12 个月实际分红收益率，用官方全收益指数与价格指数的日收益差累计（价差法·逐日口径）计算（%%DY_RANGE%%），与 Wind 披露 TTM 股息率交叉验证一致（如中证红利 4.24%，2026-07-31）；逐日口径与首尾法结果差异通常小于 0.3pct。</p>
  <p>7. <b>年度表现口径</b>：年末浮盈＝年末市值−累计投入；当年盈亏＝年末市值−上年末市值−当年投入；2026 行为截至 2026-07-31（回测区间末），非完整年度。</p>
  <p class="warn">⚠ 本页为历史数据回测，不代表未来收益。红利策略亦存在长期跑输与估值回归风险。投资有风险，决策需谨慎。</p>
</div>

<!-- CTA -->
<div class="cta">
  <p>如需获取更多定投策略参考、同步市场变化相关观察，<b>可联系我开户</b></p>
  <div class="sub">业务收入支撑日常数据与内容维护，感谢支持。投资有风险，入市需谨慎。</div>
</div>

</div>

<script>
const DATES = __DATES__;
const SERIES = __SERIES__;
const CARDS = __CARDS__;
const YIELDS = __YIELDS__;
const ANNUAL_GRID = __ANNUAL_GRID__;

const COLORS = {H00015:"#e67e22", H00922:"#3498db", H20269:"#e74c3c", H20955:"#27ae60"};
const SHORT  = {H00015:"上证红利", H00922:"中证红利", H20269:"红利低波", H20955:"红利低波100"};
const CODES  = ["H00015","H00922","H20269","H20955"];
const TOTAL  = SERIES.H20269.invested[SERIES.H20269.invested.length-1];

/* ---------- 卡片 ---------- */
(function(){
  const box = document.getElementById("cards");
  CARDS.forEach((c,i)=>{
    const minMdd = Math.min(...CARDS.map(x=>x.mdd_p));
    const tag = c.code==="H20269" ? '<span class="badge win">全场最佳</span>'
              : (c.mdd_p === minMdd ? '<span class="badge steady">回撤最小</span>' : '');
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = `
      <div class="top"><span class="dot" style="background:${COLORS[c.code]}"></span><span class="nm">${c.name}</span><span class="ix-code">${c.code}</span>${tag}</div>
      <div class="fval">¥${c.final_value.toLocaleString()} <small>终值</small></div>
      <div class="kv">
        <div><div class="k">年化(XIRR)</div><div class="v pos">${c.cagr.toFixed(2)}%</div></div>
        <div><div class="k">总收益</div><div class="v pos">+${c.total_ret.toFixed(2)}%</div></div>
        <div><div class="k">净赚</div><div class="v pos">+¥${c.profit.toLocaleString()}</div></div>
        <div><div class="k">组合最大回撤</div><div class="v neg">${c.mdd_p.toFixed(2)}%</div></div>
        <div><div class="k">当前股息率*</div><div class="v pos">${c.dy.toFixed(2)}%</div></div>
        <div><div class="k">指数10年最大回撤</div><div class="v neg">${c.mdd_i.toFixed(2)}%</div></div>
      </div>
      <div class="mdd">最大浮亏 ¥${c.mdd_p_amt.toLocaleString()}（${c.mdd_p_peak} 峰值 → ${c.mdd_p_trough} 谷底，${c.mdd_p_recover_days} 天收复）</div>
      <div class="etf" style="margin-top:8px">场外基金：${c.otc}</div>`;
    box.appendChild(el);
  });
})();

/* ---------- 股息率卡片 ---------- */
(function(){
  const box = document.getElementById("yieldCards");
  box.innerHTML = CODES.map(c=>{
    const y = YIELDS[c];
    return `<div class="card" style="padding:14px 16px">
      <div class="top"><span class="dot" style="background:${COLORS[c]}"></span><span class="nm">${SHORT[c]}</span><span class="ix-code">${c}</span></div>
      <div class="fval" style="font-size:24px">${y.dy.toFixed(2)}%</div>
      <div style="font-size:12px;color:var(--sub);margin-top:2px">近12个月实际股息率（${y.d0} ~ ${y.d1}）</div>
      <div style="font-size:11.5px;color:var(--sub);margin-top:6px;background:#fafbfc;border-radius:8px;padding:6px 8px">同期全收益 ${y.tr.toFixed(1)}% ｜ 价格 ${y.pr.toFixed(1)}%</div>
    </div>`;
  }).join("");
})();

/* ---------- 年度涨跌四指数对比表 ---------- */
(function(){
  const COLS = ["H20269","H00922","H20955","H00015"];  // 按图片列序:红利低波/中证红利/红利低波100/上证红利
  const years = Object.keys(ANNUAL_GRID).sort();
  const head = `<tr><th>年份</th>${COLS.map(c=>`<th class="num">${SHORT[c]}</th>`).join("")}</tr>`;
  const body = years.map(y=>`<tr><td><b>${y}${y==="2026"?"年(截至7月)":""}</b></td>${
    COLS.map(c=>{
      const v = ANNUAL_GRID[y][c] || 0;
      const sign = v>=0?"+":"";
      return `<td class="num ${v>=0?"pos":"neg"}"><b>${sign}${(v*100).toFixed(2)}%</b></td>`;
    }).join("")
  }</tr>`).join("");
  document.getElementById("tbl_yoy").innerHTML = head + body;
})();

/* ---------- 回撤明细表 ---------- */
(function(){
  const rows = CARDS.map(c=>`
    <tr class="${c.code==='H20269'?'hl':''}">
      <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${COLORS[c.code]}"></span> <b>${c.short}</b></td>
      <td class="num neg"><b>${c.mdd_p.toFixed(2)}%</b></td>
      <td class="num">${c.mdd_p_peak}<br><span style="color:var(--sub);font-size:11.5px">¥${c.mdd_p_peak_v.toLocaleString()}</span></td>
      <td class="num">${c.mdd_p_trough}<br><span style="color:var(--sub);font-size:11.5px">¥${c.mdd_p_trough_v.toLocaleString()}</span></td>
      <td class="num"><b class="neg">-¥${c.mdd_p_amt.toLocaleString()}</b></td>
      <td class="num">${c.mdd_p_trough_days} 天</td>
      <td class="num">${c.mdd_p_recover||"未恢复"}</td>
      <td class="num">${c.mdd_p_recover_days!=null? c.mdd_p_recover_days+" 天":"—"}</td>
    </tr>`).join("");
  document.getElementById("tbl_mdd").innerHTML = `
    <tr><th>指数</th><th class="num">最大回撤</th><th class="num">峰值日（峰值市值）</th><th class="num">谷底日（谷底市值）</th><th class="num">最大浮亏</th><th class="num">峰值→谷底</th><th class="num">收复日</th><th class="num">峰值→收复</th></tr>${rows}`;
})();

/* ---------- 区间内回撤提醒 ---------- */
(function(){
  const box = document.getElementById("alertGrid");
  // 指数口径10年回撤提醒 + 组合口径浮亏
  const idxCards = CARDS.map(c=>({short:c.short, pct:c.mdd_i, peak:c.mdd_i_peak, trough:c.mdd_i_trough, rec:c.mdd_i_recover, days:c.mdd_i_recover_days})).sort((a,b)=>a.pct-b.pct);
  const worst = idxCards[0];
  const worstPort = CARDS.slice().sort((a,b)=>a.mdd_p-b.mdd_p)[0];
  const items = [
    {n:"指数口径最深回撤（2018 熊市）", v:`${worst.pct.toFixed(2)}%`, s:`${worst.short} · ${worst.peak} → ${worst.trough}，约 ${worst.days/30.44|0} 个月收复`},
    {n:"组合口径最大浮亏", v:`-¥${worstPort.mdd_p_amt.toLocaleString()}`, s:`${worstPort.short} · 峰值 ${worstPort.mdd_p_peak} → 谷底 ${worstPort.mdd_p_trough}`},
    {n:"四个指数平均组合回撤", v:`${(CARDS.reduce((s,c)=>s+c.mdd_p,0)/4).toFixed(2)}%`, s:`2016.07 - 2026.07 定投区间内`},
    {n:"组合回撤最深的时点", v:`2021.09 - 11`, s:`红利行情阶段性回落，谷底浮亏 ${CARDS.filter(c=>c.mdd_p_trough.startsWith("2021-11")).map(c=>SHORT[c.code]+" -¥"+c.mdd_p_amt.toLocaleString()).join("、")}`},
  ];
  items.forEach(it=>{
    const el = document.createElement("div");
    el.className = "ag";
    el.innerHTML = `<div class="n">${it.n}</div><div class="v neg">${it.v}</div><div style="font-size:12px;color:var(--sub)">${it.s}</div>`;
    box.appendChild(el);
  });
})();

/* ---------- ECharts ---------- */
const fonts = {fontFamily:"-apple-system,'PingFang SC','Microsoft YaHei',sans-serif"};
const axis = {
  axisLine:{lineStyle:{color:"#d7dde6"}},
  axisLabel:{color:"#6b7686",fontSize:11,...fonts},
  splitLine:{lineStyle:{color:"#eef1f6"}}
};

/* 水下回撤图 */
let underChart=null, underMode="port";
function renderUnder(){
  const key = underMode==="port" ? "ddPort" : "ddIdx";
  const series = CODES.map(c=>({
    name:SHORT[c], type:"line", data:SERIES[c][key], smooth:false, symbol:"none",
    lineStyle:{width:1.8,color:COLORS[c]},
    areaStyle:{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:COLORS[c]+"55"},{offset:1,color:COLORS[c]+"08"}]}},
    emphasis:{focus:"series"},
    markPoint:{symbol:"pin",symbolSize:44,symbolOffset:[c==="H00015"?-14:(c==="H20269"?14:0),0],data:[{coord:[SERIES[c][key].indexOf(Math.min(...SERIES[c][key])), Math.min(...SERIES[c][key])],value:(Math.min(...SERIES[c][key])*100).toFixed(2)+"%",label:{fontSize:11,color:"#fff"}}],
      itemStyle:{color:COLORS[c]}}
  }));
  underChart.setOption({
    grid:{left:56,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",valueFormatter:v=>(v*100).toFixed(2)+"%"},
    legend:{data:CODES.map(c=>SHORT[c]),top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:DATES,boundaryGap:false,...axis},
    yAxis:{type:"value",max:0,min:underMode==="port"?-0.20:-0.32,axisLabel:{formatter:v=>(v*100).toFixed(0)+"%",color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}
document.getElementById("segPort").onclick=()=>{underMode="port";document.getElementById("segPort").className="on";document.getElementById("segIdx").className="";renderUnder();};
document.getElementById("segIdx").onclick=()=>{underMode="idx";document.getElementById("segIdx").className="on";document.getElementById("segPort").className="";renderUnder();};

/* 市值走势 */
let growthChart=null;
function renderGrowth(){
  const series = CODES.map(c=>({name:SHORT[c],type:"line",data:SERIES[c].value,smooth:false,symbol:"none",lineStyle:{width:2,color:COLORS[c]}}));
  series.push({name:"累计投入",type:"line",data:SERIES.H20269.invested,smooth:false,symbol:"none",lineStyle:{width:1.6,type:"dashed",color:"#9aa7b8"},itemStyle:{opacity:.55}});
  growthChart.setOption({
    grid:{left:64,right:24,top:30,bottom:52},
    tooltip:{trigger:"axis",valueFormatter:v=>"¥"+Math.round(v).toLocaleString()},
    legend:{data:[...CODES.map(c=>SHORT[c]),"累计投入"],top:0,textStyle:{...fonts,fontSize:12,color:"#6b7686"},icon:"roundRect"},
    xAxis:{type:"category",data:DATES,boundaryGap:false,...axis},
    yAxis:{type:"value",axisLabel:{formatter:v=>"¥"+(v>=10000?(v/10000).toFixed(1)+"万":v),color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series
  }, true);
}

/* 年度柱状 */
let annualChart=null, curCode="H20269";
function renderAnnual(){
  const c = CARDS.find(x=>x.code===curCode);
  const ydata = c.annual;
  const bars = ydata.map(a=>a.profit);
  annualChart.setOption({
    grid:{left:64,right:24,top:40,bottom:40},
    tooltip:{trigger:"axis",formatter:ps=>{const a=ydata[ps[0].dataIndex];return `${a.y}年末<br>指数年度涨跌 <b class="${a.idx>=0?"pos":"neg"}">${a.idx>=0?"+":""}${(a.idx*100).toFixed(2)}%</b>（全收益）<br>累计投入 ¥${a.inv.toLocaleString()}<br>年末市值 ¥${a.val.toLocaleString()}<br><b>浮盈 ¥${a.profit.toLocaleString()}</b>（当年盈亏 ${a.yr>=0?"+":""}¥${a.yr.toLocaleString()}）`;}},
    xAxis:{type:"category",data:ydata.map(a=>a.y),...axis},
    yAxis:{type:"value",axisLabel:{formatter:v=>"¥"+(v>=10000?(v/10000).toFixed(1)+"万":v),color:"#6b7686",fontSize:11},splitLine:{lineStyle:{color:"#eef1f6"}}},
    series:[{type:"bar",data:bars,barWidth:"46%",
      itemStyle:{color:p=>p.value>=0?"#c0392b":"#1e8e5a",borderRadius:[4,4,0,0]},
      label:{show:true,position:"top",formatter:p=>"¥"+(p.value>=10000?(p.value/10000).toFixed(1)+"万":p.value),fontSize:10.5,color:"#4a5568",...fonts}}]
  }, true);
  // 年度表格
  document.getElementById("tbl_annual").innerHTML =
    `<tr><th>年末</th><th class="num">指数年度涨跌幅</th><th class="num">累计投入</th><th class="num">账户市值</th><th class="num">累计浮盈</th><th class="num">当年盈亏</th></tr>`+
    ydata.map(a=>`<tr><td><b>${a.y}</b></td><td class="num ${a.idx>=0?"pos":"neg"}"><b>${a.idx>=0?"+":""}${(a.idx*100).toFixed(2)}%</b></td><td class="num">¥${a.inv.toLocaleString()}</td><td class="num">¥${a.val.toLocaleString()}</td><td class="num ${a.profit>=0?"pos":"neg"}">${a.profit>=0?"+":""}¥${a.profit.toLocaleString()}</td><td class="num ${a.yr>=0?"pos":"neg"}">${a.yr>=0?"+":""}¥${a.yr.toLocaleString()}</td></tr>`).join("");
}
document.getElementById("selYear").innerHTML = CODES.map(c=>`<option value="${c}" ${c===curCode?"selected":""}>${SHORT[c]} ${c}</option>`).join("");
document.getElementById("selYear").onchange = e=>{curCode=e.target.value;renderAnnual();};

/* 图例 */
(function(){
  document.getElementById("lg1").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]} 最大回撤 ${(Math.min(...SERIES[c][underMode==="port"?"ddPort":"ddIdx"])*100).toFixed(2)}%</div>`).join("");
  document.getElementById("lg2").innerHTML = CODES.map(c=>`<div class="li"><span class="sw" style="background:${COLORS[c]}"></span>${SHORT[c]}（终值 ¥${CARDS.find(x=>x.code===c).final_value.toLocaleString()}）</div>`).join("") +
    `<div class="li"><span class="sw" style="background:#9aa7b8"></span>累计投入 ¥${TOTAL.toLocaleString()}</div>`;
})();

/* 结论区 */
(function(){
  const PICK = ["H20269","H20955","H00922"];
  const pickMeta = {
    H20269: {t:"如果只能选一个：红利低波全收益",tag:"全场最佳",tagCls:"badge win",why:"收益最高且回撤中等，横跨沪深两市、50 只成分股兼顾分散与弹性。"},
    H20955: {t:"追求极致稳定：红利低波100全收益",tag:"回撤最小",tagCls:"badge steady",why:"100 只成分股足够分散，不怕单只股票暴雷；回撤最小、持有最安心。"},
    H00922: {t:"看重体验与配置：中证红利全收益",tag:"均衡之选",tagCls:"badge steady",why:"上证标杆指数，回撤控制好、恢复快；ETF 规模大、流动性好。"}
  };
  const maxCagr = Math.max(...CARDS.map(x=>x.cagr));
  const html = PICK.map(code=>{
    const c = CARDS.find(x=>x.code===code);
    const m = pickMeta[code];
    const li = [
      ["年化收益率", c.cagr.toFixed(2)+"%"+ (c.cagr===maxCagr?"（四者最高）":"")],
      ["10年终值", "¥"+c.final_value.toLocaleString()+"（+"+c.total_ret.toFixed(1)+"%）"],
      ["组合最大回撤", c.mdd_p.toFixed(2)+"%"],
      ["最大浮亏", "-¥"+c.mdd_p_amt.toLocaleString()+"（"+c.mdd_p_trough+" 谷底）"],
      ["回撤收复", c.mdd_p_recover_days+" 天"],
    ];
    return `<div class="pc">
      <div class="pt"><span class="dot" style="width:10px;height:10px;border-radius:50%;background:${COLORS[code]}"></span>${m.t} <span class="pc-tag">${m.tag}</span></div>
      <div class="pc-sub"><span class="ix-code">${c.code}</span> · 场外基金：${c.otc}</div>
      <ul>${li.map(x=>`<li><span class="k">${x[0]}</span><span class="v">${x[1]}</span></li>`).join("")}</ul>
      <div style="font-size:12.5px;color:var(--sub);margin-top:10px;background:#fafbfc;border-radius:8px;padding:8px 10px">${m.why}</div>
    </div>`;
  }).join("");
  document.getElementById("pick").innerHTML = html;
})();

/* init */
window.addEventListener("resize",()=>{underChart&&underChart.resize();growthChart&&growthChart.resize();annualChart&&annualChart.resize();});
(function init(){
  underChart = echarts.init(document.getElementById("c_under"));
  growthChart = echarts.init(document.getElementById("c_growth"));
  annualChart = echarts.init(document.getElementById("c_annual"));
  renderUnder(); renderGrowth(); renderAnnual();
})();
</script>
</body>
</html>"""

# 注入数据
def fmt(n):
    return f"{n:,.0f}"

meta = r["meta"]
amount, periods, total = meta["amount"], meta["periods"], meta["total_invest"]
cagrs = [it["cagr"] * 100 for it in idx]
mddps = [it["mdd_port"]["pct"] * 100 for it in idx]
mddi = [it["mdd_index_10y"]["pct"] * 100 for it in idx]
mdd_amts = [it["mdd_port"]["amt"] for it in idx] if "amt" in it["mdd_port"] else [round((it["mdd_port"]["peak_value"] - it["mdd_port"]["trough_value"])) for it in idx]
finals = [it["final_value"] for it in idx]
reps = {
    "%%AMOUNT%%": fmt(amount),
    "%%TOTAL%%": fmt(total),
    "%%PERIODS%%": str(periods),
    "%%CAGR_RANGE%%": f"{min(cagrs):.2f}% - {max(cagrs):.2f}%",
    "%%MDD_RANGE%%": f"-{abs(max(mddps)):.2f}% 到 -{abs(min(mddps)):.2f}%",
    "%%MDD_IDX_RANGE%%": f"-{abs(max(mddi)):.1f}% ~ -{abs(min(mddi)):.1f}%",
    "%%MDD_AMT_RANGE%%": f"{min(mdd_amts):,.0f} ~ {max(mdd_amts):,.0f}",
    "%%MDD_LIST%%": " / ".join(f"-{abs(x):.1f}%" for x in sorted(mddps)),
    "%%FINAL_BEST%%": fmt(max(finals)),
    "%%FINAL_BEST_WAN%%": f"{max(finals)/10000:.1f} 万",
    "%%DY_RANGE%%": f"{next(iter(YIELDS.values()))['d0']} ~ {next(iter(YIELDS.values()))['d1']}",
    "%%INVEST_WAN%%": f"{total/10000:g} 万",
    "%%FINAL_WAN_RANGE%%": f"{min(finals)/10000:.1f} - {max(finals)/10000:.1f} 万",
}
for k, v in reps.items():
    html = html.replace(k, v)

html = html.replace("__DATES__", jdump(DATES))
html = html.replace("__SERIES__", jdump(SERIES))
html = html.replace("__CARDS__", jdump(CARDS))
html = html.replace("__YIELDS__", jdump(YIELDS))
html = html.replace("__ANNUAL_GRID__", jdump(ANNUAL_GRID))

open("dividend_dashboard_yearly.html", "w", encoding="utf-8").write(html)
print("已生成 dividend_dashboard_yearly.html,", len(html)//1024, "KB")
