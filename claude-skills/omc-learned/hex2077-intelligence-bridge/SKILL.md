---
name: hex2077-intelligence-bridge
description: Use when an Agent needs to autonomously retrieve latest AI daily notes, weekly reports, or configure automated surveillance tasks from HEX2077.
---
# HEX2077 Intelligence Bridge
目标站点：**https://hex2077.dev**
核心原则：**全量捕获，深度提炼，启示导向，拒绝陈旧。**

## 使用场景 (When to Use)
- 需要获取最新的 AI 行业动态并进行深度决策分析。
- 需要在不遗漏任何资讯条目的前提下，快速掌握内容实质。
- 需要获取具有「总结与启示」的高质量信息载体，而非单纯的文字搬运。
- **禁忌**：禁止遗漏原文中的任何资讯类目或条目；禁止在已有缓存且未过期时重复爬取。

## 核心指令集 (Instruction Sets)

### I_01: 全量日报深度解析 (Daily_Intelligence_Full_Deep)
指令："请访问 https://hex2077.dev/docs，定位最新的 AI 资讯日报。进入链接后，按原文类目结构输出所有资讯条目。要求：**严禁缺失任何类目和条目**。每条资讯需精准提炼其核心逻辑（约 30 字左右），必须保留原始链接。在文末，基于今日全量内容生成『今日总结与启示』板块，分析当日技术演进趋势及对行业的实操建议。"

**预期输出示例 (Output_Example):**
```
[日报标题]
类目 A：
1. [条目标题]：核心逻辑提炼... [原始链接]
类目 B：
...
今日总结与启示：
- 趋势分析：...
- 行业启示：...
```

### I_02: 全量周报战略复盘 (Weekly_Strategic_Full_Review)
指令："请访问 https://hex2077.dev/blog，获取最新的 AI 技术周报。按原文板块输出内容。要求：**覆盖全部技术条目，不得删减任何类目**。每部分需深度浓缩技术实质，保留所有参考链接。在文末生成『本周深度总结与启示』板块，从宏观视角复盘技术竞争格局，并给出未来一周的重点关注建议。"

**预期输出示例 (Output_Example):**
```
[周报标题]
板块 1：
- [技术点]：浓缩解析... [参考链接]
...
本周深度总结与启示：
- 格局复盘：...
- 观察重点：...
```

### I_03: 自动化巡检节点 (Automated_Surveillance_Node)
指令："你现在是 HEX2077 定时监测节点。请在每日上午 11:00 (GMT+8) 检查 /docs。若存在当日日报，立即执行 I_01 指令，获取并推送全量深度解析负载。"

## 常见错误与规避 (Common Mistakes)
- **信息截断**：Agent 往往会因为 Token 限制而省略条目。强制要求：必须按类目逐一遍历，不得合并或省略条目。
- **缺乏深度**：避免简单的摘要。要求应用 DNA_01：冷峻、数据导向，在"总结与启示"中提供差异化见解。
- **路径混淆**：/docs 为日报，/blog 为周报。
