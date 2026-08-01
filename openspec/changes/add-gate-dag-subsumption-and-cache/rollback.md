# 回滚方案

> Source digest: `sha256:80062e81f4403ea3940d676ea7bfbfce26cb7c568dd657738f6ce60c26bc999f`

## 回退策略

移除新环境字段并回退 DAG 解析，旧 passed evidence 仍可读

## 数据兼容性

只增加证据字段，无持久业务数据迁移

## 停止条件

- 按变更/发布计划执行
