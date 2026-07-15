# 组织级 Harness 框架

本框架基于 CMMI 思想，定义了组织级的标准软件流程和 AI 协同规则。

## 框架结构

```
org-harness-framework/
├── policy/              # 组织级方针
│   └── policy.md
├── ossp/                # 组织级标准软件流程
│   └── ossp.md
├── lcm/                 # 生命周期定义
│   └── lcm.md
├── process/             # 过程定义
│   └── process.md
├── templates/           # 模板
│   └── templates.md
├── guidelines/          # 指南
│   └── guidelines.md
├── checklists/          # 检查单
│   └── checklists.md
├── dod/                 # 完工准则
│   └── dod.md
├── lessons-learned/     # 经验教训库
│   └── lessons-learned.md
└── README.md
```

## 框架层次

| 层级 | 组件 | 说明 |
|------|------|------|
| 方针层 | Policy | 组织级高层方针和价值观 |
| 流程层 | OSSP | 组织级标准软件流程 |
| 生命周期层 | LCM | 软件开发生命周期定义 |
| 过程层 | Process | 具体过程定义 |
| 资产层 | Templates/Guidelines/Checklists/DOD | 过程资产 |
| 知识层 | Lessons Learned | 经验教训库 |

## 如何使用

### 1. 组织级使用
- 组织级制定和维护这些过程资产
- 定期审查和更新
- 确保所有项目遵循

### 2. 项目级裁剪
- 项目可以根据自身特点对组织级过程进行裁剪
- 裁剪决策必须记录在项目计划中
- 裁剪不能违反组织级的核心方针

### 3. AI 协同
- AI 必须遵循组织级和项目级的过程要求
- AI 输出必须经过人工评审
- AI 使用必须记录在经验教训库中

## 框架与项目的关系

```
组织级 Harness 框架
        │
        ▼
    项目级 PDP（裁剪后的过程定义）
        │
        ▼
    项目级 Harness（AI 协同规则）
        │
        ▼
    人机协同执行
```

## 持续改进

本框架采用 PDCA 循环进行持续改进：

1. **Plan**：制定过程和规则
2. **Do**：执行过程
3. **Check**：监控和评估
4. **Act**：改进过程和规则

---

**版本**: v1.0  
**生效日期**: 2026-01-01  
**文档编号**: OHF-001
