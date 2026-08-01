# 回滚方案

> Source digest: `sha256:dc5be3c193f6d8f8dbde9e0c415bc27049de7a89afadc6f4148acaeb415db808`

## 回退策略

回退 2.4 版本元数据、成本输出和当前课件指针，保留 2.3 课件

## 数据兼容性

GatePlan 只增加字段，旧 evidence 可读，无业务数据迁移

## 停止条件

- 按变更/发布计划执行
