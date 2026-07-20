# 磨耳朵独立仓库迁移验证摘要

> 状态事实以 `mase-state.yaml` 和 `tasks.md` 为准；本文件汇总可读证据。

## 结果

| 门禁 | 结果 |
|---|---|
| 磨耳朵 Unit | 49/49 PASS |
| 磨耳朵 Integration | 55/55 PASS |
| 磨耳朵 Contract | 60/60 PASS |
| 磨耳朵 Native E2E | 20/20 PASS |
| Release build / app bundle / ad-hoc signature | PASS |
| MASE Framework Python | 49/49 PASS |
| MASE Sandbox JavaScript | 9/9 PASS |
| OpenSpec strict | PASS |
| Python compileall / rule sync / `git diff --check` | PASS |
| `mase check` | PASS · standard/generic |
| 双 Git 根与文件归属检查 | PASS |

## 仓库边界

- MASE：`/Users/dylanren/Documents/trae_projects/MASE`
- 磨耳朵：`/Users/dylanren/Documents/trae_projects/磨耳朵`
- 两个 `git rev-parse --show-toplevel` 返回不同平级目录。
- 磨耳朵仓库为 `main` 分支、本地独立 Git、无 external remote，工作树干净。
- 产品当前提交：`45510d1`；迁入快照：`3d56e5a`；迁移兼容修复：`d64768e`。
- MASE 当前树不含产品 Package、Swift 源码/测试、产品 OpenSpec、需求资料、构建脚本、`dist` 或 Swift `.build`。
- 磨耳朵当前树不含 MASE 的 `mase_cli`、profiles、schemas、agents 或 skills 运行时。

## 缓存与恢复

- 根 Swift `.build` 只保留在磨耳朵目录，并已处理路径绑定的 module cache。
- MASE 内 846MB POC `.build` 已删除；未复制第二份大型缓存。
- 可从磨耳朵独立 Git 或 MASE 来源提交 `a28c4f6` 恢复产品源码。

## 诊断说明

迁移后追加的两项构建脚本回归测试使 Integration 从 53 增至 55。一次单独复跑在系统并发负载下触发既有 18MB/3 秒性能阈值，随后复跑 55/55 通过，目标用例耗时 2.32 秒；全套迁移验收也已通过，因此未修改性能标准或业务实现。
