# 设计文档：基线故事查看面板

> 关联项目：StoryPoint Estimator AI v1.0 | 2026-07-21

## 1. 需求概述

用户上传基准故事后，只能在状态栏看到"已加载 N 条"，无法查看具体有哪些故事。新增可折叠的完整表格视图。

## 2. 新增 API

### GET /baseline/list

| 项目 | 规格 |
|------|------|
| **前置条件** | 无 |
| **成功响应** | `200`, `[{id, title, description, points}, ...]` |
| **空数据** | `200`, `[]` |

## 3. 前端改动

### 3.1 折叠面板

在 `#upload-status` 下方新增：

```html
<div id="baseline-list-toggle" class="hidden">
    <span class="collapse-toggle" onclick="toggleBaselineList()">
        ▶ 查看已加载基准故事
    </span>
</div>
<div id="baseline-list-section" class="hidden">
    <table class="match-table" style="max-height:240px; display:block; overflow-y:auto;">
        <thead><tr><th>ID</th><th>标题</th><th>描述</th><th>故事点</th></tr></thead>
        <tbody id="baseline-list-body"></tbody>
    </table>
</div>
```

### 3.2 JS 逻辑

- `loadBaselineList()` — 调用 `/baseline/list`，渲染表格行
- `toggleBaselineList()` — 切换展开/收起，切换箭头方向
- 页面初始化 + 上传确认后调用 `loadBaselineList()`

### 3.3 显示规则

- 无数据时 `#baseline-list-toggle` 保持 hidden
- 有数据时显示折叠开关，默认折叠
- 表格 body 最大高度 240px，超出垂直滚动

## 4. 改动文件

| 文件 | 改动 |
|------|------|
| `app.py` | 新增 `GET /baseline/list` 路由 |
| `templates/index.html` | 折叠面板 HTML + CSS + JS |

## 5. 交互流程

```
页面加载 → /baseline/list → 有数据 → 显示折叠开关（折叠态）
                                         ↓ 点击展开
                                       显示完整表格

上传确认 → /baseline/list → 刷新表格数据
```
