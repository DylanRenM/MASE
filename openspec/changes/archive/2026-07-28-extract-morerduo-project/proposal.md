## Why

磨耳朵只是采用 MASE 方法开发的独立产品，把产品源码、测试、需求、OpenSpec 和 1GB 以上 Swift 构建缓存放在 MASE 框架仓库中，会混淆所有权、合规检查、上下文检索和 Git 生命周期。应将它迁移到与 MASE 平级的独立目录和本地仓库，从物理上建立框架与使用者的边界。

## What Changes

- 在 `/Users/dylanren/Documents/trae_projects/磨耳朵` 创建独立项目根和本地 Git 仓库。
- 迁移 Swift Package、产品源码、资源、产品测试、需求/原型、产品 OpenSpec、构建脚本和验收包。
- 保留 MASE 框架自己的 Python 测试及 JavaScript Sandbox 测试，并将后者移出产品 `tests/e2e` 路径。
- 不复制 POC `.build`；移动根 `.build` 以避免双份缓存，验证后清理旧 POC 缓存以节省空间。
- 从 MASE 当前树删除全部磨耳朵产品文件，历史仍由原 MASE Git 提交和新仓库 provenance 记录追溯。
- 更新 MASE manifest、检查器和文档，使框架仓库不再依赖产品 `src/`、Swift tests 或产品 OpenSpec。

## Capabilities

### New Capabilities

- `repository-isolation`: MASE 框架与采用它开发的产品必须位于独立项目根、独立状态和独立 Git 仓库，且双方验证互不依赖。

### Modified Capabilities

<!-- 不改变磨耳朵产品行为，也不改变 MASE v2 已发布的过程能力。 -->

## Impact

- MASE 删除约 211 个已跟踪产品文件，并迁出 `.build`、`dist` 与产品 POC 源。
- 新仓库从已验收快照开始独立历史，README 记录来源分支/提交。
- 磨耳朵仍使用 MASE v2 Standard/Swift 规则，但 MASE 不再包含它的源码。
- 需要在新路径重新运行 49 Unit、53 Integration、60 Contract、20 E2E 和 app bundle 验证。
