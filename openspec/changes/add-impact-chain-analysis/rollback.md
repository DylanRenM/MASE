# 回滚方案

> Source digest: `sha256:2ab76a85604cdfb789a1012cd38e10ce083fd373a793dbe1bf16e447e1b2a321`

## 回退策略

revert the impact-chain framework change and regenerate IDE adapters/training deck

## 数据兼容性

existing states remain readable because impact_analysis is optional; newly generated fields can be removed on rollback

## 停止条件

- existing API contract or GatePlan regression
- candidate freeze becomes stale immediately after creation
- framework distribution or repository-boundary audit fails
