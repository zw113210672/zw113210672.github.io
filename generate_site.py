# 大伟策略 - 网站自动生成脚本
# 用法: python generate_site.py
# 功能: 读取扫描结果JSON，生成index.json + 每日记录HTML
# 设置定时任务每天15:05自动运行

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

# ========== 配置 ==========
BASE_DIR = Path(__file__).parent.resolve()
RECORDS_DIR = BASE_DIR / "records"
HTML_TEMPLATE_FILE = BASE_DIR / "records" / "2026-07-23.html"  # 模板参考
DATA_FILE = BASE_DIR.parent / "data" / "watchlist_scan_{date}.json"

# ========== 从扫描结果生成记录 ==========
def load_scan_data(scan_date: str) -> list | dict | None:
    """加载指定日期的扫描结果JSON"""
    import glob
    # 日期格式转换：支持 YYYY-MM-DD 和 YYYYMMDD
    date_compact = scan_date.replace("-", "")
    data_dir = BASE_DIR.parent / "data"
    
    # 尝试所有可能的路径模式
    possible_paths = [
        data_dir / f"watchlist_scan_{scan_date}.json",
        data_dir / f"scan_result_{scan_date}.json",
        data_dir / f"scan_{scan_date}.json",
        data_dir / f"crash_scan_{scan_date}.json",
        data_dir / f"close_scan_{scan_date}.json",
        data_dir / f"intraday_scan_{scan_date}.json",
        data_dir / f"watchlist_scan_{date_compact}.json",
        data_dir / f"crash_scan_{date_compact}.json",
        data_dir / f"close_scan_{date_compact}.json",
        data_dir / f"intraday_scan_{date_compact}.json",
    ]
    for p in possible_paths:
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
    
    # 尝试模糊匹配
    pattern = str(data_dir / f"*{date_compact}*.json")
    files = sorted(glob.glob(pattern))
    if files:
        try:
            with open(files[0], "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None


def scan_data_to_records(scan_data: dict, scan_date: str) -> list:
    """将扫描数据转换为记录格式"""
    records = []
    # 适配不同格式的扫描结果
    if isinstance(scan_data, list):
        stocks = scan_data
    elif isinstance(scan_data, dict):
        # 先尝试标准格式
        stocks = scan_data.get("results", scan_data.get("data", scan_data.get("stocks", [])))
        # 如果标准格式为空，尝试盘中扫描格式（按推荐等级分类）
        if not stocks:
            all_stocks = []
            for key in ["🎯强烈推荐", "✅推荐买入", "👀观察", "🔍关注"]:
                all_stocks.extend(scan_data.get(key, []))
            stocks = all_stocks
    else:
        return records

    for s in stocks:
        if isinstance(s, dict):
            # 获取signal：优先用intraday风格的recommendation，其次用标准signal
            sig = s.get("recommendation", s.get("signal", ""))
            # 涨幅取change或today_pct
            chg = float(s.get("change", s.get("today_pct", s.get("涨幅%", 0))))
            records.append({
                "code": s.get("code", s.get("股票代码", s.get("Code", ""))),
                "name": s.get("name", s.get("股票名称", s.get("Name", ""))),
                "signal": sig if sig else ("🎯买入" if chg >= 9.5 else "👀持有"),
                "price": s.get("price", s.get("现价", s.get("Price", 0))),
                "change": chg,
                "sector": s.get("板块", s.get("sector", s.get("Sector", ""))),
            })
    return records


def generate_daily_html(records: list, scan_date: str, scan_stats: dict = None) -> str:
    """生成每日详情HTML"""
    if not records:
        return ""
    
    # 统计
    total = len(records)
    limit_up = sum(1 for r in records if r.get("change", 0) >= 9.5)
    
    # 板块统计
    sectors = {}
    for r in records:
        sec = r.get("sector", "其他")
        if sec not in sectors:
            sectors[sec] = {"count": 0, "limit_up": 0, "best": r}
        sectors[sec]["count"] += 1
        if r.get("change", 0) >= 9.5:
            sectors[sec]["limit_up"] += 1
        if r.get("change", 0) > sectors[sec]["best"].get("change", 0):
            sectors[sec]["best"] = r
    
    best_sector = max(sectors, key=lambda s: sectors[s]["count"]) if sectors else "无"
    
    sector_rows = ""
    for sec, info in sorted(sectors.items(), key=lambda x: -x[1]["count"]):
        best = info["best"]
        sector_rows += f"""        <tr><td>{sec}</td><td>{info["count"]}</td><td>{info["limit_up"]}</td><td>{best.get("name", "")}(+{best.get("change", 0):.2f}%)</td></tr>\n"""
    
    stock_rows = ""
    for r in records:
        change = r.get("change", 0)
        sig = r.get("signal", "👀持有")
        sig_html = f'<span class="signal-buy">{sig}</span>' if "🎯" in sig else f'<span class="signal-hold">{sig}</span>'
        price = r.get("price", 0)
        try:
            price_str = f"{float(price):.2f}"
        except:
            price_str = str(price)
        stock_rows += f"""        <tr>
          <td>{r.get("code", "")}</td>
          <td>{r.get("name", "")}</td>
          <td>{sig_html}</td>
          <td>{price_str}</td>
          <td class="{'up' if change >= 0 else 'down'}">{'+' if change >= 0 else ''}{change:.2f}%</td>
          <td>{r.get("sector", "--")}</td>
        </tr>\n"""
    
    # 按涨幅排序取前N个作为涨停/大涨统计
    sorted_records = sorted(records, key=lambda r: -r.get("change", 0))
    
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{scan_date} - 大伟策略</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>

<nav class="navbar">
  <a href="/" class="nav-brand">📊 大伟<span>策略</span></a>
  <div class="nav-links">
    <a href="/">首页</a>
    <a href="/records/">归档</a>
  </div>
</nav>

<div class="container">

  <div class="detail-header">
    <a href="/" class="back-link">← 返回首页</a>
    <h1>{scan_date} 尾盘扫描报告</h1>
    <p class="detail-date">扫描时间：14:45 · 命中 {total} 只</p>
  </div>

  <div class="stats-grid">
    <div class="stat-card">
      <div class="stat-value green">{total}</div>
      <div class="stat-label">命中股票</div>
    </div>
    <div class="stat-card">
      <div class="stat-value gold">{limit_up}</div>
      <div class="stat-label">涨停</div>
    </div>
    <div class="stat-card">
      <div class="stat-value blue">{best_sector}</div>
      <div class="stat-label">最强板块</div>
    </div>
    <div class="stat-card">
      <div class="stat-value green">+{sorted_records[0].get("change", 0):.2f}%</div>
      <div class="stat-label">最大涨幅</div>
    </div>
  </div>

  <div class="scan-results">
    <h2>📋 扫描结果明细</h2>
    <table class="trade-table">
      <thead>
        <tr>
          <th>代码</th>
          <th>名称</th>
          <th>信号</th>
          <th>现价</th>
          <th>涨幅%</th>
          <th>板块</th>
        </tr>
      </thead>
      <tbody>
{stock_rows}      </tbody>
    </table>
  </div>

  <div class="scan-results">
    <h2>📊 板块分析</h2>
    <table class="trade-table">
      <thead>
        <tr><th>板块</th><th>命中数</th><th>涨停数</th><th>最强股</th></tr>
      </thead>
      <tbody>
{sector_rows}      </tbody>
    </table>
  </div>

</div>

<div class="footer">
  <p>📊 大伟策略 · 仅供参考，不构成投资建议</p>
  <p style="margin-top: 4px;">Generated by Hermes Agent · {scan_date}</p>
</div>

</body>
</html>
"""


def update_index_json(records: list, scan_date: str):
    """更新 index.json"""
    index_file = RECORDS_DIR / "index.json"
    
    # 读取现有数据
    existing = {"totalDays": 0, "totalStocks": 0, "winRate": 100, "maxProfit": 0, "latest": []}
    if index_file.exists():
        try:
            with open(index_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            pass
    
    # 更新
    existing["totalDays"] += 1
    existing["totalStocks"] = max(existing.get("totalStocks", 0), len(records))
    max_p = max((r.get("change", 0) for r in records), default=0)
    existing["maxProfit"] = max(existing.get("maxProfit", 0), round(max_p, 2))
    
    # 最新记录插入最前面
    new_entry = {
        "date": scan_date,
        "signal": "扫描",
        "stocks": [{
            "code": r.get("code", ""),
            "name": r.get("name", ""),
            "signal": r.get("signal", "👀持有"),
            "price": f"{float(r.get('price', 0)):.2f}" if r.get("price") else "0.00",
            "change": round(r.get("change", 0), 2),
            "sector": r.get("sector", "--"),
        } for r in records[:10]]  # 首页只显示前10只
    }
    existing["latest"].insert(0, new_entry)
    # 保留最近30天
    existing["latest"] = existing["latest"][:30]
    
    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    return existing


def main():
    # 默认用今天
    scan_date = sys.argv[1] if len(sys.argv) > 1 else date.today().strftime("%Y-%m-%d")
    
    print(f"📊 生成 {scan_date} 交易记录...")
    
    # 加载扫描数据
    scan_data = load_scan_data(scan_date)
    if not scan_data:
        print(f"⚠️ 未找到 {scan_date} 的扫描数据，跳过")
        return
    
    # 转成记录格式
    records = scan_data_to_records(scan_data, scan_date)
    if not records:
        print(f"⚠️ {scan_date} 扫描数据为空，跳过")
        return
    
    print(f"  命中 {len(records)} 只股票")
    
    # 生成详情页
    html = generate_daily_html(records, scan_date)
    detail_file = RECORDS_DIR / f"{scan_date}.html"
    with open(detail_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 详情页: {detail_file}")
    
    # 更新 index.json
    idx = update_index_json(records, scan_date)
    print(f"  ✅ index.json 已更新 (共 {idx['totalDays']} 天)")
    print(f"\n🎉 完成！网站已更新")


if __name__ == "__main__":
    main()
