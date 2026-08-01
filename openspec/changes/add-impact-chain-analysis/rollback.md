# 回滚方案

> Source digest: `sha256:edb05581908202fe5757e5e8f2462c2479474dad98b8c40c915443513eea823c`

## 回退策略

revert the impact-chain framework change and regenerate IDE adapters/training deck

## 数据兼容性

existing states remain readable because impact_analysis is optional; newly generated fields can be removed on rollback

## 停止条件

- existing API contract or GatePlan regression
- candidate freeze becomes stale immediately after creation
- framework distribution or repository-boundary audit fails
