# BUG 案例: {BUG 简述}

| 字段 | 值 |
|------|-----|
| 发现日期 | YYYY-MM-DD |
| 严重程度 | high / medium / low |
| 发现方式 | e2e / exploratory / code-review / security-scan |
| 类型 | 崩溃 / 逻辑 / 性能 / 并发 / 环境 / 集成 |
| 相关 Capability | {capability-name} |
| 修复人 | Agent 4 (bug-fixer) |

## 现象

<用户看到的错误是什么？>

## 根因

<技术上为什么会发生？>

## 修复

<如何修复的？>

## 为什么测试没发现？

<回顾自动化测试的缺口>

## 补充的测试用例

| 测试文件 | 测试场景 | 覆盖边界 |
|---------|---------|---------|
| `tests/unit/{capability}/...` | <场景> | <边界> |

## 经验教训

`docs/lessons/YYYY-MM-DD-{topic}.md`

## 横向扫描

<同类 BUG 是否存在于其他模块？扫描结果？>
