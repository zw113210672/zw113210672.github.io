# 📊 大伟策略

基于大盘和个股，自动生成。

## 目录结构

```
├── index.html          # 首页 - 交易记录总览
├── _config.yml         # GitHub Pages 配置
├── assets/
│   └── style.css       # 全局样式
├── records/
│   ├── index.html      # 归档页
│   ├── index.json      # 数据文件（供首页/归档页加载）
│   └── YYYY-MM-DD.html # 每日交易记录详情
├── generate_site.py    # 自动生成每日记录的脚本
└── README.md
```

## 自动更新流程

每天 15:00 收盘扫描完成后，运行：

```bash
cd D:\选股软件\hermes选股\website
python generate_site.py

# 提交到 GitHub
git add -A
git commit -m "每日更新 YYYY-MM-DD"
git push
```

## 部署

GitHub Pages 已启用，访问：https://zw113210672.github.io
